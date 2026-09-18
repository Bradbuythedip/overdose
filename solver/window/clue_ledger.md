# Clue ledger — output of running CLUE_HUNT_PROMPT.md (2026-09-17)

Run from a container where **web search works but page fetch is blocked** for
x.com, bitcoinmagazine.com, behance.net, amazon.com and nostr.com. So every
entry below is sourced from search-result snippets or from material already in
this repository, and is marked accordingly. Where the decisive fact sits on a
page I could not open, the entry says so and names it as a user action.

Confidence: **verified** = decoded/derived here or quoted from a primary source
snippet; **reported** = stated by a secondary source or snippet summary;
**inferred** = my reasoning, labelled as such.

## 1. Clue ledger

| # | date | source | exact quote / observation | who | conf. | what it constrains |
|---|---|---|---|---|---|---|
| 1 | 2022-02-11 16:25 UTC | [x.com/maxkeiser/1492173067723886594](https://x.com/maxkeiser/status/1492173067723886594) | "President @nayibbukele checking out my column "OVERDOSE" in the El Salvador edition of @BitcoinMagazine" | Keiser | verified (date by snowflake, `snowflake.py`) | article was printed and in Keiser's hands by this date; **hand-delivered to Bukele** ([elsalvadorinenglish.com, 2022-02-11](https://elsalvadorinenglish.com/2022/02/11/president-bukele-received-a-special-edition-of-the-bitcoin-magazine-from-max-keiser-and-stacy-hebert/)) |
| 2 | 2022-12-26 14:09 UTC | [x.com/maxkeiser/1607378060172460032](https://x.com/maxkeiser/status/1607378060172460032) | "Have you ever picked up a physical copy of @BitcoinMagazine and read my column and Like George Sand's hidden cryptography, I have hidden private keys in the text." | Keiser | verified | **keys, plural**; "physical copy"; "in the text"; names the George Sand device |
| 3 | 2023-03-04 17:22 UTC | [x.com/maxkeiser/1632068898169450497](https://x.com/maxkeiser/status/1632068898169450497) | "I hid a private #Bitcoin key encoded in this piece I wrote for @BitcoinMagazine Mr. President. Nobody's figured it out yet, but it's for 20 BTC" | Keiser | verified | **key, singular** ten weeks later; "encoded"; "nobody's figured it out yet" implies he can observe the address |
| 4 | 2023-03-05 14:43 UTC | [x.com/maxkeiser/1632391507008278528](https://x.com/maxkeiser/status/1632391507008278528) | mirror writing; links PMC2117809 | Keiser | verified (date); content per `keiser_research.md` | names mirror writing; points at one specific document |
| 5 | 2023-12-30 16:29 UTC | [x.com/maxkeiser/1741134493769965603](https://x.com/maxkeiser/status/1741134493769965603) | "Obviously, 'El Salvador' is a clue." | Keiser | verified (date); content per `keiser_research.md` | El Salvador is a clue (already swept as keyword, passphrase, and cipher key — null) |
| 6 | 2023-03 | [nostr.com nevent1qqsz6u7…](https://nostr.com/nevent1qqsz6u7hzvsatm5r9uts7sxuqfvpyuv25ee6ffav7r94xyn98uk3ysqpzpmhxue69uhkummnw3ezuamfdejsdzqq47) | "20 BTC hidden in Bitcoin Magazine Issue 24, by Max Keiser. Check out the pages in …" — a 7-note thread | third party, unidentified | reported (page not fetchable) | someone posted the pages publicly in March 2023; **no snippet shows a solve claim or an address** |
| 7 | — | search across X, bitcointalk, reddit, nostr, btcpuzzle.info | no snippet anywhere shows Keiser posting an address, a balance, a txid, a signed message, or "still unclaimed" with a date; no snippet shows anyone claiming a solve | — | reported (absence) | **the single most important fact is missing from the public record**: there is no evidence the prize address was ever funded |
| 8 | c. 1870–1915 | [ciphermysteries.com](https://ciphermysteries.com/2010/05/16/george-sands-cryptography), [bibmath.net](https://www.bibmath.net/crypto/index.php?action=affiche&quoi=stegano%2Flitstegano) | the famous Sand–Musset coded letters are **a hoax**, dated to 1870–1915; Sand's letter is read **every other line**, Musset's reply by **the first word of each line** ("Quand voulez-vous que je couche avec vous ?") | literature | verified (multiple independent sources) | Keiser's "George Sand's hidden cryptography" refers to the hoax letters; both devices — alternate lines and first-word-per-line — are **already swept and null** in this repo (`gen_sand.py`, `column_cipher.py`) |
| 9 | 2007 | `corpora_ref/schott_PMC2117809.txt` (held locally) | the linked paper's Leonardo material is **Figure 3** ("Leonardo da Vinci: examples of mirror writing, mirror numbers") and **Table 4**; the only numbered case is "case 28", a Japanese patient | Schott, JNNP 2007;78:5–13 | verified (grepped) | no figure, table or case number maps to anything in the article; the paper reads as a **thematic** pointer to mirror writing / Leonardo, not a book-cipher key (running-key test already null both directions) |
| 10 | Fall 2021 | [amazon.com/dp/B09MBGYK4X](https://www.amazon.com/Bitcoin-Magazine-Fall-Salvador-Issue/dp/B09MBGYK4X) | "Bitcoin Magazine (Fall, 2021) the El Salvador Issue", BTC Media LLC, 100 pages, ASIN B09MBGYK4X; listing "currently unavailable in the format shown" | Amazon | reported | **a digital edition may exist.** BTC Media publishes other issues as Kindle eBooks ([Issue One, B0BQC6GW67](https://www.amazon.com/Bitcoin-Magazine-Issue-Mihai-Alisie-ebook/dp/B0BQC6GW67); [Issue Four, B0C9K1SFW8](https://www.amazon.com/Bitcoin-Magazine-Issue-Mihai-Alisie-ebook/dp/B0C9K1SFW8)), so a Kindle Issue 24 is plausible. **User action: open the listing; if Kindle, obtain it** — canonical text retires the transcription hypothesis and vector highlights settle the geometry |
| 11 | 2021-10 / posted 2021-12 | [behance.net/gallery/133310833](https://www.behance.net/gallery/133310833/Bitcoin-Magazine-Cover) | "Original cover for the El Salvador issue of Bitcoin Magazine" | the cover's designer (name on the page, not in any snippet) | reported | **the designer is identifiable.** User action: open the page, get the name, check whether they designed the interior spread and have ever commented on it |
| 12 | 2023-04-25 → 05-09 | [bitcoinmagazine.com …el-salvador-cover-ordinals-giveaway](https://bitcoinmagazine.com/culture/bitcoin-magazine-launches-el-salvador-cover-ordinals-giveaway) | 21 numbered "El Salvador Cover Edition" magazines, each paired with an Ordinals inscription; 20 given away, 1 kept | Bitcoin Magazine | reported | the **cover** was inscribed on-chain, not the article. Explains the "Bitcoin Magazine" inscriptions `chain_tail_scan`'s PUBLISHER detector found. Also: the publisher was running Ordinals promotions *around this issue* in the same weeks Keiser tweeted the 20 BTC claim (2023-03-04) — the claim sits inside a marketing window for the issue |
| 13 | 2009-02-08 | verified twice via search, tested in `twitter_id.py` | @maxkeiser numeric user ID **20374262**, pre-Snowflake account | — | verified | tested as material in all forms — null. Recorded so nobody re-derives it |
| 14 | ~2013 | [facebook.com/cryptosrus …](https://www.facebook.com/cryptosrus/posts/the-one-that-got-awayten-years-ago-max-keiser-handed-russell-brand-1000-bitcoin-/1415517153913449/) | "Ten years ago Max Keiser handed Russell Brand 1000 bitcoin" | third party | reported | prior on Keiser's style: he gives bitcoin away **physically and publicly**, as with the Opendime hunt — consistent with a printed-object puzzle, and with a puzzle whose *promotion* matters more than its solvability |

## 2. Contradictions

- **Keys vs key.** 2022-12-26: "hidden private key**s** in the text." 2023-03-04:
  "a private key … it's for 20 BTC." Either there are several (and only one is
  the prize), or the plural was loose talk. Every "assembled fragments" reading
  has been swept (`composite.py`) and is null.
- **"In the text" vs a text that is exhausted.** ~350M derivations, a 124-bit
  capacity bound on the typographic channels, and the human-choosable phrases
  provably never funded. If it is "in the text," it is in a form no method
  here has reached — or "in the text" was loose talk too.
- **"Nobody's figured it out yet" vs no address.** He can only know it is
  unclaimed if he can watch the address. He has never shown it. Both facts can
  be true; but the second is exactly what a bluff would also look like.
- **"Physical copy" vs the Kindle edition.** He specified the printed object.
  If a Kindle edition exists, either the clue survives digitisation (it is in
  the text/layout) or it does not (it is physical — ink, paper, an insert). The
  Kindle edition decides which, cheaply.
- **The Sand device is a hoax and does not fit the prose.** Both Sand readings
  are grammatically broken at every join in this article; the reference is
  almost certainly thematic. Yet it is the only *method* he ever named.

## 3. New instructions for the pipeline

Short, as expected. Nothing found points at a derivation not already run.

- If the **Kindle edition** yields text that differs from `article_transcript.txt`
  at any character, re-run the phrase sweeps on the canonical text. The
  transcript matches printed line counts exactly on all five pages, so the
  expected diff is small — but a single character changes every hash across it.
- If the **designer** confirms any intentional element (a specific highlight
  count, a deliberate serial, an insert), that becomes a precise instruction.
  Until then there is none.

## 4. The questions, ranked

1. **Was the address ever funded, and will Keiser say so?** Ask him directly,
   publicly: "What is the address, so people can see the 20 BTC is there?" A
   refusal is itself information. This one question dominates everything else
   in this ledger. Who: anyone with reach to @maxkeiser; Stacy Herbert; Bitcoin
   Magazine's editors, who published the claim.
2. **Does a digital edition of Issue 24 exist?** Open ASIN B09MBGYK4X; check
   [store.bitcoinmagazine.com](https://store.bitcoinmagazine.com/). If yes,
   obtain it. It answers the transcription question and the physical-vs-text
   question at once.
3. **Who designed the spread, and did Keiser give them anything to embed?**
   Behance 133310833 names the cover designer. The interior may be someone
   else — the masthead page of the issue will say.
4. **What did the March-2023 nostr thread and its replies actually say?** Seven
   notes and any replies — the closest thing to a community record. Not
   fetchable from here; trivially readable from a phone.
5. **Has anyone with a physical copy checked it under UV and a loupe?** The
   only avenue no scan can close.

## 5. Honest status

The public record, as far as web search can reach it, contains **no evidence
that the prize address was ever funded** — no address, no balance, no txid, no
signed message, no "still unclaimed" with a date, and no third party claiming
a solve. Keiser's five statements are the whole of it, and they are internally
inconsistent on the one detail that matters (keys vs key). The only method he
ever named is a literary hoax whose two devices do not fit his own prose. The
claim was made inside the same weeks the publisher was running Ordinals
promotions around this issue.

Against that: ~350 million derivations, a capacity bound proving the
typographic channels cannot hold a key, and a live-endpoint result that the
human-choosable phrases were *never funded at any point in history*.

The record supports this reading: **the prize is more likely never to have
been funded than to be hidden by a method this project has not tried.** That
is not certainty. Two cheap actions could still move it — obtaining the digital
edition, and asking Keiser for the address. Everything else is compute spent
making a null more precise.

## 6. Additions from the 2026-09-18 research pass (snippet-level; x.com, nostr, bitcoinmagazine.com, instagram, archive.org all egress-blocked)

| # | date | source | exact quote / observation | who | conf. | what it constrains |
|---|---|---|---|---|---|---|
| 15 | 2021-11-11 16:09 UTC | [x.com/maxkeiser/1458829153566957568](https://x.com/maxkeiser/status/1458829153566957568) | "2012 vs 2021 Read my OVERDOSE column in @BitcoinMagazine Use Promo Code ORANGEPILL for 21% Off" | Keiser | verified text (search title), date by snowflake | **the column was on sale by 11 Nov 2021**, three months before the Bukele photo; a store promotion with no mention of a key. The two attached images are unseen (user action) |
| 16 | 2021-11-19 13:28 UTC | [x.com/maxkeiser/1461687894792445953](https://x.com/maxkeiser/status/1461687894792445953) | "Read my piece in @BitcoinMagazine "Bitcoin Is Toxic AF" The original toxic maximalist @maxkeiser - 10 yrs in the game - explains all ... Use promo code ORANGEPILL for 21% off" | Keiser | verified text, date by snowflake | he names the piece by its p.75 headline; second promo, no key. **The first hidden-key claim comes 13 months after launch** |
| 17 | 2022-02-12 | [x.com/BitcoinMagazine/1492561542751137793](https://x.com/BitcoinMagazine/status/1492561542751137793) | "Our imaginations & inventiveness have been euthanized by the rancid catnip of fiat money. #Bitcoin puts an end to the paper chase Manhattan bank money laundering lobotomy." | publisher | verified text | independent corroboration of transcript lines 69-72; the one sentence the publisher chose to quote (swept: `reading_record.py`, null) |
| 18 | 2023-03-05 | RT [x.com/Sativum_/1632512191705366528](https://x.com/Sativum_/status/1632512191705366528) preserving the original | RT @maxkeiser: "Mirror writing: neurological reflections on an unusual phenomenon" https://t.co/WkSDXKwSiv | Keiser via RT | verified | **the 'mirror' tweet was nothing but the Schott paper's title in quotes and the link.** No commentary, no instruction. Its clue status rests on timing alone; "Bitcoin is a mirror" is a standing Keiser motif (2024 column "Bitcoin Is A Mirror That Reveals All"; an Instagram reel opening "#Bitcoin is mirror") |
| 19 | 2023-12-30 | [x.com/maxkeiser/1741134493769965603](https://x.com/maxkeiser/status/1741134493769965603) | "Obviously, "El Salvador" is a clue." -- **a reply**, per a search-engine summary of the thread, to @Sharktoshi: "If I crack the code on the hidden Bitcoin in this Bitcoin Magazine article, I'll move to El Salvador." | Keiser | text verified; **reply context reported only** | if the context holds, the line is a quip on the reader's own sentence, not a cipher hint. Weight as keyword/passphrase instruction drops sharply. **User action: read the parent tweet verbatim** |
| 20 | Fall 2022 (Issue 27) | [bitcoinmagazine.com/2022-orange-party-issue](https://bitcoinmagazine.com/2022-orange-party-issue) | contents: "Overdose: Who is The Banana Republic Now, Biatch?" by Max Keiser | publisher | reported | **OVERDOSE is a recurring column.** When he tweeted "read my column ... hidden private keyS in the text" (2022-12-26) the current OVERDOSE was Issue 27, not 24. The plural reads naturally across the series; only the 2023-03-04 tweet pins 20 BTC to "this piece" |
| 21 | 2022-2024 | [bitcoinmagazine.com/authors/max-keiser](https://bitcoinmagazine.com/authors/max-keiser) and issue pages | Keiser print pieces: #24 (Toxic AF), #26 "Censorship, Dematerialization, and Bitcoin", #27 "Who is The Banana Republic Now, Biatch?", #28 "Dr. Orangelove...", #29, #30 "Buy Love, Sell Fear" (**online in full**), Inscription issue "Bitcoin Is A Mirror That Reveals All" (**online; syndicated at nasdaq.com**) | publisher | reported | no key has ever been reported found or spent in ANY of them. Two are online in full: **a control corpus**. If his device is real it should show on canonical digital text of a sibling column; a null there calibrates Issue 24's null (transcription risk vs method risk) |
| 22 | 2023-03-04 | tweet 1632068898169450497 | the whole tweet is inside quotation marks and carries one media link; a search summary reports 173 replies | Keiser | text verified; reply count reported | consistent with captioning an image (plausibly the Bukele photo). No snippet shows him answering any reply with an address, txid or balance |
| 23 | 2021-2023 | LinkedIn / ZoomInfo / 21ism (snippets) | "Annabelle Bazinet -- Director, Product Design at Bitcoin Magazine"; 2021 art director of BTC Inc: Tommy Marcheschi | third party | reported | **the @ANNABELLEBAZ credit on the spread is the magazine's in-house designer**, not an outside photographer: the person credited for the pills-and-mirrored-banknote photo is the person who laid out the pages |
| 24 | 2013 / 2023-10 | Benzinga, news.bitcoin.com, cryptoslate (snippets); tweets 1716790072689745972, 1719096140002422971 | Jones: Keiser handed him a laptop with 10,000 BTC in 2013; Nov 2023 five-question quiz for Jones to "regain" it, failed | third party / Keiser | reported | setter prior: Brand 1,000 BTC, Jones 10,000 BTC, 10 BTC El Salvador hunt -- **three publicity giveaways, none with on-chain verification or a completed payout** |
| 25 | 2021 | Amazon B09MBGYK4X (Books category, "100 pages" vs the publisher's "140+ pages") | -- | Amazon | reported | **no evidence of a digital Issue 24**; the listing is unreliable print-product metadata. Entry 10 above is downgraded |
| 26 | 2023-03-05 | nostr note (poster probably `btcschellingpt`) | "20 BTC hidden in Bitcoin Magazine Issue 24, by Max Keiser. Check out the pages in this 7 note thread Happy Treasure Hunting!" | third party | reported | the entire community record; Keiser himself never wrote "Issue 24" |

### What the additions change

- **Two of the five clues shrink.** The mirror tweet is a bare paper link (18); "El Salvador is a clue" is, on the reported context, a reply quip (19). Neither carries an instruction.
- **"Keys" plural has a mundane explanation**: OVERDOSE is a serial column (20, 21).
- **Timeline**: column on sale 2021-11-11 (15); promoted twice with no key (15, 16); first key claim 2022-12-26; 20 BTC and "this piece" 2023-03-04; community identifies Issue 24 the next day (26). The claim appears 13 months after launch, inside the publisher's promotional window for the issue (entry 12).
- **The designer is identified** (23): Annabelle Bazinet designed and photographed the spread. The banknote, the pills and the highlight bars are hers.
- **The one new lever is a control corpus** (21): two sibling columns exist as canonical digital text. Running the Issue-24 device battery on them is the first test of the METHOD rather than of this text.
