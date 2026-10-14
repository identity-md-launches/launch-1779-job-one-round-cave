# Line 3 — Stone Witness

The first working piece is [settlement-check](tools/settlement-check/README.md): a read-only Ethereum transaction settlement checker, demonstrated on a real ZTO transfer. The one-line goal is in GOAL.md; it is distinct from the Water, Base, and Moss goals read at the start of this round.

## Wall result and review

| Output | Dimensions | Format |
| --- | --- | --- |
| `artifacts/line-3/wall.png` | 1254 × 1254 | RGB PNG |
| `dist/line-3/01.jpg` | 512 × 512 | RGB JPEG |

Pepe checks a chain of stones before trusting the crossing. The installed image tool generated a worn charcoal and ochre pigment design on white. Only its pigment pixels were multiplied onto the original bare Water cave; the original background dimensions, framing, cracks, stone texture, and torchlight were retained. Every pixel outside the pigment rectangle was checked against the input and remained identical. No previous line-3 mark existed.

Chosen review step: opened and visually inspected the final full wall. Pepe has the characteristic wide mouth and heavy-lidded eyes. The palette uses charcoal, red ochre, and yellow ochre over bare stone. No letters, numbers, captions, logos, borders, political symbols, or modern objects appear. His hands are hidden under his cloak; there are zero visible hands or handprints to miscount. The marks remain uneven and worn. Unmet visual requirements: none observed in this review. This is a local visual review, not an independent certification.

The image-tool prompt requested a primitive burnt-stick Pepe crouching beside three linked stones, earth pigments only, all hands hidden, no text, and a plain white background for compositing. Image processing was a local build step only; the delivered Python tool needs no third-party dependency.

## Addition 22 — The Receiving Bowl

[payment-witness](tools/payment-witness/README.md) adds recipient and net raw ZTO
amount verification to the unchanged settlement policy. It includes a real
PoolManager-to-recipient ZTO receipt and canonical anchors that can be replayed
offline. Its README gives a single command, live usage, observed results and
the evidence limits. Line 3's goal remains unchanged.

The whole updated wall is saved to `artifacts/line-3/wall-v2.png` (named output)
and `artifacts/line-3/wall.png` (wall continuation), both identical 1254 × 1254
RGB PNGs. `dist/line-3/22.jpg` is a 512 × 512 RGB JPEG, under 100 KB. Record 22
uses the finished PNG's SHA-256. Existing records 01–21 remain unchanged.

The added bowl holds received pebbles: Pepe counts what reaches the bowl before
trusting a payment. A worn pigment addition occupies only x=709–1061,
y=350–587. All other pixels, the existing Pepe and the three-stone chain are
unchanged. Rock, cracks, framing, dimensions and light remain inherited.
The chosen review step was opening and visually inspecting the complete final
wall after compositing. Pepe retains his wide mouth and heavy-lidded eyes;
the new mark uses red/yellow ochre and charcoal, flattened rather than shaded
as a rendered object. No hands or handprints are added; the ancestor's hands
are hidden, so there are zero visible hands whose digits need counting. No
letters, numbers, captions, signatures, logos, frames, real people or prohibited
symbols were observed. No unmet visual requirements were observed. This is a
local review, not independent visual certification. Machine-readable dimensions,
formats and preservation results are in `wall-review-22.json`.

The installed assignment image tool (`mcp__image__generate`) was used under the
imagegen workflow. Its final prompt requested a single sparse prehistoric bowl
of ochre pebbles on pure white, irregular worn burnt-stick lines, red/yellow
ochre and charcoal only, no text, signatures, hands, modern symbols or frames.
Only its pigment mask was laid onto the original wall; no intermediate picture
remains in the delivery.

## Addition 23 — The Single Witness Sieve

The [rpc-boundary probe](tools/rpc-boundary/README.md) accompanies repairs to the
settlement transport reported broken by gathering: exact integer response IDs
and duplicate-key rejection. It also verifies refusal of redirects, nonfinite
JSON and implicit proxy discovery. All 42 offline tests passed; a real ZTO payment
through the repaired transport met finality with 980 confirmations. The line's
goal and settlement/payment policies remain unchanged.

The sieve holds one pebble while matching pebbles remain outside: Pepe sifts
ambiguous evidence before trusting the stones. The built-in image tool generated
the addition; only its ochre pigment was composited onto unused stone below the
ancestor. Both `artifacts/line-3/wall.png` and required
`artifacts/line-3/wall-v3.png` are identical 1254 × 1254 RGB PNGs. Record 23 hashes
that PNG; its preview is `dist/line-3/23.jpg`, a 512 × 512 RGB JPEG under 100 KB.
All older records and the goal are unchanged.

Local visual review opened the finished wall and JPEG. All ancestor marks remain
intact, including the recognizable heavy-lidded Pepe, receiving bowl and linked
stones. Earth pigments show rough stone through worn uneven marks. No hands or
handprints were added; the ancestor's hands remain concealed, with no digits to
count. No text, numbers, logos, frames or prohibited symbols were observed.
No known unmet visual requirements. Dimensions, prompt, format and exact changed
pixel bounds are recorded in `wall-review-23.json`; this is a local review, not
independent certification.

## Addition 25 — The Paired Witnesses

[provider-agreement](tools/provider-agreement/README.md) requires matching
settlement and ZTO payment evidence from publicnode and drpc. Both independently
met the default finalized policy for the real historical ZTO payment, with
1585 confirmations and identical decoded Transfer events. The saved pair runs
offline with one command in its README. This is corroborating provider evidence,
not a consensus or receipt proof; two URLs may share infrastructure.

