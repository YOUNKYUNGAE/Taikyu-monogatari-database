# -*- coding: utf-8 -*-
"""재현 패키지 검증 스크립트 — 기계 검증 + 논문 본문 수치 재산출
실행: python3 scripts/verify.py   (표준 라이브러리만 사용)
출력: 검증 항목별 통과/실패와 논문 표(최종본 기준 표 1·4·6~9)의 재계산값
"""
import csv, json, os, re, collections, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
D, A = os.path.join(ROOT,'data'), os.path.join(ROOT,'aggregates')
def load(p): return list(csv.DictReader(open(p, encoding='utf-8-sig')))

org = load(f'{D}/조직레지스트리_v1.4.csv')
ev  = load(f'{D}/사건레지스트리_v3_20260728.csv')
oh  = load(f'{D}/소속직위표_v6_20260809.csv')
ep  = load(f'{D}/사건참여표_v3_20260728.csv')
sec = load(f'{D}/절구분_v4_20260728.csv')
idx = load(f'{A}/집계_겸직지표_v4_20260812.csv')

FAIL = []
def chk(label, cond, got=''):
    print(('  [OK]   ' if cond else '  [FAIL] ') + label + (f'  → {got}' if got else ''))
    if not cond: FAIL.append(label)

def sec_ids(rows, col):
    out = set()
    for r in rows:
        for part in re.split(r'[;,]\s*', r.get(col) or ''):
            part = part.strip()
            if not part: continue
            for x in part.split('~'): out.add(x.strip())
    return out

print('\n=== 1. 규모 ===')
chk('조직 레지스트리 113건', len(org)==113, len(org))
chk('사건 레지스트리 271건', len(ev)==271, len(ev))
chk('부록 전국배경연표 32건', len(load(f'{D}/부록_전국배경연표_v1.csv'))==32)
chk('소속·직위표 973건(v1.8, J-26 반영)', len(oh)==973, len(oh))
chk('사건 참여표 1,253건', len(ep)==1253, len(ep))
chk('절 구분표 355단위(349절+장서두 6 — J-25)', len(sec)==355, len(sec))

print('\n=== 2. 기계 검증 (참조 무결성) ===')
SID = {list(r.values())[0] for r in sec}
for rows, col, nm in [(org,'근거절','조직'), (ev,'근거절','사건'), (oh,'근거절','소속직위'), (ep,'근거절','사건참여')]:
    bad = sorted(x for x in sec_ids(rows,col) if x not in SID)
    chk(f'{nm} 레지스트리 절 ID 유효성', not bad, bad[:5] or '무효 0')
oids = {o['org_id'] for o in org}; eids = {e['event_id'] for e in ev}
chk('소속직위표 org_id 참조', not [r for r in oh if r['org_id'].strip() and r['org_id'] not in oids])
chk('사건참여표 event_id 참조', not [r for r in ep if r['event_id'] not in eids])
bg = load(f'{D}/부록_전국배경연표_v1.csv')
allev = eids | {b['event_id'] for b in bg}
chk('상위 사건 참조 (레지스트리 ∪ 부록연표)', not [e for e in ev if e['상위사건'].strip() and e['상위사건'] not in allev])
xref = [e['event_id'] for e in ev if e['상위사건'].strip() and e['상위사건'] not in eids]
print(f'         ※ 상위 사건이 부록 연표에 있는 레코드 {len(xref)}건: {xref} — R-11/J-12 판정에 따른 설계(상호참조 보존)')
for rows, col, nm in [(org,'org_id','조직'), (ev,'event_id','사건'), (oh,'record_id','소속직위'), (ep,'record_id','사건참여')]:
    ids = [r[col] for r in rows]
    chk(f'{nm} ID 중복 없음', len(ids)==len(set(ids)))
ROLE = {'발기인','주도자','연설자','대표·위원','중재자','당사자·대상','참석자'}
chk('역할 통제어휘 준수', not {r['역할'] for r in ep} - ROLE, {r['역할'] for r in ep} - ROLE or 'OK')
ETYPE = {'설립','선거·임명','조직개편','창간·경영이전','집단운동·대회','중재·교섭','청원','의례','재난·사고','회의·결의'}
chk('사건유형 통제어휘 준수', not {e['사건유형'] for e in ev} - ETYPE)

