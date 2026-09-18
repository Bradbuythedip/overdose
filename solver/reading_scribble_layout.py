#!/usr/bin/env python3
"""The scribbled pull-quote's own four-line layout on p78 read by its edges (first/last words, initials, alternate lines, reversed, counts)."""
F = {'first_words': 'The love more hate', 'last_words': 'of infinitely than war.', 'initials': 'Tlmh', 'finals': 'fynr', 'alt_lines_0': 'The economy of more efficient than', 'alt_lines_1': 'love is infinitely hate and war.', 'rev_lines': 'hate and war. more efficient than love is infinitely The economy of', 'body_alt': 'love is infinitely more efficient than hate and war.', 'body_first': 'our love', 'second_words': 'economy is efficient and', 'word_counts': '3333', 'char_counts': '14 18 19 13'}
def forms():
    out = []
    for k, v in F.items():
        out += [(k, v), (k + "/lower", v.lower()), (k + "/upper", v.upper())]
    seen, uniq = set(), []
    for t, v in out:
        if v not in seen: seen.add(v); uniq.append((t, v))
    return uniq
def selftest():
    return len(forms()) > 20
if __name__ == "__main__":
    print(len(forms()), "forms; selftest", selftest())
