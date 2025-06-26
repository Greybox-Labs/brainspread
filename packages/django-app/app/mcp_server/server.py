import asyncio
import os
import django
from mcp import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
django.setup()

from .tools.page_tools import PageTools
from .tools.block_tools import BlockTools
from .tools.content_tools import ContentTools
from .tools.batch_tools import BatchTools


class BrainspreadMCPServer:
    """Main MCP server for Brainspread knowledge management system"""
    
    def __init__(self):
        self.server = Server("brainspread")
        self.setup_tools()

    def setup_tools(self):
        """Register all tool categories with the server"""
        # Register all tool categories
        page_tools = PageTools(self.server)
        block_tools = BlockTools(self.server)
        content_tools = ContentTools(self.server)
        batch_tools = BatchTools(self.server)

        # Register tools with server
        page_tools.register_tools()
        block_tools.register_tools()
        content_tools.register_tools()
        batch_tools.register_tools()

    async def run(self):
        """Run the MCP server"""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="brainspread",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=None,
                        experimental_capabilities=None,
                    ),
                ),
            )


# For direct usage
async def main():
    """Main entry point for the MCP server"""
    server = BrainspreadMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())