# Clue-hunt prompt: Max Keiser "Overdose" 20 BTC puzzle

Paste everything below the line into a fresh capable model with web search.
This is NOT a key-cracking prompt. `SOLVE_PROMPT.md` covers derivation; that
space has absorbed ~350 million attempts and the highest-prior phrases are now
*provably never funded*. What is missing is not compute. It is **evidence** —
about what the setter actually did, what the object actually contains, and
whether the prize was ever real. Go and find that.

---

## Your job, in one sentence

Build a **clue ledger**: every verifiable fact about this puzzle that
constrains where a key could be or whether one exists — each with its source,
exact wording, and date — and a ranked list of the questions that, if answered,
would change the search. **Do not attempt to derive or brute-force a private
key.** If you catch yourself hashing a phrase, stop; that is out of scope and
has been done.

## The target

Max Keiser's column **"OVERDOSE"** in **Bitcoin Magazine Issue 24, "The El
Salvador Issue"**, print, **pages 72–79** (72 is a NUMBERS page facing the
column; 73–74 the photo spread; 75–79 body text). Cover: *Display Until Feb 23,
2022*, $12.99US, UPC `0 74820 40388 4`, supplement `21`. Photographer credit
`@ANNABELLEBAZ`. He claims to have hidden a private key for 20 BTC in it.

## Keiser's own words — the only hard evidence about METHOD

Dates are decoded from the tweet snowflake IDs (`(id >> 22) + 1288834974657`
ms), not read from article datelines. Verify each; do not trust this table.

| date | tweet ID | what he said |
|---|---|---|
| 2022-02-11 | 1492173067723886594 | Bukele photographed holding the printed El Salvador edition — the article was public by this date |
| 2022-12-26 | 1607378060172460032 | "Have you ever picked up a physical copy of @BitcoinMagazine and read my column and Like George Sand's hidden cryptography, I have hidden private **keys** in the text" |
| 2023-03-04 | 1632068898169450497 | "I hid a private #Bitcoin key encoded in this piece I wrote for @BitcoinMagazine Mr. President. Nobody's figured it out yet, but it's for 20 BTC" |
| 2023-03-05 | 1632391507008278528 | mirror writing — links **PMC2117809**, G D Schott, *Mirror writing: neurological reflections on an unusual phenomenon*, JNNP 2007 |
| 2023-12-30 | 1741134493769965603 | "Obviously, 'El Salvador' is a clue." |

Note the tensions a clue hunter should pull on:
- **"keys" (plural) vs "a private key" (singular)** ten weeks apart.
- **"in the text"** vs a piece whose text has been exhaustively swept.
- **"physical copy"** — he specifies the printed object, not the article.
- **"encoded"** — his word, March 2023.
- **"Nobody's figured it out yet"** — how would he know, unless he can watch the
  address? That implies he knows the address, i.e. it exists and (he believes)
  holds coins.

## What is already established — do not redo, but DO use as constraints

- **Typographic channels cannot carry a key.** Every discrete editorial channel
  on the pages (Bitcoin/bitcoin capitalisation 30 bits, highlight colour 38,
  all-caps 44, wide gaps 7, quotes 5) totals **124 bits**, four short of a
  12-word mnemonic. Per-glyph bold measures at chance across three source
  qualities; baseline residuals at 1.14x flat pages. No underline, no
  strikethrough, no mirrored glyph exists on any page (all measured, not
  eyeballed — several claimed marks turned out to be upscaling artifacts).
- **Highlight colour is binary, not ternary**: all white highlights sit on the
  dark-brown page 77 where black would be invisible; the colour is forced by
  the page ground, not chosen.
- **Two banknote serials**, one cutout reused: `CL 76841714 A` (district `L12`)
  across 73/74, and `KB 46279860` ghosted on page 72. Both exhausted as
  material, checksum, entropy, KDF input, BIP-39 index, mirrored, rotated.
- **The George Sand alternate-line reading is grammatically broken at every
  join** — the article was not written so alternate lines flow. So his Sand
  reference is likely *thematic* ("a key hidden in plain text") rather than the
  literal device. A clue hunter should find out **which Sand story he means**.
- **The Schott paper as a running key / book-cipher key: null** in both
  directions with a firing control.
- **Keiser's X numeric user ID is 20374262** (pre-Snowflake account, created
  2009-02-08). Tested as material, null.
