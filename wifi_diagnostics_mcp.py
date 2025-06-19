#!/usr/bin/env python3
"""
WiFi Diagnostics MCP Server for Windows (Fixed Version)
Provides automated WiFi troubleshooting capabilities via Model Context Protocol
"""

import asyncio
import subprocess
import json
import datetime
import os
import sys
from pathlib import Path
from typing import Dict, List, Any

# Try to use fastmcp if available, otherwise use mcp
try:
    from fastmcp import FastMCP
    mcp = FastMCP("WiFi Diagnostics")
except ImportError:
    # Fallback to standard mcp module
    from mcp.server.models import InitializationOptions
    from mcp.server.stdio import stdio_server
    from mcp.server import Server
    from mcp.types import Tool, TextContent
    
    mcp = Server("WiFi Diagnostics")

# Utility functions
def run_command(cmd: List[str], shell: bool = False) -> Dict[str, Any]:
    """Execute a command and return output"""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            shell=shell,
            timeout=30
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "command": " ".join(cmd) if isinstance(cmd, list) else cmd
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Command timed out", "command": " ".join(cmd)}
    except Exception as e:
        return {"success": False, "error": str(e), "command": " ".join(cmd)}

def run_powershell(script: str) -> Dict[str, Any]:
    """Execute PowerShell script and return output"""
    return run_command(["powershell", "-NoProfile", "-Command", script])

# Core diagnostic functions (undecorated for internal use and testing)
def _check_wifi_status() -> Dict[str, Any]:
    """Check current WiFi adapter status and connection state"""
    results = {}
    
    # Get WiFi interfaces
    interfaces = run_command(["netsh", "wlan", "show", "interfaces"])
    results["interfaces"] = interfaces
    
    # Get current profile
    current_profile = run_command(["netsh", "wlan", "show", "profiles"])
    results["profiles"] = current_profile
    
    # Get adapter info via PowerShell
    adapter_info = run_powershell("""
        Get-NetAdapter -Name '*Wi-Fi*', '*Wireless*' | 
        Select-Object Name, Status, LinkSpeed, DriverVersion | 
        ConvertTo-Json
    """)
    results["adapters"] = adapter_info
    
    return results

def _diagnose_connection_issues() -> Dict[str, Any]:
    """Run comprehensive WiFi connection diagnostics"""
    results = {}
    
    # Check IP configuration
    ipconfig = run_command(["ipconfig", "/all"])
    results["ipconfig"] = ipconfig
    
    # Test connectivity
    connectivity = run_powershell("""
        $tests = @()
        $tests += Test-NetConnection -ComputerName 8.8.8.8 -InformationLevel Detailed | 
                  Select-Object ComputerName, PingSucceeded, NameResolutionSucceeded
        $tests += Test-NetConnection -ComputerName google.com -Port 443 -InformationLevel Detailed |
                  Select-Object ComputerName, TcpTestSucceeded
        $tests | ConvertTo-Json
    """)
    results["connectivity"] = connectivity
    
    # Check DNS
    dns_test = run_command(["nslookup", "google.com"])
    results["dns"] = dns_test
    
    # Get DHCP info
    dhcp_info = run_powershell("""
        Get-NetIPConfiguration | Where-Object {$_.InterfaceAlias -like '*Wi-Fi*' -or $_.InterfaceAlias -like '*Wireless*'} | 
        Select-Object InterfaceAlias, IPv4Address, IPv4DefaultGateway, DNSServer |
        ConvertTo-Json
    """)
    results["dhcp"] = dhcp_info
    
    return results

