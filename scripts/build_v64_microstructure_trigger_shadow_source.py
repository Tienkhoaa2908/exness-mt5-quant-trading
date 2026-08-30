#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT = HERE / "build_v63_profit_quality_risk_zone_source.py"
V64_ROOT = r"mt5_quant\\v64_microstructure_trigger_shadow"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


parent = load(PARENT, "v63_parent_for_v64")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        raise RuntimeError(f"V64 {label} drifted expected=1 actual={n}")
    return text.replace(old, new, 1)


def replace_function(text: str, start_sig: str, next_sig: str, replacement: str, label: str) -> str:
    start = text.find(start_sig)
    if start < 0:
        raise RuntimeError(f"V64 function missing {label} start={start_sig}")
    end = text.find(next_sig, start + len(start_sig))
    if end < 0:
        raise RuntimeError(f"V64 function missing {label} next={next_sig}")
    return text[:start] + replacement.strip() + "\n\n" + text[end:]


V64_HELPERS = r'''
#define V64_ARCH_NONE 0
#define V64_ARCH_PULLBACK_SWEEP 1
#define V64_ARCH_BREAKOUT_RETEST 2
#define V64_NOISE_MAX 24

struct V64NoiseShadow
{
   bool active;
   long id;
   int dir;
   datetime started;
   double entry;
   double max_pnl;
   double min_pnl;
   int state[9];
};

V64NoiseShadow g_v64_noise[V64_NOISE_MAX];
long g_v64_noise_seq=0;
int g_v64_pending_arch=V64_ARCH_NONE;
string V64_NOISE_FILE="V64_NOISE_SHADOW.csv";

string V64ArchName(const int a)
{
   if(a==V64_ARCH_PULLBACK_SWEEP) return "PULLBACK_SWEEP_BOS";
   if(a==V64_ARCH_BREAKOUT_RETEST) return "BREAKOUT_RETEST_BOS";
   return "NONE";
}

double V64Efficiency(MqlRates &r[],const int n,const int bars)
{
   int use=MathMin(bars,n-1);
   if(use<3) return 0.0;
   double path=0.0;
   for(int i=0;i<use;i++) path+=MathAbs(r[i].close-r[i+1].close);
   if(path<=0.0) return 0.0;
   return MathAbs(r[0].close-r[use].close)/path;
}

bool V64TrendQualityPass(const int d,const int arch,string &detail,double &h1sep,double &h4sep,double &h1slope,double &h4slope,double &eff)
{
   detail="";h1sep=h4sep=h1slope=h4slope=eff=0.0;
   MqlRates h1[],h4[],m15[];
   ArraySetAsSeries(h1,true);ArraySetAsSeries(h4,true);ArraySetAsSeries(m15,true);
   int n1=CopyRates(_Symbol,PERIOD_H1,1,90,h1);
   int n4=CopyRates(_Symbol,PERIOD_H4,1,90,h4);
   int n15=CopyRates(_Symbol,PERIOD_M15,1,40,m15);
   if(n1<70 || n4<70 || n15<24){detail="trend_quality_history_not_ready";return false;}

   double a1=V64ATR(h1,n1,14,0),a4=V64ATR(h4,n4,14,0);
   double f1=V64EMA(h1,n1,20,0),s1=V64EMA(h1,n1,50,0),f1p=V64EMA(h1,n1,20,3);
   double f4=V64EMA(h4,n4,20,0),s4=V64EMA(h4,n4,50,0),f4p=V64EMA(h4,n4,20,3);
   if(a1<=0 || a4<=0 || f1<=0 || s1<=0 || f4<=0 || s4<=0){detail="trend_quality_indicators_not_ready";return false;}

   h1sep=MathAbs(f1-s1)/a1;
   h4sep=MathAbs(f4-s4)/a4;
   h1slope=d*(f1-f1p)/a1;
   h4slope=d*(f4-f4p)/a4;
   eff=V64Efficiency(m15,n15,12);

   if((d>0 && (f1<=s1 || f4<=s4)) || (d<0 && (f1>=s1 || f4>=s4)))
   {detail="htf_ema_order_opposed";return false;}
   if(h1sep<InpV64MinH1EmaSepAtr){detail="h1_ema_separation_weak";return false;}
   if(h4sep<InpV64MinH4EmaSepAtr){detail="h4_ema_separation_weak";return false;}
   if(h1slope<InpV64MinH1SlopeAtr){detail="h1_slope_weak";return false;}
   if(h4slope<InpV64MinH4SlopeAtr){detail="h4_slope_weak";return false;}
   double min_eff=(arch==V64_ARCH_BREAKOUT_RETEST ? InpV64MinBreakoutEfficiency : InpV64MinPullbackEfficiency);
   if(eff<min_eff){detail="m15_efficiency_weak";return false;}
   detail="trend_quality_ok";
   return true;
}

int V64ClassifyArchetype(const int d,V64Features &f,string &detail)
{
   bool pullback=(f.pullback_dir==d && (f.liquidity_sweep_dir==d || f.order_block_retest_dir==d || f.location_dir==d));
   bool breakout=(f.bos_choch_dir==d && f.structure_dir==d && (f.fvg_dir==d || f.order_block_retest_dir==d));
   if(pullback){detail="pullback_sweep_context";return V64_ARCH_PULLBACK_SWEEP;}
   if(breakout){detail="breakout_retest_context";return V64_ARCH_BREAKOUT_RETEST;}
   detail="no_complete_archetype";
   return V64_ARCH_NONE;
}

bool V64MicroSweepBos(const int d,string &detail)
{
   detail="";
   MqlRates m1[];ArraySetAsSeries(m1,true);
   int n=CopyRates(_Symbol,PERIOD_M1,1,80,m1);
   if(n<30){detail="m1_history_not_ready";return false;}
   double atr=V64ATR(m1,n,14,0);
   if(atr<=0.0){detail="m1_atr_not_ready";return false;}
   double body=MathAbs(m1[0].close-m1[0].open);
   double range=MathMax(_Point,m1[0].high-m1[0].low);
   if(body<InpV64MinM1BodyAtr*atr || body/range<InpV64MinM1BodyFraction)
   {detail="m1_displacement_too_weak";return false;}

   double refLow=m1[4].low,refHigh=m1[4].high;
   for(int i=5;i<=10;i++){refLow=MathMin(refLow,m1[i].low);refHigh=MathMax(refHigh,m1[i].high);}
   bool sweep=false;
   for(int i=1;i<=3;i++)
   {
      if(d>0 && m1[i].low<refLow-InpV64MinSweepAtr*atr && m1[i].close>refLow) sweep=true;
      if(d<0 && m1[i].high>refHigh+InpV64MinSweepAtr*atr && m1[i].close<refHigh) sweep=true;
   }
   if(!sweep){detail="liquidity_sweep_reclaim_missing";return false;}

   double microHigh=m1[1].high,microLow=m1[1].low;
   for(int i=2;i<=3;i++){microHigh=MathMax(microHigh,m1[i].high);microLow=MathMin(microLow,m1[i].low);}
   bool bos=(d>0 ? m1[0].close>microHigh+InpV64MicroBosBufferAtr*atr : m1[0].close<microLow-InpV64MicroBosBufferAtr*atr);
   if(!bos){detail="micro_bos_missing";return false;}
   detail="sweep_reclaim_micro_bos";
   return true;
}

bool V64MicroBreakRetestBos(const int d,string &detail)
{
   detail="";
   MqlRates m1[];ArraySetAsSeries(m1,true);
   int n=CopyRates(_Symbol,PERIOD_M1,1,80,m1);
   if(n<30){detail="m1_history_not_ready";return false;}
   double atr=V64ATR(m1,n,14,0);
   if(atr<=0.0){detail="m1_atr_not_ready";return false;}
   double body=MathAbs(m1[0].close-m1[0].open);
   double range=MathMax(_Point,m1[0].high-m1[0].low);
   if(body<InpV64MinM1BodyAtr*atr || body/range<InpV64MinM1BodyFraction)
   {detail="m1_displacement_too_weak";return false;}

   double olderHigh=m1[4].high,olderLow=m1[4].low;
   for(int i=5;i<=9;i++){olderHigh=MathMax(olderHigh,m1[i].high);olderLow=MathMin(olderLow,m1[i].low);}
   bool retest=(d>0 ? (m1[1].low<=olderHigh+InpV64RetestAtr*atr && m1[1].close>=olderHigh-InpV64RetestAtr*atr)
                    : (m1[1].high>=olderLow-InpV64RetestAtr*atr && m1[1].close<=olderLow+InpV64RetestAtr*atr));
   if(!retest){detail="micro_retest_missing";return false;}
   bool bos=(d>0 ? m1[0].close>MathMax(m1[1].high,olderHigh)+InpV64MicroBosBufferAtr*atr
                 : m1[0].close<MathMin(m1[1].low,olderLow)-InpV64MicroBosBufferAtr*atr);
   if(!bos){detail="micro_bos_missing";return false;}
   detail="break_retest_micro_bos";
   return true;
}

bool V64MicroTriggerConfirmed(const int d,const int arch,string &detail)
{
   if(arch==V64_ARCH_PULLBACK_SWEEP) return V64MicroSweepBos(d,detail);
   if(arch==V64_ARCH_BREAKOUT_RETEST) return V64MicroBreakRetestBos(d,detail);
   detail="invalid_archetype";return false;
}

int V64NoiseSlot()
{
   for(int i=0;i<V64_NOISE_MAX;i++) if(!g_v64_noise[i].active) return i;
   return -1;
}

void V64NoiseStart(const int d,const double entry)
{
   int k=V64NoiseSlot();
   if(k<0){V64PendingEvent("NOISE_SHADOW",d,"slot_exhausted",entry,0,0);return;}
   g_v64_noise[k].active=true;g_v64_noise[k].id=++g_v64_noise_seq;g_v64_noise[k].dir=d;
   g_v64_noise[k].started=TimeCurrent();g_v64_noise[k].entry=entry;
   g_v64_noise[k].max_pnl=0.0;g_v64_noise[k].min_pnl=0.0;
   for(int j=0;j<9;j++) g_v64_noise[k].state[j]=0;
}

void V64NoiseFinish(const int k,const string reason)
{
   string row=LongToString(g_v64_noise[k].id)+","+TimeToString(g_v64_noise[k].started,TIME_DATE|TIME_MINUTES|TIME_SECONDS)+","+
      TimeToString(TimeCurrent(),TIME_DATE|TIME_MINUTES|TIME_SECONDS)+","+IntegerToString(g_v64_noise[k].dir)+","+
      DoubleToString(g_v64_noise[k].entry,_Digits)+","+DoubleToString(g_v64_noise[k].max_pnl,4)+","+DoubleToString(g_v64_noise[k].min_pnl,4);
   for(int j=0;j<9;j++) row+=","+IntegerToString(g_v64_noise[k].state[j]);
   row+=","+reason;
   V64Append(V64_NOISE_FILE,row);
   g_v64_noise[k].active=false;
}

void V64UpdateNoiseShadows()
{
   const double stops[3]={1.10,1.35,1.60};
   const double targets[3]={3.00,3.50,4.00};
   for(int k=0;k<V64_NOISE_MAX;k++)
   {
      if(!g_v64_noise[k].active) continue;
      MqlTick tick;if(!SymbolInfoTick(_Symbol,tick)) continue;
      double exitp=(g_v64_noise[k].dir>0 ? tick.bid : tick.ask);
      ENUM_ORDER_TYPE ot=(g_v64_noise[k].dir>0 ? ORDER_TYPE_BUY : ORDER_TYPE_SELL);
      double pnl=0.0;if(!OrderCalcProfit(ot,_Symbol,InpV64FixedLot,g_v64_noise[k].entry,exitp,pnl)) continue;
      g_v64_noise[k].max_pnl=MathMax(g_v64_noise[k].max_pnl,pnl);
      g_v64_noise[k].min_pnl=MathMin(g_v64_noise[k].min_pnl,pnl);
      int unresolved=0;
      for(int si=0;si<3;si++) for(int ti=0;ti<3;ti++)
      {
         int j=si*3+ti;
         if(g_v64_noise[k].state[j]!=0) continue;
         if(pnl>=targets[ti]) g_v64_noise[k].state[j]=1;
         else if(pnl<=-stops[si]) g_v64_noise[k].state[j]=-1;
         else unresolved++;
      }
      if(unresolved==0){V64NoiseFinish(k,"all_resolved");continue;}
      if(TimeCurrent()-g_v64_noise[k].started>=InpV64NoiseShadowMaxMinutes*60)
         V64NoiseFinish(k,"time_expired");
   }
}
'''

