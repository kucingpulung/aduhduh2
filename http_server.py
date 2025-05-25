import asyncio
import logging

class HTTPServer:
    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port
        self.logger = logging.getLogger(__name__)

    async def handle_request(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        try:
            request = await reader.read(1024)
            if not request:
                return

            request_line = request.decode().splitlines()[0]
            self.logger.info("HTTP Request: %s", request_line)

            path = request.decode().split(" ")[1]
            if path == "/":
                response = (
                    "HTTP/1.1 200 OK\r\n"
                    "Content-Type: text/plain\r\n"
                    "\r\n"
                    "Bot is running!"
                )
            else:
                response = (
                    "HTTP/1.1 404 Not Found\r\n"
                    "Content-Type: text/plain\r\n"
                    "\r\n"
                    "404 Not Found"
                )

            writer.write(response.encode())
            await writer.drain()
        except Exception as e:
            self.logger.error(f"HTTP error: {e}")
        finally:
            writer.close()
            await writer.wait_closed()

    async def run_server(self) -> None:
        server = await asyncio.start_server(self.handle_request, self.host, self.port)
        self.logger.info("HTTP server listening on %s:%d", self.host, self.port)
        async with server:
            await server.serve_forever()
