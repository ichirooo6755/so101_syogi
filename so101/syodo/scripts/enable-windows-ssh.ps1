# Enable OpenSSH Server, TCP 22, and PowerShell as the default shell.
# Run in an elevated PowerShell.
#Requires -RunAsAdministrator
$ErrorActionPreference = "Stop"

Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0 -ErrorAction SilentlyContinue | Out-Null
Start-Service sshd
Set-Service -Name sshd -StartupType Automatic

if (-not (Get-NetFirewallRule -Name "OpenSSH-Server-In-TCP" -ErrorAction SilentlyContinue)) {
    New-NetFirewallRule -Name "OpenSSH-Server-In-TCP" -DisplayName "OpenSSH Server (sshd)" `
        -Enabled True -Direction Inbound -Protocol TCP -Action Allow -LocalPort 22 | Out-Null
}

$pwsh = (Get-Command powershell.exe).Source
New-ItemProperty -Path "HKLM:\SOFTWARE\OpenSSH" -Name DefaultShell -Value $pwsh -PropertyType String -Force | Out-Null

Write-Host "sshd running. Connect from Mac after adding a key with add-mac-ssh-key.ps1"
Get-Service sshd | Format-List Name, Status, StartType
