# Offline ordered EIP-712 request set checker

Compare a complete, ordered collection of captured `eth_signTypedData_v4`
requests with a separately reviewed intended collection. Catch missing or added
requests, duplicate review labels, reordering, changed public accounts and
changed typed-data encoding. Python standard library only; copy this entire
folder to use it independently offline. It reads JSON and prints a report.

One command from the repository root:

```sh
python3 -B line-4/tools/request-set-check/request_set_check.py line-4/tools/request-set-check/zto-set.json line-4/tools/request-set-check/zto-set.json --summary
```

Tried: exit **0**, `accepted: true`, one matched account and encoding, historical
ZTO digest `0xf33e2506e5c103f98dbfe3feb6d4b87d55f1fad4e423dbaa8462465ff4ab9774`.
Self-comparison demonstrates execution, not independent approval. Substitute
`line-4/tools/request-set-check/missing-set.json` as the second input to see
exit **1**, `accepted: false`, with `zto-receipt-review` listed as missing.

For real use, prepare the intended collection independently. Capture the client
requests separately and associate them with the reviewed labels in capture order.
Both inputs contain exactly one `requests` array. Every entry contains exactly
`reviewId` and `request`. `request` is the ancestor's strict provider envelope
(`method`, `params`) or complete JSON-RPC 2.0 envelope. The method must be
`eth_signTypedData_v4`, with exactly a public account address followed by a JSON
**string** of complete typed data. This collection is a review artifact, never
a JSON-RPC batch to dispatch.

Labels are case-sensitive, unique ASCII identifiers of 1–64 characters: start
with a letter or digit, then letters, digits, dots, underscores or hyphens.
The intended collection must contain 1–16 entries; the client may contain 0–16.
Acceptance requires identical label membership and order, plus every public
account and complete encoding matching. Repeated identical payloads with
different labels are allowed: labels identify review steps, not unique digests.
Missing and added entries are also fully validated; malformed unmatched input
is an error. JSON-RPC IDs and provider-versus-JSON-RPC wrapping are deliberately
ignored, but review order is mandatory. Equivalent address case and encoded
integer notation may match. Full reports retain ancestor JSON Pointer differences.

Exit **0**: complete match. Exit **1**: valid collections differ. Exit **2**:
invalid input, unsafe paths or exceeded bounds. Each file is at most 65,536
bytes, read as a no-follow regular file beneath cwd. Hidden paths, parent
traversal and symlinks are refused; POSIX directory descriptors are required.
The inherited strict parser rejects duplicate keys, floats, nonfinite values,
invalid Unicode, cycles, depth over 48 and node counts over 8,192. All inherited
encoding/trace bounds apply. The complete aggregate report is capped at
1,048,576 bytes **before** `--summary` removes detailed differences.

Tried 22 tests, acceptance and omission CLIs, and a detached folder copy with
no line siblings or network. Tests cover missing/extra/reordered/renamed entries,
duplicate IDs on either side, empty intended input, altered ZTO amount, account
mismatch despite equal digests, transport/case equivalence, malformed unmatched
requests, strict parsing, bounds, immutability and CLI error/rejection exits.

```sh
python3 -B -m unittest discover -s line-4/tools/request-set-check -v
```

The demo preserves the ancestor's historical real-ZTO payment-evidence request.
Its illustrative public account is the observed recipient, without a claim of
ownership, consent or an actual signing workflow. No fresh chain observation
is claimed. `provenance.json` hashes the four unchanged ancestor source copies
and source fixture. The encoder follows [EIP-712](https://eips.ethereum.org/EIPS/eip-712);
it and the comparison code are reused, not independent cryptographic engines.

Labels and order are caller assertions: they are not part of the signed digest
or authenticated by this tool. Relabeling identical payloads is undetectable.
It compares saved collections, not a live wallet stream or execution schedule.
A match establishes neither intended provenance, account ownership, consent,
payment, contract support nor replay protection. Nothing is signed, sent or
dispatched; no wallet, key, environment or network access occurs.

The accompanying mark means: Pepe checks every pebble and the order of their trail.
