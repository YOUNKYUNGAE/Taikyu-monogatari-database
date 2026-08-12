# -*- coding: utf-8 -*-
"""그림 3-1(인물-조직)·3-2(인물-사건) 이원 연결망 생성
실행: python3 scripts/make_fig3_networks.py   (출력: ../figures/)
의존: matplotlib, networkx, adjustText(라벨 겹침 조정), graphviz(sfdp — 배치 계산, 시스템 패키지)
배치: sfdp(overlap=prism, 고정 파라미터) → 본체 연결성분만 표시. 엣지 검정(alpha .3).
라벨: 조직명 전체 / 사건명은 식별 참여 6명 이상 / 인물명은 핵심 중첩층 22인만.
색: 조직 = 활동 영역 4색(그림 4와 동일), 사건 = 시기구획 3단계 + 시기외. 폰트: Noto Sans CJK JP.
"""
import csv, os, unicodedata, math, subprocess, tempfile
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import networkx as nx
from matplotlib.lines import Line2D
from adjustText import adjust_text

nfc=lambda s: unicodedata.normalize('NFC', s or '')
plt.rcParams['font.family']='Noto Sans CJK JP'; plt.rcParams['axes.unicode_minus']=False
import os as _os
ROOT=_os.path.join(_os.path.dirname(_os.path.abspath(__file__)),'..')
D,A,OUT=[_os.path.join(ROOT,x) for x in ('data','aggregates','figures')]
def load(p): return list(csv.DictReader(open(p,encoding='utf-8-sig')))
org=load(f'{D}/조직레지스트리_v1.4.csv'); ev=load(f'{D}/사건레지스트리_v3_20260728.csv')
oh=load(f'{D}/소속직위표_v6_20260809.csv'); ep=load(f'{D}/사건참여표_v3_20260728.csv')
idx=load(f'{A}/집계_겸직지표_v4_20260812.csv')

CAT={'행정':'#0072B2','경제':'#E69F00','언론':'#009E73','그 밖의 결사':'#B4B4B4'}
CORE_C='#D55E00'; PERSON_C='#9AA3AA'
INK,MUT,SURF='#1a1a1a','#767676','#FCFCFB'
SEQ3={'민회기(1903~05)':'#8FB4D3','민단 제도화기(1906~07)':'#3671A7','확장기(1908~10)':'#02375F','시기외':'#B4B4B4'}
STROKE=[pe.withStroke(linewidth=2.4, foreground=SURF)]

core={nfc(r['인물']) for r in idx if int(r['임원직수'])>=3 and int(r['소속조직수'])>=3 and int(r['참여사건수'])>=5 and int(r['활동영역수'])>=3}
orgname={nfc(o['org_id']):nfc(o['표준조직명']) for o in org}
def dom(t):
    t=nfc(t)
    if t.startswith('행정·자치'): return '행정'
    if t.startswith('경제'): return '경제'
    if t.startswith('언론'): return '언론'
    return '그 밖의 결사'
orgdom={nfc(o['org_id']):dom(o['조직유형']) for o in org}
evname={nfc(e['event_id']):nfc(e['사건명']) for e in ev}
evper={nfc(e['event_id']):nfc(e['시기구획']) for e in ev}

def sfdp_layout(G, big, K=0.45, sep=8, wbig=0.7, wsm=0.2):
    ids={n:f'n{i}' for i,n in enumerate(G.nodes())}
    L=['graph g {',f'graph [overlap=prism, sep="+{sep}", K={K}];','node [shape=point, fixedsize=true];']
    for n in G.nodes():
        w=wbig if n in big else wsm
        L.append(f'{ids[n]} [width={w}, height={w}];')
    for u,v in G.edges(): L.append(f'{ids[u]} -- {ids[v]};')
    L.append('}')
    with tempfile.NamedTemporaryFile('w',suffix='.dot',delete=False) as f:
        f.write('\n'.join(L)); dot=f.name
    out=subprocess.run(['sfdp','-Tplain',dot],capture_output=True,text=True,timeout=900).stdout
    rev={v:k for k,v in ids.items()}; pos={}
    for ln in out.splitlines():
        p=ln.split()
        if p and p[0]=='node': pos[rev[p[1]]]=(float(p[2]),float(p[3]))
    return pos