print('\n=== 3. 논문 표 재산출 ===')
c = collections.Counter(r['구분'] for r in oh)
chk('표 1 직위 797·소속 176', (c['직위'],c['소속'])==(797,176), f"{c['직위']}·{c['소속']}")
mapped = sum(1 for r in oh if r['org_id'].strip())
chk('표 1 매핑 790·미매핑 183', (mapped,len(oh)-mapped)==(790,183), f'{mapped}·{len(oh)-mapped}')
cd = collections.Counter(r['보조사료대조'] for r in oh)
chk('표 4 확인 127·미확인 91·미대조 755', (cd['확인'],cd['미확인'],cd['미대조'])==(127,91,755), dict(cd))
chk('표 4 확인율 58.3%', round(cd['확인']/218*100,1)==58.3, f"{cd['확인']/218*100:.1f}%")
chk("'전국-대구반응' 13건", sum(1 for e in ev if e['지역구분']=='전국-대구반응')==13)
tt = collections.Counter(e['시기구획'] for e in ev)
chk('사건 시기구획 민회기 44·제도화기 128·확장기 88', 
    (tt['민회기(1903~05)'],tt['민단 제도화기(1906~07)'],tt['확장기(1908~10)'])==(44,128,88), dict(tt))
core = [r for r in idx if int(r['임원직수'])>=3 and int(r['소속조직수'])>=3 and int(r['참여사건수'])>=5 and int(r['활동영역수'])>=3]
mid  = [r for r in idx if int(r['임원직수'])>=2 and int(r['참여사건수'])>=3]
allp = {r['인물'] for r in oh} | {r['인물'] for r in ep}
chk('핵심 중첩층 22명', len(core)==22, len(core))
chk('중간층 74명', len(mid)==74, len(mid))
chk('전체 등장 591명', len(allp)==591, len(allp))
chk('4영역 인물 9명', sum(1 for r in idx if r['활동영역수']=='4')==9)
chk("직위 '기타' 465건(47.8%)",
    sum(1 for r in oh if r['직위']=='기타')==465 and round(465/973*100,1)==47.8)
per = json.load(open(f'{A}/집계_시기별임원_v1.json', encoding='utf-8'))
s1,s2,s3 = set(per['P1']), set(per['P2']), set(per['P3'])
chk('표 8 임원 86→200→135', (len(s1),len(s2),len(s3))==(86,200,135), (len(s1),len(s2),len(s3)))
chk('표 8 지속률 35/24/19%', (round(len(s1&s2)/len(s1)*100), round(len(s2&s3)/len(s2)*100), round(len(s1&s3)/len(s1)*100))==(35,24,19))
kor = json.load(open(f'{A}/집계_조선인비대칭_v3_20260812.json', encoding='utf-8'))
chk('조선인 소속·직위 76건(7.8%)', kor['oh_kor']==76 and round(76/973*100,1)==7.8)
chk('조선인 사건 참여 68건(5.4%)', kor['ep_kor']==68 and round(68/1253*100,1)==5.4)
chk('일본인 1,160·불명 25', (kor['ep_jp'],kor['ep_unknown'])==(1160,25))
chk('발기인 일본인 94(8.1%)·조선인 1(1.5%)',
    kor['jp_roles']['발기인']==94 and kor['kor_roles']['발기인']==1)
chk('복권 당첨자 8건 제외 반영', not [r for r in ep if r['event_id']=='E127'])
chk('봉영 숙소 7건 대표·위원 재판정',
    sum(1 for r in ep if r['event_id']=='E254' and r['역할']=='대표·위원')==10)
kbak = [r for r in ep if r['인물']=='박중양']
chk('박중양 31건 = 조선인 68건의 45.6%', len(kbak)==31 and round(31/68*100,1)==45.6)
attr = {r['한글표기']: r['민족'] for r in load(f'{D}/인물속성_테이블_v2.csv')}
evd  = {e['event_id']: e for e in ev}
JP = [r for r in ep if attr.get(r['인물'])=='일본인']; KO=[r for r in ep if attr.get(r['인물'])=='조선인']
chk('표 9 기준선 5.5% (68/1,228)', round(len(KO)/(len(JP)+len(KO))*100,1)==5.5)
chk('표 9 발기인 몫 1.1% (0.19배)',
    round(1/(94+1)*100,1)==1.1 and round((1/95)/(len(KO)/(len(JP)+len(KO))),2)==0.19)
