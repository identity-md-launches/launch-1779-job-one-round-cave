# Offline ZTO snapshot report

Turn a saved hash-pinned ZTO observation into one HTML file that a worker can
read in a browser without Python, a network connection, or a wallet. The exporter
uses only Python's standard library. It verifies all five requests/responses
before displaying exact supply, decimals, finalized block identity, source label,
timestamp and two explicitly distinguished SHA-256 commitments. Expandable
sections expose each request and the complete JSON evidence.

One command from the repository root shows it working, entirely offline:

```sh
python3 -B line-1/tools/snapshot-report/report.py line-1/tools/compare-zto-snapshots/live-zto.json
```

This prints the self-contained HTML. Open the included `example.html` to inspect
the same result directly in a browser. To save your own report without replacing
any existing file:

```sh
python3 -B line-1/tools/snapshot-report/report.py line-1/tools/compare-zto-snapshots/live-zto.json --output line-1/tools/snapshot-report/my-report.html
```

Tried against the predecessor's **real saved public Ethereum observation** at
block 26192611: exit 0, 52,563-byte HTML, 18 decimals and exactly
1,000,000,000.000000000000000000 ZTO total supply. This step did not fetch a new
chain observation. Its historical timestamp is displayed as untrusted metadata.
The complete embedded transcript parses back to the original JSON content and
passes the inherited verifier. Ten new offline tests passed:

```sh
python3 -B line-1/tools/snapshot-report/test_report.py
```

Tests exercise real evidence round-trip, tampering, a resealed wrong contract,
duplicate keys, hostile HTML in provider fields, exact-byte versus content
hashes, size expansion, determinism, no-clobber publication, symlinks, rejected
paths and invalid-input failure without an output file. Test mutations are
synthetic; none are presented as chain observations. The first local run found
that repeating full responses exceeded the output budget; requests now show
their response checksum and the complete transcript appears only once.

Input and output are bounded to 100,000 bytes each. HTML expansion may make an
otherwise valid input too large; it is rejected without writing partial output.
Input paths must be visible, relative workspace paths. Output uses the inherited
POSIX no-follow, atomic no-clobber writer. Existing targets are refused. Exit 0
means generation succeeded; invalid input or file errors return 1 on stderr.
Keep the sibling `hash-pinned-zto`, `bounded-rpc-snapshot` and
`safe-snapshot-files` folders: these ordinary local Python files are dependencies.
The resulting HTML needs none of those folders and loads no external assets.

All evidence is escaped into text nodes; no scripts, links, forms or wallet
features are emitted. A restrictive content security policy adds defense in
depth. The report uses native browser details elements; no browser automation or
cross-browser visual certification was performed.

Limits: a validated provider observation is not an Ethereum state proof. A forged
and consistently resealed transcript can pass. Neither checksums nor source
labels establish authenticity or freshness. An HTML file can itself be edited;
opening it does not rerun verification. Keep and replay the original JSON for
independent checks. Copying embedded JSON preserves its content, not its original
whitespace or exact-file hash. This reports ZTO supply, not balances, prices,
payments or investment value.
