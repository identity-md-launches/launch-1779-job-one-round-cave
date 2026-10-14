"""Offline report checks using saved real ZTO evidence and labeled mutations."""
import copy
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import patch
import io

R = runpy.run_path(str(Path(__file__).with_name('report.py')))
P = R['P']
RAW = Path('line-1/tools/compare-zto-snapshots/live-zto.json').read_bytes()


class Document(HTMLParser):
    def __init__(self, raw):
        super().__init__(convert_charrefs=True)
        self.tags = []
        self.attrs = []
        self.transcript = ''
        self.inside = False
        self.feed(raw.decode())

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        self.attrs.extend(attrs)
        if tag == 'pre' and dict(attrs).get('id') == 'transcript':
            self.inside = True

    def handle_endtag(self, tag):
        if tag == 'pre':
            self.inside = False

    def handle_data(self, data):
        if self.inside:
            self.transcript += data


def seal(bundle):
    for read in bundle['reads']:
        read['response_sha256'] = P['digest'](read['response'])
    bundle['reads_sha256'] = P['digest'](bundle['reads'])
    return json.dumps(bundle).encode()


class ReportTests(unittest.TestCase):
    def test_real_report_round_trip(self):
        report = R['render'](RAW)
        doc = Document(report)
        original = json.loads(RAW)
        self.assertEqual(json.loads(doc.transcript), original)
        self.assertEqual(P['validate_bundle'](json.loads(doc.transcript)),
                         P['validate_bundle'](original))
        self.assertEqual(doc.tags.count('details'), 6)
        self.assertIn(hashlib.sha256(RAW).hexdigest().encode(), report)
        self.assertIn(b'1000000000.000000000000000000', report)

    def test_no_active_content(self):
        doc = Document(R['render'](RAW))
        self.assertFalse(set(doc.tags) & {'script', 'img', 'iframe', 'link', 'form', 'object', 'embed'})
        self.assertFalse(any(k.startswith('on') or k in ('src', 'href') for k, v in doc.attrs))
        self.assertIn(('http-equiv', 'Content-Security-Policy'), doc.attrs)

    def test_hostile_provider_text_remains_text(self):
        b = json.loads(RAW)
        attack = '</pre><script>alert(1)</script><img src="https://invalid/" onerror="x">&'
        b['reads'][1]['response']['result']['extra'] = attack
        b['reads'][0]['content_type'] = attack
        doc = Document(R['render'](seal(b)))
        self.assertNotIn('script', doc.tags)
        self.assertNotIn('img', doc.tags)
        self.assertEqual(json.loads(doc.transcript), b)

    def test_tampered_commitment_rejected(self):
        b = json.loads(RAW)
        b['reads'][2]['response']['result'] = '0x' + 'f' * 64
        with self.assertRaises(ValueError):
            R['render'](json.dumps(b).encode())

    def test_resealed_wrong_contract_rejected(self):
        b = json.loads(RAW)
        b['reads'][2]['params'][0]['to'] = '0xd34a99bc0f67ae1bbd63c660e6d0b0dd03e263b7'
        with self.assertRaises(ValueError):
            R['render'](seal(b))

    def test_duplicate_json_rejected(self):
        with self.assertRaises(P['B']['SnapshotError']):
            R['render'](b'{"schema":1,"schema":2}')

    def test_byte_limit_and_expansion(self):
        with self.assertRaises(ValueError):
            R['render'](b' ' * 100001)
        b = json.loads(RAW)
        b['reads'][1]['response']['result']['extra'] = '<' * 14000
        raw = seal(b)
        self.assertLess(len(raw), 100000)
        with self.assertRaisesRegex(ValueError, 'rendered report exceeds'):
            R['render'](raw)

    def test_byte_hash_differs_content_hash_stable(self):
        b = json.loads(RAW)
        compact = P['canonical'](b)
        self.assertNotEqual(hashlib.sha256(RAW).hexdigest(), hashlib.sha256(compact).hexdigest())
        for raw in (RAW, compact):
            output = R['render'](raw)
            self.assertIn(P['digest'](b).encode(), output)
            self.assertIn(hashlib.sha256(raw).hexdigest().encode(), output)

    def test_deterministic_and_no_mutation(self):
        original = copy.deepcopy(RAW)
        self.assertEqual(R['render'](RAW), R['render'](RAW))
        self.assertEqual(RAW, original)

    def test_cli_files_and_no_clobber(self):
        Path('test/scratch').mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir='test/scratch') as folder:
            root = Path(folder).resolve().relative_to(Path.cwd())
            source, output = root / 'source.json', root / 'report.html'
            source.write_bytes(RAW)
            with patch('sys.stdout', new_callable=io.StringIO), patch('sys.stderr', new_callable=io.StringIO):
                self.assertEqual(R['main']([str(source), '--output', str(output)]), 0)
                expected = output.read_bytes()
                self.assertEqual(R['main']([str(source), '--output', str(output)]), 1)
                self.assertEqual(output.read_bytes(), expected)
                link = root / 'link.json'
                link.symlink_to('source.json')
                self.assertEqual(R['main']([str(link)]), 1)
                self.assertEqual(R['main'](['../source.json']), 1)
                source.write_bytes(b'{}')
                new = root / 'invalid.html'
                self.assertEqual(R['main']([str(source), '--output', str(new)]), 1)
                self.assertFalse(new.exists())


if __name__ == '__main__':
    unittest.main()
