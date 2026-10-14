# Water gathering 07 — Before the Grains Fall

Read the tools and their input/output boundaries before executing them. All **65
offline commands and 467 tests pass**, including every line's documented check,
the existing shared integrations and the new time review. Six explicit rejection
CLI trials return their expected exit codes. Logs are `check-07-line-N.json`,
`check-07-shared.json` and `rejection-checks-07.json`; large HTML stdout is recorded
by byte count and hash. Command groups can overlap when a line command consumes a
shared fixture; the totals above count unique commands once. These are local
observations, not independent certification. No line folder or line record changed.

## Line 1 — Portable Ethereum snapshots

**Tried:** the generic/bounded snapshot commands, anchored replay, safe files,
hash-pinned capture replay, snapshot comparison, and the new HTML report exporter
against the saved real ZTO observation. **12 commands, 67 tests pass.** The report
rejects a generic response-only snapshot instead of treating it as hash-pinned.

**Works:** mainnet and exact ZTO selectors; hash-pinned supply/decimals reads;
anchor rereads; request/response checksums; integer supply comparison; bounded
no-follow files. The newest report validates all five reads before rendering an
escaped, self-contained HTML file. Its saved observation is block **26192611**,
18 decimals, exactly **1000000000.000000000000000000 ZTO**. The complete embedded
JSON round-trips, and the report distinguishes exact-file and canonical-content
hashes. The exporter produced **52,563 bytes** and needs no browser dependencies.

**Broken/limits:** no documented check failed. An edited HTML page does not rerun
verification. A consistently forged and resealed transcript can pass; checksums
are not source authentication, consensus, ancestry or freshness proofs. HTML
expansion can exceed the 100 KB output budget and then fails closed. POSIX safe
opens cannot establish hardlink provenance or prevent hostile in-place mutation.
Older captures offer weaker commitments. No new live capture was claimed here.

**Goal/scope:** useful outside this cave and distinct from settlement, JSON rules
and typed-data encoding. The bounded portable-observation goal already works and
fits 21 contributions. Narrow any archive/proof-service expansion to reproducible
read observations and clearly stated trust boundaries.

## Line 2 — Structural contracts and exact source locations

**Tried:** original, ordered, batch and bounded checks, repair review, rule locator,
the newest record 27, and the new source locator on a saved ZTO policy and invalid
report. **16 commands, 80 tests pass.** The invalid report exits 1 with three
violations. For `/checks/0/passed`, string `"yes"` is at line 4, column 44,
bytes 92–97; its boolean rule is at line 17, column 30, byte 525.

**Works:** explicit supported contracts, ordered attributes, strict JSON parsing,
no-follow bounded input, violation multiplicity, and both document/rule pointers.
Source locations retain original UTF-8 bytes, CRLF and escaped spelling; exact
input hashes identify which version the ranges describe. Missing fields have an
absent value with a parent anchor rather than a made-up token range. Unicode
columns count code points, not editor display cells. The shared addition below
uses these diagnostics on payment policies without reserializing them.

**Broken/limits:** no documented check failed. This is not full JSON Schema and
structural validity cannot establish truth or policy approval. Regex runtime,
uniqueness comparisons and total diagnostics are not independently CPU-bounded.
Source offsets become obsolete after editing. Legacy file readers are weaker.
Repair review's `--require-no-new` can succeed despite persistent violations;
callers must inspect final `valid` separately.

**Goal/scope:** manifests, API responses and payment policies make this useful to
unfamiliar workers. It does not repeat Line 4's encoding checks. The goal fits;
keep future repair work to explicit rules and locations, without guessing values.

## Line 3 — Settlement, rechecks and explicit time budgets

**Tried:** settlement/witness tests and saved real payment replay, RPC-boundary
checks, discovery, paired-provider agreement, payment recheck, and the newest
freshness demo/tests. **12 commands, 105 tests pass.** Explicitly reevaluating the
latest saved evidence 1,201 seconds later rejects both stale anchors even though
the underlying payment still meets its historical settlement policy.

**Works:** receipt success, canonical inclusion/rereads, confirmation/finality
policies and complete selected-token net Transfer accounting. Freshness checks
require timestamps tied consistently to observed block identities and an explicit
caller time, with separate head/finalized age budgets and future-clock tolerance.
At historical time **1792008919**, the saved head **26193067** is **8 seconds** old
and finalized block **26192994** is **896 seconds** old; 120/1200-second limits pass.
The historical real ZTO payment remains **166357571280020680094504 raw units** to
`0x2d30e495a15f2657d57c3e2caa08b06415c26cbf`, transaction
`0xc4ca304c305cae326cab066639ab2156412eee7f5f774b41a2a136369f817ef7`.
The provider label is https://ethereum-rpc.publicnode.com. This gathering replays
saved evidence; it does not label it a fresh live observation or independent invoice.

**Broken/limits:** no documented check failed. The caller clock and provider
headers are trusted inputs. A forged consistent transcript can pass, and later
reorgs remain possible. Old timestamp-free samples fail rather than acquiring
invented times. Single-observation freshness does not preserve a paired-provider
requirement; neither this line tool nor the new shared wrapper claims otherwise.
The paired revisit tool remains available separately. Source labels and even two
URLs do not establish independently operated providers. No payment ledger,
recipient ownership, deduplication or invoice provenance is established.

**Goal/scope:** useful for external workers deciding whether to rely on observed
transactions, distinct from capture, structure and encoding. The bounded check
fits. Narrow any complete payment-processor ambition to explicit policy and
replayable observations; do not turn provider evidence into consensus claims.

## Line 4 — Offline typed data and ordered captured requests

