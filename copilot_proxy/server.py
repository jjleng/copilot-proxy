import json
from typing import Generator

import requests
from mitmproxy import ctx, http

from copilot_proxy.inject_responses import MODELS_TO_INJECT, TOKEN_TO_INJECT
from copilot_proxy.config import MODEL_URL, MODEL_API_KEY, MODEL_NAME


def code_completions(messages: dict) -> Generator[bytes, None, None]:
    """
    Generate code completions using the specified model.
    """
    if not MODEL_URL or not MODEL_API_KEY or not MODEL_NAME:
        raise ValueError("You must specify env vars `MODEL_URL`, `MODEL_API_KEY` and `MODEL_NAME`")

    headers = {
        "Authorization": f"Bearer {MODEL_API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "model": MODEL_NAME,
        "messages": messages,
        "temperature": 0.0,
        "max_tokens": 2500,
        "stream": True,
    }

    with requests.post(MODEL_URL, headers=headers, json=data, stream=True) as response:
        for chunk in response.iter_content(chunk_size=None):
            if chunk:
                yield chunk


def request(flow: http.HTTPFlow) -> None:
    """
    Log details of the incoming HTTP request.
    """
    ctx.log.info(f"Request to {flow.request.pretty_url}")
    ctx.log.info(f"Request method: {flow.request.method}")
    ctx.log.info(f"Request headers: {dict(flow.request.headers)}")
    if flow.request.content and "api.github" in flow.request.pretty_url:
        ctx.log.info(f"Request body: {flow.request.get_text()}")


def responseheaders(flow: http.HTTPFlow) -> None:
    if flow.request.pretty_url == "https://api.githubcopilot.com/chat/completions":
        if not flow.request.content:
            return

        messages = json.loads(flow.request.content.decode("utf-8"))["messages"]
        iterator = code_completions(messages)

        def stream_chunks(data):
            for chunk in iterator:
                yield chunk

        flow.response = http.Response.make(
            200, # Necessary, since we inject wrong token to the client. api.githubcopilot.com/chat/completions returns 401
            # headers fields might not be needed
            headers={
                "Content-Type": "application/json",
                "x-request-id": flow.request.headers[b"x-request-id"],
                "content-security-policy": "default-src 'none'; sandbox",
            },
        )

        del flow.response.headers[b"content-length"]
        # Stream has be to hijacked in responseheaders
        # https://docs.mitmproxy.org/stable/overview-features/#streaming
        flow.response.stream = stream_chunks


def response(flow: http.HTTPFlow) -> None:
    """
    Log details of the outgoing HTTP response and modify specific responses.
    """
    assert flow.response
    ctx.log.info(
        f"Response from {flow.request.pretty_url}: {flow.response.status_code}"
    )
    ctx.log.info(f"Response headers: {dict(flow.response.headers)}")
    if flow.response.content and "api.github" in flow.request.pretty_url:
        ctx.log.info(
            f"Response body for {flow.request.pretty_url}: {flow.response.get_text()}"
        )

    if flow.request.pretty_url == "https://api.githubcopilot.com/models":
        flow.response = http.Response.make(
            200,
            json.dumps(MODELS_TO_INJECT).encode("utf-8"),
            {"Content-Type": "application/json"},
        )
    elif flow.request.pretty_url == "https://api.github.com/copilot_internal/v2/token":
        flow.response = http.Response.make(
            200, json.dumps(TOKEN_TO_INJECT).encode("utf-8"), {"Content-Type": "application/json"}
        )


addons = [
    request,
    responseheaders,
    response,
]

def run(port: int) -> None:
    from mitmproxy.tools.main import mitmdump

    mitmdump(["-p", str(port), "-s", __file__])
