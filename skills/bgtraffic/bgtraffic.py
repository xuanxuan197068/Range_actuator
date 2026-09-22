#!/usr/bin/env python3
# bgtraffic: 随机业务背景流量发生器（零依赖）
import random, time, urllib.request, socket, urllib.error
TARGETS = [
    ("http://10.1.2.3:8888/api", "GET", None),
    ("http://10.1.2.2:5601/api/status", "GET", None),
    ("http://10.1.1.7/", "GET", None),
    ("http://10.1.1.7:8088/", "GET", None),
    ("http://10.1.1.7:8180/logincheck.php", "GET", None),
    ("http://10.1.1.10:6379", "RAW", None),
    ("http://10.1.1.4:3306", "RAW", None),
]
UAS = ["Mozilla/5.0 (WinNT; Office)", "gov-client/2.1", "Mozilla/5.0 backup-agent", "curl/7.68"]
def hit_http(u):
    req = urllib.request.Request(u, headers={"User-Agent": random.choice(UAS)})
    urllib.request.urlopen(req, timeout=5)
def hit_raw(hostport):
    host, port = hostport.split("//")[1].split(":")
    s = socket.create_connection((host, int(port)), timeout=4)
    s.sendall(b"PING\r\n" if port == "6379" else b"")
    s.close()
def main():
    while True:
        t = random.choice(TARGETS)
        try:
            if t[1] == "RAW":
                hit_raw(t[0])
            else:
                hit_http(t[0])
        except Exception:
            pass
        time.sleep(random.uniform(30, 180))
if __name__ == "__main__":
    main()
