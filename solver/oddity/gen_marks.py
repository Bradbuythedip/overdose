#!/usr/bin/env python3
"""The two typographic marks the transcript does not record:
  UNDERLINE  p75: "They discount stuff in advance."
  STRIKE     p76: "(and 10years of watching Peter Schiff miss buying bitcoin"
                  -- stops at the line break, mid-clause.
Both sit on the piece's most anomalous spots.  Nothing in this repo has ever
used them: bold and highlight were catalogued, rules were not."""
import re, itertools
UL = "They discount stuff in advance."
ST = "(and 10years of watching Peter Schiff miss buying bitcoin"
REST = "since I started honey-badgering him to buy some at $1 back in 2011)"
out=[]
def add(*xs):
    for x in xs:
        if not x: continue
        x=x.strip()
        if 2<len(x)<4000: out.append(x)
def addv(*xs):
    for s in xs:
        if not s: continue
        w=[x for x in re.split(r'[\s]+', s) if x]
        add(s, s.lower(), s.upper(), s.rstrip('.'), s.strip('()'),
            ''.join(w), ''.join(w).lower(), ''.join(w).upper(),
            ' '.join(w[::-1]), s[::-1], s.lower()[::-1],
            re.sub(r'[^A-Za-z0-9]','',s), re.sub(r'[^A-Za-z0-9]','',s).lower(),
            ''.join(x[0] for x in w), ''.join(x[0] for x in w).lower(),
            ''.join(x.capitalize() for x in w))
for s in (UL, ST, REST, ST+' '+REST, ST.lstrip('('), ST.lstrip('(').rstrip()):
    addv(s)
# both marks together, in printed order and reversed
for sep in ['', ' ', ' | ', ' - ', '. ', '\t']:
    addv(UL+sep+ST); addv(ST+sep+UL)
addv(UL.rstrip('.')+' '+ST.lstrip('('))
# the sentence with the struck run DELETED (the "edited" reading)
FULL = ("Gotta be this way. Forty years of dumb post-1971 fiat money nonsense "
        "(and 10years of watching Peter Schiff miss buying bitcoin since I "
        "started honey-badgering him to buy some at $1 back in 2011) have "
        "dulled shitcoiners' and nocoiners' minds.")
DEL = FULL.replace(ST+' ', '')
addv(DEL); addv(FULL)
addv("Forty years of dumb post-1971 fiat money nonsense since I started "
     "honey-badgering him to buy some at $1 back in 2011) have dulled "
     "shitcoiners' and nocoiners' minds.")
addv("Gotta be this way. Forty years of dumb post-1971 fiat money nonsense "
     "have dulled shitcoiners' and nocoiners' minds.")
# struck words alone, and struck words minus the anomaly
sw = ST.lstrip('(').split()
addv(' '.join(sw)); addv(' '.join(w for w in sw if w!='10years'))
addv(' '.join(sw[1:])); addv(' '.join(sw[:-1]))
for a in range(len(sw)):
    for b in range(a+2, len(sw)+1):
        seg=' '.join(sw[a:b])
        add(seg); add(seg.lower())
# underlined words alone
uw = UL.rstrip('.').split()
for a in range(len(uw)):
    for b in range(a+1, len(uw)+1):
        seg=' '.join(uw[a:b]); add(seg); add(seg.lower()); add(''.join(uw[a:b]).lower())
# the two marks crossed with the flags
for a in [UL.rstrip('.'), 'They discount stuff in advance', 'Theydiscountstuffinadvance']:
    for b in ['10years', 'mEthereum', 'Overdose', 'OVERDOSE', '20 BTC', 'MaxKeiser']:
        add(a+b, a+' '+b, b+a, b+' '+a, (a+b).lower(), (a+b).replace(' ','').lower())
# named marks
addv('underline strikethrough', 'strikethrough underline',
     'underlined struck', 'struck out', 'deleted', 'DELETED',
     'They discount stuff in advance 10years')
seen=set()
for s in out:
    if s not in seen: seen.add(s); print(s)
