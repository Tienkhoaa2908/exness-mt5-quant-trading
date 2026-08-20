#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, pathlib, re, sys

ACCEPTED_V30_SHA = "4222120de5ded19ab7da172ad4c1e65d2a54b8bac7491fcd7927685b17b09a05"
EXPECTED_V31_SHA = "8dccbe939bb93a188675c4c61f2030f335a311113d97c813ec1e021ebcc052eb"

def sha256(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def replace_once(s: str, old: str, new: str) -> str:
    n = s.count(old)
    if n != 1:
        raise RuntimeError(f"expected exactly one occurrence, found {n}: {old[:100]!r}")
    return s.replace(old, new, 1)

def build(src: pathlib.Path, out: pathlib.Path) -> None:
    got = sha256(src)
    if got != ACCEPTED_V30_SHA:
        raise RuntimeError(f"accepted V30 source hash mismatch expected={ACCEPTED_V30_SHA} actual={got}")
    s = src.read_text(encoding="utf-8-sig")
    s = replace_once(s, '#define MT5Q_RELEASE_ID "v30_ml_dl_feature_lake_v1"', '#define MT5Q_RELEASE_ID "v31_mt5_model_gate_lab_v1"')
    s = replace_once(
        s,
        'input string InpOutputTag = "ml_dl_feature_lake_v1";',
        'input string InpOutputTag = "v31_mt5_model_gate_lab_v1";\n'
        'input int    InpV31GateBit = -1; // -1 baseline; 0 CatBoost; 1 ExtraTrees; 2 MLP; 3 LinearSVM; 4 CB_AND_ET; 5 majority_2of4\n'
        'input string InpV31GateTapeFile = "mt5_quant\\\\inputs\\\\v31_gate_tape.csv";'
    )
    gate_block = r'''int g_v31_gate_handle=INVALID_HANDLE;
datetime g_v31_gate_time=0;
int g_v31_gate_long[CANDIDATE_COUNT];
int g_v31_gate_short[CANDIDATE_COUNT];
bool g_v31_gate_eof=false;

bool V31ReadGateRow()
{
   if(g_v31_gate_handle==INVALID_HANDLE || FileIsEnding(g_v31_gate_handle)){ g_v31_gate_eof=true; return false; }
   string ts=FileReadString(g_v31_gate_handle);
   if(ts==""){ g_v31_gate_eof=true; return false; }
   datetime t=StringToTime(ts);
   if(t<=0){ g_v31_gate_eof=true; return false; }
   for(int ci=0;ci<CANDIDATE_COUNT;++ci)
   {
      g_v31_gate_long[ci]=(int)FileReadNumber(g_v31_gate_handle);
      g_v31_gate_short[ci]=(int)FileReadNumber(g_v31_gate_handle);
   }
   g_v31_gate_time=t;
   return true;
}

bool V31InitGateTape()
{
   ArrayInitialize(g_v31_gate_long,0);
   ArrayInitialize(g_v31_gate_short,0);
   g_v31_gate_time=0; g_v31_gate_eof=false;
   if(InpV31GateBit<0) return true;
   if(InpV31GateBit>5){ PrintFormat("V31 invalid gate bit=%d",InpV31GateBit); return false; }
   g_v31_gate_handle=FileOpen(InpV31GateTapeFile,FILE_READ|FILE_CSV|FILE_ANSI|FILE_COMMON,',');
   if(g_v31_gate_handle==INVALID_HANDLE){ PrintFormat("V31 gate tape open failed file=%s err=%d",InpV31GateTapeFile,GetLastError()); return false; }
   for(int k=0;k<1+2*CANDIDATE_COUNT;++k) FileReadString(g_v31_gate_handle); // header
   if(!V31ReadGateRow()){ Print("V31 gate tape contains no data rows"); return false; }
   PrintFormat("V31 gate tape ready bit=%d first_time=%s",InpV31GateBit,TimeToString(g_v31_gate_time,TIME_DATE|TIME_MINUTES));
   return true;
}

bool V31GateAllows(const datetime barTime,const int ci,const int dir)
{
   if(InpV31GateBit<0) return true;
   if(ci<0 || ci>=CANDIDATE_COUNT || dir==0 || g_v31_gate_handle==INVALID_HANDLE) return false;
   while(g_v31_gate_time>0 && g_v31_gate_time<barTime)
   {
      if(!V31ReadGateRow()){ g_v31_gate_time=0; return false; }
   }
   if(g_v31_gate_time!=barTime) return false;
   int mask=(dir>0 ? g_v31_gate_long[ci] : g_v31_gate_short[ci]);
   int bit=(1<<InpV31GateBit);
   return ((mask&bit)!=0);
}

'''
    s = replace_once(s, 'int hEma10=INVALID_HANDLE;', gate_block + 'int hEma10=INVALID_HANDLE;')
    old_manifest = 'x+="bar_feature_lake=1\\r\\nbar_feature_schema=v30_bar_features_v1\\r\\nfuture_labels_in_ea=0\\r\\n";'
    s = replace_once(s, old_manifest, old_manifest + '\n   x+="v31_model_gate=1\\r\\ngate_bit="+IntegerToString(InpV31GateBit)+"\\r\\ngate_tape="+InpV31GateTapeFile+"\\r\\n";')
    s = replace_once(s, 'BuildCatalog(); LoadAdaptiveState(); if(!CreateHandles()) return INIT_FAILED;', 'BuildCatalog(); LoadAdaptiveState(); if(!V31InitGateTape()) return INIT_FAILED; if(!CreateHandles()) return INIT_FAILED;')
    rel = 'Rel(hH1Ema50); Rel(hH1Ema200); Rel(hRsi2); Rel(hRsi14); Rel(hMacd); Rel(hAdx); Rel(hBands);'
    s = replace_once(s, rel, rel + '\n   if(g_v31_gate_handle!=INVALID_HANDLE){ FileClose(g_v31_gate_handle); g_v31_gate_handle=INVALID_HANDLE; }')
    gate_point = 'if(InpUseTradeSessionPreflight && !TradeSessionOpenAt(tick.time)){ C[ci].session_reject++; continue; }\n\n      C[ci].selected_signals++;'
    s = replace_once(s, gate_point, 'if(InpUseTradeSessionPreflight && !TradeSessionOpenAt(tick.time)){ C[ci].session_reject++; continue; }\n      if(!V31GateAllows(r[0].time,ci,dir)){ C[ci].quality_reject++; continue; }\n\n      C[ci].selected_signals++;')
    s = s.replace('ML_DL_FEATURE_LAKE_V1 START', 'V31_MODEL_GATE_LAB_V1 START').replace('ML_DL_FEATURE_LAKE_V1 DONE', 'V31_MODEL_GATE_LAB_V1 DONE')
    if re.search(r'OrderSend\(|OrderSendAsync\(|\bCTrade\b|trade\.Buy\(|trade\.Sell\(', s):
        raise RuntimeError('forbidden native-order token introduced')
    if 'MQLInfoInteger(MQL_TESTER)' not in s:
        raise RuntimeError('tester-only guard missing')
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(s, encoding='utf-8', newline='\r\n')
    built = sha256(out)
    if built != EXPECTED_V31_SHA:
        raise RuntimeError(f"V31 deterministic hash mismatch expected={EXPECTED_V31_SHA} actual={built}")
    print(f"V31 source PASS sha256={built} path={out}")

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--source', required=True)
    ap.add_argument('--output', required=True)
    a = ap.parse_args()
    build(pathlib.Path(a.source), pathlib.Path(a.output))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
