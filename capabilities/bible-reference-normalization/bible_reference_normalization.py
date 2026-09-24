"""Offline P0 normalizer; resources and contract are loaded from this checkout."""

import json
from pathlib import Path
import re
import unicodedata

from jsonschema import Draft202012Validator, SchemaError, ValidationError


class NormalizationError(Exception):
    """Implementation-local failure; not a CAIF result contract."""


class AmbiguousReference(NormalizationError):
    """More than one supported interpretation remains."""


class UnsupportedSyntax(NormalizationError):
    """Input is outside the implemented reference grammar."""


class InvalidReference(NormalizationError):
    """Unknown book/profile or nonexistent/reversed coordinates."""


class ResourceConfigurationError(NormalizationError):
    """Resources, runtime Unicode version, or output contract are inconsistent."""


_ROOT = Path(__file__).resolve().parent
_RESOURCE_DIR = _ROOT / 'resources'
_SCHEMA = _ROOT.parents[1] / 'shared/contracts/BiblePassageReference.schema.json'
_ASCII_LOWER = str.maketrans('ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'Duplicate JSON key: {key}')
        result[key] = value
    return result


def _read(path):
    return json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=_unique_object)


def _token(text, language):
    text = re.sub(r'[\x09-\x0d ]+', ' ', unicodedata.normalize('NFC', text)).strip(' ')
    return text.translate(_ASCII_LOWER) if language == 'en' else text


def _load():
    """Fail closed on missing data or incompatible resource bindings."""
    try:
        profiles = _read(_RESOURCE_DIR / 'canon-profiles.json')
        if profiles['schema_version'] != '1.0':
            raise ValueError('Unsupported profile resource schema')
        data = {}
        for key, filename in [('books', 'books.json'), ('aliases', 'book-aliases.json'),
                              ('structure', 'bible-structure.json')]:
            binding = profiles['resources'][key]
            if binding['file'] != filename:
                raise ValueError(f'Unexpected resource path: {key}')
            data[key] = _read(_RESOURCE_DIR / filename)
            for version in ('schema_version', 'data_version'):
                if data[key][version] != binding[version] or binding[version] != profiles[version]:
                    raise ValueError(f'Resource version mismatch: {key}')
        if data['aliases']['matching_normalization']['unicode_normalization_version'] != unicodedata.unidata_version:
            raise ValueError('Runtime Unicode version differs from alias resource')
        registry = data['books']['books']
        if not isinstance(registry, dict) or not registry or any(not k for k in registry):
            raise ValueError('Invalid book registry')
        if profiles['default_profile'] not in profiles['profiles']:
            raise ValueError('Missing default profile')
        for profile_id, profile in profiles['profiles'].items():
            members = profile['book_ids']
            structure = data['structure']['profiles'][profile_id]
            if (len(members) != len(set(members)) or not members
                    or not set(members) <= registry.keys()
                    or set(structure['books']) != set(members)
                    or structure['encoding'] != 'contiguous-verse-counts'):
                raise ValueError('Profile membership/structure mismatch')
            for book in members:
                counts = structure['books'][book]['verse_counts']
                if not isinstance(counts, list) or not counts or any(type(n) is not int or n < 1 for n in counts):
                    raise ValueError(f'Invalid verse counts: {book}')
        for alias in data['aliases']['aliases']:
            if (alias['language'] not in ('en', 'zh-Hant', 'zh-Hans')
                    or not isinstance(alias['text'], str) or not alias['text']
                    or not isinstance(alias['book_ids'], list) or not alias['book_ids']
                    or not set(alias['book_ids']) <= registry.keys()):
                raise ValueError('Invalid alias record')
        schema = _read(_SCHEMA)
        Draft202012Validator.check_schema(schema)
        return profiles, data, Draft202012Validator(schema)
    except (OSError, ValueError, KeyError, TypeError, AttributeError, SchemaError) as exc:
        raise ResourceConfigurationError(str(exc)) from exc


# Numeral grammar, not Bible data. Only conventional Chinese numbers 1..199.
_DIGITS = '一二三四五六七八九'


def _chinese_number(n):
    if n < 10:
        return _DIGITS[n - 1]
    if n < 100:
        tens, units = divmod(n, 10)
        return ('' if tens == 1 else _DIGITS[tens - 1]) + '十' + (_DIGITS[units - 1] if units else '')
    rest = n - 100
    if rest == 0:
        return '一百'
    if rest < 10:
        return '一百零' + _DIGITS[rest - 1]
    return '一百' + ('一' if rest < 20 else '') + _chinese_number(rest)


