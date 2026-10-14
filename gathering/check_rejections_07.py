#!/usr/bin/env python3
"""Exercise the latest line CLIs and time-review rejection paths offline."""
import json
from pathlib import Path
import subprocess
import sys


def main():
    policy = json.loads(Path('shared/payment-evidence/example.timed-policy.json').read_text())
    policy['finalized'] = 'yes'  # Deliberately invalid test input, never chain evidence.
    scratch = Path('test/scratch')
    scratch.mkdir(parents=True, exist_ok=True)
    invalid = scratch / 'invalid-policy-07.json'
    invalid.write_text(json.dumps(policy, indent=2) + '\n')
    timing = ['--as-of', '1792010120', '--max-head-age', '120',
              '--max-finalized-age', '1200', '--future-skew', '30']
    commands = [
        (1, ['line-1/tools/snapshot-report/report.py',
             'line-1/tools/bounded-rpc-snapshot/sample-zto-supply.json']),
        (1, ['line-2/tools/source-locator/locate.py',
             'line-2/tools/json-contract/report.contract.json',
             'line-2/tools/rule-locator/report.invalid.json']),
        (1, ['line-3/tools/settlement-freshness/freshness.py', '--replay',
             'line-3/tools/settlement-freshness/live-evidence.json', '--policy',
             'line-3/tools/settlement-freshness/observed-policy.json', *timing]),
        (1, ['line-4/tools/request-set-check/request_set_check.py',
             'line-4/tools/request-set-check/zto-set.json',
             'line-4/tools/request-set-check/missing-set.json', '--summary']),
        (1, ['shared/payment-evidence/time_review.py',
             'shared/payment-evidence/example.timed-transcript.json',
             'shared/payment-evidence/example.timed-policy.json', *timing]),
        (2, ['shared/payment-evidence/time_review.py',
             'shared/payment-evidence/example.timed-transcript.json', str(invalid), *timing]),
    ]
    rows = []
    for expected, args in commands:
        result = subprocess.run([sys.executable, '-B', *args], capture_output=True,
                                text=True, timeout=30)
        rows.append({'command': ['python3', '-B', *args], 'expectedExitCode': expected,
                     'exitCode': result.returncode, 'passed': result.returncode == expected,
                     'stdout': result.stdout, 'stderr': result.stderr})
    Path('gathering/rejection-checks-07.json').write_text(json.dumps(rows, indent=2) + '\n')
    passed = all(row['passed'] for row in rows)
    print(json.dumps({'passed': passed, 'checks': len(rows)}))
    return 0 if passed else 1


if __name__ == '__main__':
    sys.exit(main())
