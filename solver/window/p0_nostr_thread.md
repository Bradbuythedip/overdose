# P0: a second announcement channel, and still no address (2026-09-18)

## The new artifact: a 7-note Nostr thread

Search surfaced a Nostr event this project had never recorded:

> "20 BTC hidden in Bitcoin Magazine Issue 24, by Max Keiser. Check out the
> pages in [a 7 note thread] … Happy Treasure Hunting! Repost far and wide"

`nostr.com` is blocked by this container's egress policy, but an `nevent`
string is self-describing, so it was decoded offline (`nevent.py`, bech32 +
NIP-19 TLV) rather than fetched:

```
nevent1qqsz6u7hzvsatm5r9uts7sxuqfvpyuv25ee6ffav7r94xyn98uk3ysqpzpmhxue69uhkummnw3ezuamfdejsdzqq47

event id : 2d73d71321d5ee832f170f40dc025812718aa673a4a7acf0cb5312653f2d1240
relay    : wss://nostr.wine
```

The TLV carries no author pubkey and no kind — only the event id and one relay
hint. Dated **2023-05-03 per the search index — i.e. the same window as the
mirror-writing tweet**, and described as a thread of **seven** notes, which
matches pages 73–79 one note per page.

### Why it matters, and why it is not a solve

It is a second, independent publication channel for the same claim. Three
things follow:

1. **The seven page images may exist at a provenance other than the seven
   iPhone JPEGs in `public/images/`.** Image forensics on those files is
   already closed (no trailing data, no COM/EXIF payload, no LSB, DQTs
   byte-identical, never re-encoded). A differently-sourced copy would be a
   genuinely new artifact rather than a re-run — but only if it is not the
   same seven files reposted, which is the likelier case.
2. The note is **promotional**, exactly like the tweets. It states the prize
   and asks for reposts. It does not state an address.
3. It does not change the dating. It sits inside the 2021-11-11 → 2023-03-05
   window the clue ledger already covers.

### What is needed to read it

One `REQ` to `wss://nostr.wine` (or any large relay) for
`{"ids":["2d73d713…3f2d1240"]}`, plus the `#e` replies for the other six notes.
Roughly ten seconds of work on a machine with network. This container has none:
every relay, every Nostr front-end (`nostr.com`, `njump.me`) and every general
host tested returns 403 at the egress proxy.

## The funding question, restated after searching

Across every search this session — the announcement, the thread, the puzzle's
status, and explicit searches for a scam/unfunded reading — there is still:

- **no address**
- **no txid**
- **no signed message**
- **no claim of a solve, by anyone, at any date**
- **no "still unclaimed" from Keiser or Bitcoin Magazine**

One corroborating behavioural data point turned up that the repo had only in
prose: Keiser's other headline giveaway, a 10,000 BTC crypto quiz, is reported
as having **paid out nothing** (Alex Jones "misses out on $344M prize").
`final_assessment.md` §5 already lists the physical Opendimes and that quiz as
the reference class. This is a second source for it.

That is not proof of anything. Absence of a published address is consistent
with a funded prize the setter simply never doxxed, and "nobody's figured it
out yet" only requires that Keiser can watch an address. But the record after
five public statements and two publication channels contains zero
chain-verifiable content, and **that remains the single most informative fact
in the case**.

## Egress: what this container can and cannot do

Recorded so nobody repeats it. Every one of these returns 403 CONNECT at the
proxy:

```
bitcoinmagazine.com   nostr.com        njump.me         www.nasdaq.com
blockstream.info      mempool.space    blockchair.com   api.blockcypher.com
bitcointalk.org       reddit.com       x.com            nitter.net
archive.org           web.archive.org  relay.damus.io   api.nostr.band
ncbi.nlm.nih.gov      duckduckgo.com
```

`pypi.org` and `files.pythonhosted.org` are in the proxy bypass list, so the
crypto toolchain (`mnemonic`, `ecdsa`, `base58`) is installable — which is how
`schott_index.py` runs. Web **search** works; web **fetch** does not, for any
host in this case.

The consequence is structural, not incidental:

- **P0 cannot be closed from here.** No chain oracle is reachable, so
  `everused.py` cannot run at all.
- **P1 cannot be run from here.** The sibling columns are web-served on
  `bitcoinmagazine.com` and syndicated on `nasdaq.com`; both are blocked. The
  checksum-first sweep does *not* need print line breaks — a printed WIF
  survives reflow as a character run — so **web text of the siblings is
  sufficient for that arm**, unlike the Sand/Musset arm, which needs the
  typeset lines (`pamphlet_not_public.md`). Anyone with an unrestricted
  network can run it in minutes: save the article text, then
  `python3 wif_hunt.py --transcript <sibling>.txt`.

### A prior that lowers P1's expected value regardless

The online siblings are fully web-indexed, unlike Issue 24, whose text
`no_digital_footprint.md` shows exists nowhere digitally. A 51-character base58
run printed in an indexed article would have been scraped by every key-hunting
crawler within days of publication. So P1's realistic value is **calibration of
Issue 24's null**, not discovery — which is how the handoff prompt already
frames it.
