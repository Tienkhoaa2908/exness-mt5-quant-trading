#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT = HERE / "build_v64_microstructure_trigger_shadow_source_fixed.py"
V65_ROOT = r"mt5_quant\\v65_micro_stop_calibration"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


parent = load(PARENT, "v64_parent_for_v65")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        raise RuntimeError(f"V65 {label} drifted expected=1 actual={n}")
    return text.replace(old, new, 1)


def replace_function(text: str, start_sig: str, next_sig: str, replacement: str, label: str) -> str:
    start = text.find(start_sig)
    if start < 0:
        raise RuntimeError(f"V65 function missing {label} start={start_sig}")
    end = text.find(next_sig, start + len(start_sig))
    if end < 0:
        raise RuntimeError(f"V65 function missing {label} next={next_sig}")
    return text[:start] + replacement.strip() + "\n\n" + text[end:]


MICRO_SWEEP = r'''
bool V64MicroSweepBos(const int d,string &detail,double &micro_stop)
{
   detail="";micro_stop=0.0;
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
   double sweepExtreme=(d>0 ? DBL_MAX : -DBL_MAX);
   for(int i=1;i<=3;i++)
   {
      if(d>0 && m1[i].low<refLow-InpV64MinSweepAtr*atr && m1[i].close>refLow)
      {sweep=true;sweepExtreme=MathMin(sweepExtreme,m1[i].low);}
      if(d<0 && m1[i].high>refHigh+InpV64MinSweepAtr*atr && m1[i].close<refHigh)
      {sweep=true;sweepExtreme=MathMax(sweepExtreme,m1[i].high);}
   }
   if(!sweep){detail="liquidity_sweep_reclaim_missing";return false;}

   double microHigh=m1[1].high,microLow=m1[1].low;
   for(int i=2;i<=3;i++){microHigh=MathMax(microHigh,m1[i].high);microLow=MathMin(microLow,m1[i].low);}
   bool bos=(d>0 ? m1[0].close>microHigh+InpV64MicroBosBufferAtr*atr : m1[0].close<microLow-InpV64MicroBosBufferAtr*atr);
   if(!bos){detail="micro_bos_missing";return false;}

   micro_stop=(d>0 ? sweepExtreme-InpV64MicroStopAtrBuffer*atr : sweepExtreme+InpV64MicroStopAtrBuffer*atr);
   if(micro_stop<=0.0 || !MathIsValidNumber(micro_stop)){detail="micro_stop_invalid";return false;}
   detail="sweep_reclaim_micro_bos";
   return true;
}
'''

MICRO_BREAK = r'''
bool V64MicroBreakRetestBos(const int d,string &detail,double &micro_stop)
{
   detail="";micro_stop=0.0;
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

   micro_stop=(d>0 ? m1[1].low-InpV64MicroStopAtrBuffer*atr : m1[1].high+InpV64MicroStopAtrBuffer*atr);
   if(micro_stop<=0.0 || !MathIsValidNumber(micro_stop)){detail="micro_stop_invalid";return false;}
   detail="break_retest_micro_bos";
   return true;
}
'''

