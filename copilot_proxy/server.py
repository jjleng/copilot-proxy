import json
import re
import time
from typing import Any, Generator, Iterator

import requests
from mitmproxy import ctx, http

from copilot_proxy.config import (MODEL_API_KEY, MODEL_NAME, MODEL_URL,
                                  URLS_OF_INTEREST)
from copilot_proxy.inject_responses import MODELS_TO_INJECT, TOKEN_TO_INJECT
from copilot_proxy.utils import parse_sse_stream


# GH Copilot still uses the completion API, which is deprecated. See below
# https://platform.openai.com/docs/api-reference/completions
# And, Ollama and OpenRouter don't support the completions endpoint well.
# Therefore, we do conversions and use the chat completion API instead.
def code_completion(completion_input: dict) -> Generator[bytes, Any, None]:
    if not MODEL_URL or not MODEL_API_KEY or not MODEL_NAME:
        raise ValueError(
            "You must specify env vars `MODEL_URL`, `MODEL_API_KEY` and `MODEL_NAME`"
        )

    # Extracting necessary parts from the completion input
    prompt = completion_input.get("prompt", "")
    suffix = completion_input.get("suffix", "")
    max_tokens = completion_input.get("max_tokens", 500)
    temperature = completion_input.get("temperature", 0.2)
    top_p = completion_input.get("top_p", 1)
    n = completion_input.get("n", 3)
    stop = completion_input.get("stop", [])
    stream = completion_input.get("stream", True)
    extra = completion_input.get("extra", {})

    # Combine prompt and suffix for the user message
    user_prompt = (
        f"{prompt}<insert_your_completion_here>{suffix}\n\n"
        f"Extra Context:\n{json.dumps(extra)}\n\n"
        "The completion is additional code or comments that users might want to add. "
        "Do not repeat the first line of the suffix in your response. "
        "Do not use markdown or code blocks; just print the code or comments directly. "
        f"Now insert your completion at the place marked by `<insert_your_completion_here>`"
    )

    # Formatting the chat completion API input
    system_prompt = "You are an expert programmer that completes code snippets."

    # Formatting the chat completion API input
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    chat_completion_input = {
        "model": MODEL_NAME,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": top_p,
        "n": n,
        "stop": stop,
        "stream": stream,
    }

    # Making the API call
    url = MODEL_URL
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {MODEL_API_KEY}",
    }

    # `stream`` is always True
    response = requests.post(
        url, headers=headers, data=json.dumps(chat_completion_input), stream=stream
    )
    response.raise_for_status()

    for data in parse_sse_stream(response=response):
        decoded_line = data.strip()
        if not decoded_line:
            continue
        if decoded_line == "[DONE]":
            break

        data_dict = json.loads(decoded_line)
        choices = data_dict.get("choices", [])

        for choice in choices:
            content = choice.get("delta", {}).get("content", "")
            if content:
                result = {
                    "id": data_dict.get("id"),
                    "created": data_dict.get("created") or int(time.time()),
                    "choices": [
                        {
                            "text": content,
                            "index": choice.get("index"),
                            "finish_reason": choice.get("finish_reason"),
                            "logprobs": choice.get("logprobs"),
                            "p": "aaaa",
                        }
                    ],
                }
                yield f"data: {json.dumps(result)}\n\n".encode("utf-8")
    yield "data: [DONE]\n\n".encode("utf-8")


def code_gen(messages: dict) -> Generator[bytes, None, None]:
    """
    Generate code using the specified model.
    """
    if not MODEL_URL or not MODEL_API_KEY or not MODEL_NAME:
        raise ValueError(
            "You must specify env vars `MODEL_URL`, `MODEL_API_KEY` and `MODEL_NAME`"
        )

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
    if flow.request.content and re.search(URLS_OF_INTEREST, flow.request.pretty_url):
        ctx.log.info(
            f"Request body for {flow.request.pretty_url}: {flow.request.get_text()}"
        )


def handle_streaming_response(
    flow: http.HTTPFlow, iterator: Iterator[bytes], content_type: str
) -> None:
    def stream_chunks(data):
        for chunk in iterator:
            yield chunk

    flow.response = http.Response.make(
        200,  # Necessary, since we inject wrong token to the client. api.githubcopilot.com/chat/completions returns 401
        # headers fields might not be needed
        headers={
            "Content-Type": content_type,
            "x-request-id": flow.request.headers[b"x-request-id"],
            "content-security-policy": "default-src 'none'; sandbox",
        },
    )

    del flow.response.headers[b"content-length"]
    # Stream has be to hijacked in responseheaders
    # https://docs.mitmproxy.org/stable/overview-features/#streaming
    flow.response.stream = stream_chunks


def responseheaders(flow: http.HTTPFlow) -> None:
    if not flow.request.content:
        return

    if flow.request.pretty_url == "https://api.githubcopilot.com/chat/completions":
        messages = json.loads(flow.request.content.decode("utf-8"))["messages"]
        handle_streaming_response(flow, code_gen(messages), "application/json")
    elif (
        flow.request.pretty_url
        == "https://copilot-proxy.githubusercontent.com/v1/engines/copilot-codex/completions"
    ):
        body = json.loads(flow.request.content.decode("utf-8"))
        handle_streaming_response(flow, code_completion(body), "text/event-stream")


def response(flow: http.HTTPFlow) -> None:
    """
    Log details of the outgoing HTTP response and modify specific responses.
    """
    assert flow.response
    ctx.log.info(
        f"Response from {flow.request.pretty_url}: {flow.response.status_code}"
    )
    ctx.log.info(f"Response headers: {dict(flow.response.headers)}")
    if flow.response.content and re.search(URLS_OF_INTEREST, flow.request.pretty_url):
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
            200,
            json.dumps(TOKEN_TO_INJECT).encode("utf-8"),
            {"Content-Type": "application/json"},
        )


addons = [
    request,
    responseheaders,
    response,
]


def run(port: int) -> None:
    from mitmproxy.tools.main import mitmdump

    mitmdump(["-p", str(port), "-s", __file__])
