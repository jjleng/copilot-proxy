from copilot_proxy.utils import (generate_epoch_15min_later, generate_fake_asn,
                                 generate_fake_ip, generate_random_string)

MODELS_TO_INJECT = {
    "data": [
        {
            "capabilities": {
                "family": "gpt-3.5-turbo",
                "limits": {"max_prompt_tokens": 7168},
                "object": "model_capabilities",
                "type": "chat",
            },
            "id": "gpt-3.5-turbo",
            "name": "GPT 3.5 Turbo",
            "object": "model",
            "version": "gpt-3.5-turbo-0613",
        },
        {
            "capabilities": {
                "family": "gpt-3.5-turbo",
                "limits": {"max_prompt_tokens": 7168},
                "object": "model_capabilities",
                "type": "chat",
            },
            "id": "gpt-3.5-turbo-0613",
            "name": "GPT 3.5 Turbo (2023-06-13)",
            "object": "model",
            "version": "gpt-3.5-turbo-0613",
        },
        {
            "capabilities": {
                "family": "gpt-4",
                "limits": {"max_prompt_tokens": 6144},
                "object": "model_capabilities",
                "type": "chat",
            },
            "id": "gpt-4",
            "name": "GPT 4",
            "object": "model",
            "version": "gpt-4-0613",
        },
        {
            "capabilities": {
                "family": "gpt-4",
                "limits": {"max_prompt_tokens": 6144},
                "object": "model_capabilities",
                "type": "chat",
            },
            "id": "gpt-4-0613",
            "name": "GPT 4 (2023-06-13)",
            "object": "model",
            "version": "gpt-4-0613",
        },
        {
            "capabilities": {
                "family": "gpt-4-turbo",
                "limits": {"max_prompt_tokens": 6144},
                "object": "model_capabilities",
                "type": "chat",
            },
            "id": "gpt-4-0125-preview",
            "name": "GPT 4 Turbo (2024-01-25 Preview)",
            "object": "model",
            "version": "gpt-4-0125-preview",
        },
        {
            "capabilities": {
                "family": "text-embedding-ada-002",
                "limits": {"max_inputs": 256},
                "object": "model_capabilities",
                "type": "embeddings",
            },
            "id": "text-embedding-ada-002",
            "name": "Embedding V2 Ada",
            "object": "model",
            "version": "text-embedding-ada-002",
        },
        {
            "capabilities": {
                "family": "text-embedding-ada-002",
                "object": "model_capabilities",
                "type": "embeddings",
            },
            "id": "text-embedding-ada-002-index",
            "name": "Embedding V2 Ada (Index)",
            "object": "model",
            "version": "text-embedding-ada-002",
        },
        {
            "capabilities": {
                "family": "text-embedding-3-small",
                "object": "model_capabilities",
                "type": "embeddings",
            },
            "id": "text-embedding-3-small",
            "name": "Embedding V3 small",
            "object": "model",
            "version": "text-embedding-3-small",
        },
        {
            "capabilities": {
                "family": "text-embedding-3-small",
                "object": "model_capabilities",
                "type": "embeddings",
            },
            "id": "text-embedding-3-small-inference",
            "name": "Embedding V3 small (Inference)",
            "object": "model",
            "version": "text-embedding-3-small",
        },
    ],
    "object": "list",
}

tid = generate_random_string()
expire_time = generate_epoch_15min_later()

TOKEN_TO_INJECT = {
    "annotations_enabled": False,
    "chat_enabled": True,
    "chat_jetbrains_enabled": True,
    "code_quote_enabled": True,
    "codesearch": False,
    "copilot_ide_agent_chat_gpt4_small_prompt": False,
    "copilotignore_enabled": False,
    "endpoints": {
        "api": "https://api.githubcopilot.com",
        "origin-tracker": "https://origin-tracker.githubusercontent.com",
        "proxy": "https://copilot-proxy.githubusercontent.com",
        "telemetry": "https://copilot-telemetry-service.githubusercontent.com",
    },
    "expires_at": expire_time,
    "individual": True,
    "nes_enabled": False,
    "prompt_8k": True,
    "public_suggestions": "disabled",
    "refresh_in": 1500,
    "sku": "monthly_subscriber",
    "snippy_load_test_enabled": False,
    "telemetry": "disabled",
    "token": f"tid={tid};exp={expire_time};sku=monthly_subscriber;st=dotcom;chat=1;8kp=1;ip={generate_fake_ip()};asn={generate_fake_asn()}",
    "tracking_id": tid,
    "vsc_electron_fetcher": False,
}