HOST={'중재·교섭','집단운동·대회','청원'}
h=lambda g: sum(1 for r in g if r['역할']=='당사자·대상' and evd[r['event_id']]['사건유형'] in HOST)
chk('적대적 국면 노출 조선인 10.3% · 일본인 3.4% (3.1배)',
    (round(h(KO)/len(KO)*100,1), round(h(JP)/len(JP)*100,1))==(10.3,3.4)
    and round((h(KO)/len(KO))/(h(JP)/len(JP)),1)==3.1)
chk('일본인 당사자·대상 319건 중 제도 내부 273건',
    sum(1 for r in JP if r['역할']=='당사자·대상')==319
    and sum(1 for r in JP if r['역할']=='당사자·대상' and evd[r['event_id']]['사건유형'] in
            {'선거·임명','의례','조직개편','설립','창간·경영이전'})==273)

print('\n=== 3-2. 영역 겹침과 겸직 집중 (표 7·6.3절) ===')
dm={r['인물']:set(x.strip() for x in r['영역'].split('·') if x.strip()) for r in idx}
DOM=['행정','경제','언론','동원']
nd={d:sum(1 for p in dm if d in dm[p]) for d in DOM}
chk('영역별 인물 수 72·87·38·54', (nd['행정'],nd['경제'],nd['언론'],nd['동원'])==(72,87,38,54), nd)
OBS={('행정','경제'):32,('행정','동원'):27,('행정','언론'):20,('경제','동원'):20,('경제','언론'):19,('언론','동원'):16}
bad2=[(a,b,sum(1 for p in dm if a in dm[p] and b in dm[p])) for (a,b),o in OBS.items()
      if sum(1 for p in dm if a in dm[p] and b in dm[p])!=o]
chk('표 7 여섯 쌍의 관측 겹침', not bad2, bad2 or '전부 일치')
kc=[len(dm[p]) for p in dm]
chk('영역 보유 160·2영역+ 57·3영역+ 25·4영역 9',
    (sum(1 for k in kc if k>=1),sum(1 for k in kc if k>=2),sum(1 for k in kc if k>=3),sum(1 for k in kc if k==4))==(160,57,25,9))
chk('3영역+ 25명 중 핵심 중첩층 22명',
    sum(1 for r in core if len(dm[r['인물']])>=3)==22)
chk("언론 38명 중 다영역 28명(74%)",
    sum(1 for p in dm if '언론' in dm[p] and len(dm[p])>=2)==28)
chk("경제 87명 중 단영역 49명(56%)",
    sum(1 for p in dm if '경제' in dm[p] and len(dm[p])==1)==49)
print('         ※ 순열 기댓값·p값(표 7)과 Fisher 검정(7장)은 scripts/permutation_test.py로 재산출')
from math import lgamma, exp as _exp
def _logC(n,k): return lgamma(n+1)-lgamma(k+1)-lgamma(n-k+1)
def _fisher(a,b,c,d):
    n=a+b+c+d; p=0.0
    for x in range(a,min(a+b,a+c)+1): p+=_exp(_logC(a+b,x)+_logC(c+d,(a+c)-x)-_logC(n,a+c))
    return p
chk('7장 적대 노출 Fisher p=.011', round(_fisher(h(KO),len(KO)-h(KO),h(JP),len(JP)-h(JP)),3)==0.011)
_fk=sum(1 for r in KO if r['역할']=='발기인'); _fj=sum(1 for r in JP if r['역할']=='발기인')
chk('7장 발기인 Fisher p=.025', round(_fisher(_fj,len(JP)-_fj,_fk,len(KO)-_fk),3)==0.025)

print('\n=== 4. 겸직 지표 독립 재계산 (591명 전수) ===')
off = collections.Counter(r['인물'] for r in oh if r['구분']=='직위')
ogn = collections.defaultdict(set); [ogn[r['인물']].add(r['org_id']) for r in oh if r['org_id'].strip()]
evn = collections.defaultdict(set); [evn[r['인물']].add(r['event_id']) for r in ep]
bad = [r['인물'] for r in idx if (int(r['임원직수']),int(r['소속조직수']),int(r['참여사건수']))
       != (off[r['인물']], len(ogn[r['인물']]), len(evn[r['인물']]))]
chk('겸직 지표 591명 전원 일치', not bad, bad[:5] or '불일치 0')

print('\n' + ('='*46))
print('전체 통과' if not FAIL else f'★ 실패 {len(FAIL)}건: ' + ', '.join(FAIL))
sys.exit(1 if FAIL else 0)
