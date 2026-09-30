import asyncio
import importlib.util
from pathlib import Path

from google.adk.tools import FunctionTool
from document_retrieval_tool import PdfCorpus, create_document_retrieval_tool


def test_actual_document_tool(tmp_path):
    source = Path(__file__).resolve().parents[3] / 'capabilities/document-retrieval/tests/pdf_fixtures.py'
    spec = importlib.util.spec_from_file_location('synthetic_pdf', source)
    fixture = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixture)
    path = fixture.make_pdf(tmp_path / 'test.pdf', ['faith hope'])
    corpus = PdfCorpus([path], provenance_status='known_source', trust_status='unverified', access_classification='internal')
    tool = create_document_retrieval_tool(corpus)
    assert isinstance(tool, FunctionTool)
    schema = tool._get_declaration().parameters_json_schema
    assert schema['required'] == ['query']
    assert set(schema['properties']) == {'query', 'top_k'}
    async def invoke(args):
        return await tool.run_async(args=args, tool_context=None)
    assert asyncio.run(invoke({'query': 'faith'})) == {'evidence': corpus.retrieve('faith')}
    assert asyncio.run(invoke({'query': 'unfindableterm'})) == {'evidence': []}
    assert 'error' in asyncio.run(invoke({'query': ''}))


def test_operational_errors_propagate():
    import pytest
    class BrokenCorpus:
        def retrieve(self, *args, **kwargs):
            raise RuntimeError('operational failure')
    tool = create_document_retrieval_tool(BrokenCorpus())
    with pytest.raises(RuntimeError):
        asyncio.run(tool.run_async(args={'query': 'faith'}, tool_context=None))
