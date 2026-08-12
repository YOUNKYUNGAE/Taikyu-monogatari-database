# -*- coding: utf-8 -*-
"""논문 2 그림 5종 생성 (v5) — 재현 패키지용
실행: python3 scripts/make_figs_v5.py   (출력: ../figures/)
v5 변경: 그림 5에 Fisher 정확검정 결과 병기(적대 노출 p=.011, 발기인 p=.025) — 논문 7장 수정 연동
그림 1 조직 신설 시기별 분포 / 2 사건 유형 시기별 분포 / 3 핵심 22인 겸직 프로필
그림 4 핵심 22인 × 주요 조직 겸직 행렬 / 5 조선인의 수량적·질적 비대칭
색: 색맹 안전 검증 통과 팔레트(범주 3색 + 순차 5단계). 폰트: Noto Sans CJK JP.
"""
import csv, json, os, re, collections
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D

plt.rcParams['font.family']='Noto Sans CJK JP'; plt.rcParams['axes.unicode_minus']=False
ROOT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..')
D,A,OUT=[os.path.join(ROOT,x) for x in ('data','aggregates','figures')]
def load(p): return list(csv.DictReader(open(p,encoding='utf-8-sig')))
org=load(f'{D}/조직레지스트리_v1.4.csv'); ev=load(f'{D}/사건레지스트리_v3_20260728.csv')
oh=load(f'{D}/소속직위표_v6_20260809.csv'); ep=load(f'{D}/사건참여표_v3_20260728.csv')
idx=load(f'{A}/집계_겸직지표_v4_20260812.csv')
KOR=json.load(open(f'{A}/집계_조선인비대칭_v3_20260812.json',encoding='utf-8'))
orgname={o['org_id']:o['표준조직명'] for o in org}; orgtype={o['org_id']:o['조직유형'] for o in org}

CAT={'행정':'#0072B2','경제':'#E69F00','언론':'#009E73','그 밖의 결사':'#B4B4B4'}
SEQ=['#8FB4D3','#5E93C1','#3671A7','#12528B','#02375F']
CMAP=LinearSegmentedColormap.from_list('seq',['#F4F7FA']+SEQ)
INK,MUT,GRID,SURF='#1a1a1a','#767676','#E4E4E4','#FCFCFB'
P1,P2,P3='민회기(1903~05)','민단 제도화기(1906~07)','확장기(1908~10)'
PL=['민회기\n1903~05','제도화기\n1906~07','확장기\n1908~10']
def domain(t):
    if t.startswith('행정·자치'): return '행정'
    if t.startswith('경제'):     return '경제'
    if t.startswith('언론'):     return '언론'
    return '그 밖의 결사'
def bucket(y):
    m=re.match(r'(\d{4})',y or '')
    if not m: return None
    y=int(m.group(1))
    return P1 if 1903<=y<=1905 else (P2 if 1906<=y<=1907 else (P3 if 1908<=y<=1910 else None))
def style(ax):
    for s in ('top','right','left','bottom'): ax.spines[s].set_visible(False)
    ax.tick_params(colors=MUT,labelsize=9,length=0)
def grid_cells(ax,nx,ny):
    ax.set_xticks(np.arange(-.5,nx,1),minor=True); ax.set_yticks(np.arange(-.5,ny,1),minor=True)
    ax.grid(which='minor',color=SURF,lw=3); ax.tick_params(which='minor',length=0)
def save(fig,n):
    fig.savefig(f'{OUT}/{n}',dpi=300,bbox_inches='tight',facecolor=SURF); plt.close(fig); print('  ',n)

# ───────── 그림 1. 조직 신설의 시기별 분포 ─────────
TY=['행정·자치','경제','언론','교육·종교','공익·위생','동향·친목','임시조직','기관']
def tyg(t):
    if t.startswith('행정·자치'): return '행정·자치'
    if t.startswith('경제'): return '경제'
    if t.startswith('언론'): return '언론'
    if t.startswith('교육'): return '교육·종교'
    if '공익' in t or '위생' in t: return '공익·위생'
    if t.startswith('동향'): return '동향·친목'
    if t.startswith('임시'): return '임시조직'
    return '기관'
M=np.zeros((len(TY),3))
for o in org:
    b=bucket(o['설립시기'])
    if b: M[TY.index(tyg(o['조직유형'])),[P1,P2,P3].index(b)]+=1
