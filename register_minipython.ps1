# PowerShell script to register .minipython file association on Windows
# Requires Administrator privileges to write to HKLM, or use HKCU for current user.

$Extension = ".minipython"
$ProgID = "MiniPython.File"
$Description = "MiniPython Script"
$IconPath = "`"$PSScriptRoot\assets\images\logominipython.ico`",0"
$Command = "python -m minipython `"%1`""

# 1. Register the ProgID
New-Item -Path "HKCU:\Software\Classes\$ProgID" -Force | Out-Null
Set-ItemProperty -Path "HKCU:\Software\Classes\$ProgID" -Name "(Default)" -Value $Description
New-Item -Path "HKCU:\Software\Classes\$ProgID\DefaultIcon" -Force | Out-Null
Set-ItemProperty -Path "HKCU:\Software\Classes\$ProgID\DefaultIcon" -Name "(Default)" -Value $IconPath
New-Item -Path "HKCU:\Software\Classes\$ProgID\shell\open\command" -Force | Out-Null
Set-ItemProperty -Path "HKCU:\Software\Classes\$ProgID\shell\open\command" -Name "(Default)" -Value $Command

# 2. Associate the extension
New-Item -Path "HKCU:\Software\Classes\$Extension" -Force | Out-Null
Set-ItemProperty -Path "HKCU:\Software\Classes\$Extension" -Name "(Default)" -Value $ProgID
# Doubling up icon on the extension itself for better reliability
New-Item -Path "HKCU:\Software\Classes\$Extension\DefaultIcon" -Force | Out-Null
Set-ItemProperty -Path "HKCU:\Software\Classes\$Extension\DefaultIcon" -Name "(Default)" -Value $IconPath

# 3. Aggressive Icon Cache Reset
Write-Host "Resetting Windows Icon Cache..." -ForegroundColor Yellow
if (Get-Process explorer -ErrorAction SilentlyContinue) {
    Stop-Process -Name explorer -Force
    Start-Sleep -Seconds 1
}

# Clear icon cache files
$cachePath = "$env:LOCALAPPDATA\Microsoft\Windows\Explorer"
Get-ChildItem -Path $cachePath -Filter "iconcache*" -File | Remove-Item -Force -ErrorAction SilentlyContinue

# Restart explorer
Start-Process explorer.exe

# Notify Shell
$code = @'
[DllImport("shell32.dll", CharSet = CharSet.Auto, SetLastError = true)]
public static extern void SHChangeNotify(uint wEventId, uint uFlags, IntPtr dwItem1, IntPtr dwItem2);
'@
$type = Add-Type -MemberDefinition $code -Name "Shell32" -Namespace "WinAPI" -PassThru
$type::SHChangeNotify(0x08000000, 0x0000, [IntPtr]::Zero, [IntPtr]::Zero)

Write-Host "Success! .minipython files are now associated with the MiniPython MP icon." -ForegroundColor Green
Write-Host "Explorer has been restarted to apply changes." -ForegroundColor Cyan
