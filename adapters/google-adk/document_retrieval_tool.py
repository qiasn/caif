"""Additive ADK binding for the generic document-retrieval capability."""
import importlib.util
from pathlib import Path
import sys

from google.adk.tools import FunctionTool


def _load_capability():
    name = '_caif_document_retrieval'
    source = Path(__file__).resolve().parents[2] / 'capabilities/document-retrieval/document_retrieval.py'
    if name in sys.modules:
        module = sys.modules[name]
        if Path(module.__file__).resolve() != source:
            raise ImportError('Unexpected document retrieval module')
        return module
    spec = importlib.util.spec_from_file_location(name, source)
    if spec is None or spec.loader is None:
        raise ImportError('Cannot load document retrieval capability')
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    return module


PdfCorpus = _load_capability().PdfCorpus


def create_document_retrieval_tool(corpus):
    """Bind a host-selected corpus; models cannot supply paths or policy labels."""
    def retrieve_document_evidence(query: str, top_k: int = 5) -> dict:
        """Find source pages matching query terms in the configured corpus.

        Args:
            query: Search terms; matches are candidates, not proof of an answer.
            top_k: Maximum number of source pages to return.

        Returns:
            Evidence objects unchanged in an ADK transport dictionary. Empty evidence
            means no matches; never substitute model knowledge for source evidence.
        """
        try:
            return {'evidence': corpus.retrieve(query, top_k=top_k)}
        except ValueError:
            return {'error': {'type': 'InvalidQuery', 'message': 'Supply search terms and a result limit from 1 to 20.'}}
    return FunctionTool(func=retrieve_document_evidence)
