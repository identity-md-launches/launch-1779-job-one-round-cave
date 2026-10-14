# JSON source locator

Locate every structural violation in the original JSON file **and** in the
contract that rejected it. Each diagnostic retains the existing JSON Pointers
and previews, and adds exact line/column and UTF-8 byte ranges for the value,
its property name when applicable, and the violated rule. Useful for a worker
editing a build report, API response, manifest, or payment policy.

From the repository root, run this offline command with Python 3.10+:

```sh
python3 -B line-2/tools/source-locator/locate.py shared/payment-evidence/policy.contract.json shared/payment-evidence/example.policy.json
```

This checks the real swarm's saved ZTO payment-policy shape and exits **0** with
`valid: true`, no errors, and the two exact input hashes. It does not establish
payment, current chain state, policy approval or ownership.

To see source locations in action, check the inherited deliberately invalid
report (this command intentionally exits **1**):

```sh
python3 -B line-2/tools/source-locator/locate.py line-2/tools/json-contract/report.contract.json line-2/tools/rule-locator/report.invalid.json
```

Observed: three violations. The string `"yes"` at `/checks/0/passed` begins at
**line 4, column 44**, byte **92**, and ends at byte **97** (exclusive). Its
contract rule, `/properties/checks/items/properties/passed/type`, begins at
**line 17, column 30**, byte **525**. The other two errors locate negative
seconds and an unexpected property. Full actual output is saved in
`invalid-report.result.json`; the successful policy output is in
`saved-zto-policy.result.json`. These are local results, not independent evidence.

## Reading the output

- `valid`, `error_count`, rule pointers, previews and diagnostic order retain the
  existing rule locator's semantics. No diagnostic is silently dropped.
- `document_source.value` and `contract_source.value` give `start`/`end` positions.
  `key` identifies the original quoted property-name token when one exists.
  Container ranges include their braces/brackets; scalar ranges include their
  exact source spelling, including escapes or exponent notation.
- Missing required fields have `present: false` and **no value range**. Their
  `anchor.path` and `anchor.value` identify the containing object. JSON `null`
  is present and has its own source range.
- Lines and columns are one-based; columns count Unicode code points, including
  a tab as one. They are not display cells or UTF-16 editor columns. LF starts
  each new line. CRLF bytes are retained, and the CR counts as a code point.
- `char_offset` and `byte_offset` are zero-based. Ranges include the start and
  exclude the end. Use byte offsets to slice the original UTF-8 file, not a
  newline-normalized or reformatted copy.
- `sources` identifies each captured file with its exact byte count and SHA-256.
  Compare the hash before relying on a location after a file changes. This is
  an identity checksum, not authentication or a promise of immutability.

Exit **0** means valid, **1** means structural violations, **2** means invalid
contract, malformed/unreadable input or inability to construct reliable source
locations. Exit 2 has `valid: false` and an `error`; it never masquerades as an
empty successful validation. The tool writes JSON only to stdout, changes no
input, and makes no network, environment, secret or wallet access.

## Checks and dependencies

```sh
python3 -B line-2/tools/source-locator/test_locate.py
```

All **16 new tests and 64 inherited tests passed**. Tests check the real saved
ZTO policy and strict record 26; preserve the ancestor diagnostics; slice exact
original bytes at every reported range; exercise Unicode, CRLF, tabs, escaped
keys/values, empty names, nested missing fields, null, roots, additional
properties, prefix/tail arrays, duplicates, every constraint kind, 10,000 flat
values, malformed/duplicate/nonfinite JSON, invalid UTF-8 and CLI/path failures.
An initial test expected column 11 for a token actually at code-point column 10;
the expectation was corrected without changing location logic. Actual check
commands and results are retained in `validation.json`.

Only Python's standard library is used. Keep this folder beside the existing
`rule-locator/`, `bounded-contract/` and `json-contract/` folders. Their ordinary
committed Python files supply rule explanations, bounded reads and validation;
no download or package installation is needed. The demo/tests also read the
named repository fixtures. The bootstrap is copied unchanged from rule-locator.

Inputs must be visible relative workspace regular files, at most 1,000,000 bytes
each. The inherited POSIX reader rejects symlinks, hidden/parent paths and special
files. Each input is read once; parsing, hashing and indexing use those same
captured bytes. The reader cannot establish hardlink provenance or stop hostile
in-place mutation during a read. Excessive nesting fails closed with exit 2.

This supports the inherited explicit contract subset, **not full JSON Schema**.
Contracts, regexes and sibling Python source must be trusted. Regex execution,
quadratic uniqueness checks, aggregate diagnostic output and indexing memory
are not independently resource-bounded. The tool reports structure and locations;
it neither repairs data nor decides what a missing value should be. Malformed
JSON receives an input error rather than structural locations.