def _check_authentication_issues() -> Dict[str, Any]:
    """Check for 802.1X authentication problems and certificate issues"""
    results = {}
    
    # Get authentication events
    auth_events = run_powershell("""
        Get-WinEvent -FilterHashtable @{
            LogName='Microsoft-Windows-WLAN-AutoConfig/Operational'
            ID=8001,8002,8003,11001
        } -MaxEvents 20 -ErrorAction SilentlyContinue |
        Select-Object TimeCreated, Id, Message |
        ConvertTo-Json
    """)
    results["auth_events"] = auth_events
    
    # Check certificates
    cert_check = run_powershell("""
        $certs = @()
        $certs += Get-ChildItem Cert:\\LocalMachine\\My | 
                  Where-Object {$_.NotAfter -lt (Get-Date).AddDays(30)} |
                  Select-Object Subject, NotAfter, Thumbprint
        $certs += Get-ChildItem Cert:\\CurrentUser\\My | 
                  Where-Object {$_.NotAfter -lt (Get-Date).AddDays(30)} |
                  Select-Object Subject, NotAfter, Thumbprint
        $certs | ConvertTo-Json
    """)
    results["certificates"] = cert_check
    
    # Get saved network profiles with auth info
    profiles = run_command(["netsh", "wlan", "show", "profiles"])
    if profiles["success"]:
        # Extract profile names and get details
        profile_names = []
        for line in profiles["stdout"].split('\n'):
            if "All User Profile" in line:
                name = line.split(":")[1].strip()
                profile_names.append(name)
        
        results["profile_details"] = {}
        for name in profile_names[:5]:  # Limit to first 5 profiles
            detail = run_command(["netsh", "wlan", "show", "profile", f'name="{name}"', "key=clear"])
            results["profile_details"][name] = detail
    
    return results

def _analyze_wifi_environment() -> Dict[str, Any]:
    """Analyze WiFi environment for interference and signal issues"""
    results = {}
    
    # Get available networks
    networks = run_command(["netsh", "wlan", "show", "networks", "mode=bssid"])
    results["available_networks"] = networks
    
    # Get signal strength
    signal_info = run_powershell("""
        netsh wlan show interfaces | Select-String 'Signal' | ForEach-Object { $_.ToString().Trim() }
    """)
    results["signal_strength"] = signal_info
    
    # Get driver information
    driver_info = run_powershell("""
        Get-NetAdapter -Name '*Wi-Fi*', '*Wireless*' | 
        Get-NetAdapterAdvancedProperty |
        Select-Object DisplayName, DisplayValue |
        ConvertTo-Json
    """)
    results["driver_settings"] = driver_info
    
    return results

def _generate_diagnostic_report() -> Dict[str, Any]:
    """Generate comprehensive WiFi diagnostic report"""
    report = {
        "timestamp": datetime.datetime.now().isoformat(),
        "system_info": {},
        "diagnostics": {}
    }
    
    # Generate Windows WiFi report
    wifi_report = run_command(["netsh", "wlan", "show", "wlanreport"])
    report["wifi_report_generated"] = wifi_report["success"]
    
    if wifi_report["success"]:
        report_path = Path(os.environ["ProgramData"]) / "Microsoft" / "Windows" / "WlanReport" / "wlan-report-latest.html"
        report["wifi_report_path"] = str(report_path)
    
    # Collect all diagnostic data using undecorated functions
    report["diagnostics"]["status"] = _check_wifi_status()
    report["diagnostics"]["connection"] = _diagnose_connection_issues()
    report["diagnostics"]["authentication"] = _check_authentication_issues()
    report["diagnostics"]["environment"] = _analyze_wifi_environment()
    
    # Generate summary
    issues_found = []
    
    # Check for common issues
    status_data = report["diagnostics"]["status"]
    if status_data.get("interfaces", {}).get("stdout", ""):
        if "disconnected" in status_data["interfaces"]["stdout"].lower():
            issues_found.append("WiFi adapter is disconnected")
    
    conn_data = report["diagnostics"]["connection"]
    if conn_data.get("connectivity", {}).get("stdout", ""):
        try:
            conn_results = json.loads(conn_data["connectivity"]["stdout"])
            if isinstance(conn_results, list) and len(conn_results) > 0:
                if not conn_results[0].get("PingSucceeded", False):
                    issues_found.append("No internet connectivity detected")
        except:
            pass
    
    auth_data = report["diagnostics"]["authentication"]
    if auth_data.get("auth_events", {}).get("stdout", ""):
        if "8002" in auth_data["auth_events"]["stdout"]:
            issues_found.append("Authentication failures detected")
    
    report["summary"] = {
        "issues_found": issues_found,
        "total_issues": len(issues_found),
        "status": "Issues detected" if issues_found else "No major issues found"
    }
    
    return report

