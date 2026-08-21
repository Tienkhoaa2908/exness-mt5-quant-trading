#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, pathlib, re

EXPECTED_PARENT_RELEASE='v38_fast_harvest_lab_v1'
NEW_RELEASE='v42_baseline_router_upgrade_exact_mt5_v1'

OLD_ROUTERS=[
    'adaptive_ewma_hl8_thr0',
    'adaptive_ewma_hl8_thr0p05',
    'adaptive_ewma_hl10_thr0p05',
    'adaptive_ewma_hl12_thr0p05',
    'adaptive_cp_fast5_slow20_thr0p30',
]
NEW_SPECS=[
    (23,'adaptive_ewma_hl8_thr0','v42_hl8_switch15m',15*60),
    (24,'adaptive_ewma_hl8_thr0','v42_hl8_switch30m',30*60),
    (25,'adaptive_ewma_hl8_thr0p05','v42_hl8_thr0p05_switch15m',15*60),
    (26,'adaptive_ewma_hl10_thr0p05','v42_hl10_thr0p05_switch15m',15*60),
    (27,'adaptive_ewma_hl12_thr0p05','v42_hl12_thr0p05_switch15m',15*60),
    (28,'adaptive_cp_fast5_slow20_thr0p30','v42_cp_fast5_slow20_switch15m',15*60),
]

def sha256(p:pathlib.Path)->str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def one(s:str, old:str, new:str)->str:
    n=s.count(old)
    if n!=1:
        raise RuntimeError(f'expected exactly one occurrence, found {n}: {old[:140]!r}')
    return s.replace(old,new,1)

def adaptive_setup_line(text:str, name:str, new_index:int, new_name:str)->str:
    pat=re.compile(r'^\s*SetupAdaptiveRouter\(\s*\d+\s*,\s*"'+re.escape(name)+r'"(?P<tail>\s*,[^;]+)\);\s*$',re.M)
    m=pat.search(text)
    if not m:
        raise RuntimeError(f'could not locate adaptive setup for {name}')
    return f'   SetupAdaptiveRouter({new_index},"{new_name}"{m.group("tail")});'

