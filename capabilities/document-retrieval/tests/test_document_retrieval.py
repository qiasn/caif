import hashlib

import pytest
from pypdf import PdfReader

from document_retrieval import PdfCorpus, DocumentRetrievalError
from pdf_fixtures import make_pdf

LABELS = dict(provenance_status='known_source', trust_status='unverified', access_classification='internal')


def test_pages_contract_and_original_content(tmp_path):
    path = make_pdf(tmp_path / 'synthetic.pdf', ['faith hope', '', '約書亞 faith'])
    corpus = PdfCorpus([path], **LABELS)
    assert [d['status'] for d in corpus.diagnostics] == ['indexed', 'empty', 'indexed']
    results = corpus.retrieve('faith')
    assert len(results) == 2
    reader = PdfReader(path)
    for item, number in zip(results, [1, 3]):
        corpus._validator.validate(item)
        assert item['content'] == reader.pages[number-1].extract_text()
        assert item['citation']['location'] == f'PDF page {number}'
        assert item['citation']['uri'] is None
        assert item['citation']['source_id'] == 'sha256:' + hashlib.sha256(path.read_bytes()).hexdigest()
        assert all(item[k] == v for k, v in LABELS.items())
    assert corpus.retrieve('約書亞')[0]['citation']['location'] == 'PDF page 3'
    assert corpus.retrieve('unfindableterm') == []
    results[0]['content'] = 'changed'
    assert corpus.retrieve('faith')[0]['content'] != 'changed'


def test_overlap_order_and_deduplication(tmp_path):
    path = make_pdf(tmp_path / 'sample.pdf', ['hope', 'faith hope', 'faith faith'])
    corpus = PdfCorpus([path, path], **LABELS)
    assert len(corpus.diagnostics) == 3
    assert [e['citation']['location'] for e in corpus.retrieve('FAITH hope absent', 2)] == ['PDF page 2', 'PDF page 3']


@pytest.mark.parametrize('query,limit', [('', 5), ('!!!', 5), (None, 5), ('hope', 0), ('hope', True), ('hope', 21)])
def test_invalid_query(tmp_path, query, limit):
    corpus = PdfCorpus([make_pdf(tmp_path / 'sample.pdf', ['hope'])], **LABELS)
    with pytest.raises(ValueError):
        corpus.retrieve(query, limit)


def test_invisible_text_not_evidence(tmp_path):
    corpus = PdfCorpus([make_pdf(tmp_path / 'hidden.pdf', ['secret'], invisible=True)], **LABELS)
    assert corpus.retrieve('secret') == []
    assert corpus.diagnostics[0]['status'] == 'unsupported_visibility'


def test_bad_file_operational_error(tmp_path):
    with pytest.raises(DocumentRetrievalError):
        PdfCorpus([tmp_path / 'missing.pdf'], **LABELS)


def test_invalid_labels_even_empty_corpus():
    with pytest.raises(DocumentRetrievalError):
        PdfCorpus([], **dict(LABELS, trust_status='invented'))


def test_cropped_page_excluded(tmp_path):
    from pypdf import PdfWriter
    path = make_pdf(tmp_path / 'crop.pdf', ['outside'])
    writer = PdfWriter(clone_from=path)
    writer.pages[0].cropbox.upper_right = (100, 100)
    writer.write(path)
    corpus = PdfCorpus([path], **LABELS)
    assert corpus.retrieve('outside') == []
    assert 'cropped_page' in corpus.diagnostics[0]['reasons']


def test_corrupt_and_encrypted_sources(tmp_path):
    from pypdf import PdfWriter
    bad = tmp_path / 'bad.pdf'
    bad.write_bytes(b'not a pdf')
    with pytest.raises(DocumentRetrievalError):
        PdfCorpus([bad], **LABELS)
    encrypted = make_pdf(tmp_path / 'encrypted.pdf', ['faith'])
    writer = PdfWriter(clone_from=encrypted)
    writer.encrypt('synthetic-password')
    writer.write(encrypted)
    with pytest.raises(DocumentRetrievalError):
        PdfCorpus([encrypted], **LABELS)


def test_source_change_changes_identity(tmp_path):
    path = make_pdf(tmp_path / 'source.pdf', ['faith'])
    first = PdfCorpus([path], **LABELS).retrieve('faith')[0]
    make_pdf(path, ['faith changed'])
    second = PdfCorpus([path], **LABELS).retrieve('faith')[0]
    assert first['evidence_id'] != second['evidence_id']


@pytest.mark.parametrize('prefix,expected', [('0 0 612 792 re W n ', True), ('0 0 10 10 re W n ', False)])
def test_clipping_qualification(tmp_path, prefix, expected):
    corpus = PdfCorpus([make_pdf(tmp_path / 'clip.pdf', ['faith'], prefix=prefix)], **LABELS)
    assert bool(corpus.retrieve('faith')) == expected


def test_english_term_boundaries(tmp_path):
    corpus = PdfCorpus([make_pdf(tmp_path / 'terms.pdf', ['faith', 'AI'])], **LABELS)
    assert [e['citation']['location'] for e in corpus.retrieve('AI')] == ['PDF page 2']
