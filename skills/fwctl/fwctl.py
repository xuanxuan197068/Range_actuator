#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fwctl.py v4 — 各域跳板机上，SOC 经 SSH 调用：vyos 双态切换 + 规则管理（自动探测绑定规则集）"""
import sys, os, re, paramiko, warnings
warnings.filterwarnings("ignore")
EDGE = {"hq": ("10.0.254.2", "10.0.254.100"), "fya": ("10.1.254.2", "10.1.254.100"),
        "bc": ("10.6.254.2", "10.6.254.100"), "cd": ("10.3.254.2", "10.3.254.100")}
action = sys.argv[1] if len(sys.argv) > 1 else "status"
dom0 = sys.argv[2] if len(sys.argv) > 2 else ""
dom = os.environ.get("SOC_DOMAIN", dom0 if dom0 in EDGE else "hq")
ip, atk = EDGE[dom]
c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(ip, username="vyos", password="vyosP@ssword12#$", timeout=15, allow_agent=False, look_for_keys=False)
NL = chr(10)

def sh(cmd, t=120):
    _, o, e = c.exec_command(cmd, timeout=t)
    return o.read().decode("utf-8", "replace") + "[E]" + e.read().decode()[:150]

def vbash(L):
    return sh("vbash -s <<'VYS'" + NL + NL.join(L) + NL + "VYS", 120)

conf = sh("/opt/vyatta/bin/vyatta-op-cmd-wrapper show configuration commands", 40)
m = re.search(r"set interfaces ethernet \S+ firewall in name (\S+)", conf)
RS = m.group(1).strip("'") if m else "EDGE-IN"

def show_conf(grep):
    return sh("/opt/vyatta/bin/vyatta-op-cmd-wrapper show configuration commands | grep " + grep + " | sort", 40).strip()

if action == "list":
    print("RULESET: " + RS)
    print("BOUND: " + sh("/opt/vyatta/bin/vyatta-op-cmd-wrapper show configuration commands | grep 'firewall in '", 40).strip())
    for ln in show_conf("'firewall name " + RS + " rule '").splitlines():
        print(ln.strip())
    c.close(); sys.exit(0)

if action == "rule-add":
    rn, rac, rpr, rsrc, rdst, rdp, rds = sys.argv[2:9]
    L = ["source /opt/vyatta/etc/functions/script-template", "configure",
         "set firewall name " + RS + " rule " + rn + " action " + rac]
    if rpr != "-": L.append("set firewall name " + RS + " rule " + rn + " protocol " + rpr)
    if rsrc != "-": L.append("set firewall name " + RS + " rule " + rn + " source address " + rsrc)
    if rdst != "-": L.append("set firewall name " + RS + " rule " + rn + " destination address " + rdst)
    if rdp != "-": L.append("set firewall name " + RS + " rule " + rn + " destination port " + rdp)
    L += ["set firewall name " + RS + " rule " + rn + " description " + (rds if rds != "-" else "SOC-RULE-" + rn),
          "commit", "save", "exit"]
    out = vbash(L)
    cur = show_conf("'name " + RS + " rule " + rn + " '")
    print(("OK-ADD-" + rn) if ("Done" in out and cur) else ("FAIL | " + out.strip()[-150:]))
    c.close(); sys.exit(0)

if action == "rule-del":
    rn = sys.argv[2]
    L = ["source /opt/vyatta/etc/functions/script-template", "configure",
         "delete firewall name " + RS + " rule " + rn, "commit", "save", "exit"]
    out = vbash(L)
    cur = show_conf("'firewall name " + RS + " rule " + rn + " '")
    print(("OK-DEL-" + rn) if ("Done" in out and not cur) else ("FAIL | " + out.strip()[-150:]))
    c.close(); sys.exit(0)

if action == "status":
    print(sh("/opt/vyatta/bin/vyatta-op-cmd-wrapper show configuration commands | grep 'firewall in' | head -2", 40).strip())
    print(sh("/opt/vyatta/bin/vyatta-op-cmd-wrapper show configuration commands | grep 'rule 5 ' | head -5", 40).strip())
    c.close(); sys.exit(0)

# protect / allow
L = ["source /opt/vyatta/etc/functions/script-template", "configure"]
if action == "protect":
    L += ["set firewall name " + RS + " rule 5 action reject",
          "set firewall name " + RS + " rule 5 description PROTECT-MODE-2026",
          "set firewall name " + RS + " rule 5 protocol tcp",
          "set firewall name " + RS + " rule 5 log enable",
          "set firewall name " + RS + " rule 5 source address " + atk]
elif action == "allow":
    L += ["set firewall name " + RS + " rule 5 action accept",
          "set firewall name " + RS + " rule 5 description PROTECT-OVERRIDE-ALLOW"]
L += ["commit", "save", "exit"]
out = vbash(L)
cur = sh("/opt/vyatta/bin/vyatta-op-cmd-wrapper show configuration commands | grep 'name " + RS + " rule 5 ' | head -2", 40)
if action == "allow":
    ok = "accept" in cur
else:
    ok = "reject" in cur
print(("OK-" + action + " RS=" + RS) if ok else ("FAIL RS=" + RS + " | " + out.strip()[-150:]))
print(cur.strip()[:200])
c.close()
