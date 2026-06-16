"""Install the project requirements with the active Python interpreter."""

import subprocess
import sys


def main() -> int:
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
        check=False,
    )
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
