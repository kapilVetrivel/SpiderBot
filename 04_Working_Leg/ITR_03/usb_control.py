# usb_control.py
import os
import sys

HUB_ID = "1-1"
UNBIND_PATH = "/sys/bus/usb/drivers/usb/unbind"
BIND_PATH = "/sys/bus/usb/drivers/usb/bind"


def has_root():
    return os.geteuid() == 0


def write_sysfs(path: str, value: str):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Path does not exist: {path}")
    with open(path, "w", encoding="utf-8") as f:
        f.write(value)


def usb_disable():
    write_sysfs(UNBIND_PATH, HUB_ID)


def usb_enable():
    write_sysfs(BIND_PATH, HUB_ID)


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ("on", "off"):
        print("Usage: sudo python3 usb_control.py [on|off]")
        sys.exit(1)

    if not has_root():
        print("This script must be run as root (sudo).")
        sys.exit(1)

    try:
        if sys.argv[1] == "off":
            usb_disable()
            print("USB ports disabled")
        else:
            usb_enable()
            print("USB ports enabled")
    except FileNotFoundError as e:
        print(f"File path error: {e}")
        sys.exit(1)
    except PermissionError as e:
        print(f"Permission denied: {e}")
        sys.exit(1)
    except OSError as e:
        print(f"Failed to write sysfs entry: {e}")
        sys.exit(1)


if __name__ == "__main__":
    usb_disable()
