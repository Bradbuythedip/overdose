# The prize is unswept: what that eliminates (2026-09-14)

User-supplied intelligence, from direct conversation with Keiser on Twitter:
**the prize has not been swept.** Recorded as a premise from the user, not as
something verified here — but its consequences are sharp enough to reshape the
search, so they are worth stating exactly.

## It kills joint J1

`window/working_backwards.md` ranked the oracle blind spot (J1) as the most
likely explanation for a universal, featureless null: our sweeps can only ask
*"is this funded now?"*, never *"did this ever exist?"*, so a swept prize reads
identically to a wrong answer.

An unswept prize is still funded. `/tmp/address_map.bin` is the **complete**
set of currently-funded addresses — 56,795,328 of them, every address with a
non-zero balance, at any amount. So:

> If the prize is unswept, its address IS in our index, and a correct
> derivation WOULD have fired.

J1 is dead. This also retires `window/the_oracle_blind_spot.md` and my own
`wf/ORACLE_BLINDSPOT.md` as explanations, though the methodological point in
them stands.

## What remains is exactly two branches

| joint | claim | status |
|---|---|---|
| ~~J1~~ | ~~our detector cannot see it~~ | **eliminated by the unswept premise** |
| J2 | the material is not in what we searched | open |
| J3 | the derivation was never tried | open |

That is the entire remaining space. Every one of the ~150M derivations was
scored against an index that provably contains the target, so the failure is
in the *input* (J2) or the *method* (J3), and nowhere else.

## It also locates the address

An unswept prize of 20 BTC sits in a currently-funded address holding about 20
BTC. The project has already enumerated that population:

| set | n |
|---|---|
| addresses holding exactly 20.00000000 BTC | 962 |
| of those, named | 870 |
| in-window (funded Sept-2021 to Mar-2023, never moved, absent pre-2021) | **122** |
| tier 1: in-window, exactly 20, legacy P2PKH | **32** |

`window/candidates_exact20_inwindow.txt` holds the 122. Three were already
flagged as "personal peel" shaped — one or two inputs, a payment plus change,
not an exchange sweep — and funded near publication:

```
1BX2qZ9y1Db8SpRKjeViUhjuadWtL4X29t    2 Nov 2021
1AkNdBrfKVyoLuhnRKZuZRZg3j7jQxaWFi   27 Feb 2022   (16 days after publication)
1H8Ki8vUU6qeMMWgkaPSJwwRv3rRYuuU64    1 Jun 2022
```

Two entries in that file are already excluded: `1Q7kHGPCrMWgB16EvhZpqSovc1LLPo3o28`
and `1fUejUxqCWqEjt5wvsAnr3p5KrytNRT53` are CashFX Group deposit wallets
(`window/ruled_out_1Q7kHGPC.md`).

Caveat that keeps this honest: "for 20 BTC" need not mean exactly
20.00000000, and the prize could be P2SH or segwit. The 122 is the tightest
defensible set, not a certainty.

## The highest-value action is no longer compute

The user has a channel no sweep has: **direct contact with the setter.** Four
questions, ranked by how much each collapses the search:

1. **"What is the address?"** Ends it. The prize becomes verifiable, and
   `wf/reverse_lookup.py` works backwards from there to the method.
2. **"Is the key all in Issue 24, or spread across your columns?"** This is the
   single most valuable *question*, because it decides J2 against J3 — the
   whole remaining space. He said key**s**, plural, "in the text" of his column
   generally, and only Issue 24 has ever been examined.
3. **"Is it a 12-word phrase, a WIF, or a raw hex key?"** Names the derivation
   family and retires most of J3 at a stroke.
4. **"Is it one of these 32?"** Even a yes/no locates the prize inside an
   enumerated set.

Question 2 is the one to ask if only one gets answered. Page 72 is the standing
proof that missing source material is this project's binding constraint: it sat
inside the issue we already had, absent from every transcript, for three
sessions, and it carried a second banknote serial and 22 printed numerals that
no corpus contained.
