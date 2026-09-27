"""Deterministic orchestration tests, not evidence of live model behavior."""
import asyncio
import socket

import pytest
from google.adk.models import BaseLlm, LlmResponse
from google.genai import types

import minimal_agent as experiment
from bible_reference_tool import bible_reference_tool, normalize_bible_reference


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError('Offline tests must not contact a model or network')
    monkeypatch.setattr(socket.socket, 'connect', forbidden)
    monkeypatch.setattr(socket, 'create_connection', forbidden)
    monkeypatch.setattr(socket, 'getaddrinfo', forbidden)
    for key in ('GOOGLE_API_KEY', 'GEMINI_API_KEY', 'CAIF_ADK_MODEL', 'GOOGLE_GENAI_USE_VERTEXAI'):
        monkeypatch.delenv(key, raising=False)


def test_agent_construction():
    agent = experiment.create_agent('gemini-offline-placeholder')
    assert agent.tools == [bible_reference_tool]
    assert not agent.sub_agents
    assert agent.instruction == experiment.INSTRUCTION
    assert len(agent.instruction.split()) < 90
    for domain_detail in ('約', 'Jude', 'protestant', 'verse_counts', 'zh-Hant', 'chapter_start'):
        assert domain_detail not in agent.instruction


@pytest.mark.parametrize('configuration', [{}, {'CAIF_ADK_MODEL': 'gemini-placeholder'},
    {'GOOGLE_GENAI_USE_VERTEXAI': 'true'}])
def test_live_preflight_stops_without_configuration(monkeypatch, configuration):
    for name, value in configuration.items():
        monkeypatch.setenv(name, value)
    with pytest.raises(RuntimeError):
        asyncio.run(experiment.run_live_experiment())


class ScriptedModel(BaseLlm):
    """Supply known function calls; never simulate autonomous model judgment."""
    model: str = 'scripted-offline'

    async def generate_content_async(self, llm_request, stream=False):
        responses = [part.function_response for content in llm_request.contents
                     for part in content.parts or [] if part.function_response]
        if responses:
            result = responses[-1].response
            text = 'Please clarify the reference.' if 'error' in result else 'The tool normalized the reference.'
            yield LlmResponse(content=types.Content(role='model', parts=[types.Part(text=text)]))
        else:
            message = next(part.text for content in llm_request.contents if content.role == 'user'
                           for part in content.parts or [] if part.text)
            span = dict(experiment.EXAMPLES)[message]
            yield LlmResponse(content=types.Content(role='model', parts=[types.Part(
                function_call=types.FunctionCall(name='normalize_bible_reference', args={'raw_reference': span}))]))


def test_real_runner_capture_with_scripted_model():
    records = asyncio.run(experiment._run_experiment(ScriptedModel()))
    assert len(records) == 5
    for record, (message, span) in zip(records, experiment.EXAMPLES):
        assert record['user'] == message
        assert len(record['tool_calls']) == len(record['tool_responses']) == 1
        assert record['tool_calls'][0]['args'] == {'raw_reference': span}
        assert record['tool_responses'][0]['response'] == normalize_bible_reference(span)
        assert record['checks'][0]['event_equals_adapter_return'] is True
        assert record['checks'][0]['raw_reference_matches_user_span'] is True
        assert record['final_responses']
    assert records[-1]['checks'][0]['adapter_error'] is True
    assert records[-1]['final_responses'] == ['Please clarify the reference.']
    assert records[-1]['checks'][0]['original_text_matches_user_span'] is None
    assert all(r['checks'][0]['original_text_matches_user_span'] for r in records[:-1])