MICRO_CONFIRM_AND_TARGET = r'''
bool V64MicroTriggerConfirmed(const int d,const int arch,string &detail,double &micro_stop)
{
   micro_stop=0.0;
   if(arch==V64_ARCH_PULLBACK_SWEEP) return V64MicroSweepBos(d,detail,micro_stop);
   if(arch==V64_ARCH_BREAKOUT_RETEST) return V64MicroBreakRetestBos(d,detail,micro_stop);
   detail="invalid_archetype";return false;
}

bool V64BuildMicroStopTarget(const int d,const double entry,const double micro_stop,
                             double &stop,double &tp,double &risk_cash,double &risk_pct,
                             double &margin_cash,double &spread_points,double &spread_cash,
                             double &risk_spread_ratio,string &reject)
{
   reject="";stop=micro_stop;tp=0.0;risk_cash=0.0;risk_pct=0.0;margin_cash=0.0;
   spread_points=0.0;spread_cash=0.0;risk_spread_ratio=0.0;
   if((d>0 && stop>=entry) || (d<0 && stop<=entry)){reject="invalid_micro_structural_stop";return false;}

   double dist=MathAbs(entry-stop);
   long stops_level=SymbolInfoInteger(_Symbol,SYMBOL_TRADE_STOPS_LEVEL);
   double min_dist=(double)stops_level*_Point;
   if(min_dist>0.0 && dist<min_dist){reject="broker_stop_too_close";return false;}

   risk_cash=V64RiskCash(d,entry,stop,InpV64FixedLot);
   if(risk_cash<=0.0){reject="risk_calc_failed";return false;}
   double eq=AccountInfoDouble(ACCOUNT_EQUITY);
   risk_pct=(eq>0.0 ? 100.0*risk_cash/eq : 0.0);

   spread_cash=V64SpreadCash(d,InpV64FixedLot,spread_points);
   if(spread_cash<=0.0){reject="spread_calc_failed";return false;}
   risk_spread_ratio=risk_cash/spread_cash;

   if(risk_cash<InpV64MinStopRiskCash-1e-9){reject="micro_risk_too_tight";return false;}
   if(risk_cash>InpV64MaxStopRiskCash+1e-9){reject="micro_risk_cash_cap";return false;}
   if(risk_spread_ratio<InpV64MinRiskSpreadRatio){reject="micro_risk_spread_ratio_low";return false;}

   double spread_allowed=MathMin(InpV64MaxSpreadCash,InpV64PrimaryTargetCash*(InpV64MaxSpreadTargetPct/100.0));
   if(spread_cash>spread_allowed+1e-9){reject="spread_cost_guard";return false;}

   ENUM_ORDER_TYPE ot=(d>0 ? ORDER_TYPE_BUY : ORDER_TYPE_SELL);
   if(!OrderCalcMargin(ot,_Symbol,InpV64FixedLot,entry,margin_cash)){reject="margin_calc_failed";return false;}
   double free_margin=AccountInfoDouble(ACCOUNT_MARGIN_FREE);
   if(free_margin<=0.0 || margin_cash>free_margin*(InpV64MaxMarginUsagePct/100.0))
   {reject="margin_guard";return false;}

   if(!V64PriceForCashTarget(d,entry,InpV64PrimaryTargetCash,tp))
   {reject="cash_target_calc_failed";return false;}
   return true;
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
   double invalidation_px=(g_v64_pending_dir>0 ? tick.bid : tick.ask);
   if((g_v64_pending_dir>0 && invalidation_px<=g_v64_pending_raw_stop) || (g_v64_pending_dir<0 && invalidation_px>=g_v64_pending_raw_stop))
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

   // M5 remains a context/structure gate, but its old swing is no longer used
   // as the mandatory cash stop. The confirmed M1 trigger owns invalidation.
   double m5_context_stop=0.0;
   if(!V64M5RefinedStop(d,entry,m5_context_stop))
   {V64PendingEvent("M5_CONTEXT_WAIT",d,"m5_structure_not_ready",entry,0,0);return;}

   string micro="";double micro_stop=0.0;
   if(!V64MicroTriggerConfirmed(d,g_v64_pending_arch,micro,micro_stop))
   {V64PendingEvent("REFINE_WAIT",d,micro,entry,0,0);return;}

   double stop=0,tp=0,risk_cash=0,risk_pct=0,margin_cash=0,spread_points=0,spread_cash=0,ratio=0;string reject="";
   bool feasible=V64BuildMicroStopTarget(d,entry,micro_stop,stop,tp,risk_cash,risk_pct,margin_cash,spread_points,spread_cash,ratio,reject);
   V64PendingEvent("MICRO_CANDIDATE",d,V64ArchName(g_v64_pending_arch),risk_cash,spread_cash,ratio);
   if(!feasible)
   {V64PendingEvent("MICRO_REJECT",d,reject,risk_cash,spread_cash,ratio);return;}

   V64LogDirectionalEval(cur,d,V64ArchName(g_v64_pending_arch),"",entry,stop,tp,risk_cash,risk_pct,margin_cash,spread_points,spread_cash,1,"m1_micro");
   string preflight_detail="";long preflight_retcode=0;
   if(!V64OrderPreflight(d,entry,stop,tp,preflight_detail,preflight_retcode))
   {V64PendingEvent("ORDER_PREFLIGHT",d,preflight_detail,entry,stop,(double)preflight_retcode);V64ClearPending("preflight_block");g_v64_pending_arch=V64_ARCH_NONE;return;}

   g_trade.SetExpertMagicNumber(InpV64Magic);g_trade.SetDeviationInPoints(50);g_trade.SetTypeFillingBySymbol(_Symbol);
   bool sent=(d>0 ? g_trade.Buy(InpV64FixedLot,_Symbol,0.0,stop,tp,"V65 MICRO L") : g_trade.Sell(InpV64FixedLot,_Symbol,0.0,stop,tp,"V65 MICRO S"));
   string send_detail=(sent ? "sent" : "rejected_"+IntegerToString((int)g_trade.ResultRetcode()));
   V64PendingEvent("REFINED_ENTRY",d,send_detail,entry,risk_cash,spread_cash);
   if(sent)
   {
      double shadow_entry=g_trade.ResultPrice();
      if(shadow_entry<=0.0) shadow_entry=entry;
      V64NoiseStart(d,shadow_entry);
      V64PendingEvent("NOISE_SHADOW",d,"actual_fill_anchor",shadow_entry,entry,shadow_entry-entry);
      g_v64_pending=false;g_v64_pending_dir=0;g_v64_pending_armed=0;g_v64_pending_arch=V64_ARCH_NONE;
   }
}
'''


