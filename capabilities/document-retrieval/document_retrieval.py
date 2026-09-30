"""Generic evidence retrieval, implemented initially with PDF pages and overlap."""
from copy import deepcopy
import hashlib
from io import BytesIO
import json
from pathlib import Path
import re
import unicodedata

from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from pypdf import PdfReader, __version__ as PYPDF_VERSION


class DocumentRetrievalError(Exception):
    """Operational/configuration error, not an empty retrieval result."""


def _validator():
    root = Path(__file__).resolve().parents[2] / 'shared/contracts'
    citation = json.loads((root / 'Citation.schema.json').read_text())
    evidence = json.loads((root / 'RetrievedEvidence.schema.json').read_text())
    registry = Registry().with_resource(citation['$id'], Resource.from_contents(citation))
    Draft202012Validator.check_schema(evidence)
    return Draft202012Validator(evidence, registry=registry)


def _search_text(text):
    return ' '.join(unicodedata.normalize('NFC', text).casefold().split())


def _extract(page):
    """Return full extracted page text and conservative visibility diagnostics."""
    reasons = set()
    if page.cropbox != page.mediabox:
        reasons.add('cropped_page')
    resources = page.get('/Resources', {})
    state = {'mode': 0, 'ca': 1, 'CA': 1, 'mask': '/None', 'clip': False, 'blend': '/Normal'}
    stack = []
    clip_rectangle = None
    rectangle_count = 0

    def visit(op, args, cm, tm):
        nonlocal state, clip_rectangle, rectangle_count
        if op == b'q':
            stack.append(state.copy())
        elif op == b'Q' and stack:
            state = stack.pop()
        elif op == b're':
            rectangle_count += 1
            x, y, width, height = map(float, args)
            a, b, c, d, e, f = cm
            if b == c == 0:
                xs = sorted((a*x+e, a*(x+width)+e))
                ys = sorted((d*y+f, d*(y+height)+f))
                clip_rectangle = (xs[0], ys[0], xs[1], ys[1])
            else:
                clip_rectangle = None
        elif op in (b'm', b'l', b'c', b'v', b'y', b'h', b'n', b'S', b'f', b'f*'):
            clip_rectangle = None
            rectangle_count = 0
        elif op in (b'W', b'W*'):
            # Exporters commonly clip to the page with sub-millipoint rounding.
            box = list(map(float, page.cropbox))
            covers_page = rectangle_count == 1 and clip_rectangle is not None and all(
                (edge <= bound + 0.001 if i < 2 else edge >= bound - 0.001)
                for i, (edge, bound) in enumerate(zip(clip_rectangle, box)))
            state['clip'] = state['clip'] or not covers_page
        elif op == b'Tr':
            state['mode'] = int(args[0])
        elif op == b'gs':
            gs = resources.get('/ExtGState', {}).get(args[0])
            if gs is not None:
                gs = gs.get_object()
                state['ca'] = gs.get('/ca', state['ca'])
                state['CA'] = gs.get('/CA', state['CA'])
                state['mask'] = gs.get('/SMask', state['mask'])
                state['blend'] = gs.get('/BM', state['blend'])
        elif op in (b'BDC', b'BMC') and args and str(args[0]) == '/OC':
            reasons.add('optional_content')
        elif op == b'Do':
            obj = resources.get('/XObject', {}).get(args[0])
            if obj is not None and obj.get_object().get('/Subtype') == '/Form':
                reasons.add('nested_form')
        elif op in (b'Tj', b'TJ', b"'", b'"'):
            if state['clip']:
                reasons.add('clipped_text')
            if state['blend'] != '/Normal':
                reasons.add('text_blend_mode')
            if state['mode'] not in (0, 1, 2):
                reasons.add('invisible_or_clipping_text')
            if state['ca'] != 1 or state['CA'] != 1 or state['mask'] != '/None':
                reasons.add('text_transparency_or_mask')

    text = page.extract_text(visitor_operand_before=visit)
    if '\ufffd' in text or any(0xD800 <= ord(c) <= 0xDFFF for c in text):
        reasons.add('unmapped_text')
    return text, sorted(reasons)


class PdfCorpus:
    """Caller-controlled in-memory PDF implementation; no application defaults."""

    def __init__(self, paths, *, provenance_status, trust_status, access_classification):
        self._pages = []
        self.diagnostics = []
        seen = set()
        try:
            self._validator = _validator()
            labels = dict(provenance_status=provenance_status, trust_status=trust_status,
                          access_classification=access_classification)
            # Validate caller labels even when every source page is empty.
            for field, value in labels.items():
                if value not in self._validator.schema['properties'][field]['enum']:
                    raise ValueError(f'Invalid {field}')
            for source in paths:
                path = Path(source)
                raw = path.read_bytes()
                digest = hashlib.sha256(raw).hexdigest()
                if digest in seen:
                    continue
                seen.add(digest)
                source_id = 'sha256:' + digest
                reader = PdfReader(BytesIO(raw), strict=True)
                if reader.is_encrypted:
                    raise ValueError('Encrypted PDFs are not supported')
                for number, page in enumerate(reader.pages, 1):
                    text, reasons = _extract(page)
                    status = 'unsupported_visibility' if reasons else 'indexed' if text.strip() else 'empty'
                    self.diagnostics.append(dict(source_id=source_id, page=number, status=status, reasons=reasons))
                    if status != 'indexed':
                        continue
                    item = dict(schema_version='1.0', evidence_id=f'{source_id}:page:{number}',
                                content=text, citation=dict(schema_version='1.0', source_id=source_id,
                                source_type='document', title=path.name, location=f'PDF page {number}', uri=None),
                                retrieval_method='p1b-pdf-term-overlap-v1',
                                extensions={'extraction': {'library': 'pypdf', 'version': PYPDF_VERSION,
                                'content_sha256': hashlib.sha256(text.encode('utf-8')).hexdigest()}}, **labels)
                    self._validator.validate(item)
                    self._pages.append((item, _search_text(text), number))
        except Exception as exc:
            raise DocumentRetrievalError('Document ingestion or configuration failed') from exc

    def retrieve(self, query, top_k=5):
        if not isinstance(query, str) or not query.strip():
            raise ValueError('Supply a nonempty text query')
        if type(top_k) is not int or not 1 <= top_k <= 20:
            raise ValueError('top_k must be an integer from 1 through 20')
        terms = set(re.findall(r'[a-z0-9]+|[\u3400-\u9fff]+', _search_text(query)))
        if not terms:
            raise ValueError('Query has no supported searchable terms')
        ranked = []
        for item, text, number in self._pages:
            counts = [len(re.findall(r'(?<![a-z0-9])' + re.escape(term) + r'(?![a-z0-9])', text))
                      if term.isascii() else text.count(term) for term in terms]
            overlap = sum(count > 0 for count in counts)
            if overlap:
                ranked.append((-overlap, -sum(counts), item['citation']['source_id'], number, item))
        results = [deepcopy(row[-1]) for row in sorted(ranked, key=lambda row: row[:-1])[:top_k]]
        for item in results:
            self._validator.validate(item)
        return results
