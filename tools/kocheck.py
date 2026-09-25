# -*- coding: utf-8 -*-
r"""번역 검사 — «쓰는 순간» 돌린다. 빌더(build.py)도 squeeze() 를 거쳐 넣는다.

  python tools/kocheck.py            # work/ko/*.tsv 전부
  python tools/kocheck.py 파일.tsv    # 한 파일

번역 파일 형식: 파일(LANG0|advice0‥3|credits) · 묶음 · 번호 · KO  (`\n` = 줄바꿈, `<P>` = 쪽 넘김)
work/text/*.tsv 를 그대로 복사해 KO 열(6번째)을 채워도 된다(열 수로 알아본다).

막는 것(오류):
  - 제어·자리표시 불일치: %s %d <1> <2> <P> ＠＠＠＠ 의 개수가 원문(JP)과 다름
  - 줄 폭 초과: `\n`/<P> 로 나뉜 한 줄이 22칸(220px) 넘음 — 한글·전각 = 10px, 반각 = 5px(글꼴 실측), 공백 = 4px 로 계산
  - 쪽당 4줄 이상(대사창 3줄)
  - 번역 안의 일본어 가나·한자(빠뜨린 곳)
경고:
  - 원문엔 `\n` 이 있는데 번역엔 없는 30칸 넘는 줄(자동 줄바꿈이 낱말을 자를 수 있음 — PoC 1 실기로 확인 예정)
규칙(자동 적용): 문장부호(, . ! ? : ;) 뒤 공백은 지운다 — squeeze().
"""
import glob, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOX = 220          # 대사창 한 줄 px (전각 22자)
LINES = 3
TOKENS = re.compile(r'%[0-9]*[sdc]|<\d>|<P>|＠＠＠＠')
KANA_KANJI = re.compile(r'[぀-ヿ一-鿿]')


def squeeze(s):
    """문장부호 뒤 공백 제거(전프로젝트 규칙). 숫자 사이 마침표(1.5)·줄임표는 그대로."""
    return re.sub(r'([,.!?:;])[ ]+(?=\S)', r'\1', s)


def px(seg):
    w = 0
    for c in seg:
        o = ord(c)
        if c == ' ':
            w += 4
        elif o < 0x80 or 0xFF61 <= o <= 0xFF9F:
            w += 5
        else:
            w += 10
    return w


def source():
    src = {}
    for fn in glob.glob(os.path.join(ROOT, 'work', 'text', '*.tsv')):
        b = os.path.basename(fn)[:-4]
        for ln in open(fn, encoding='utf-8'):
            if ln.startswith('#'):
                continue
            r = ln.rstrip('\n').split('\t')
            src[(b, int(r[0]), int(r[1]))] = r
    return src


def rows(fn):
    base = os.path.basename(fn)[:-4]
    for n, ln in enumerate(open(fn, encoding='utf-8'), 1):
        if ln.startswith('#') or not ln.strip():
            continue
        r = ln.rstrip('\n').split('\t')
        if len(r) >= 6 and r[0].isdigit():            # work/text 복사본: 묶음·번호·식별자·EN·JP·KO
            yield n, (base, int(r[0]), int(r[1])), r[5]
        else:
            yield n, (r[0], int(r[1]), int(r[2])), r[3] if len(r) > 3 else ''


def check(fn, src):
    err, warn, done = [], [], 0
    for n, key, ko in rows(fn):
        if not ko:
            continue
        done += 1
        ko = squeeze(ko)
        where = '%s:%d %s/%d/%d' % (os.path.basename(fn), n, *key)
        s = src.get(key)
        if not s:
            err.append('%s 원문에 없는 줄' % where)
            continue
        jp = s[4]
        if sorted(TOKENS.findall(jp)) != sorted(TOKENS.findall(ko)):
            err.append('%s 제어 불일치 JP%s KO%s' % (where, TOKENS.findall(jp), TOKENS.findall(ko)))
        if KANA_KANJI.search(TOKENS.sub('', ko)):
            err.append('%s 일본어 남음: %s' % (where, ko[:40]))
        for page in ko.split('<P>'):
            lines = page.split('\\n')
            if len(lines) > LINES:
                err.append('%s 쪽당 %d줄(최대 %d): %s' % (where, len(lines), LINES, page[:30]))
            for seg in lines:
                w = px(TOKENS.sub('', seg))
                if w > BOX:
                    err.append('%s 줄 폭 %dpx > %d: %s' % (where, w, BOX, seg))
                elif w > 300 and '\\n' in jp:
                    warn.append('%s 긴 줄(자동 줄바꿈 의존) %dpx: %s' % (where, w, seg[:30]))
    return err, warn, done


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    src = source()
    files = sys.argv[1:] or sorted(glob.glob(os.path.join(ROOT, 'work', 'ko', '*.tsv')))
    E = W = D = 0
    for fn in files:
        e, w, d = check(fn, src)
        for x in e:
            print('⛔', x)
        for x in w:
            print('⚠', x)
        E += len(e); W += len(w); D += d
    print('번역 %d줄 · 오류 %d · 경고 %d' % (D, E, W))
    sys.exit(1 if E else 0)