def transform(allowed_direction: int) -> str:
    if allowed_direction not in (-1, 1):
        raise ValueError("allowed_direction must be -1 or 1")
    text = parent.transform(allowed_direction)
    text = replace_once(text, '#property version   "64.00"', '#property version   "65.00"', "version")
    text = replace_once(text, r"mt5_quant\\v64_microstructure_trigger_shadow", V65_ROOT, "FILE_COMMON root")
    text = replace_once(text, "input long   InpV64Magic = 640064;", "input long   InpV64Magic = 650065;", "magic")
    text = replace_once(text, "input double InpV64MaxStopRiskCash = 1.20;", "input double InpV64MaxStopRiskCash = 1.25;", "max planned risk")
    text = replace_once(text, "input double InpV64EmergencyLossCash = 1.15;", "input double InpV64EmergencyLossCash = 1.20;", "emergency loss")
    text = replace_once(
        text,
        "input double InpV64MicroBosBufferAtr = 0.02;",
        "input double InpV64MicroBosBufferAtr = 0.02;\ninput double InpV64MicroStopAtrBuffer = 0.10;",
        "micro stop input",
    )
    text = replace_once(
        text,
        'string V64_NOISE_FILE="V64_NOISE_SHADOW.csv";',
        'string V64_NOISE_FILE=V64_ROOT+"\\\\V64_NOISE_SHADOW.csv";',
        "noise FILE_COMMON root",
    )

    text = replace_function(text, "bool V64MicroSweepBos", "bool V64MicroBreakRetestBos", MICRO_SWEEP, "micro sweep")
    text = replace_function(text, "bool V64MicroBreakRetestBos", "bool V64MicroTriggerConfirmed", MICRO_BREAK, "micro breakout")
    text = replace_function(text, "bool V64MicroTriggerConfirmed", "int V64NoiseSlot", MICRO_CONFIRM_AND_TARGET, "micro confirm + target")
    text = replace_function(text, "void V64ManagePendingEntry", "void V64EvaluateBar", MANAGE_PENDING, "manage pending")

    validate(text, allowed_direction)
    return text


def validate(text: str, allowed_direction: int) -> None:
    required = (
        V65_ROOT,
        "InpV64Magic = 650065",
        "InpV64FixedLot = 0.01",
        "InpV64PrimaryTargetCash = 3.50",
        "InpV64MaxStopRiskCash = 1.25",
        "InpV64EmergencyLossCash = 1.20",
        "InpV64MicroStopAtrBuffer = 0.10",
        f"InpV64AllowedDirection = {allowed_direction}",
        "V64BuildMicroStopTarget",
        "MICRO_CANDIDATE",
        "MICRO_REJECT",
        '"m1_micro"',
        "V64MicroTriggerConfirmed(d,g_v64_pending_arch,micro,micro_stop)",
        "V64M5RefinedStop(d,entry,m5_context_stop)",
        'string V64_NOISE_FILE=V64_ROOT+"\\\\V64_NOISE_SHADOW.csv";',
        "IntegerToString(g_v64_noise[k].id)",
    )
    for token in required:
        if token not in text:
            raise RuntimeError(f"V65 required token missing: {token}")
    if "LongToString(" in text:
        raise RuntimeError("V65 generated MQL contains non-portable LongToString")
    manage = text[text.index("void V64ManagePendingEntry"):text.index("void V64EvaluateBar")]
    if manage.index("V64MicroTriggerConfirmed") > manage.index("V64BuildMicroStopTarget"):
        raise RuntimeError("V65 micro trigger must precede micro stop cash-risk validation")
    if "V64BuildStopTarget(d,cur,entry" in manage:
        raise RuntimeError("V65 manage pending still uses old M5/M15 stop as cash stop")
    if 'g_v64_stop_source!="m5"' in manage:
        raise RuntimeError("V65 still requires old M5 stop source")


def build(output: Path, allowed_direction: int) -> str:
    text = transform(allowed_direction).replace("\n", "\r\n")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8", newline="")
    digest = sha256(output)
    print(f"V65_SOURCE_SHA256={digest}")
    print(f"V65_SOURCE_PATH={output}")
    print(f"V65_ALLOWED_DIRECTION={allowed_direction}")
    print(f"V65_FILE_COMMON_ROOT={V65_ROOT}")
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