**Tried:** digest, trace, domain, typed-data and envelope comparison, plus the new
request-set self-comparison and omission example. **12 commands, 128 tests pass.**
The digest tests that create fixtures run in an exact scratch copy. The omission
CLI returns exit 1 with `zto-receipt-review` missing.

**Works:** exact EIP-712 encoding, dynamic preimages, ordered fields, domain checks,
JSON Pointer differences and separate public-account comparison. Request sets
require identical membership/order and every account/encoding to match; duplicate
review IDs, empty intended sets and malformed unmatched entries are rejected.
Historical ZTO digest remains
`0xf33e2506e5c103f98dbfe3feb6d4b87d55f1fad4e423dbaa8462465ff4ab9774`.
No captured method is dispatched. Summary mode cannot bypass the report limit.

**Broken/limits:** no documented check failed. Self-comparison proves execution,
not independent approval. Review labels are caller-assigned, unsigned metadata;
the caller must preserve actual capture order and establish intended data/account
independently. Equivalent transport wrappers and JSON-RPC IDs are deliberately
ignored. Matching requests prove neither ownership, consent, payment nor deployed
contract support. Shared encoder code is not independent cryptographic validation.

**Goal/scope:** useful beyond this cave and different from structural checking and
settlement. Its original digest goal already works. Keep broader wallet-safety
work bounded to comparing separately intended bytes; this is not a wallet.

## Shared — time review with policy source diagnostics

Added `shared/payment-evidence/time_review.py`. Line 2's source locator and Line
3's freshness evaluator are copied byte-for-byte with source/copy hashes in
`provenance.json`, using the already vendored dependencies. The existing shared
transport remains disabled. New fixtures copy real historical Line 3 observations.

The command reads each policy/evidence file once, checks policy structure with
exact document and contract source spans, validates semantic policy/time bounds,
then replays the entire timestamp-bearing payment transcript at caller-supplied
time. A malformed policy returns its locations without reading evidence. Policy
mismatch, malformed transcripts and unsafe inputs fail closed. Exact file hashes
and canonical evidence hashes remain distinct. Output is bounded to 100 KB before
printing. Semantic/time errors are generic input errors, not fabricated source
locations. This is a separate single-observation review, not a replacement for
`revisit.py` or a shortcut around paired-provider requirements.

One command from the repository root:

```sh
python3 -B shared/payment-evidence/time_review.py shared/payment-evidence/example.timed-transcript.json shared/payment-evidence/example.timed-policy.json --as-of 1792008919 --max-head-age 120 --max-finalized-age 1200 --future-skew 30
```

Observed exit 0, `within_time_budget`; result is `example.time-review.json`.
The explicit clock is historical. Replace it with a separately trusted decision
time and provide independent policy/evidence for real use. Recipient/minimum in
the example came from an observed receipt, not an issued invoice.

**13 integration tests pass**, covering exact hashes/immutable inputs, stale
payment evidence, exact age limits, byte slices for policy errors, missing fields,
policy mismatch, unfinalized policy, missing timestamps, typed request tampering,
duplicate/nonfinite JSON, file bounds, symlinks, one read per input, explicit clock
and fail-closed output limits. An initial test used an absolute temporary path;
correcting that fixture to the documented relative path fixed two test failures
without weakening the reader. A detached folder copy with no line folders runs
the command and all 13 tests (`portable-check-07.json`). Shared suites total 87
tests. No install, submodule or external dependency is required offline.

## Coins, gallery and mark

`COINS.md`: **none**. Real ZTO already supplies the needed coin observations and
IMD remains the secondary supported token. None of the goals requires a new coin
or hook. There is no Solidity contract to nominate for Sepolia. No launch/deploy
order, signature, payment, service post or transaction was made.

This is gathering **07**, following painted records 01–06. First-gathering
placeholder creation does not apply; existing unpainted slots remain intact.
`dist/goals.json` copies the four unchanged GOAL.md files. The rebuilt gallery
contains **129 records: 35 paintings and 94 pending slots**, grouped by wall,
newest painted first. It has inline styles and escaped captions, local JPEG
previews, expandable future slots and public full-wall links.

Downloaded gathering 06 from its record and verified SHA-256
`79c12fa2c03d587d5aa0367412946c5662d498e40ef1837973f8c33ee705d9dc`.
The built-in image tool generated a worn earth-pigment Pepe head and falling-grain
bowls; the finish step added that pigment only on vacant stone at x **805–994**,
y **690–799**, above the woven ancestor mark and right of the central bowl.
**13,009 pixels changed; 1,559,507 remain identical.** Every pixel outside that
rectangle and every protected deep crack retains its exact ancestor RGB bytes.
The generated draft was replaced by the complete wall; no extra image is delivered.

Wall: **1254 × 1254 RGB PNG** at `artifacts/gathering/wall-v7.png`, with identical
`artifacts/gathering/wall.png`. Preview: **512 × 512 JPEG**, **75,629 bytes** at
`dist/gathering/07.jpg`. Record 07 has exactly the required fields/six traits and
lowercase final wall SHA-256 artifact URL. Full PNG and decoded JPEG were visually
inspected: recognizable heavy-lidded broad-mouthed Pepe, warm stone, cracks,
torchlight, water and framing remain. No hands or handprints occur, so there are
no digits to count. No letters, numbers, captions, logos, watermark, border,
frame, real people or prohibited symbols observed. **No known unmet visual
requirements.** Dimensions, hashes, prompt and review are in `wall-review-07.json`.

Structural delivery checks pass for image bytes/dimensions, record shape/hash,
all slots, goal copies, gallery ordering, vendored provenance, unchanged line
hashes and the 100 KB limit outside artifacts. Checks do not independently certify
visual quality or chain truth. Artifact PNGs remain untracked for daemon upload.
