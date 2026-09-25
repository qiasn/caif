"""Google ADK invocation adapter for the unchanged checkout-local CAIF capability."""

import importlib.util
from pathlib import Path
import sys
from types import ModuleType

from google.adk.tools import FunctionTool


def _load_capability() -> ModuleType:
    """Isolate checkout loading until CAIF provides an installable Python package."""
    name = '_caif_p0_bible_reference_normalization'
    source = (Path(__file__).resolve().parents[2] / 'capabilities'
              / 'bible-reference-normalization' / 'bible_reference_normalization.py')
    if name in sys.modules:
        module = sys.modules[name]
        if Path(module.__file__).resolve() != source:
            raise ImportError('CAIF capability module identity collision')
        return module
    spec = importlib.util.spec_from_file_location(name, source)
    if spec is None or spec.loader is None:
        raise ImportError('Cannot load the CAIF Bible reference capability')
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    return module


_capability = _load_capability()


def normalize_bible_reference(
    raw_reference: str,
    language: str | None = None,
    canon_profile: str | None = None,
) -> dict:
    """Invoke CAIF Bible reference normalization without changing the supplied text.

    Args:
        raw_reference: Exact reference text supplied by the caller; do not rewrite it.
        language: Optional language hint passed unchanged to the capability.
        canon_profile: Optional profile identifier; omission uses the capability default.

    Returns:
        The unchanged canonical BiblePassageReference on success, or an adapter-local
        error for an expected reference failure. Request clarification for ambiguity;
        never guess a replacement reference. Operational failures propagate.
    """
    try:
        return _capability.normalize_reference(
            raw_reference, language=language, canon_profile=canon_profile
        )
    except _capability.AmbiguousReference:
        return {'error': {'type': 'AmbiguousReference',
                          'message': 'The reference is ambiguous. Ask the caller to clarify.'}}
    except _capability.UnsupportedSyntax:
        return {'error': {'type': 'UnsupportedSyntax',
                          'message': 'The reference syntax is unsupported. Ask the caller for a supported reference.'}}
    except _capability.InvalidReference:
        return {'error': {'type': 'InvalidReference',
                          'message': 'The reference or supplied options are invalid. Ask the caller to check them.'}}


bible_reference_tool = FunctionTool(func=normalize_bible_reference)
