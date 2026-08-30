#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT = HERE / "build_v61_profit_ratchet_m5_refinement_source_fixed.py"
V62_ROOT = r"mt5_quant\\v62_direction_isolated_entry_refinement"
FIXED_LOT = 0.01
MAGIC = 620062


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


parent = load(PARENT, "v61_fixed_parent_for_v62")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        raise RuntimeError(f"V62 {label} drifted expected=1 actual={n}")
    return text.replace(old, new, 1)


def replace_function(text: str, start_sig: str, next_sig: str, replacement: str, label: str) -> str:
    start = text.find(start_sig)
    if start < 0:
        raise RuntimeError(f"V62 function missing {label} start={start_sig}")
    end = text.find(next_sig, start + len(start_sig))
    if end < 0:
        raise RuntimeError(f"V62 function missing {label} next={next_sig}")
    return text[:start] + replacement.strip() + "\n\n" + text[end:]


PENDING_HELPERS = r'''
void V62PendingEvent(const string event,const int d,const string detail,const double v1,const double v2,const double v3)
{
   V62Append(V62_EVENTS,TimeToString(TimeCurrent(),TIME_DATE|TIME_MINUTES|TIME_SECONDS)+","+event+","+
      IntegerToString(d)+","+detail+","+DoubleToString(v1,4)+","+DoubleToString(v2,4)+","+DoubleToString(v3,4));
}

void V62ClearPending(const string detail)
{
   if(g_v62_pending)
      V62PendingEvent("PENDING_END",g_v62_pending_dir,detail,g_v62_pending_reference,g_v62_pending_raw_stop,0.0);
   g_v62_pending=false;
   g_v62_pending_dir=0;
   g_v62_pending_armed=0;
   g_v62_pending_reference=0.0;
   g_v62_pending_raw_stop=0.0;
   g_v62_pending_score=0;
}

double V62RawM15Stop(const int d,V62Features &f)
{
   if(d>0) return f.swing_low-InpV62StopAtrBuffer*f.atr15;
   if(d<0) return f.swing_high+InpV62StopAtrBuffer*f.atr15;
   return 0.0;
}

void V62LogDirectionalEval(V62Features &f,const int d,const string selector_reason,const string reject,
                          const double entry,const double stop,const double tp,const double risk_cash,
                          const double risk_pct,const double margin_cash,const double spread_points,
                          const double spread_cash,const int feasible,const string stop_source)
{
   string row=TimeToString(TimeCurrent(),TIME_DATE|TIME_MINUTES|TIME_SECONDS)+","+
      IntegerToString(f.h4_trend)+","+IntegerToString(f.h1_trend)+","+IntegerToString(f.m15_trend)+","+
      IntegerToString(f.structure_dir)+","+IntegerToString(f.bos_choch_dir)+","+IntegerToString(f.fvg_dir)+","+
      IntegerToString(f.liquidity_sweep_dir)+","+IntegerToString(f.order_block_retest_dir)+","+
      IntegerToString(f.pullback_dir)+","+IntegerToString(f.di_dir)+","+IntegerToString(f.macd_dir)+","+
      IntegerToString(f.location_dir)+","+DoubleToString(f.atr15,5)+","+DoubleToString(f.rsi2,3)+","+
      DoubleToString(f.rsi14,3)+","+DoubleToString(f.adx,3)+","+DoubleToString(f.plus_di,3)+","+
      DoubleToString(f.minus_di,3)+","+DoubleToString(f.macd,6)+","+DoubleToString(f.macd_slope,6)+","+
      DoubleToString(f.distance_ema_atr,4)+","+DoubleToString(f.range_location,4)+","+
      IntegerToString(f.long_score)+","+IntegerToString(f.short_score)+","+IntegerToString(d)+","+selector_reason+","+
      DoubleToString(entry,_Digits)+","+DoubleToString(stop,_Digits)+","+DoubleToString(tp,_Digits)+","+
      DoubleToString(risk_cash,4)+","+DoubleToString(risk_pct,4)+","+DoubleToString(margin_cash,4)+","+
      DoubleToString(spread_points,1)+","+DoubleToString(spread_cash,4)+","+IntegerToString(feasible)+","+
      reject+","+stop_source+",0";
   V62Append(V62_EVAL,row);
}

bool V62MicroEntryReady(const int d,string &detail)
{
   detail="";
   MqlRates m5[],m1[];
   ArraySetAsSeries(m5,true);ArraySetAsSeries(m1,true);
   int n5=CopyRates(_Symbol,PERIOD_M5,1,120,m5);
   int n1=CopyRates(_Symbol,PERIOD_M1,1,40,m1);
   if(n5<80 || n1<12){detail="micro_history_not_ready";return false;}

   double atr5=V62ATR(m5,n5,14,0);
   double ema20=V62EMA(m5,n5,20,0);
   double ema50=V62EMA(m5,n5,50,0);
   if(atr5<=0.0 || ema20<=0.0 || ema50<=0.0){detail="micro_indicators_not_ready";return false;}

   bool trend=(d>0 ? ema20>ema50 : ema20<ema50);
   bool retest=(d>0 ? (m5[0].low<=ema20+InpV62M5RetestAtr*atr5 && m5[0].close>=ema20-InpV62M5ReclaimAtr*atr5)
                    : (m5[0].high>=ema20-InpV62M5RetestAtr*atr5 && m5[0].close<=ema20+InpV62M5ReclaimAtr*atr5));
   bool m1_turn=(d>0 ? (m1[0].close>m1[0].open && m1[0].close>m1[1].close)
                      : (m1[0].close<m1[0].open && m1[0].close<m1[1].close));
   if(!trend){detail="m5_trend_not_aligned";return false;}
   if(!retest){detail="m5_retest_not_reached";return false;}
   if(!m1_turn){detail="m1_turn_not_confirmed";return false;}
   detail="m5_retest_m1_turn";
   return true;
}

void V62ArmPending(const int d,V62Features &f,const string why)
{
   if(d==0 || d!=InpV62AllowedDirection) return;
   double raw=V62RawM15Stop(d,f);
   MqlTick t;
   if(!SymbolInfoTick(_Symbol,t)) return;
   double entry=(d>0 ? t.ask : t.bid);
   if(raw<=0.0 || (d>0 && raw>=entry) || (d<0 && raw<=entry))
   {
      V62LogDirectionalEval(f,d,why,"invalid_arm_structural_stop",entry,raw,0,0,0,0,0,0,0,"m15");
      return;
   }

   g_v62_pending=true;
   g_v62_pending_dir=d;
   g_v62_pending_features=f;
   g_v62_pending_armed=TimeCurrent();
   g_v62_pending_reference=entry;
   g_v62_pending_raw_stop=raw;
   g_v62_pending_score=(d>0 ? f.long_score : f.short_score);
   V62LogDirectionalEval(f,d,why,"pending_entry_refinement",entry,raw,0,0,0,0,0,0,0,"m15");
   V62PendingEvent("PENDING_ARM",d,"m15_signal",entry,raw,(double)g_v62_pending_score);
}

void V62ManagePendingEntry()
{
   if(!g_v62_pending || InpV62ScreenOnly) return;
   if(g_v62_pending_dir!=InpV62AllowedDirection){V62ClearPending("direction_mismatch");return;}

   ulong ticket=0;int pd=0;double pe=0,ps=0,pt=0;
   if(V62OwnedPosition(ticket,pd,pe,ps,pt)){V62ClearPending("position_exists");return;}
   if(g_shadow_open){V62ClearPending("shadow_exists");return;}

   if(TimeCurrent()-g_v62_pending_armed>InpV62PendingMaxMinutes*60)
   { V62ClearPending("expired"); return; }

   MqlTick tick;
   if(!SymbolInfoTick(_Symbol,tick)) return;
   double px=(g_v62_pending_dir>0 ? tick.bid : tick.ask);
   if((g_v62_pending_dir>0 && px<=g_v62_pending_raw_stop) ||
      (g_v62_pending_dir<0 && px>=g_v62_pending_raw_stop))
   { V62ClearPending("invalidated_before_entry"); return; }

   datetime m1bar=iTime(_Symbol,PERIOD_M1,0);
   if(m1bar<=0 || m1bar==g_v62_last_m1_bar) return;
   g_v62_last_m1_bar=m1bar;

   string micro="";
   if(!V62MicroEntryReady(g_v62_pending_dir,micro)) return;

   int d=g_v62_pending_dir;
   double entry=(d>0 ? tick.ask : tick.bid);
   double stop=0.0,tp=0.0,risk_cash=0.0,risk_pct=0.0,margin_cash=0.0,spread_points=0.0,spread_cash=0.0;
   string reject="";
   bool feasible=V62BuildStopTarget(d,g_v62_pending_features,entry,stop,tp,risk_cash,risk_pct,
                                    margin_cash,spread_points,spread_cash,reject);
   if(!feasible)
   {
      V62PendingEvent("REFINE_WAIT",d,reject,entry,risk_cash,spread_cash);
      return;
   }

   V62LogDirectionalEval(g_v62_pending_features,d,"refined_entry",reject,entry,stop,tp,risk_cash,risk_pct,
                         margin_cash,spread_points,spread_cash,1,g_v62_stop_source);

   string preflight_detail="";long preflight_retcode=0;
   if(!V62OrderPreflight(d,entry,stop,tp,preflight_detail,preflight_retcode))
   {
      V62PendingEvent("ORDER_PREFLIGHT",d,preflight_detail,entry,stop,(double)preflight_retcode);
      V62ClearPending("preflight_block");
      return;
   }

   g_trade.SetExpertMagicNumber(InpV62Magic);
   g_trade.SetDeviationInPoints(50);
   g_trade.SetTypeFillingBySymbol(_Symbol);
   bool sent=false;
   if(d>0) sent=g_trade.Buy(InpV62FixedLot,_Symbol,0.0,stop,tp,"V62 REFINE L");
   else sent=g_trade.Sell(InpV62FixedLot,_Symbol,0.0,stop,tp,"V62 REFINE S");

   string send_detail=(sent ? "sent" : "rejected_"+IntegerToString((int)g_trade.ResultRetcode()));
   V62PendingEvent("REFINED_ENTRY",d,send_detail,entry,risk_cash,spread_cash);
   if(sent)
   {
      V62StartShadow(d,entry,stop,risk_cash,g_v62_pending_score);
      g_v62_pending=false;
      g_v62_pending_dir=0;
      g_v62_pending_armed=0;
   }
}
'''

