from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from .services import (
    AIProviderError,
    GeminiChatProvider,
    OpenAIChatProvider,
    get_generation_provider,
)


def test_factory_selects_openai_provider(settings):
    settings.AI_GENERATION_PROVIDER = 'openai'
    settings.OPENAI_API_KEY = 'test-openai-key'

    with patch('apps.ai_assistant.services.OpenAI') as client_class:
        provider = get_generation_provider()

    assert isinstance(provider, OpenAIChatProvider)
    client_class.assert_called_once_with(
        api_key='test-openai-key',
        timeout=settings.AI_REQUEST_TIMEOUT_SECONDS,
    )


def test_factory_selects_gemini_provider_with_compatible_base_url(settings):
    settings.AI_GENERATION_PROVIDER = 'gemini'
    settings.GEMINI_GENERATION_MODEL = 'gemini-3.1-flash-lite'
    settings.GEMINI_API_KEY = 'test-gemini-key'
    settings.GEMINI_BASE_URL = (
        'https://generativelanguage.googleapis.com/v1beta/openai/'
    )

    with patch('apps.ai_assistant.services.OpenAI') as client_class:
        provider = get_generation_provider()

    assert isinstance(provider, GeminiChatProvider)
    assert provider.model == 'gemini-3.1-flash-lite'
    client_class.assert_called_once_with(
        api_key='test-gemini-key',
        timeout=settings.AI_REQUEST_TIMEOUT_SECONDS,
        base_url=settings.GEMINI_BASE_URL,
    )


def test_gemini_provider_sends_messages_and_returns_safe_result(settings):
    settings.GEMINI_GENERATION_MODEL = 'gemini-3.1-flash-lite'
    settings.GEMINI_API_KEY = 'test-gemini-key'
    messages = [{'role': 'user', 'content': 'RAG là gì?'}]
    response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content='Câu trả lời.'))],
        usage=SimpleNamespace(total_tokens=17),
    )

    with patch('apps.ai_assistant.services.OpenAI') as client_class:
        completion = Mock(return_value=response)
        client_class.return_value.chat.completions.create = completion
        result = GeminiChatProvider().generate(messages)

    assert result == {'content': 'Câu trả lời.', 'tokens_used': 17}
    completion.assert_called_once_with(
        model='gemini-3.1-flash-lite',
        messages=messages,
        temperature=0.4,
        max_tokens=1000,
    )


@pytest.mark.parametrize('provider_name', ['openai', 'gemini'])
def test_selected_provider_requires_its_server_side_key(settings, provider_name):
    settings.AI_GENERATION_PROVIDER = provider_name
    settings.OPENAI_API_KEY = ''
    settings.GEMINI_API_KEY = ''

    with patch('apps.ai_assistant.services.OpenAI') as client_class:
        with pytest.raises(AIProviderError, match='not configured'):
            get_generation_provider()

    client_class.assert_not_called()


def test_unknown_provider_fails_closed(settings):
    settings.AI_GENERATION_PROVIDER = 'unknown-provider'

    with pytest.raises(AIProviderError, match='not configured'):
        get_generation_provider()
