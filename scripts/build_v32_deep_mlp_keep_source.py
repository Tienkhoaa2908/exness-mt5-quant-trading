#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, pathlib, re

ACCEPTED_V30_SHA='4222120de5ded19ab7da172ad4c1e65d2a54b8bac7491fcd7927685b17b09a05'
EXPECTED_V32_SHA='ff131ff8ce1d5ba7c3be42c8d6acdbb6f64a898d51fe6c64771f29e91ae5543a'

def sha256(p:pathlib.Path)->str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def replace_once(s,old,new):
    n=s.count(old)
    if n!=1: raise RuntimeError(f'expected exactly one occurrence, found {n}: {old[:120]!r}')
    return s.replace(old,new,1)

def build(src:pathlib.Path,out:pathlib.Path):
    got=sha256(src)
    if got!=ACCEPTED_V30_SHA: raise RuntimeError(f'accepted V30 source hash mismatch expected={ACCEPTED_V30_SHA} actual={got}')
    s=src.read_text(encoding='utf-8-sig')
    s=replace_once(s,'#define MT5Q_RELEASE_ID "v30_ml_dl_feature_lake_v1"','#define MT5Q_RELEASE_ID "v32_deep_mlp_keep_sweep_usd40_continuous_v1"')
    s=replace_once(s,
        'input string InpOutputTag = "ml_dl_feature_lake_v1";',
        'input string InpOutputTag = "v32_deep_mlp_keep_sweep_usd40_continuous_v1";\n'
        'input int    InpV32GateBit = -1; // -1 baseline; 0 MLP50; 1 MLP60; 2 MLP70; 3 MLP80; 4 MLP90\n'
        'input string InpV32GateTapeFile = "mt5_quant\\\\inputs\\\\v32_mlp_keep_tape.csv";\n'
        'input bool   InpV32ContinuousUsd40 = true; // book 3 carries capital month-to-month; EOM liquidation retained'
    )
    gate_block=r'''int g_v32_gate_handle=INVALID_HANDLE;
datetime g_v32_gate_time=0;
int g_v32_gate_long[CANDIDATE_COUNT];
int g_v32_gate_short[CANDIDATE_COUNT];
bool g_v32_gate_eof=false;
double g_v32_month_start_balance[TOTAL_BOOKS];

bool V32ReadGateRow()
{
   if(g_v32_gate_handle==INVALID_HANDLE || FileIsEnding(g_v32_gate_handle)){ g_v32_gate_eof=true; return false; }
   string ts=FileReadString(g_v32_gate_handle);
   if(ts==""){ g_v32_gate_eof=true; return false; }
   datetime t=StringToTime(ts);
   if(t<=0){ g_v32_gate_eof=true; return false; }
   for(int ci=0;ci<CANDIDATE_COUNT;++ci)
   {
      g_v32_gate_long[ci]=(int)FileReadNumber(g_v32_gate_handle);
      g_v32_gate_short[ci]=(int)FileReadNumber(g_v32_gate_handle);
   }
   g_v32_gate_time=t;
   return true;
}

bool V32InitGateTape()
{
   ArrayInitialize(g_v32_gate_long,0);
   ArrayInitialize(g_v32_gate_short,0);
   ArrayInitialize(g_v32_month_start_balance,0.0);
   g_v32_gate_time=0; g_v32_gate_eof=false;
   if(InpV32GateBit<0) return true;
   if(InpV32GateBit>4){ PrintFormat("V32 invalid gate bit=%d",InpV32GateBit); return false; }
   g_v32_gate_handle=FileOpen(InpV32GateTapeFile,FILE_READ|FILE_CSV|FILE_ANSI|FILE_COMMON,',');
   if(g_v32_gate_handle==INVALID_HANDLE){ PrintFormat("V32 gate tape open failed file=%s err=%d",InpV32GateTapeFile,GetLastError()); return false; }
   for(int k=0;k<1+2*CANDIDATE_COUNT;++k) FileReadString(g_v32_gate_handle);
   if(!V32ReadGateRow()){ Print("V32 gate tape contains no data rows"); return false; }
   PrintFormat("V32 gate tape ready bit=%d first_time=%s",InpV32GateBit,TimeToString(g_v32_gate_time,TIME_DATE|TIME_MINUTES));
   return true;
}

bool V32GateAllows(const datetime barTime,const int ci,const int dir)
{
   if(InpV32GateBit<0) return true;
   if(ci<0 || ci>=CANDIDATE_COUNT || dir==0 || g_v32_gate_handle==INVALID_HANDLE) return false;
   while(g_v32_gate_time>0 && g_v32_gate_time<barTime)
   {
      if(!V32ReadGateRow()){ g_v32_gate_time=0; return false; }
   }
   if(g_v32_gate_time!=barTime) return false;
   int mask=(dir>0 ? g_v32_gate_long[ci] : g_v32_gate_short[ci]);
   int bit=(1<<InpV32GateBit);
   return ((mask&bit)!=0);
}

'''
    s=replace_once(s,'int hEma10=INVALID_HANDLE;',gate_block+'int hEma10=INVALID_HANDLE;')
    s=replace_once(s,'   return "usd40_r1p0_cent";','   return InpV32ContinuousUsd40 ? "usd40_r1p0_cent_continuous" : "usd40_r1p0_cent";')
    reset_old='''         int ix=BI(ci,bi); ResetPositionFields(B[ix]);
         B[ix].balance=BookInitial(bi); B[ix].peak_mtm=B[ix].balance; B[ix].max_mtm_dd_pct=0;'''
    reset_new='''         int ix=BI(ci,bi);
         double v32Start=BookInitial(bi); double v32Peak=v32Start; double v32MaxDd=0.0;
         if(InpV32ContinuousUsd40 && bi==3 && g_months_written>0){ v32Start=B[ix].balance; v32Peak=B[ix].peak_mtm; v32MaxDd=B[ix].max_mtm_dd_pct; }
         ResetPositionFields(B[ix]);
         B[ix].balance=v32Start; g_v32_month_start_balance[ix]=B[ix].balance;
         B[ix].peak_mtm=v32Peak; B[ix].max_mtm_dd_pct=v32MaxDd;'''
    s=replace_once(s,reset_old,reset_new)
    s=replace_once(s,'         int ix=BI(ci,bi); double initial=BookInitial(bi); double net=B[ix].balance-initial; double ret=initial>0?100.0*net/initial:0;',
        '         int ix=BI(ci,bi); double initial=(InpV32ContinuousUsd40 && bi==3 ? g_v32_month_start_balance[ix] : BookInitial(bi)); double net=B[ix].balance-initial; double ret=initial>0?100.0*net/initial:0;')
    old_manifest='x+="bar_feature_lake=1\\r\\nbar_feature_schema=v30_bar_features_v1\\r\\nfuture_labels_in_ea=0\\r\\n";'
    s=replace_once(s,old_manifest,old_manifest+'\n   x+="v32_deep_mlp_keep_sweep=1\\r\\ngate_bit="+IntegerToString(InpV32GateBit)+"\\r\\ngate_tape="+InpV32GateTapeFile+"\\r\\ncontinuous_usd40="+(InpV32ContinuousUsd40?"1":"0")+"\\r\\ncontinuous_book=usd40_r1p0_cent_continuous\\r\\nmonthly_liquidation=1\\r\\n";')
    s=replace_once(s,'BuildCatalog(); LoadAdaptiveState(); if(!CreateHandles()) return INIT_FAILED;','BuildCatalog(); LoadAdaptiveState(); if(!V32InitGateTape()) return INIT_FAILED; if(!CreateHandles()) return INIT_FAILED;')
    rel='Rel(hH1Ema50); Rel(hH1Ema200); Rel(hRsi2); Rel(hRsi14); Rel(hMacd); Rel(hAdx); Rel(hBands);'
    s=replace_once(s,rel,rel+'\n   if(g_v32_gate_handle!=INVALID_HANDLE){ FileClose(g_v32_gate_handle); g_v32_gate_handle=INVALID_HANDLE; }')
    gate_point='if(InpUseTradeSessionPreflight && !TradeSessionOpenAt(tick.time)){ C[ci].session_reject++; continue; }\n\n      C[ci].selected_signals++;'
    s=replace_once(s,gate_point,'if(InpUseTradeSessionPreflight && !TradeSessionOpenAt(tick.time)){ C[ci].session_reject++; continue; }\n      if(!V32GateAllows(r[0].time,ci,dir)){ C[ci].quality_reject++; continue; }\n\n      C[ci].selected_signals++;')
    s=s.replace('ML_DL_FEATURE_LAKE_V1 START','V32_DEEP_MLP_KEEP_SWEEP START').replace('ML_DL_FEATURE_LAKE_V1 DONE','V32_DEEP_MLP_KEEP_SWEEP DONE')
    if re.search(r'OrderSend\(|OrderSendAsync\(|\bCTrade\b|trade\.Buy\(|trade\.Sell\(',s): raise RuntimeError('forbidden native-order token introduced')
    if 'MQLInfoInteger(MQL_TESTER)' not in s: raise RuntimeError('tester-only guard missing')
    out.parent.mkdir(parents=True,exist_ok=True); out.write_text(s,encoding='utf-8',newline='\r\n')
    built=sha256(out)
    if built!=EXPECTED_V32_SHA: raise RuntimeError(f'V32 deterministic hash mismatch expected={EXPECTED_V32_SHA} actual={built}')
    print(f'V32 source PASS sha256={built} path={out}')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--output',required=True);a=ap.parse_args();build(pathlib.Path(a.source),pathlib.Path(a.output))
if __name__=='__main__': raise SystemExit(main())
