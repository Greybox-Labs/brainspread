import asyncio
from typing import Any

from django.core.management.base import BaseCommand

from mcp_server.server import BrainspreadMCPServer


class Command(BaseCommand):
    help = 'Run the Brainspread MCP server'

    def add_arguments(self, parser):
        parser.add_argument(
            '--host',
            type=str,
            default='localhost',
            help='Host to bind the server to (not used for stdio)',
        )
        parser.add_argument(
            '--port',
            type=int,
            default=8888,
            help='Port to bind the server to (not used for stdio)',
        )

    def handle(self, *args: Any, **options: Any) -> None:
        self.stdout.write(
            self.style.SUCCESS('Starting Brainspread MCP server...')
        )
        
        try:
            server = BrainspreadMCPServer()
            asyncio.run(server.run())
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.SUCCESS('MCP server stopped.')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error running MCP server: {e}')
            )
            raise