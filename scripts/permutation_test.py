# -*- coding: utf-8 -*-
"""영역 쌍 겹침의 순열검정 — 논문 표 7 재산출 (표준 라이브러리만)
실행: python3 scripts/permutation_test.py

귀무모형: 각 인물의 활동 영역 '개수'와 영역별 인물 수(행정 72·경제 87·언론 38·동원 54)를
보존한 채, 어떤 영역인가만 영역 규모에 비례해 무작위로 재추첨한다(2,000회, 고정 시드 42).
관측 겹침이 이 기댓값을 유의하게 넘는 쌍이 있는지 검정한다.

아울러 7장의 민족 간 비율 차이(적대적 국면 노출, 발기인)에 대한 Fisher 정확검정을 함께 산출한다.
"""
import csv, os, random, collections
from math import lgamma, exp

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
D, A = os.path.join(ROOT, 'data'), os.path.join(ROOT, 'aggregates')
def load(p): return list(csv.DictReader(open(p, encoding='utf-8-sig')))

# ── 표 7. 영역 쌍 겹침의 순열검정 ─────────────────────────────
idx = load(f'{A}/집계_겸직지표_v4_20260812.csv')
dm = {r['인물']: set(x.strip() for x in r['영역'].split('·') if x.strip()) for r in idx}
DOM = ['행정', '경제', '언론', '동원']
nd = {d: sum(1 for p in dm if d in dm[p]) for d in DOM}
pairs = [('언론','동원'), ('행정','언론'), ('행정','동원'), ('경제','언론'), ('행정','경제'), ('경제','동원')]
obs = {(a,b): sum(1 for p in dm if a in dm[p] and b in dm[p]) for a,b in pairs}

random.seed(42)
counts = [len(dm[p]) for p in dm if dm[p]]
sim_res = {pr: [] for pr in pairs}
NSIM = 2000
for _ in range(NSIM):
    poolc = collections.Counter({d: nd[d] for d in DOM})
    ov = collections.Counter(); ok = True
    for k in sorted(counts, reverse=True):
        doms = []
        for _ in range(k):
            avail = [d for d in DOM if poolc[d] > 0 and d not in doms]
            if not avail: ok = False; break
            c = random.choices(avail, weights=[poolc[d] for d in avail])[0]
            doms.append(c); poolc[c] -= 1
        if not ok: break
        s = set(doms)
        for a,b in pairs:
            if a in s and b in s: ov[(a,b)] += 1
    if not ok: continue
    for pr in pairs: sim_res[pr].append(ov[pr])

print(f'=== 표 7. 영역 쌍 겹침 — 관측 vs 순열 기댓값 (유효 {len(sim_res[pairs[0]])}회) ===')
print('영역별 인물 수:', {d: nd[d] for d in DOM},
      '/ 영역 보유 인물', sum(1 for p in dm if dm[p]), '명')
for pr in sorted(pairs, key=lambda x: -obs[x]):
    sims = sim_res[pr]; m = sum(sims)/len(sims)
    hi = sum(1 for s in sims if s >= obs[pr]) / len(sims)
    lo = sum(1 for s in sims if s <= obs[pr]) / len(sims)
    print(f'{pr[0]}∩{pr[1]}: 관측 {obs[pr]:2d} | 기댓값 {m:5.1f} | p(관측 이상) {hi:.3f} | p(관측 이하) {lo:.3f}')

# ── 겸직 집중도 (6.3절 서술 수치) ────────────────────────────
kcnt = collections.Counter(len(dm[p]) for p in dm)
print('\n=== 겸직 집중도 ===')
print(f'영역 1개 이상 {sum(v for k,v in kcnt.items() if k>=1)}명 / 2개 이상 {sum(v for k,v in kcnt.items() if k>=2)}명 '
      f'/ 3개 이상 {sum(v for k,v in kcnt.items() if k>=3)}명 / 4개 {kcnt[4]}명')
for d in DOM:
    mem = [p for p in dm if d in dm[p]]
    single = sum(1 for p in mem if len(dm[p]) == 1)
    print(f'{d}: {len(mem)}명 중 단영역 {single}명({single/len(mem)*100:.0f}%) · 다영역 {len(mem)-single}명({(len(mem)-single)/len(mem)*100:.0f}%)')

# ── 7장. Fisher 정확검정 ─────────────────────────────────────
def logC(n, k): return lgamma(n+1) - lgamma(k+1) - lgamma(n-k+1)
def fisher_onesided(a, b, c, d):
    """P(X >= a) — 2x2 [[a,b],[c,d]], 초기하 분포"""
    n = a+b+c+d; p = 0.0
    for x in range(a, min(a+b, a+c)+1):
        p += exp(logC(a+b, x) + logC(c+d, (a+c)-x) - logC(n, a+c))
    return p

ep = load(f'{D}/사건참여표_v3_20260728.csv')
ev = {e['event_id']: e for e in load(f'{D}/사건레지스트리_v3_20260728.csv')}
attr = {r['한글표기']: r['민족'] for r in load(f'{D}/인물속성_테이블_v2.csv')}
JP = [r for r in ep if attr.get(r['인물']) == '일본인']
KO = [r for r in ep if attr.get(r['인물']) == '조선인']
HOST = {'중재·교섭', '집단운동·대회', '청원'}
hk = sum(1 for r in KO if r['역할'] == '당사자·대상' and ev[r['event_id']]['사건유형'] in HOST)
hj = sum(1 for r in JP if r['역할'] == '당사자·대상' and ev[r['event_id']]['사건유형'] in HOST)
fk = sum(1 for r in KO if r['역할'] == '발기인')
fj = sum(1 for r in JP if r['역할'] == '발기인')

print('\n=== 7장. Fisher 정확검정 (단측) ===')
p1 = fisher_onesided(hk, len(KO)-hk, hj, len(JP)-hj)
print(f'적대적 국면 노출: 조선인 {hk}/{len(KO)}({hk/len(KO)*100:.1f}%) vs 일본인 {hj}/{len(JP)}({hj/len(JP)*100:.1f}%) → p = {p1:.4f}')
p2 = fisher_onesided(fj, len(JP)-fj, fk, len(KO)-fk)  # 일본인 쪽 과다 = 조선인 쪽 과소
print(f'발기인: 조선인 {fk}/{len(KO)}({fk/len(KO)*100:.1f}%) vs 일본인 {fj}/{len(JP)}({fj/len(JP)*100:.1f}%) → p = {p2:.4f}')