ARM_PENDING = r'''
void V64ArmPending(const int d,V64Features &f,const string why)
{
   if(d==0 || d!=InpV64AllowedDirection) return;
   string arch_detail="";
   int arch=V64ClassifyArchetype(d,f,arch_detail);
   if(arch==V64_ARCH_NONE)
   {
      V64LogDirectionalEval(f,d,why,"no_complete_archetype",0,0,0,0,0,0,0,0,0,"none");
      return;
   }

   if(g_v64_pending)
   {
      if(g_v64_pending_dir==d && g_v64_pending_arch==arch)
      {
         V64PendingEvent("PENDING_REFRESH",d,"first_arm_ttl_preserved",g_v64_pending_reference,
                         g_v64_pending_raw_stop,(double)g_v64_pending_score);
         return;
      }
      V64ClearPending("direction_or_archetype_changed_before_rearm");
   }

   double raw=V64RawM15Stop(d,f);
   MqlTick t;if(!SymbolInfoTick(_Symbol,t)) return;
   double entry=(d>0 ? t.ask : t.bid);
   if(raw<=0.0 || (d>0 && raw>=entry) || (d<0 && raw<=entry))
   {V64LogDirectionalEval(f,d,why,"invalid_arm_structural_stop",entry,raw,0,0,0,0,0,0,0,"m15");return;}

   g_v64_pending=true;g_v64_pending_dir=d;g_v64_pending_features=f;g_v64_pending_armed=TimeCurrent();
   g_v64_pending_reference=entry;g_v64_pending_raw_stop=raw;g_v64_pending_score=(d>0 ? f.long_score : f.short_score);
   g_v64_pending_arch=arch;
   V64LogDirectionalEval(f,d,why,"pending_"+V64ArchName(arch),entry,raw,0,0,0,0,0,0,0,"m15");
   V64PendingEvent("PENDING_ARM",d,V64ArchName(arch),entry,raw,(double)g_v64_pending_score);
}
'''

