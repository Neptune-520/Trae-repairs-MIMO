import os
from typing import Any, AsyncIterator

import httpx
from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse

app = FastAPI()

UPSTREAM_BASE_URL = os.getenv("UPSTREAM_BASE_URL", "https://token-plan-cn.xiaomimimo.com")
UPSTREAM_API_KEY = os.getenv("UPSTREAM_API_KEY", "")


def patch_messages(payload: dict[str, Any]) -> dict[str, Any]:
    messages = payload.get("messages")

    if not isinstance(messages, list):
        return payload

    for message in messages:
        if not isinstance(message, dict):
            continue

        if message.get("role") == "assistant" and "reasoning_content" not in message:
            message["reasoning_content"] = ""

    return payload


async def stream_response(
    client: httpx.AsyncClient,
    upstream_resp: httpx.Response,
) -> AsyncIterator[bytes]:
    try:
        async for chunk in upstream_resp.aiter_bytes():
            yield chunk
    except httpx.HTTPError:
        return
    finally:
        await upstream_resp.aclose()
        await client.aclose()


async def proxy_request(request: Request, path: str):
    body = await request.json() if request.method != "GET" else {}
    body = patch_messages(body)

    upstream_url = f"{UPSTREAM_BASE_URL.rstrip('/')}/{path.lstrip('/')}"

    headers = {
        "Content-Type": "application/json",
    }

    if UPSTREAM_API_KEY:
        headers["Authorization"] = f"Bearer {UPSTREAM_API_KEY}"

    stream = bool(body.get("stream"))

    client = httpx.AsyncClient(timeout=None)

    if stream:
        try:
            upstream_req = client.build_request(
                request.method,
                upstream_url,
                headers=headers,
                json=body,
            )
            upstream_resp = await client.send(upstream_req, stream=True)
        except httpx.HTTPError as exc:
            await client.aclose()
            return Response(
                content=str(exc),
                status_code=502,
                media_type="text/plain",
            )

        return StreamingResponse(
            stream_response(client, upstream_resp),
            status_code=upstream_resp.status_code,
            headers={
                "Content-Type": upstream_resp.headers.get(
                    "Content-Type",
                    "text/event-stream"
                )
            },
        )

    async with client:
        try:
            upstream_resp = await client.request(
                request.method,
                upstream_url,
                headers=headers,
                json=body,
            )
        except httpx.HTTPError as exc:
            return Response(
                content=str(exc),
                status_code=502,
                media_type="text/plain",
            )

    return Response(
        content=upstream_resp.content,
        status_code=upstream_resp.status_code,
        media_type=upstream_resp.headers.get("Content-Type", "application/json"),
    )


@app.api_route("/v1/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def v1_proxy(request: Request, path: str):
    return await proxy_request(request, f"v1/{path}")


@app.get("/")
async def root():
    return {
        "ok": True,
        "usage": "Send requests to /v1/{path}, for example /v1/chat/completions",
    }


@app.get("/health")
async def health():
    return {"ok": True}