EVALUATE_BAR = r'''
void V62EvaluateBar()
{
   V62Features f;
   bool ready=V62BuildFeatures(f);
   string why=(ready ? "" : "feature_not_ready");
   int d=(ready ? V62SelectDirection(f,why) : 0);
   if(d==0) return;
   if(d!=InpV62AllowedDirection)
   {
      V62LogDirectionalEval(f,d,why,"direction_isolated_out",0,0,0,0,0,0,0,0,0,"none");
      return;
   }
   V62ArmPending(d,f,why);
}
'''

ON_TICK = r'''
void OnTick()
{
   V62UpdateShadow();
   V62ManageProfitRatchet();
   V62MaybeSoftLossCut();
   V62ManagePendingEntry();

   datetime bar=iTime(_Symbol,PERIOD_M15,0);
   if(bar<=0 || bar==g_last_m15_bar) return;
   g_last_m15_bar=bar;
   if(g_shadow_open) g_shadow_bars++;

   ulong ticket=0;int d=0;double e=0,s=0,t=0;
   if(V62OwnedPosition(ticket,d,e,s,t)) return;
   if(g_shadow_open) return;
   V62EvaluateBar();
}
'''


def transform(allowed_direction: int) -> str:
    if allowed_direction not in (-1, 1):
        raise ValueError("allowed_direction must be -1 or 1")

    text = parent.transform()
    text = replace_once(text, '#property version   "61.00"', '#property version   "62.00"', "version")
    text = text.replace("V61", "V62").replace("v61", "v62")
    text = text.replace(r"mt5_quant\\v62_profit_ratchet_m5_refinement", V62_ROOT)
    text = replace_once(text, "input long   InpV62Magic = 610061;", "input long   InpV62Magic = 620062;", "magic")
    text = replace_once(
        text,
        "input bool   InpV62UseM5Refinement = true;\ninput double InpV62M5StopAtrBuffer = 0.10;",
        "input bool   InpV62UseM5Refinement = true;\n"
        "input double InpV62M5StopAtrBuffer = 0.10;\n"
        f"input int    InpV62AllowedDirection = {allowed_direction};\n"
        "input int    InpV62PendingMaxMinutes = 240;\n"
        "input double InpV62M5RetestAtr = 0.30;\n"
        "input double InpV62M5ReclaimAtr = 0.10;",
        "direction and entry-refinement inputs",
    )

    globals_anchor = 'string g_v62_stop_source="";'
    globals_new = globals_anchor + r'''
bool g_v62_pending=false;
int g_v62_pending_dir=0;
datetime g_v62_pending_armed=0;
datetime g_v62_last_m1_bar=0;
double g_v62_pending_reference=0.0;
double g_v62_pending_raw_stop=0.0;
int g_v62_pending_score=0;'''
    text = replace_once(text, globals_anchor, globals_new, "pending primitive globals")

    features_anchor = "   int short_score;\n};"
    text = replace_once(text, features_anchor, features_anchor + "\nV62Features g_v62_pending_features;", "pending feature state")

    text = replace_function(text, "void V62EvaluateBar()", "int OnInit()", PENDING_HELPERS + "\n\n" + EVALUATE_BAR, "evaluate")
    text = replace_function(text, "void OnTick()", "void OnTradeTransaction", ON_TICK, "OnTick")

    validate(text, allowed_direction)
    return text


