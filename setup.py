import os
import requests
import sys
from pathlib import Path


def download_stream(url, dest_path, chunk_size=1 << 20):
    """Download a file with streaming and basic progress. Returns downloaded bytes or raises."""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    with requests.get(url, stream=True, headers=headers, allow_redirects=True, timeout=30) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        downloaded = 0
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(dest_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        pct = min(downloaded / total * 100, 100.0)
                        print(f"\rDownloading {dest_path.name}: {pct:5.1f}%", end="", flush=True)
                    else:
                        print(f"\rDownloading {dest_path.name}: {downloaded} bytes", end="", flush=True)
        print()
    return downloaded


def download_yolo_files():
    """Download YOLOv3-tiny files (smaller and faster).

    Notes:
    - The original host for `yolov3-tiny.weights` rejects automated requests (403). We attempt a couple of mirrors.
    - If automatic download of weights fails, the script will create `download_yolo_weights.bat` that opens a browser to the official mirror page so users can manually download.
    """
    files = [
        {
            "name": "yolov3-tiny.weights",
            # Preferred mirror: GitHub user-hosted binary release (pjreddie original site blocks some clients)
            "urls": [
                "https://github.com/pjreddie/darknet/releases/download/darknet_yolo_v3_optimize/yolov3-tiny.weights",
                "https://pjreddie.com/media/files/yolov3-tiny.weights",
            ],
        },
        {
            "name": "yolov3-tiny.cfg",
            "urls": [
                "https://raw.githubusercontent.com/pjreddie/darknet/master/cfg/yolov3-tiny.cfg",
            ],
        },
        {
            "name": "coco.names",
            "urls": [
                "https://raw.githubusercontent.com/pjreddie/darknet/master/data/coco.names",
            ],
        },
    ]

    base_dir = Path.cwd()
    weights_download_failed = False

    for entry in files:
        name = entry["name"]
        dest = base_dir / name
        if dest.exists() and dest.stat().st_size > 0:
            print(f"✓ {name} already exists ({dest.stat().st_size} bytes)")
            continue

        success = False
        for url in entry["urls"]:
            try:
                print(f"Attempting to download {name} from: {url}")
                downloaded = download_stream(url, dest)
                if downloaded > 0:
                    # Basic validation: weights should be significantly larger than small text/html pages
                    if name.endswith('.weights') and downloaded < 3_000_000:
                        # Likely an HTML error page or truncated file; remove and continue
                        print(f"Downloaded {name} appears too small ({downloaded} bytes). Treating as failed.")
                        try:
                            dest.unlink(missing_ok=True)
                        except Exception:
                            pass
                        continue
                    print(f"✓ Downloaded {name} ({downloaded} bytes)")
                    success = True
                    break
            except requests.HTTPError as he:
                print(f"HTTP error downloading {name} from {url}: {he}")
            except requests.RequestException as re:
                print(f"Network error downloading {name} from {url}: {re}")
            except Exception as e:
                print(f"Error downloading {name} from {url}: {e}")

        if not success:
            print(f"❌ All automatic download attempts failed for {name}.")
            if name.endswith(".weights"):
                weights_download_failed = True
            else:
                return False

    # If weights failed, create a helpful batch file to open the official download link for manual download
    if weights_download_failed:
        bat_path = base_dir / "download_yolo_weights.bat"
        with open(bat_path, "w") as b:
            b.write("@echo off\n")
            b.write("echo The automatic download of yolov3-tiny.weights failed. Opening a browser so you can manually download it...\n")
            b.write("start https://pjreddie.com/darknet/yolo/\n")
            b.write("echo Save the file as yolov3-tiny.weights in this folder: %cd%\n")
            b.write("pause\n")
        print(f"⚠️  Created '{bat_path.name}' — run it to open the download page and manually save the weights in this directory.")
        return False

    return True


if __name__ == "__main__":
    ok = download_yolo_files()
    if ok:
        print("\n✅ All files downloaded successfully!")
        sys.exit(0)
    else:
        print("\n❌ Some downloads failed. See messages above. If weights failed, run 'download_yolo_weights.bat' to download manually.")
        sys.exit(2)