MANAGE_PENDING = r'''
void V64ManagePendingEntry()
{
   if(!g_v64_pending || InpV64ScreenOnly) return;
   if(g_v64_pending_dir!=InpV64AllowedDirection){V64ClearPending("direction_mismatch");g_v64_pending_arch=V64_ARCH_NONE;return;}

   ulong ticket=0;int pd=0;double pe=0,ps=0,pt=0;
   if(V64OwnedPosition(ticket,pd,pe,ps,pt)){V64ClearPending("position_exists");g_v64_pending_arch=V64_ARCH_NONE;return;}
   if(TimeCurrent()-g_v64_pending_armed>InpV64PendingMaxMinutes*60)
   {V64ClearPending("expired_first_arm_ttl");g_v64_pending_arch=V64_ARCH_NONE;return;}

   MqlTick tick;if(!SymbolInfoTick(_Symbol,tick)) return;
   double px=(g_v64_pending_dir>0 ? tick.bid : tick.ask);
   if((g_v64_pending_dir>0 && px<=g_v64_pending_raw_stop) || (g_v64_pending_dir<0 && px>=g_v64_pending_raw_stop))
   {V64ClearPending("invalidated_before_entry");g_v64_pending_arch=V64_ARCH_NONE;return;}

   datetime m1bar=iTime(_Symbol,PERIOD_M1,0);
   if(m1bar<=0 || m1bar==g_v64_last_m1_bar) return;
   g_v64_last_m1_bar=m1bar;

   int d=g_v64_pending_dir;
   V64Features cur;if(!V64BuildFeatures(cur)) return;
   if(cur.h4_trend!=d || cur.h1_trend!=d)
   {V64PendingEvent("ENTRY_VETO",d,"stale_h4_h1_regime",cur.adx,(double)cur.h4_trend,(double)cur.h1_trend);V64ClearPending("stale_h4_h1_regime");g_v64_pending_arch=V64_ARCH_NONE;return;}
   string current_why="";int current_d=V64SelectDirection(cur,current_why);
   if(current_d==-d)
   {V64PendingEvent("ENTRY_VETO",d,"opposite_current_selector",(double)current_d,cur.adx,0);V64ClearPending("opposite_current_selector");g_v64_pending_arch=V64_ARCH_NONE;return;}

   string quality="";
   if(!V64EntryQualityPass(d,cur,quality))
   {V64PendingEvent("ENTRY_VETO",d,quality,cur.adx,(double)cur.di_dir,(double)cur.macd_dir);V64ClearPending(quality);g_v64_pending_arch=V64_ARCH_NONE;return;}

   double h1sep=0,h4sep=0,h1slope=0,h4slope=0,eff=0;string tq="";
   if(!V64TrendQualityPass(d,g_v64_pending_arch,tq,h1sep,h4sep,h1slope,h4slope,eff))
   {V64PendingEvent("ENTRY_VETO",d,tq,h1sep,h4sep,eff);return;}

   if(!SymbolInfoTick(_Symbol,tick)) return;
   double entry=(d>0 ? tick.ask : tick.bid);
   double stop=0,tp=0,risk_cash=0,risk_pct=0,margin_cash=0,spread_points=0,spread_cash=0;string reject="";
   bool feasible=V64BuildStopTarget(d,cur,entry,stop,tp,risk_cash,risk_pct,margin_cash,spread_points,spread_cash,reject);
   if(!feasible)
   {
      string event=(reject=="structural_risk_cash_cap" || reject=="structural_risk_too_tight" || reject=="stop_too_far_atr" ? "RISK_ZONE_WAIT" : "REFINE_WAIT");
      V64PendingEvent(event,d,reject,entry,risk_cash,spread_cash);return;
   }
   if(g_v64_stop_source!="m5")
   {V64PendingEvent("RISK_ZONE_WAIT",d,"m5_structural_stop_not_ready",entry,risk_cash,spread_cash);return;}
   if(spread_cash<=0.0 || risk_cash/spread_cash<InpV64MinRiskSpreadRatio)
   {V64PendingEvent("RISK_ZONE_WAIT",d,"risk_spread_ratio_low",risk_cash,spread_cash,(spread_cash>0?risk_cash/spread_cash:0));return;}

   string micro="";
   if(!V64MicroTriggerConfirmed(d,g_v64_pending_arch,micro))
   {V64PendingEvent("REFINE_WAIT",d,micro,entry,risk_cash,spread_cash);return;}

   V64LogDirectionalEval(cur,d,V64ArchName(g_v64_pending_arch),"",entry,stop,tp,risk_cash,risk_pct,margin_cash,spread_points,spread_cash,1,g_v64_stop_source);
   string preflight_detail="";long preflight_retcode=0;
   if(!V64OrderPreflight(d,entry,stop,tp,preflight_detail,preflight_retcode))
   {V64PendingEvent("ORDER_PREFLIGHT",d,preflight_detail,entry,stop,(double)preflight_retcode);V64ClearPending("preflight_block");g_v64_pending_arch=V64_ARCH_NONE;return;}

   g_trade.SetExpertMagicNumber(InpV64Magic);g_trade.SetDeviationInPoints(50);g_trade.SetTypeFillingBySymbol(_Symbol);
   bool sent=(d>0 ? g_trade.Buy(InpV64FixedLot,_Symbol,0.0,stop,tp,"V64 MICRO L") : g_trade.Sell(InpV64FixedLot,_Symbol,0.0,stop,tp,"V64 MICRO S"));
   string send_detail=(sent ? "sent" : "rejected_"+IntegerToString((int)g_trade.ResultRetcode()));
   V64PendingEvent("REFINED_ENTRY",d,send_detail,entry,risk_cash,spread_cash);
   if(sent)
   {
      V64NoiseStart(d,entry);
      g_v64_pending=false;g_v64_pending_dir=0;g_v64_pending_armed=0;g_v64_pending_arch=V64_ARCH_NONE;
   }
}
'''