def draw(G,persons,others,ocolor,olab,plab,title,sub,legend_items,fname,label_fs=6.6,K=0.45,sep=8,wbig=0.7,gamma=1.0,figsz=16):
    # 본체(최대 연결성분)만
    comps=sorted(nx.connected_components(G), key=len, reverse=True)
    Gg=G.subgraph(comps[0])
    dropped_n=G.number_of_nodes()-Gg.number_of_nodes(); dropped_c=len(comps)-1
    pos=sfdp_layout(Gg,set(others)|core,K=K,sep=sep,wbig=wbig)
    if gamma!=1.0:  # 중심 밀집부 방사형 확장(반지름의 거듭제곱 변환)
        cx=sum(p[0] for p in pos.values())/len(pos); cy=sum(p[1] for p in pos.values())/len(pos)
        import math as _m
        rmax=max(_m.hypot(x-cx,y-cy) for x,y in pos.values()) or 1
        pos={n:(cx+(x-cx)*((_m.hypot(x-cx,y-cy)/rmax)**(gamma-1)),
                cy+(y-cy)*((_m.hypot(x-cx,y-cy)/rmax)**(gamma-1))) for n,(x,y) in pos.items()}
    persons=[n for n in persons if n in Gg]; others=[n for n in others if n in Gg]
    deg=dict(Gg.degree())
    fig,ax=plt.subplots(figsize=(figsz,figsz)); ax.axis('off'); fig.patch.set_facecolor(SURF)
    # 곡선 엣지(2차 베지어, 곡률 0.15) — 핵심 22인 연결선은 진한 검정
    from matplotlib.path import Path as MPath
    from matplotlib.collections import PathCollection
    def bez(u,v,rad=0.15):
        x1,y1=pos[u]; x2,y2=pos[v]
        mx,my=(x1+x2)/2,(y1+y2)/2
        dx,dy=x2-x1,y2-y1
        cx,cy=mx-dy*rad, my+dx*rad
        return MPath([(x1,y1),(cx,cy),(x2,y2)],[MPath.MOVETO,MPath.CURVE3,MPath.CURVE3])
    light=[bez(u,v) for u,v in Gg.edges() if not (u in core or v in core)]
    dark =[bez(u,v) for u,v in Gg.edges() if (u in core or v in core)]
    ax.add_collection(PathCollection(light,facecolor='none',edgecolor='black',linewidth=0.28,alpha=0.22,zorder=1))
    ax.add_collection(PathCollection(dark, facecolor='none',edgecolor='black',linewidth=0.65,alpha=0.85,zorder=2.5))
    ax.autoscale_view()
    for n in others:
        x,y=pos[n]; ax.scatter(x,y,s=32+26*math.sqrt(deg[n]),marker='s',color=ocolor[n],edgecolor='white',linewidth=0.5,zorder=3)
    for n in persons:
        x,y=pos[n]
        if n in core: ax.scatter(x,y,s=90+34*math.sqrt(deg[n]),color=CORE_C,edgecolor='white',linewidth=0.8,zorder=4)
        else: ax.scatter(x,y,s=9+6*math.sqrt(deg[n]),color=PERSON_C,alpha=0.75,edgecolor='none',zorder=2)
    texts=[]
    for n,lab in olab.items():
        if n not in pos: continue
        x,y=pos[n]
        texts.append(ax.text(x,y,lab,fontsize=label_fs,color=INK,ha='center',va='center',zorder=6,path_effects=STROKE))
    for n in plab:
        if n not in pos: continue
        x,y=pos[n]
        texts.append(ax.text(x,y,n,fontsize=8.2,color=CORE_C,ha='center',va='center',fontweight='bold',zorder=7,path_effects=STROKE))
    xs=[p[0] for p in pos.values()]; ys=[p[1] for p in pos.values()]
    adjust_text(texts, x=xs, y=ys, ax=ax,
                expand=(1.15,1.35), force_text=(0.3,0.5), force_points=(0.2,0.4),
                arrowprops=dict(arrowstyle='-', color='#8A8A8A', lw=0.5, alpha=0.8),
                lim=250)
    ax.set_title(title,fontsize=18,color=INK,loc='left',pad=20,fontweight='bold')
    sub2=sub+f' · 본체 연결성분만 표시(소성분 {dropped_c}개·노드 {dropped_n}개 제외)'
    ax.text(0,1.011,sub2,transform=ax.transAxes,fontsize=9.8,color=MUT)
    ax.legend(handles=legend_items,loc='lower right',frameon=False,fontsize=9.5,labelcolor=INK)
    fig.savefig(f'{OUT}/{fname}',dpi=200,bbox_inches='tight',facecolor=SURF); plt.close(fig); print(' saved',fname)