- **Ever-funded verdict**: the 39 most human-choosable strings (the
  thrice-printed pull-quote, headline, sign-off, both serials, cover, page 72)
  x 5 script forms = 4,550 addresses, asked a live endpoint *"was this ever
  funded, at any point"* — **zero were**. Control: `correct horse battery
  staple` shows 148,425 fundings / 15.95 BTC received / 0 balance, invisible to
  offline snapshots. The obvious phrases are not the key and never were.
- 962 addresses hold exactly 20 BTC on-chain; the property discriminates
  nothing. Three "personal peel"-shaped ones funded near publication exist
  (`1BX2qZ9y1Db8SpRKjeViUhjuadWtL4X29t`, `1AkNdBrfKVyoLuhnRKZuZRZg3j7jQxaWFi`,
  `1H8Ki8vUU6qeMMWgkaPSJwwRv3rRYuuU64`); none is derivable from the article.
- His **other** hidden-bitcoin scheme (10 BTC "hidden in El Salvador") was
  **physical** — Opendime hardware wallets — not a cipher. That is a prior on
  how he thinks.

## Where to actually look — ranked

### 1. Is the prize real? (the question that dominates everything)
Every observation so far is consistent with the address never having been
funded. Find any evidence either way:
- Has Keiser ever posted the **address**, a **balance**, a **txid**, a
  **signed message**, or said "it's still there / still unclaimed" with a date?
- Has anyone **asked him for the address** publicly, and what did he reply?
- Did he ever say **when** he funded it, or **which wallet** he used?
- Is there any tweet/podcast where he says the key format — "12 words",
  "a seed phrase", "a WIF", "a brainwallet"?
Search X replies to all five tweets above, his replies to others in Dec 2022–
Jan 2024, and every podcast appearance in that window (Orange Pill Podcast
with Stacy Herbert, Simply Bitcoin, Bitcoin Magazine's own shows, Swan,
Coin Stories, Robert Breedlove, Peter McCormack).

### 2. The publisher's digital edition
Bitcoin Magazine sells digital/PDF editions of print issues. **A digital
edition of Issue 24 would be the single most valuable artifact obtainable**:
canonical text (retiring the transcription-error hypothesis for good), vector
highlight boxes with exact coordinates, embedded fonts (settling bold as a
font property beyond measurement), and any hidden layer or metadata the
designer left. Find out: does one exist, where, and what format. Also the
issue's **table of contents and masthead page** — names of the art director
and designer of this spread.

### 3. The designer
Keiser wrote the words; someone else laid out the pages, drew the highlight
bars, placed the pills and the mirrored banknote. If a key was embedded
visually, that person did it. Identify the designer / art director of Issue
24. Have they ever spoken about it? The photographer `@ANNABELLEBAZ` is
credited on the spread — find their account and any posts about the shoot
(the banknote prop, the pills, the location).

### 4. The rest of THIS issue
"Keys" plural, "in the text" of his column — but a clue hunter should also
check the rest of Issue 24, which the reader *does* have: the contents page,
letters, any editor's note mentioning the column, the back cover, adverts on
facing pages. Especially anything that references "Overdose", "20 BTC", a
hidden key, or Keiser. (Other *issues* are out of bounds — a fair puzzle is
solvable from the object the reader holds.)

### 5. Which George Sand story does he mean?
"George Sand's hidden cryptography" most likely refers to the apocryphal
Sand–Musset letters: read every other line (or the first word of each line)
for a hidden message. But there are several versions circulating, and Keiser
may have a specific one in mind — a book, a documentary, a Stacy Herbert
segment. Find where he encountered it. If his version is "first word of every
line" rather than "alternate lines", that is a different, specific instruction.

### 6. Why THAT paper?
He linked PMC2117809 specifically. Read it. Is there a figure, a numbered
table, a specific Leonardo passage, a case number, that he might be pointing
at? Does he reference Leonardo da Vinci's mirror writing elsewhere? A setter
who links one document usually has one thing in it in mind.

### 7. Community record
- The nostr thread "20 BTC hidden in Bitcoin Magazine Issue 24" (7 notes,
  March 2023) — who posted, what pages, any replies claiming progress.
- bitcointalk, r/Bitcoin, r/BitcoinPuzzles, Telegram puzzle groups, the
  btcpuzzle.info list — has anyone claimed a solve, published an address, or
  reported asking Keiser?
- Bukele's Feb 2022 photo — which pages are visible in his hands? Compare to
  the scans.

### 8. The physical object
Things a scan cannot see: UV-reactive ink, microprinting, embossing, a
different paper stock on one page, a tip-in card, something under the
barcode. Anyone with a physical copy should check under UV and with a loupe.
Report what to look for, not results you cannot have.

## Rules of evidence

- **Quote verbatim, cite the URL, date by snowflake where possible.** No
  paraphrase presented as quote. If you cannot find a source, say "unsourced".
- **Distinguish Keiser's words from other people's.** Quote-aggregator sites
  misattribute (e.g. "swarm of cyber hornets" is Saylor's, not Keiser's).
- **Distinguish "he said X" from "X is true."** He may be bluffing, may have
  never funded it, may misremember his own construction.
- **Never fabricate.** A missing fact is a finding; an invented one poisons
  everything downstream.
- **Mark confidence** on every ledger entry: verified / reported / inferred.
- **Do not derive keys.** If a clue suggests a specific derivation, write the
  derivation *down* as a testable instruction for the derivation pipeline.
  Do not run it yourself.

## Output contract

1. **CLUE LEDGER** — a table: `# | date | source URL | exact quote or
   observation | who said it | confidence | what it constrains`.
2. **CONTRADICTIONS** — where Keiser's statements disagree with each other or
   with the object (e.g. keys vs key; "in the text" vs text exhausted).
3. **NEW INSTRUCTIONS FOR THE PIPELINE** — any derivation a clue *specifically*
   points to, stated precisely enough to implement, with the clue that
   motivates it. Expect this list to be short. An empty list is a valid result.
4. **THE QUESTIONS** — ranked: what single answer would most change the search,
   who could answer it, and how to ask. Question #1 is almost certainly
   *"Was the address ever funded, and will Keiser say so?"*
5. **HONEST STATUS** — one paragraph. If the evidence points to the prize never
   having been funded, say so plainly. Do not manufacture hope; do not
   manufacture despair. State what the record supports.