fig,ax=plt.subplots(figsize=(7.0,4.5))
ax.imshow(M,cmap=CMAP,vmin=0,vmax=M.max(),aspect='auto')
for i in range(len(TY)):
    for j in range(3):
        v=int(M[i,j])
        if v: ax.text(j,i,str(v),ha='center',va='center',fontsize=11,
                      color='white' if v>M.max()*.55 else INK,fontweight='bold' if v>=8 else 'normal')
ax.set_xticks(range(3)); ax.set_xticklabels(PL,fontsize=10,color=INK)
ax.set_yticks(range(len(TY))); ax.set_yticklabels(TY,fontsize=10,color=INK)
grid_cells(ax,3,len(TY)); style(ax)
fig.text(.02,1.03,'그림 1. 조직 신설의 시기별 분포',fontsize=13,color=INK,fontweight='bold')
fig.text(.02,.995,'설립 시기를 특정할 수 있는 79건 · 셀 숫자 = 신설 조직 수 · 시기 불명 34건 제외',fontsize=9.5,color=MUT)
save(fig,'그림1_조직신설_시기분포.png')

# ───────── 그림 2. 사건 유형의 시기별 분포 ─────────
ET=['설립','선거·임명','조직개편','중재·교섭','집단운동·대회','청원','회의·결의','창간·경영이전','의례','재난·사고']
M2=np.zeros((len(ET),3))
for e in ev:
    if e['시기구획'] in (P1,P2,P3): M2[ET.index(e['사건유형']),[P1,P2,P3].index(e['시기구획'])]+=1
fig,ax=plt.subplots(figsize=(7.0,5.1))
ax.imshow(M2,cmap=CMAP,vmin=0,vmax=M2.max(),aspect='auto')
for i in range(len(ET)):
    for j in range(3):
        v=int(M2[i,j])
        if v: ax.text(j,i,str(v),ha='center',va='center',fontsize=11,
                      color='white' if v>M2.max()*.55 else INK,fontweight='bold' if v>=20 else 'normal')
ax.set_xticks(range(3)); ax.set_xticklabels(PL,fontsize=10,color=INK)
ax.set_yticks(range(len(ET))); ax.set_yticklabels(ET,fontsize=10,color=INK)
grid_cells(ax,3,len(ET)); style(ax)
fig.text(.02,1.03,'그림 2. 사건 유형의 시기별 분포',fontsize=13,color=INK,fontweight='bold')
fig.text(.02,.998,'시기 내 260건 · 셀 숫자 = 사건 수 · 시기외 11건 제외',fontsize=9.5,color=MUT)
save(fig,'그림2_사건유형_시기분포.png')

# ───────── 그림 3. 핵심 22인 겸직 프로필 ─────────
core=[r for r in idx if int(r['임원직수'])>=3 and int(r['소속조직수'])>=3 and int(r['참여사건수'])>=5 and int(r['활동영역수'])>=3]
rows=sorted(core,key=lambda r:(-int(r['임원직수']),-int(r['참여사건수'])))
names=[r['인물'] for r in rows]
ARR={r['인물']:r['대구도래연도'] for r in load(f'{D}/도래연도_대구기준_v1_20260727.csv') if r['대구도래연도']}
ARR.update({'가와이 아사오':'1904','나카에 고로헤이':'1904','야스마쓰 구마키치':'1904','시라타 신스케':'1904',
            '와타나베 히스루':'1905','아오키 시게노부':'1905','가토 이치로':'1906','니시자와 사토루':'1906','오키타 스테지로':'1907'})
fig,axes=plt.subplots(1,3,figsize=(9.3,6.8),sharey=True,gridspec_kw={'wspace':.10,'width_ratios':[1,1,1.15]})
for ax,(k,lab,c) in zip(axes,[('임원직수','임원직 수',SEQ[4]),('소속조직수','소속 조직 수',SEQ[2]),('참여사건수','참여 사건 수','#CC79A7')]):
    v=[int(r[k]) for r in rows]
    ax.hlines(range(len(v)),0,v,color=c,lw=1.4,alpha=.45)
    ax.scatter(v,range(len(v)),s=86,color=c,zorder=3,edgecolor=SURF,lw=1.6)
    for i,x in enumerate(v): ax.text(x+max(v)*.05,i,str(x),va='center',fontsize=9,color=INK)
    ax.set_xlim(0,max(v)*1.22); ax.set_xticks([]); style(ax); ax.invert_yaxis()
    ax.set_title(lab,fontsize=11,color=INK,loc='left',pad=10)
