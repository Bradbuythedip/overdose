#!/usr/bin/env python3
"""
Three clues, three languages: the BIP-39 wordlists nobody has used here.

George Sand wrote in FRENCH. Leonardo's mirror writing is ITALIAN. "Obviously,
'El Salvador' is a clue" -- SPANISH, and the "Mr. President" tweet addresses
a Spanish speaker. BIP-39 has a wordlist for each, and no module in this repo
has ever used any list but English (grep: none). Every index sequence the
object offers is therefore mapped through the Spanish, French and Italian
lists here, English kept as the control that reproduces bip39_index.py:

  the serial digits in every grouping (singles, pairs, triples, quads,
  cumulative; A, B, AB, BA, ABA, BAB...), the article's numerals in print
  order (bip39_index.numerals, number words included), the NUMBERS page's
  figures in print order (page72.LINES: 165, 572, 2020, 4.8, 930.44, 2026,
  3.9, 35.8, 14.5, 2019, 72), structural counts (words per line/sentence/
  paragraph, characters per line, word lengths), highlighted-word positions

Each 12/15/18/21/24-word window is emitted as 'mn:<lang>:<phrase>' so the
sweep checksum-tests it IN THAT LANGUAGE and derives any valid one against
its chance rate. Plus the clue phrases themselves in those languages as plain
brainwallet text: Sobredosis (Overdose), Ley Bitcoin, clave privada, "Cette
nuit" -- the actual hidden message of the Sand-Musset letter -- and so on.

OMITS  English-list readings of the same sequences (bip39_index.py,
index_cipher.py, serial2_exhaust.py F, gen_numbers.py); English clue words
(clue_serial.py, gen_keiser.py).
"""
import itertools, re

LANGS = ("spanish", "french", "italian", "english")

PHRASES = [
    # Spanish / El Salvador
    "El Salvador", "Sobredosis", "SOBREDOSIS", "sobredosis", "Sobredosis de Bitcoin", "Sobredosis Max Keiser",
    "República de El Salvador", "Republica de El Salvador", "San Salvador", "Ley Bitcoin", "Ley Bitcoin 2021",
    "Decreto 57", "Decreto Legislativo 57", "Bitcoin es moneda de curso legal", "moneda de curso legal",
    "7 de septiembre de 2021", "7 septiembre 2021", "07/09/2021", "2021-09-07", "20210907", "09/07/2021",
    "Nayib Bukele", "Nayib Armando Bukele Ortez", "Bukele", "El Zonte", "Playa Bitcoin", "Bitcoin Beach",
    "Chivo", "Chivo Wallet", "Ciudad Bitcoin", "Bitcoin City", "Bono Volcán", "Bono Volcan", "Conchagua",
    "clave privada", "llave privada", "espejo", "escritura especular", "escritura en espejo", "la clave",
    "El Salvador es una pista", "pista", "Obviamente El Salvador es una pista", "Señor Presidente", "Senor Presidente",
    "Presidente Bukele", "veinte bitcoin", "20 bitcoin", "El Salvador 20 BTC", "Pulgarcito", "Pulgarcito de América",
    "colón", "colon", "colón salvadoreño", "SV", "SLV", "503", "+503", "222", "13.7942 -88.8965",
    # French / George Sand
    "Cette nuit", "cette nuit", "CETTE NUIT", "Cette nuit.", "Quand voulez-vous que je couche avec vous",
    "Quand voulez-vous que je couche avec vous ?", "Cette insigne faveur que votre coeur réclame",
    "Cette insigne faveur", "George Sand", "Georges Sand", "Aurore Dupin", "Amantine Lucile Aurore Dupin",
    "Alfred de Musset", "Musset", "Sand Musset", "clé privée", "cle privee", "la clé", "miroir", "écriture en miroir",
    "écriture spéculaire", "Je suis très émue de vous dire", "Je suis tres emue de vous dire",
    # Italian / Leonardo
    "Leonardo da Vinci", "Leonardo", "da Vinci", "Leonardo di ser Piero da Vinci", "scrittura speculare",
    "specchio", "chiave privata", "la chiave", "sovradosaggio", "overdose",
    # cross-language with the serials
    "El Salvador CL76841714A", "Sobredosis 76841714", "Cette nuit 76841714", "El Salvador 46279860",
    "Sobredosis CL76841714A KB46279860", "El Salvador 76841714 46279860",
]


