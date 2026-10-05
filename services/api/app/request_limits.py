"""Bound JSON metadata requests without trusting Content-Length or loading unbounded bodies."""
from starlette.responses import JSONResponse


class MetadataSafetyMiddleware:
    def __init__(self, app, max_bytes: int = 2 * 1024 * 1024):
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        original_receive = receive
        if scope["method"] in {"POST", "PUT", "PATCH"}:
            body = bytearray()
            while True:
                message = await original_receive()
                if message["type"] == "http.disconnect":
                    return
                body.extend(message.get("body", b""))
                if len(body) > self.max_bytes:
                    await JSONResponse({"detail":"Metadata request exceeds 2 MiB limit"},status_code=413)(scope,receive,send)
                    return
                if not message.get("more_body",False):
                    break
            replayed = False

            async def bounded_receive():
                nonlocal replayed
                if not replayed:
                    replayed = True
                    return {"type":"http.request", "body":bytes(body), "more_body":False}
                return await original_receive()
            receive = bounded_receive

        async def security_send(message):
            if message["type"] == "http.response.start":
                headers = [(key,value) for key,value in message.get("headers",[]) if key.lower() != b"server"]
                headers.extend([(b"x-content-type-options",b"nosniff"), (b"referrer-policy",b"no-referrer"),
                                (b"x-frame-options",b"DENY")])
                message = {**message,"headers":headers}
            await send(message)
        await self.app(scope, receive, security_send)
