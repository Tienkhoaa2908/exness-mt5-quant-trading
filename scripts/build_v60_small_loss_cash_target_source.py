#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
V59_BUILDER = HERE / "build_v59_integrated_bidirectional_rr_source.py"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


v59 = load(V59_BUILDER, "v59_parent_for_v60")
EXPERT_NAME = "V60SmallLossCashTarget"
FIXED_LOT = 0.01
MAGIC = 600060


def replace_once(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        raise RuntimeError(f"V60 {label} drifted expected=1 actual={n}")
    return text.replace(old, new, 1)


def replace_function(text: str, start_sig: str, next_sig: str, new_body: str, label: str) -> str:
    start = text.find(start_sig)
    if start < 0:
        raise RuntimeError(f"V60 function missing {start_sig}")
    end = text.find(next_sig, start + len(start_sig))
    if end < 0:
        raise RuntimeError(f"V60 next function missing {next_sig}")
    return text[:start] + new_body.rstrip() + "\n\n" + text[end:]


PRICE_TARGET_HELPER = r'''
bool V60PriceForCashTarget(const int d,const double entry,const double target_cash,double &tp)
{
   tp=0.0;
   if(d==0 || entry<=0.0 || target_cash<=0.0) return false;
   ENUM_ORDER_TYPE ot=(d>0 ? ORDER_TYPE_BUY : ORDER_TYPE_SELL);
   double tick_size=SymbolInfoDouble(_Symbol,SYMBOL_TRADE_TICK_SIZE);
   if(tick_size<=0.0) tick_size=_Point;
   if(tick_size<=0.0) return false;

   double lo=0.0,hi=tick_size,pnl=0.0;
   bool bracket=false;
   for(int i=0;i<48;++i)
   {
      double p=entry+d*hi;
      if(p<=0.0) break;
      if(OrderCalcProfit(ot,_Symbol,InpV60FixedLot,entry,p,pnl) && pnl>=target_cash)
      { bracket=true; break; }
      hi*=2.0;
   }
   if(!bracket) return false;

   for(int i=0;i<64;++i)
   {
      double mid=0.5*(lo+hi);
      double p=entry+d*mid;
      if(!OrderCalcProfit(ot,_Symbol,InpV60FixedLot,entry,p,pnl)) return false;
      if(pnl>=target_cash) hi=mid; else lo=mid;
   }
   tp=NormalizeDouble(entry+d*hi,_Digits);
   return (tp>0.0 && MathIsValidNumber(tp));
}
'''

START_SHADOW = r'''
void V60StartShadow(const int d,const double entry,const double stop,const double risk_cash,const int score)
{
   g_shadow_open=true;g_shadow_dir=d;g_shadow_entry_time=TimeCurrent();g_shadow_entry=entry;g_shadow_stop=stop;
   g_shadow_risk_dist=MathAbs(entry-stop);g_shadow_risk_cash=risk_cash;g_shadow_score=score;g_shadow_bars=0;
   g_shadow_max_r=-1000.0;g_shadow_min_r=1000.0;
   g_shadow_max_cash=-1.0e12;g_shadow_min_cash=1.0e12;g_shadow_last_cash=0.0;
   g_cash2_done=false;g_cash3_done=false;g_cash4_done=false;
   g_cash2=0.0;g_cash3=0.0;g_cash4=0.0;
}
'''

FINISH_SHADOW = r'''
void V60FinishShadow(const string reason)
{
   if(!g_shadow_open) return;
   double fallback=(reason=="structural_stop" ? -g_shadow_risk_cash : g_shadow_last_cash);
   if(!g_cash2_done) g_cash2=fallback;
   if(!g_cash3_done) g_cash3=fallback;
   if(!g_cash4_done) g_cash4=fallback;
   string row=TimeToString(g_shadow_entry_time,TIME_DATE|TIME_MINUTES|TIME_SECONDS)+","+
      TimeToString(TimeCurrent(),TIME_DATE|TIME_MINUTES|TIME_SECONDS)+","+
      IntegerToString(g_shadow_dir)+","+DoubleToString(g_shadow_entry,_Digits)+","+
      DoubleToString(g_shadow_stop,_Digits)+","+DoubleToString(g_shadow_risk_cash,4)+","+
      IntegerToString(g_shadow_score)+","+DoubleToString(g_shadow_max_r,4)+","+
      DoubleToString(g_shadow_min_r,4)+","+DoubleToString(g_shadow_max_cash,4)+","+
      DoubleToString(g_shadow_min_cash,4)+","+DoubleToString(g_cash2,4)+","+
      DoubleToString(g_cash3,4)+","+DoubleToString(g_cash4,4)+","+
      IntegerToString(g_shadow_bars)+","+reason;
   V60Append(V60_SHADOW,row);
   g_shadow_open=false;
}
'''

UPDATE_SHADOW = r'''
void V60UpdateShadow()
{
   if(!g_shadow_open || g_shadow_risk_dist<=0.0) return;
   MqlTick t;
   if(!SymbolInfoTick(_Symbol,t)) return;
   double px=(g_shadow_dir>0 ? t.bid : t.ask);
   double r=(g_shadow_dir*(px-g_shadow_entry))/g_shadow_risk_dist;
   if(r>g_shadow_max_r) g_shadow_max_r=r;
   if(r<g_shadow_min_r) g_shadow_min_r=r;

   ENUM_ORDER_TYPE ot=(g_shadow_dir>0 ? ORDER_TYPE_BUY : ORDER_TYPE_SELL);
   double cash=0.0;
   if(!OrderCalcProfit(ot,_Symbol,InpV60FixedLot,g_shadow_entry,px,cash)) return;
   g_shadow_last_cash=cash;
   if(cash>g_shadow_max_cash) g_shadow_max_cash=cash;
   if(cash<g_shadow_min_cash) g_shadow_min_cash=cash;

   if(!g_cash2_done && cash>=InpV60ShadowTargetCash2){g_cash2=InpV60ShadowTargetCash2;g_cash2_done=true;}
   if(!g_cash3_done && cash>=InpV60ShadowTargetCash3){g_cash3=InpV60ShadowTargetCash3;g_cash3_done=true;}
   if(!g_cash4_done && cash>=InpV60ShadowTargetCash4){g_cash4=InpV60ShadowTargetCash4;g_cash4_done=true;}

   bool stop_hit=(g_shadow_dir>0 ? px<=g_shadow_stop : px>=g_shadow_stop);
   if(stop_hit)
   {
      if(!g_cash2_done){g_cash2=-g_shadow_risk_cash;g_cash2_done=true;}
      if(!g_cash3_done){g_cash3=-g_shadow_risk_cash;g_cash3_done=true;}
      if(!g_cash4_done){g_cash4=-g_shadow_risk_cash;g_cash4_done=true;}
      V60FinishShadow("structural_stop");
      return;
   }
   if(g_cash2_done && g_cash3_done && g_cash4_done){V60FinishShadow("all_cash_targets_resolved");return;}
   if(g_shadow_bars>=InpV60MaxBarsInTrade){V60FinishShadow("time_exit");return;}
}
'''

SOFT_CUT = r'''
void V60MaybeSoftLossCut()
{
   if(InpV60ScreenOnly || InpV60SoftLossCash<=0.0) return;
   ulong ticket=0;int d=0;double entry=0.0,sl=0.0,tp=0.0;
   if(!V60OwnedPosition(ticket,d,entry,sl,tp)) return;
   MqlTick t;
   if(!SymbolInfoTick(_Symbol,t)) return;
   double exitp=(d>0 ? t.bid : t.ask);
   ENUM_ORDER_TYPE ot=(d>0 ? ORDER_TYPE_BUY : ORDER_TYPE_SELL);
   double floating=0.0;
   if(!OrderCalcProfit(ot,_Symbol,InpV60FixedLot,entry,exitp,floating)) return;
   if(floating>-InpV60SoftLossCash) return;

   V60Features f;
   if(!V60BuildFeatures(f)) return;
   bool structural_flip=(f.bos_choch_dir==-d || f.structure_dir==-d);
   bool momentum_flip=(f.m15_trend==-d && f.macd_dir==-d && f.di_dir==-d);
   if(!structural_flip && !momentum_flip) return;

   g_trade.SetExpertMagicNumber(InpV60Magic);
   bool closed=g_trade.PositionClose(ticket);
   V60Append(V60_EVENTS,TimeToString(TimeCurrent(),TIME_DATE|TIME_MINUTES|TIME_SECONDS)+
      ",SOFT_LOSS_CUT,"+IntegerToString(d)+","+(closed?"closed":"close_failed")+","+
      DoubleToString(floating,4)+","+IntegerToString(f.bos_choch_dir)+","+IntegerToString(f.m15_trend));
}
'''

ON_TICK = r'''
void OnTick()
{
   V60UpdateShadow();
   V60MaybeSoftLossCut();
   datetime bar=iTime(_Symbol,PERIOD_M15,0);
   if(bar<=0 || bar==g_last_m15_bar) return;
   g_last_m15_bar=bar;
   if(g_shadow_open) g_shadow_bars++;
   ulong ticket=0;int d=0;double e=0,s=0,t=0;
   if(!InpV60ScreenOnly && V60OwnedPosition(ticket,d,e,s,t)) return;
   if(g_shadow_open) return;
   V60EvaluateBar();
}
'''


def transform() -> str:
    text = v59.MQL
    text = replace_once(text, '#property version   "59.00"', '#property version   "60.00"', "version")
    text = text.replace("V59", "V60").replace("v59", "v60")
    text = replace_once(text, "input long   InpV60Magic = 590059;", "input long   InpV60Magic = 600060;", "magic")
    text = replace_once(
        text,
        "input double InpV60ActualRR = 3.0;\ninput double InpV60MaxStopRiskCash = 8.0;\ninput double InpV60MaxStopATR = 1.50;",
        "input double InpV60PrimaryTargetCash = 2.00;\n"
        "input double InpV60ShadowTargetCash2 = 2.00;\n"
        "input double InpV60ShadowTargetCash3 = 3.00;\n"
        "input double InpV60ShadowTargetCash4 = 4.00;\n"
        "input double InpV60SoftLossCash = 1.00;\n"
        "input double InpV60MaxStopRiskCash = 1.25;\n"
        "input double InpV60MaxStopATR = 1.25;",
        "loss-target inputs",
    )
    text = replace_once(
        text,
        "input double InpV60MaxSpreadRiskPct = 10.0;",
        "input double InpV60MaxSpreadTargetPct = 15.0;",
        "spread target input",
    )
    text = replace_once(text, "input int    InpV60MaxBarsInTrade = 64;", "input int    InpV60MaxBarsInTrade = 48;", "time cap")

    # Fix the V59 premium/discount overlap: 45-55% becomes neutral.
    text = replace_once(
        text,
        "if(f.range_location<=0.55) f.location_dir=1;\n      else if(f.range_location>=0.45) f.location_dir=-1;",
        "if(f.range_location<=0.45) f.location_dir=1;\n      else if(f.range_location>=0.55) f.location_dir=-1;",
        "location symmetry",
    )

    # Trend following now means H4 and H1 must both align; neutral H4 is not enough.
    text = replace_once(
        text,
        "bool long_regime=(f.h1_trend==1 && f.h4_trend!=-1);\n   bool short_regime=(f.h1_trend==-1 && f.h4_trend!=1);",
        "bool long_regime=(f.h1_trend==1 && f.h4_trend==1);\n   bool short_regime=(f.h1_trend==-1 && f.h4_trend==-1);",
        "strict H4 alignment",
    )

    # With a small loss budget, spread is judged against the profit target rather than a tiny fraction of stop risk.
    text = replace_once(
        text,
        "double spread_allowed=MathMin(InpV60MaxSpreadCash,risk_cash*(InpV60MaxSpreadRiskPct/100.0));",
        "double spread_allowed=MathMin(InpV60MaxSpreadCash,InpV60PrimaryTargetCash*(InpV60MaxSpreadTargetPct/100.0));",
        "spread cash budget",
    )

    text = replace_once(text, "bool V60BuildStopTarget", PRICE_TARGET_HELPER + "\nbool V60BuildStopTarget", "cash target helper")
    text = replace_once(
        text,
        "tp=entry+d*InpV60ActualRR*dist;\n   if(!MathIsValidNumber(tp) || tp<=0.0){reject=\"invalid_target\";return false;}",
        "if(!V60PriceForCashTarget(d,entry,InpV60PrimaryTargetCash,tp))\n"
        "   {reject=\"cash_target_calc_failed\";return false;}",
        "primary cash target",
    )

    old_globals = """bool g_rr2_done=false;\nbool g_rr25_done=false;\nbool g_rr3_done=false;\ndouble g_rr2=0.0;\ndouble g_rr25=0.0;\ndouble g_rr3=0.0;"""
    new_globals = """double g_shadow_max_cash=-1.0e12;\ndouble g_shadow_min_cash=1.0e12;\ndouble g_shadow_last_cash=0.0;\nbool g_cash2_done=false;\nbool g_cash3_done=false;\nbool g_cash4_done=false;\ndouble g_cash2=0.0;\ndouble g_cash3=0.0;\ndouble g_cash4=0.0;"""
    text = replace_once(text, old_globals, new_globals, "cash shadow globals")

    text = replace_function(text, "void V60StartShadow", "void V60FinishShadow", START_SHADOW, "start shadow")
    text = replace_function(text, "void V60FinishShadow", "void V60UpdateShadow", FINISH_SHADOW, "finish shadow")
    text = replace_function(text, "void V60UpdateShadow", "void V60EnsureHeaders", UPDATE_SHADOW, "update shadow")

    text = replace_once(
        text,
        'V60Append(V60_SHADOW,"entry_time,exit_time,direction,entry,stop,risk_cash,score,max_r,min_r,result_2r,result_2p5r,result_3r,bars,reason");',
        'V60Append(V60_SHADOW,"entry_time,exit_time,direction,entry,stop,risk_cash,score,max_r,min_r,max_cash,min_cash,result_cash_2,result_cash_3,result_cash_4,bars,reason");',
        "shadow header",
    )

    text = replace_once(text, '"V60 L"', '"V60 $2 L"', "long comment")
    text = replace_once(text, '"V60 S"', '"V60 $2 S"', "short comment")

    text = replace_once(text, "void OnTick()", SOFT_CUT + "\nvoid OnTick()", "soft cut insertion")
    text = replace_function(text, "void OnTick()", "void OnTradeTransaction", ON_TICK, "OnTick loss manager")

    text = replace_once(
        text,
        "if(InpV60FixedLot!=0.01 || InpV60ActualRR<2.0 || InpV60ActualRR>3.0 || InpV60MaxStopRiskCash<=0.0)\n      return INIT_PARAMETERS_INCORRECT;",
        "if(InpV60FixedLot!=0.01 || InpV60PrimaryTargetCash<=0.0 || InpV60MaxStopRiskCash<=0.0 ||\n"
        "      InpV60SoftLossCash<=0.0 || InpV60SoftLossCash>InpV60MaxStopRiskCash ||\n"
        "      InpV60ShadowTargetCash2<=0.0 || InpV60ShadowTargetCash3<InpV60ShadowTargetCash2 ||\n"
        "      InpV60ShadowTargetCash4<InpV60ShadowTargetCash3)\n"
        "      return INIT_PARAMETERS_INCORRECT;",
        "init loss-target guard",
    )
    text = text.replace("integrated_bidirectional_rr", "small_loss_cash_target")
    return text


def validate(text: str) -> None:
    required = (
        "STRATEGY TESTER ONLY",
        "InpV60FixedLot = 0.01",
        "InpV60Magic = 600060",
        "InpV60PrimaryTargetCash = 2.00",
        "InpV60SoftLossCash = 1.00",
        "InpV60MaxStopRiskCash = 1.25",
        "f.h1_trend==1 && f.h4_trend==1",
        "f.h1_trend==-1 && f.h4_trend==-1",
        "f.range_location<=0.45",
        "f.range_location>=0.55",
        "V60PriceForCashTarget",
        "result_cash_2,result_cash_3,result_cash_4",
        "SOFT_LOSS_CUT",
        "g_trade.Buy",
        "g_trade.Sell",
        "CopyRates(_Symbol,PERIOD_M15,1,320,m15)",
    )
    for token in required:
        if token not in text:
            raise RuntimeError(f"V60 required token missing: {token}")
    forbidden = (
        "InpV60ActualRR",
        "f.h4_trend!=-1",
        "f.h4_trend!=1",
        "range_location<=0.55) f.location_dir=1",
        "range_location>=0.45) f.location_dir=-1",
        "V59",
        "v52_b4_or_b3_trend_bos",
        "PositionClosePartial",
    )
    for token in forbidden:
        if token in text:
            raise RuntimeError(f"V60 forbidden token present: {token}")
    if text.count("{") != text.count("}"):
        raise RuntimeError("V60 MQL brace imbalance")


def build(output: Path) -> str:
    text = transform().replace("\n", "\r\n")
    validate(text)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8", newline="")
    digest = v59.sha256(output)
    print(f"V60 source built sha256={digest} path={output}")
    return digest


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()
    build(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
