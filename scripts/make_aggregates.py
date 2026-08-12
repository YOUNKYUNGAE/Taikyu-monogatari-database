# -*- coding: utf-8 -*-
"""겸직 지표·영역 행렬 산출 — 활동 영역 배정 규칙의 정본 구현
실행: python3 scripts/make_aggregates.py
검증: 기존 집계_겸직지표_v1.csv의 '영역' 열과 599명 전원 일치(불일치 0)

활동 영역 배정 규칙
  행정  : 소속 조직 중 조직유형이 '행정·자치'로 시작하는 것이 있음
  경제  : 조직유형이 '경제'로 시작
  언론  : 조직유형이 '언론'으로 시작
  동원  : '집단운동·대회' 또는 '청원' 사건에 발기인·주도자·연설자·대표·위원 역할로 참여

  ※ 앞의 셋은 조직 소속으로, 넷째는 사건 참여의 역할로 정해진다. 정의가 비대칭인 것은
    의도된 것이다. 행정·경제·언론은 상설 기구에의 소속이 곧 그 영역에서의 활동이지만,
    집합행동은 상설 조직이 아니라 국면마다 조직되므로 소속이 아닌 역할로 포착해야 한다.
    참석자·중재자·당사자·대상은 능동적 참여로 보지 않아 제외한다.
"""
import csv, json, os, collections

ROOT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..')
D,A=os.path.join(ROOT,'data'),os.path.join(ROOT,'aggregates')
def load(p): return list(csv.DictReader(open(p,encoding='utf-8-sig')))
org=load(f'{D}/조직레지스트리_v1.4.csv'); ev=load(f'{D}/사건레지스트리_v3_20260728.csv')
oh=load(f'{D}/소속직위표_v6_20260809.csv'); ep=load(f'{D}/사건참여표_v3_20260728.csv')
otype={o['org_id']:o['조직유형'] for o in org}
etype={e['event_id']:e['사건유형'] for e in ev}

MOBILE_EVENTS={'집단운동·대회','청원'}
MOBILE_ROLES={'발기인','주도자','연설자','대표·위원'}
ORDER=['행정','경제','언론','동원']          # 표시 순서 고정

def domains(person, orgs_of, mob_of):
    d=set()
    for t in orgs_of:
        if t.startswith('행정·자치'): d.add('행정')
        if t.startswith('경제'):     d.add('경제')
        if t.startswith('언론'):     d.add('언론')
    if mob_of: d.add('동원')
    return [x for x in ORDER if x in d]

people=sorted({r['인물'] for r in oh} | {r['인물'] for r in ep})
off=collections.Counter(r['인물'] for r in oh if r['구분']=='직위')
orgs=collections.defaultdict(set); [orgs[r['인물']].add(r['org_id']) for r in oh if r['org_id'].strip()]
evs =collections.defaultdict(set); [evs[r['인물']].add(r['event_id']) for r in ep]
otypes=collections.defaultdict(set)
for r in oh:
    if r['org_id'].strip(): otypes[r['인물']].add(otype[r['org_id']])
mob=collections.defaultdict(bool)
for r in ep:
    if etype[r['event_id']] in MOBILE_EVENTS and r['역할'] in MOBILE_ROLES: mob[r['인물']]=True

rows=[]
for p in people:
    d=domains(p,otypes[p],mob[p])
    rows.append({'인물':p,'임원직수':off[p],'소속조직수':len(orgs[p]),'참여사건수':len(evs[p]),
                 '활동영역수':len(d),'영역':' ·'.join(d)})
out=f'{A}/집계_겸직지표_v4_20260812.csv'
with open(out,'w',newline='',encoding='utf-8-sig') as f:
    w=csv.DictWriter(f,fieldnames=['인물','임원직수','소속조직수','참여사건수','활동영역수','영역']); w.writeheader(); w.writerows(rows)

# 영역 간 겸직 행렬
dm={r['인물']:set(x.strip() for x in r['영역'].split('·') if x.strip()) for r in rows}
M={a:{b:sum(1 for p in dm if a in dm[p] and b in dm[p]) for b in ORDER} for a in ORDER}
json.dump(M,open(f'{A}/집계_영역행렬_v4_20260812.json','w',encoding='utf-8'),ensure_ascii=False)

# 기존 v1과 대조 (v1 파일이 있을 때만 — 최종 패키지에는 미포함)
import os as _os
if not _os.path.exists(f'{A}/집계_겸직지표_v1.csv'):
    print(f'산출 완료: {out}')
    raise SystemExit(0)
old={r['인물']:set(x.strip() for x in (r['영역'] or '').split('·') if x.strip()) for r in load(f'{A}/집계_겸직지표_v1.csv')}
bad=[p for p in old if p in dm and old[p]!=dm[p]]
print(f'겸직지표 {len(rows)}명 산출 → {os.path.basename(out)}')
print(f'영역 배정 v1 대조(공통 {len([p for p in old if p in dm])}명): 불일치 {len(bad)}건' + (f' {bad[:5]}' if bad else '  ✓ 완전 일치'))
print('영역별 인물 수:', {a:M[a][a] for a in ORDER})

core=[r for r in rows if r['임원직수']>=3 and r['소속조직수']>=3 and r['참여사건수']>=5 and r['활동영역수']>=3]
mid =[r for r in rows if r['임원직수']>=2 and r['참여사건수']>=3]
print(f'핵심 중첩층 {len(core)}명 / 중간층 {len(mid)}명 / 전체 등장 {len(rows)}명')
print('4영역 인물', sum(1 for r in rows if r['활동영역수']==4), '명')
