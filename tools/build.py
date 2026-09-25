# -*- coding: utf-8 -*-
r"""테마파크 DS 한글판 빌드 — 일본어(JP) 자리를 한국어로.

  python tools/build.py <번역 폴더 work/ko> <출력.nds | --dry>

1) work/ko/*.tsv (파일 · 묶음 · 번호 · KO, `\n` = 줄바꿈) → DATA/<파일>-JP.DAT 의 그 줄을 바꾼다(tools/langdat.py).
2) 글꼴 DATA/fontAll.nftr: 한자 칸(U+4E00‥9FFF 쌍)을 «번역에 쓴 한글 음절»로 갈아 끼운다.
   아직 번역 안 한 일본어 줄이 쓰는 한자는 남긴다(keep). 글꼴 크기 불변.
   한글 = 갈무리9, 11×13 칸에서 일본어 글자와 같은 2‥10행, 전진폭 10.
3) 제스처 → 탭 패치(tools/tapfix.py).
"""
import glob, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import ndspy.rom
import bdf, nftr
import langdat, tapfix, kocheck

ROM = langdat.ROM
GALMURI9 = 'C:/claude/utils/font/Galmuri-v2.40.3/Galmuri9.bdf'
FONT = 'DATA/fontAll.nftr'
TOP, BOTTOM = 2, 10          # 일본어 글자가 쓰는 행(실측: 漢·あ 2‥10)
ADV = 10
LANG_NAME = '한국어'           # 언어 선택 목록의 일본어 자리


def load_ko(folder):
    out = {}
    for fn in sorted(glob.glob(os.path.join(folder, '*.tsv'))):
        for ln in open(fn, encoding='utf-8'):
            if ln.startswith('#') or not ln.strip():
                continue
            f, g, i, ko = ln.rstrip('\n').split('\t')[:4]
            if not ko:
                continue
            key = (f, int(g), int(i))
            assert key not in out, '중복 %s' % (key,)
            out[key] = kocheck.squeeze(ko).replace('\\n', '\n')
    return out


def hangul_glyph(G, asc, ch, f):
    arr, _ = bdf.render(G, asc, ord(ch), f.cw, f.ch, asc)
    rows = [y for y in range(f.ch) if any(arr[y])]
    assert rows, '갈무리9 에 없는 글자 %r' % ch
    shift = (TOP + BOTTOM) // 2 - (rows[0] + rows[-1]) // 2          # 세로 가운데를 일본어 글자 가운데(6행)에
    arr = [arr[y - shift] if 0 <= y - shift < f.ch else [0] * f.cw for y in range(f.ch)]
    xs = [x for row in arr for x, v in enumerate(row) if v]
    bits = ''.join(str(v) for row in arr for v in row)
    bits += '0' * (-len(bits) % 8)
    bm = bytes(int(bits[k:k + 8], 2) for k in range(0, len(bits), 8))
    return bm + bytes(f.tsize - len(bm)), (1, max(xs) + 1, ADV)


def main():
    folder, out = sys.argv[1], sys.argv[2]
    ko = load_ko(folder)
    r = ndspy.rom.NintendoDSRom.fromFile(ROM)
    texts = {}
    for b in langdat.BASES:
        name = 'DATA/%s-JP.DAT' % b
        groups = langdat.parse(bytes(r.getFileByName(name)))
        n = 0
        for (f, g, i), s in ko.items():
            if f == b:
                assert g < len(groups) and i < len(groups[g]), '없는 줄 %s %d %d' % (f, g, i)
                groups[g][i] = s
                n += 1
        texts[b] = groups
        r.setFileByName(name, langdat.build(groups))
        print('  %-8s 바꾼 줄 %d' % (b, n))
    # 언어 선택 목록의 «日本語»(LANG0 10/10)는 «지금 언어의 파일»에서 읽는다 → 모든 언어 파일에서 «한국어»로
    #   (한자 칸을 한글로 바꾸므로 다른 언어에 남은 日本語 는 깨진다)
    for lg in ('EN', 'FR', 'GR', 'ES', 'ITA'):
        name = 'DATA/LANG0-%s.DAT' % lg
        g = langdat.parse(bytes(r.getFileByName(name)))
        assert g[10][10] == '日本語', (lg, g[10][10])
        g[10][10] = LANG_NAME
        r.setFileByName(name, langdat.build(g))
    texts['LANG0'][10][10] = LANG_NAME
    r.setFileByName('DATA/LANG0-JP.DAT', langdat.build(texts['LANG0']))
    alltext = ''.join(s for gs in texts.values() for g in gs for s in g) + LANG_NAME
    syl = sorted({c for c in alltext if 0xAC00 <= ord(c) <= 0xD7A3})
    keep = {c for c in alltext if 0x4E00 <= ord(c) <= 0x9FFF}
    f = nftr.Nftr(bytes(r.getFileByName(FONT)))
    old = len(bytes(r.getFileByName(FONT)))
    G, asc = bdf.load(GALMURI9)
    items = [(ord(c),) + hangul_glyph(G, asc, c, f) for c in syl]
    nftr.replace_kanji(f, items, keep=keep)
    fb = f.build()
    assert len(fb) == old, ('글꼴 크기 바뀜', old, len(fb))
    r.setFileByName(FONT, fb)
    print('  글꼴: 한글 %d자 → 한자 칸(남긴 한자 %d)' % (len(syl), len(keep)))
    data = tapfix.patch(r.save())
    if out == '--dry':
        print('예행 끝(파일 안 씀)')
        return
    open(out, 'wb').write(data)
    import hashlib
    print('완료 %s md5 %s' % (out, hashlib.md5(data).hexdigest()))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
