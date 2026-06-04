import re
import subprocess
import sys
from pathlib import Path

CLOUDFLARED_PATH = str(Path(__file__).parent / "tools" / "cloudflared-windows-amd64.exe")
LOCAL_URL = "http://localhost:8000"

def start_cloudflare_tunnel():
    cmd = [
        CLOUDFLARED_PATH,
        "tunnel",
        "--url",
        LOCAL_URL,
    ]

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="ignore",
    )

    public_url = None

    for line in process.stdout:
        print(line, end="")

        match = re.search(r"https://[-a-zA-Z0-9]+\.trycloudflare\.com", line)
        if match:
            public_url = match.group(0)
            print("\nCloudflare Tunnel URL:", public_url)
            break

    if not public_url:
        process.terminate()
        raise RuntimeError("Cloudflare Tunnel URL을 찾지 못했습니다.")

    return process, public_url


if __name__ == "__main__":
    process, url = start_cloudflare_tunnel()

    print("\nColab BACKEND_URL 에 아래 주소를 넣으세요:")
    print(url)

    try:
        process.wait()
    except KeyboardInterrupt:
        print("\nCloudflare Tunnel 종료")
        process.terminate()
        sys.exit(0)
