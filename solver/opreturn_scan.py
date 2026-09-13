#!/usr/bin/env python3
"""
Scan candidate funding transactions for OP_RETURN payloads.

Replaces the fragile bash one-liner: one API call per tx (not two), retry with
backoff on rate-limit, tolerates malformed/empty responses, decodes payloads to
ASCII, and is resumable.

  # build the txid list from whatever address_check runs you have
  cat *_resolved.tsv | awk -F'\t' '$4>0 && $4<=781000 && $10=="YES" {print $1"\t"$3}' \
      | grep -v '^address' | sort -u > cand_txids.tsv

  python3 opreturn_scan.py --txids cand_txids.tsv --out opreturn_hits.tsv

Also usable as a keyword hunt: --grep keiser,overdose,bukele will flag any
payload containing those strings (case-insensitive) even if it decodes messily.
"""
import argparse, json, os, sys, time, urllib.request, urllib.error

API = "https://blockstream.info/api"


def get(url, tries=6, timeout=30):
    """GET with exponential backoff. Returns parsed JSON or None."""
    for a in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "overdose-solver/1.0"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            # 429 rate limit, 5xx transient
            time.sleep(min(2 ** a, 30))
        except Exception:
            time.sleep(min(2 ** a, 30))
    return None


def decode_payload(hexstr):
    """Best-effort ASCII decode of an OP_RETURN payload."""
    try:
        raw = bytes.fromhex(hexstr)
    except ValueError:
        return "", ""
    ascii_ = "".join(chr(b) if 32 <= b < 127 else "." for b in raw)
    try:
        utf8 = raw.decode("utf-8")
    except UnicodeDecodeError:
        utf8 = ""
    return ascii_, utf8


def extract_opreturns(tx):
    """Return list of (asm, payload_hex) for every OP_RETURN output."""
    out = []
    for v in tx.get("vout", []) or []:
        if v.get("scriptpubkey_type") != "op_return":
            continue
        asm = v.get("scriptpubkey_asm", "") or ""
        # payload is whatever follows OP_RETURN / the pushdata opcode
        payload = ""
        for tok in asm.split():
            if tok.startswith("OP_"):
                continue
            if len(tok) > len(payload):
                payload = tok
        out.append((asm, payload))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--txids", required=True,
                    help="file with txid in a column (address<TAB>txid, or bare txid)")
    ap.add_argument("--out", default="opreturn_hits.tsv")
    ap.add_argument("--api", default=API)
    ap.add_argument("--sleep", type=float, default=0.8,
                    help="blockstream rate-limits hard; 0.8s is safe for a few hundred")
    ap.add_argument("--grep", default="",
                    help="comma-separated keywords to flag inside payloads")
    a = ap.parse_args()

    keywords = [k.strip().lower() for k in a.grep.split(",") if k.strip()]

    # accept "addr<TAB>txid", "txid", or CSV; skip headers and junk
    entries = []
    for line in open(a.txids):
        line = line.strip()
        if not line or line.startswith("#") or line.lower().startswith("address"):
            continue
        parts = [p.strip() for p in line.replace(",", "\t").split("\t") if p.strip()]
        txid = next((p for p in parts if len(p) == 64 and
                     all(c in "0123456789abcdefABCDEF" for c in p)), None)
        if not txid:
            continue
        addr = parts[0] if parts[0] != txid else ""
        entries.append((addr, txid))

    # dedupe on txid, preserve order
    seen, todo = set(), []
    for addr, txid in entries:
        if txid not in seen:
            seen.add(txid)
            todo.append((addr, txid))

    done = set()
    if os.path.exists(a.out):
        for line in open(a.out):
            p = line.split("\t")
            if len(p) > 1:
                done.add(p[1])
        sys.stderr.write(f"resuming: {len(done)} already scanned\n")
    else:
        with open(a.out, "w") as f:
            f.write("address\ttxid\tn_opreturn\tasm\tpayload_hex\tascii\tutf8\tkeyword_hit\n")

    todo = [(ad, tx) for ad, tx in todo if tx not in done]
    sys.stderr.write(f"scanning {len(todo)} unique transactions "
                     f"(sleep={a.sleep}s, ~{len(todo)*a.sleep/60:.1f} min)\n\n")

    out = open(a.out, "a")
    found = failed = 0
    for i, (addr, txid) in enumerate(todo, 1):
        time.sleep(a.sleep)
        tx = get(f"{a.api}/tx/{txid}")
        if tx is None or "vout" not in tx:
            failed += 1
            sys.stderr.write(f"  [{i}/{len(todo)}] {txid[:12]} FETCH FAILED\n")
            continue
        ops = extract_opreturns(tx)
        if not ops:
            continue
        found += 1
        for asm, payload in ops:
            asc, utf8 = decode_payload(payload)
            hit = ""
            blob = (asc + " " + utf8 + " " + payload).lower()
            for k in keywords:
                if k in blob:
                    hit = k
                    break
            out.write(f"{addr}\t{txid}\t{len(ops)}\t{asm}\t{payload}\t{asc}\t{utf8}\t{hit}\n")
            out.flush()
            star = "  *** KEYWORD " + hit.upper() + " ***" if hit else ""
            sys.stderr.write(f"\n*** OP_RETURN  {addr or '(no addr)'}  tx={txid}{star}\n")
            sys.stderr.write(f"    asm:   {asm[:160]}\n")
            sys.stderr.write(f"    ascii: {asc[:160]!r}\n")
            if utf8:
                sys.stderr.write(f"    utf8:  {utf8[:160]!r}\n")
            sys.stderr.flush()
        if i % 25 == 0:
            sys.stderr.write(f"  [{i}/{len(todo)}] {found} with OP_RETURN, {failed} fetch failures\n")
            sys.stderr.flush()

    out.close()
    sys.stderr.write(f"\nDONE. {len(todo)} scanned, {found} had OP_RETURN, "
                     f"{failed} fetch failures -> {a.out}\n")
    if failed:
        sys.stderr.write("re-run the same command to retry the failures (resumable)\n")


if __name__ == "__main__":
    main()
