#!/usr/bin/env python3
# secbridge v2: 安全设备日志桥 —— UDP514 + 8100双协议(HTTP/syslog) → 落盘+计数+转发 T-Pot(UDP514+TCP1514)
import socket, threading, time, os, json

TPOT = os.environ.get("TPOT_ADDR", "127.0.0.1")
LOGDIR = "/var/log/seclog"
os.makedirs(LOGDIR, exist_ok=True)
STATS = "/opt/secbridge/stats.json"
counters = {"udp": 0, "fwd_ok": 0, "fwd_tcp": 0, "sources": {}}
lock = threading.Lock()
NL = bytes([10])

def handle(src_ip, data):
    ts = time.strftime("%Y-%m-%dT%H:%M:%S")
    line = "%s %s" % (ts, data.decode("utf-8", "replace").strip()[:1500])
    with lock:
        counters["udp"] += 1
        counters["sources"][src_ip] = counters["sources"].get(src_ip, 0) + 1
        try:
            with open(os.path.join(LOGDIR, src_ip.replace(":", "_") + ".log"), "a") as f:
                f.write(line + "\n")
        except Exception:
            pass
    try:
        fw = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        fw.sendto(data, (TPOT, 514))
        fw.close()
        with lock:
            counters["fwd_ok"] += 1
    except Exception:
        pass
    try:
        tc = socket.create_connection((TPOT, 1514), timeout=3)
        tc.sendall(data if data.endswith(NL) else data + NL)
        tc.close()
        with lock:
            counters["fwd_tcp"] += 1
    except Exception:
        pass

def udp_loop(port=514):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("0.0.0.0", port))
    while True:
        d, a = s.recvfrom(65535)
        handle(a[0], d)

def port8100_loop():
    hs = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    hs.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    hs.bind(("0.0.0.0", 8100))
    hs.listen(8)
    while True:
        c, a = hs.accept()

        def h(c=c, a=a):
            try:
                c.settimeout(3)
                buf = b""
                while True:
                    try:
                        d = c.recv(65535)
                    except Exception:
                        break
                    if not d:
                        break
                    buf += d
                    while NL in buf:
                        line, buf = buf.split(NL, 1)
                        ls_ = line.strip()
                        if ls_.startswith(b"GET") or ls_.startswith(b"POST") or ls_.startswith(b"HEAD"):
                            with lock:
                                body = json.dumps({"ts": time.strftime("%F %T"), "tpot": TPOT,
                                                   **counters}, indent=1).encode()
                            try:
                                resp = b"HTTP/1.0 200 OK" + bytes([13, 10]) + \
                                       b"Content-Type: application/json" + bytes([13, 10, 13, 10]) + body
                                c.sendall(resp)
                            except Exception:
                                pass
                        elif ls_:
                            handle(a[0], line)
                rest = buf.strip()
                if rest and not rest.startswith(b"GET"):
                    handle(a[0], buf)
            except Exception:
                pass
            finally:
                c.close()

        threading.Thread(target=h, daemon=True).start()

def stat_loop():
    while True:
        os.makedirs("/opt/secbridge", exist_ok=True)
        with lock:
            snap = dict(counters)
        with open(STATS, "w") as f:
            json.dump({"ts": time.strftime("%F %T"), "tpot": TPOT, **snap}, f)
        time.sleep(20)

for t in (udp_loop, lambda: udp_loop(8100), port8100_loop, stat_loop):
    threading.Thread(target=t, daemon=True).start()
while True:
    time.sleep(3600)
