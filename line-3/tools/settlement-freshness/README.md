# Settlement freshness

Check a finalized Ethereum payment against an explicit time budget before relying
on it. A transaction can meet its payment and finality policy while its RPC view
is old. This standard-library Python tool adds separate maximum ages for the
sampled latest and finalized blocks, plus a caller-chosen future-clock tolerance.
It uses real ZTO first; IMD policies are also supported.

One command from the repository root works offline, without packages:

```sh
python3 -B line-3/tools/settlement-freshness/freshness.py --demo
```

It returns exit **0**, `accepted: true`, `state: within_time_budget`. This demo
evaluates a real saved observation **at its historical trial time**, never today's
freshness. Its recipient and minimum came from an ancestor's observed ZTO receipt,
not an independently issued invoice.

## What happened when tried

A read-only mainnet trial sampled head **26193067**, timestamp **1792008911**,
and finalized head **26192994**, timestamp **1792008023**. At caller time
**1792008919**, their ages were **8 seconds** and **896 seconds**. Both passed the
chosen **120-second head / 1,200-second finalized** limits and **30-second future
skew**. Collection took one second. The same finalized ZTO payment remained valid:

- Transaction: `0xc4ca304c305cae326cab066639ab2156412eee7f5f774b41a2a136369f817ef7`
- Recipient: `0x2d30e495a15f2657d57c3e2caa08b06415c26cbf`
- Net receipt: **166357571280020680094504 raw ZTO**
- Token: `0xd782bdea4ef02a0bd391eb9089470c8080f0a68e`

The actual timestamp-bearing transcript is [live-evidence.json](live-evidence.json).
[trial.json](trial.json) records the time arguments and result; the demo recomputes
the decision rather than trusting that result. Public source:
[Ethereum Publicnode](https://ethereum-rpc.publicnode.com), accessed through the
assignment's supplied Ethereum routing. Source labels are not authenticated.

Re-evaluating that same observation 1,201 seconds later rejects it with
`head_too_old` and `finalized_too_old`, even though its historical payment check
still passes. Exact age boundaries pass; one second beyond them rejects.

## Supply your own policy and time

Outside `--demo`, the caller must supply all three of `--as-of`, `--max-head-age`
and `--max-finalized-age`, and a separate `--policy` file. The tool never reads a
saved timestamp as the evaluation clock and never reads the system clock itself.
Use trusted Unix seconds appropriate to your decision. Future skew defaults to
zero. A live run evaluates against the supplied time even if collection takes
time; callers should re-evaluate its saved sample at the decision time when that
delay matters. There is no claim about validity after the evaluation time.

This explicit historical replay is equivalent to the demo:

```sh
python3 -B line-3/tools/settlement-freshness/freshness.py --replay line-3/tools/settlement-freshness/live-evidence.json --policy line-3/tools/settlement-freshness/observed-policy.json --as-of 1792008919 --max-head-age 120 --max-finalized-age 1200 --future-skew 30
```

For a live observation, replace `--replay FILE` with `--live`, use your current
trusted time, and supply your independently chosen payment policy. Do not reuse
the historical time to claim current acceptance. `--rpc https://eth.drpc.org`
selects the other documented endpoint. Default is Publicnode. There is no retry,
fallback, timer, signing, sending, deployment, or file-writing CLI behavior.
Live output includes `sample` only when complete evidence can be replayed.

The policy is a JSON object with exactly `tx`, `recipient`, `minimum_raw`,
`token`, `confirmations`, and `finalized`; see
[observed-policy.json](observed-policy.json) for the real historical example.
Amounts are positive decimal strings in base units. The token is `ZTO` or `IMD`,
confirmations are an integer 1..1,000,000, and this tool requires `finalized: true`.
The evidence must match the independently selected policy, after address/hash
case normalization. The example is illustrative, not a recipient recommendation.

Age limits are integer seconds in 1..604800; future skew is 0..3600. `as-of` is
an integer Unix second in 1..253402300799. These are input bounds, not recommended
settlement settings. Choose age/finality requirements for your actual use.

## Checks and decisions

Every block observation must carry a valid timestamp bound to its number and
hash. Repeated observations of the same height/hash must agree exactly. One hash
cannot identify two headers, and timestamps must increase with observed heights.
The sampled head and finalized anchor ages are compared independently. This
measures the age of the observed chain view, **not the age of the payment**: an
old finalized transfer can be checked against a recent head.

The inherited replayer checks exact JSON request types, request order, complete
consumption, execution, canonical rereads, confirmations, finality, and full
selected-token Transfer accounting. Older timestamp-free witness transcripts
are refused; timestamps are never inferred or filled in. Malformed or conflicting
evidence fails closed. There is no saved `accepted` flag that can override checks.

| Result | Meaning | Exit |
| --- | --- | --- |
| `within_time_budget` | Payment and both explicit time bounds pass | 0 |
| `review_required` | Payment failed or an anchor is absent, too old, or too far in the future | 1 |
| `input_error` | Invalid policy/time, mismatch, unsafe file, or inconsistent saved evidence | 2 |
| `provider_error` | Live evidence could not be obtained and fully replayed | 2 |

Run the offline regression suite:

```sh
python3 -B -m unittest discover -s line-3/tools/settlement-freshness -p 'test_*.py' -v
```

All **21 tests passed**, including the real ZTO observation, independent age
limits, exact/future boundaries, stale evidence despite a successful payment,
changed/missing/malformed timestamps, timestamp order, changed header identity,
policy mismatch, payment shortfall, revert, missing receipt, transcript tampering,
invalid input before transport construction, live/replay agreement, provider
failure, disabled proxy discovery and CLI requirements. Mutated observations
exist only as rejection tests, never as fabricated live evidence.

## Portability and limits

Copy this folder with its sibling `payment-recheck`, `provider-agreement`,
`payment-witness`, and `settlement-check` folders. Python 3.9+ and POSIX safe-open
support suffice; no third-party dependency or network is needed for replay.
All file inputs use the inherited 90 KB, workspace-relative, no-symlink,
regular-file reader with duplicate-key/nonfinite JSON rejection. RPC calls use
an explicit User-Agent, bounded replies and timeouts, no redirects, no environment
or proxy discovery, and only allowlisted reads. The tool prints JSON to stdout.

Provider timestamps and the caller's clock are trusted inputs, not authenticated
time. Consistently forged headers and receipts can pass. This is not a consensus
or receipt proof, a freshness oracle, independent-provider agreement, proof of
block ancestry, an invoice registry, or a payment ledger. A provider can lag
within the chosen age limit. Reorgs can occur later. An incorrect evaluation time
can accept stale evidence or reject current evidence; historical replay cannot
establish today's canonicality. These limits are reported in every result.
