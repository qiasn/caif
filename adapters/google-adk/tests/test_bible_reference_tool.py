"""Exercise the installed ADK boundary without agents, models, or credentials."""

import asyncio
import importlib.util
import json
from pathlib import Path
import socket
import sys

from google.adk.tools import FunctionTool
from jsonschema import Draft202012Validator
import pytest

import bible_reference_normalization as direct
import bible_reference_tool as adapter


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError('Adapter tests must not use the network')
    monkeypatch.setattr(socket.socket, 'connect', forbidden)
    monkeypatch.setattr(socket, 'create_connection', forbidden)
    monkeypatch.setattr(socket, 'getaddrinfo', forbidden)
    for name in ('GOOGLE_API_KEY', 'GEMINI_API_KEY', 'GOOGLE_APPLICATION_CREDENTIALS'):
        monkeypatch.delenv(name, raising=False)


def invoke(args):
    # This synchronous tool neither requests nor uses ToolContext. No Agent or
    # Runner is constructed; run_async is the real ADK implementation.
    return asyncio.run(adapter.bible_reference_tool.run_async(args=args, tool_context=None))


def test_actual_tool_and_generated_declaration():
    assert isinstance(adapter.bible_reference_tool, FunctionTool)
    declaration = adapter.bible_reference_tool._get_declaration()
    assert declaration.name == 'normalize_bible_reference'
    assert 'unchanged canonical BiblePassageReference' in declaration.description
    schema = declaration.parameters_json_schema
    assert schema['required'] == ['raw_reference']
    assert set(schema['properties']) == {'raw_reference', 'language', 'canon_profile'}
    assert schema['properties']['raw_reference']['type'] == 'string'
    for field in ('language', 'canon_profile'):
        assert schema['properties'][field]['default'] is None
        assert {p['type'] for p in schema['properties'][field]['anyOf']} == {'string', 'null'}
    validator = Draft202012Validator(schema)
    validator.validate({'raw_reference': '約三16'})
    validator.validate({'raw_reference': '約三16', 'language': None, 'canon_profile': None})
    assert not validator.is_valid({})
    assert not validator.is_valid({'raw_reference': 123})


@pytest.mark.parametrize('options', [{}, {'language': None, 'canon_profile': None},
    {'language': 'zh', 'canon_profile': 'protestant-66-paratext-english'}])
def test_forwarding_and_unchanged_object(monkeypatch, options):
    supplied = ' \t約三16\n'
    calls = []
    expected = direct.normalize_reference(supplied, **options)
    def capture(raw_reference, *, language=None, canon_profile=None):
        calls.append((raw_reference, language, canon_profile))
        return expected
    monkeypatch.setattr(adapter._capability, 'normalize_reference', capture)
    assert invoke({'raw_reference': supplied, **options}) is expected
    assert calls == [(supplied, options.get('language'), options.get('canon_profile'))]


@pytest.mark.parametrize('raw', ['約三16', '约三16', 'John 3', 'John 3:16-4:3',
    'Jude 5', '創世紀1-3章', ' \t約三16\r\n'])
def test_success_matches_independent_direct_call(raw):
    result = invoke({'raw_reference': raw})
    assert result == direct.normalize_reference(raw)
    assert result['original_text'] == raw
    schema = json.loads(direct._SCHEMA.read_text())
    Draft202012Validator(schema).validate(result)


@pytest.mark.parametrize('exception_name', ['AmbiguousReference', 'UnsupportedSyntax', 'InvalidReference'])
def test_expected_exception_translation_sanitizes_details(monkeypatch, exception_name):
    def fail(*args, **kwargs):
        raise getattr(adapter._capability, exception_name)('secret /internal/path traceback details')
    monkeypatch.setattr(adapter._capability, 'normalize_reference', fail)
    result = invoke({'raw_reference': 'input'})
    assert set(result) == {'error'}
    assert result['error']['type'] == exception_name
    assert result['error']['message']
    assert 'secret' not in str(result) and '/internal/path' not in str(result)
    if exception_name == 'AmbiguousReference':
        assert 'clarify' in result['error']['message']


@pytest.mark.parametrize('raw,kind', [('John 22', 'InvalidReference'),
    ('John 3:16,18', 'UnsupportedSyntax'), ('約翰3:16', 'UnsupportedSyntax')])
def test_real_reference_failures(raw, kind):
    result = invoke({'raw_reference': raw})
    assert result['error']['type'] == kind
    assert 'schema_version' not in result


@pytest.mark.parametrize('error', [adapter._capability.ResourceConfigurationError('broken resource'),
    RuntimeError('programming failure'), TypeError('internal defect')])
def test_operational_and_unexpected_failures_propagate(monkeypatch, error):
    def fail(*args, **kwargs):
        raise error
    monkeypatch.setattr(adapter._capability, 'normalize_reference', fail)
    with pytest.raises(type(error)) as caught:
        invoke({'raw_reference': 'John 3'})
    assert caught.value is error


def test_real_missing_resource_propagates(monkeypatch, tmp_path):
    monkeypatch.setattr(adapter._capability, '_RESOURCE_DIR', tmp_path)
    with pytest.raises(adapter._capability.ResourceConfigurationError):
        invoke({'raw_reference': 'John 3'})


def test_missing_required_argument_is_adk_error(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail('ADK must not call the capability without raw_reference')
    monkeypatch.setattr(adapter._capability, 'normalize_reference', forbidden)
    result = invoke({})
    assert isinstance(result['error'], str)
    assert 'raw_reference' in result['error']


def test_adk_filters_undeclared_arguments():
    assert invoke({'raw_reference': 'John 3', 'surrounding_text': 'ignored by ADK'}) == direct.normalize_reference('John 3')


def test_loader_and_invocation_from_unrelated_directory(monkeypatch, tmp_path):
    source = Path(adapter.__file__).resolve()
    expected = direct.normalize_reference('約三16')
    monkeypatch.chdir(tmp_path)
    # Force a fresh capability load to verify that import-time resolution itself
    # is independent of cwd, not only calls after an earlier successful import.
    monkeypatch.delitem(sys.modules, adapter._capability.__name__)
    spec = importlib.util.spec_from_file_location('_adapter_cwd_test', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert Path(module._capability.__file__).resolve() == Path(direct.__file__).resolve()
    assert module._load_capability() is module._capability
    result = asyncio.run(module.bible_reference_tool.run_async(args={'raw_reference': '約三16'}, tool_context=None))
    assert result == expected
