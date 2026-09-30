"""Offline CKAIS boundary tests with the real ADK orchestration and CAIF tool."""
import asyncio
from pathlib import Path
import socket

from google.adk.models import BaseLlm, LlmResponse
from google.genai import types
import pytest

import ckais_agent as app

NORMALIZATION_CASES = {
    'Please normalize 約三16': '約三16',
    'Normalize Jn 3:16': 'Jn 3:16',
    '請把創世紀1-3章標準化': '創世紀1-3章',
    'Normalize Jude 5': 'Jude 5',
    'Please normalize John 3:16,18': 'John 3:16,18',
}
UNAVAILABLE_CASES = {
    'What passage is Jn 3:16?': 'Bible-text retrieval is unavailable in this experiment.',
    'What does Jn 3:16 say?': 'Bible-text retrieval is unavailable in this experiment.',
    'Explain Jn 3:16': 'Passage explanation is unavailable in this experiment.',
    'Find sermons about Jn 3:16': 'Sermon retrieval is unavailable in this experiment.',
}
CLARIFICATION_CASES = {
    'Help me with Jn 3:16': 'Do you want the reference normalized, the passage text, or an explanation?',
}


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
    # Fixture decisions are supplied, not inferred: these tests verify the
    # application boundary, not live-model compliance with the instruction.
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
            presentation = {**UNAVAILABLE_CASES, **CLARIFICATION_CASES}.get(message)
            if presentation:
                yield LlmResponse(content=types.Content(role='model', parts=[types.Part(text=presentation)]))
                return
            span = NORMALIZATION_CASES[message]
            yield LlmResponse(content=types.Content(role='model', parts=[types.Part(
                function_call=types.FunctionCall(name='normalize_bible_reference', args={'raw_reference': span}))]))


def test_exact_existing_tool_and_application_instruction():
    import bible_reference_tool
    assert app.create_agent(ScriptedModel()).tools == [bible_reference_tool.bible_reference_tool]
    assert not app.create_agent(ScriptedModel()).sub_agents
    for semantic in ('Jude', '約三16', 'Genesis', 'verse_counts', 'protestant', 'alias'):
        assert semantic not in app.INSTRUCTION


@pytest.mark.parametrize('message,span', list(NORMALIZATION_CASES.items()))
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
    assert record['canonical_results'][0]['payload']['original_text'] == '約三16'


@pytest.mark.parametrize('configuration', [{}, {'CAIF_ADK_MODEL': 'gemini-placeholder'},
    {'GOOGLE_GENAI_USE_VERTEXAI': 'true'}])
def test_live_preflight(monkeypatch, configuration):
    for key, value in configuration.items():
        monkeypatch.setenv(key, value)
    with pytest.raises(RuntimeError):
        asyncio.run(app.run_live_experiment())


@pytest.mark.parametrize('message,presentation', list({**UNAVAILABLE_CASES, **CLARIFICATION_CASES}.items()))
def test_unavailable_or_unclear_intent_has_no_canonical_success(monkeypatch, message, presentation):
    def forbidden(*args, **kwargs):
        pytest.fail('Normalization must not substitute for an unavailable or unclear task')
    monkeypatch.setattr(app._adapter._capability, 'normalize_reference', forbidden)
    record, = asyncio.run(app.observe_requests(ScriptedModel(), [message]))
    assert record['user'] == message
    assert record['tool_calls'] == []
    assert record['canonical_results'] == []
    assert record['tool_errors'] == []
    assert record['presentation'] == [presentation]


def test_agent_receives_capability_selection_instruction():
    instruction = app.create_agent(ScriptedModel()).instruction
    assert instruction == app.INSTRUCTION
    for requirement in ('can fulfill the requested task', 'do not call normalization as a substitute',
                        'genuinely ambiguous intent', 'ask what the user',
                        'passage-text requests', 'not canonical data'):
        assert requirement in instruction
    assert set(app.EXAMPLES) == set(NORMALIZATION_CASES) | set(UNAVAILABLE_CASES) | set(CLARIFICATION_CASES)
