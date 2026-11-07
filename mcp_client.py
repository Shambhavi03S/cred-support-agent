"""Task 14: standalone MCP client (separate process from the LangGraph agent).

Connects to the running MCP server, lists tools and calls check_loan_application_status
for several record IDs, printing the standardised MCP response for each.
"""
import asyncio
import json
import os
import sys

from fastmcp import Client

URL = os.getenv("MCP_URL", "http://127.0.0.1:8001/mcp")
IDS = sys.argv[1:] or ["LA-1001", "LA-1005", "LA-9999"]


async def main() -> int:
    async with Client(URL) as client:
        tools = await client.list_tools()
        print("MCP tools:", [t.name for t in tools])
        for rid in IDS:
            res = await client.call_tool("check_loan_application_status", {"record_id": rid})
            print(f"\n--- call_tool(record_id={rid!r}) isError={res.is_error}")
            print("structured:", json.dumps(res.structured_content or res.data, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