axes[0].set_yticks(range(len(names)))
axes[0].set_yticklabels([f'{n}   {ARR.get(n,"—")}' for n in names],fontsize=9.5,color=INK)
for ax in axes: ax.tick_params(axis='y',length=0)
fig.text(.02,1.005,'그림 3. 핵심 중첩층 22인의 겸직 프로필',fontsize=13,color=INK,fontweight='bold')
fig.text(.02,.977,'임원직 수 내림차순 · 인물명 옆은 대구 도래 연도(— 는 불명) · 확인된 13명 중 8명이 1904년 이전 도래',fontsize=9.5,color=MUT)
save(fig,'그림3_핵심22인_겸직프로필.png')

# ───────── 그림 4. 핵심 22인 × 주요 조직 겸직 행렬 ─────────
CORE=[r['인물'] for r in core]
cnt=collections.Counter(r['org_id'] for r in oh if r['인물'] in CORE and r['org_id'].strip())
sel=[o for o,c in cnt.most_common() if c>=4]
mat={p:collections.Counter() for p in CORE}
for r in oh:
    if r['인물'] in CORE and r['org_id'] in sel: mat[r['인물']][r['org_id']]+=1
ppl=sorted(CORE,key=lambda p:(-sum(1 for o in sel if mat[p][o]),p))
sel=sorted(sel,key=lambda o:-sum(1 for p in ppl if mat[p][o]))
SHORT={'일본적십자사 한국특별위원부 대구지부':'적십자 대구지부','신구부대 환송영회 위원회':'신구부대 환송영회',
'대구마쓰하코석유판매조합':'석유판매조합','대구일본인상업회의소':'상업회의소','대구일본인거류민회':'거류민회',
'대구거류민단':'거류민단','남한연초주식회사':'남한연초','대구수산주식회사':'대구수산','대구도로위원회':'도로위원회','대구신문사조합':'신문사조합'}
fig,ax=plt.subplots(figsize=(8.0,7.4))
ax.imshow(np.zeros((len(ppl),len(sel))),cmap=LinearSegmentedColormap.from_list('x',[SURF,SURF]),aspect='auto')
for i,p in enumerate(ppl):
    for j,o in enumerate(sel):
        v=mat[p][o]
        if v:
            ax.add_patch(Rectangle((j-.42,i-.42),.84,.84,facecolor=CAT[domain(orgtype[o])],edgecolor='none'))
            ax.text(j,i,str(v),ha='center',va='center',fontsize=8,color='white',fontweight='bold')
ax.set_xticks(range(len(sel))); ax.set_xticklabels([SHORT.get(orgname[o],orgname[o]) for o in sel],
                                                   rotation=45,ha='left',fontsize=9.5,color=INK)
ax.xaxis.set_ticks_position('top')
ax.set_yticks(range(len(ppl))); ax.set_yticklabels(ppl,fontsize=9.5,color=INK)
ax.set_xticks(np.arange(-.5,len(sel),1),minor=True); ax.set_yticks(np.arange(-.5,len(ppl),1),minor=True)
ax.grid(which='minor',color='white',lw=2); ax.tick_params(which='minor',length=0); style(ax)
ax.set_xlim(-.5,len(sel)-.5); ax.set_ylim(len(ppl)-.5,-.5)
ax.legend(handles=[Line2D([],[],marker='s',ls='',ms=9,mfc=CAT[k],mec='none',label=k) for k in CAT],
          loc='upper left',bbox_to_anchor=(0,-.03),ncol=4,frameon=False,fontsize=9.5,handletextpad=.5)
fig.text(.02,1.16,'그림 4. 핵심 중첩층 22인 × 주요 조직 겸직 행렬',fontsize=13,color=INK,fontweight='bold')
fig.text(.02,1.135,'임원 4인 이상이 공유하는 조직 %d개 · 칸 색 = 조직이 부여하는 활동 영역(3.7절) · 숫자 = 같은 조직 내 직위 수(빈칸 = 임원직 없음)'%len(sel),fontsize=9.5,color=MUT)
save(fig,'그림4_겸직행렬.png')

