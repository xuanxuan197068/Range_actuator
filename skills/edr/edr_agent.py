#!/usr/bin/env python3
# edr_agent: 内网主机 EDR 探针 —— 心跳(45-90s) + auth.log 增量上报 → hub 10.0.1.8:1514
import socket, time, subprocess, os, random

HUB = ("10.0.1.8", 1514)
HOST = socket.gethostname()
IP = subprocess.run(["hostname", "-I"], capture_output=True, text=True).stdout.split()[0] if subprocess.run(["hostname", "-I"], capture_output=True, text=True).stdout.strip() else "0.0.0.0"
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def send(prio, msg):
    try:
        s.sendto(("<%d>EDR host=%s ip=%s %s" % (prio, HOST, IP, msg)).encode(), HUB)
    except Exception:
        pass

def heartbeat():
    send(14, "type=heartbeat alive=1")

def auth_tail():
    path = "/var/log/auth.log"
    if not os.path.exists(path):
        path = "/var/log/secure"
    if not os.path.exists(path):
        return None, 0
    size = os.path.getsize(path)
    return path, size

last_path, last_size = auth_tail()
heartbeat()
while True:
    time.sleep(random.uniform(45, 90))
    try:
        p, cur = auth_tail()
        if p and p == last_path and cur > last_size:
            with open(p, "r", errors="replace") as f:
                f.seek(last_size)
                for i, line in enumerate(f):
                    if i >= 20:
                        break
                    if "Failed password" in line or "Accepted" in line or "sudo:" in line or "session opened" in line:
                        send(11, "type=auth " + line.strip()[:300])
            last_size = cur
        elif p != last_path:
            last_path, last_size = p, cur
        heartbeat()
    except Exception as e:
        send(11, "type=agent_error " + str(e)[:120])
