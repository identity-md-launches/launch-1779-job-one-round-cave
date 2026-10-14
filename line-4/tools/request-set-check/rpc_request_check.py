#!/usr/bin/env python3
"""Check captured eth_signTypedData_v4 envelopes offline; no RPC or signing."""
import argparse
import json
import sys

from request_compare import compare, MAX_REPORT_BYTES
from typed_digest import (TypedDataError, load_workspace_json, loads_bounded,
                          parse_hex, validate_tree)


def unpack(envelope):
    """Accept a strict provider request or JSON-RPC 2.0 request, never a batch."""
    validate_tree(envelope)
    if type(envelope) is not dict:
        raise TypedDataError('request must be an object, not a batch')
    keys = set(envelope)
    if keys == {'method', 'params'}:
        transport = 'provider'
    elif keys == {'jsonrpc', 'id', 'method', 'params'}:
        if envelope['jsonrpc'] != '2.0':
            raise TypedDataError('jsonrpc must be 2.0')
        if type(envelope['id']) not in (str, int):
            raise TypedDataError('id must be a string or integer (not null or boolean)')
        transport = 'jsonrpc'
    else:
        raise TypedDataError('expected method/params, optionally both jsonrpc/id; no extra fields')
    if envelope['method'] != 'eth_signTypedData_v4':
        raise TypedDataError('only eth_signTypedData_v4 is supported')
    params = envelope['params']
    if type(params) is not list or len(params) != 2:
        raise TypedDataError('params must be [public account address, typed-data JSON string]')
    account = '0x' + parse_hex(params[0], 20).hex()
    if type(params[1]) is not str:
        raise TypedDataError('second parameter must be a JSON string; objects are not accepted')
    data = loads_bounded(params[1].encode('utf-8'))
    return account, data, transport


def check(intended, client):
    """Intended envelope must be independently reviewed, including its account."""
    account_a, data_a, transport_a = unpack(intended)
    account_b, data_b, transport_b = unpack(client)
    result = compare(data_a, data_b)
    result['typedDataMatches'] = result.pop('accepted')
    result['accountMatches'] = account_a == account_b
    result['accepted'] = result['typedDataMatches'] and result['accountMatches']
    result['intendedAccount'] = account_a
    result['clientAccount'] = account_b
    result['transport'] = {'intended': transport_a, 'client': transport_b}
    result['ignoredMetadata'] = 'JSON-RPC id and transport wrapper are not signed or compared'
    result['accountBinding'] = 'compared separately; public account parameter is not part of the EIP-712 digest'
    if len(json.dumps(result, ensure_ascii=True, indent=2).encode()) > MAX_REPORT_BYTES:
        raise TypedDataError('envelope comparison exceeds report limit')
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('intended', help='independently reviewed intended envelope JSON beneath cwd')
    parser.add_argument('client', help='captured client envelope JSON beneath cwd')
    parser.add_argument('--summary', action='store_true')
    args = parser.parse_args(argv)
    try:
        result = check(load_workspace_json(args.intended), load_workspace_json(args.client))
        if args.summary:
            result.pop('differences')
        print(json.dumps(result, ensure_ascii=True, indent=2))
        return 0 if result['accepted'] else 1
    except (ValueError, OSError, RecursionError) as exc:
        print(f'rpc-request-check: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
