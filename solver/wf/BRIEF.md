# Brief for workflow agents (read fully before doing anything)

You are one agent in a multi-agent attack on Max Keiser's "Overdose" 20 BTC
puzzle (Bitcoin Magazine Issue 24, El Salvador edition, pages 73-79, Nov 2021).
Read `solver/SOLVE_PROMPT.md` first: it lists what is ALREADY ELIMINATED. Do
not redo any of it. Then read `solver/article_transcript.txt` (line breaks are
as printed).

Clues, dated by tweet snowflake:
- 2021-11-19  Keiser: "Read my piece in Bitcoin Magazine 'Bitcoin Is Toxic AF'"
- 2022-12-26  "Like George Sand's hidden cryptography, I have hidden private keyS in the text"
- 2023-03-04  "I hid a private key encoded in this piece ... it's for 20 BTC"
- 2023-03-05  mirror writing (links Schott 2007, JNNP, PMC2117809 "Mirror writing:
              neurological reflections on an unusual phenomenon" - Leonardo, Lewis Carroll)
- 2023-12-30  replying to "if I crack it I'll move to El Salvador": "Obviously, 'El Salvador' is a clue."

Page images: /home/user/overdose/IMG_6244.jpeg .. IMG_6250.jpeg (pages 73-79).
2x zoomed horizontal strips of the text pages: solver/strips/p{75..79}_s{00..09}_y{Y}.png
(320 px tall at 1x, 260 px step, so consecutive strips overlap by 60 px).

## Tooling you MUST use (no network to any Bitcoin API; do not try)

`solver/harness.py` (run `python3 harness.py --selftest` from solver/ once; it must print SELFTEST PASS):
- `Oracle()` -> `.funded(addr)`, `.check_priv(priv32) -> [(type, addr)]`,
  `.check_phrase_direct(phrase)` (7 fast hashes x 5 script types)
  The oracle is an April-2023 rich list (1.72M addresses down to ~1 BTC, positive
  control: all 870 known exactly-20-BTC addresses present). A 20 BTC prize
  address funded by Apr 2023 MUST be in it.
- `addrs_for_priv(priv32)`, `bip39_addrs(mnemonic, passphrase, paths)`,
  `electrum_v2_addrs(text, passphrase, n)`, `electrum_old_addrs(words, n)`
- Checksum oracles needing no chain: `wif_check`, `bip38_check`, `mini_check`,
  `bip39_valid(words)`, `electrum_v2_type(text)` ('standard'/'segwit'/None),
  `electrum_old_valid(words)`
- `englishness_z(s)` : English-trigram z-score vs letter-shuffled null
  (article prose scores about +70; noise is |z| < ~5). Remember the lesson in
  `solver/window/every_nth_resolved.md`: the null must match the OPERATION.
- Wordlists: /tmp/wl/bip39_english.txt, old Electrum list in harness.ELECTRUM_OLD.
- Python libs available: coincurve, ecdsa, base58, mnemonic, numpy, PIL.

Standing rules:
1. A null from any new data source or pipeline means nothing until that
   pipeline has produced a KNOWN POSITIVE (run and show a control).
2. Never present an unverified key. A candidate counts only if the oracle says
   its address is funded, or a WIF/BIP38 checksum validates.
3. Put your scripts in solver/wf/<your-label>.py so they can be re-run. Be
   frugal with per-candidate cost: fast hashes first, HD paths from
   `quick_paths()` before `default_paths()`.
4. Report exactly what you tried, counts, controls, and hits (probably none).
