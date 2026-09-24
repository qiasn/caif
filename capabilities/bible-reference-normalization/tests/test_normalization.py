"""Offline behavioral and resource-integrity checks for the P0 vertical slice."""
import json
from pathlib import Path
import socket

import pytest
from jsonschema import Draft202012Validator

import bible_reference_normalization as normalizer
from bible_reference_normalization import (
    AmbiguousReference, InvalidReference, ResourceConfigurationError,
    UnsupportedSyntax, normalize_reference,
)

PROFILE = 'protestant-66-paratext-english'
RESOURCE_DIR = Path(normalizer.__file__).parent / 'resources'
SCHEMA = json.loads(normalizer._SCHEMA.read_text())


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError('Tests and normalizer must remain offline')
    monkeypatch.setattr(socket, 'socket', forbidden)
    monkeypatch.setattr(socket, 'create_connection', forbidden)


@pytest.mark.parametrize('raw,book,coordinates', [
    ('John 3', 'John', (3, None, 3, None)),
    ('John 3:16', 'John', (3, 16, 3, 16)),
    ('Jn 3:16', 'John', (3, 16, 3, 16)),
    ('John 3:16-18', 'John', (3, 16, 3, 18)),
    ('John 3:16-4:3', 'John', (3, 16, 4, 3)),
    ('Genesis 1-3', 'Genesis', (1, None, 3, None)),
    ('Jude 5', 'Jude', (1, 5, 1, 5)),
    ('Jude 1', 'Jude', (1, 1, 1, 1)),
    ('Jude chapter 1', 'Jude', (1, None, 1, None)),
    ('約三16', 'John', (3, 16, 3, 16)),
    ('约三16', 'John', (3, 16, 3, 16)),
    ('創世紀1-3章', 'Genesis', (1, None, 3, None)),
    ('创世记1-3章', 'Genesis', (1, None, 3, None)),
    ('創1-3', 'Genesis', (1, None, 3, None)),
    ('约翰福音3:16', 'John', (3, 16, 3, 16)),
    ('約翰福音三章十六節', 'John', (3, 16, 3, 16)),
    ('约翰福音三章十六节', 'John', (3, 16, 3, 16)),
    ('John chapter 3 verses 16-18', 'John', (3, 16, 3, 18)),
    ('3 John 1:15', '3 John', (1, 15, 1, 15)),
    ('約翰三書15', '3 John', (1, 15, 1, 15)),
    ('约翰三书15', '3 John', (1, 15, 1, 15)),
    ('Revelation 12:18', 'Revelation', (12, 18, 12, 18)),
    ('2 Corinthians 13:14', '2 Corinthians', (13, 14, 13, 14)),
    (' \t jN\t3:16\r\n', 'John', (3, 16, 3, 16)),
    ('1\t Corinthians 13', '1 Corinthians', (13, None, 13, None)),
    ('猶大書1章', 'Jude', (1, None, 1, None)),
    ('詩篇一百一十九章', 'Psalms', (119, None, 119, None)),
    ('約三', 'John', (3, None, 3, None)),
])
def test_success(raw, book, coordinates):
    result = normalize_reference(raw)
    cs, vs, ce, ve = coordinates
    assert result == dict(schema_version='1.0', book=book, chapter_start=cs,
                         verse_start=vs, chapter_end=ce, verse_end=ve,
                         original_text=raw, canon_profile=PROFILE)
    Draft202012Validator(SCHEMA).validate(result)


@pytest.mark.parametrize('raw', [
    'John 22', 'John 3:37', 'John 3:18-16', 'Genesis 3-1',
    'John 3:16-4:55', 'John 4:3-3:16', 'John 0', 'Jude 26',
    '3 John 1:16', 'Revelation 12:19', '2 Corinthians 13:15',
    'Unknown 3:16', '', '   ', None,
])
def test_invalid(raw):
    with pytest.raises(InvalidReference):
        normalize_reference(raw)


@pytest.mark.parametrize('raw', [
    'John 3:16,18', 'John 3; Romans 8', 'John 3:16-Romans 4:3',
    'John', 'John 3:16ff', 'John 3:16a', 'John 3:0', 'Jude 0',
    '約翰3:16', '约翰3:16', '約三1:5', '约三1:5',
    'John three sixteen eighteen', 'John 3 16 18', 'John 3-4:3',
    'John ３:１６', 'John 3:16 trailing text', 'John 3:-1',
    'Jn. 3:16', 'Jude 5-7',
])
def test_unsupported(raw):
    with pytest.raises(UnsupportedSyntax):
        normalize_reference(raw)


@pytest.mark.parametrize('language', [None, 'zh', 'zh-Hant', 'zh-Hans', 'unknown'])
def test_shared_chinese_spelling_does_not_infer_script(language):
    result = normalize_reference('民1:1', language=language)
    assert result['book'] == 'Numbers'
    assert 'language' not in result


def test_language_and_profile_selection():
    assert normalize_reference('John 3', language='unknown', canon_profile=PROFILE)['book'] == 'John'
    with pytest.raises(InvalidReference):
        normalize_reference('John 3', language='zh')
    with pytest.raises(InvalidReference):
        normalize_reference('创世记1', language='zh-Hant')
    with pytest.raises(InvalidReference):
        normalize_reference('John 3', canon_profile='other')
    with pytest.raises(InvalidReference):
        normalize_reference('John 3', language=[])


@pytest.fixture
def resources(tmp_path, monkeypatch):
    for source in RESOURCE_DIR.glob('*.json'):
        (tmp_path / source.name).write_bytes(source.read_bytes())
    monkeypatch.setattr(normalizer, '_RESOURCE_DIR', tmp_path)
    return tmp_path


