# -*- coding: utf-8 -*-
r"""이름 입력 가나 자판(DATA/jp_*.kbdmap) → 한글 음절.

형식: FFFE + UTF-16 51자. 화면은 세로 5칸씩 열(あいうえお / かきくけこ …), や·わ 열은 3칸 + 부호.
가나 칸(46)만 바꾸고 부호 ！？、。ー 는 제자리에 둔다.

  かな   = 오십음 자리 그대로: ㅇㄱㅅㄷㄴㅎㅁ × ㅏㅣㅡㅔㅗ · 야유요 · ㄹ × ㅏㅣㅡㅔㅗ · 와워은
  カナ   = 같은 자음 × ㅓㅜㅐㅕㅠ
  ゛     = 거센·된소리(ㅂㅋㅈㅌㅍㅊㄲ + ㄸ·ㅃ·ㅆ)  — かな 쪽은 ㅏㅣㅡㅔㅗ, カナ 쪽은 ㅓㅜㅐㅕㅠ
  ゜·小字 = 받침 있는 흔한 음절(BATCHIM, ㄱㄴㄷ 순)
"""
import os, sys

CHO = 'ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ'
JUNG = 'ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ'


def syl(c, v, jong=0):
    return chr(0xAC00 + (CHO.index(c) * 21 + JUNG.index(v)) * 28 + jong)


def grid(cons, vows):
    return [syl(c, v) for c in cons for v in vows]


A = 'ㅏㅣㅡㅔㅗ'
O = 'ㅓㅜㅐㅕㅠ'
# 쪽마다 46칸: 7열×5 + や열 3 + ら열 5 + わ열 3
PAGES = {
    'jp_hiragana': grid('ㅇㄱㅅㄷㄴㅎㅁ', A) + list('야유요') + grid('ㄹ', A) + list('와워피'),   # «은» 자리 → «피»(하스피)
    'jp_katakana': list('어우애여얘') + grid('ㄱㅅㄷㄴㅎㅁ', O) + list('예의왜') + grid('ㄹ', O) + list('위외웨'),   # ㅇ 열 «유» 는 かな 야유요 와 겹쳐 «얘»
    'jp_dakuten': grid('ㅂㅋㅈㅌㅍㅊㄲ', A) + list('따띠또') + grid('ㅃ', A) + list('싸씨쏘'),
    'jp_katakana_dakuten': grid('ㅂㅋㅈㅌㅍㅊㄲ', O) + list('떠뚜때') + grid('ㅃ', O) + list('써쑤쌔'),
}
BATCHIM = ('각 간 갈 감 강 개 객 건 걸 검 겸 결 경 곡 곤 골 공 관 광 국 군 굴 궁 권 귤 근 금 급 긍 길 김 깅 꽃 꿈 '
           '낙 난 날 남 낭 년 념 녕 논 농 눈 늘 님 '
           '단 달 담 당 덕 돈 돌 동 둘 득 들 등 딸 땅 똘 '
           '락 란 랄 람 랑 량 련 렬 령 록 론 롱 룡 룬 률 륭 른 름 릉 린 림 립 링 '
           '막 만 말 맘 망 맹 멍 면 명 목 몽 묵 문 물 민 밀 '
           '박 반 발 밤 방 백 번 범 법 벽 변 별 병 복 본 봄 봉 분 불 붕 빈 빛 빙 '
           '산 살 삼 상 생 석 선 설 섬 섭 성 속 손 솔 송 숙 순 술 숭 슬 승 식 신 실 심 쌍 '
           '악 안 알 암 앙 약 양 억 언 얼 엄 업 연 열 염 엽 영 옥 온 올 옹 완 왕 욕 용 욱 운 울 웅 원 월 윤 율 융 은 을 음 응 익 인 일 임 입 잉 '
           '작 잔 장 적 전 절 점 정 존 종 준 중 즉 증 직 진 질 짐 집 징 '
           '찬 참 창 책 천 철 첨 청 촌 총 춘 충 측 층 칠 침 칭 '
           '탁 탄 탐 탑 탕 택 톤 통 판 팔 팡 편 평 폭 품 풍 필 핑 '
           '학 한 할 함 합 항 행 향 헌 혁 현 협 형 혜 혼 홍 환 활 황 훈 훤 휘 흥 희 힘').split()