EVALUATE_BAR = r'''
void V64EvaluateBar()
{
   V64Features f;bool ready=V64BuildFeatures(f);string why=(ready ? "" : "feature_not_ready");
   int d=(ready ? V64SelectDirection(f,why) : 0);if(d==0) return;
   if(d!=InpV64AllowedDirection)
   {
      if(g_v64_pending) V64ClearPending("opposite_direction_signal");
      g_v64_pending_arch=V64_ARCH_NONE;
      V64LogDirectionalEval(f,d,why,"direction_isolated_out",0,0,0,0,0,0,0,0,0,"none");return;
   }
   V64ArmPending(d,f,why);
}
'''

ON_TICK = r'''
void OnTick()
{
   V64UpdateNoiseShadows();
   V64HardCashLossGuard();
   V64ManageProfitRatchet();
   V64MaybeSoftLossCut();
   V64ManagePendingEntry();

   datetime bar=iTime(_Symbol,PERIOD_M15,0);
   if(bar<=0 || bar==g_last_m15_bar) return;
   g_last_m15_bar=bar;

   ulong ticket=0;int d=0;double e=0,s=0,t=0;
   if(V64OwnedPosition(ticket,d,e,s,t)) return;
   V64EvaluateBar();
}
'''


def transform(allowed_direction: int) -> str:
    if allowed_direction not in (-1, 1):
        raise ValueError("allowed_direction must be -1 or 1")
    text = parent.transform(allowed_direction)
    text = replace_once(text, '#property version   "63.00"', '#property version   "64.00"', "version")
    text = text.replace("V63", "V64").replace("v63", "v64")
    text = text.replace(r"mt5_quant\\v64_profit_quality_risk_zone", V64_ROOT)
    text = replace_once(text, "input long   InpV64Magic = 630063;", "input long   InpV64Magic = 640064;", "magic")
    text = replace_once(text, "input double InpV64MinStopRiskCash = 0.60;", "input double InpV64MinStopRiskCash = 0.85;", "min risk")
    text = replace_once(text, "input double InpV64MaxStopRiskCash = 1.05;", "input double InpV64MaxStopRiskCash = 1.20;", "max risk")
    text = replace_once(text, "input double InpV64EmergencyLossCash = 1.10;", "input double InpV64EmergencyLossCash = 1.15;", "emergency risk")
    marker = "input double InpV64MinEntryADX = 16.0;"
    extra = marker + "\n" + "\n".join([
        "input double InpV64MinRiskSpreadRatio = 4.0;",
        "input double InpV64MinM1BodyAtr = 0.25;",
        "input double InpV64MinM1BodyFraction = 0.45;",
        "input double InpV64MinSweepAtr = 0.05;",
        "input double InpV64MicroBosBufferAtr = 0.02;",
        "input double InpV64RetestAtr = 0.15;",
        "input double InpV64MinH1EmaSepAtr = 0.12;",
        "input double InpV64MinH4EmaSepAtr = 0.08;",
        "input double InpV64MinH1SlopeAtr = 0.02;",
        "input double InpV64MinH4SlopeAtr = 0.01;",
        "input double InpV64MinPullbackEfficiency = 0.12;",
        "input double InpV64MinBreakoutEfficiency = 0.18;",
        "input int    InpV64NoiseShadowMaxMinutes = 480;",
    ])
    text = replace_once(text, marker, extra, "V64 micro inputs")

    # Insert helpers after inherited globals/functions are available but before ArmPending replacement.
    text = replace_once(text, "void V64ArmPending", V64_HELPERS + "\nvoid V64ArmPending", "V64 helpers")
    text = replace_function(text, "void V64ArmPending", "void V64ManagePendingEntry", ARM_PENDING, "arm")
    text = replace_function(text, "void V64ManagePendingEntry", "void V64EvaluateBar", MANAGE_PENDING, "manage pending")
    text = replace_function(text, "void V64EvaluateBar", "int OnInit()", EVALUATE_BAR, "evaluate")
    text = replace_function(text, "void OnTick()", "void OnTradeTransaction", ON_TICK, "OnTick")
    text = replace_once(
        text,
        "int OnInit()\n{\n   if(InpV64EmergencyLossCash<=0.0 || InpV64MinEntryADX<0.0) return INIT_PARAMETERS_INCORRECT;",
        "int OnInit()\n{\n   if(InpV64EmergencyLossCash<=0.0 || InpV64MinEntryADX<0.0 || InpV64MinRiskSpreadRatio<=0.0 || InpV64NoiseShadowMaxMinutes<1) return INIT_PARAMETERS_INCORRECT;",
        "init guards",
    )
    validate(text, allowed_direction)
    return text


