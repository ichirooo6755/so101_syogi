# Register a Mac SSH public key for passwordless login.
# Mac OpenSSH rejects the Japanese account name 電研, so this also ensures
# an ASCII admin user `syodo` exists. Run in an elevated PowerShell.
#Requires -RunAsAdministrator
param(
    [Parameter(Mandatory = $true)]
    [string]$PublicKey
)

$ErrorActionPreference = "Stop"
if ($PublicKey -notmatch '^\s*ssh-(ed25519|rsa) ') {
    throw "PublicKey must start with ssh-ed25519 or ssh-rsa"
}

$asciiUser = "syodo"
if (-not (Get-LocalUser -Name $asciiUser -ErrorAction SilentlyContinue)) {
    $pass = ConvertTo-SecureString ([guid]::NewGuid().ToString()) -AsPlainText -Force
    New-LocalUser -Name $asciiUser -Password $pass -PasswordNeverExpires `
        -UserMayNotChangePassword -AccountNeverExpires | Out-Null
    Add-LocalGroupMember -Group "Administrators" -Member $asciiUser
    Write-Host "Created local admin user '$asciiUser' (SSH key only; random password)."
}

$dir = "C:\ProgramData\ssh"
$keyFile = Join-Path $dir "administrators_authorized_keys"
New-Item -ItemType Directory -Force -Path $dir | Out-Null
$normalized = $PublicKey.Trim()
$existing = @()
if (Test-Path $keyFile) {
    $existing = Get-Content -LiteralPath $keyFile -ErrorAction SilentlyContinue
}
if ($existing -notcontains $normalized) {
    Add-Content -LiteralPath $keyFile -Value $normalized -Encoding ascii
}

# Windows sshd refuses this file unless ACL is Administrators + SYSTEM only.
icacls $keyFile /inheritance:r | Out-Null
icacls $keyFile /grant:r "SYSTEM:(F)" "BUILTIN\Administrators:(F)" | Out-Null

Write-Host "Key installed. From Mac:"
Write-Host "  ssh syodo-windows"
Write-Host "  (Host syodo-windows -> User syodo @ desktop-nt5t7n1)"
