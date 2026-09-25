# -*- coding: utf-8 -*-
r"""테마파크 DS — 동그라미/V 제스처 선택을 «탭»으로도 되게 하는 ARM9 패치.

제스처 판정 함수 0x2084E2C (펜을 뗄 때):
  0x2085014 bl  0x2084D0C        ; 획 테두리 상자 대각선^2
  0x2085018 cmp r0, #0xE1        ; 225(≈15px) 이하 = 탭
  0x208501C movgt r4, #1         ; 크면 제스처 인식으로
  0x2085020 movle fp, #1         ; 탭이면 버퍼만 비우고 끝  ← 여기를 «탭 → 동그라미 처리»로
동그라미 처리 = 0x2085178: 중심(0x2084D94) → 0x2041948(cx,cy,0) → 0x2041948(cx,cy,1) → sl=1
  → 0x20851BC 에서 fp!=0 이면 버퍼 비움.

빈 자리: 0x2085054~0x20850D0 의 «sb=0/1/2 세 벌 똑같은 블록»을 한 벌(값 = sb+1)로 줄여 0x208507C~ 를 비운다.
  python tools/tapfix.py <원본.nds> <출력.nds>
"""
import sys
import keystone

BASE = 0x2000000
ks = keystone.Ks(keystone.KS_ARCH_ARM, keystone.KS_MODE_ARM)


def asm(addr, src):
    b, _ = ks.asm(src, addr)
    return bytes(b)


ORIG_BLOCK = bytes.fromhex(  # 0x2085054 ~ 0x20850D4 (32 워드) — 원본 확인용 앞부분
    '000059e3')                # cmp sb, #0

COMPACT = '''
ldr r0, [r5, #0x14]
str r0, [sp, #0x20]
add r0, sb, #1
str r0, [sp, #0x24]
ldr r1, [r4]
mov r0, #0xc
mla r0, r1, r0, r8
ldr r0, [r0, sb, lsl #2]
str r0, [sp, #0x28]
b 0x20850d4
'''
TRAMP = 0x208507C
TRAMP_SRC = '''
mov fp, #1
b 0x2085178
'''


def patch(rom):
    a = bytearray(rom)
    arm9_off = int.from_bytes(a[0x20:0x24], 'little')
    o = lambda addr: arm9_off + addr - BASE
    assert a[o(0x2085054):o(0x2085058)] == ORIG_BLOCK, '원본 블록 다름'
    assert a[o(0x2085020):o(0x2085024)] == asm(0x2085020, 'movle fp, #1'), '0x2085020 원본 다름'
    assert a[o(0x2085178):o(0x208517C)] == asm(0x2085178, 'add r0, sp, #0x14'), '동그라미 처리 시작 다름'
    c = asm(0x2085054, COMPACT)
    assert 0x2085054 + len(c) <= TRAMP
    t = asm(TRAMP, TRAMP_SRC)
    assert TRAMP + len(t) <= 0x20850D4
    a[o(0x2085054):o(0x20850D4)] = c + b'\0' * (TRAMP - 0x2085054 - len(c)) + t + b'\0' * (0x20850D4 - TRAMP - len(t))
    a[o(0x2085020):o(0x2085024)] = asm(0x2085020, 'ble 0x%x' % TRAMP)
    return bytes(a)


if __name__ == '__main__':
    src, dst = sys.argv[1], sys.argv[2]
    open(dst, 'wb').write(patch(open(src, 'rb').read()))
    print('ok', dst)
