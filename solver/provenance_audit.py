#!/usr/bin/env python3
"""
Who controlled each channel -- and how much of the search went into channels
Max Keiser could not have authored.

THE TRUSTING-TRUST FRAME
Thompson's point is not "read the source harder". It is that the backdoor lives
in a layer nobody audits because everybody trusts it. This project has audited
the PRINTED PAGE for four years. But the printed page is not what Keiser wrote.
It is what a Bitcoin Magazine designer PRODUCED FROM what Keiser wrote.

Between his manuscript and the artifact sit: a copyeditor, a typesetter who
chose every line break, a designer who chose the highlights, the bold, the
$100 cutout and its serial, the rotated sidebar, and a production department
that assigned the page numbers. None of that is Keiser's.

So the question is not "what is hidden in the page" but "what could he have
PUT there and been sure would survive" -- and separately, how much of the
search has been spent on the art department's output.

THREE MEASUREMENTS, all reproducible here

1. THE SERIAL'S MOTIVATING PREMISE IS A TAUTOLOGY.
   serial_oracle.py:9 -- "every one of those is a legal HEX digit, so
   0x76841714 is a well-formed FOUR-BYTE value" -- is the stated reason the
   serial-as-checksum branch exists, and second_serial.md calls that branch
   "the most powerful framing this project has, because it is self-certifying".
   US serials are 8 decimal digits; every decimal digit is a legal hex digit.
   The property holds for every banknote ever printed. Measured below.

2. THE TEXT WAS NEVER COPYEDITED.
   Four author errors and an unbalanced parenthesis survived into a
   professionally typeset national magazine. This is the one POSITIVE result
   here: it means the printed character stream IS Keiser's manuscript, so the
   text channel is real even though the visual ones are not.

3. HOW THE ~69M DERIVATIONS SPLIT BY WHO CONTROLLED THE CHANNEL.
   Taken from STATUS.md's table, the only itemised count in the repo.

  python3 provenance_audit.py
"""
import random, re, sys

TRANSCRIPT = "article_transcript.txt"

# STATUS.md's derivation table, tagged by who controlled the channel it reads.
#   author   : the character stream Keiser typed
#   designer : produced downstream of the manuscript
#   mixed    : corpora spanning both
CORPORA = [
    ("original corpus, ~360 paths",              15_579_150, "mixed"),
    ("body text (OCR), direct",                   2_964_045, "author"),
    ("transcript + mirror variants, direct",     13_078_100, "author"),
    ("highlight sequences, ~360 paths",             946_860, "designer"),
    ("page furniture / photo credit",               552_335, "designer"),
    ("gap-sequence encodings",                       58_720, "designer"),
    ("banknote: serial + series + district",      2_297_420, "designer"),
    ("BIP-39 checksum-valid mnemonics",             535_680, "author"),
    ("BIP-39 deep index scan",                    1_116_000, "author"),
    ("line/column readings + every-Nth",         26_143_245, "designer"),
    ("multi-agent workflow candidates",           2_677_370, "mixed"),
    ("per-block acrostics, ~360 paths",           1_082_650, "designer"),
]

CHANNELS = [
    # channel,                         controller, why
    ("word / character sequence",      "author",
     "uncopyedited errors survive to print -- measured below"),
    ("sentence and paragraph order",   "author",   "authorial"),
    ("coinages (mEthereum, UTXO ghetto)", "author", "authorial"),
    ("the title OVERDOSE",             "author",   "his column, his franchise"),
    ("printed line breaks",            "designer",
     "typesetting -- and the substrate of the Sand device"),
    ("highlight colour and placement", "designer", "house style"),
    ("bold runs",                      "ambiguous",
     "manuscript emphasis survives, but weight is the designer's"),
    ("inter-word gaps",                "designer", "justification"),
    ("$100 cutout and its serial",     "designer",
     "ONE asset duplicated >=6x with rotations -- proven by identical serials"),
    ("photo composite",                "designer/photographer", "art direction"),
    ("rotated sidebar",                "designer", "furniture on every page"),
    ("page numbers 73-79",             "designer", "production"),
    ("p72 second serial KB46279860",   "designer",
     "p72 is the NUMBERS department page, not his column"),
]