# 이름에 흔한 받침 음절 — 먼저 넣는다
NAME = ('한 민 진 준 현 영 정 성 은 연 원 윤 용 철 석 상 동 명 종 경 승 훈 혁 빈 선 인 근 순 숙 란 린 설 별 빛 솔 '
        '결 률 름 강 광 국 군 권 길 김 남 단 덕 란 력 록 룡 만 문 범 박 반 방 백 병 봉 산 신 실 심 안 양 언 엄 옥 완 왕 '
        '욱 운 웅 월 율 융 일 임 장 전 절 점 준 중 지 찬 창 천 청 춘 충 탁 태 택 필 학 함 항 행 향 헌 형 혜 홍 환 활 황 흥 희').split()


def score_rest(rest):
    """받침 음절 고르기: 이름 목록 순위 → 번역문 빈도 → 가나다"""
    import glob
    freq = {}
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for fn in glob.glob(os.path.join(root, 'work', 'ko', '*.tsv')):
        for c in open(fn, encoding='utf-8').read():
            freq[c] = freq.get(c, 0) + 1
    rank = {s: i for i, s in enumerate(NAME)}
    return sorted(rest, key=lambda s: (rank.get(s, 10 ** 6), -freq.get(s, 0), s))


def pages():
    used = [s for p in PAGES.values() for s in p]
    has_jong = lambda s: (ord(s) - 0xAC00) % 28 != 0
    pool = [s for s in dict.fromkeys(NAME + BATCHIM) if s not in used and (has_jong(s) or s in NAME)]
    rest = sorted(score_rest(pool)[:46 * 4])                  # 184개 고른 뒤 가나다순으로 늘어놓는다
    out = dict(PAGES)
    for k, name in enumerate(('jp_handaku', 'jp_small', 'jp_katakana_handaku', 'jp_katakana_small')):
        chunk = rest[46 * k:46 * (k + 1)]
        assert len(chunk) == 46, (name, len(chunk))
        out[name] = chunk
    for name, p in out.items():
        assert len(p) == 46, (name, len(p))
    allsyl = [s for n, p in out.items() if n in USED for s in p]   # 쓰는 두 쪽 안에서만 중복 검사
    assert len(allsyl) == len(set(allsyl)), '자판 음절 중복'
    return out


def is_kana(c):
    return 0x3040 <= ord(c) <= 0x30FF and c != 'ー'


# 가나 칸 말고 부호 칸도 바꾸는 쪽: 한글1 의 일본어 쉼표·마침표 → 파·크(파크 이름 — 사용자 지정 2026-09-25)
PUNCT = {'jp_hiragana': {'、': '파', '。': '크'}}


def build(orig, syls, punct=None):
    assert orig[:2] == b'\xff\xfe'
    t = orig[2:].decode('utf-16-le')
    kana = [i for i, c in enumerate(t) if is_kana(c)]
    assert len(kana) == 46, len(kana)
    t = list(t)
    for i, s in zip(kana, syls):
        t[i] = s
    for i, c in enumerate(t):
        if punct and c in punct:
            t[i] = punct[c]
    return b'\xff\xfe' + ''.join(t).encode('utf-16-le')


USED = ('jp_hiragana', 'jp_katakana')   # ⛔ 게임이 불러오는 가나 자판은 이 둘뿐(코드 문자열 실측) — ゛゜小字 는 쪽이 아니라 «방금 친 글자 변환»


def apply(r):
    """ndspy ROM 에 적용(쓰는 두 쪽만) → 쓴 음절 목록"""
    out = []
    for name, syls in pages().items():
        if name not in USED:
            continue
        fn = 'DATA/%s.kbdmap' % name
        d = build(bytes(r.getFileByName(fn)), syls, PUNCT.get(name))
        r.setFileByName(fn, d)
        out += syls + list(PUNCT.get(name, {}).values())
    return out


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    P = pages()
    rest_total = len([s for s in dict.fromkeys(BATCHIM)])
    print('받침 목록 %d개(중복 제거), 자판 쓰는 수 %d' % (rest_total, sum(len(p) for p in P.values())))
    for name, p in P.items():
        cols = [p[0:5], p[5:10], p[10:15], p[15:20], p[20:25], p[25:30], p[30:35], p[35:38], p[38:43], p[43:46]]
        print('%-22s %s' % (name, ' '.join(''.join(c) for c in cols)))