def build(source:pathlib.Path, output:pathlib.Path)->None:
    s=source.read_text(encoding='utf-8-sig')
    if f'#define MT5Q_RELEASE_ID "{EXPECTED_PARENT_RELEASE}"' not in s:
        raise RuntimeError('parent V38 release marker missing')
    if '#define CANDIDATE_COUNT 23' not in s:
        raise RuntimeError('parent V38 candidate count mismatch')
    for n in OLD_ROUTERS:
        if n not in s:
            raise RuntimeError(f'parent adaptive router missing: {n}')
    for bad in (r'OrderSend\(',r'OrderSendAsync\(',r'\bCTrade\b',r'trade\.Buy\(',r'trade\.Sell\('):
        if re.search(bad,s):
            raise RuntimeError(f'forbidden native order path already present: {bad}')
    if 'MQLInfoInteger(MQL_TESTER)' not in s:
        raise RuntimeError('tester-only guard missing in parent source')

    clone_lines=[adaptive_setup_line(s,src,idx,new) for idx,src,new,_ in NEW_SPECS]

    s=one(s,f'#define MT5Q_RELEASE_ID "{EXPECTED_PARENT_RELEASE}"',f'#define MT5Q_RELEASE_ID "{NEW_RELEASE}"')
    s=one(s,'#define CANDIDATE_COUNT 23','#define CANDIDATE_COUNT 29')
    s=one(s,'input string InpOutputTag = "v38_fast_harvest_lab_v1";','input string InpOutputTag = "v42_baseline_router_upgrade_exact_mt5_v1";')
    s=one(s,'input bool   InpV34WriteIntraTradeTelemetry = true;','input bool   InpV34WriteIntraTradeTelemetry = false;')
    s=one(s,'input bool   InpV38WriteM1FastTelemetry = true;','input bool   InpV38WriteM1FastTelemetry = false;')

    guard=r'''
int g_v42_switch_delay_seconds[CANDIDATE_COUNT];
int g_v42_last_direction[CANDIDATE_COUNT];
datetime g_v42_last_switch_time[CANDIDATE_COUNT];
long g_v42_switch_events[CANDIDATE_COUNT];
long g_v42_switch_blocks[CANDIDATE_COUNT];

void V42SetDirectionSwitchGuard(const int ci,const int delaySeconds)
{
   if(ci<0 || ci>=CANDIDATE_COUNT) return;
   g_v42_switch_delay_seconds[ci]=(delaySeconds>0 ? delaySeconds : 0);
}

bool V42DirectionSwitchAllows(const datetime barTime,const int ci,const int direction)
{
   if(ci<0 || ci>=CANDIDATE_COUNT) return false;
   int delay=g_v42_switch_delay_seconds[ci];
   if(delay<=0) return true;
   if(direction==0) return false;
   if(g_v42_last_direction[ci]==0)
   {
      g_v42_last_direction[ci]=direction;
      g_v42_last_switch_time[ci]=barTime;
      return true;
   }
   if(direction!=g_v42_last_direction[ci])
   {
      g_v42_last_direction[ci]=direction;
      g_v42_last_switch_time[ci]=barTime;
      g_v42_switch_events[ci]++;
      g_v42_switch_blocks[ci]++;
      return false;
   }
   if(g_v42_last_switch_time[ci]>0 && (barTime-g_v42_last_switch_time[ci])<delay)
   {
      g_v42_switch_blocks[ci]++;
      return false;
   }
   return true;
}

'''
    s=one(s,'void BuildCatalog()\n{',guard+'void BuildCatalog()\n{')

    catalog_marker='''   SetupV38FastClone(22,"v38_adaptive_timebox30m",4,0.0,0.0,0.0,30*60);
}'''
    additions=['   // V42 exact-MT5 router challengers; parent adaptive arguments are cloned unchanged.']
    for (idx,src,new,delay),line in zip(NEW_SPECS,clone_lines):
        additions.append(line)
        additions.append(f'   V42SetDirectionSwitchGuard({idx},{delay});')
    catalog_new='''   SetupV38FastClone(22,"v38_adaptive_timebox30m",4,0.0,0.0,0.0,30*60);
'''+"\n".join(additions)+'''\n}'''
    s=one(s,catalog_marker,catalog_new)

    gate_point='''if(InpUseTradeSessionPreflight && !TradeSessionOpenAt(tick.time)){ C[ci].session_reject++; continue; }

      C[ci].selected_signals++;'''
    gate_new='''if(InpUseTradeSessionPreflight && !TradeSessionOpenAt(tick.time)){ C[ci].session_reject++; continue; }
      if(!V42DirectionSwitchAllows(r[0].time,ci,dir)){ C[ci].quality_reject++; continue; }

      C[ci].selected_signals++;'''
    s=one(s,gate_point,gate_new)

    marker='''   x+="v34_specialists=smc_ict_causal,price_action_causal,wyckoff_proxy_causal,tick_microstructure_proxy,parallel_specialist_confluence\\r\\n";'''
    manifest=marker+'''\n   x+="v42_baseline_router_upgrade=1\\r\\n";
   x+="v42_control=adaptive_ewma_hl8_thr0\\r\\n";
   x+="v42_mechanism=direction_switch_hysteresis_only\\r\\n";
   x+="v42_primary_delay_seconds=900\\r\\n";
   x+="v42_sensitivity_delay_seconds=1800\\r\\n";
   x+="v42_risk_changed=0\\r\\nv42_entry_exit_geometry_changed=0\\r\\n";'''
    s=one(s,marker,manifest)

    s=s.replace('V38_FAST_HARVEST_LAB START','V42_BASELINE_ROUTER_UPGRADE START').replace('V38_FAST_HARVEST_LAB DONE','V42_BASELINE_ROUTER_UPGRADE DONE')
    if '#define CANDIDATE_COUNT 29' not in s:
        raise RuntimeError('V42 candidate count not applied')
    for _,_,new,_ in NEW_SPECS:
        if new not in s:
            raise RuntimeError(f'V42 candidate missing after build: {new}')
    for bad in (r'OrderSend\(',r'OrderSendAsync\(',r'\bCTrade\b',r'trade\.Buy\(',r'trade\.Sell\('):
        if re.search(bad,s):
            raise RuntimeError(f'forbidden native order path introduced: {bad}')
    if 'MQLInfoInteger(MQL_TESTER)' not in s:
        raise RuntimeError('tester-only guard lost')
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(s,encoding='utf-8',newline='\r\n')
    print(f'V42 source PASS sha256={sha256(output)} path={output}')

def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--output',required=True);a=ap.parse_args()
    build(pathlib.Path(a.source),pathlib.Path(a.output));return 0
if __name__=='__main__': raise SystemExit(main())
