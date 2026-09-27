"""Offline CKAIS boundary tests with the real ADK orchestration and CAIF tool."""
import asyncio
from pathlib import Path
import socket

from google.adk.models import BaseLlm, LlmResponse
from google.genai import types
import pytest

import ckais_agent as app

SPANS = ('約三16', 'Jn 3:16', '創世紀1-3章', 'Jude 5', 'John 3:16,18')


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError('Offline test attempted network access')
    monkeypatch.setattr(socket.socket, 'connect', forbidden)
    monkeypatch.setattr(socket, 'create_connection', forbidden)
    monkeypatch.setattr(socket, 'getaddrinfo', forbidden)
    for key in ('GOOGLE_API_KEY', 'GEMINI_API_KEY', 'CAIF_ADK_MODEL', 'GOOGLE_GENAI_USE_VERTEXAI'):
        monkeypatch.delenv(key, raising=False)


class ScriptedModel(BaseLlm):
    model: str = 'scripted-offline'

    async def generate_content_async(self, llm_request, stream=False):
        responses = [p.function_response for c in llm_request.contents
                     for p in c.parts or [] if p.function_response]
        if responses:
            payload = responses[-1].response
            # Deliberately misleading presentation cannot become canonical data.
            text = ('I claim success: John 3:16.' if 'error' in payload else
                    'Genesis 1:1-3:24' if payload['book'] == 'Genesis' else 'Normalized reference.')
            yield LlmResponse(content=types.Content(role='model', parts=[types.Part(text=text)]))
        else:
            message = next(p.text for c in llm_request.contents if c.role == 'user'
                           for p in c.parts or [] if p.text)
            span = dict(zip(app.EXAMPLES, SPANS))[message]
            yield LlmResponse(content=types.Content(role='model', parts=[types.Part(
                function_call=types.FunctionCall(name='normalize_bible_reference', args={'raw_reference': span}))]))


def test_exact_existing_tool_and_application_instruction():
    import bible_reference_tool
    assert app.create_agent(ScriptedModel()).tools == [bible_reference_tool.bible_reference_tool]
    assert not app.create_agent(ScriptedModel()).sub_agents
    for semantic in ('Jude', '約三16', 'Genesis', 'verse_counts', 'protestant', 'alias'):
        assert semantic not in app.INSTRUCTION


@pytest.mark.parametrize('message,span', list(zip(app.EXAMPLES, SPANS)))
def test_application_boundary(message, span):
    record, = asyncio.run(app.observe_requests(ScriptedModel(), [message]))
    expected = app._adapter.normalize_bible_reference(span)
    assert record['user'] == message
    assert record['tool_calls'][0]['args'] == {'raw_reference': span}
    if 'error' in expected:
        assert record['canonical_results'] == []
        assert record['tool_errors'][0]['payload'] == expected
        assert expected['error']['type'] == 'UnsupportedSyntax'
        assert 'claim success' in record['presentation'][0]
    else:
        assert record['canonical_results'][0]['payload'] == expected
        assert record['canonical_results'][0]['payload']['original_text'] == span
        assert record['tool_errors'] == []
        if expected['book'] == 'Genesis':
            assert expected['verse_start'] is expected['verse_end'] is None
            assert record['presentation'] == ['Genesis 1:1-3:24']
    assert record['presentation']


def test_unrelated_working_directory(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    assert app._load_adapter() is app._adapter
    assert Path(app._adapter.__file__).name == 'bible_reference_tool.py'
    record, = asyncio.run(app.observe_requests(ScriptedModel(), [app.EXAMPLES[0]]))
    assert record['canonical_results'][0]['payload']['original_text'] == SPANS[0]


@pytest.mark.parametrize('configuration', [{}, {'CAIF_ADK_MODEL': 'gemini-placeholder'},
    {'GOOGLE_GENAI_USE_VERTEXAI': 'true'}])
def test_live_preflight(monkeypatch, configuration):
    for key, value in configuration.items():
        monkeypatch.setenv(key, value)
    with pytest.raises(RuntimeError):
        asyncio.run(app.run_live_experiment())