def edit(resources, filename, change):
    path = resources / filename
    data = json.loads(path.read_text())
    change(data)
    path.write_text(json.dumps(data, ensure_ascii=False))


@pytest.mark.parametrize('reverse', [False, True])
def test_ambiguity_preserved_independent_of_alias_order(resources, reverse):
    def change(data):
        data['aliases'].append(dict(language='en', text='JN', book_ids=['Genesis']))
        if reverse:
            data['aliases'].reverse()
    edit(resources, 'book-aliases.json', change)
    with pytest.raises(AmbiguousReference):
        normalize_reference('Jn 3:16')
    # One book having no such chapter must not be used to choose the other.
    with pytest.raises(AmbiguousReference):
        normalize_reference('Jn 40:1')


@pytest.mark.parametrize('filename,change', [
    ('books.json', lambda d: d.update(data_version='wrong')),
    ('books.json', lambda d: d['books'].pop('John')),
    ('book-aliases.json', lambda d: d['aliases'][0].update(book_ids=['Missing'])),
    ('book-aliases.json', lambda d: d['matching_normalization'].update(unicode_normalization_version='wrong')),
    ('canon-profiles.json', lambda d: d['profiles'][PROFILE]['book_ids'].append('John')),
    ('bible-structure.json', lambda d: d['profiles'][PROFILE]['books'].pop('John')),
    ('bible-structure.json', lambda d: d['profiles'][PROFILE]['books'].update(Unknown={'verse_counts': [1]})),
    ('bible-structure.json', lambda d: d['profiles'][PROFILE]['books']['John'].update(verse_counts=[True])),
    ('bible-structure.json', lambda d: d['profiles'][PROFILE]['books']['John'].update(verse_counts=[])),
])
def test_resource_corruption(resources, filename, change):
    edit(resources, filename, change)
    with pytest.raises(ResourceConfigurationError):
        normalize_reference('John 3')


@pytest.mark.parametrize('content', [None, '{', '{"schema_version":"1.0","schema_version":"1.0"}'])
def test_missing_malformed_duplicate_json(resources, content):
    path = resources / 'books.json'
    if content is None:
        path.unlink()
    else:
        path.write_text(content)
    with pytest.raises(ResourceConfigurationError):
        normalize_reference('John 3')


def test_contract_validation_is_not_skipped(tmp_path, monkeypatch):
    schema = dict(SCHEMA, required=SCHEMA['required'] + ['impossible'])
    path = tmp_path / 'schema.json'
    path.write_text(json.dumps(schema))
    monkeypatch.setattr(normalizer, '_SCHEMA', path)
    with pytest.raises(ResourceConfigurationError):
        normalize_reference('John 3:16')


def test_resource_integrity_and_all_chapter_boundaries():
    profiles, data, validator = normalizer._load()
    members = profiles['profiles'][PROFILE]['book_ids']
    books = data['structure']['profiles'][PROFILE]['books']
    assert len(members) == len(set(members)) == 66
    assert set(members) == set(books) == set(data['books']['books'])
    assert sum(len(b['verse_counts']) for b in books.values()) == 1189
    assert sum(sum(b['verse_counts']) for b in books.values()) == 31104
    aliases = {}
    for alias in data['aliases']['aliases']:
        key = normalizer._token(alias['text'], alias['language'])
        aliases.setdefault(key, set()).update(alias['book_ids'])
    assert all(len(candidates) == 1 for candidates in aliases.values())
    # Every canonical book and every chapter's first/last address, plus overflow.
    # Reuse checked data to avoid thousands of redundant disk/schema loads.
    original_load = normalizer._load
    try:
        normalizer._load = lambda: (profiles, data, validator)
        for book, entry in books.items():
            for chapter, maximum in enumerate(entry['verse_counts'], 1):
                for verse in {1, maximum}:
                    result = normalize_reference(f'{book} {chapter}:{verse}')
                    assert result['book'] == book
                    assert result['verse_start'] == result['verse_end'] == verse
                    validator.validate(result)
                with pytest.raises(InvalidReference):
                    normalize_reference(f'{book} {chapter}:{maximum + 1}')
            with pytest.raises(InvalidReference):
                normalize_reference(f'{book} {len(entry["verse_counts"]) + 1}:1')
    finally:
        normalizer._load = original_load


def test_cross_language_collision(resources):
    def change(data):
        data['aliases'].append(dict(language='zh-Hant', text='Jn', book_ids=['Jude']))
    edit(resources, 'book-aliases.json', change)
    with pytest.raises(AmbiguousReference):
        normalize_reference('Jn 1-3')
    assert normalize_reference('Jn 1-3', language='en')['book'] == 'John'


@pytest.mark.parametrize('raw', ['約三1:5', '约三1:5', '約1三:5', '約一2:3'])
def test_mixed_numerals_are_not_concatenated(raw):
    with pytest.raises(UnsupportedSyntax):
        normalize_reference(raw)


def test_all_resource_aliases():
    data = json.loads((RESOURCE_DIR / 'book-aliases.json').read_text())
    for alias in data['aliases']:
        result = normalize_reference(alias['text'] + ' 1:1', language=alias['language'])
        assert result['book'] in alias['book_ids']
        Draft202012Validator(SCHEMA).validate(result)


@pytest.mark.parametrize('book', ['Obadiah', 'Philemon', '2 John', '3 John', 'Jude'])
def test_single_chapter_rule_is_general(book):
    verse = normalize_reference(f'{book} 5')
    assert (verse['chapter_start'], verse['verse_start'], verse['chapter_end'], verse['verse_end']) == (1, 5, 1, 5)
    chapter = normalize_reference(f'{book} chapter 1')
    assert chapter['chapter_start'] == chapter['chapter_end'] == 1
    assert chapter['verse_start'] is chapter['verse_end'] is None
