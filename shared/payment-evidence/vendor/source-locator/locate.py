#!/usr/bin/env python3
"""Locate structural JSON violations in the exact document and contract bytes."""
import argparse
from bisect import bisect_right
import hashlib
import json
import math
from pathlib import Path
import sys
import types

def bounded_module():
    # Bootstrap only the fixed, trusted sibling; user inputs use its no-follow reader.
    source = Path(__file__).absolute().parent.parent / 'bounded-contract' / 'check.py'
    relative = source.relative_to(Path.cwd()).as_posix()
    if any(not p or p.startswith('.') for p in relative.split('/')):
        raise ValueError('run inside the workspace containing the sibling tools')
    # Open each component without following links, including the trusted bootstrap.
    import os
    import stat
    directory = os.open('.', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    leaf = None
    try:
        parts = relative.split('/')
        for part in parts[:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                            dir_fd=directory)
            os.close(directory)
            directory = child
        leaf = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                       dir_fd=directory)
        if not stat.S_ISREG(os.fstat(leaf).st_mode):
            raise ValueError('trusted sibling must be a regular file')
        chunks, remaining = [], 1_000_001
        while remaining:
            chunk = os.read(leaf, min(65536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        code = b''.join(chunks)
        if len(code) > 1_000_000:
            raise ValueError('trusted sibling exceeds byte limit')
    finally:
        if leaf is not None:
            os.close(leaf)
        os.close(directory)
    module = types.ModuleType('repair_bounded_contract')
    module.__file__ = str(source)
    exec(compile(code, str(source), 'exec'), module.__dict__)
    return module



def dependencies():
    bounded = bounded_module()
    source = Path(__file__).absolute().parent.parent / 'rule-locator' / 'explain.py'
    relative = source.relative_to(Path.cwd()).as_posix()
    locator = types.ModuleType('source_rule_locator')
    locator.__file__ = str(source)
    exec(compile(bounded.read_bytes(relative), str(source), 'exec'), locator.__dict__)
    return bounded, bounded.engine_module(), locator


def strict_json(text):
    def pairs(entries):
        result = {}
        for key, value in entries:
            if key in result:
                raise ValueError('duplicate JSON property: ' + key)
            result[key] = value
        return result

    def finite(token):
        value = float(token)
        if not math.isfinite(value):
            raise ValueError('JSON number must be finite')
        return value

    def reject(token):
        raise ValueError('invalid JSON constant: ' + token)

    return json.loads(text, object_pairs_hook=pairs,
                      parse_float=finite, parse_constant=reject)


def pointer(parent, key):
    return parent + '/' + str(key).replace('~', '~0').replace('/', '~1')


class Source:
    """Index exact token ranges after strict JSON parsing, without rewriting input.

    Offsets are zero-based and end-exclusive. Lines and Unicode code-point
    columns are one-based. LF starts a line; CRLF is preserved in the bytes.
    """
    def __init__(self, data, name):
        if not isinstance(data, bytes) or len(data) > 1_000_000:
            raise ValueError('source must be at most 1,000,000 bytes')
        self.name = name
        self.data = data
        self.text = data.decode('utf-8')
        self.value = strict_json(self.text)
        self.values = {}
        self.keys = {}
        self.pos = 0
        self.decoder = json.JSONDecoder()
        self._walk(self.value, '')
        self._space()
        if self.pos != len(self.text):
            raise ValueError('source index did not consume the complete document')
        self.lines = [0] + [i + 1 for i, ch in enumerate(self.text) if ch == '\n']
        # Calculate only token endpoints in one forward pass. Do not repeatedly
        # encode every prefix (quadratic on large, flat JSON documents).
        endpoints = {p for pair in list(self.values.values()) + list(self.keys.values())
                     for p in pair}
        self.byte_offsets = {}
        previous = total = 0
        for offset in sorted(endpoints):
            total += len(self.text[previous:offset].encode('utf-8'))
            self.byte_offsets[offset] = total
            previous = offset

    def _space(self):
        while self.pos < len(self.text) and self.text[self.pos] in ' \t\r\n':
            self.pos += 1

    def _take(self, expected):
        self._space()
        if self.text[self.pos:self.pos + 1] != expected:
            raise ValueError('source index delimiter mismatch')
        self.pos += 1

    def _walk(self, value, path):
        self._space()
        start = self.pos
        if isinstance(value, dict):
            self._take('{')
            for index, (key, child) in enumerate(value.items()):
                if index:
                    self._take(',')
                self._space()
                key_start = self.pos
                actual, self.pos = self.decoder.raw_decode(self.text, self.pos)
                if actual != key:
                    raise ValueError('source index property mismatch')
                child_path = pointer(path, key)
                self.keys[child_path] = (key_start, self.pos)
                self._take(':')
                self._walk(child, child_path)
            self._take('}')
        elif isinstance(value, list):
            self._take('[')
            for index, child in enumerate(value):
                if index:
                    self._take(',')
                self._walk(child, pointer(path, index))
            self._take(']')
        else:
            _, self.pos = self.decoder.raw_decode(self.text, self.pos)
        self.values[path] = (start, self.pos)

    def position(self, offset):
        line = bisect_right(self.lines, offset)
        return {'line': line, 'column': offset - self.lines[line - 1] + 1,
                'char_offset': offset, 'byte_offset': self.byte_offsets[offset]}

    def span(self, pair):
        return {'start': self.position(pair[0]), 'end': self.position(pair[1])}

    def location(self, path):
        if path in self.values:
            result = {'file': self.name, 'present': True,
                      'value': self.span(self.values[path])}
            if path in self.keys:
                result['key'] = self.span(self.keys[path])
            return result
        # Required fields have no token. Anchor their parent object explicitly;
        # never pretend the parent is the missing value's own source range.
        if not path or '/' not in path:
            raise ValueError('missing source pointer has no parent')
        parent = path.rsplit('/', 1)[0]
        if parent not in self.values:
            raise ValueError('missing source pointer has no indexed parent')
        return {'file': self.name, 'present': False,
                'anchor': {'path': parent, 'value': self.span(self.values[parent])}}

    def identity(self):
        return {'file': self.name, 'bytes': len(self.data),
                'sha256': hashlib.sha256(self.data).hexdigest()}


def locate(engine, locator, contract_source, document_source):
    # Validity, diagnostic order and rule pointers remain the ancestor's job.
    result = locator.explain(engine, contract_source.value, document_source.value)
    for error in result['errors']:
        error['document_source'] = document_source.location(error['path'])
        error['contract_source'] = contract_source.location(error['contract_path'])
        if not error['contract_source']['present']:
            raise ValueError('rule pointer has no source token')
    result['sources'] = {'contract': contract_source.identity(),
                         'document': document_source.identity()}
    result['coordinates'] = {
        'lines': 'one-based; LF begins each new line',
        'columns': 'one-based Unicode code points, not display cells or UTF-16 units',
        'offsets': 'zero-based; ranges include start and exclude end',
        'encoding': 'UTF-8; source bytes and CRLF are preserved'}
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('contract', help='trusted contract, relative workspace file')
    parser.add_argument('document', help='JSON input, relative workspace file')
    args = parser.parse_args(argv)
    try:
        bounded, engine, locator = dependencies()
        # Read each file exactly once; hashes, parsing and locations refer to the
        # same captured bytes even if the path is later replaced.
        contract = Source(bounded.read_bytes(args.contract), args.contract)
        document = Source(bounded.read_bytes(args.document), args.document)
        result = locate(engine, locator, contract, document)
        print(json.dumps(result, indent=2, ensure_ascii=True, allow_nan=False))
        return 0 if result['valid'] else 1
    except (ValueError, OSError, RecursionError, KeyError, IndexError) as exc:
        print(json.dumps({'valid': False, 'error': str(exc)}, ensure_ascii=True))
        return 2


if __name__ == '__main__':
    sys.exit(main())
