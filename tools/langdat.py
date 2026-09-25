# -*- coding: utf-8 -*-
r"""테마파크 DS 언어 텍스트(LANG0-*.DAT · advice0‥3-*.DAT · credits-*.DAT) 읽기·쓰기.

형식: u16 묶음 수 N · u16 묶음별 줄 수 ×N · 그 뒤로 NUL 로 끝나는 UTF-8 문자열이 차례로(오프셋 표 없음).
  LANG0 N=25, advice N=7, credits N=1.
  python tools/langdat.py dump      # work/text/<이름>.tsv (키 = COD 식별자, EN, JP)
"""
import os, struct, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROM = r'C:/claude/roms/nds/Theme Park DS.nds'
BASES = ['LANG0', 'advice0', 'advice1', 'advice2', 'advice3', 'credits']


def parse(d):
    n = struct.unpack_from('<H', d, 0)[0]
    counts = list(struct.unpack_from('<%dH' % n, d, 2))
    p = 2 + 2 * n
    groups = []
    for c in counts:
        g = []
        for _ in range(c):
            e = d.index(b'\0', p)
            g.append(d[p:e].decode('utf-8'))
            p = e + 1
        groups.append(g)
    assert p == len(d) or not d[p:].strip(b'\0'), ('꼬리 남음', len(d) - p)
    return groups


def build(groups):
    out = struct.pack('<H', len(groups)) + struct.pack('<%dH' % len(groups), *[len(g) for g in groups])
    for g in groups:
        for s in g:
            out += s.encode('utf-8') + b'\0'
    return out


def dump():
    import ndspy.rom
    r = ndspy.rom.NintendoDSRom.fromFile(ROM)
    os.makedirs(os.path.join(ROOT, 'work', 'text'), exist_ok=True)
    tot = 0
    for b in BASES:
        L = {lg: parse(bytes(r.getFileByName('DATA/%s-%s.DAT' % (b, lg)))) for lg in ('COD', 'EN', 'JP')}
        for lg in ('EN', 'JP'):
            assert build(L[lg]) == bytes(r.getFileByName('DATA/%s-%s.DAT' % (b, lg))), '왕복 실패 %s %s' % (b, lg)
        esc = lambda s: s.replace('\\', '\\\\').replace('\n', '\\n').replace('\t', '\\t')
        rows = []
        for gi, g in enumerate(L['EN']):
            cod = L['COD'][gi] if gi < len(L['COD']) else []
            for i, s in enumerate(g):
                key = cod[i] if i < len(cod) else ''
                jp = L['JP'][gi][i] if gi < len(L['JP']) and i < len(L['JP'][gi]) else ''
                rows.append('%d\t%d\t%s\t%s\t%s\t' % (gi, i, key, esc(s), esc(jp)))
        with open(os.path.join(ROOT, 'work', 'text', b + '.tsv'), 'w', encoding='utf-8') as f:
            f.write('#묶음\t번호\t식별자\tEN\tJP\tKO\n' + '\n'.join(rows) + '\n')
        n = len(rows)
        en = sum(len(s) for g in L['EN'] for s in g)
        print('%-8s 묶음 %2d · 줄 %4d · EN %6d자 · JP %6d자 · 묶음수 EN/JP/COD 일치 %s' % (
            b, len(L['EN']), n, en, sum(len(s) for g in L['JP'] for s in g),
            [len(g) for g in L['EN']] == [len(g) for g in L['JP']] == [len(g) for g in L['COD']]))
        tot += n
    print('합계 줄', tot)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    dump()
