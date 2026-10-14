# Shared pieces

[RPC evidence bridge](rpc-evidence/README.md) combines line 1's capture format
and line 2's structural checker. It includes vendored standard-library code,
a real mainnet sample, an offline command and six regression tests. Copy its
folder into any workspace; no packages, network or cave records are needed for
validation. Capturing fresh evidence uses only public read RPC methods.

[Payment evidence bridge](payment-evidence/README.md) connects all four lines:
bounded RPC reads, structural contracts, settlement/net ZTO or IMD payment
verification, and offline typed-data commitments. It binds replay to an independently
supplied policy and includes real historical and fresh mainnet observations,
vendored standard-library code and 14 integration tests. Copy its folder to use it
without the cave or line folders.

Gathering 03 adds [payment commitment explanation](payment-evidence/explain.py):
replay the checked payment, inspect its EIP-712 field words and compare an exact
client request, locating mismatches by JSON Pointer. The trace is vendored from
Line 4 and connects to the existing four-line bridge. Twelve integration tests
and a fresh real ZTO payment exercise it entirely offline after capture.

Gathering 04 adds payment domain binding: see `payment-evidence/bind.py` and its
README for a single offline decision requiring payment policy, exact client
encoding, and independently supplied domain/type to all match. No signing or
new coin is needed.

Gathering 05 adds `payment-evidence/corroborate.py`: two provider transcripts
must independently meet the payment policy and agree, then their complete
content commitment must match the separately reviewed intended request and
exact client encoding. It shares the current agreement and request comparison
pieces, with 16 integration tests and a detached offline trial. ZTO supplies the
real evidence; no additional coin, package or wallet is required.

Gathering 06 adds `payment-evidence/revisit.py`: preserve paired-provider policy
across a payment recheck, require both sampled heads to advance without alerts,
then bind the new evidence to an independently reviewed captured request and
compare the client's public account as well as EIP-712 encoding. Invalid policies
have exact document/contract rule pointers. Includes unchanged vendored line
pieces, 14 integration tests and a detached offline demo using real historical
ZTO observations. It never dispatches a captured method or promotes a baseline.

Gathering 07 adds `payment-evidence/time_review.py`: check an independently chosen
payment policy with exact UTF-8 source/rule locations, then replay timestamp-bearing
ZTO/IMD evidence against explicit caller time and age budgets. Includes real
historical ZTO fixtures and 13 integration tests. A detached folder reproduces
both acceptance and stale-evidence rejection offline. It reviews one observation
and does not substitute for the paired-provider requirements of `revisit.py`.
