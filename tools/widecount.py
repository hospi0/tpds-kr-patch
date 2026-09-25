# -*- coding: utf-8 -*-
"""대사창 폭(220px)을 넘는 한국어 줄 — 원문도 넓어서 검사기가 허용한 줄(자동 줄바꿈·다른 칸 의존) 목록"""
import collections, glob, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kocheck

SPLIT = re.compile(r'<P>|\\n')

if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    src = kocheck.source()
    ex = []
    for fn in sorted(glob.glob(os.path.join(kocheck.ROOT, 'work', 'ko', '*.tsv'))):
        for n, key, ko in kocheck.rows(fn):
            if not ko:
                continue
            for seg in SPLIT.split(kocheck.squeeze(ko)):
                w = kocheck.px(kocheck.TOKENS.sub('', seg))
                if w > kocheck.BOX:
                    ex.append((key, w, src[key][2].strip(), seg))
    print('220px 넘는 한국어 줄 %d' % len(ex))
    print(collections.Counter((k[0], k[1]) for k, *_ in ex).most_common(20))
    for k, w, cid, seg in ex[:int(sys.argv[1]) if len(sys.argv) > 1 else 15]:
        print('%s/%d/%d %dpx %s | %s' % (k[0], k[1], k[2], w, cid, seg[:50]))
