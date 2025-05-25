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

            self.logger.info("HTTP request: %s", request.decode().splitlines()[0])

            path = request.decode().split(" ")[1]
            if path == "/":
                response = (
                    "HTTP/1.1 200 OK\r\n"
                    "Content-Type: text/html\r\n"
                    "\r\n"
                    "<html><head><title>Teleshare</title></head><body><h1>Teleshare</h1><p>Bot aktif dan sehat.</p></body></html>"
                )
            else:
                response = "HTTP/1.1 404 Not Found\r\n\r\n<h1>404 Not Found</h1>"

            writer.write(response.encode())
            await writer.drain()
        except ConnectionResetError:
            self.logger.info("Connection lost")
        finally:
            writer.close()
            await writer.wait_closed()

    async def run_server(self) -> None:
        server = await asyncio.start_server(self.handle_request, self.host, self.port)
        self.logger.info("HTTPServer running on %s:%d", self.host, self.port)
        async with server:
            await server.serve_forever()
