#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,pathlib,re
ACCEPTED_V34='8d3700911e2fe680a2a4b02994680e812825ab6cf517bf509aaa4ac230526a77'
def sha(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def one(s,a,b):
 n=s.count(a)
 if n!=1: raise RuntimeError(f'expected 1 occurrence got {n}: {a[:100]!r}')
 return s.replace(a,b,1)
def build(src,out):
 src=pathlib.Path(src);out=pathlib.Path(out)
 if sha(src)!=ACCEPTED_V34: raise RuntimeError(f'V34 source hash mismatch actual={sha(src)}')
 s=src.read_text(encoding='utf-8-sig')
 s=one(s,'#define MT5Q_RELEASE_ID "v34_parallel_alpha_lab_v1"','#define MT5Q_RELEASE_ID "v35_ai_all_expert_meta_router_v1"')
 s=one(s,'#define CANDIDATE_COUNT 17','#define CANDIDATE_COUNT 18')
 s=one(s,'input string InpOutputTag = "v34_parallel_alpha_lab_v1";','input string InpOutputTag = "v35_ai_all_expert_meta_router_v1";')
 s=one(s,'   PP_V34_CONFLUENCE=13\n};','   PP_V34_CONFLUENCE=13,\n   PP_V35_META_ROUTER=14\n};')
 s=one(s,'   SIG_V34_CONFLUENCE=8192\n};','   SIG_V34_CONFLUENCE=8192,\n   SIG_V35_META_ROUTER=16384\n};')
 s=one(s,'input bool   InpV34WriteIntraTradeTelemetry = true;','''input bool   InpV34WriteIntraTradeTelemetry = true;
input string InpV35RouterTapeFile = "mt5_quant\\inputs\\v35_specialist_router_tape.csv";''')
 router=r'''int g_v35_router_handle=INVALID_HANDLE;
datetime g_v35_router_time=0;
int g_v35_router_dir=0;
int g_v35_router_source=-1;
double g_v35_router_score=-999.0;
double g_v35_router_threshold=999.0;

bool V35ReadRouterRow()
{
   if(g_v35_router_handle==INVALID_HANDLE || FileIsEnding(g_v35_router_handle)) return false;
   string ts=FileReadString(g_v35_router_handle); if(ts=="") return false;
   datetime t=StringToTime(ts); if(t<=0) return false;
   g_v35_router_dir=(int)FileReadNumber(g_v35_router_handle);
   g_v35_router_source=(int)FileReadNumber(g_v35_router_handle);
   g_v35_router_score=FileReadNumber(g_v35_router_handle);
   g_v35_router_threshold=FileReadNumber(g_v35_router_handle);
   g_v35_router_time=t; return true;
}

bool V35InitRouterTape()
{
   g_v35_router_handle=FileOpen(InpV35RouterTapeFile,FILE_READ|FILE_CSV|FILE_ANSI|FILE_COMMON,',');
   if(g_v35_router_handle==INVALID_HANDLE){ PrintFormat("V35 router tape open failed file=%s err=%d",InpV35RouterTapeFile,GetLastError()); return false; }
   for(int k=0;k<5;++k) FileReadString(g_v35_router_handle);
   if(!V35ReadRouterRow()){ Print("V35 router tape has no rows"); return false; }
   return true;
}

bool V35SyncRouter(const datetime barTime)
{
   while(g_v35_router_time>0 && g_v35_router_time<barTime){ if(!V35ReadRouterRow()){ g_v35_router_time=0; return false; } }
   return g_v35_router_time==barTime;
}

'''
 s=one(s,'int g_v34_tape_handle=INVALID_HANDLE;',router+'int g_v34_tape_handle=INVALID_HANDLE;')
 s=one(s,'   SetupCandidate(16,"v34_specialist_confluence","parallel_specialist_confluence",PP_V34_CONFLUENCE,0.0,-1,false,false,0.0,0,SIG_V34_CONFLUENCE);\n}',
'''   SetupCandidate(16,"v34_specialist_confluence","parallel_specialist_confluence",PP_V34_CONFLUENCE,0.0,-1,false,false,0.0,0,SIG_V34_CONFLUENCE);
   SetupCandidate(17,"v35_ai_all_expert_meta_router","ai_all_expert_meta_router",PP_V35_META_ROUTER,0.0,-1,false,false,0.0,0,SIG_V35_META_ROUTER);
}''')
 s=one(s,'   if(st.kind>=PP_V34_SMC_ICT && st.kind<=PP_V34_CONFLUENCE) return V34SpecialistSignal(st.kind,direction,activeMask);\n   return false;',
'''   if(st.kind>=PP_V34_SMC_ICT && st.kind<=PP_V34_CONFLUENCE) return V34SpecialistSignal(st.kind,direction,activeMask);
   if(st.kind==PP_V35_META_ROUTER){ direction=g_v35_router_dir; if(direction!=0) activeMask=SIG_V35_META_ROUTER; return true; }
   return false;''')
 s=one(s,'BuildCatalog(); LoadAdaptiveState(); if(!V34InitTape()) return INIT_FAILED; if(!CreateHandles()) return INIT_FAILED;',
'BuildCatalog(); LoadAdaptiveState(); if(!V34InitTape()) return INIT_FAILED; if(!V35InitRouterTape()) return INIT_FAILED; if(!CreateHandles()) return INIT_FAILED;')
 s=one(s,'   if(!V34SyncTape(r[0].time)){ for(int ci=12;ci<CANDIDATE_COUNT;++ci) C[ci].data_reject++; }',
'''   if(!V34SyncTape(r[0].time)){ for(int ci=12;ci<=16;++ci) C[ci].data_reject++; }
   if(!V35SyncRouter(r[0].time)) C[17].data_reject++;''')
 s=one(s,'   if(g_v34_tape_handle!=INVALID_HANDLE){ FileClose(g_v34_tape_handle); g_v34_tape_handle=INVALID_HANDLE; }',
'''   if(g_v34_tape_handle!=INVALID_HANDLE){ FileClose(g_v34_tape_handle); g_v34_tape_handle=INVALID_HANDLE; }
   if(g_v35_router_handle!=INVALID_HANDLE){ FileClose(g_v35_router_handle); g_v35_router_handle=INVALID_HANDLE; }''')
 s=s.replace('V34_PARALLEL_ALPHA_LAB START','V35_AI_SPECIALIST_META_ROUTER START').replace('V34_PARALLEL_ALPHA_LAB DONE','V35_AI_SPECIALIST_META_ROUTER DONE')
 s=s.replace('format=mt5_quant_v34_parallel_alpha_lab_v1','format=mt5_quant_v35_ai_all_expert_meta_router_v1').replace('source_file=V34ParallelAlphaLab.mq5','source_file=V35AiSpecialistMetaRouter.mq5')
 s=s.replace('candidate_count=17','candidate_count=18')
 s=one(s,'   x+="microstructure_note=L1_tick_path_proxy_not_true_L2_L3_orderflow\\r\\n";',
'''   x+="microstructure_note=L1_tick_path_proxy_not_true_L2_L3_orderflow\r\n";
   x+="intra_trade_m15="+(InpV34WriteIntraTradeTelemetry?"1":"0")+"\r\n";
   x+="v35_ai_all_expert_meta_router=1\r\nrouter_tape="+InpV35RouterTapeFile+"\r\n";''')
 if re.search(r'OrderSend\(|OrderSendAsync\(|\bCTrade\b|trade\.Buy\(|trade\.Sell\(',s): raise RuntimeError('forbidden order token')
 if 'MQLInfoInteger(MQL_TESTER)' not in s: raise RuntimeError('tester guard missing')
 out.parent.mkdir(parents=True,exist_ok=True);out.write_text(s,encoding='utf-8',newline='\r\n');print('V35 source PASS sha256='+sha(out)+' path='+str(out))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--output',required=True);a=ap.parse_args();build(a.source,a.output)
if __name__=='__main__': main()
