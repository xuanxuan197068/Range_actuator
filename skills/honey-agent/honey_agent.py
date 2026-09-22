#!/usr/bin/env python3
# honey_agent: 纯 stdlib 多协议中低交互蜜罐（免 Docker），连接/凭据捕获 → syslog 域 T-Pot:514
# conf: /opt/honey/conf.json  [{"proto":"ssh","port":2222},...]  变更后 systemctl restart honey
import socket, threading, time, json, os, sys, base64

CONF = "/opt/honey/conf.json"
TPOT = os.environ.get("TPOT_ADDR", "10.0.249.4")
SELF = "0.0.0.0"
try:
    import subprocess
    SELF = subprocess.run(["hostname", "-I"], capture_output=True, text=True).stdout.split()[0]
except Exception:
    pass

udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def report(proto, port, src, event, extra=""):
    try:
        udp.sendto(("<13>HONEY host=%s proto=%s dport=%s src=%s event=%s %s"
                    % (SELF, proto, port, src, event, extra)).encode()[:900], (TPOT, 514))
    except Exception:
        pass

BANNERS = {
    "ssh": b"SSH-2.0-OpenSSH_7.4\r\n",
    "http": b"",
    "telnet": b"\xff\xfd\x01\xff\xfd\x03Welcome to router management\r\nLogin: ",
    "ftp": b"220 vsFTPd 3.0.3 ready\r\n",
    "mysql": b"",  # mysql needs greeting packet; simplified raw accept
    "redis": b"",
}

def honeypot_session(proto, port, c, addr):
    try:
        c.settimeout(20)
        if BANNERS.get(proto):
            try:
                c.sendall(BANNERS[proto])
            except Exception:
                return
        report(proto, port, addr[0], "connect")
        buf = b""
        while True:
            try:
                d = c.recv(2048)
            except Exception:
                break
            if not d:
                break
            buf += d
            if proto == "http":
                head = buf.split(b"\r\n")[0].decode("utf-8", "replace")
                report(proto, port, addr[0], "http", head[:120])
                try:
                    c.sendall(b"HTTP/1.1 200 OK\r\nContent-Length: 5\r\n\r\nhello")
                except Exception:
                    pass
                break
            elif proto in ("telnet", "ftp"):
                line = buf.decode("utf-8", "replace").strip()
                if line:
                    report(proto, port, addr[0], "cred", "input=" + line[:80])
                    buf = b""
                    if proto == "ftp" and line.upper().startswith("USER"):
                        try: c.sendall(b"331 Please specify the password.\r\n")
                        except Exception: pass
                    elif proto == "ftp":
                        try: c.sendall(b"530 Login incorrect.\r\n")
                        except Exception: pass
            elif proto == "ssh":
                report(proto, port, addr[0], "ssh-client-version", buf.split(b"\r")[0].decode("utf-8", "replace")[:60])
                # 简化：不实现完整握手，抓取客户端版本即可
                break
            elif proto == "mysql":
                report(proto, port, addr[0], "mysql-client-packet", base64.b64encode(buf[:40]).decode()[:60])
                break
            elif proto == "redis":
                cmds = buf.decode("utf-8", "replace").strip().split("\r\n")
                report(proto, port, addr[0], "redis-cmd", " ".join(x for x in cmds if not x.startswith("$"))[:100])
                try: c.sendall(b"+OK\r\n")
                except Exception: pass
                buf = b""
    except Exception:
        pass
    finally:
        try: c.close()
        except Exception: pass

def serve(proto, port):
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.bind(("0.0.0.0", int(port)))
    except Exception as e:
        report(proto, port, SELF, "bind-fail", str(e)[:60])
        return
    s.listen(16)
    while True:
        c, a = s.accept()
        threading.Thread(target=honeypot_session, args=(proto, port, c, a), daemon=True).start()

def load_conf():
    try:
        with open(CONF) as f:
            return json.load(f)
    except Exception:
        return []

if __name__ == "__main__":
    seen = set()
    while True:
        conf = load_conf()
        for item in conf:
            key = (item.get("proto"), int(item.get("port", 0)))
            if key in seen:
                continue
            seen.add(key)
            threading.Thread(target=serve, args=key, daemon=True).start()
            report(key[0], key[1], SELF, "honeypot-up")
        time.sleep(10)