def validate(text: str, allowed_direction: int) -> None:
    required = (
        V64_ROOT,
        "InpV64FixedLot = 0.01",
        "InpV64PrimaryTargetCash = 3.50",
        "InpV64MinStopRiskCash = 0.85",
        "InpV64MaxStopRiskCash = 1.20",
        "InpV64EmergencyLossCash = 1.15",
        "InpV64MinRiskSpreadRatio = 4.0",
        f"InpV64AllowedDirection = {allowed_direction}",
        "PULLBACK_SWEEP_BOS",
        "BREAKOUT_RETEST_BOS",
        "liquidity_sweep_reclaim_missing",
        "micro_bos_missing",
        "risk_spread_ratio_low",
        "V64TrendQualityPass",
        "V64UpdateNoiseShadows",
        "V64_NOISE_SHADOW.csv",
        "OrderCalcProfit",
        "CopyRates(_Symbol,PERIOD_M1,1,80,m1)",
        "CopyRates(_Symbol,PERIOD_H1,1,90,h1)",
        "CopyRates(_Symbol,PERIOD_H4,1,90,h4)",
        "V64OrderPreflight",
        "g_trade.Buy",
        "g_trade.Sell",
    )
    for token in required:
        if token not in text:
            raise RuntimeError(f"V64 required token missing: {token}")
    if r"mt5_quant\\v64_profit_quality_risk_zone" in text:
        raise RuntimeError("V64 stale inherited FILE_COMMON root remains")
    # Actual execution must not be blocked by the old single-lane V63 shadow lifecycle.
    tick = text[text.index("void OnTick()"):text.index("void OnTradeTransaction", text.index("void OnTick()"))]
    if "if(g_shadow_open) return;" in tick or "V64UpdateShadow();" in tick:
        raise RuntimeError("V64 legacy single shadow still gates actual execution")
    manage = text[text.index("void V64ManagePendingEntry"):text.index("void V64EvaluateBar", text.index("void V64ManagePendingEntry"))]
    if "V64StartShadow(" in manage:
        raise RuntimeError("V64 actual send still starts legacy single shadow")


def build(output: Path, allowed_direction: int) -> str:
    text = transform(allowed_direction).replace("\n", "\r\n")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8", newline="")
    digest = sha256(output)
    print(f"V64_SOURCE_SHA256={digest}")
    print(f"V64_SOURCE_PATH={output}")
    print(f"V64_ALLOWED_DIRECTION={allowed_direction}")
    print(f"V64_FILE_COMMON_ROOT={V64_ROOT}")
    return digest


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--allowed-direction", required=True, type=int, choices=(-1, 1))
    args = ap.parse_args()
    build(args.output, args.allowed_direction)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
