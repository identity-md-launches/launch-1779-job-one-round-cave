#!/usr/bin/env python3
"""Turn a verified ZTO snapshot into one self-contained, offline HTML report."""
import argparse
import hashlib
from html import escape
import json
from pathlib import Path
import runpy
import sys

P = runpy.run_path(str(Path(__file__).resolve().parents[1] /
                      'hash-pinned-zto' / 'pinned.py'))
MAX_BYTES = 100000


def render(raw):
    """Validate original JSON bytes before rendering; no network or scripts."""
    if not isinstance(raw, bytes) or len(raw) > MAX_BYTES:
        raise ValueError('input must be bytes, at most 100000 bytes')
    bundle = P['B']['parse_json'](raw)
    info = P['validate_bundle'](bundle)
    fields = [
        ('Network', 'Ethereum mainnet (chain ID 1)'),
        ('Token', 'ZTO'),
        ('Contract', info['zto_address']),
        ('Total supply (ZTO)', info['total_supply_tokens']),
        ('Total supply (raw integer)', info['total_supply_raw']),
        ('Decimals observed', info['decimals']),
        ('Finalized block observed', info['block_number']),
        ('Block hash', info['block_hash']),
        ('Provider label', bundle['rpc_url']),
        ('Capture timestamp (untrusted metadata)', bundle['captured_at_utc']),
        ('Original file SHA-256', hashlib.sha256(raw).hexdigest()),
        ('Canonical bundle SHA-256', P['digest'](bundle)),
    ]
    rows = ''.join('<dt>' + escape(k) + '</dt><dd>' + escape(str(v)) + '</dd>'
                   for k, v in fields)
    reads = []
    labels = ['Observe chain', 'Select finalized anchor', 'Read ZTO totalSupply()',
              'Read ZTO decimals()', 'Recheck anchor height']
    for label, read in zip(labels, bundle['reads']):
        # Content stays exclusively in escaped text nodes, including provider extras.
        request = {key: read[key] for key in ('method', 'params', 'content_type', 'response_sha256')}
        text = json.dumps(request, indent=2, sort_keys=True, ensure_ascii=True,
                          allow_nan=False)
        reads.append('<details><summary>' + escape(label) + '</summary><pre>' +
                     escape(text) + '</pre></details>')
    transcript = json.dumps(bundle, sort_keys=True, separators=(',', ':'),
                            ensure_ascii=True, allow_nan=False)
    page = '''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<title>ZTO snapshot report</title>
<style>body{font:17px/1.55 system-ui,sans-serif;max-width:920px;margin:auto;padding:24px;color:#202b26;background:#faf8f2}h1{line-height:1.2}dt{font-weight:bold;margin-top:14px}dd{margin:0;overflow-wrap:anywhere;font-family:monospace}aside{border-left:5px solid #975125;padding:8px 18px;background:#f0e6d5}summary{cursor:pointer;padding:12px 0;font-weight:bold}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:13px;padding:12px;background:#eaece6}footer{margin-top:24px;font-size:14px}@media print{body{padding:0}details{break-inside:avoid}}</style>
</head><body><main><h1>ZTO snapshot report</h1>
<p>Saved Ethereum provider observation. The generating tool validated the complete
five-read transcript and its checksums before producing this page.</p>
<aside><strong>Observation, not proof.</strong> This historical report does not
establish current supply, freshness, provider authenticity, consensus, ownership,
payment or market price. A forged and consistently resealed transcript can pass.
The source label and timestamp are not authenticated. Opening this page does not
revalidate it or contact Ethereum. Anyone can edit an HTML report.</aside>
<h2>Observed values</h2><dl>''' + rows + '''</dl>
<h2>What was checked</h2><p>Mainnet chain ID; the finalized block selection;
the real ZTO contract and exact supply/decimals selectors; both state calls pinned
to the same block hash with requireCanonical=true; an unchanged anchor on reread;
successful RPC envelopes, request/response commitments and exact integer amounts.</p>
<h2>Inspect the five requests</h2><p>Each request below includes its response
checksum. Full responses appear once in the complete transcript below.</p>''' + ''.join(reads) + '''
<h2>Portable evidence</h2><p>Keep the original JSON file alongside this report for
independent replay. The original-file hash commits to its exact bytes, including
whitespace. The canonical-bundle hash commits to parsed JSON content. Below is
the complete equivalent JSON transcript; copying its text preserves content,
but changes the original-file hash if serialization differs.</p>
<details><summary>Complete JSON transcript</summary><pre id="transcript">''' + escape(transcript) + '''</pre></details>
</main><footer>Static offline document. No scripts, remote assets, forms, wallet
connections or transactions.</footer></body></html>
'''
    result = page.encode('utf-8')
    if len(result) > MAX_BYTES:
        raise ValueError('rendered report exceeds 100000 bytes; no report written')
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('snapshot', help='hash-pinned ZTO JSON, relative workspace path')
    parser.add_argument('--output', help='NEW relative workspace HTML path (else stdout)')
    args = parser.parse_args(argv)
    try:
        if args.output:
            P['SAFE']['parts'](args.output)
        raw = P['SAFE']['read_bytes'](args.snapshot, MAX_BYTES)
        rendered = render(raw)
        if args.output:
            P['SAFE']['write_bytes'](args.output, rendered, MAX_BYTES)
            print(json.dumps({'output': args.output, 'bytes': len(rendered),
                              'sha256': hashlib.sha256(rendered).hexdigest()}))
        else:
            sys.stdout.write(rendered.decode('utf-8'))
        return 0
    except (ValueError, OSError, RecursionError, P['B']['SnapshotError']) as exc:
        print('snapshot-report: ' + str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
