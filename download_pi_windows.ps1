# download_pi_windows.ps1 - PowerShell helper to download Raspberry Pi files to current directory
# Run in PowerShell (Windows) to pull necessary Pi files for transfer to Raspberry Pi

$raw = "https://raw.githubusercontent.com/ishpreet404/roboGaurdian/main"
$files = @(
  "pi_camera_server.py",
  "raspberry_pi_server.py",
  "raspberry_pi_server_safe.py",
  "setup_raspberry_pi.sh",
  "setup_remote_access.sh",
  "PI_SETUP_COMMANDS.md",
  "UART_SETUP_GUIDE.md",
  "esp32_robot_9600_baud.ino",
  "esp32_connection_fixer.py",
  "yolov8n.pt"
)

mkdir -Force pi_files | Out-Null

foreach ($f in $files) {
  $url = "$raw/$f"
  $out = "pi_files\$f"
  Write-Host "Downloading $f..."
  try {
    Invoke-WebRequest -Uri $url -OutFile $out -UseBasicParsing -ErrorAction Stop
  } catch {
    Write-Warning "Failed to download $f"
  }
}

Write-Host "Done. Files are in .\pi_files" -ForegroundColor Green
