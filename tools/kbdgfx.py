# -*- coding: utf-8 -*-
r"""이름 입력 자판 그림(DATA/fs_chat_keyboard_jp.NCGR, 256×96 8bpp, 타일 32열 순서대로) — 왼쪽 버튼 글자.

실측(2026-09-25): 바탕 색 20 · 글자 색 22(테두리 선도 22 — 버튼 안쪽만 건드린다).
  かな → 한글1 · カナ → 한글2 (갈무리7, 원래 글자 자리 7행)
  ゛ · ゜ · 小字 → 빈칸(글자만 지움. 한글 글자에는 변환이 먹지 않아 눌러도 아무 일 없음)
"""
import os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bdf

GALMURI7 = 'C:/claude/utils/font/Galmuri-v2.40.3/Galmuri7.bdf'
NAME = 'DATA/fs_chat_keyboard_jp.NCGR'
W, H = 256, 96
BG, FG = 20, 22
# (지울 영역 x0,y0,x1,y1 끝 포함, 새 글자, 글자 윗줄)
BUTTONS = [
    ((5, 6, 23, 18), '한글1', 9),
    ((5, 22, 23, 33), '한글2', 25),
    ((4, 40, 25, 54), None, 0),
    ((4, 58, 25, 72), None, 0),
    ((4, 76, 25, 90), None, 0),
]


# 갈무리7 «2»는 폭 4 → 버튼(19px)에 «한글2»가 1px 넘친다: 폭 3 짜리로 직접(7행, 갈무리 숫자와 같은 2‥8행)
NARROW = {'2': ['##.', '..#', '..#', '.#.', '#..', '#..', '###']}   # ⛔ ### ..# ###… 꼴은 «ㄹ» 로 보인다


def text_bits(text, G, asc):
    cols = []
    for k, ch in enumerate(text):
        if ch in NARROW:
            g = NARROW[ch]
            arr = [[0] * 12 for _ in range(12)]
            for y, row in enumerate(g):
                for x, c in enumerate(row):
                    arr[2 + y][x] = int(c == '#')
        else:
            arr, adv = bdf.render(G, asc, ord(ch), 12, 12, asc)
        xs = [x for row in arr for x, v in enumerate(row) if v]
        x0, x1 = min(xs), max(xs)
        if k:
            cols.append([0] * 12)
        for x in range(x0, x1 + 1):
            cols.append([arr[y][x] for y in range(12)])
    rows = [y for y in range(12) if any(c[y] for c in cols)]
    return [[c[y] for c in cols] for y in range(rows[0], rows[-1] + 1)]


def build(ncgr):
    i = ncgr.index(b'RAHC')
    sz = struct.unpack_from('<I', ncgr, i + 0x18)[0]
    data = bytearray(ncgr[i + 0x20:i + 0x20 + sz])
    px = lambda x, y: (y // 8 * 32 + x // 8) * 64 + (y % 8) * 8 + x % 8
    G, asc = bdf.load(GALMURI7)
    for (x0, y0, x1, y1), text, top in BUTTONS:
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if data[px(x, y)] == FG:
                    data[px(x, y)] = BG
        if text:
            b = text_bits(text, G, asc)
            h, w = len(b), len(b[0])
            assert w <= x1 - x0 + 1, '%s 폭 %d > %d' % (text, w, x1 - x0 + 1)
            ox = x0 + (x1 - x0 + 1 - w) // 2
            for y in range(h):
                for x in range(w):
                    if b[y][x]:
                        data[px(ox + x, top + y)] = FG
    return ncgr[:i + 0x20] + bytes(data) + ncgr[i + 0x20 + sz:]


def apply(r):
    r.setFileByName(NAME, build(bytes(r.getFileByName(NAME))))


if __name__ == '__main__':
    import ndspy.rom
    from PIL import Image
    r = ndspy.rom.NintendoDSRom.fromFile('C:/claude/roms/nds/Theme Park DS.nds')
    pal = bytes(r.getFileByName('DATA/fs_keyboardColor.NCLR'))
    pd = pal[pal.index(b'TTLP') + 0x18:]
    rgb = [((c & 31) << 3, ((c >> 5) & 31) << 3, ((c >> 10) & 31) << 3) for c in (struct.unpack_from('<H', pd, 2 * k)[0] for k in range(256))]
    ims = []
    for d in (bytes(r.getFileByName(NAME)), build(bytes(r.getFileByName(NAME)))):
        i = d.index(b'RAHC'); data = d[i + 0x20:]
        im = Image.new('RGB', (40, H))
        for y in range(H):
            for x in range(40):
                im.putpixel((x, y), rgb[data[(y // 8 * 32 + x // 8) * 64 + (y % 8) * 8 + x % 8]])
        ims.append(im)
    out = Image.new('RGB', (84, H), (0, 0, 0)); out.paste(ims[0], (0, 0)); out.paste(ims[1], (44, 0))
    p = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(HERE), 'my files', '그래픽', '01_자판버튼(왼원본_오른한글).png')
    os.makedirs(os.path.dirname(p), exist_ok=True)
    out.resize((84 * 6, H * 6), Image.NEAREST).save(p)
    print('저장', p)
