#!/usr/bin/env python3
"""Compare an intended EIP-712 request with client bytes, offline; never sign."""
import argparse
import json
import sys

from typed_digest import TypedDataError, load_workspace_json
from typed_trace import explain

MAX_REPORT_BYTES = 1_048_576


def encoding_node(node):
    """Keep commitment-relevant bytes, excluding presentation of atomic values.

    Preimages distinguish dynamic inputs even in the event of a hash collision.
    Type encodings preserve field/dependency order, including empty arrays.
    """
    keys = ('type', 'kind', 'word', 'typeEncoding', 'preimage')
    return {key: node[key] for key in keys if key in node}


def compare(intended, client):
    """Pure comparison. The caller, not this tool, establishes intended provenance."""
    left, right = explain(intended), explain(client)
    a = {node['path']: encoding_node(node) for node in left['nodes']}
    b = {node['path']: encoding_node(node) for node in right['nodes']}
    differences = []
    if left['primaryType'] != right['primaryType']:
        differences.append({'path': '/primaryType', 'reason': 'primary type differs',
                            'intended': left['primaryType'], 'client': right['primaryType']})
    # Ancestor nodes are reported too: their differing preimages explain which
    # containing struct/array changed. No differences are silently truncated.
    for path in sorted(a.keys() | b.keys()):
        if path not in a:
            reason = 'client encoding node added'
        elif path not in b:
            reason = 'intended encoding node missing'
        elif a[path] != b[path]:
            reason = 'encoded type or bytes differ'
        else:
            continue
        differences.append({'path': path, 'reason': reason,
                            'intended': a.get(path), 'client': b.get(path)})
    digest_matches = left['digest'] == right['digest']
    result = {
        'accepted': digest_matches and not differences,
        'digestMatches': digest_matches,
        'encodingMatches': not differences,
        'intended': {key: left[key] for key in
                     ('primaryType', 'domainSeparator', 'messageHash', 'digest')},
        'client': {key: right[key] for key in
                   ('primaryType', 'domainSeparator', 'messageHash', 'digest')},
        'differenceCount': len(differences), 'differences': differences,
        'intendedSource': 'caller-supplied; not authenticated by this tool',
    }
    if len(json.dumps(result, ensure_ascii=True, indent=2).encode()) > MAX_REPORT_BYTES:
        raise TypedDataError('comparison exceeds 1048576-byte report limit')
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('intended', help='independently prepared intended request JSON beneath cwd')
    parser.add_argument('client', help='client request JSON beneath cwd')
    parser.add_argument('--summary', action='store_true', help='hashes and difference count only')
    args = parser.parse_args(argv)
    try:
        result = compare(load_workspace_json(args.intended), load_workspace_json(args.client))
        if args.summary:
            result = {k: v for k, v in result.items() if k != 'differences'}
        print(json.dumps(result, ensure_ascii=True, indent=2))
        return 0 if result['accepted'] else 1
    except (ValueError, OSError, RecursionError) as exc:
        print(f'request-compare: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
