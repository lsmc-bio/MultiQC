from typing import Any, Dict, Optional

from multiqc import config
from multiqc.core import ai


def test_openai_default_provider_auto_detects_from_env(monkeypatch):
    monkeypatch.delenv("SEQERA_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("TOWER_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "dummy-openai-key")

    config.ai_summary = True
    config.ai_provider = None
    config.ai_model = None

    client = ai.get_llm_client()

    assert isinstance(client, ai.OpenAiClient)
    assert client.api_key == "dummy-openai-key"
    assert client.model == ai.DEFAULT_OPENAI_MODEL


def test_openai_explicit_provider_uses_default_gpt55_model(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "dummy-openai-key")

    config.ai_summary = True
    config.ai_provider = "openai"
    config.ai_model = None

    client = ai.get_llm_client()

    assert isinstance(client, ai.OpenAiClient)
    assert client.model == "gpt-5.5"
    assert client.max_tokens() == ai.GPT55_CONTEXT_WINDOW


def test_gpt5_family_uses_reasoning_parameters(monkeypatch):
    captured_body: Optional[Dict[str, Any]] = None

    def fake_request(self, url, headers, body, retries=None):
        nonlocal captured_body
        captured_body = body
        return {"choices": [{"message": {"content": "- ok"}}], "model": body["model"]}

    monkeypatch.setattr(ai.OpenAiClient, "_request_with_error_handling_and_retries", fake_request)

    config.ai_model = "gpt-5.5"
    config.ai_reasoning_effort = None
    config.ai_max_completion_tokens = None
    config.ai_extra_query_options = None

    client = ai.OpenAiClient("dummy-openai-key")
    response = client._query("Summarize this report")

    assert response.model == "gpt-5.5"
    assert captured_body is not None
    assert captured_body["model"] == "gpt-5.5"
    assert captured_body["max_completion_tokens"] == 4000
    assert captured_body["reasoning_effort"] == "medium"
    assert "temperature" not in captured_body
    assert captured_body["messages"][0]["role"] == "developer"
