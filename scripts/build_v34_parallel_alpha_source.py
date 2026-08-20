#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,pathlib,re
ACCEPTED='4222120de5ded19ab7da172ad4c1e65d2a54b8bac7491fcd7927685b17b09a05'

def sha(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def one(s,a,b):
 n=s.count(a)
 if n!=1: raise RuntimeError(f'expected 1 occurrence got {n}: {a[:100]!r}')
 return s.replace(a,b,1)

def build(src,out):
 src=pathlib.Path(src);out=pathlib.Path(out)
 if sha(src)!=ACCEPTED: raise RuntimeError('accepted V30 source hash mismatch')
 s=src.read_text(encoding='utf-8-sig')
 s=one(s,'#define MT5Q_RELEASE_ID "v30_ml_dl_feature_lake_v1"','#define MT5Q_RELEASE_ID "v34_parallel_alpha_lab_v1"')
 s=one(s,'#define CANDIDATE_COUNT 12','#define CANDIDATE_COUNT 17')
 s=one(s,'input string InpOutputTag = "ml_dl_feature_lake_v1";','input string InpOutputTag = "v34_parallel_alpha_lab_v1";')
 s=one(s,'   PP_SLOW_MOM=8\n};','   PP_SLOW_MOM=8,\n   PP_V34_SMC_ICT=9,\n   PP_V34_PRICE_ACTION=10,\n   PP_V34_WYCKOFF=11,\n   PP_V34_MICROSTRUCTURE=12,\n   PP_V34_CONFLUENCE=13\n};')
 s=one(s,'   SIG_SLOW_MOM=256\n};','   SIG_SLOW_MOM=256,\n   SIG_V34_SMC_ICT=512,\n   SIG_V34_PRICE_ACTION=1024,\n   SIG_V34_WYCKOFF=2048,\n   SIG_V34_MICROSTRUCTURE=4096,\n   SIG_V34_CONFLUENCE=8192\n};')
 s=one(s,'input bool   InpWriteBarFeatures = true;','input bool   InpWriteBarFeatures = false;')
 s=one(s,'input bool   InpUseTradeSessionPreflight = true;',
'''input bool   InpUseTradeSessionPreflight = true;
input string InpV34AlphaTapeFile = "mt5_quant\\inputs\\v34_parallel_alpha_tape.csv";
input bool   InpV34ContinuousUsd40 = true;
input bool   InpV34WriteIntraTradeTelemetry = true;''')
 tape=r'''int g_v34_tape_handle=INVALID_HANDLE;
datetime g_v34_tape_time=0;
int g_v34_dir[5];
double g_v34_score[5];
bool g_v34_tape_eof=false;
double g_v34_month_start_balance[TOTAL_BOOKS];
datetime g_v34_last_telemetry_bar=0;

bool V34ReadTapeRow()
{
   if(g_v34_tape_handle==INVALID_HANDLE || FileIsEnding(g_v34_tape_handle)){ g_v34_tape_eof=true; return false; }
   string ts=FileReadString(g_v34_tape_handle);
   if(ts==""){ g_v34_tape_eof=true; return false; }
   datetime t=StringToTime(ts); if(t<=0){ g_v34_tape_eof=true; return false; }
   for(int k=0;k<5;++k){ g_v34_dir[k]=(int)FileReadNumber(g_v34_tape_handle); g_v34_score[k]=FileReadNumber(g_v34_tape_handle); }
   g_v34_tape_time=t; return true;
}

bool V34InitTape()
{
   ArrayInitialize(g_v34_dir,0); ArrayInitialize(g_v34_score,0.0); ArrayInitialize(g_v34_month_start_balance,0.0);
   g_v34_tape_handle=FileOpen(InpV34AlphaTapeFile,FILE_READ|FILE_CSV|FILE_ANSI|FILE_COMMON,',');
   if(g_v34_tape_handle==INVALID_HANDLE){ PrintFormat("V34 alpha tape open failed file=%s err=%d",InpV34AlphaTapeFile,GetLastError()); return false; }
   for(int k=0;k<11;++k) FileReadString(g_v34_tape_handle);
   if(!V34ReadTapeRow()){ Print("V34 alpha tape contains no data rows"); return false; }
   PrintFormat("V34 alpha tape ready first_time=%s",TimeToString(g_v34_tape_time,TIME_DATE|TIME_MINUTES));
   return true;
}

bool V34SyncTape(const datetime barTime)
{
   while(g_v34_tape_time>0 && g_v34_tape_time<barTime)
   {
      if(!V34ReadTapeRow()){ g_v34_tape_time=0; return false; }
   }
   return g_v34_tape_time==barTime;
}

bool V34SpecialistSignal(const int kind,int &direction,int &activeMask)
{
   direction=0; activeMask=0; int k=-1; int mask=0;
   if(kind==PP_V34_SMC_ICT){ k=0; mask=SIG_V34_SMC_ICT; }
   else if(kind==PP_V34_PRICE_ACTION){ k=1; mask=SIG_V34_PRICE_ACTION; }
   else if(kind==PP_V34_WYCKOFF){ k=2; mask=SIG_V34_WYCKOFF; }
   else if(kind==PP_V34_MICROSTRUCTURE){ k=3; mask=SIG_V34_MICROSTRUCTURE; }
   else if(kind==PP_V34_CONFLUENCE){ k=4; mask=SIG_V34_CONFLUENCE; }
   else return false;
   direction=g_v34_dir[k]; if(direction!=0) activeMask=mask; return true;
}

'''
 s=one(s,'int hEma10=INVALID_HANDLE;',tape+'int hEma10=INVALID_HANDLE;')
 marker='''   // Change-proxy probe: fast5 vs slow20 divergence >=0.30R switches to fast score; otherwise slow score.
   SetupAdaptiveRouter(11,"adaptive_cp_fast5_slow20_thr0p30",4,0.05,0.00);
}'''
 repl='''   // Change-proxy probe: fast5 vs slow20 divergence >=0.30R switches to fast score; otherwise slow score.
   SetupAdaptiveRouter(11,"adaptive_cp_fast5_slow20_thr0p30",4,0.05,0.00);

   // V34 independent specialist entries. Signals come from a causal closed-bar tape and share the same 2ATR / peak-lock / 4R exit geometry.
   SetupCandidate(12,"v34_smc_ict_causal","smc_ict_causal",PP_V34_SMC_ICT,0.0,-1,false,false,0.0,0,SIG_V34_SMC_ICT);
   SetupCandidate(13,"v34_price_action_causal","price_action_causal",PP_V34_PRICE_ACTION,0.0,-1,false,false,0.0,0,SIG_V34_PRICE_ACTION);
   SetupCandidate(14,"v34_wyckoff_proxy_causal","wyckoff_proxy_causal",PP_V34_WYCKOFF,0.0,-1,false,false,0.0,0,SIG_V34_WYCKOFF);
   SetupCandidate(15,"v34_tick_microstructure_proxy","tick_microstructure_proxy",PP_V34_MICROSTRUCTURE,0.0,-1,false,false,0.0,0,SIG_V34_MICROSTRUCTURE);
   SetupCandidate(16,"v34_specialist_confluence","parallel_specialist_confluence",PP_V34_CONFLUENCE,0.0,-1,false,false,0.0,0,SIG_V34_CONFLUENCE);
}'''
 s=one(s,marker,repl)
 s=one(s,'   if(st.kind==PP_SLOW_MOM){ if(!slowReady) return false; direction=slowDir; if(direction!=0) activeMask=SIG_SLOW_MOM; return true; }\n   return false;',
'''   if(st.kind==PP_SLOW_MOM){ if(!slowReady) return false; direction=slowDir; if(direction!=0) activeMask=SIG_SLOW_MOM; return true; }
   if(st.kind>=PP_V34_SMC_ICT && st.kind<=PP_V34_CONFLUENCE) return V34SpecialistSignal(st.kind,direction,activeMask);
   return false;''')
 s=one(s,'   return "usd40_r1p0_cent";','   return InpV34ContinuousUsd40 ? "usd40_r1p0_cent_continuous" : "usd40_r1p0_cent";')
 old='''         int ix=BI(ci,bi); ResetPositionFields(B[ix]);
         B[ix].balance=BookInitial(bi); B[ix].peak_mtm=B[ix].balance; B[ix].max_mtm_dd_pct=0;'''
 new='''         int ix=BI(ci,bi);
         double v34Start=BookInitial(bi); double v34Peak=v34Start; double v34MaxDd=0.0;
         if(InpV34ContinuousUsd40 && bi==3 && g_months_written>0){ v34Start=B[ix].balance; v34Peak=B[ix].peak_mtm; v34MaxDd=B[ix].max_mtm_dd_pct; }
         ResetPositionFields(B[ix]); B[ix].balance=v34Start; g_v34_month_start_balance[ix]=B[ix].balance;
         B[ix].peak_mtm=v34Peak; B[ix].max_mtm_dd_pct=v34MaxDd;'''
 s=one(s,old,new)
 s=one(s,'         int ix=BI(ci,bi); double initial=BookInitial(bi); double net=B[ix].balance-initial; double ret=initial>0?100.0*net/initial:0;',
'         int ix=BI(ci,bi); double initial=(InpV34ContinuousUsd40 && bi==3 ? g_v34_month_start_balance[ix] : BookInitial(bi)); double net=B[ix].balance-initial; double ret=initial>0?100.0*net/initial:0;')
 telemetry_func=r'''
string V34IntraTradeFile(){ return g_run_folder+"\intra_trade_m15.csv"; }

void V34EnsureIntraTradeFile()
{
   if(!InpV34WriteIntraTradeTelemetry) return;
   string f=V34IntraTradeFile();
   if(FileIsExist(f,FILE_COMMON)) return;
   int h=FileOpen(f,FILE_WRITE|FILE_CSV|FILE_ANSI|FILE_COMMON,','); if(h==INVALID_HANDLE) return;
   FileWrite(h,"time","month","candidate","family","book","entry_time","direction","age_seconds","unrealized_r","peak_r","mae_r","giveback_from_peak_r","stop_r","tp_r","balance","entry_risk_cash","signal_sources");
   FileClose(h);
}

void V34AppendIntraTradeTelemetry(const datetime barTime,const MqlTick &tick)
{
   if(!InpV34WriteIntraTradeTelemetry || barTime<=0 || barTime==g_v34_last_telemetry_bar) return;
   g_v34_last_telemetry_bar=barTime;
   string f=V34IntraTradeFile(); int h=FileOpen(f,FILE_READ|FILE_WRITE|FILE_CSV|FILE_ANSI|FILE_COMMON,','); if(h==INVALID_HANDLE) return;
   FileSeek(h,0,SEEK_END);
   for(int ci=0;ci<CANDIDATE_COUNT;++ci)
   {
      for(int z=0;z<2;++z)
      {
         int bi=(z==0?0:3); int ix=BI(ci,bi); if(!B[ix].open) continue;
         double px=B[ix].direction>0?tick.bid:tick.ask; double ur=PriceR(B[ix],px);
         double stopR=PriceR(B[ix],B[ix].stop); double tpR=PriceR(B[ix],B[ix].tp);
         double peak=MathMax(B[ix].mfe_r,ur); double gb=MathMax(0.0,peak-ur);
         long age=(long)MathMax(0.0,(double)(barTime-B[ix].entry_time));
         FileWrite(h,TimeToString(barTime,TIME_DATE|TIME_MINUTES|TIME_SECONDS),g_month_tag,C[ci].name,C[ci].family,BookName(bi),
                   TimeToString(B[ix].entry_time,TIME_DATE|TIME_MINUTES|TIME_SECONDS),B[ix].direction>0?"LONG":"SHORT",age,
                   DoubleToString(ur,6),DoubleToString(peak,6),DoubleToString(B[ix].mae_r,6),DoubleToString(gb,6),
                   DoubleToString(stopR,6),DoubleToString(tpR,6),DoubleToString(B[ix].balance,6),DoubleToString(B[ix].initial_risk_cash,6),B[ix].signal_sources);
      }
   }
   FileClose(h);
}

'''
 s=one(s,'void EnsureFiles()',telemetry_func+'void EnsureFiles()')
 s=one(s,'void EnsureFiles()\n{\n   if(InpWriteBarFeatures) EnsureBarFeatureFile();','void EnsureFiles()\n{\n   V34EnsureIntraTradeFile();\n   if(InpWriteBarFeatures) EnsureBarFeatureFile();')
 s=one(s,'   g_last_tick=tick; g_have_tick=true;\n   ProcessExits(tick);','   g_last_tick=tick; g_have_tick=true;\n   datetime v34bt[1]; if(CopyTime(_Symbol,_Period,0,1,v34bt)==1 && v34bt[0]!=g_v34_last_telemetry_bar) V34AppendIntraTradeTelemetry(v34bt[0],tick);\n   ProcessExits(tick);')
 s=one(s,'x+="candidate_count=12\\r\\nbook_count=4\\r\\nmonthly_reset=1\\r\\nmonths_written="+IntegerToString((int)g_months_written)+"\\r\\n";',
'x+="candidate_count=17\\r\\nbook_count=4\\r\\nmonthly_reset=1\\r\\nmonths_written="+IntegerToString((int)g_months_written)+"\\r\\n";')
 s=one(s,'x+="books=norm10k_r0p5_continuous,usd40_r0p5_cent,usd40_r0p75_cent,usd40_r1p0_cent\\r\\n";',
'x+="books=norm10k_r0p5_continuous,usd40_r0p5_cent,usd40_r0p75_cent,usd40_r1p0_cent_continuous\\r\\n";')
 s=one(s,'   x+="bar_feature_lake=1\\r\\nbar_feature_schema=v30_bar_features_v1\\r\\nfuture_labels_in_ea=0\\r\\n";',
'''   x+="bar_feature_lake=1\r\nbar_feature_schema=v30_bar_features_v1\r\nfuture_labels_in_ea=0\r\n";
   x+="v34_parallel_alpha_lab=1\r\nalpha_tape="+InpV34AlphaTapeFile+"\r\ncontinuous_usd40="+(InpV34ContinuousUsd40?"1":"0")+"\r\n";
   x+="v34_specialists=smc_ict_causal,price_action_causal,wyckoff_proxy_causal,tick_microstructure_proxy,parallel_specialist_confluence\r\n";
   x+="microstructure_note=L1_tick_path_proxy_not_true_L2_L3_orderflow\r\n";''')
 s=one(s,'BuildCatalog(); LoadAdaptiveState(); if(!CreateHandles()) return INIT_FAILED;',
'BuildCatalog(); LoadAdaptiveState(); if(!V34InitTape()) return INIT_FAILED; if(!CreateHandles()) return INIT_FAILED;')
 rel='Rel(hH1Ema50); Rel(hH1Ema200); Rel(hRsi2); Rel(hRsi14); Rel(hMacd); Rel(hAdx); Rel(hBands);'
 s=one(s,rel,rel+'\n   if(g_v34_tape_handle!=INVALID_HANDLE){ FileClose(g_v34_tape_handle); g_v34_tape_handle=INVALID_HANDLE; }')
 sync_marker='''   bool slowReady=SignalSlowMomentum(r,tick.time,slowDir);

   if(InpWriteBarFeatures) AppendBarFeatures'''
 s=one(s,sync_marker,'''   bool slowReady=SignalSlowMomentum(r,tick.time,slowDir);
   if(!V34SyncTape(r[0].time)){ for(int ci=12;ci<CANDIDATE_COUNT;++ci) C[ci].data_reject++; }

   if(InpWriteBarFeatures) AppendBarFeatures''')
 s=s.replace('ML_DL_FEATURE_LAKE_V1 START','V34_PARALLEL_ALPHA_LAB START').replace('ML_DL_FEATURE_LAKE_V1 DONE','V34_PARALLEL_ALPHA_LAB DONE')
 s=s.replace('format=mt5_quant_ml_dl_feature_lake_v1','format=mt5_quant_v34_parallel_alpha_lab_v1').replace('source_file=MlDlFeatureLakeV1.mq5','source_file=V34ParallelAlphaLab.mq5')
 if re.search(r'OrderSend\(|OrderSendAsync\(|\bCTrade\b|trade\.Buy\(|trade\.Sell\(',s): raise RuntimeError('forbidden native order token')
 if 'MQLInfoInteger(MQL_TESTER)' not in s: raise RuntimeError('tester-only guard missing')
 if s.count('SetupCandidate(12')!=1 or s.count('SetupCandidate(16')!=1: raise RuntimeError('V34 catalog insertion failed')
 out.parent.mkdir(parents=True,exist_ok=True); out.write_text(s,encoding='utf-8',newline='\r\n')
 print('V34 source PASS sha256='+sha(out)+' path='+str(out))

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--output',required=True);a=ap.parse_args();build(a.source,a.output)
if __name__=='__main__': main()
