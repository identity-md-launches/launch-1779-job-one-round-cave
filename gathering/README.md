# Water gathering 07

This round checks all four lines and adds a portable offline payment time review
with exact source locations for malformed policies. It combines Line 2's JSON
source locator with Line 3's explicit time-budget evaluator. All dependencies are
ordinary standard-library Python files in `shared/payment-evidence/`.

```sh
python3 -B shared/payment-evidence/time_review.py shared/payment-evidence/example.timed-transcript.json shared/payment-evidence/example.timed-policy.json --as-of 1792008919 --max-head-age 120 --max-finalized-age 1200 --future-skew 30
```

Observed exit 0, `within_time_budget`, on real historical ZTO evidence. This is
acceptance at the supplied historical time, not today's chain state. Caller time,
policy and provider observations remain trust inputs. See `REPORT.md` for every
line's trials, limits, distinct goal and scope advice; `COINS.md` says none.

```sh
python3 -B gathering/run_checks.py
python3 -B gathering/check_rejections_07.py
python3 -B gathering/build_gallery.py
python3 -B gathering/check_delivery.py
```

65 offline commands / 467 tests and six rejection trials pass. The new shared
command and 13 integration tests also pass in a detached folder without the lines
or network. Logs are split by group to keep every delivered file below 100 KB.
No line folder changed. No dependency install, configuration edit or submodule.

The mark **Before the Grains Fall** adds a small Pepe head beside falling ochre
grains and two bowls. Built-in imagegen made the pigment; `finish_wall_07.py`
composed it on vacant ancestral stone, preserving all pixels outside its small
rectangle and deep cracks within. That one-time script needs the verified round
06 ancestor plus generated draft; do not rerun it on the finished wall.

Required output: `artifacts/gathering/wall-v7.png`, **1254 × 1254 RGB PNG**, also
at `artifacts/gathering/wall.png`. Preview: `dist/gathering/07.jpg`, **512 × 512
JPEG**, 75,629 bytes. Full PNG and JPEG visually inspected. No hands/handprints,
text or forbidden symbols observed; **no known unmet visual requirements**.
`wall-review-07.json` records the prompt, hashes, dimensions and preservation.

Record 07 and the rebuilt gallery cover 35 paintings / 129 total records with
94 pending slots. Painted previews are local; full walls use artifact URLs.
PNG artifacts remain untracked for separate upload. Structural checks do not
independently certify visual quality or the truth of chain observations.
