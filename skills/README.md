# 靶场攻防 Skills

跨域总拓扑靶场（148 台 VM × 4 域）配套的攻防组件，全部为纯 Python stdlib 零依赖实现：

| 组件 | 说明 |
|---|---|
| tpot-soc | TPot-SOC 集成安全管理端：EDR/蜜罐/WAF 监控 + 漏洞映射 + 攻防态势 + 策略开关 + 流量机器人控制 |
| honey-agent | 免 Docker 多协议蜜罐引擎（ssh/telnet/http/ftp/redis/mysql），连接/凭据捕获上报 |
| edr | 主机探针（agent）+ 汇聚端（hub），心跳 + auth.log 增量上报 |
| secbridge | 安全设备日志桥：收 syslog → 落盘/统计/视图 → 双路转发 T-Pot |
| bgtraffic | 随机业务背景流量发生器（可限速/开关） |
| fwctl | vyos 边界防火墙双态切换 + 规则管理（list/rule-add/rule-del） |

详细部署与验收见 `tpot-soc/soc.py` 同目录的 TPot-SOC交付说明.md。
