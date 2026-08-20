#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, pathlib, re

ACCEPTED_V34_SHA = "8bae2c56d43d11809ae96b5ee2f4bfe59007231ed5642bebe73dfbe2db7a7f10"

def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def one(text: str, old: str, new: str) -> str:
    n = text.count(old)
    if n != 1:
        raise RuntimeError(f"expected exactly one occurrence, found {n}: {old[:140]!r}")
    return text.replace(old, new, 1)

def build(source: pathlib.Path, output: pathlib.Path) -> None:
    got = sha256(source)
    if got != ACCEPTED_V34_SHA:
        raise RuntimeError(f"accepted V34 source hash mismatch expected={ACCEPTED_V34_SHA} actual={got}")
    s = source.read_text(encoding="utf-8-sig")

    s = one(s,
        '#define MT5Q_RELEASE_ID "v34_parallel_alpha_lab_v1"',
        '#define MT5Q_RELEASE_ID "v38_fast_harvest_lab_v1"')
    s = one(s, '#define CANDIDATE_COUNT 17', '#define CANDIDATE_COUNT 23')
    s = one(s,
        'input string InpOutputTag = "v34_parallel_alpha_lab_v1";',
        'input string InpOutputTag = "v38_fast_harvest_lab_v1";')
    s = one(s,
        'input bool   InpV34WriteIntraTradeTelemetry = true;',
        'input bool   InpV34WriteIntraTradeTelemetry = true;\n'
        'input bool   InpV38WriteM1FastTelemetry = true;')

    s = one(s,
        '   int slow_mom_hold_seconds;\n   long adaptive_reject;',
        '   int slow_mom_hold_seconds;\n'
        '   int fast_exit_mode;\n'
        '   double fast_target_r;\n'
        '   double fast_arm_r;\n'
        '   double fast_giveback_r;\n'
        '   int fast_timebox_seconds;\n'
        '   long adaptive_reject;')

    s = one(s,
        '   double mfe_r;\n   double mae_r;\n   string signal_sources;',
        '   double mfe_r;\n'
        '   double mae_r;\n'
        '   datetime fast_sample_time;\n'
        '   double fast_last_r;\n'
        '   double fast_last_delta_r;\n'
        '   int fast_sample_count;\n'
        '   datetime v38_prev_m1_time;\n'
        '   double v38_prev_m1_r;\n'
        '   string signal_sources;')

    s = one(s,
        '   C[i].slow_mom_hold_seconds=8*3600;\n   C[i].adaptive_reject=0;',
        '   C[i].slow_mom_hold_seconds=8*3600;\n'
        '   C[i].fast_exit_mode=0;\n'
        '   C[i].fast_target_r=0.0;\n'
        '   C[i].fast_arm_r=0.0;\n'
        '   C[i].fast_giveback_r=0.0;\n'
        '   C[i].fast_timebox_seconds=0;\n'
        '   C[i].adaptive_reject=0;')

    fast_setup = r'''
void SetupV38FastClone(const int i,const string name,const int mode,const double targetR,
                       const double armR,const double givebackR,const int timeboxSeconds)
{
   SetupAdaptiveRouter(i,name,0,0.00,0.00);
   C[i].family="adaptive_shadow_expert_router_fast_harvest";
   C[i].fast_exit_mode=mode;
   C[i].fast_target_r=targetR;
   C[i].fast_arm_r=armR;
   C[i].fast_giveback_r=givebackR;
   C[i].fast_timebox_seconds=timeboxSeconds;
   if(mode==1) C[i].policy_name="v38_fast_tp_"+DoubleToString(targetR,2)+"R";
   else if(mode==2) C[i].policy_name="v38_fast_giveback_"+DoubleToString(givebackR,2)+"R_after_"+DoubleToString(armR,2)+"R";
   else if(mode==3) C[i].policy_name="v38_velocity_decay_after_"+DoubleToString(armR,2)+"R";
   else if(mode==4) C[i].policy_name="v38_timebox_"+IntegerToString(timeboxSeconds/60)+"m";
}

'''
    s = one(s, 'void BuildCatalog()\n{', fast_setup + 'void BuildCatalog()\n{')

    catalog_old = '''   SetupCandidate(16,"v34_specialist_confluence","parallel_specialist_confluence",PP_V34_CONFLUENCE,0.0,-1,false,false,0.0,0,SIG_V34_CONFLUENCE);
}'''
    catalog_new = '''   SetupCandidate(16,"v34_specialist_confluence","parallel_specialist_confluence",PP_V34_CONFLUENCE,0.0,-1,false,false,0.0,0,SIG_V34_CONFLUENCE);

   // V38 clones the accepted adaptive_ewma_hl8_thr0 entry/router logic exactly and changes only exit timing.
   SetupV38FastClone(17,"v38_adaptive_fast_tp0p50",1,0.50,0.0,0.0,0);
   SetupV38FastClone(18,"v38_adaptive_fast_tp0p75",1,0.75,0.0,0.0,0);
   SetupV38FastClone(19,"v38_adaptive_fast_tp1p00",1,1.00,0.0,0.0,0);
   SetupV38FastClone(20,"v38_adaptive_fast_gb0p25_after0p75",2,0.0,0.75,0.25,0);
   SetupV38FastClone(21,"v38_adaptive_velocity_decay_after0p50",3,0.0,0.50,0.0,0);
   SetupV38FastClone(22,"v38_adaptive_timebox30m",4,0.0,0.0,0.0,30*60);
}'''
    s = one(s, catalog_old, catalog_new)

    s = one(s,
        '   b.mfe_r=0; b.mae_r=0; b.signal_sources="";',
        '   b.mfe_r=0; b.mae_r=0; b.fast_sample_time=0; b.fast_last_r=0; b.fast_last_delta_r=0; b.fast_sample_count=0;\n'
        '   b.v38_prev_m1_time=0; b.v38_prev_m1_r=0; b.signal_sources="";')

    fast_exit = r'''
bool V38FastExitTriggered(const int ci,BookState &b,const MqlTick &tick,const double px,string &reason)
{
   reason="";
   if(!b.open || ci<0 || ci>=CANDIDATE_COUNT) return false;
   int mode=C[ci].fast_exit_mode;
   if(mode<=0) return false;
   double r=PriceR(b,px);
   long age=(long)MathMax(0.0,(double)(tick.time-b.entry_time));

   if(mode==1)
   {
      if(C[ci].fast_target_r>0.0 && r>=C[ci].fast_target_r)
      {
         reason="V38_FAST_TP"; return true;
      }
      return false;
   }

   if(mode==2)
   {
      if(C[ci].fast_arm_r>0.0 && b.mfe_r>=C[ci].fast_arm_r &&
         r>0.0 && r<=b.mfe_r-C[ci].fast_giveback_r)
      {
         reason="V38_FAST_GIVEBACK"; return true;
      }
      return false;
   }

   if(mode==3)
   {
      if(b.fast_sample_time<=0)
      {
         b.fast_sample_time=tick.time; b.fast_last_r=r; b.fast_last_delta_r=0.0; b.fast_sample_count=0;
         return false;
      }
      if((tick.time-b.fast_sample_time)>=60)
      {
         double delta=r-b.fast_last_r;
         double prev=b.fast_last_delta_r;
         b.fast_last_r=r; b.fast_last_delta_r=delta; b.fast_sample_time=tick.time; b.fast_sample_count++;
         if(b.fast_sample_count>=2 && b.mfe_r>=C[ci].fast_arm_r && r>=0.25 &&
            delta<=-0.05 && prev<=0.05)
         {
            reason="V38_VELOCITY_DECAY"; return true;
         }
      }
      return false;
   }

   if(mode==4)
   {
      if(C[ci].fast_timebox_seconds>0 && age>=C[ci].fast_timebox_seconds)
      {
         reason="V38_TIMEBOX"; return true;
      }
      return false;
   }
   return false;
}

'''
    s = one(s, 'void ProcessExits(const MqlTick &tick)\n{', fast_exit + 'void ProcessExits(const MqlTick &tick)\n{')

    exit_old = '''         bool stopHit=B[ix].direction>0 ? px<=B[ix].stop : px>=B[ix].stop;
         if(stopHit){ string rsn=MathAbs(B[ix].stop-B[ix].initial_stop)>0.1*_Point?"PROTECT_STOP":"SL"; CloseBook(ci,bi,B[ix],tick,px,rsn); continue; }

         if(C[ci].policy==PP_PARTIAL50_AT_1R'''
    exit_new = '''         bool stopHit=B[ix].direction>0 ? px<=B[ix].stop : px>=B[ix].stop;
         if(stopHit){ string rsn=MathAbs(B[ix].stop-B[ix].initial_stop)>0.1*_Point?"PROTECT_STOP":"SL"; CloseBook(ci,bi,B[ix],tick,px,rsn); continue; }

         string v38Reason="";
         if(V38FastExitTriggered(ci,B[ix],tick,px,v38Reason))
         { CloseBook(ci,bi,B[ix],tick,px,v38Reason); continue; }

         if(C[ci].policy==PP_PARTIAL50_AT_1R'''
    s = one(s, exit_old, exit_new)

    telemetry = r'''
string V38M1FastTelemetryFile(){ return g_run_folder+"\\intra_trade_m1_fast.csv"; }

datetime g_v38_m1_bucket=0;
long g_v38_m1_ticks=0;
long g_v38_m1_up=0;
long g_v38_m1_down=0;
double g_v38_m1_first_mid=0.0;
double g_v38_m1_last_mid=0.0;
double g_v38_m1_abs_path=0.0;
double g_v38_m1_high_mid=0.0;
double g_v38_m1_low_mid=0.0;
double g_v38_m1_spread_sum_points=0.0;
double g_v38_m1_spread_max_points=0.0;

void V38EnsureM1FastTelemetryFile()
{
   if(!InpV38WriteM1FastTelemetry) return;
   string f=V38M1FastTelemetryFile();
   if(FileIsExist(f,FILE_COMMON)) return;
   int h=FileOpen(f,FILE_WRITE|FILE_CSV|FILE_ANSI|FILE_COMMON,','); if(h==INVALID_HANDLE) return;
   FileWrite(h,"time","month","candidate","book","entry_time","direction","age_seconds",
             "unrealized_r","mfe_r","mae_r","giveback_from_peak_r","r_delta_1m",
             "tick_count","tick_direction_imbalance","mid_net_move_r","mid_abs_path_r","mid_range_r",
             "spread_mean_points","spread_max_points");
   FileClose(h);
}

void V38ResetM1Agg(const datetime bucket,const MqlTick &tick)
{
   double mid=0.5*(tick.bid+tick.ask);
   g_v38_m1_bucket=bucket; g_v38_m1_ticks=1; g_v38_m1_up=0; g_v38_m1_down=0;
   g_v38_m1_first_mid=mid; g_v38_m1_last_mid=mid; g_v38_m1_abs_path=0.0;
   g_v38_m1_high_mid=mid; g_v38_m1_low_mid=mid;
   double pt=SymbolInfoDouble(_Symbol,SYMBOL_POINT);
   double sp=(pt>0 ? (tick.ask-tick.bid)/pt : 0.0);
   g_v38_m1_spread_sum_points=sp; g_v38_m1_spread_max_points=sp;
}

void V38AppendM1FastTelemetry(const datetime availableTime,const MqlTick &tick)
{
   if(!InpV38WriteM1FastTelemetry || g_v38_m1_ticks<=0) return;
   string f=V38M1FastTelemetryFile();
   int h=FileOpen(f,FILE_READ|FILE_WRITE|FILE_CSV|FILE_ANSI|FILE_COMMON,','); if(h==INVALID_HANDLE) return;
   FileSeek(h,0,SEEK_END);
   int ci=7;
   for(int z=0;z<2;++z)
   {
      int bi=(z==0?0:3); int ix=BI(ci,bi); if(!B[ix].open) continue;
      double px=B[ix].direction>0?tick.bid:tick.ask;
      double r=PriceR(B[ix],px);
      double peak=MathMax(B[ix].mfe_r,r);
      double gb=MathMax(0.0,peak-r);
      double riskDist=MathAbs(B[ix].entry-B[ix].initial_stop);
      double net=(riskDist>0 ? (g_v38_m1_last_mid-g_v38_m1_first_mid)/riskDist : 0.0);
      if(B[ix].direction<0) net=-net;
      double path=(riskDist>0 ? g_v38_m1_abs_path/riskDist : 0.0);
      double range=(riskDist>0 ? (g_v38_m1_high_mid-g_v38_m1_low_mid)/riskDist : 0.0);
      double imb=(g_v38_m1_up+g_v38_m1_down)>0 ?
                 (double)(g_v38_m1_up-g_v38_m1_down)/(double)(g_v38_m1_up+g_v38_m1_down) : 0.0;
      double d1=(B[ix].v38_prev_m1_time>0 ? r-B[ix].v38_prev_m1_r : 0.0);
      double spMean=g_v38_m1_ticks>0 ? g_v38_m1_spread_sum_points/(double)g_v38_m1_ticks : 0.0;
      long age=(long)MathMax(0.0,(double)(availableTime-B[ix].entry_time));
      FileWrite(h,TimeToString(availableTime,TIME_DATE|TIME_MINUTES|TIME_SECONDS),g_month_tag,C[ci].name,BookName(bi),
                TimeToString(B[ix].entry_time,TIME_DATE|TIME_MINUTES|TIME_SECONDS),B[ix].direction>0?"LONG":"SHORT",age,
                DoubleToString(r,6),DoubleToString(peak,6),DoubleToString(B[ix].mae_r,6),DoubleToString(gb,6),DoubleToString(d1,6),
                g_v38_m1_ticks,DoubleToString(imb,6),DoubleToString(net,6),DoubleToString(path,6),DoubleToString(range,6),
                DoubleToString(spMean,3),DoubleToString(g_v38_m1_spread_max_points,3));
      B[ix].v38_prev_m1_time=availableTime; B[ix].v38_prev_m1_r=r;
   }
   FileClose(h);
}

void V38UpdateM1FastTelemetry(const MqlTick &tick)
{
   if(!InpV38WriteM1FastTelemetry) return;
   datetime bucket=(datetime)(tick.time-(tick.time%60));
   if(g_v38_m1_bucket<=0){ V38ResetM1Agg(bucket,tick); return; }
   if(bucket!=g_v38_m1_bucket)
   {
      V38AppendM1FastTelemetry(bucket,tick);
      V38ResetM1Agg(bucket,tick);
      return;
   }
   double mid=0.5*(tick.bid+tick.ask);
   double d=mid-g_v38_m1_last_mid;
   if(d>0) g_v38_m1_up++; else if(d<0) g_v38_m1_down++;
   g_v38_m1_abs_path+=MathAbs(d);
   g_v38_m1_last_mid=mid;
   if(mid>g_v38_m1_high_mid) g_v38_m1_high_mid=mid;
   if(mid<g_v38_m1_low_mid) g_v38_m1_low_mid=mid;
   double pt=SymbolInfoDouble(_Symbol,SYMBOL_POINT);
   double sp=(pt>0 ? (tick.ask-tick.bid)/pt : 0.0);
   g_v38_m1_spread_sum_points+=sp;
   if(sp>g_v38_m1_spread_max_points) g_v38_m1_spread_max_points=sp;
   g_v38_m1_ticks++;
}

'''
    s = one(s, 'string V34IntraTradeFile(){ return g_run_folder+"\\\\intra_trade_m15.csv"; }',
            telemetry + 'string V34IntraTradeFile(){ return g_run_folder+"\\\\intra_trade_m15.csv"; }')

    s = one(s,
        '   V34EnsureIntraTradeFile();\n   if(InpWriteBarFeatures) EnsureBarFeatureFile();',
        '   V34EnsureIntraTradeFile();\n   V38EnsureM1FastTelemetryFile();\n   if(InpWriteBarFeatures) EnsureBarFeatureFile();')

    s = one(s,
        '   g_last_tick=tick; g_have_tick=true;\n   datetime v34bt[1];',
        '   g_last_tick=tick; g_have_tick=true;\n'
        '   V38UpdateM1FastTelemetry(tick);\n'
        '   datetime v34bt[1];')

    s = one(s,
        'x+="format=mt5_quant_v34_parallel_alpha_lab_v1\\r\\n";',
        'x+="format=mt5_quant_v38_fast_harvest_lab_v1\\r\\n";')
    s = one(s,
        'x+="source_file=V34ParallelAlphaLab.mq5\\r\\n";',
        'x+="source_file=V38FastHarvestLab.mq5\\r\\n";')
    s = one(s,
        'x+="candidate_count=17\\r\\nbook_count=4\\r\\nmonthly_reset=1\\r\\nmonths_written="+IntegerToString((int)g_months_written)+"\\r\\n";',
        'x+="candidate_count=23\\r\\nbook_count=4\\r\\nmonthly_reset=1\\r\\nmonths_written="+IntegerToString((int)g_months_written)+"\\r\\n";')
    s = one(s,
        '   x+="v34_specialists=smc_ict_causal,price_action_causal,wyckoff_proxy_causal,tick_microstructure_proxy,parallel_specialist_confluence\\r\\n";',
        '   x+="v34_specialists=smc_ict_causal,price_action_causal,wyckoff_proxy_causal,tick_microstructure_proxy,parallel_specialist_confluence\\r\\n";\n'
        '   x+="v38_fast_harvest_lab=1\\r\\n";\n'
        '   x+="v38_fast_exit_arms=tp0p50,tp0p75,tp1p00,giveback0p25_after0p75,velocity_decay_after0p50,timebox30m\\r\\n";\n'
        '   x+="v38_m1_fast_telemetry="+(InpV38WriteM1FastTelemetry?"1":"0")+"\\r\\n";')
    s = one(s,
        'PrintFormat("V34_PARALLEL_ALPHA_LAB START %s %s candidates=%d books=%d",_Symbol,PeriodText(),CANDIDATE_COUNT,BOOK_COUNT);',
        'PrintFormat("V38_FAST_HARVEST_LAB START %s %s candidates=%d books=%d",_Symbol,PeriodText(),CANDIDATE_COUNT,BOOK_COUNT);')
    s = one(s,
        'PrintFormat("V34_PARALLEL_ALPHA_LAB DONE months=%d",(int)g_months_written);',
        'PrintFormat("V38_FAST_HARVEST_LAB DONE months=%d",(int)g_months_written);')

    if re.search(r'OrderSend\(|OrderSendAsync\(|\bCTrade\b|trade\.Buy\(|trade\.Sell\(', s):
        raise RuntimeError("forbidden native-order token introduced")
    if 'MQLInfoInteger(MQL_TESTER)' not in s:
        raise RuntimeError("tester-only guard missing")
    for token in [
        'adaptive_ewma_hl8_thr0',
        'v38_adaptive_fast_tp0p50',
        'v38_adaptive_fast_tp0p75',
        'v38_adaptive_fast_tp1p00',
        'v38_adaptive_fast_gb0p25_after0p75',
        'v38_adaptive_velocity_decay_after0p50',
        'v38_adaptive_timebox30m',
        'V38FastExitTriggered',
        'intra_trade_m1_fast.csv',
    ]:
        if token not in s:
            raise RuntimeError(f"V38 required token missing: {token}")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(s, encoding="utf-8", newline="\r\n")
    print(f"V38 source PASS sha256={sha256(output)} path={output}")

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True)
    ap.add_argument("--output", required=True)
    a = ap.parse_args()
    build(pathlib.Path(a.source), pathlib.Path(a.output))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