def _seqs():
    """name -> list of ints (the index sequences)."""
    S = {}
    import serial_combine as SC
    S.update({"serial/" + k: v for k, v in SC.index_sequences().items()})
    try:
        import bip39_index as BI
        nums = BI.numerals()
        S["article/numerals"] = nums
        S["article/numerals.cum"] = list(itertools.accumulate(nums))
        ds = "".join(str(n) for n in nums)
        for k in (2, 3, 4):
            S[f"article/numerals.d{k}"] = [int(ds[i:i + k]) for i in range(0, len(ds) - k + 1, k)]
    except Exception:
        pass
    try:
        import page72
        toks = re.findall(r"\d+(?:\.\d+)?", " ".join(page72.LINES))
        ints, digits = [], ""
        seen = set()
        for t in toks:
            if t in seen: continue
            seen.add(t); digits += t.replace(".", "")
            ints += [int(p) for p in t.split(".")]
        S["p72/ints"] = ints
        S["p72/ints.cum"] = list(itertools.accumulate(ints))
        for k in (2, 3, 4):
            S[f"p72/digits.d{k}"] = [int(digits[i:i + k]) for i in range(0, len(digits) - k + 1, k)]
        S["p72/digits.d1"] = [int(c) for c in digits]
    except Exception:
        pass
    import article
    lines, sents, paras = article.load()
    L = [l for l in lines if l.strip()]
    words = " ".join(paras).split()
    S["struct/line_words"] = [len(l.split()) for l in L]
    S["struct/line_chars"] = [len(l) for l in L]
    S["struct/sent_words"] = [len(x.split()) for x in sents]
    S["struct/para_words"] = [len(p.split()) for p in paras]
    S["struct/word_lengths"] = [len(re.sub(r"[^A-Za-z]", "", w)) for w in words]
    for k in ("struct/line_words", "struct/sent_words", "struct/para_words"):
        S[k + ".cum"] = list(itertools.accumulate(S[k]))
    try:
        low = [re.sub(r"[^a-z]", "", w.lower()) for w in words]
        pos = []
        for l in open("highlights_ordered.tsv", encoding="utf-8"):
            if l.startswith("#") or not l.strip(): continue
            p = l.rstrip("\n").split("\t")
            if len(p) < 3: continue
            hw = [re.sub(r"[^a-z]", "", w.lower()) for w in p[2].split()]
            hw = [w for w in hw if w]
            if not hw: continue
            for i in range(len(low) - len(hw) + 1):
                if low[i:i + len(hw)] == hw:
                    pos += list(range(i, i + len(hw))); break
        if pos: S["highlight/word_positions"] = pos; S["highlight/word_positions.b1"] = [p + 1 for p in pos]
    except OSError:
        pass
    return {k: v for k, v in S.items() if len(v) >= 12}


def forms():
    from mnemonic import Mnemonic
    WL = {l: Mnemonic(l).wordlist for l in LANGS}
    out = []
    for name, seq in _seqs().items():
        sizes = (12, 24) if len(seq) > 300 else (12, 15, 18, 21, 24)
        for lang in LANGS:
            for base in (0, 1):
                ws = [WL[lang][(n - base) % 2048] for n in seq]
                for k in sizes:
                    for i in range(0, len(ws) - k + 1):
                        out.append((f"{lang}/{name}/b{base}/w{k}@{i}", f"mn:{lang}:" + " ".join(ws[i:i + k])))
    for i, ph in enumerate(PHRASES):
        out.append((f"phrase/{i}/{ph[:30]}", ph))
        if ph != ph.lower(): out.append((f"phrase/{i}/{ph[:30]}/lower", ph.lower()))
        if ph != ph.upper(): out.append((f"phrase/{i}/{ph[:30]}/upper", ph.upper()))
    seen, uniq = set(), []
    for t, v in out:
        if v not in seen: seen.add(v); uniq.append((t, v))
    return uniq


def selftest():
    F = forms(); tags = [t for t, _ in F]; vals = [v for _, v in F]
    ok = len(set(tags)) == len(tags) and all(vals)
    ok &= any(v.startswith("mn:spanish:") for v in vals) and any(v.startswith("mn:french:") for v in vals) \
          and any(v.startswith("mn:italian:") for v in vals)
    ok &= "Cette nuit" in vals and "Sobredosis" in vals
    # the serial digits through the Spanish list, base 0: 7 -> 'abierto'? verify by direct lookup instead of memory
    from mnemonic import Mnemonic
    es = Mnemonic("spanish").wordlist
    want = "mn:spanish:" + " ".join(es[int(c)] for c in "768417144627")
    ok &= want in vals
    n_mn = sum(1 for v in vals if v.startswith("mn:"))
    print(f"  {len(F):,} forms, {n_mn:,} mnemonic candidates across {len(LANGS)} languages, {len(F)-n_mn} plain phrases")
    return bool(ok)


if __name__ == "__main__":
    print(len(forms()), "forms; selftest", selftest())