def validate(text: str, allowed_direction: int) -> None:
    required = (
        V62_ROOT,
        "InpV62FixedLot = 0.01",
        "InpV62PrimaryTargetCash = 3.00",
        "InpV62ProfitArmCash = 2.00",
        "InpV62ProfitLockCash = 1.00",
        "InpV62MinStopRiskCash = 0.75",
        "InpV62MaxStopRiskCash = 1.25",
        f"InpV62AllowedDirection = {allowed_direction}",
        "InpV62PendingMaxMinutes = 240",
        "CopyRates(_Symbol,PERIOD_M5,1,120,m5)",
        "CopyRates(_Symbol,PERIOD_M1,1,40,m1)",
        "m5_retest_m1_turn",
        "PENDING_ARM",
        "REFINE_WAIT",
        "REFINED_ENTRY",
        "V62OrderPreflight",
        "V62ManageProfitRatchet",
        "g_trade.Buy",
        "g_trade.Sell",
    )
    for token in required:
        if token not in text:
            raise RuntimeError(f"V62 required token missing: {token}")
    if r"mt5_quant\\v62_profit_ratchet_m5_refinement" in text:
        raise RuntimeError("V62 stale inherited FILE_COMMON root remains")
    struct_end = text.index("   int short_score;\n};")
    pending_decl = text.index("V62Features g_v62_pending_features;")
    if pending_decl <= struct_end:
        raise RuntimeError("V62 pending feature state declared before V62Features definition")


def build(output: Path, allowed_direction: int) -> str:
    text = transform(allowed_direction).replace("\n", "\r\n")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8", newline="")
    digest = sha256(output)
    print(f"V62_SOURCE_SHA256={digest}")
    print(f"V62_SOURCE_PATH={output}")
    print(f"V62_ALLOWED_DIRECTION={allowed_direction}")
    print(f"V62_FILE_COMMON_ROOT={V62_ROOT}")
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