def _coordinates(text, chinese, single_chapter):
    text = text.strip(' \t\r\n\v\f')
    explicit_chapter = False
    if chinese:
        # Mixed Chinese chapter + Arabic verse is the approved 約三16 grammar.
        match = re.fullmatch(r'([一二三四五六七八九十百零]+)([0-9]+)', text)
        if match:
            text = match[1] + ':' + match[2]
        if re.search(r'[一二三四五六七八九十百零][0-9]|[0-9][一二三四五六七八九十百零]', text):
            raise UnsupportedSyntax('Unsupported mixed numeral')
        numerals = {_chinese_number(n): str(n) for n in range(1, 200)}
        def replace(match):
            try:
                return numerals[match[0]]
            except KeyError:
                raise UnsupportedSyntax('Unsupported Chinese numeral') from None
        text = re.sub(r'[一二三四五六七八九十百零]+', replace, text)
        if re.fullmatch(r'[0-9]+(?:-[0-9]+)?章', text):
            explicit_chapter = True
            text = text[:-1]
        else:
            text = re.sub(r'^([0-9]+)章([0-9]+(?:-[0-9]+)?)[節节]$', r'\1:\2', text)
    else:
        match = re.fullmatch(r'chapter ([0-9]+)(?: verses? ([0-9]+(?:-[0-9]+)?))?', text.translate(_ASCII_LOWER))
        if match:
            explicit_chapter = True
            text = match[1] + (':' + match[2] if match[2] else '')
    match = re.fullmatch(r'([0-9]+)(?::([0-9]+))?(?:-([0-9]+)(?::([0-9]+))?)?', text)
    if not match:
        raise UnsupportedSyntax('Expected one supported contiguous passage')
    try:
        a, b, c, d = (int(n) if n is not None else None for n in match.groups())
    except ValueError:
        raise UnsupportedSyntax('Coordinate numeral is too long') from None
    if b is None:
        if d is not None:
            raise UnsupportedSyntax('Mixed chapter and verse endpoints')
        if single_chapter and not explicit_chapter:
            if c is not None:
                raise UnsupportedSyntax('Use explicit chapter:verse endpoints for single-chapter verse ranges')
            return 1, a, 1, a
        return a, None, c if c is not None else a, None
    return a, b, (c if d is not None else a), (d if d is not None else c if c is not None else b)


def normalize_reference(raw_reference, *, language=None, canon_profile=None):
    """Return a schema-validated dict, or raise a NormalizationError subclass.

    No surrounding-text inference is performed. Unknown language hints search
    all alias languages. Resources are read afresh; failures never return a
    partially normalized object.
    """
    if not isinstance(raw_reference, str) or not raw_reference.strip():
        raise InvalidReference('raw_reference must be a nonempty string')
    if language is not None and not isinstance(language, str):
        raise InvalidReference('language must be a string or None')
    profiles, data, validator = _load()
    profile_id = profiles['default_profile'] if canon_profile is None else canon_profile
    if not isinstance(profile_id, str) or profile_id not in profiles['profiles']:
        raise InvalidReference('Unsupported canon_profile')
    profile = profiles['profiles'][profile_id]
    languages = ([language] if language in profile['input_languages'] else
                 ['zh-Hant', 'zh-Hans'] if language == 'zh' else profile['input_languages'])
    aliases = {}
    for alias in data['aliases']['aliases']:
        tag = alias['language']
        if tag in languages:
            aliases.setdefault((tag, _token(alias['text'], tag)), set()).update(alias['book_ids'])
    structure = data['structure']['profiles'][profile_id]['books']
    interpretations = set()
    recognized = False
    # Enumerate complete token/grammar splits; never choose by alias entry order.
    for split in range(1, len(raw_reference) + 1):
        matches = {
            tag: aliases.get((tag, _token(raw_reference[:split], tag)), set())
            for tag in languages
        }
        candidates = set().union(*matches.values())
        if not candidates:
            continue
        recognized = True
        parsed = set()
        for tag, books in matches.items():
            for book in books:
                if book not in structure:
                    continue
                try:
                    coords = _coordinates(raw_reference[split:], tag != 'en', len(structure[book]['verse_counts']) == 1)
                except UnsupportedSyntax:
                    continue
                parsed.add((book, *coords))
        # Neither domain validity nor language entry order may choose a book.
        if parsed and len(candidates) > 1:
            raise AmbiguousReference(f'Book candidates: {sorted(candidates)}')
        interpretations.update(parsed)
    if not interpretations:
        if recognized:
            raise UnsupportedSyntax('Recognized book but unsupported or deferred reference syntax')
        raise InvalidReference('No accepted book alias in the selected language')
    if len(interpretations) != 1:
        raise AmbiguousReference('Multiple supported reference interpretations')
    book, cs, vs, ce, ve = interpretations.pop()
    counts = structure[book]['verse_counts']
    if vs == 0 or ve == 0:
        raise UnsupportedSyntax('Verse zero is outside P0')
    if not (1 <= cs <= ce <= len(counts)):
        raise InvalidReference('Nonexistent or reversed chapter range')
    if vs is not None and (not (1 <= vs <= counts[cs - 1] and 1 <= ve <= counts[ce - 1]) or (cs, vs) > (ce, ve)):
        raise InvalidReference('Nonexistent or reversed verse range')
    result = dict(schema_version='1.0', book=book, chapter_start=cs, verse_start=vs,
                  chapter_end=ce, verse_end=ve, original_text=raw_reference, canon_profile=profile_id)
    try:
        validator.validate(result)
    except ValidationError as exc:
        raise ResourceConfigurationError('Constructed output violates the shared contract') from exc
    return result