# ───────── 그림 5. 조선인의 위치 ─────────
evd={e['event_id']:e for e in ev}
attr={r['한글표기']:r['민족'] for r in load(f'{D}/인물속성_테이블_v2.csv')}
jp=[r for r in ep if attr.get(r['인물'])=='일본인']; ko=[r for r in ep if attr.get(r['인물'])=='조선인']
R=['연설자','중재자','주도자','참석자','당사자·대상','대표·위원','발기인']
base=len(ko)/(len(jp)+len(ko))*100
share=[]
for r in R:
    j=sum(1 for x in jp if x['역할']==r); k=sum(1 for x in ko if x['역할']==r)
    share.append((r,j,k,k/(j+k)*100))
HOST={'중재·교섭','집단운동·대회','청원'}
def host(g): return sum(1 for r in g if r['역할']=='당사자·대상' and evd[r['event_id']]['사건유형'] in HOST)
hj,hk=host(jp)/len(jp)*100, host(ko)/len(ko)*100

fig,axes=plt.subplots(1,2,figsize=(9.8,4.9),gridspec_kw={'width_ratios':[1.35,1],'wspace':.30})
ax=axes[0]; y=np.arange(len(R))
for i,(r,j,k,sh) in enumerate(share):
    c=SEQ[4] if sh<base else SEQ[1]
    ax.barh(i,sh,.5,color=c)
    ax.text(sh+.5,i,f'{sh:.1f}%',va='center',fontsize=9.5,color=INK,fontweight='bold' if sh<base else 'normal')
    ax.text(max(x[3] for x in share)*1.28,i,f'일본인 {j:,} · 조선인 {k}',va='center',fontsize=8.5,color=MUT)
ax.axvline(base,color='#CC79A7',lw=1.6,zorder=3)
ax.text(base,-0.95,f'  기준선 {base:.1f}%  (민족 판정 1,228건 중 조선인 비중)',fontsize=9,color='#A34E82',va='top')
ax.set_yticks(y); ax.set_yticklabels(R,fontsize=10,color=INK); ax.invert_yaxis()
ax.set_xticks([]); ax.set_xlim(0,max(s[3] for s in share)*1.75); ax.set_ylim(len(R)+.15,-1.5); style(ax)
ax.set_title('각 역할에서 조선인이 차지하는 몫',fontsize=11,color=INK,loc='left',pad=10)
ax2=axes[1]
ax2.bar([0,1],[hj,hk],.46,color=['#C9D6E1',SEQ[3]])
for i,(v,l,n) in enumerate([(hj,'일본인',host(jp)),(hk,'조선인',host(ko))]):
    ax2.text(i,v+.35,f'{v:.1f}%',ha='center',fontsize=13,color=INK if i else MUT,fontweight='bold')
    ax2.text(i,-0.45,f'{l}\n{n}건 / {len(jp) if i==0 else len(ko):,}건',ha='center',va='top',fontsize=9.5,color=MUT)
ax2.annotate('',xy=(1.27,hk),xytext=(1.27,hj),arrowprops=dict(arrowstyle='<->',color='#E8362A',lw=1.4))
import matplotlib.patheffects as _pe
_st=[_pe.withStroke(linewidth=3,foreground='white')]
ax2.text(1.33,(hj+hk)/2,f'{hk/hj:.1f}배',fontsize=13,color='#E8362A',fontweight='bold',va='center',path_effects=_st)
ax2.text(1.33,(hj+hk)/2-1.15,'Fisher p=.011',fontsize=8.5,color='#E8362A',va='center',path_effects=_st)
ax2.set_xticks([]); ax2.set_yticks([]); ax2.set_xlim(-.6,1.85); ax2.set_ylim(-3.1,hk*1.28); style(ax2)
ax2.set_title('적대적 국면의 대상이 될 확률',fontsize=11,color=INK,loc='left',pad=10)
ax2.text(-.55,hk*1.16,'중재·교섭·집단운동·청원 사건에서\n‘당사자·대상’으로 기록된 비율',fontsize=9,color=MUT)
fig.text(.02,1.05,'그림 5. 조선인의 위치 — 발기하지 않고, 겨냥된다',fontsize=13,color=INK,fontweight='bold')
fig.text(.02,1.012,'사건 참여표 1,253건 중 일본인 1,160·조선인 68·민족 판정 불명 25건(집계 제외) · 코딩북 J-23·J-24 반영 · 검정: scripts/permutation_test.py',fontsize=9.5,color=MUT)
save(fig,'그림5_조선인_비대칭.png')
print('그림 5종 저장 완료')