def _fix_common_issues() -> Dict[str, Any]:
    """Attempt to fix common WiFi issues automatically"""
    fixes_applied = []
    results = {}
    
    # Reset WiFi adapter
    reset_adapter = run_powershell("""
        Get-NetAdapter -Name '*Wi-Fi*', '*Wireless*' | Restart-NetAdapter
    """)
    if reset_adapter["success"]:
        fixes_applied.append("Reset WiFi adapter")
    results["adapter_reset"] = reset_adapter
    
    # Flush DNS cache
    dns_flush = run_command(["ipconfig", "/flushdns"])
    if dns_flush["success"]:
        fixes_applied.append("Flushed DNS cache")
    results["dns_flush"] = dns_flush
    
    # Release and renew IP
    ip_release = run_command(["ipconfig", "/release"])
    ip_renew = run_command(["ipconfig", "/renew"])
    if ip_renew["success"]:
        fixes_applied.append("Renewed IP address")
    results["ip_renewal"] = {"release": ip_release, "renew": ip_renew}
    
    # Reset TCP/IP stack
    tcp_reset = run_command(["netsh", "int", "ip", "reset"], shell=True)
    if tcp_reset["success"]:
        fixes_applied.append("Reset TCP/IP stack (restart required)")
    results["tcp_reset"] = tcp_reset
    
    # Reset Winsock
    winsock_reset = run_command(["netsh", "winsock", "reset"], shell=True)
    if winsock_reset["success"]:
        fixes_applied.append("Reset Winsock (restart required)")
    results["winsock_reset"] = winsock_reset
    
    results["summary"] = {
        "fixes_applied": fixes_applied,
        "restart_required": "TCP/IP stack" in " ".join(fixes_applied) or "Winsock" in " ".join(fixes_applied)
    }
    
    return results

# MCP Tool implementations (decorated versions that call the core functions)
@mcp.tool()
def check_wifi_status() -> Dict[str, Any]:
    """Check current WiFi adapter status and connection state"""
    return _check_wifi_status()

@mcp.tool()
def diagnose_connection_issues() -> Dict[str, Any]:
    """Run comprehensive WiFi connection diagnostics"""
    return _diagnose_connection_issues()

@mcp.tool()
def check_authentication_issues() -> Dict[str, Any]:
    """Check for 802.1X authentication problems and certificate issues"""
    return _check_authentication_issues()

@mcp.tool()
def analyze_wifi_environment() -> Dict[str, Any]:
    """Analyze WiFi environment for interference and signal issues"""
    return _analyze_wifi_environment()

@mcp.tool()
def generate_diagnostic_report() -> Dict[str, Any]:
    """Generate comprehensive WiFi diagnostic report"""
    return _generate_diagnostic_report()

@mcp.tool()
def fix_common_issues() -> Dict[str, Any]:
    """Attempt to fix common WiFi issues automatically"""
    return _fix_common_issues()

# Main entry point
if __name__ == "__main__":
    # Check if using fastmcp or standard mcp
    if 'FastMCP' in globals():
        # FastMCP handles everything
        mcp.run()
    else:
        # Standard MCP server setup
        async def main():
            async with stdio_server() as (read_stream, write_stream):
                await mcp.run(
                    read_stream,
                    write_stream,
                    InitializationOptions(
                        server_name="WiFi Diagnostics",
                        server_version="1.0.0"
                    )
                )
        
        asyncio.run(main())
