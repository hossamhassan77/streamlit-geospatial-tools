import subprocess
import sys

with open("requirements.txt") as f:
    packages = [line.strip() for line in f if line.strip() and not line.startswith("#")]

failed = []

for package in packages:
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", package],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"❌ FAILED: {package}")
        failed.append(package)
    else:
        print(f"✅ OK: {package}")

if failed:
    print("\n--- Failed packages ---")
    for p in failed:
        print(f"  {p}")