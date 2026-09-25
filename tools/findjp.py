# -*- coding: utf-8 -*-
"""화면 문구가 어느 텍스트 줄인지 찾기: python tools/findjp.py 문구 [문구…]  (work/text/*.tsv 의 JP 열)"""
import glob, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def rows():
    for fn in sorted(glob.glob(os.path.join(ROOT, 'work', 'text', '*.tsv'))):
        for l in open(fn, encoding='utf-8'):
            if l.startswith('#'):
                continue
            r = l.rstrip('\n').split('\t')
            yield os.path.basename(fn)[:-4], r


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    R = list(rows())
    for q in sys.argv[1:]:
        hit = [(n, r[0], r[1], r[2], r[4][:50]) for n, r in R if q in r[4]]
        print('%s\t%d\t%s' % (q, len(hit), hit[:3]))
