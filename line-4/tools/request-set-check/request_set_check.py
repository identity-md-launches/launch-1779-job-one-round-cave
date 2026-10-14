#!/usr/bin/env python3
"""Compare an ordered review collection of captured EIP-712 requests offline."""
import argparse
import json
import re
import sys

from rpc_request_check import check
from typed_digest import TypedDataError, load_workspace_json, validate_tree

MAX_REQUESTS = 16
MAX_REPORT_BYTES = 1_048_576
REVIEW_ID = re.compile(r'[A-Za-z0-9][A-Za-z0-9._-]{0,63}\Z')


def collection(value, intended=False):
    validate_tree(value)
    if type(value) is not dict or set(value) != {'requests'}:
        raise TypedDataError('collection must contain exactly requests')
    entries = value['requests']
    if type(entries) is not list or len(entries) > MAX_REQUESTS:
        raise TypedDataError('requests must be a list of at most 16 entries')
    if intended and not entries:
        raise TypedDataError('intended collection must not be empty')
    ids, requests = [], {}
    for entry in entries:
        if type(entry) is not dict or set(entry) != {'reviewId', 'request'}:
            raise TypedDataError('entry must contain exactly reviewId and request')
        key = entry['reviewId']
        if type(key) is not str or not REVIEW_ID.fullmatch(key):
            raise TypedDataError('reviewId must be 1-64 ASCII letters/digits/._-, starting with a letter/digit')
        if key in requests:
            raise TypedDataError('duplicate reviewId: ' + key)
        ids.append(key)
        requests[key] = entry['request']
    return ids, requests


def bounded(report):
    if len(json.dumps(report, ensure_ascii=True, indent=2).encode('utf-8')) > MAX_REPORT_BYTES:
        raise TypedDataError('request set exceeds 1048576-byte report limit')


def compare_set(intended, client):
    """Require complete membership, exact review order and every account/encoding."""
    left_ids, left = collection(intended, intended=True)
    right_ids, right = collection(client)
    missing = [key for key in left_ids if key not in right]
    added = [key for key in right_ids if key not in left]
    report = {
        'version': 1, 'accepted': False,
        'intendedOrder': left_ids, 'clientOrder': right_ids,
        'membershipMatches': not missing and not added,
        'orderMatches': left_ids == right_ids,
        'missing': missing, 'added': added, 'items': [],
        'reviewIds': 'caller-assigned labels, not signed or authenticated',
        'ignoredMetadata': 'JSON-RPC id and provider/JSON-RPC wrapper; review order is required',
        'intendedSource': 'caller-supplied; requires independent review',
    }
    # Validate unmatched entries too: an added malformed request is an input
    # error, not a valid mismatch. No client request is ever dispatched.
    for key in missing:
        check(left[key], left[key])
    for key in added:
        check(right[key], right[key])
    all_match = True
    for key in left_ids:
        if key not in right:
            continue
        result = check(left[key], right[key])
        all_match = all_match and result['accepted']
        report['items'].append({'reviewId': key, **result})
        bounded(report)
    report['accepted'] = report['membershipMatches'] and report['orderMatches'] and all_match
    bounded(report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('intended', help='independently reviewed collection beneath cwd')
    parser.add_argument('client', help='separately captured collection beneath cwd')
    parser.add_argument('--summary', action='store_true')
    args = parser.parse_args(argv)
    try:
        report = compare_set(load_workspace_json(args.intended), load_workspace_json(args.client))
        if args.summary:
            for item in report['items']:
                item.pop('differences')
        print(json.dumps(report, ensure_ascii=True, indent=2))
        return 0 if report['accepted'] else 1
    except (ValueError, OSError, RecursionError) as exc:
        print('request-set-check: ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
