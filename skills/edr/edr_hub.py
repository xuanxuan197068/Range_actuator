#!/usr/bin/env python3
# edr_hub: 汇聚内网 EDR agent 事件(UDP 1514) → 落盘 + 计数 + 转发 T-Pot HQ(UDP 514)
import socket, threading, time, os, json
LOG = "/var/log/edr/events.log"
os.makedirs("/var/log/edr", exist_ok=True)
STAT = "/opt/edr-hub/stats.json"
TPOT = os.environ.get("TPOT_ADDR", "10.0.249.4")
c = {"events": 0, "hosts": {}}
lock = threading.Lock()
fwd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
def loop():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("0.0.0.0", 1514))
    while True:
        d, a = s.recvfrom(65535)
        host = a[0]
        line = "%s %s" % (time.strftime("%Y-%m-%dT%H:%M:%S"), d.decode("utf-8", "replace").strip()[:1200])
        with lock:
            c["events"] += 1
            c["hosts"][host] = c["hosts"].get(host, 0) + 1
            with open(LOG, "a") as f:
                f.write(line + "\n")
        try:
            fwd.sendto(("<13>EDR-HUB " + line).encode(), (TPOT, 514))
        except Exception:
            pass
def stat():
    while True:
        os.makedirs("/opt/edr-hub", exist_ok=True)
        with lock:
            snap = dict(c)
        with open(STAT, "w") as f:
            json.dump({"ts": time.strftime("%F %T"), **snap}, f)
        time.sleep(20)
threading.Thread(target=loop, daemon=True).start()
threading.Thread(target=stat, daemon=True).start()
while True:
    time.sleep(3600)