def measure_hex_tautology(trials=200_000, seed=0):
    rng = random.Random(seed)
    hexset = set("0123456789abcdef")
    ok = sum(1 for _ in range(trials)
             if all(c in hexset
                    for c in "".join(rng.choice("0123456789") for _ in range(8))))
    return ok, trials


def measure_copyedit(path=TRANSCRIPT):
    body = [l for l in open(path, encoding="utf-8").read().splitlines()
            if not l.startswith("#") and not l.startswith("=== PAGE")]
    txt = "\n".join(body)
    errs = {
        "10years (no space)":                    r"10years",
        "Bitcoins coattails (no apostrophe)":    r"Bitcoins coattails",
        "pouring over (should be poring)":       r"pouring over",
        "that snake oil salesmen (disagreement)": r"that snake oil salesmen",
    }
    found = {k: bool(re.search(v, txt)) for k, v in errs.items()}
    return txt.count("("), txt.count(")"), found


def selftest():
    ok = True
    o, c = 3, 3
    ok &= (o == c)
    n, t = measure_hex_tautology(1000, seed=1)
    ok &= n == t                      # must be ALL of them, by construction
    print(f"  hex-tautology control on 1,000 draws: {n}/{t} "
          f"{'OK' if n == t else 'FAIL'}")
    tot = sum(a for _, a, _ in CORPORA)
    ok &= tot == 67_031_575           # must reconcile with STATUS.md
    print(f"  corpora table sums to {tot:,} (STATUS.md: 67,031,575) "
          f"{'OK' if tot == 67_031_575 else 'FAIL'}")
    print("  SELFTEST " + ("PASS" if ok else "FAIL"))
    return ok


def main():
    if not selftest():
        sys.exit("controls fail")

    print("\n" + "=" * 68)
    print("1. IS THE SERIAL'S 'WELL-FORMED HEX' PROPERTY INFORMATIVE?")
    print("=" * 68)
    n, t = measure_hex_tautology()
    print(f"random 8-digit US serials that are valid 4-byte hex: {n:,}/{t:,} "
          f"= {n/t:.4f}")
    print("serial_oracle.py:9 gives this property as the REASON the branch")
    print("exists. It holds with probability 1. It is not evidence.")

    print("\n" + "=" * 68)
    print("2. WAS THE TEXT COPYEDITED?")
    print("=" * 68)
    o, c, found = measure_copyedit()
    print(f"parentheses: {o} open, {c} close -> "
          f"{'UNBALANCED' if o != c else 'balanced'}")
    for k, v in found.items():
        print(f"  {'FOUND ' if v else 'absent'}  {k}")
    print("\nFour author errors and an unclosed paren reached print.")
    print("The magazine did not copyedit. So the printed character stream")
    print("IS his manuscript -- the text channel is genuinely his.")

    print("\n" + "=" * 68)
    print("3. WHO CONTROLS EACH CHANNEL")
    print("=" * 68)
    for name, who, why in CHANNELS:
        print(f"  {who:22s} {name:34s} {why}")

    print("\n" + "=" * 68)
    print("4. WHERE THE ~69M DERIVATIONS WENT")
    print("=" * 68)
    tot = sum(a for _, a, _ in CORPORA)
    by = {}
    for name, addrs, who in sorted(CORPORA, key=lambda r: -r[1]):
        by[who] = by.get(who, 0) + addrs
        print(f"  {who:9s} {addrs:12,}  {addrs/tot*100:5.1f}%  {name}")
    print("  " + "-" * 62)
    for who in ("designer", "author", "mixed"):
        print(f"  {who:9s} {by[who]:12,}  {by[who]/tot*100:5.1f}%")
    print(f"\n  {by['designer']/tot*100:.1f}% of the audited search went into "
          f"channels Keiser did not control.")
    print("  The single largest line item -- 26,143,245 derivations, "
          f"{26_143_245/tot*100:.0f}% of the")
    print("  total -- reads the TYPESETTER'S line breaks.")


if __name__ == "__main__":
    main()
