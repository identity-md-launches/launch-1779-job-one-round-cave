"""Offline source-location regressions; ephemeral files stay in test/scratch/."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import tempfile
import types
import unittest

SCRIPT = Path('line-2/tools/source-locator/locate.py')
source = types.ModuleType('source_locator_tests')
source.__file__ = str(SCRIPT.absolute())
exec(compile(SCRIPT.read_bytes(), str(SCRIPT), 'exec'), source.__dict__)
bounded, engine, locator = source.dependencies()


def encoded(value):
    return json.dumps(value, indent=2, ensure_ascii=False).encode('utf-8')


class SourceTests(unittest.TestCase):
    def check(self, contract, document):
        cs = source.Source(contract, 'contract.json')
        ds = source.Source(document, 'document.json')
        original = locator.explain(engine, cs.value, ds.value)
        result = source.locate(engine, locator, cs, ds)
        self.assertEqual(result['valid'], original['valid'])
        self.assertEqual(result['error_count'], original['error_count'])
        self.assertEqual([{k: v for k, v in error.items()
                           if k not in ('document_source', 'contract_source')}
                          for error in result['errors']], original['errors'])
        for error in result['errors']:
            rule = self.slice(cs, error['contract_source']['value'])
            self.assertTrue(engine.same(json.loads(rule), locator.at(cs.value, error['contract_path'])))
            loc = error['document_source']
            if loc['present']:
                token = self.slice(ds, loc['value'])
                self.assertTrue(engine.same(json.loads(token), locator.at(ds.value, error['path'])))
            else:
                self.assertNotIn('value', loc)
                self.assertIsInstance(json.loads(self.slice(ds, loc['anchor']['value'])), dict)
        return result

    def slice(self, doc, span):
        start, end = span['start'], span['end']
        raw = doc.data[start['byte_offset']:end['byte_offset']].decode('utf-8')
        self.assertEqual(raw, doc.text[start['char_offset']:end['char_offset']])
        for point in (start, end):
            prefix = doc.text[:point['char_offset']]
            self.assertEqual(point['line'], prefix.count('\n') + 1)
            self.assertEqual(point['column'], len(prefix.rsplit('\n', 1)[-1]) + 1)
        return raw

    def test_actual_invalid_report(self):
        result = self.check(bounded.read_bytes('line-2/tools/json-contract/report.contract.json'),
                            bounded.read_bytes('line-2/tools/rule-locator/report.invalid.json'))
        self.assertEqual(result['error_count'], 3)
        error = next(e for e in result['errors'] if e['path'] == '/checks/0/passed')
        self.assertEqual(error['contract_path'], '/properties/checks/items/properties/passed/type')
        self.assertTrue(error['document_source']['present'])

    def test_actual_saved_zto_policy(self):
        result = self.check(bounded.read_bytes('shared/payment-evidence/policy.contract.json'),
                            bounded.read_bytes('shared/payment-evidence/example.policy.json'))
        self.assertTrue(result['valid'])
        self.assertEqual(result['errors'], [])

    def test_actual_strict_numbered_record(self):
        result = self.check(bounded.read_bytes('line-2/tools/ordered-deliverables/record.strict.contract.json'),
                            bounded.read_bytes('dist/line-2/26.json'))
        self.assertTrue(result['valid'])

    def test_unicode_crlf_tabs_and_escaped_key(self):
        contract = {'type': 'object', 'properties': {'é/🐸~': {'type': 'integer'}}}
        document = '{\r\n\t"é/🐸~": "non",\r\n "ignored": 4\r\n}'.encode('utf-8')
        result = self.check(encoded(contract), document)
        e = result['errors'][0]
        self.assertEqual(e['path'], '/é~1🐸~0')
        start = e['document_source']['value']['start']
        self.assertEqual((start['line'], start['column']), (2, 10))
        self.assertGreater(start['byte_offset'], start['char_offset'])
        self.assertEqual(e['document_source']['key']['start']['column'], 2)

    def test_escaped_lexemes_are_not_reserialized(self):
        document = b'{"a\\u002fb~": "\\u006e\\u006f", "empty": []}'
        contract = {'type': 'object', 'properties': {'a/b~': {'type': 'integer'}}}
        e = self.check(encoded(contract), document)['errors'][0]
        ds = source.Source(document, 'd')
        self.assertEqual(self.slice(ds, e['document_source']['key']), '"a\\u002fb~"')
        self.assertEqual(self.slice(ds, e['document_source']['value']), '"\\u006e\\u006f"')

    def test_missing_field_and_present_null_are_distinct(self):
        c = {'type': 'object', 'required': ['missing'], 'properties': {
             'missing': {'type': 'integer'}, 'present': {'type': 'integer'}}}
        result = self.check(encoded(c), b'{"present":null}')
        missing, present = result['errors']
        self.assertFalse(missing['document_source']['present'])
        self.assertEqual(missing['document_source']['anchor']['path'], '')
        self.assertEqual(missing['contract_path'], '/required/0')
        self.assertTrue(present['document_source']['present'])

    def test_empty_and_escaped_missing_names(self):
        for name in ('', '/', '~', 'a/b~c', '~1', '0', 'é🐸'):
            c = {'type': 'object', 'properties': {'box': {'type': 'object',
                'required': [name], 'properties': {name: {'type': 'null'}}}}}
            e = self.check(encoded(c), b'{"box":{}}')['errors'][0]
            self.assertEqual(e['document_source']['anchor']['path'], '/box')

    def test_root_span_and_trailing_whitespace(self):
        result = self.check(b' {"type":"integer"} \n', b' \n true\t\n')
        e = result['errors'][0]
        self.assertEqual(e['path'], '')
        self.assertNotIn('key', e['document_source'])
        self.assertEqual(e['document_source']['value']['start']['byte_offset'], 3)
        self.assertEqual(e['document_source']['value']['end']['byte_offset'], 7)

    def test_additional_property_key_span(self):
        c = b'{"type":"object","additionalProperties":false}'
        e = self.check(c, b'{"surprise":[1, {"x":2}]}')['errors'][0]
        self.assertEqual(e['path'], '/surprise')
        self.assertEqual(e['document_source']['key']['start']['byte_offset'], 1)
        self.assertEqual(e['document_source']['key']['end']['byte_offset'], 11)

    def test_prefix_tail_and_duplicate_locations(self):
        c = {'type': 'array', 'prefixItems': [{'type': 'string'}],
             'items': {'type': 'integer', 'minimum': 3}, 'uniqueItems': True}
        errors = self.check(encoded(c), b'[null, 2, 2]')['errors']
        self.assertEqual([e['contract_path'] for e in errors],
                         ['/items/minimum', '/items/minimum', '/prefixItems/0/type', '/uniqueItems'])
        self.assertEqual(errors[-1]['document_source']['value']['start']['byte_offset'], 10)

    def test_all_token_types_and_exact_ranges(self):
        raw = b' {"a": [true,false,null,-10,1.20e+2,"a\\\"b",{},[]],"":{}} '
        doc = source.Source(raw, 'd')
        for path, pair in doc.values.items():
            parsed = json.loads(self.slice(doc, doc.span(pair)))
            self.assertTrue(engine.same(parsed, locator.at(doc.value, path)))

    def test_all_supported_constraints_and_multiplicity(self):
        cases = [({'type': 'string', 'minLength': 3, 'pattern': '^x', 'enum': ['xxx']}, 'a'),
                 ({'type': 'string', 'maxLength': 0}, 'a'),
                 ({'type': 'array', 'minItems': 2}, []),
                 ({'type': 'array', 'maxItems': 0}, [1]),
                 ({'type': 'integer', 'minimum': 2}, 1),
                 ({'type': 'number', 'maximum': 2}, 3.5)]
        for c, d in cases:
            self.assertFalse(self.check(encoded(c), encoded(d))['valid'])

    def test_input_identity_commits_formatting(self):
        c = encoded({'type': 'object'})
        for d in (b'{}', b' { }\n'):
            result = self.check(c, d)
            self.assertEqual(result['sources']['document']['sha256'], hashlib.sha256(d).hexdigest())
            self.assertEqual(result['sources']['document']['bytes'], len(d))

    def test_malformed_duplicate_nonfinite_and_encoding_refused(self):
        cases = [b'{', b'{}[]', b'01', b'[1,]', b'NaN', b'Infinity', b'1e9999',
                 b'{"x":1,"\\u0078":2}', b'"\xff"', b'\xef\xbb\xbf{}',
                 b'{"x":1,}', b'"\x01"', b' ' * 1_000_001]
        for data in cases:
            with self.subTest(data=data[:40]):
                with self.assertRaises(ValueError):
                    source.Source(data, 'd')

    def test_many_flat_tokens(self):
        raw = encoded(['é🐸', 123, None, {}, []] * 2000)
        doc = source.Source(raw, 'flat')
        self.assertEqual(len(doc.values), 10001)
        self.assertEqual(json.loads(self.slice(doc, doc.span(doc.values['/9999']))), [])

    def test_cli_exits_and_no_follow_boundaries(self):
        Path('test/scratch').mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir='test/scratch') as directory:
            root = Path(directory).absolute().relative_to(Path.cwd())
            c, d = root / 'contract.json', root / 'document.json'
            c.write_bytes(b'{"type":"integer"}')
            def run(name):
                out = io.StringIO()
                with contextlib.redirect_stdout(out):
                    code = source.main([str(c), str(name)])
                return code, json.loads(out.getvalue())
            d.write_bytes(b'1')
            self.assertEqual(run(d)[0], 0)
            d.write_bytes(b'true')
            self.assertEqual(run(d)[0], 1)
            d.write_bytes(b'{')
            code, result = run(d)
            self.assertEqual(code, 2)
            self.assertFalse(result['valid'])
            self.assertNotIn('errors', result)
            link = root / 'link.json'
            link.symlink_to('document.json')
            for name in (link, '/outside.json', '../outside.json', '.hidden.json'):
                self.assertEqual(run(name)[0], 2)
            d.write_bytes(b'1')
            c.write_bytes(b'{"type":"integer","minimun":2}')
            self.assertEqual(run(d)[0], 2)


if __name__ == '__main__':
    unittest.main(verbosity=2)
