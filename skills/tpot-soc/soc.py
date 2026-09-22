#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TPot-SOC: 集成安全管理端（EDR/蜜罐/WAF 覆盖+捕获+漏洞关联+防御策略开关）
纯 stdlib。监听: syslog UDP514/TCP514/TCP1514 + Web :80
env: DOMAIN(hq|fya|bc|cd) FORWARD_TO(可选,UDP转发) JUMP_IP JUMP_USER JUMP_PASS
"""
import socket, socketserver, threading, time, os, re, json, sqlite3, subprocess

BASE = "/opt/soc"
DB = BASE + "/soc.db"
DOMAIN = os.environ.get("DOMAIN", "hq")
FORWARD_TO = os.environ.get("FORWARD_TO", "")
JUMP_IP = os.environ.get("JUMP_IP", "")
JUMP_USER = os.environ.get("JUMP_USER", "user")
JUMP_PASS = os.environ.get("JUMP_PASS", "gzhu@20260225")
WEB_PORT = int(os.environ.get("WEB_PORT", "80"))
ATTACKER_RE = re.compile(r"^10\.\d+\.254\.100$")

VULN_MAP = {
 ("10.6.2.2",7001):("WebLogic wls-wsat 反序列化 RCE","CVE-2017-10271"),
 ("10.0.2.3",8090):("Fastjson 反序列化 RCE","autoType bypass"),
 ("10.1.2.3",8888):("Jupyter Notebook 未授权（内核执行）","CWE-306"),
 ("10.1.2.3",6379):("Redis 未授权访问","CWE-306"),
 ("10.1.1.10",6379):("Redis 未授权写 authorized_keys","CWE-306"),
 ("10.6.1.6",445):("Samba 远程代码执行(SambaCry)","CVE-2017-7494"),
 ("10.3.1.3",80):("DokuWiki ACL 绕过/任意文件上传","CWE-862"),
 ("10.3.1.3",3000):("RocketChat API 滥用","CWE-284"),
 ("10.3.2.2",8080):("Spring Boot Actuator 泄露","CWE-200"),
 ("10.3.1.14",6443):("K3s API 匿名访问","CWE-306"),
 ("10.3.1.12",2375):("Docker API 未授权(容器逃逸)","CWE-306"),
 ("10.1.1.7",8180):("通达OA 未授权访问/RCE","CWE-306"),
 ("10.1.1.8",3306):("MySQL-UDF 提权","CWE-250"),
 ("10.0.1.6",1521):("Oracle TNS 弱口令/提权","CWE-522"),
 ("10.6.1.7",8929):("GitLab 未授权API/Token泄露","CWE-200"),
 ("10.6.1.4",80):("phpMyAdmin 弱口令","CWE-522"),
 ("10.3.1.9",8081):("D-Link 信息泄露/未授权","CWE-200"),
 ("10.3.1.9",8082):("雄迈 DVR 未授权视频流","CWE-306"),
 ("10.6.1.3",1433):("MSSQL sa 弱口令","CWE-522"),
 ("10.1.1.2",445):("域控 SMB(PT-Hash/委派滥用)","CWE-284"),
}
HP_PORT_SVC = {22:"SSH",80:"HTTP",445:"SMB",3306:"MySQL",3389:"RDP",8080:"HTTP",6379:"Redis",1521:"Oracle"}

os.makedirs(BASE, exist_ok=True)
os.makedirs("/var/log/tpot", exist_ok=True)
db = sqlite3.connect(DB, check_same_thread=False)
db.execute("CREATE TABLE IF NOT EXISTS ev(ts TEXT, cat TEXT, src TEXT, dst TEXT, port TEXT, vuln TEXT, cve TEXT, raw TEXT)")
db.execute("CREATE TABLE IF NOT EXISTS alerts(id INTEGER PRIMARY KEY AUTOINCREMENT, level TEXT, msg TEXT, ts TEXT DEFAULT (datetime('now','localtime')))")
db.execute("CREATE INDEX IF NOT EXISTS idx_ev_cat ON ev(cat)")
db.execute("CREATE INDEX IF NOT EXISTS idx_ev_ts ON ev(ts)")
db.execute("CREATE TABLE IF NOT EXISTS edr(ip TEXT PRIMARY KEY, host TEXT, last TEXT, n INTEGER)")
db.execute("CREATE TABLE IF NOT EXISTS hp(ip TEXT PRIMARY KEY, host TEXT, kind TEXT, last TEXT, n INTEGER)")
db.commit()
lock = threading.Lock()


HP_LIST = {
 "hq":  ["10.0.1.200","10.0.1.201","10.0.1.202","10.0.10.200","10.0.10.201","10.0.10.202"],
 "fya": ["10.1.1.200","10.1.1.201","10.1.1.202","10.1.10.200","10.1.10.201","10.1.10.202"],
 "bc":  ["10.6.1.200","10.6.1.201","10.6.1.202","10.6.10.200","10.6.10.201","10.6.10.202"],
 "cd":  ["10.3.1.200","10.3.1.201","10.3.1.202","10.3.10.200","10.3.10.201","10.3.10.202"],
}
HP_PORTS = [22,80,445,3306,3389,8080]

def prober():
    while True:
        for ip in HP_LIST.get(DOMAIN, []):
            open_ports = []
            for p in HP_PORTS:
                try:
                    s_ = socket.create_connection((ip, p), timeout=1.2)
                    open_ports.append(str(p)); s_.close()
                except Exception:
                    pass
            state = "在线(" + ",".join(open_ports) + ")" if open_ports else "不可达"
            with lock:
                db.execute("INSERT INTO hp(ip,host,kind,last,n) VALUES(?,?,?,?,1) "
                           "ON CONFLICT(ip) DO UPDATE SET last=?,kind=?,host=?",
                           (ip, ip, state, now(), now(), state, state, state))
                db.commit()
        time.sleep(60)

def now(): return time.strftime("%Y-%m-%dT%H:%M:%S")

def classify(src, data):
    s = data.decode("utf-8", "replace")
    with lock:
        if "EDR host=" in s:
            m = re.search(r"host=([^\s]+)", s)
            hname = m.group(1) if m else src
            db.execute("INSERT INTO ev VALUES(?,?,?,?,?,?,?,?)", (now(),"edr",src,"","","","",s[:600]))
            db.execute("INSERT INTO edr(ip,host,last,n) VALUES(?,?,?,1) ON CONFLICT(ip) DO UPDATE SET last=?,n=n+1,host=?",
                       (hname, hname, now(), now(), hname))
        elif "HP-CONN" in s or "HP-WIN" in s:
            hpip = (re.search(r"hp=(\S+)", s) or re.search(r"host=([\d.]+)", s) or [None,src])[1] if (re.search(r"hp=(\S+)", s) or re.search(r"host=([\d.]+)", s)) else src
            m = re.search(r"src=([\d.]+)", s); p = re.search(r"dport=(\d+)", s)
            cap_src = m.group(1) if m else src
            dport = p.group(1) if p else ""
            attacker = "是" if ATTACKER_RE.match(cap_src) else "否"
            vuln = HP_PORT_SVC.get(int(dport), "") if dport.isdigit() else ""
            db.execute("INSERT INTO ev VALUES(?,?,?,?,?,?,?,?)", (now(),"hp",cap_src,hpip,dport,("攻击捕获("+attacker+")" if attacker=="是" else "连接记录"),vuln,s[:600]))
            db.execute("INSERT INTO hp(ip,host,kind,last,n) VALUES(?,?,?,?,1) ON CONFLICT(ip) DO UPDATE SET last=?,kind=?",
                       (hpip,hpip,"sensor",now(),now(),"sensor"))
        elif "EDGE-IN-5" in s or "PROTECT-MODE" in s:
            sp = re.search(r"SRC=((?:\d{1,3}\.){3}\d{1,3})", s)
            dp = re.search(r"DST=((?:\d{1,3}\.){3}\d{1,3})", s)
            pt = re.search(r"DPT=(\d+)", s)
            dip = dp.group(1) if dp else ""
            dport = pt.group(1) if pt else ""
            src = sp.group(1) if sp else src
            vm = VULN_MAP.get((dip, int(dport))) if (dip and dport.isdigit()) else None
            db.execute("INSERT INTO ev VALUES(?,?,?,?,?,?,?,?)",
                (now(),"block",src,dip,dport,(vm[0] if vm else "未知攻击"),(vm[1] if vm else ""),s[:600]))
        elif "HONEY" in s:
            mh = re.search(r"host=([^\s]+)", s)
            hpip = mh.group(1) if mh else src
            m = re.search(r"src=([^\s]+)", s)
            pm = re.search(r"proto=([^\s]+)", s)
            em_ = re.search(r"event=([^\s]+)", s)
            dp = re.search(r"dport=(\d+)", s)
            cap_src = m.group(1) if m else src
            proto = pm.group(1) if pm else ""
            evt = em_.group(1) if em_ else ""
            dport = dp.group(1) if dp else ""
            vuln = "蜜罐上线" if evt == "honeypot-up" else "蜜罐诱捕(%s/%s)" % (proto, evt)
            db.execute("INSERT INTO ev VALUES(?,?,?,?,?,?,?,?)",
                (now(),"honey",cap_src,hpip,dport,vuln,proto,s[:600]))
            db.execute("INSERT INTO hp(ip,host,kind,last,n) VALUES(?,?,?,?,1) "
                       "ON CONFLICT(ip) DO UPDATE SET last=?,kind=?",
                       (hpip, hpip, "动态蜜罐", now(), now(), "动态蜜罐"))
        else:
            db.execute("INSERT INTO ev VALUES(?,?,?,?,?,?,?,?)", (now(),"syslog",src,"","","","",s[:600]))
        db.commit()

def alert_engine():
    """每 30s 巡检：拦截速率突变 / 蜜罐凭据捕获 / EDR 心跳丢失 → alerts 表 + 顶部横幅"""
    last_block = 0
    last_hosts = {}
    while True:
        try:
            n_blk = q("SELECT COUNT(*) FROM ev WHERE cat='block'")[0][0]
            if n_blk - last_block > 20:
                with lock:
                    db.execute("INSERT INTO alerts(level,msg) VALUES('high',?)",
                               ("拦截速率突变：30 秒内新增 %d 次拦截" % (n_blk - last_block),))
                    db.commit()
            last_block = n_blk
            cred = q("SELECT COUNT(*) FROM ev WHERE cat='honey' AND vuln LIKE '%cred%'")[0][0]
            if cred > 0 and q("SELECT COUNT(*) FROM alerts WHERE msg LIKE '%凭据%'")[0][0] == 0:
                with lock:
                    db.execute("INSERT INTO alerts(level,msg) VALUES('high',?)",
                               ("蜜罐捕获到攻击者提交的凭据（%d 条）——高度可疑" % cred,))
                    db.commit()
            cur_hosts = {r[0]: r[1] for r in q("SELECT host,last FROM edr")}
            for h, last in cur_hosts.items():
                if h in last_hosts and last == last_hosts[h] and h != "gzhu":
                    if q("SELECT COUNT(*) FROM alerts WHERE msg LIKE ?", ("%" + h + "%",))[0][0] == 0:
                        with lock:
                            db.execute("INSERT INTO alerts(level,msg) VALUES('mid',?)",
                                       ("EDR 心跳丢失:" + h + "（最后：" + last + "）",))
                            db.commit()
            last_hosts = cur_hosts
        except Exception:
            pass
        time.sleep(30)

def collector():
    def udp_l():
        sk = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sk.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sk.bind(("0.0.0.0", 514))
        while True:
            d, a = sk.recvfrom(65535)
            handle(a[0], d)
    def handle(src, d):
        classify(src, d)
        with open("/var/log/tpot/security.log", "a") as f:
            f.write("%s %s %s\n" % (now(), src, d.decode("utf-8","replace")[:1200]))
        if FORWARD_TO:
            try:
                socket.getaddrinfo
                fw = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                fw.sendto(d, (FORWARD_TO, 514))
            except Exception:
                pass
    def tcp_l(port):
        sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sk.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sk.bind(("0.0.0.0", port)); sk.listen(16)
        while True:
            c, a = sk.accept()
            def h(c=c, a=a):
                buf = b""
                try:
                    while True:
                        d = c.recv(65535)
                        if not d: break
                        buf += d
                        while bytes([10]) in buf:
                            line, buf = buf.split(bytes([10]), 1)
                            if line.strip():
                                handle(a[0], line)
                except Exception: pass
                finally: c.close()
            threading.Thread(target=h, daemon=True).start()
    for t in (udp_l, lambda: tcp_l(514), lambda: tcp_l(1514), prober):
        threading.Thread(target=t, daemon=True).start()

def q(sql, args=()):
    with lock:
        return db.execute(sql, args).fetchall()

PAGE = """<!doctype html><html><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>TPot-SOC __D1__</title><style>
:root{--bg:#0b1220;--card:#131e31;--txt:#e8eefb;--mut:#8fa3c0;--acc:#4cc2ff;--ok:#3ddc84;--bad:#ff6b6b;--warn:#ffc861;--line:#24344f}
*{box-sizing:border-box}body{font-family:system-ui,"Segoe UI","Microsoft YaHei",sans-serif;margin:0;background:var(--bg);color:var(--txt)}
nav{background:linear-gradient(90deg,#0a3d62,#1e3a8a 60%,#3b1e8a);padding:12px 24px;display:flex;align-items:center;flex-wrap:wrap;gap:8px;position:sticky;top:0;z-index:99;box-shadow:0 2px 14px #000a}
nav b{font-size:19px;color:#fff;margin-right:14px;letter-spacing:.5px}
nav a{color:#a9d6ff;text-decoration:none;font-weight:600;padding:7px 13px;border-radius:9px;font-size:14.5px}
nav a:hover{background:#ffffff1e}
.domswitch{margin-left:auto;display:flex;gap:4px;background:#0a1526;padding:3px;border-radius:10px;border:1px solid var(--line)}
.domswitch a{padding:5px 12px;font-size:13px;border-radius:7px}
.domswitch a.cur{background:#2f6fed;color:#fff}
.wrap{max-width:1220px;margin:0 auto;padding:10px 16px 60px}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px 20px;margin:14px 0;box-shadow:0 4px 18px #0005}
h2{margin:2px 0 12px;font-size:16.5px;color:#7dd3fc;border-left:4px solid var(--acc);padding-left:10px}
table{border-collapse:collapse;width:100%}
th,td{border:1px solid var(--line);padding:7px 10px;font-size:13.2px;text-align:left;vertical-align:top}
th{background:#12365e;color:#fff;font-weight:600;position:sticky;top:52px}
tr:nth-child(even){background:#ffffff07}
tr.ev{cursor:pointer}tr.ev:hover{background:#4cc2ff18}
.btn{padding:8px 16px;border:0;border-radius:9px;color:#fff;cursor:pointer;font-size:13.5px;font-weight:700;transition:.15s}
.btn:disabled{opacity:.45;cursor:wait}
.on{background:linear-gradient(135deg,#16a34a,#22c55e)}.off{background:linear-gradient(135deg,#dc2626,#ef4444)}
.blue{background:linear-gradient(135deg,#2563eb,#3b82f6)}.warn{background:linear-gradient(135deg,#d97706,#f59e0b)}
.small{color:var(--mut);font-size:12px}
.badge{display:inline-block;padding:2.5px 10px;border-radius:99px;font-size:11.5px;font-weight:700}
.b-ok{background:#0d3b21;color:#6ee7a0}.b-bad{background:#4c1113;color:#fda4a4}.b-warn{background:#4a3208;color:#fcd34d}.b-info{background:#0c334d;color:#7dd3fc}.b-mid{background:#3b2350;color:#d8b4fe}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px}
.kpi{background:linear-gradient(145deg,#16233a,#0d1830);border:1px solid var(--line);border-radius:14px;padding:15px;text-align:center;cursor:pointer;transition:.15s}
.kpi:hover{border-color:var(--acc)}
.kpi .n{font-size:32px;font-weight:800;color:var(--acc)}
.kpi .t{color:var(--mut);font-size:12.5px;margin-top:3px}
pre{background:#070d18;border:1px solid var(--line);border-radius:10px;padding:12px;overflow:auto;font-size:12px;color:#9deaf7;white-space:pre-wrap}
input,select{background:#0a1526;border:1px solid var(--line);color:var(--txt);border-radius:8px;padding:8px 10px;font-size:13.5px;margin:3px}
input:focus{outline:2px solid var(--acc)}
form{display:inline}
.alertbar{background:linear-gradient(90deg,#7f1d1d,#b91c1c);color:#fff;padding:10px 18px;border-radius:12px;margin:12px 0;font-weight:600;cursor:pointer}
.alertbar.mid{background:linear-gradient(90deg,#78350f,#b45309)}
.detail{background:#0a1526;border-left:3px solid var(--acc);padding:10px 14px;margin:4px 0;border-radius:0 10px 10px 0}
.detail table th{position:static}
.chain-cell{padding:10px;text-align:center;border:1px solid var(--line)}
.spark{display:flex;align-items:flex-end;gap:2px;height:60px}
.spark div{background:linear-gradient(180deg,#4cc2ff,#1d4ed8);border-radius:2px 2px 0 0;min-width:6px;flex:1}
.bar-row{display:flex;align-items:center;gap:8px;margin:5px 0}
.bar-label{width:230px;font-size:12.5px;color:var(--mut);text-align:right;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.bar-val{height:20px;background:linear-gradient(90deg,#f97316,#ef4444);border-radius:4px;min-width:24px;display:flex;align-items:center;padding:0 7px;font-size:11.5px;font-weight:700;color:#fff}
#toast{position:fixed;bottom:24px;right:24px;background:#12365e;color:#fff;padding:13px 22px;border-radius:12px;box-shadow:0 6px 24px #000c;display:none;z-index:999;font-weight:600;border:1px solid #4cc2ff66}
.spin{display:inline-block;width:14px;height:14px;border:2.5px solid #fff5;border-top-color:#fff;border-radius:50%;animation:sp .7s linear infinite;vertical-align:-2px;margin-right:6px}
@keyframes sp{to{transform:rotate(360deg)}}
</style></head><body>
<nav><b>🛡 TPot-SOC</b>
<a href="/">总览</a><a href="/edr">EDR</a><a href="/hp">蜜罐</a><a href="/honey">动态蜜罐</a><a href="/waf">WAF</a><a href="/chains">攻防态势</a><a href="/bots">流量机器人</a><a href="/policy">防御策略</a>
<span class=domswitch>__DOMS__</span>
</nav><div class=wrap>__BODY__</div>
<div id=toast></div>
<script>
function toast(m,ok){var t=document.getElementById('toast');t.textContent=m;t.style.display='block';t.style.background=ok===false?'#7f1d1d':'#12365e';setTimeout(()=>t.style.display='none',3800)}
function api(url,body,btn){if(btn){btn.disabled=true;btn.innerHTML='<span class=spin></span>执行中'}
 fetch(url,{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:body})
 .then(r=>r.text()).then(t=>{var ok=t.indexOf('失败')<0&&t.indexOf('FAIL')<0;toast(t.replace(/<[^>]+>/g,'').split('\n')[0].slice(0,120)||'完成',ok);if(btn){btn.disabled=false;btn.innerText=btn.dataset.orig;if(ok)setTimeout(()=>location.reload(),900)}})
 .catch(e=>{toast('网络错误:'+e,false);if(btn){btn.disabled=false;btn.innerText=btn.dataset.orig}})}
function toggle(dom,btn){btn.dataset.orig=btn.innerText;if(!confirm('确认切换 '+dom+' 的防御策略？\n演练模式将放行攻击机流量'))return;api('/api/policy?domain='+dom,'x=1',btn)}
function policyAll(act,btn){btn.dataset.orig=btn.innerText;if(!confirm(act==='allow'?'⚠ 全部放行=全域进入演练模式，确认？':'全部拦截=全域恢复防御，确认？'))return;api('/api/policy-all','act='+act,btn)}
function banIP(src,btn){btn.dataset.orig=btn.innerText;if(!confirm('一键封禁源 '+src+'（写入边界 reject 规则，24h 后需手动解除）'))return;api('/api/ban','src='+encodeURIComponent(src),btn)}
function honeyGo(f,btn){var b=new URLSearchParams(new FormData(f)).toString();btn.dataset.orig=btn.innerText;api('/api/honey',b,btn)}
function honeyDel(ip,proto,port,btn){btn.dataset.orig='下线';api('/api/honey','ip='+ip+'&proto='+proto+'&port='+port+'&act=remove',btn)}
function honeyDelete(f,btn){var b=new URLSearchParams(new FormData(f)).toString();btn.dataset.orig=btn.innerText;api('/api/honey',b,btn)}
function ruleGo(f,btn){var b=new URLSearchParams(new FormData(f)).toString();btn.dataset.orig=btn.innerText;api('/api/rules',b,btn)}
function ruleDel(f,btn){var b=new URLSearchParams(new FormData(f)).toString();btn.dataset.orig=btn.innerText;api('/api/rules',b,btn)}
function toggleDetail(id){var d=document.getElementById(id);d.style.display=d.style.display==='none'?'':'none'}
function ackAlert(id){api('/api/alert-ack','id='+id,null)}
function botAdd(f,btn){var b=new URLSearchParams(new FormData(f)).toString();b+='&act=add';btn.dataset.orig=btn.innerText;api('/api/bots',b,btn)}
function botGo(ip,state,btn){btn.dataset.orig=btn.innerText;api('/api/bots','ip='+ip+'&state='+state+'&act=ctl',btn)}
</script></body></html>"""

def badge(txt):
    cls = "b-ok" if txt in ("直接在线", "protect", "在线") else ("b-warn" if txt in ("经桥在线", "allow") else "b-bad")
    return '<span class="badge %s">%s</span>' % (cls, txt)

def kpi(n, t, link="#"):
    return '<div class=kpi onclick="location=\'%s\'"><div class=n>%s</div><div class=t>%s</div></div>' % (link, n, t)

def timeline_svg(hours=24):
    """24h 攻击时间线：每小时 block+honey 计数 → SVG 柱状"""
    rows = q("SELECT substr(ts,1,13) h, COUNT(*) FROM ev WHERE cat IN ('block','honey') AND ts >= datetime('now','localtime','-%d hours') GROUP BY h" % hours)
    m = {r[0]: r[1] for r in rows}
    import datetime as _dt
    now_ = _dt.datetime.now()
    bars = []
    for i in range(hours - 1, -1, -1):
        hh = (now_ - _dt.timedelta(hours=i)).strftime("%Y-%m-%dT%H")
        v = m.get(hh, 0)
        bars.append((hh[-2:] + "时", v))
    mx = max([v for _, v in bars] + [1])
    W, H, GAP = 1150, 110, 2.5
    bw = (W - GAP * len(bars)) / len(bars)
    parts = ['<svg viewBox="0 0 %d %d" style="width:100%%;background:#0a1526;border-radius:10px;border:1px solid #24344f">' % (W, H)]
    for i, (lab, v) in enumerate(bars):
        h = int(v / mx * (H - 34)) if v else 1
        x = i * (bw + GAP)
        parts.append('<rect x="%.1f" y="%d" width="%.1f" height="%d" rx="2" fill="%s"><title>%s · %d 次</title></rect>'
                     % (x, H - 22 - h, bw, h, "#ef4444" if v > mx * 0.5 else "#4cc2ff", lab, v))
        if i % 3 == 0:
            parts.append('<text x="%.1f" y="%d" fill="#8fa3c0" font-size="10" text-anchor="middle">%s</text>' % (x + bw / 2, H - 8, lab))
    parts.append("</svg>")
    return "".join(parts)

def topbar_chart(limit=8):
    """命中漏洞 TOP 横向条形图（HTML div 实现）"""
    rows = q("SELECT vuln, cve, COUNT(*) c FROM ev WHERE cat='block' GROUP BY vuln, cve ORDER BY c DESC LIMIT %d" % limit)
    if not rows:
        return '<p class=small>暂无拦截数据</p>'
    mx = rows[0][2]
    out = []
    for v, cve, c in rows:
        label = (v + (" [" + cve + "]" if cve else ""))[:36]
        w = max(int(c / mx * 420), 26)
        out.append('<div class=bar-row><div class=bar-label title="%s">%s</div><div class=bar-val style="width:%dpx">%d</div></div>' % (label, label, w, c))
    return "".join(out)

def src_profile(src_ip):
    """源 IP 画像"""
    n = q("SELECT COUNT(*) FROM ev WHERE src=? AND cat='block'", (src_ip,))[0][0]
    tg = q("SELECT DISTINCT dst || ':' || port FROM ev WHERE src=? AND cat='block' LIMIT 12", (src_ip,))
    hn = q("SELECT COUNT(*) FROM ev WHERE src=? AND cat='honey'", (src_ip,))[0][0]
    return n, tg, hn

def ev_rows_with_detail(rows, idx=0):
    """事件行 + 点击展开下钻（原始日志+画像+封禁按钮）"""
    out = []
    for i, r in enumerate(rows):
        ts, cat, src, dst, port, vuln = r
        if cat == "honey" and "上线" in str(vuln):
            continue
        detail_id = "d%d" % (idx + i)
        raw_row = q("SELECT raw FROM ev WHERE ts=? AND src=? AND cat=? LIMIT 1", (ts, src, cat))
        raw = (raw_row[0][0] if raw_row else "")[:600]
        n_blk, tgts, n_hn = src_profile(src)
        tlist = "、".join(x[0] for x in tgts[:8]) or "—"
        detail = ('<div class=detail id="%s" style="display:none"><b>原始日志</b><pre>%s</pre>'
                  '<b>攻击源画像</b>：累计拦截 %d 次 · 蜜罐捕获 %d 次 · 攻击目标：%s<br>'
                  '<button class="btn off" onclick="banIP(\'%s\',this)">⛔ 一键封禁 %s</button></div>'
                  % (detail_id, raw.replace("<", "&lt;"), n_blk, n_hn, tlist, src, src))
        cat_badge = {"block": '<span class="badge b-bad">拦截</span>',
                     "honey": '<span class="badge b-warn">蜜罐</span>',
                     "edr": '<span class="badge b-info">EDR</span>'}.get(cat, cat)
        out.append('<tr class=ev onclick="toggleDetail(\'%s\')"><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>%s'
                   % (detail_id, ts[5:] if len(ts) > 5 else ts, cat_badge, src, dst or "—", port or "—", vuln, detail))
    return "".join(out)

# 15 条攻击链定义（链名 → 入口域/资产/漏洞）
CHAINS = [
 ("路径一","fya","CmsEasy LFI → 域控","10.1.2.2:80"),
 ("路径二","hq","PbootCMS → 跨域","10.6.x"),
 ("路径三","cd","O2OA → K8s","10.3.2.3:80"),
 ("路径四","hq","Fastjson → AD 域","10.0.2.3:8090"),
 ("路径五","cd","Spring Boot → 工控","10.3.2.2:8080"),
 ("路径六","cd","Seafile → 家庭网","10.3.2.3:80"),
 ("路径七","hq","AnyConnect VPN → 堡垒","10.0.2.2:8443"),
 ("路径八","fya","MinIO/Jupyter → 大数据","10.1.2.3:8888"),
 ("路径九","hq","PPTP VPN → 涉密网","10.0.1.2"),
 ("路径十","fya","Kibana → 政务云","10.1.2.2:5601"),
 ("路径十一","cd","DokuWiki → 办公横向","10.3.1.3:80"),
 ("路径十二","bc","WebLogic → BC 全域","10.6.2.2:7001"),
 ("路径十三","bc","Jellyfin → 监控区","10.3.1.6"),
 ("路径十四","fya","Redis → 全库接管","10.1.1.10:6379"),
 ("路径十五","bc","RV110W → 摄像头","10.6.1.9:8082"),
]



def table(rows, head):
    h = "<tr>" + "".join("<th>%s</th>" % x for x in head) + "</tr>"
    b = "".join("<tr>" + "".join("<td>%s</td>" % c for c in r) + "</tr>" for r in rows)
    return "<table>%s%s</table>" % (h, b)

def get_policy_state():
    try:
        with open(BASE + "/policy_state.json") as f:
            return json.load(f).get("protect", "?")
    except Exception:
        return "?"

DOM_IPS = {"hq": "127.0.0.1", "fya": "10.1.249.200", "bc": "10.6.249.200", "cd": "10.3.249.200"}
DOM_NAMES = {"hq": "天权域", "fya": "天玑域", "bc": "天枢域", "cd": "天璇域"}
def jump_curl(url, method="GET", timeout=30):
    import paramiko, warnings as W
    W.filterwarnings("ignore")
    c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(JUMP_IP, username=JUMP_USER, password=JUMP_PASS, timeout=15)
    flag = "-X POST" if method == "POST" else ""
    _, o, e = c.exec_command("curl -s -m %d %s '%s' | head -c 4000" % (timeout, flag, url), timeout=timeout + 20)
    out = o.read().decode("utf-8", "replace")
    c.close()
    return out

_stats_cache = {"ts": 0, "data": {}}

def dom_stats(dom):
    import time as _t
    if _t.time() - _stats_cache["ts"] < 45 and dom in _stats_cache["data"]:
        return _stats_cache["data"][dom]
    if dom == DOMAIN:
        return {"domain": DOMAIN, "policy": get_policy_state(),
                "edr_hosts": q("SELECT COUNT(*) FROM edr")[0][0],
                "hp_sensors": q("SELECT COUNT(*) FROM hp")[0][0],
                "blocks": q("SELECT COUNT(*) FROM ev WHERE cat='block'")[0][0]}
    try:
        r = json.loads(jump_curl("http://%s/api/stats" % DOM_IPS[dom]))
    except Exception:
        r = {"domain": dom, "policy": "不可达", "blocks": "-"}
    _stats_cache["data"][dom] = r
    _stats_cache["ts"] = _t.time()
    return r

def dom_toggle(dom):
    if dom == DOMAIN:
        st = get_policy_state()
        action = "allow" if st == "protect" else "protect"
        ok, out = run_fwctl(action)
        return dom, action, ok, out
    try:
        r = jump_curl("http://%s/api/policy" % DOM_IPS[dom], "POST", 40)
        ok = "成功" in r
        return dom, ("allow" if '"protect"' not in r else "protect"), ok, r[-120:]
    except Exception as ex:
        return dom, "-", False, str(ex)[:120]

SEC_DEVS = [
 ("hq", "总公司边界防火墙", ["10.0.254.2", "10.0.253.1", "10.0.254.1"]),
 ("hq", "内部防火墙", ["10.0.251.2", "10.0.251.1"]),
 ("hq", "内部WAF", ["10.0.249.1", "10.0.250.1"]),
 ("hq", "WAF", ["10.0.252.2", "10.0.2.1"]),
 ("fya", "富裕边界防火墙", ["10.1.254.2", "10.1.253.1"]),
 ("fya", "省公司防火墙", ["10.1.251.2", "10.1.249.1"]),
 ("fya", "WAF", ["10.1.2.1", "10.1.252.2"]),
 ("bc", "省B边界防火墙", ["10.6.254.2", "10.6.253.1", "10.6.252.1"]),
 ("bc", "省B内部防火墙", ["10.6.249.1", "10.6.251.2"]),
 ("bc", "WAF", ["10.6.2.1", "10.6.252.2"]),
 ("cd", "边界防火墙", ["10.3.254.2", "10.3.253.1"]),
 ("cd", "省D内部防火墙", ["10.3.249.1", "10.3.251.2"]),
 ("cd", "WAF", ["10.3.2.1", "10.3.252.2"]),
]

def secdev_rows():
    seen = {}
    for src, n, last in q("SELECT src, COUNT(*), MAX(ts) FROM ev GROUP BY src"):
        seen[src] = (n, last)
    if DOMAIN == "hq":
        global _src_cache
        try:
            _src_cache
        except NameError:
            _src_cache = {"ts": 0, "data": {}}
        import time as _t
        if _t.time() - _src_cache["ts"] > 90:
            fresh = {}
            for d in ("fya", "bc", "cd"):
                try:
                    ext = json.loads(jump_curl("http://%s/api/sources" % DOM_IPS[d], "GET", 6))
                    fresh.update(ext)
                except Exception:
                    pass
            if fresh:
                _src_cache = {"ts": _t.time(), "data": fresh}
        for ip, v in _src_cache["data"].items():
            if ip not in seen:
                seen[ip] = tuple(v)
    BRIDGE = {"hq": "10.0.1.2", "fya": "10.1.2.2", "bc": "10.6.1.5", "cd": "10.3.1.14"}
    rows = []
    for dom, nm, ips in SEC_DEVS:
        best = max((seen.get(ip, (0, "-")) for ip in ips), key=lambda x: x[0])
        bn, bl = seen.get(BRIDGE.get(dom, ""), (0, "-"))
        if best[0] > 0:
            st = "直接在线"
        elif bn > 0:
            st = "经桥在线"
        else:
            st = "暂无日志"
        rows.append((DOM_NAMES[dom], nm, ips[0], best[0] if best[0] else bn, best[1] if best[0] else bl, badge(st)))
    return rows

def up_unquote(v):
    import urllib.parse as up
    return up.unquote_plus(v.replace("+", "%2B")).replace("%2B", "+")

def run_fwctl_ext(action, args=None):
    """经本域跳板执行 fwctl 任意子命令；返回(ok, output)"""
    argstr = " ".join(str(a).replace(" ", "\ ") for a in (args or []))
    try:
        import paramiko, warnings
        warnings.filterwarnings("ignore")
        c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        c.connect(JUMP_IP, username=JUMP_USER, password=JUMP_PASS, timeout=15)
        _, o, e = c.exec_command("SOC_DOMAIN=%s python3 /opt/soc/fwctl.py %s %s" % (DOMAIN, action, argstr), timeout=45)
        out = o.read().decode("utf-8", "replace") + e.read().decode("utf-8", "replace")
        c.close()
    except Exception as ex:
        return False, "jump-error: " + str(ex)[:150]
    ok = out.strip().startswith("OK") or action == "list" and out.strip().startswith("RULESET")
    return ok, out.strip()[-3000:]

HONEY_REG = BASE + "/honey_registry.json"
TPOT_SELF = {"hq": "10.0.249.4", "fya": "10.1.249.200", "bc": "10.6.249.200", "cd": "10.3.249.200"}.get(DOMAIN, "10.0.249.4")
HONEY_CODE = None
try:
    with open(BASE + "/honey_agent.py", "rb") as f:
        HONEY_CODE = f.read()
except Exception:
    HONEY_CODE = None

def honey_registry():
    try:
        with open(HONEY_REG) as f:
            return json.load(f)
    except Exception:
        return []

def honey_registry_save(rows):
    with open(HONEY_REG, "w") as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)

def jump2ssh(target_ip, inner_cmd, user="user", pwd="gzhu@20260225"):
    """T-Pot -> 本域跳板 -> 目标机 执行命令（双跳）"""
    import paramiko, warnings
    warnings.filterwarnings("ignore")
    j = paramiko.SSHClient(); j.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    j.connect(JUMP_IP, username=JUMP_USER, password=JUMP_PASS, timeout=15)
    b64inner = __import__("base64").b64encode(inner_cmd.encode()).decode()
    inner_py = (
        "import paramiko, warnings, base64\n"
        "warnings.filterwarnings('ignore')\n"
        "c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())\n"
        "c.connect('" + target_ip + "', username='" + user + "', password='" + pwd + "', timeout=12, allow_agent=False, look_for_keys=False)\n"
        "cmd = base64.b64decode('" + b64inner + "').decode()\n"
        "_, o, e = c.exec_command(cmd, timeout=120)\n"
        "print(o.read().decode('utf-8', 'replace'))\n"
        "print('[E]' + e.read().decode()[:200])\n"
        "c.close()\n")
    _, o, e = j.exec_command("python3 - <<'PYIN'\n" + inner_py + "PYIN", timeout=150)
    out = o.read().decode("utf-8", "replace") + e.read().decode("utf-8", "replace")
    j.close()
    return out

def honey_deploy(target_ip, proto, port, remove=False):
    import base64
    b64code = base64.b64encode(HONEY_CODE).decode() if HONEY_CODE else "SKIP"
    unit_tpl = ("[Unit]\nDescription=honey agent\nAfter=network.target\n[Service]\nType=simple\n"
                "Environment=TPOT_ADDR=" + TPOT_SELF + "\nExecStart=/usr/bin/python3 /opt/honey/honey_agent.py\n"
                "Restart=always\n[Install]\nWantedBy=multi-user.target\n")
    py_lines = [
        "import json, base64, os",
        "CONF='/opt/honey/conf.json'",
        "proto='%s'; port='%s'; remove=%s" % (proto, port, "True" if remove else "False"),
        "try: rows=json.load(open(CONF))",
        "except: rows=[]",
        "rows=[r for r in rows if not (r.get('proto')==proto and str(r.get('port'))==str(port))]",
        "if not remove: rows.append({'proto':proto,'port':port})",
        "os.makedirs('/opt/honey', exist_ok=True)",
        "json.dump(rows, open(CONF,'w'))",
        "b64='%s'" % b64code,
        "if b64 and b64!='SKIP' and not os.path.exists('/opt/honey/honey_agent.py'):",
        "    open('/opt/honey/honey_agent.py','wb').write(base64.b64decode(b64))",
        "open('/etc/systemd/system/honey.service','w').write(open('/tmp/unit.txt').read()) if os.path.exists('/tmp/unit.txt') else None",
        "print('CONF-NOW', rows)",
    ]
    sh_lines = [
        "mkdir -p /opt/honey",
        "printf '%s' > /tmp/unit.txt" % unit_tpl.replace("'", "'\\''"),
        "echo '%s' | base64 -d > /tmp/h.py" % base64.b64encode(("\n".join(py_lines)).encode()).decode(),
        "python3 /tmp/h.py",
        "install -m 644 /tmp/unit.txt /etc/systemd/system/honey.service",
        "sed -i 's/TPOT_ADDR=127.0.0.1/TPOT_ADDR=%s/' /etc/systemd/system/honey.service" % TPOT_SELF,
        "systemctl daemon-reload",
        "systemctl enable --now honey",
        "systemctl restart honey",
        "sleep 2",
        "systemctl is-active honey",
        "ss -tln | grep -c '%s'" % port,
    ]
    inner = ("echo '%s' | base64 -d > /tmp/h.sh && "
             "echo 'gzhu@20260225' | sudo -S --prompt='' bash /tmp/h.sh 2>&1"
             % base64.b64encode(("\n".join(sh_lines)).encode()).decode())
    out = jump2ssh(target_ip, inner)
    ok = "active" in out or "CONF-NOW" in out
    reg = honey_registry()
    reg = [r for r in reg if not (r.get("ip") == target_ip and r.get("proto") == proto and str(r.get("port")) == str(port))]
    if not remove:
        reg.append({"ip": target_ip, "proto": proto, "port": str(port), "ts": now()})
    honey_registry_save(reg)
    return ok, out.strip()[-260:]

def run_fwctl(action):
    """经本域跳板机(paramiko)执行 vyos 双态切换"""
    try:
        import paramiko, warnings
        warnings.filterwarnings("ignore")
        c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        c.connect(JUMP_IP, username=JUMP_USER, password=JUMP_PASS, timeout=15)
        _, o, e = c.exec_command("SOC_DOMAIN=%s python3 /opt/soc/fwctl.py %s" % (DOMAIN, action), timeout=120)
        out = o.read().decode("utf-8", "replace") + e.read().decode("utf-8", "replace")
        c.close()
    except Exception as ex:
        return False, "jump-error: " + str(ex)[:150]
    ok = ("OK-" + action) in out
    if ok:
        with open(BASE + "/policy_state.json", "w") as f:
            json.dump({"protect": action, "ts": now()}, f)
    return ok, out.strip()[-200:]

class H(socketserver.BaseRequestHandler):
    def handle(self):
        try:
            data = self.request.recv(8192).decode("utf-8", "replace")
            path = (data.split(" ")[1] if " " in data else "/").split("?")[0]
            import urllib.parse as _up0
            _qs = _up0.parse_qs((data.split(" ")[1] if " " in data else "").split("?", 1)[-1])
            globals()["VDOM"] = _qs.get("dom", [DOMAIN])[0]
            import traceback
            try:
                body = self.route(path, data)
            except Exception:
                body = "<pre>" + traceback.format_exc()[-1200:] + "</pre>"
            self.request.sendall(("HTTP/1.0 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\n" + body).encode())
        except Exception as e:
            try:
                self.request.sendall(("HTTP/1.0 500\r\n\r\n" + str(e)).encode())
            except Exception:
                pass
    def route(self, path, raw):
        _dom_links = (("hq", "天权"), ("fya", "天玑"), ("bc", "天枢"), ("cd", "天璇"), ("all", "全局"))
        doms = str("").join('<a href="/?dom=%s" class="%s">%s</a>' % (d, "cur" if d == VDOM else "", n)
                       for d, n in _dom_links)
        P = lambda c, _d=doms: PAGE.replace("__D1__", DOMAIN.upper()).replace("__DOMS__", _d).replace("__BODY__", c)
        if path == "/" or path == "":
            alerts = q("SELECT id, level, msg, ts FROM alerts WHERE id NOT IN (SELECT 1) ORDER BY id DESC LIMIT 3")
            try:
                acked = set(json.load(open(BASE + "/acked.json")))
            except Exception:
                acked = set()
            alerts = [a for a in alerts if str(a[0]) not in acked][:2]
            alert_html = "".join('<div class="alertbar %s" onclick="ackAlert(%d);this.style.display=\'none\'">🔔 %s <span class=small style="color:#fff9">%s · 点击确认</span></div>'
                                  % (a[1], a[0], a[2], a[3]) for a in alerts)
            n_edr = q("SELECT COUNT(*) FROM edr")[0][0]
            n_blk = q("SELECT COUNT(*) FROM ev WHERE cat='block'")[0][0]
            n_hp = q("SELECT COUNT(*) FROM hp WHERE kind LIKE '在线%' OR kind LIKE '%('")[0][0]
            n_honey = q("SELECT COUNT(*) FROM ev WHERE cat='honey' AND vuln NOT LIKE '%%上线'")[0][0]
            n_alert = q("SELECT COUNT(*) FROM alerts")[0][0]
            recent = q("SELECT ts,cat,src,dst,port,vuln FROM ev WHERE cat IN('block','honey') ORDER BY ts DESC LIMIT 40")
            domrows = []
            for d in ("hq", "fya", "bc", "cd"):
                st = dom_stats(d)
                tag = "本域" if d == DOMAIN else DOM_NAMES[d]
                cur = st.get("policy", "?")
                btn = ('<button class="btn off" onclick="toggle(\'%s\',this)">放行</button>' % d) if cur == "protect" else ('<button class="btn on" onclick="toggle(\'%s\',this)">拦截</button>' % d)
                domrows.append("<tr><td>%s(%s)</td><td>%s</td><td>%s</td><td>%s台/%s蜜罐</td><td>%s</td></tr>" % (
                    tag, d, badge(cur), st.get("blocks", "-"), st.get("edr_hosts", "-"), st.get("hp_sensors", "-"), btn))
            return P("""%s
<div class=grid>%s</div>
<div class=card><h2>全域防御策略（即时切换，20-60秒生效）</h2>
<table><tr><th>域</th><th>策略</th><th>累计拦截</th><th>EDR/蜜罐</th><th>操作</th></tr>%s</table>
<button class="btn off" onclick="policyAll('allow',this)">全部放行(演练)</button>
<button class="btn on" style="margin-left:6px" onclick="policyAll('protect',this)">全部拦截(防御)</button>
<p class=small>规则配置：<a href=/policy style="color:#7dd3fc">防御策略</a> ｜ 攻击链态势：<a href=/chains style="color:#7dd3fc">攻防态势</a> ｜ 蜜罐下发：<a href=/honey style="color:#7dd3fc">动态蜜罐</a></p></div>
<div class=card><h2>攻击时间线（24 小时）</h2>%s</div>
<div class=card><h2>命中漏洞 TOP</h2>%s</div>
<div class=card><h2>最近攻击事件（点击行下钻：原始日志 / 攻击源画像 / 一键封禁）</h2>
<table><tr><th>时间</th><th>类型</th><th>源</th><th>目标</th><th>端口</th><th>判定</th></tr>%s</table></div>""" % (
                alert_html,
                "".join([kpi(n_edr, "EDR 覆盖主机", "/edr"), kpi(n_blk, "累计拦截攻击", "/waf"),
                         kpi(n_hp, "蜜罐在线", "/hp"), kpi(n_honey, "蜜罐捕获", "/honey"),
                         kpi(n_alert, "待处理告警", "#")]),
                "".join(domrows), timeline_svg(), topbar_chart(), ev_rows_with_detail(recent)))

        if path == "/chains":
            domrows = []
            for d in ("hq", "fya", "bc", "cd"):
                st = dom_stats(d)
                domrows.append("<td class=chain-cell>%s<br>%s</td>" % (badge(st.get("policy", "?")), st.get("blocks", "-")))
            rows = []
            for nm, dom, desc, entry in CHAINS:
                n_hit = q("SELECT COUNT(*) FROM ev WHERE cat='block' AND vuln LIKE ?", ("%" + desc.split(" ")[0] + "%",))[0][0]
                if n_hit == 0:
                    n_hit = q("SELECT COUNT(*) FROM ev WHERE cat='block' AND dst LIKE ?", ("%" + entry.split(":")[0] + "%",))[0][0]
                rows.append("<tr><td><b>%s</b></td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
                            % (nm, DOM_NAMES.get(dom, dom), desc, entry, domrows[0] if dom == "hq" else "",
                               domrows[1] if dom == "fya" else "", domrows[2] if dom == "bc" else "",
                               domrows[3] if dom == "cd" else ""))
            heads = "".join("<th>%s 策略/拦截</th>" % DOM_NAMES[d] for d in ("hq", "fya", "bc", "cd"))
            return P("""<div class=card><h2>攻防链态势矩阵（15 条攻击链 × 四域防御状态）</h2>
<p class=small>每行=一条攻击链；其所属域列显示当前防御策略与累计拦截数——<span class="badge b-ok">protect</span>=演练会被拦截，<span class="badge b-bad">allow</span>=演练可打通。入口资产命中过拦截的链在"命中"列有数值。</p>
<table><tr><th>攻击链</th><th>所属域</th><th>剧本</th><th>入口资产</th>%s<th>历史命中</th></tr>%s</table></div>
<div class=card><h2>演练操作指引</h2>
<ol class=small><li>在 <a href=/policy style="color:#7dd3fc">防御策略</a> 将目标链所属域切为"放行(演练)"</li>
<li>登录对应攻击机（atkA/B/C/D）按剧本执行攻击（参见 攻击实录/ 目录）</li>
<li>回到本页与 <a href=/ style="color:#7dd3fc">总览</a> 观察蜜罐捕获与 EDR 事件</li>
<li>演练完成切回"拦截(防御)"</li></ol></div>""" % (heads.replace("<th>", "<th>").replace("策略/拦截</th>", "策略/拦截</th>"), "".join(rows).replace("<td></td>", "<td>—</td>")))

        if path == "/api/ban" and "POST" in raw:
            body = raw.split(chr(13) + chr(10) + chr(13) + chr(10), 1)[-1]
            kv = dict(p.split("=", 1) for p in body.split("&") if "=" in p)
            src_ip = up_unquote(kv.get("src", ""))
            if not src_ip:
                return "参数缺失"
            rn = str(int(time.time()) % 9000 + 500)
            ok, out = run_fwctl_ext("rule-add", [rn, "reject", "all", src_ip + "/32", "-", "-", "SOC-BAN-" + src_ip])
            return ("封禁 %s 成功（规则 %s）" % (src_ip, rn)) if ok else ("封禁失败: " + out[:120])

        if path == "/api/alert-ack" and "POST" in raw:
            body = raw.split(chr(13) + chr(10) + chr(13) + chr(10), 1)[-1]
            aid = body.split("=")[-1].strip()
            try:
                acked = json.load(open(BASE + "/acked.json"))
            except Exception:
                acked = []
            if aid not in acked:
                acked.append(aid)
            json.dump(acked, open(BASE + "/acked.json", "w"))
            return "告警已确认"

        if path == "/edr":
            import time as _t, datetime as _dt
            nowts = _dt.datetime.now()
            hosts = q("SELECT ip,host,last,n FROM edr ORDER BY last DESC")
            rows = []
            n_alive = 0
            for ip_, hn_, last_, n_ in hosts:
                try:
                    dts = _dt.datetime.strptime(last_, "%Y-%m-%dT%H:%M:%S")
                    age = (nowts - dts).total_seconds()
                except Exception:
                    age = 99999
                alive = age < 180
                if alive:
                    n_alive += 1
                st = '<span class="badge b-ok">存活 (%ds前)</span>' % int(age) if alive else '<span class="badge b-bad">失联</span>'
                rows.append((hn_, hn_, last_, n_, st))
            auths = q("SELECT ts,src,raw FROM ev WHERE cat='edr' AND raw LIKE '%%auth%%' ORDER BY ts DESC LIMIT 15")
            return P("""<div class=card><h2>EDR 覆盖（存活 %d / 总 %d，实时刷新：心跳超180秒判失联）</h2>%s</div>
<div class=card><h2>EDR 捕获（认证类事件）</h2>%s</div>""" % (
                n_alive, len(rows),
                table(rows, ["主机名", "标识", "最近心跳", "事件数", "存活状态"]),
                table([(a, b, c[100:260]) for a, b, c in auths], ["时间", "源", "事件"])))

        if path == "/hp":
            sens = q("SELECT ip,last,n FROM hp ORDER BY last DESC")
            caps = q("SELECT ts,src,dst,port,vuln FROM ev WHERE cat='hp' ORDER BY ts DESC LIMIT 20")
            return P("""<div class=card><h2>蜜罐覆盖（上报传感器 %d / 目标 24 台高交互蜜罐）</h2>%s</div>
<div class=card><h2>蜜罐捕获（连接/攻击）</h2>%s</div>""" % (len(sens),
                table(sens, ["蜜罐IP", "最近上报", "累计捕获"]),
                table(caps, ["时间", "来源", "蜜罐", "端口/服务", "判定"])))
        if path == "/waf":
            blocks = q("SELECT vuln,cve,src,dst,port,COUNT(*) FROM ev WHERE cat='block' GROUP BY vuln,cve,src,dst,port ORDER BY 6 DESC LIMIT 20")
            try:
                ok, rules = run_fwctl_ext("list")
                rules_html = "<pre>%s</pre>" % rules[:3000]
            except Exception as ex:
                rules_html = "<pre>%s</pre>" % ex
            return P("""<div class=card><h2>WAF/边界拦截明细（规则命中的攻击→漏洞映射）</h2>%s</div>
<div class=card><h2>受控安全设备（实际接入本域日志流的设备）</h2>%s
<p class=small>共 %d 台串联设备（4边界+4WAF+3内部FW+2内部WAF），另有IDS×2为纯被动传感器（无管理面，豁免）；250.2/251.2 经网关链路汇入。跨域设备在各域控制台查看。</p></div>
<div class=card><h2>当前规则集（实时读取）</h2>%s</div>""" % (
                table(blocks, ["攻击/漏洞", "编号", "攻击源", "目标", "端口", "次数"]),
                table(secdev_rows(), ["域", "设备", "IP", "累计日志", "最近上报", "状态"]),
                len(SEC_DEVS), rules_html))

        if path == "/policy":
            doms = []
            for d in ("hq", "fya", "bc", "cd"):
                st = dom_stats(d)
                tag = "本域" if d == DOMAIN else DOM_NAMES[d]
                cur = st.get("policy", "?")
                btn = ('<button class="btn off" onclick="toggle(\'%s\',this)">放行</button>' % d) if cur == "protect" else ('<button class="btn on" onclick="toggle(\'%s\',this)">拦截</button>' % d)
                doms.append("<tr><td>%s(%s)</td><td>%s</td><td>拦截%s / EDR %s台 / 蜜罐%s</td><td>%s</td></tr>" % (tag, d, badge(cur), st.get("blocks", 0), st.get("edr_hosts", 0), st.get("hp_sensors", 0), btn))
            rules_html = "<pre>加载失败</pre>"
            try:
                ok, out = run_fwctl_ext("list")
                rules_html = "<pre>%s</pre>" % (out[:3000] if ok else out)
            except Exception as ex:
                rules_html = "<pre>%s</pre>" % ex
            return P("""<div class=card><h2>全域防御策略总控</h2>
<table><tr><th>域</th><th>当前策略</th><th>概览</th><th>操作</th></tr>%s</table>
<button class="btn off" onclick="policyAll('allow',this)" style="margin:10px 6px">全部放行(演练)</button>
<button class="btn on" onclick="policyAll('protect',this)">全部拦截(防御)</button>
<p class=small>拦截=EDGE-IN rule5 reject 本域攻击机；放行=rule5 accept 覆盖。跨域经跳板链路代理执行，每次约20-60秒。</p></div>
<div class=card><h2>安全设备策略配置（本域 %s）</h2>
<form onsubmit="event.preventDefault();ruleGo(this,this.querySelector('button'))">%s
<button class="btn blue" type=submit>保存规则</button></form>
<p class=small>字段：编号(10-9999，避开5)｜动作 accept/reject/drop｜协议 tcp/udp/-｜源/目标 CIDR 或 -｜端口 如80,443 或 -｜描述</p></div>
<div class=card><h2>当前规则集（实时）</h2>%s
<form onsubmit="event.preventDefault();ruleDel(this,this.querySelector('button'))">%s<button class="btn off" type=submit>删除该编号规则</button></form></div>""" % (
                "".join(doms), DOMAIN.upper(),
                "".join('<input name=%s placeholder="%s" style="width:%spx;margin:2px">' % (f, ph, w) for f, ph, w in
                        [("rn","编号",50),("rac","动作",80),("rpr","协议",60),("rsrc","源CIDR",130),("rdst","目标CIDR",130),("rdp","端口",80),("rds","描述",160)]),
                rules_html,
                '<input name=del_rn placeholder="要删除的规则编号" style="width:150px">'))

        if path == "/api/policy" and "POST" in raw:
            import urllib.parse as up
            qs = up.parse_qs(((raw.split(" ")[1] if " " in raw else "")).split("?", 1)[-1])
            d = qs.get("domain", [DOMAIN])[0]
            if d not in DOM_IPS:
                d = DOMAIN
            dom, action, ok, out = dom_toggle(d)
            return ("%s → %s 成功" % (dom, action)) if ok else ("%s 失败: %s" % (dom, out[:120]))

        if path == "/api/policy-all" and "POST" in raw:
            act = "allow" if "allow" in raw.split(chr(13))[0] else "protect"
            # 逐域先归一到目标态：先读各域状态，再切换到目标
            results = []
            for d in ("hq", "fya", "bc", "cd"):
                st = dom_stats(d).get("policy")
                if st == act:
                    results.append("%s:已是%s" % (d, act))
                    continue
                dom, action, ok, out = dom_toggle(d)
                results.append("%s:%s(%s)" % (d, action, "OK" if ok else "FAIL"))
            return "全部→%s：" % act + "；".join(results)

        if path == "/api/rules" and "POST" in raw:
            body = raw.split(chr(13) + chr(10) + chr(13) + chr(10), 1)[-1]
            kv = {}
            for pair in body.split("&"):
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    kv[k] = up_unquote(v)
            if "del_rn" in kv and kv.get("del_rn", "").strip():
                ok, out = run_fwctl_ext("rule-del", [kv["del_rn"].strip()])
                return ("删除规则 %s 成功" % kv["del_rn"]) if ok else ("失败: " + out[:150])
            need = ("rn", "rac")
            if all(kv.get(k, "").strip() for k in need):
                args = [kv.get(k, "-").strip() or "-" for k in ("rn", "rac", "rpr", "rsrc", "rdst", "rdp", "rds")]
                ok, out = run_fwctl_ext("rule-add", args)
                return ("新增规则 %s 成功" % args[0]) if ok else ("失败: " + out[:150])
            return "<h3>参数缺失</h3><a href=/policy>返回</a>"

        if path == "/honey":
            _hl = ""
            try:
                for r in q("SELECT host FROM edr ORDER BY host LIMIT 60"):
                    _hl += "<option value=\"%s\">%s</option>" % (r[0], r[0])
            except Exception:
                pass
            for extra in ("10.0.1.2", "10.0.1.4", "10.0.1.5", "10.1.2.2", "10.6.1.5", "10.3.1.14"):
                if extra not in _hl:
                    _hl += "<option value=\"%s\">跳板/载体 %s</option>" % (extra, extra)

            reg = honey_registry()
            regrows = [(r["ip"], r["proto"], r["port"], r["ts"],
                        '<button class="btn off" onclick="honeyDel(\'%s\',\'%s\',\'%s\',this)">下线</button>' % (r["ip"], r["proto"], r["port"]))
                       for r in reg]
            caps = q("SELECT ts,src,dst,port,vuln FROM ev WHERE cat='honey' AND vuln!='蜜罐上线' ORDER BY ts DESC LIMIT 20")
            ups = q("SELECT ts,dst, COUNT(*) FROM ev WHERE cat='honey' AND vuln='蜜罐上线' GROUP BY dst ORDER BY 3 DESC LIMIT 10")
            _page = """<div class=card><h2>动态蜜罐下发（免 Docker，纯 Python 蜜罐引擎）</h2>
<form onsubmit="event.preventDefault();honeyGo(this,this.querySelector('button'))">
<input name=ip list=hostlist placeholder="选择或输入目标 IP" style="width:180px">
<datalist id=hostlist>__HL__</datalist>
<select name=proto><option value=ssh>SSH</option><option value=http>HTTP</option><option value=telnet>Telnet</option><option value=ftp>FTP</option><option value=redis>Redis</option><option value=mysql>MySQL</option></select>
<input name=port placeholder="端口(如 2323)" style="width:100px">
<input type=hidden name=act value=add>
<button class="btn blue" type=submit>下发蜜罐到该端口</button></form>
<p class=small>支持任意 Linux 内网机（Windows 目标暂不支持）；下发后引擎自动上报连接/凭据捕获到本域 T-Pot。引擎已内置：ssh/telnet 抓客户端版本与输入、http 抓请求行、redis 抓命令、ftp 抓 USER 口令。</p></div>
<div class=card><h2>已部署蜜罐（注册表）</h2>%s</div>
<div class=card><h2>蜜罐诱捕记录（连接/凭据）</h2>%s</div>
<div class=card><h2>蜜罐引擎心跳</h2>%s</div>""" % (
                table(regrows, ["目标 IP", "协议", "端口", "下发时间", "操作"]),
                table(caps, ["时间", "来源 IP", "蜜罐主机", "端口", "捕获内容"]),
                table(ups, ["时间", "蜜罐主机", "上线次数"]).replace("__HL__", _hl))

        if path == "/api/honey" and "POST" in raw:
            body = raw.split(chr(13) + chr(10) + chr(13) + chr(10), 1)[-1]
            kv = {}
            for pair in body.split("&"):
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    kv[k] = up_unquote(v)
            act = kv.get("act", "add")
            ip_, pr_, pt_ = kv.get("ip", "").strip(), kv.get("proto", "").strip(), kv.get("port", "").strip()
            if not (ip_ and pr_ and pt_):
                return "<h3>参数缺失</h3><a href=/honey>返回</a>"
            ok, out = honey_deploy(ip_, pr_, pt_, remove=(act == "remove"))
            return ("%s %s:%s(%s) 成功" % ("下线" if act == "remove" else "下发", ip_, pt_, pr_)) if ok else ("失败: " + out[:150])

        if path == "/bots":
            _hl = ""
            try:
                for r in q("SELECT host FROM edr ORDER BY host LIMIT 60"):
                    _hl += "<option value=\"%s\">%s</option>" % (r[0], r[0])
            except Exception:
                pass
            for extra in ("10.0.1.2", "10.0.1.4", "10.0.1.5", "10.1.2.2", "10.6.1.5", "10.3.1.14"):
                if extra not in _hl:
                    _hl += "<option value=\"%s\">跳板/载体 %s</option>" % (extra, extra)
            reg = []
            try:
                reg = json.load(open(BASE + "/bots.json"))
            except Exception:
                reg = []
            regrows = [(r["ip"], r.get("dom", "-"), r.get("rate", "30-180s"), r.get("status", "?"),
                        '<button class="btn %s" onclick="botGo(\'%s\',\'%s\',this)">%s</button>' % (
                            "on" if r.get("status") == "on" else "off", r["ip"],
                            "off" if r.get("status") == "on" else "on",
                            "停止" if r.get("status") == "on" else "启动")) for r in reg]
            return P("""<div class=card><h2>流量机器人（背景干扰流量）控制</h2>
<form onsubmit="event.preventDefault();botAdd(this,this.querySelector('button.add'))">
<input name=ip list=hostlist2 placeholder="选择或输入载体 IP" style="width:170px">
<datalist id=hostlist2>%s</datalist>
<select name=rate><option value="30-180">速率: 标准（30-180s 随机）</option>
<option value="10-40">速率: 高频（10-40s）</option>
<option value="300-900">速率: 低频（5-15分钟）</option></select>
<button class="btn blue add" type=submit>部署机器人到该机</button></form>
<p class=small>机器人在载体机上以 bgtraffic 运行，对本域业务服务发起随机正常请求（模拟员工上网/OA访问等），形成背景干扰流量。攻击流量混入其中，用于检验检测能力。</p></div>
<div class=card><h2>已部署机器人（注册表）</h2>%s</div>""" % (_hl, table(regrows, ["载体 IP", "域", "速率", "状态", "操作"])))

        if path == "/api/bots" and "POST" in raw:
            body = raw.split(chr(13) + chr(10) + chr(13) + chr(10), 1)[-1]
            kv = {}
            for pair in body.split("&"):
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    kv[k] = up_unquote(v)
            act = kv.get("act", "add")
            ip_ = kv.get("ip", "").strip()
            rate = kv.get("rate", "30-180").strip() or "30-180"
            if not ip_:
                return "参数缺失"
            if act == "add":
                py_lines = [
                    "import json",
                    "rate='%s'" % rate,
                    "src=open('/opt/bgtraffic/bgtraffic.py').read()",
                    "src=src.replace('random.uniform(30, 180)','random.uniform(R0, R1)')",
                    "for a,b in [('R0',rate.split('-')[0]),('R1',rate.split('-')[1])]:",
                    "    src=src.replace(a,b)",
                    "open('/opt/bgtraffic/bgtraffic.py','w').write(src)",
                ]
                import base64 as _b2
                inner = ("echo 'gzhu@20260225' | sudo -S --prompt='' bash -c '"
                         "mkdir -p /opt/bgtraffic; "
                         + "systemctl is-active bgtraffic >/dev/null 2>&1 || "
                         + "printf \"[Unit]\nDescription=bgtraffic\nAfter=network.target\n[Service]\nType=simple\nExecStart=/usr/bin/python3 /opt/bgtraffic/bgtraffic.py\nRestart=always\n[Install]\nWantedBy=multi-user.target\n\" > /etc/systemd/system/bgtraffic.service; "
                         + "systemctl daemon-reload; systemctl enable --now bgtraffic; systemctl restart bgtraffic; sleep 2; systemctl is-active bgtraffic' 2>/dev/null")
                ok_, out = honey_deploy(ip_, "bot", rate, remove=False) if False else (None, None)
                # 直接复用 jump2ssh
                try:
                    res = jump2ssh(ip_, "echo '%s' | sudo -S --prompt='' bash -c 'systemctl is-active bgtraffic >/dev/null 2>&1 && echo HAVE || (mkdir -p /opt/bgtraffic && systemctl enable --now bgtraffic 2>/dev/null; echo NEW)'" % "gzhu@20260225")
                    have = "HAVE" in res or "active" in res
                except Exception:
                    have = False
                # 改速率
                sh_lines = [
                    "cd /opt/bgtraffic",
                    "sed -i 's/random.uniform([0-9]*, *[0-9]*)/random.uniform(%s,%s)/' bgtraffic.py || true" % (rate.split("-")[0], rate.split("-")[1]),
                    "systemctl restart bgtraffic",
                    "sleep 1; systemctl is-active bgtraffic",
                ]
                import base64 as _b3
                _NL = chr(10)
                inner2 = ("echo '%s' | base64 -d > /tmp/b.sh && echo 'gzhu@20260225' | sudo -S --prompt='' bash /tmp/b.sh 2>&1"
                          % _b3.b64encode(_NL.join(sh_lines).encode()).decode())
                try:
                    out2 = jump2ssh(ip_, inner2)
                    ok2 = "active" in out2
                except Exception as ex:
                    ok2, out2 = False, str(ex)
                reg = []
                try:
                    reg = json.load(open(BASE + "/bots.json"))
                except Exception:
                    pass
                reg = [r for r in reg if r.get("ip") != ip_]
                reg.append({"ip": ip_, "rate": rate + "s", "status": "on" if ok2 else "off",
                            "dom": DOMAIN, "ts": now()})
                json.dump(reg, open(BASE + "/bots.json", "w"), ensure_ascii=False, indent=1)
                return ("机器人 %s 部署成功（速率 %ss）" % (ip_, rate)) if ok2 else ("失败: " + out2[:150])
            else:
                onoff = kv.get("state", "off")
                sh_lines = ["systemctl %s bgtraffic" % ("restart" if onoff == "on" else "stop"),
                            "sleep 1; systemctl is-active bgtraffic || true"]
                import base64 as _b4
                inner3 = ("echo '%s' | base64 -d > /tmp/b.sh && echo 'gzhu@20260225' | sudo -S --prompt='' bash /tmp/b.sh 2>&1"
                          % _b4.b64encode(chr(10).join(sh_lines).encode()).decode())
                try:
                    out3 = jump2ssh(ip_, inner3)
                    st = "on" if onoff == "on" else "off"
                except Exception as ex:
                    st, out3 = "off", str(ex)
                reg = []
                try:
                    reg = json.load(open(BASE + "/bots.json"))
                except Exception:
                    pass
                for r in reg:
                    if r.get("ip") == ip_:
                        r["status"] = st
                json.dump(reg, open(BASE + "/bots.json", "w"), ensure_ascii=False, indent=1)
                return ("机器人 %s 已%s" % (ip_, "启动" if st == "on" else "停止"))

        if path == "/api/sources":
            seen = {}
            for src, n, last in q("SELECT src, COUNT(*), MAX(ts) FROM ev GROUP BY src"):
                seen[src] = [n, last]
            return json.dumps(seen)

        if path == "/api/stats":
            body = json.dumps({"domain": DOMAIN, "policy": get_policy_state(),
                               "edr_hosts": q("SELECT COUNT(*) FROM edr")[0][0],
                               "hp_sensors": q("SELECT COUNT(*) FROM hp")[0][0],
                               "blocks": q("SELECT COUNT(*) FROM ev WHERE cat='block'")[0][0]})
            return body
        return P("<div class=card>404</div>")

class Srv(socketserver.ThreadingTCPServer):
    daemon_threads = True
    allow_reuse_address = True

if __name__ == "__main__":
    collector()
    Srv(("0.0.0.0", WEB_PORT), H).serve_forever()
