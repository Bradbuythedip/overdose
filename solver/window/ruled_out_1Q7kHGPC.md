# 1Q7kHGPCrMWgB16EvhZpqSovc1LLPo3o28 — ruled out, twice (2026-09-13)

This address has now been proposed as the puzzle wallet twice in this project.
Recording the refutation permanently so it does not come back a third time.

## What is true about it

Verified locally against `address_map.bin`:

```
1Q7kHGPCrMWgB16EvhZpqSovc1LLPo3o28
  balance 2000000000 sats = 20.00000000 BTC
  in the 962 exactly-20 set : yes
  in the 870 named set      : yes
  in targets_all116         : yes
```

So it is a genuine candidate. It has been in our candidate list from the start.

## Why that is not evidence

**962 addresses hold exactly 20.00000000 BTC** (`window/funnel_audit.md`),
against 142 at 19 BTC and 94 at 21 BTC — 20 is simply a popular round holding,
about 7x its whole-BTC neighbours. The candidate set was *filtered* on the
exactly-20 property, so "it holds exactly 20 BTC" cannot discriminate this
address from the other 961. Every argument of that form is circular.

## Why it is ruled out

Its funding transaction is a **66-input consolidation** (independently
reported as 67 inputs from a live Esplora query — either way, a service sweep), and
`18r8ftfovKza9cDEvVRaqRjkaDPXj16dAQ` appears **twice** among those inputs.
That address is independently documented as the **CashFX Group Ponzi scheme's
deposit-and-withdrawal wallet**:

- 19,830 transactions, 1,591.29 BTC total throughput, now zero balance
- BehindMLM's blockchain analysis: *"On March 10th CashFX Group started using
  the wallet 18r8ftfovKza9cDEvVRaqRjkaDPXj16dAQ to accept new deposits and pay
  out withdrawal requests"*
- the SEC stated CashFX Group *"shows indication of a possible Ponzi scheme"*

And the operating pattern documented for that wallet is exactly the shape of
our funding transaction: *"Deposits were grouped together and sent to multiple
withdrawals in single transactions."* A 66-input consolidation paying out is
the CashFX payout fingerprint, not a magazine puzzle being funded.

Timing agrees: the CashFX wallet's documented active period runs March–May 2021
(the "sustained drop from the ATH of 53% over 7 days" is May 2021), which is
before the February 2022 publication of the article.

## The "incoming wallets tell us how to solve it" idea is backwards

Worth stating plainly, because it is an appealing thought:

1. Keiser said the key is **encoded in the article text**. The intended solve
   path is: read the magazine → decode the key → sweep the coins. The funding
   transaction is how the address *received* its coins; it is not part of the
   cipher.
2. **You cannot derive a private key from a list of input addresses.** Input
   addresses are hash160s of other people's public keys. No amount of reading
   them yields the spending key for the output.
3. It is circular as a method. To read a funding transaction's inputs you must
   already know which address to look at — but identifying the address is
   *downstream* of decoding the key. If you needed the inputs to solve it, the
   puzzle would be unsolvable by its own stated route.

What the inputs *are* good for is **attribution** — evidence about who funded
the address. That is exactly the test applied here, and it comes back CashFX
Ponzi rather than Max Keiser.

## What would actually change this verdict

An input list showing funding from a wallet plausibly Keiser's — an exchange
withdrawal to a fresh single-purpose address, or a cluster tied to him — rather
than from a payment processor with 19,830 transactions. If anyone can produce
the full input list of
`9de8217e245b08630767c7539afd2224132527edb52b58c7bf178bb6eb63fa42`, it can be
tested directly: every input checked against the named 870, against known
Keiser addresses, and for service-cluster membership.