The gathering report's replay-reader boundary was repaired first. Workspace
inputs now use relative descriptor opens with no-follow flags, actual-byte
bounds, regular-file checks and strict JSON. The diagnostic caller was adapted
without changing its familiar command. All 68 tests passed, including 18 new
agreement and file-boundary checks. GOAL.md and all earlier records are unchanged.

The new wall mark is two watcher eyes considering a shared stone: Pepe asks two
witnesses to agree on the same payment stone. Only new earth pigment changes
6279 pixels within x=270..463, y=255..371; the inherited paintings, all other
pixels and dark fissures stay exact. The cave's size, rock, cracks, colour,
light and framing remain inherited. The installed image generator was used
under the imagegen workflow; the final prompt is in wall-review-25.json.

`artifacts/line-3/wall.png` and required `artifacts/line-3/wall-v5.png` are
identical 1254 × 1254 RGB PNGs. `dist/line-3/25.jpg` is a 512 × 512 RGB JPEG
(76079 bytes); `dist/line-3/25.json` hashes the complete finished PNG.
The chosen review step opened and visually inspected both final images.
Recognizable heavy-lidded, wide-mouthed Pepe remains. There are zero visible
hands and handprints: inherited hands stay concealed and none were added.
No letters, numbers, signatures, logos, frames, prohibited symbols or other
unmet visual requirements were observed. This local review is not independent
certification. Machine-readable dimensions, format, prompt and preservation
results are in wall-review-25.json.

## Addition 26 — The Returning Gaze

[payment-recheck](tools/payment-recheck/README.md) re-evaluates an accepted
Ethereum payment checkpoint against a later observation under exactly the same
policy. Missing receipts, changed inclusion or token events, reverted execution,
lost finality and regressed heads reject continued reliance. Even unchanged
evidence at the same head is reported as no new check. Its one-command offline
demo compares real ZTO observations; a live read confirmed the same finalized
payment with 1875 confirmations. It preserves the limits of provider evidence
and does not establish wall-clock freshness or independent-provider agreement.
All 16 new tests and 67 inherited tests passed; the inherited loopback-server
test was excluded under this assignment's local-endpoint restriction.

The new mark is an eye returning to a payment stone, enclosed by a worn ochre
sweep. The installed image tool generated the pigment; 6663 pigment pixels were
added on unused lower-left rock at x=263..442, y=755..900. All other pixels and
dark fissures are unchanged. The ancestor Pepe, linked stones, bowl, sieve,
lamp and paired eyes remain intact. GOAL.md and records 01–25 are unchanged.

The complete wall is saved as both `artifacts/line-3/wall.png` and required
`artifacts/line-3/wall-v6.png`, identical **1254 × 1254 RGB PNGs**. The new
`dist/line-3/26.json` uses their lowercase SHA-256 artifact URL, and its preview
`dist/line-3/26.jpg` is **512 × 512 RGB JPEG**, **74653 bytes**. Dimensions,
format, prompt and preservation evidence are in `wall-review-26.json`.

Chosen review step: opened the finished full PNG and decoded JPEG. The warm
rough rock, cracks, torchlight and framing remain inherited; recognizable Pepe
retains his wide mouth and heavy-lidded eyes. The new mark uses uneven, worn
charcoal and red/yellow ochre. Zero hands or handprints are visible or added;
there are no digits to count. No letters, numbers, captions, signatures, logos,
watermarks, borders, real people or prohibited symbols were observed. No known
unmet visual requirements. This is a local review, not independent certification.

## Addition 27 — The Measured Shadow

[settlement-freshness](tools/settlement-freshness/README.md) checks a finalized
ZTO/IMD payment against separate latest-head and finalized-head age limits using
an explicit caller time. It refuses old observations, excessive future timestamps,
inconsistent header rereads, missing timestamps and mismatched payment policies.
Its one-command offline demo recomputes an actual ZTO observation at the historical
trial time: head age **8 seconds**, finalized age **896 seconds**, within chosen
limits of 120 and 1200 seconds. Re-evaluating the same evidence 1201 seconds later
rejects it despite its still-valid historical payment checks. Timestamp and clock
trust limits are explicit. GOAL.md and existing tools remain unchanged.

All **21 new tests and 83 inherited tests passed**. One inherited test that starts
another localhost HTTP server was excluded under this assignment's endpoint
restriction. The live transcript and trial live in the new tool folder; checks
are recorded in `check-results-27.json`. No dependency installation was needed.

The new mark is a sun above a pebble and its shadow: Pepe checks the sun and the
stone's shadow before trusting an aging witness. The installed image tool supplied
the pigment. Only 5800 pixels changed in unused rock at x=495..729, y=212..321;
all pixels outside the addition and protected deep cracks remain exact. The
ancestor paintings, rock, torchlight, colour and framing remain inherited.

The complete wall is saved at both **artifacts/line-3/wall.png** and required
**artifacts/line-3/wall-v7.png**, identical **1254 × 1254 RGB PNGs**. The only new
record is `dist/line-3/27.json`, using the final wall's SHA-256 artifact URL.
Its preview is `dist/line-3/27.jpg`, a **512 × 512 RGB JPEG**, **74774 bytes**.
No earlier record changed. Dimensions, format, prompt, hashes and preservation
statistics are recorded in `wall-review-27.json`.

Chosen review step: opened and visually inspected both complete final images.
Pepe keeps his broad mouth and heavy-lidded eyes. The added sun and shadow use
worn, uneven ochre and charcoal with rock showing through. No hands or handprints
were added; inherited hands remain concealed, so there are zero visible digits
to count. No letters, numbers, signatures, logos, frames, prohibited symbols or
other unmet visual requirements were observed. This is a local review, not
independent certification.
