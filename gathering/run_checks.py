#!/usr/bin/env python3
"""Run every line's documented offline check without modifying line folders."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent.parent


def main():
    if Path.cwd().resolve() != ROOT:
        raise SystemExit('Run this command from the repository root')
    scratch = ROOT / 'test/scratch'
    scratch.mkdir(parents=True, exist_ok=True)
    # Line 4's tests create/remove fixtures beside their source. Run an exact
    # copy in scratch so even temporary line-folder modifications are avoided.
    shutil.copytree(ROOT / 'line-4/tools/typed-digest', scratch / 'typed-digest', dirs_exist_ok=True)
    commands = [
        ['line-1/tools/rpc_snapshot.py', '--verify', 'line-1/tools/bounded-rpc-snapshot/sample-zto-supply.json'],
        ['line-1/tools/bounded-rpc-snapshot/snapshot.py', '--verify', 'line-1/tools/bounded-rpc-snapshot/sample-zto-supply.json'],
        ['line-1/tools/anchored-zto-snapshot/anchored.py', '--verify', 'line-1/tools/anchored-zto-snapshot/sample.json'],
        ['line-2/tools/json-contract/check.py', 'line-2/tools/json-contract/report.contract.json', 'line-2/tools/json-contract/report.example.json'],
        ['line-2/tools/json-contract/test_check.py'],
        ['line-2/tools/ordered-deliverables/check.py', 'line-2/tools/ordered-deliverables/handoff.contract.json', 'line-2/tools/ordered-deliverables/handoff.example.json'],
        ['line-2/tools/ordered-deliverables/test_ordered.py'],
        ['line-2/tools/batch-contract/check.py', 'line-2/tools/ordered-deliverables/record.strict.contract.json', 'dist/line-2/01.json', 'dist/line-2/22.json', 'dist/line-2/23.json'],
        ['-m', 'unittest', 'discover', '-s', 'line-3/tools/settlement-check', '-p', 'test_*.py', '-v'],
        ['line-3/tools/payment-witness/witness.py', '--replay', 'line-3/tools/payment-witness/live-evidence.json'],
        ['-m', 'unittest', 'discover', '-s', 'line-3/tools/payment-witness', '-p', 'test_*.py', '-v'],
        ['line-3/tools/rpc-boundary/check.py'],
        ['line-4/tools/typed-digest/typed_digest.py', 'line-4/tools/typed-digest/zto-example.json', '--expect', '0xc292388738e2cf2c7f57b9b8926821aff508ed38c1b355020cc7dc459dbbb8cb'],
        ['-m', 'unittest', 'discover', '-s', 'test/scratch/typed-digest', '-p', 'test_*.py', '-v'],
        ['line-4/tools/typed-trace/typed_trace.py', 'line-4/tools/typed-trace/zto-payment.json', '--expect', '0xf33e2506e5c103f98dbfe3feb6d4b87d55f1fad4e423dbaa8462465ff4ab9774', '--summary'],
        ['-m', 'unittest', 'discover', '-s', 'line-4/tools/typed-trace', '-p', 'test_*.py', '-v'],
        ['shared/rpc-evidence/test_bridge.py'],
        ['shared/rpc-evidence/verify.py', 'shared/rpc-evidence/chain-id.snapshot.json'],
        ['shared/payment-evidence/test_evidence.py'],
        ['shared/payment-evidence/explain.py', 'shared/payment-evidence/example.transcript.json', 'shared/payment-evidence/example.policy.json', '--summary'],
        ['shared/payment-evidence/test_explain.py'],
        ['line-1/tools/safe-snapshot-files/test_safe_files.py'],
        ['line-1/tools/anchored-zto-snapshot/anchored.py', '--verify', 'line-1/tools/safe-snapshot-files/live-zto.json'],
        ['line-1/tools/safe-snapshot-files/safe_files.py', 'line-1/tools/safe-snapshot-files/live-zto.json'],
        ['line-2/tools/bounded-contract/check.py', 'line-2/tools/ordered-deliverables/record.strict.contract.json', 'dist/line-2/01.json', 'dist/line-2/22.json', 'dist/line-2/23.json', 'dist/line-2/24.json'],
        ['line-2/tools/bounded-contract/test_check.py'],
        ['line-3/tools/discovery-diagnostic/diagnose.py', '--replay-known'],
        ['-m', 'unittest', 'discover', '-s', 'line-3/tools/discovery-diagnostic', '-p', 'test_*.py'],
        ['line-4/tools/domain-check/domain_check.py', 'line-4/tools/domain-check/zto-payment.json', '--chain-id', '1', '--name', 'Read-only Payment Evidence', '--version', '1', '--primary-type', 'PaymentEvidence', '--no-verifier', '--expect', '0xf33e2506e5c103f98dbfe3feb6d4b87d55f1fad4e423dbaa8462465ff4ab9774'],
        ['-m', 'unittest', 'discover', '-s', 'line-4/tools/domain-check', '-v'],
        ['shared/payment-evidence/test_bind.py'],
        ['shared/payment-evidence/bind.py', 'shared/payment-evidence/example.transcript.json', 'shared/payment-evidence/example.policy.json', 'shared/payment-evidence/example.typed-data.json', '--chain-id', '1', '--name', 'Read-only Payment Evidence', '--version', '1', '--primary-type', 'PaymentEvidence', '--no-verifier', '--summary']]
    commands.extend([
        ['line-1/tools/hash-pinned-zto/pinned.py', '--verify', 'line-1/tools/hash-pinned-zto/live-zto.json'],
        ['line-1/tools/hash-pinned-zto/test_pinned.py'],
        ['line-2/tools/repair-review/review.py', 'line-2/tools/repair-review/handoff.contract.json', 'line-2/tools/repair-review/before.example.json', 'line-2/tools/repair-review/after.example.json'],
        ['line-2/tools/repair-review/test_review.py'],
        ['line-2/tools/bounded-contract/check.py', 'line-2/tools/ordered-deliverables/record.strict.contract.json', 'dist/line-2/25.json'],
        ['line-3/tools/provider-agreement/agreement.py', '--demo'],
        ['-m', 'unittest', 'discover', '-s', 'line-3/tools/provider-agreement', '-p', 'test_*.py', '-v'],
        ['line-4/tools/request-compare/request_compare.py', 'line-4/tools/request-compare/zto-intended.json', 'line-4/tools/request-compare/zto-intended.json', '--summary'],
        ['-m', 'unittest', 'discover', '-s', 'line-4/tools/request-compare', '-v'],
    ])
    commands.extend([
        ['shared/payment-evidence/test_corroborate.py'],
        ['shared/payment-evidence/corroborate.py', 'shared/payment-evidence/example.paired.json', 'shared/payment-evidence/example.paired-policy.json', 'shared/payment-evidence/example.paired-intended.json', 'shared/payment-evidence/example.paired-intended.json', '--summary'],
    ])
    commands.extend([
        ['line-1/tools/compare-zto-snapshots/compare.py', 'line-1/tools/hash-pinned-zto/live-zto.json', 'line-1/tools/compare-zto-snapshots/live-zto.json'],
        ['line-1/tools/compare-zto-snapshots/test_compare.py'],
        ['line-2/tools/rule-locator/explain.py', 'shared/payment-evidence/policy.contract.json', 'shared/payment-evidence/example.policy.json'],
        ['line-2/tools/rule-locator/test_explain.py'],
        ['line-2/tools/bounded-contract/check.py', 'line-2/tools/ordered-deliverables/record.strict.contract.json', 'dist/line-2/26.json'],
        ['line-3/tools/payment-recheck/recheck.py', '--demo'],
        ['-m', 'unittest', 'discover', '-s', 'line-3/tools/payment-recheck', '-v'],
        ['line-4/tools/rpc-request-check/rpc_request_check.py', 'line-4/tools/rpc-request-check/zto-envelope.json', 'line-4/tools/rpc-request-check/zto-envelope.json', '--summary'],
        ['-m', 'unittest', 'discover', '-s', 'line-4/tools/rpc-request-check', '-v'],
    ])
    commands.extend([
        ['shared/payment-evidence/test_revisit.py'],
        ['shared/payment-evidence/revisit.py', 'shared/payment-evidence/example.paired.json', 'shared/payment-evidence/round05.paired.json', 'shared/payment-evidence/example.paired-policy.json', 'shared/payment-evidence/example.revisit-envelope.json', 'shared/payment-evidence/example.revisit-envelope.json', '--summary'],
    ])
    commands.extend([
        ['line-1/tools/snapshot-report/report.py', 'line-1/tools/compare-zto-snapshots/live-zto.json'],
        ['line-1/tools/snapshot-report/test_report.py'],
        ['line-2/tools/source-locator/locate.py', 'shared/payment-evidence/policy.contract.json', 'shared/payment-evidence/example.policy.json'],
        ['line-2/tools/source-locator/test_locate.py'],
        ['line-2/tools/bounded-contract/check.py', 'line-2/tools/ordered-deliverables/record.strict.contract.json', 'dist/line-2/27.json'],
        ['line-3/tools/settlement-freshness/freshness.py', '--demo'],
        ['-m', 'unittest', 'discover', '-s', 'line-3/tools/settlement-freshness', '-v'],
        ['line-4/tools/request-set-check/request_set_check.py', 'line-4/tools/request-set-check/zto-set.json', 'line-4/tools/request-set-check/zto-set.json', '--summary'],
        ['-m', 'unittest', 'discover', '-s', 'line-4/tools/request-set-check', '-v'],
    ])
    commands.extend([
        ['shared/payment-evidence/test_time_review.py'],
        ['shared/payment-evidence/time_review.py', 'shared/payment-evidence/example.timed-transcript.json', 'shared/payment-evidence/example.timed-policy.json', '--as-of', '1792008919', '--max-head-age', '120', '--max-finalized-age', '1200', '--future-skew', '30'],
    ])
    results = []
    for args in commands:
        command = [sys.executable, '-B', *args]
        started = time.monotonic()
        result = subprocess.run(command, capture_output=True, text=True, timeout=45)
        results.append({'command': ' '.join(['python3', '-B', *args]),
                        'exitCode': result.returncode, 'seconds': round(time.monotonic()-started, 3),
                        'stdout': result.stdout if len(result.stdout) < 15000 else '[large HTML output; SHA-256 ' + __import__('hashlib').sha256(result.stdout.encode()).hexdigest() + '; bytes ' + str(len(result.stdout.encode())) + ']', 'stderr': result.stderr})
        print('PASS' if result.returncode == 0 else 'FAIL', ' '.join(args), flush=True)
    for group in ['line-1', 'line-2', 'line-3', 'line-4', 'shared']:
        selected = [r for r in results if group in r['command'] or (group == 'line-4' and 'test/scratch/typed-digest' in r['command'])]
        (ROOT / ('gathering/check-07-' + group + '.json')).write_text(json.dumps(selected, separators=(',', ':'))+'\n')
    return 0 if all(r['exitCode'] == 0 for r in results) else 1


if __name__ == '__main__':
    sys.exit(main())
