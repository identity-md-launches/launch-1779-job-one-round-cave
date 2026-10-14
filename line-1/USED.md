The first step used the supplied cave wall as the base image and added its Pepe figure.
This step restored the first painted line-1 wall from the SHA-256 artifact in `dist/line-1/01.json` because later numbered records were unpainted slots and no local wall PNG was present. It used that painting as the exact base, edited a new pigment mark on open rock, and kept the older Pepe and framing.
The bounded snapshot tool builds on the original `line-1/tools/rpc_snapshot.py` interface and answers the public-read safety issue described in `gathering/REPORT.md`. It uses the real ZTO token address for its live read example.
The anchored ZTO snapshot tool reuses `line-1/tools/bounded-rpc-snapshot/snapshot.py` for strict public-read transport and response-envelope checks. It used Ethereum mainnet's finalized block and the real ZTO contract for its saved example; no coin, account, key, or transaction was used.
The existing bounded snapshot CLI was also tightened so its verify and output paths stay inside the current workspace, following the concern in `gathering/REPORT.md`.
The safe snapshot files piece uses the existing bounded and anchored snapshot interfaces and saved real ZTO evidence. It repairs the symlink/replacement concerns reported in gathering/REPORT.md with descriptor-relative no-follow input and no-clobber output, then records a fresh real ZTO capture. The wall uses record 23's hash-verified painting as its base; an image-generated woven boundary on empty rock represents this file boundary. No older record or goal was changed.
The hash-pinned ZTO piece reuses bounded snapshot JSON/envelope checks and the safe-files boundary. It advances the block-number limitation noted in gathering/REPORT.md with EIP-1898 blockHash/requireCanonical state reads and exact observed decimal rendering. Five real Ethereum public reads produced the included portable ZTO bundle; no wallet, coin creation or transaction was needed. The wall starts from record 24's SHA-256-verified ancestor; two image-generated ochre links were retained on empty upper-right rock, with the older paintings kept pixel-exact.

The snapshot-comparison piece reuses the hash-pinned verifier and its bounded JSON and no-follow file reader unchanged. It compares an ancestor's real ZTO bundle with a fresh five-read public capture, refusing incompatible anchors/precision and rendering exact signed supply differences offline. Gathering 05 reported no broken Line 1 checks. The wall begins with record 25's SHA-256-verified painting; the new small paired-seed mark represents carrying two observations together. GOAL.md and all older records remain unchanged.

The offline snapshot report reuses the hash-pinned verifier, bounded JSON parser,
safe file boundary and comparison piece's real saved ZTO observation unchanged.
Gathering 06 reported no broken Line 1 checks. It adds a browser-readable single
HTML file with exact amounts, both file/content hashes and the full transcript.
The wall starts from record 26's hash-verified painting and retains only a new
image-generated shell on bare stone. `image_bytes.py` is copied byte-for-byte
from gathering's reviewed standard-library PNG/JPEG codec for delivery formatting.
No new dependencies, chain submissions, environment access or coin were needed.