# ── 3-1 ──
G=nx.Graph(); ohm=[r for r in oh if r['org_id'].strip()]
for r in ohm:
    p,o=nfc(r['인물']),nfc(r['org_id'])
    G.add_node(p,b='p'); G.add_node(o,b='o'); G.add_edge(p,o)
persons=[n for n,d in G.nodes(data=True) if d['b']=='p']; orgs=[n for n,d in G.nodes(data=True) if d['b']=='o']
draw(G,persons,orgs,{o:CAT[orgdom[o]] for o in orgs},{o:orgname[o] for o in orgs},{p for p in persons if p in core},
 '그림 3-1. 인물–조직 이원 연결망',
 f'인물 {len(persons)}명(원) × 조직 {len(orgs)}개(사각) · 소속·직위 {len(ohm)}건(관내 매핑분) · 노드 크기 = 연결 수 · 인물 이름은 핵심 중첩층 22인만 표기',
 [Line2D([0],[0],marker='o',color='none',markerfacecolor=CORE_C,markersize=9,label='핵심 중첩층 22인(연결선 진한 검정)'),
  Line2D([0],[0],marker='o',color='none',markerfacecolor=PERSON_C,markersize=6,label='그 밖의 인물'),
  Line2D([0],[0],marker='s',color='none',markerfacecolor=CAT['행정'],markersize=9,label='행정·자치 조직'),
  Line2D([0],[0],marker='s',color='none',markerfacecolor=CAT['경제'],markersize=9,label='경제 조직'),
  Line2D([0],[0],marker='s',color='none',markerfacecolor=CAT['언론'],markersize=9,label='언론 조직'),
  Line2D([0],[0],marker='s',color='none',markerfacecolor=CAT['그 밖의 결사'],markersize=9,label='그 밖의 결사·기관')],
 '그림3-1_인물조직_연결망.png')

# ── 3-2 ──
G2=nx.Graph()
for r in ep:
    p,e=nfc(r['인물']),nfc(r['event_id'])
    if e not in evname: continue
    G2.add_node(p,b='p'); G2.add_node(e,b='e'); G2.add_edge(p,e)
persons2=[n for n,d in G2.nodes(data=True) if d['b']=='p']; evs=[n for n,d in G2.nodes(data=True) if d['b']=='e']
deg2=dict(G2.degree())
elab={e:evname[e] for e in evs if deg2[e]>=6}
draw(G2,persons2,evs,{e:SEQ3.get(evper.get(e,'시기외'),'#B4B4B4') for e in evs},elab,{p for p in persons2 if p in core},
 '그림 3-2. 인물–사건 이원 연결망',
 f'인물 {len(persons2)}명(원) × 사건 {len(evs)}건(사각) · 참여 레코드 1,253건(인물–사건 연결 {G2.number_of_edges()}개) · 사건명은 식별 참여 6명 이상({len(elab)}건)만, 인물 이름은 핵심 중첩층 22인만 표기',
 [Line2D([0],[0],marker='o',color='none',markerfacecolor=CORE_C,markersize=9,label='핵심 중첩층 22인(연결선 진한 검정)'),
  Line2D([0],[0],marker='o',color='none',markerfacecolor=PERSON_C,markersize=6,label='그 밖의 인물'),
  Line2D([0],[0],marker='s',color='none',markerfacecolor=SEQ3['민회기(1903~05)'],markersize=9,label='민회기(1903~05) 사건'),
  Line2D([0],[0],marker='s',color='none',markerfacecolor=SEQ3['민단 제도화기(1906~07)'],markersize=9,label='제도화기(1906~07) 사건'),
  Line2D([0],[0],marker='s',color='none',markerfacecolor=SEQ3['확장기(1908~10)'],markersize=9,label='확장기(1908~10) 사건'),
  Line2D([0],[0],marker='s',color='none',markerfacecolor='#B4B4B4',markersize=9,label='시기외 사건')],
 '그림3-2_인물사건_연결망.png',label_fs=6.2,K=0.7,sep=12,wbig=1.0,gamma=0.72,figsz=18)
