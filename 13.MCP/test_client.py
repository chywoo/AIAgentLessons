import asyncio

from mcp import Client


async def main():
    async with Client("http://localhost:8000/mcp") as client:
        print("Server:", client.server_info)
        print("Protocol:", client.protocol_version)

        result = await client.list_tools()
        # for tool in result.tools:
        #     print()
        #     print("Name:", tool.name)
        #     print("Desription:", tool.description)
        #     print("Schema:", tool.input_schema)

        result = await client.call_tool(
            "calculator",
            {
                "a": 123,
                "b": 456,
                "operation": "multiply",
            },
        )

        print("Result:", result.content)


if __name__ == "__main__":
    asyncio.run(main())
