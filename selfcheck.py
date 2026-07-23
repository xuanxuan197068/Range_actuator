#!/usr/bin/env python3
"""只读真机自检：用 TOPO_COOKIE 连真实靶场，走 MCP 协议验证 session / 项目 / 设备查询。

只做只读操作，绝不创建或下发脚本。
用法：
    export TOPO_COOKIE='登录后的完整 Cookie'
    .venv/bin/python selfcheck.py
"""
from __future__ import annotations

import asyncio
import os

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

REPO = os.path.dirname(os.path.abspath(__file__))


async def main() -> int:
    if not os.environ.get("TOPO_COOKIE"):
        print("✗ 未设置 TOPO_COOKIE。先 export TOPO_COOKIE='...'（或写进 .env）再运行。")
        return 1

    env = dict(os.environ)
    env.setdefault("TOPO_BASE_URL", "http://172.23.215.103/api/topo")
    params = StdioServerParameters(
        command=os.path.join(REPO, ".venv", "bin", "topo-mcp"), args=[], env=env
    )

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print(f"• 已注册工具数: {len(tools.tools)}")

            status = (await session.call_tool("topo_session_status", {})).structuredContent or {}
            print(f"• 登录状态: authenticated={status.get('authenticated')} detail={status.get('detail')}")
            if not status.get("authenticated"):
                print("✗ 未认证：Cookie 可能无效/过期，请更新 TOPO_COOKIE。")
                return 1
            print("✓ 认证通过")

            pl = (await session.call_tool("topo_list_projects", {})).structuredContent or {}
            projects = pl.get("projects", [])
            print(f"• 项目数: {pl.get('count')} (truncated={pl.get('truncated')})")
            for p in projects[:5]:
                print(f"    - {p['id']}  {p['name']}  status={p.get('status')}  vmCount={p.get('vmCount')}")
            if not projects:
                print("✓ 查询通道正常（当前账户下无项目）。")
                return 0

            pid = projects[0]["id"]
            dl = (
                await session.call_tool("topo_list_devices", {"project_id": pid})
            ).structuredContent or {}
            devices = dl.get("devices", [])
            print(f"• 项目 {pid} 设备数: {dl.get('count')}")
            for d in devices[:5]:
                print(f"    - {d['id']}  {d['name']}  os={d['osFamily']}  ip={d.get('ipAddresses')}")

            print("\n✓ 只读自检完成：session / projects / devices 均正常工作。")
            return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
