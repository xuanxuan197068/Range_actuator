# 靶场 API MCP 服务 V1.0 实现计划（精简版）

> 本文档可以直接交给编码 Agent 使用。  
> 目标目录：`C:\Users\B1-1205\Desktop\靶场api工具打包`

---

## 1. 项目目标

把现有靶场 API 调用代码整理成一个本地 MCP 服务，让 Agent 可以通过标准工具完成：

- 检查靶场登录状态。
- 查询项目。
- 查询项目中的设备。
- 获取项目设备清单。
- 查询已有脚本。
- 向指定设备提交脚本。
- 查询脚本执行日志。

Agent 只需要关心项目、设备、脚本和执行结果，不需要关心：

- Cookie 如何保存和发送。
- API 地址如何拼接。
- HTTP Header 和请求方法。
- Base64 编解码。
- 远端分页。
- 靶场原始响应格式。

---

## 2. 当前文件的作用

目标目录中已经提取了以下文件：

| 文件 | 作用 | V1.0 处理方式 |
|---|---|---|
| `topo_adapter.py` | 封装项目、设备、脚本和日志相关接口 | 核心迁移文件，改造成新的异步 Adapter |
| `topo_api_client.py` | 发送底层 HTTP 请求 | 不直接复用，重写成固定靶场地址的安全 Transport |
| `schemas.py` | 定义项目、设备、脚本等数据结构 | 提取 V1.0 需要的模型 |
| `settings.py` | 管理配置 | 重写，改成独立项目配置 |
| `session.py` | 获取和管理 Cookie，包含浏览器登录 | 只保留凭据管理思路，删除 Selenium 和浏览器逻辑 |
| `base64_encoder.py` | 对脚本文本进行 Base64 编码 | 只保留纯编码函数 |
| `inventory.py` | 汇总项目和设备信息 | 修改 import 后迁移 |
| `execution.py` | 组织脚本创建、下发和结果合并 | 只参考执行流程，不迁移旧 Job 和线程逻辑 |
| `deployment.py` | 项目部署和清理 | V1.0 暂不迁移 |

这些文件目前还依赖原项目目录，不能直接作为独立项目运行。新项目需要重新建立 package、依赖、入口和测试。

---

## 3. V1.0 功能范围

### 必须实现

建议提供以下 MCP 工具：

```text
topo_session_status
topo_list_projects
topo_list_devices
topo_get_inventory
topo_list_scripts
topo_get_script
topo_list_script_logs
topo_prepare_script_execution
topo_execute_script
```

其中：

- 前 7 个工具负责查询。
- `topo_prepare_script_execution` 负责检查项目、设备、脚本大小和执行参数，并生成执行计划。
- `topo_execute_script` 负责真正提交脚本。

### V1.0 暂不实现

- 项目部署和取消部署。
- reset、强制清场和删除脚本。
- 浏览器自动登录。
- Web UI。
- 多阶段工作流。
- 后台任务队列。
- 任意 API path 调用。
- Agent 自定义 URL、Header 或 Cookie。

---

## 4. 推荐架构

```text
Agent
  ↓ MCP tools
tools.py
  ↓
业务服务 / inventory / execution plan
  ↓
adapter.py
  ↓
transport.py
  ↓
靶场 API
```

旁路组件：

```text
settings.py      管理服务配置
credentials.py   管理 Cookie
models.py        定义输入输出模型
security.py      脱敏、hash 和输入限制
audit.py         记录写操作审计
```

建议的新项目结构：

```text
靶场api工具打包/
  pyproject.toml
  README.md
  .env.example

  src/
    topo_mcp/
      server.py
      tools.py
      settings.py
      credentials.py
      transport.py
      adapter.py
      models.py
      inventory.py
      security.py
      audit.py

  tests/
```

根目录现有 9 个文件保留作为迁移参考，不直接进入正式 package。

---

## 5. 核心实现思路

### 5.1 MCP 服务

- 使用 Python 和 MCP Python SDK。
- V1.0 只提供 stdio MCP。
- 使用明确的业务工具，不提供通用 HTTP 请求工具。
- 输入输出使用 Pydantic 模型，向 Agent 返回统一、简洁的结构化结果。

### 5.2 靶场请求

- 使用 `httpx.AsyncClient`。
- Base URL 只能由服务端配置。
- Adapter 只传相对 API path。
- Cookie 由 Transport 自动注入。
- GET 可以对临时网络故障做少量重试。
- POST 不自动重试，避免重复创建或执行脚本。

### 5.3 Cookie

- 桌面环境优先存入系统 keyring。
- 也可以通过受控的环境变量注入。
- Cookie 不出现在 MCP 参数、返回结果、日志和异常中。
- 删除旧 `session.py` 中的 Selenium 和浏览器登录流程。

### 5.4 查询能力

优先完成项目、设备、Inventory、脚本和日志查询。

查询工具需要做到：

- 自动处理远端分页。
- 限制单次返回数量。
- 不返回脚本 Base64。
- 不返回 Cookie、Authorization 和原始敏感字段。
- 日志过长时进行截断。

### 5.5 脚本执行

脚本执行采用两步：

