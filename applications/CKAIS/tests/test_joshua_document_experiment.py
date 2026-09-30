"""Synthetic documents and scripted model; never load the private real corpus."""
import asyncio
import importlib.util
from pathlib import Path
import socket

import pytest
from google.adk.models import BaseLlm, LlmResponse
from google.genai import types
import joshua_document_experiment as app


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError('Offline test attempted network access')
    monkeypatch.setattr(socket.socket, 'connect', forbidden)
    monkeypatch.setattr(socket, 'getaddrinfo', forbidden)
    monkeypatch.setattr(socket, 'create_connection', forbidden)


@pytest.fixture
def corpus(tmp_path):
    source = Path(__file__).resolve().parents[3] / 'capabilities/document-retrieval/tests/pdf_fixtures.py'
    spec = importlib.util.spec_from_file_location('synthetic_pdf', source)
    fixture = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixture)
    path = fixture.make_pdf(tmp_path / 'synthetic.pdf', ['faith hope', '約書亞 synthetic'])
    return app.load_corpus([path])


class ScriptedModel(BaseLlm):
    model: str = 'scripted-offline'

    async def generate_content_async(self, llm_request, stream=False):
        responses = [p.function_response for c in llm_request.contents for p in c.parts or [] if p.function_response]
        if responses:
            # Test that even an unsupported claim is not the application's answer.
            yield LlmResponse(content=types.Content(role='model', parts=[types.Part(text='Unsupported claim attributed to Joshua.')]))
        else:
            query = next(p.text for c in llm_request.contents if c.role == 'user' for p in c.parts or [] if p.text)
            yield LlmResponse(content=types.Content(role='model', parts=[types.Part(function_call=types.FunctionCall(
                name='retrieve_document_evidence', args={'query': query}))]))


@pytest.mark.parametrize('query', ['faith', '約書亞', 'unfindableterm'])
def test_evidence_separate_from_presentation(corpus, query):
    record, = asyncio.run(app.observe_requests(ScriptedModel(), [query], corpus=corpus))
    expected = corpus.retrieve(query)
    assert record['evidence'] == expected
    assert record['tool_responses'] == [{'evidence': expected}]
    assert record['model_presentation'] == ['Unsupported claim attributed to Joshua.']
    assert record['presentation'] != record['model_presentation'][0]
    if not expected:
        assert record['presentation'] == app.NO_EVIDENCE
    else:
        assert all(e['citation']['uri'] is None for e in expected)
        assert all(e['trust_status'] == 'unverified' for e in expected)


def test_corpus_count_guard(monkeypatch, tmp_path):
    monkeypatch.setattr(app, 'CORPUS', tmp_path)
    with pytest.raises(RuntimeError):
        app.load_corpus()
