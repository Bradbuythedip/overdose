"""Map per-glyph stroke widths (from p79_strokes.py) onto transcript characters by monospace pitch."""
import json,sys
S='/tmp/claude-0/-home-user-overdose/c95379e1-4acd-5742-a1a9-2a7a29aef63b/scratchpad/p79/'
res=json.load(open(S+'strokes.json'))
lines=[l.rstrip('\n') for l in open('article_transcript.txt',encoding='utf-8')][150:]
lines=[l for l in lines if l.strip() and not l.startswith('MAX')]
assert len(lines)==25, len(lines)
out={}
for i in range(1,26):
    txt=lines[i-1]
    comps=res[str(i)]
    # nonspace char indices
    idx=[k for k,ch in enumerate(txt) if ch!=' ']
    xs=[c['xc'] for c in comps]
    # pitch from first and last glyph; the em-dash may be one glyph
    first,last=idx[0],idx[-1]
    pitch=(xs[-1]-xs[0])/(last-first)
    row=[]
    used={}
    for c in comps:
        slot=first+round((c['xc']-xs[0])/pitch)
        ch=txt[slot] if 0<=slot<len(txt) else '?'
        row.append((slot,ch,c['w'],c['h']))
    out[i]={'text':txt,'pitch':round(pitch,3),'n_glyphs':len(comps),'n_chars':len(idx),'glyphs':row}
    flag='' if len(comps)==len(idx) else '  <-- glyph count %d vs chars %d'%(len(comps),len(idx))
    print('L%02d pitch=%.2f%s'%(i,pitch,flag))
    print('   '+' '.join('%s%s'%(ch, ('B' if w>=3.6 else ('?' if w>=3.05 else '.'))) for s,ch,w,h in row))
    print('   '+' '.join('%.1f'%w for s,ch,w,h in row))
json.dump(out,open(S+'mapped.json','w'),indent=0)
