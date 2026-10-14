#!/usr/bin/env python3
"""Locate policy mistakes, then evaluate saved payment evidence at explicit time."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

from check import module

source = module('time_review_source', 'vendor/source-locator/locate.py')
freshness = module('time_review_freshness', 'vendor/settlement-freshness/freshness.py')
MAX_BYTES = 90000
MAX_OUTPUT_BYTES = 100000
HERE = Path(__file__).resolve().parent


def review(transcript_path, policy_path, as_of, max_head_age,
           max_finalized_age, future_skew=0):
    """Read each input once; source locations and decisions use those same bytes.

    No current clock is guessed. Caller time and policy must be independently
    selected. Historical timestamps inside the transcript cannot set the clock.
    """
    bounded, engine, locator = source.dependencies()
    contract_path = (HERE / 'policy.contract.json').relative_to(Path.cwd()).as_posix()
    contract = source.Source(bounded.read_bytes(contract_path, MAX_BYTES), contract_path)
    raw_policy = bounded.read_bytes(str(policy_path), MAX_BYTES)
    policy = source.Source(raw_policy, str(policy_path))
    explanation = source.locate(engine, locator, contract, policy)
    if not explanation['valid']:
        return {'accepted': False, 'state': 'policy_error',
                'policyExplanation': explanation,
                'evidenceEvaluated': False}
    # Semantic bounds (including finalized=true and uint256 amounts) are checked
    # separately from structural rules, before reading potentially large evidence.
    freshness.validate(policy.value, as_of, max_head_age, max_finalized_age, future_skew)
    raw = bounded.read_bytes(str(transcript_path), MAX_BYTES)
    sample = source.strict_json(raw.decode('utf-8'))
    result = freshness.evaluate(sample, policy.value, as_of, max_head_age,
                                max_finalized_age, future_skew)
    result.update(policyExplanation=explanation, evidenceEvaluated=True,
                  transcriptFile={'file': str(transcript_path), 'bytes': len(raw),
                                  'sha256': hashlib.sha256(raw).hexdigest()},
                  providerAgreement='Single saved observation; no independent-provider agreement is established.')
    return result


def render(result):
    text = json.dumps(result, ensure_ascii=True, allow_nan=False, indent=2) + '\n'
    if len(text.encode('utf-8')) > MAX_OUTPUT_BYTES:
        raise ValueError('time review exceeds 100000-byte output limit')
    return text


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('transcript', help='saved timestamp-bearing payment evidence')
    parser.add_argument('policy', help='independently chosen payment policy file')
    parser.add_argument('--as-of', type=int, required=True)
    parser.add_argument('--max-head-age', type=int, required=True)
    parser.add_argument('--max-finalized-age', type=int, required=True)
    parser.add_argument('--future-skew', type=int, default=0)
    args = parser.parse_args(argv)
    try:
        result = review(args.transcript, args.policy, args.as_of, args.max_head_age,
                        args.max_finalized_age, args.future_skew)
        text = render(result)  # Refuse oversized diagnostics before any stdout.
        print(text, end='')
        return 0 if result['accepted'] else 2 if result['state'] == 'policy_error' else 1
    except (ValueError, OSError, TypeError, KeyError, IndexError, RecursionError):
        print(json.dumps({'accepted': False, 'state': 'input_error',
                          'reason': 'Invalid time/policy input, unsafe file, inconsistent evidence or output limit.'}))
        return 2


if __name__ == '__main__':
    sys.exit(main())
