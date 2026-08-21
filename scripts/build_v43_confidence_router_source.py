#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, pathlib, re

EXPECTED_PARENT_RELEASE='v38_fast_harvest_lab_v1'
NEW_RELEASE='v43_confidence_aware_router_exact_mt5_v1'

PARENTS={
    'adaptive_ewma_hl8_thr0p05': (1,0.05),
    'adaptive_ewma_hl10_thr0p05': (2,0.05),
}
NEW_SPECS=[
    (23,'adaptive_ewma_hl8_thr0p05','v43_hl8_thr0p05_conf0p05',0,0.05),
    (24,'adaptive_ewma_hl10_thr0p05','v43_hl10_thr0p05_conf0p05',1,0.05),
    (25,'adaptive_ewma_hl8_thr0p05','v43_hl8_thr0p05_conf0p10',2,0.10),
    (26,'adaptive_ewma_hl10_thr0p05','v43_hl10_thr0p05_conf0p10',3,0.10),
]

def sha256(p:pathlib.Path)->str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def one(s:str, old:str, new:str)->str:
    n=s.count(old)
    if n!=1:
        raise RuntimeError(f'expected exactly one occurrence, found {n}: {old[:160]!r}')
    return s.replace(old,new,1)

def build(source:pathlib.Path, output:pathlib.Path)->None:
    s=source.read_text(encoding='utf-8-sig')
    if f'#define MT5Q_RELEASE_ID "{EXPECTED_PARENT_RELEASE}"' not in s:
        raise RuntimeError('parent V38 release marker missing')
    if '#define CANDIDATE_COUNT 23' not in s:
        raise RuntimeError('parent V38 candidate count mismatch')
    for parent in PARENTS:
        if parent not in s:
            raise RuntimeError(f'parent router missing: {parent}')
    for bad in (r'OrderSend\(',r'OrderSendAsync\(',r'\bCTrade\b',r'trade\.Buy\(',r'trade\.Sell\('):
        if re.search(bad,s):
            raise RuntimeError(f'forbidden native order path already present: {bad}')
    if 'MQLInfoInteger(MQL_TESTER)' not in s:
        raise RuntimeError('tester-only guard missing in parent source')

    s=one(s,f'#define MT5Q_RELEASE_ID "{EXPECTED_PARENT_RELEASE}"',f'#define MT5Q_RELEASE_ID "{NEW_RELEASE}"')
    s=one(s,'#define CANDIDATE_COUNT 23','#define CANDIDATE_COUNT 27')
    s=one(s,'input string InpOutputTag = "v38_fast_harvest_lab_v1";','input string InpOutputTag = "v43_confidence_aware_router_exact_mt5_v1";')
    s=one(s,'input bool   InpV34WriteIntraTradeTelemetry = true;','input bool   InpV34WriteIntraTradeTelemetry = false;')
    s=one(s,'input bool   InpV38WriteM1FastTelemetry = true;','input bool   InpV38WriteM1FastTelemetry = false;')

    s=one(s,
'''   double adaptive_switch_penalty;
   bool slow_mom_timebox;''',
'''   double adaptive_switch_penalty;
   bool v43_confidence_router;
   int v43_slot;
   double v43_direction_margin;
   bool slow_mom_timebox;''')

    s=one(s,
'''   C[i].adaptive_switch_penalty=0.0;
   C[i].slow_mom_timebox=false;''',
'''   C[i].adaptive_switch_penalty=0.0;
   C[i].v43_confidence_router=false;
   C[i].v43_slot=-1;
   C[i].v43_direction_margin=0.0;
   C[i].slow_mom_timebox=false;''')

    s=one(s,
'''int g_last_selected_expert[ADAPT_VARIANT_COUNT];

int g_v34_tape_handle=INVALID_HANDLE;''',
'''int g_last_selected_expert[ADAPT_VARIANT_COUNT];

#define V43_SLOT_COUNT 4
int g_v43_last_direction[V43_SLOT_COUNT];
long g_v43_direction_conflicts[V43_SLOT_COUNT];
long g_v43_incumbent_holds[V43_SLOT_COUNT];

int g_v34_tape_handle=INVALID_HANDLE;''')

    setup_marker='''void SetupV38FastClone(const int i,const string name,const int mode,const double targetR,
                       const double armR,const double givebackR,const int timeboxSeconds)'''
    v43_setup='''void SetupV43ConfidenceRouter(const int i,const string name,const int variant,const double minScore,
                              const int slot,const double directionMargin)
{
   SetupAdaptiveRouter(i,name,variant,minScore,0.00);
   C[i].family="adaptive_shadow_expert_router_confidence_aware";
   C[i].v43_confidence_router=true;
   C[i].v43_slot=slot;
   C[i].v43_direction_margin=directionMargin;
   if(slot>=0 && slot<V43_SLOT_COUNT)
   {
      g_v43_last_direction[slot]=0;
      g_v43_direction_conflicts[slot]=0;
      g_v43_incumbent_holds[slot]=0;
   }
}

'''
    s=one(s,setup_marker,v43_setup+setup_marker)

    catalog_marker='''   SetupV38FastClone(22,"v38_adaptive_timebox30m",4,0.0,0.0,0.0,30*60);
}'''
    additions='''   // V43 bounded confidence-aware router challengers. No post-result margin sweep.
   SetupV43ConfidenceRouter(23,"v43_hl8_thr0p05_conf0p05",1,0.05,0,0.05);
   SetupV43ConfidenceRouter(24,"v43_hl10_thr0p05_conf0p05",2,0.05,1,0.05);
   SetupV43ConfidenceRouter(25,"v43_hl8_thr0p05_conf0p10",1,0.05,2,0.10);
   SetupV43ConfidenceRouter(26,"v43_hl10_thr0p05_conf0p10",2,0.05,3,0.10);'''
    s=one(s,catalog_marker,
'''   SetupV38FastClone(22,"v38_adaptive_timebox30m",4,0.0,0.0,0.0,30*60);
'''+additions+'''
}''')

    resolve_marker='''bool ResolveAdaptiveSignal(const CandidateState &st,const double atr,const datetime when,
                           const int emaDir,const int trendDir,const int macdDir,const int bosDir,const int slowDir,
                           int &direction,int &activeMask)
{'''
    v43_resolve='''bool ResolveV43ConfidenceSignal(const CandidateState &st,const double atr,const datetime when,
                                const int emaDir,const int trendDir,const int macdDir,const int bosDir,const int slowDir,
                                int &direction,int &activeMask)
{
   direction=0; activeMask=0;
   double bestLong=-DBL_MAX,bestShort=-DBL_MAX;
   int longExpert=-1,longMask=0,shortExpert=-1,shortMask=0;
   int v=st.adaptive_variant;
   for(int e=0;e<EXPERT_COUNT;++e)
   {
      int d=0,m=0;
      if(!ExpertSignalInfo(e,atr,when,emaDir,trendDir,macdDir,bosDir,slowDir,d,m)) return false;
      if(d==0 || m==0) continue;
      double score=AdaptiveExpertScore(v,e);
      if(score<st.adaptive_min_score) continue;
      if(d>0 && score>bestLong){ bestLong=score; longExpert=e; longMask=m; }
      if(d<0 && score>bestShort){ bestShort=score; shortExpert=e; shortMask=m; }
   }

   if(longExpert<0 && shortExpert<0) return true;

   int chosenDir=0,chosenExpert=-1,chosenMask=0;
   if(longExpert>=0 && shortExpert<0){ chosenDir=1; chosenExpert=longExpert; chosenMask=longMask; }
   else if(shortExpert>=0 && longExpert<0){ chosenDir=-1; chosenExpert=shortExpert; chosenMask=shortMask; }
   else
   {
      double gap=MathAbs(bestLong-bestShort);
      int leaderDir=(bestLong>bestShort ? 1 : (bestShort>bestLong ? -1 : 0));
      int slot=st.v43_slot;
      if(slot>=0 && slot<V43_SLOT_COUNT) g_v43_direction_conflicts[slot]++;

      if(gap<1e-9)
      {
         if(slot>=0 && slot<V43_SLOT_COUNT && g_v43_last_direction[slot]!=0)
            chosenDir=g_v43_last_direction[slot];
         else
            return true;
      }
      else if(gap<st.v43_direction_margin && slot>=0 && slot<V43_SLOT_COUNT && g_v43_last_direction[slot]!=0)
      {
         chosenDir=g_v43_last_direction[slot];
         g_v43_incumbent_holds[slot]++;
      }
      else chosenDir=leaderDir;

      if(chosenDir>0){ chosenExpert=longExpert; chosenMask=longMask; }
      else { chosenExpert=shortExpert; chosenMask=shortMask; }
   }

   direction=chosenDir; activeMask=chosenMask;
   int slot=st.v43_slot;
   if(slot>=0 && slot<V43_SLOT_COUNT) g_v43_last_direction[slot]=chosenDir;
   if(v>=0 && v<ADAPT_VARIANT_COUNT) g_last_selected_expert[v]=chosenExpert;
   return true;
}

'''
    s=one(s,resolve_marker,v43_resolve+resolve_marker)

    s=one(s,
'''   direction=0; activeMask=0;
   double best=-DBL_MAX,second=-DBL_MAX; int bestExpert=-1,bestDir=0,bestMask=0;''',
'''   direction=0; activeMask=0;
   if(st.v43_confidence_router)
      return ResolveV43ConfidenceSignal(st,atr,when,emaDir,trendDir,macdDir,bosDir,slowDir,direction,activeMask);
   double best=-DBL_MAX,second=-DBL_MAX; int bestExpert=-1,bestDir=0,bestMask=0;''')

    manifest_marker='''   x+="v38_m1_fast_telemetry="+(InpV38WriteM1FastTelemetry?"1":"0")+"\\r\\n";'''
    manifest_new=manifest_marker+'''
   x+="v43_confidence_aware_router=1\\r\\n";
   x+="v43_parents=adaptive_ewma_hl8_thr0p05,adaptive_ewma_hl10_thr0p05\\r\\n";
   x+="v43_mechanism=directional_top_score_margin_prefers_active_incumbent_only_under_conflict\\r\\n";
   x+="v43_direction_margins_r=0.05,0.10\\r\\n";
   x+="v43_global_time_hysteresis=0\\r\\n";
   x+="v43_risk_changed=0\\r\\n";
   x+="v43_entry_exit_geometry_changed=0\\r\\n";'''
    s=one(s,manifest_marker,manifest_new)

    s=s.replace('V38_FAST_HARVEST_LAB START','V43_CONFIDENCE_AWARE_ROUTER START').replace('V38_FAST_HARVEST_LAB DONE','V43_CONFIDENCE_AWARE_ROUTER DONE')

    if '#define CANDIDATE_COUNT 27' not in s:
        raise RuntimeError('V43 candidate count not applied')
    for _,_,name,_,_ in NEW_SPECS:
        if name not in s:
            raise RuntimeError(f'V43 candidate missing after build: {name}')
    for token in ['ResolveV43ConfidenceSignal','V43_SLOT_COUNT','v43_confidence_aware_router=1','v43_global_time_hysteresis=0']:
        if token not in s:
            raise RuntimeError('V43 token missing: '+token)
    for bad in (r'OrderSend\(',r'OrderSendAsync\(',r'\bCTrade\b',r'trade\.Buy\(',r'trade\.Sell\('):
        if re.search(bad,s):
            raise RuntimeError(f'forbidden native order path introduced: {bad}')
    if 'MQLInfoInteger(MQL_TESTER)' not in s:
        raise RuntimeError('tester-only guard lost')

    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(s,encoding='utf-8',newline='\r\n')
    print(f'V43 source PASS sha256={sha256(output)} path={output}')

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--source',required=True)
    ap.add_argument('--output',required=True)
    a=ap.parse_args()
    build(pathlib.Path(a.source),pathlib.Path(a.output))
    return 0

if __name__=='__main__':
    raise SystemExit(main())
