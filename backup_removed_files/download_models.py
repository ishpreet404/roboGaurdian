import urllib.request
import os
import requests

def download_file(url, filename):
    """Download file with progress indicator"""
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    
    with open(filename, 'wb') as file:
        downloaded = 0
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                file.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    percent = min((downloaded / total_size) * 100, 100.0)
                    print(f"\rDownloading {filename}: {percent:.1f}%", end='', flush=True)
                else:
                    print(f"\rDownloading {filename}: {downloaded} bytes", end='', flush=True)
    print(f"\n✓ Downloaded {filename}")
    return downloaded

print("Downloading MobileNet SSD model files...")

# Download prototxt
try:
    prototxt_url = "https://raw.githubusercontent.com/chuanqi305/MobileNet-SSD/master/deploy.prototxt"
    downloaded_size = download_file(prototxt_url, "MobileNetSSD_deploy.prototxt")
    
    # Verify the file was downloaded successfully
    if os.path.exists("MobileNetSSD_deploy.prototxt") and downloaded_size > 0:
        file_size = os.path.getsize("MobileNetSSD_deploy.prototxt")
        print(f"✓ File verified: {file_size} bytes")
    else:
        raise Exception("File download failed or file is empty")
        
except Exception as e:
    print(f"Error downloading prototxt: {e}")
    # Fallback method
    try:
        urllib.request.urlretrieve(prototxt_url, "MobileNetSSD_deploy.prototxt")
        if os.path.exists("MobileNetSSD_deploy.prototxt"):
            file_size = os.path.getsize("MobileNetSSD_deploy.prototxt")
            print(f"✓ Downloaded using fallback method: {file_size} bytes")
        else:
            print("❌ Fallback download also failed")
    except Exception as fallback_error:
        print(f"❌ Fallback download failed: {fallback_error}")

print("\n" + "="*60)
print("MobileNet SSD Model Setup")
print("="*60)

# Check if caffemodel already exists
caffemodel_path = "MobileNetSSD_deploy.caffemodel"
if os.path.exists(caffemodel_path):
    file_size = os.path.getsize(caffemodel_path)
    if file_size > 20000000:  # Should be around 23MB
        print(f"✓ Caffemodel already exists: {file_size/1024/1024:.1f} MB")
        print("✓ Model setup complete!")
    else:
        print(f"⚠️  Caffemodel exists but seems too small: {file_size/1024/1024:.1f} MB")
        print("   Expected size: ~23 MB. Please re-download.")
else:
    print("⚠️  IMPORTANT: Manual download required for caffemodel")
    print("The caffemodel file is hosted on Google Drive and requires manual download:")
    print("\n1. Open this link in your browser:")
    print("   https://drive.google.com/uc?export=download&id=0B3gersZ2cHIxRm5PMWRoTkdHdHc")
    print("\n2. Click download when prompted")
    print("\n3. Save the file as 'MobileNetSSD_deploy.caffemodel' in this directory:")
    print(f"   {os.getcwd()}")
    print("\n4. The file should be about 23 MB")

# Create a simple batch file for Windows users
if os.name == 'nt':  # Windows
    with open('download_model.bat', 'w') as f:
        f.write('@echo off\n')
        f.write('echo Opening model download link in browser...\n')
        f.write('start https://drive.google.com/uc?export=download^&id=0B3gersZ2cHIxRm5PMWRoTkdHdHc\n')
        f.write('echo.\n')
        f.write('echo Please download the file and save it as "MobileNetSSD_deploy.caffemodel"\n')
        f.write('pause\n')
    print("\n✓ Created 'download_model.bat' - double-click to open download link")