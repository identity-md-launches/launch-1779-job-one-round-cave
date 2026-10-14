import contextlib
import copy
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from request_set_check import compare_set, main
from typed_digest import TypedDataError, loads_bounded

ROOT = Path(__file__).parent
DEMO = json.loads((ROOT / 'zto-set.json').read_text())


class SetTests(unittest.TestCase):
    def setUp(self):
        self.left = copy.deepcopy(DEMO)
        self.right = copy.deepcopy(DEMO)

    def two(self):
        for side in (self.left, self.right):
            entry = copy.deepcopy(side['requests'][0])
            entry['reviewId'] = 'second-review'
            side['requests'].append(entry)

    def test_historical_match(self):
        result = compare_set(self.left, self.right)
        self.assertTrue(result['accepted'])
        self.assertEqual(result['items'][0]['client']['digest'],
                         '0xf33e2506e5c103f98dbfe3feb6d4b87d55f1fad4e423dbaa8462465ff4ab9774')

    def test_missing(self):
        self.right['requests'].clear()
        result = compare_set(self.left, self.right)
        self.assertFalse(result['accepted'])
        self.assertEqual(result['missing'], ['zto-receipt-review'])

    def test_added(self):
        self.two()
        self.left['requests'].pop()
        result = compare_set(self.left, self.right)
        self.assertFalse(result['accepted'])
        self.assertEqual(result['added'], ['second-review'])

    def test_reordered_even_with_identical_payloads(self):
        self.two()
        self.right['requests'].reverse()
        result = compare_set(self.left, self.right)
        self.assertTrue(result['membershipMatches'])
        self.assertTrue(all(x['accepted'] for x in result['items']))
        self.assertFalse(result['orderMatches'])
        self.assertFalse(result['accepted'])

    def test_renamed(self):
        self.right['requests'][0]['reviewId'] = 'different'
        result = compare_set(self.left, self.right)
        self.assertEqual(result['missing'], ['zto-receipt-review'])
        self.assertEqual(result['added'], ['different'])
        self.assertFalse(result['accepted'])

    def test_duplicate_id_either_side(self):
        for side in ('left', 'right'):
            self.setUp()
            value = getattr(self, side)
            value['requests'].append(copy.deepcopy(value['requests'][0]))
            with self.assertRaisesRegex(TypedDataError, 'duplicate reviewId'):
                compare_set(self.left, self.right)

    def test_empty_intended_never_vacuously_accepted(self):
        with self.assertRaisesRegex(TypedDataError, 'must not be empty'):
            compare_set({'requests': []}, {'requests': []})

    def test_wrong_account_equal_digest(self):
        self.right['requests'][0]['request']['params'][0] = '0xd782bdea4ef02a0bd391eb9089470c8080f0a68e'
        result = compare_set(self.left, self.right)
        self.assertFalse(result['accepted'])
        self.assertTrue(result['items'][0]['digestMatches'])
        self.assertFalse(result['items'][0]['accountMatches'])

    def test_changed_amount_has_pointer(self):
        envelope = self.right['requests'][0]['request']
        data = json.loads(envelope['params'][1])
        data['message']['minimumRaw'] = str(int(data['message']['minimumRaw']) + 1)
        envelope['params'][1] = json.dumps(data)
        result = compare_set(self.left, self.right)
        self.assertFalse(result['accepted'])
        self.assertIn('/message/minimumRaw', [d['path'] for d in result['items'][0]['differences']])

    def test_case_and_transport_id_equivalence(self):
        request = self.right['requests'][0]['request']
        request['params'][0] = '0x' + request['params'][0][2:].upper()
        request.update(jsonrpc='2.0', id='different-id')
        self.assertTrue(compare_set(self.left, self.right)['accepted'])

    def test_malformed_unmatched_request_not_hidden(self):
        self.two()
        self.right['requests'][1]['request']['method'] = 'eth_sendTransaction'
        self.left['requests'].pop()
        with self.assertRaisesRegex(TypedDataError, 'only eth_signTypedData_v4'):
            compare_set(self.left, self.right)
        with self.assertRaises(TypedDataError):
            compare_set(self.right, self.left)

    def test_schema_shapes(self):
        bad = [[], None, {'requests': {}}, {'requests': [], 'extra': 1},
               {'requests': [None]}, {'requests': [{'reviewId': 'a'}]}]
        for value in bad:
            with self.subTest(value=value), self.assertRaises(TypedDataError):
                compare_set(self.left, value)

    def test_label_bounds(self):
        for key in ('', '.a', 'a/b', 'a b', 'é', 'a\n', 'a' * 65, True, 1):
            self.right['requests'][0]['reviewId'] = key
            with self.subTest(key=key), self.assertRaises(TypedDataError):
                compare_set(self.left, self.right)

    def test_entry_cap_and_max_label(self):
        self.right['requests'][0]['reviewId'] = 'a' * 64
        self.assertFalse(compare_set(self.left, self.right)['accepted'])
        self.right['requests'] = [dict(reviewId=str(i), request=DEMO['requests'][0]['request']) for i in range(17)]
        with self.assertRaisesRegex(TypedDataError, 'at most 16'):
            compare_set(self.left, self.right)

    def test_cycle_and_bad_unicode(self):
        self.right['requests'].append(self.right)
        with self.assertRaises(TypedDataError):
            compare_set(self.left, self.right)
        self.right = copy.deepcopy(DEMO)
        self.right['requests'][0]['reviewId'] = '\ud800'
        with self.assertRaises(TypedDataError):
            compare_set(self.left, self.right)

    def test_strict_json_duplicate_float_and_depth(self):
        for raw in (b'{"requests":[],"requests":[]}', b'{"requests":1.5}',
                    b'[' * 49 + b'0' + b']' * 49, b' ' * 65537):
            with self.subTest(raw=raw[:60]), self.assertRaises(ValueError):
                loads_bounded(raw)

    def test_aggregate_report_cap(self):
        with patch('request_set_check.MAX_REPORT_BYTES', 100):
            with self.assertRaisesRegex(TypedDataError, 'report limit'):
                compare_set(self.left, self.right)

    def test_no_mutation(self):
        left, right = copy.deepcopy(self.left), copy.deepcopy(self.right)
        compare_set(self.left, self.right)
        self.assertEqual(self.left, left)
        self.assertEqual(self.right, right)

    def test_cli_accept_and_summary(self):
        path = str(ROOT / 'zto-set.json')
        for options in ([], ['--summary']):
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(main([path, path] + options), 0)
            result = json.loads(output.getvalue())
            self.assertTrue(result['accepted'])
            self.assertEqual('differences' in result['items'][0], not bool(options))

    def test_cli_reject_missing(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main([str(ROOT / 'zto-set.json'), str(ROOT / 'missing-set.json')]), 1)

    def test_cli_outside_and_symlink(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(['../outside.json', str(ROOT / 'zto-set.json')]), 2)
            # Tests are read-only; the scratch runner supplies this link.
            link = Path('test/scratch/request-set-link.json')
            if link.is_symlink():
                self.assertEqual(main([str(link), str(ROOT / 'zto-set.json')]), 2)

    def test_summary_does_not_bypass_report_cap(self):
        with patch('request_set_check.MAX_REPORT_BYTES', 100), contextlib.redirect_stderr(io.StringIO()):
            path = str(ROOT / 'zto-set.json')
            self.assertEqual(main([path, path, '--summary']), 2)


if __name__ == '__main__':
    unittest.main()
