# topo-mcp — 靶场 API 本地 MCP 服务（V1）

把靶场（topo）API 封装成一个本地 **stdio MCP 服务**，让 Agent 只在「项目 → 设备 → 脚本 → 日志 → 执行」层面工作，完全不接触 Cookie、Base64、HTTP header、API path、分页。

第一版通过**环境变量注入 Cookie**（`TOPO_COOKIE`），不含浏览器登录 / keyring / 多阶段工作流 / 后台任务队列。

## 工具一览（9 个）

| 工具 | 说明 |
|---|---|
| `topo_session_status` | 检查登录状态（Cookie 是否有效、靶场是否可达） |
| `topo_list_projects` | 列出所有项目（自动翻页，超量截断） |
| `topo_list_devices` | 列出项目下已部署设备（可按 name/ip/sys_type 过滤） |
| `topo_get_inventory` | 项目信息 + 设备清单汇总 |
| `topo_list_scripts` | 列出脚本（只含元信息 + hash + 摘要，**无内容/base64**） |
| `topo_get_script` | 查询单个脚本元信息（**无内容/base64**） |
| `topo_list_script_logs` | 查询执行日志（长 outMsg/errMsg 截断） |
| `topo_prepare_script_execution` | 校验并生成执行计划（返回 `planId`，不触碰后端写接口） |
| `topo_execute_script` | 按计划真正下发脚本（需开关 + confirm） |

## 安装

需要 Python ≥ 3.10。

```bash
cd /home/xuan/Range_actuator
python3 -m venv .venv
.venv/bin/pip install -e .
```

## 配置（环境变量，前缀 `TOPO_`）

复制 `.env.example` 为 `.env` 并填写，或在 Agent 的 `mcpServers.env` 里注入同名变量。

| 变量 | 默认 | 说明 |
|---|---|---|
| `TOPO_BASE_URL` | `http://172.23.215.103/api/topo` | 靶场根地址（只由服务端配置） |
| `TOPO_COOKIE` | 空 | 登录后复制的完整 Cookie 头值 |
| `TOPO_ALLOW_EXECUTE` | `false` | 写开关，`true` 才允许 `topo_execute_script` 真正下发 |
| `TOPO_PROJECT_ALLOWLIST` | 空=不限制 | 逗号分隔的项目 id/name 白名单 |
| `TOPO_MAX_DEVICES_PER_EXEC` | `20` | 单次执行设备数上限 |
| `TOPO_MAX_SCRIPT_BYTES` | `65536` | 单脚本字节上限 |
| `TOPO_API_PAGE_SIZE` / `TOPO_MAX_ITEMS` | `200` / `500` | 远端分页 / 查询返回上限 |
| `TOPO_HTTP_TIMEOUT` / `TOPO_GET_RETRIES` | `30` / `2` | 超时秒 / 仅 GET 重试次数 |
| `TOPO_LOG_MSG_MAXLEN` | `4000` | 日志消息截断长度 |

**获取 Cookie**：浏览器登录靶场后，从开发者工具的任一请求里复制完整 `Cookie` 请求头值，粘进 `TOPO_COOKIE`。

## 运行

```bash
.venv/bin/topo-mcp          # 走 stdio，一般由 MCP 客户端/Agent 拉起
```

## 在 Agent 里注册（示例）

```json
{
  "mcpServers": {
    "topo": {
      "command": "/home/xuan/Range_actuator/.venv/bin/topo-mcp",
      "args": [],
      "env": {
        "TOPO_BASE_URL": "http://172.23.215.103/api/topo",
        "TOPO_COOKIE": "在此粘贴 Cookie",
        "TOPO_ALLOW_EXECUTE": "true"
      }
    }
  }
}
```

## 典型流程（对应 run.txt）

1. `topo_list_projects` → 找到目标项目。
2. `topo_list_devices` → 按公司网络 / IP / 名称筛出目标设备（如主/辅域控）。
3. `topo_prepare_script_execution`（`language` = bash/powershell，`mode` = ssh/qga）→ 校验并拿到 `planId`。
4. `topo_execute_script(plan_id, confirm=true)` → 逐设备建私有脚本 → 置 ready → `run/private` 下发。
5. `topo_list_script_logs`（按 `projectId` + `scriptId`）→ 轮询结果，**重点看 `outMsg`**，而非只看 `status=success`。

## 安全设计要点

- 不暴露通用 HTTP 工具；Base URL 只由服务端配置，Agent 不能传任意 URL/Header/Cookie/path。
- Cookie 由 transport 注入，**不进入**任何工具参数、返回值、日志、异常。
- 查询工具不返回脚本 base64/明文，只给 hash + 摘要。
- 写操作两步（prepare → execute），默认由 `TOPO_ALLOW_EXECUTE` 关闭，需 `confirm=true`；受项目白名单、设备归属、设备数/脚本大小限制约束。
- `run/private` 下发的是「设备当前 ready 的私有脚本」；执行时会在下发前把本次脚本显式置 ready，并以 `plan_id` 做幂等，避免重复下发。
- GET 允许少量重试，POST/PUT/DELETE 不自动重试。

## 测试

```bash
.venv/bin/pip install -e ".[dev]"
.venv/bin/pytest        # 离线单测，不连真实靶场
```

## 注意事项
务必让agent读取topo-swagger-summary.md使其熟知调用方式。