```text
prepare
  → 校验项目、设备、模式和脚本大小
  → 计算脚本 hash
  → 返回待执行计划

execute
  → 再次核对计划
  → 创建 private script
  → 触发脚本运行
  → 返回 scriptId 和提交状态
```

写操作必须：

- 默认关闭。
- 通过服务端配置显式开启。
- 只允许操作项目 allowlist 中的项目。
- 校验设备确实属于指定项目。
- 限制单次设备数量和脚本大小。
- 使用幂等键，避免同一请求被重复执行。
- 记录项目、设备、脚本名称、脚本 hash 和结果，不记录脚本文本或 Cookie。

### 5.6 当前最重要的接口风险

旧代码调用：

```text
POST /device_scripts/run/private
```

时只发送 `deviceIds + mode`，没有发送 `scriptId`。

正式开放 `topo_execute_script` 前，必须确认该接口只会运行本次创建的脚本。建议优先：

1. 查找可以显式传入 `scriptId` 的接口；或
2. 通过后端代码/API 文档确认 `run/private` 的准确行为；或
3. 只在专门交给本 MCP 独占操作的测试项目中使用。

在这一点没有确认前，可以先发布只读版本，但不要对外宣称脚本执行已经正式可用。

---

## 6. 具体实施计划

### 阶段一：建立独立项目

- 新建 `pyproject.toml`。
- 建立 `src/topo_mcp` package。
- 配置 `topo-mcp` 启动命令。
- 添加 MCP SDK、httpx、Pydantic 和 keyring 等依赖。
- 确保新代码不再依赖原项目的 `backend.*` 和 `tools.*`。

完成结果：项目可以安装，MCP 服务可以启动。

### 阶段二：实现公共基础

- 重写 Settings。
- 实现 CredentialProvider。
- 重写异步 Transport。
- 实现统一错误处理和敏感信息脱敏。
- 迁移 Base64、脚本 hash 和摘要等纯函数。

完成结果：可以安全调用固定靶场 API，Cookie 不暴露给 Agent。

### 阶段三：完成查询工具

- 迁移项目、设备、脚本和日志 Adapter。
- 实现 Inventory 组合逻辑。
- 注册 7 个查询工具。
- 增加结果数量和日志长度限制。

完成结果：Agent 可以完成“项目 → 设备 → 脚本 → 日志”的只读操作。

这一步完成后即可得到第一个可使用的只读 RC。

### 阶段四：完成脚本执行

- 确认 `run/private` 的真实接口语义。
- 实现 prepare 和 execute。
- 增加项目 allowlist、设备归属校验、幂等控制和审计。
- 对同一项目或设备的并发写操作进行限制。

完成结果：Agent 可以安全地向指定设备提交脚本。

### 阶段五：测试和发布

- 使用 mock API 测试所有工具。
- 进行 stdio MCP 冒烟测试。
- 在干净虚拟环境中安装和启动。
- 构建 wheel。
- 编写 README、安装说明、Cookie 初始化方法和 Agent 配置示例。
- 真实写测试只在用户指定的专用项目和设备中执行。

---

## 7. V1.0 最终效果

管理员完成安装和 Cookie 初始化后，只需要在 Agent 中注册：

```json
{
  "mcpServers": {
    "topo": {
      "command": "C:\\path\\to\\venv\\Scripts\\topo-mcp.exe",
      "args": [],
      "env": {
        "TOPO_ENVIRONMENT": "default",
        "TOPO_BASE_URL": "https://target-range.example/api/topo"
      }
    }
  }
}
```

之后 Agent 可以：

1. 查询项目。
2. 找到目标设备。
3. 查看设备和脚本信息。
4. 准备脚本执行计划。
5. 在允许写操作时提交脚本。
6. 查询日志并总结执行结果。

Agent 不需要接触 Cookie、Base64、HTTP Header、API path 和底层响应结构。

---

## 8. V1.0 验收标准

- 新项目可以独立安装和启动。
- 不依赖原 `topo_api_suite` 的 PYTHONPATH。
- MCP Client 能发现并调用工具。
- 项目、设备、Inventory、脚本和日志查询可用。
- Cookie 和脚本文本不会进入日志或错误信息。
- Agent 不能传任意 URL、Header、Cookie 或 API path。
- 写操作默认关闭，项目 allowlist 有效。
- POST 不会被自动重试。
- `run/private` 的语义已经确认后，才启用正式脚本执行。
- mock 测试和 MCP 冒烟测试通过。
- README 和 Agent 配置示例完整。

---

## 9. 给编码 Agent 的要求

1. 只在 `C:\Users\B1-1205\Desktop\靶场api工具打包` 中创建正式项目。
2. 不修改原 `topo_api_suite` 项目。
3. 不复制或读取旧项目中的真实 Cookie。
4. 不通过修改 `PYTHONPATH` 继续依赖旧代码。
5. 不把通用 HTTP Client 直接暴露为 MCP tool。
6. 先完成查询能力，再实现写操作。
7. 写接口语义未确认前保持写操作关闭。
8. 未获得用户明确授权，不调用真实写接口。
9. 完成后报告新增文件、工具列表、测试结果、安装命令和 Agent 配置方法。
