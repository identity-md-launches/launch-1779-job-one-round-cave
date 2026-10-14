"""Offline integration checks using real historical ZTO evidence."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import time_review as t

HERE = Path(__file__).resolve().parent.relative_to(Path.cwd())
SAMPLE = HERE / 'example.timed-transcript.json'
POLICY = HERE / 'example.timed-policy.json'
TIME = (1792008919, 120, 1200, 30)


class ReviewTests(unittest.TestCase):
    def setUp(self):
        Path('test/scratch').mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir='test/scratch')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).absolute().relative_to(Path.cwd())

    def write(self, name, value):
        path = self.root / name
        path.write_text(json.dumps(value, indent=2))
        return path

    def cli(self, sample=SAMPLE, policy=POLICY, when=TIME[0]):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = t.main([str(sample), str(policy), '--as-of', str(when),
                           '--max-head-age', '120', '--max-finalized-age', '1200',
                           '--future-skew', '30'])
        return code, json.loads(out.getvalue())

    def test_real_historical_acceptance_and_exact_input_hashes(self):
        before = SAMPLE.read_bytes(), POLICY.read_bytes()
        result = t.review(SAMPLE, POLICY, *TIME)
        self.assertTrue(result['accepted'])
        self.assertEqual(result['anchors']['head']['ageSeconds'], 8)
        self.assertEqual(result['anchors']['finalized']['ageSeconds'], 896)
        self.assertEqual(result['transcriptFile']['sha256'], hashlib.sha256(before[0]).hexdigest())
        self.assertEqual(result['policyExplanation']['sources']['document']['sha256'], hashlib.sha256(before[1]).hexdigest())
        self.assertEqual(before, (SAMPLE.read_bytes(), POLICY.read_bytes()))

    def test_stale_evidence_rejected_even_when_payment_passes(self):
        code, result = self.cli(when=TIME[0]+1201)
        self.assertEqual(code, 1)
        self.assertTrue(result['payment']['accepted'])
        self.assertEqual(result['alerts'], ['head_too_old', 'finalized_too_old'])

    def test_exact_age_boundaries(self):
        self.assertTrue(t.review(SAMPLE, POLICY, TIME[0], 8, 896, 30)['accepted'])
        self.assertFalse(t.review(SAMPLE, POLICY, TIME[0], 7, 896, 30)['accepted'])

    def test_structural_error_has_exact_source_and_rule_spans(self):
        policy = json.loads(POLICY.read_text())
        policy['finalized'] = 'yes'
        path = self.write('invalid.json', policy)
        code, result = self.cli(sample='missing-evidence.json', policy=path)
        self.assertEqual(code, 2)
        self.assertEqual(result['state'], 'policy_error')
        self.assertFalse(result['evidenceEvaluated'])
        error = result['policyExplanation']['errors'][0]
        span = error['document_source']['value']
        self.assertEqual(path.read_bytes()[span['start']['byte_offset']:span['end']['byte_offset']], b'"yes"')
        self.assertEqual(error['contract_path'], '/properties/finalized/type')

    def test_missing_policy_field_is_absent_not_null(self):
        policy = json.loads(POLICY.read_text())
        del policy['recipient']
        _, result = self.cli(policy=self.write('missing.json', policy))
        error = result['policyExplanation']['errors'][0]
        self.assertFalse(error['document_source']['present'])
        self.assertNotIn('value', error['document_source'])

    def test_policy_cannot_silently_change_evidence(self):
        policy = json.loads(POLICY.read_text())
        policy['minimum_raw'] = '1'
        code, result = self.cli(policy=self.write('mismatch.json', policy))
        self.assertEqual((code, result['state']), (2, 'input_error'))

    def test_semantic_policy_failure(self):
        policy = json.loads(POLICY.read_text())
        policy['finalized'] = False
        self.assertEqual(self.cli(policy=self.write('unfinalized.json', policy))[0], 2)

    def test_timestamp_free_ancestor_and_tampered_requests_fail(self):
        old = HERE / 'example.transcript.json'
        self.assertEqual(self.cli(sample=old)[0], 2)
        sample = json.loads(SAMPLE.read_text())
        sample['reads'][1]['params'][1] = 0
        self.assertEqual(self.cli(sample=self.write('tampered.json', sample))[0], 2)

    def test_duplicate_json_and_nonfinite_fail(self):
        bad = self.root / 'malformed.json'
        for raw in ('{"version":1,"version":1}', '{"value":NaN}', '{'):
            bad.write_text(raw)
            self.assertEqual(self.cli(sample=bad)[0], 2)
            self.assertEqual(self.cli(policy=bad)[0], 2)

    def test_unsafe_and_oversized_inputs_fail(self):
        link = self.root / 'link.json'
        link.symlink_to(POLICY.resolve())
        for path in (link, '../outside.json', '.hidden.json'):
            self.assertEqual(self.cli(policy=path)[0], 2)
        large = self.root / 'large.json'
        large.write_bytes(b' ' * 90001)
        self.assertEqual(self.cli(sample=large)[0], 2)

    def test_input_files_read_once(self):
        bounded, engine, locator = t.source.dependencies()
        reads = []
        original = bounded.read_bytes
        def read(path, limit):
            reads.append(str(path))
            return original(path, limit)
        with patch.object(t.source, 'dependencies', return_value=(bounded, engine, locator)), patch.object(bounded, 'read_bytes', side_effect=read):
            self.assertTrue(t.review(SAMPLE, POLICY, *TIME)['accepted'])
        self.assertEqual(reads.count(str(SAMPLE)), 1)
        self.assertEqual(reads.count(str(POLICY)), 1)

    def test_clock_required_not_taken_from_saved_observation(self):
        with self.assertRaises(ValueError):
            t.review(SAMPLE, POLICY, None, 120, 1200)
        self.assertEqual(self.cli(when=1)[0], 1)

    def test_cli_success_and_bounded_fail_closed_output(self):
        self.assertEqual(self.cli()[0], 0)
        with patch.object(t, 'MAX_OUTPUT_BYTES', 100):
            code, result = self.cli()
        self.assertEqual((code, result['state']), (2, 'input_error'))


if __name__ == '__main__':
    unittest.main(verbosity=2)
