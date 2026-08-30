#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT = HERE / "build_v62_direction_isolated_entry_refinement_source.py"
V63_ROOT = r"mt5_quant\\v63_profit_quality_risk_zone"
FIXED_LOT = 0.01
MAGIC = 630063


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


parent = load(PARENT, "v62_parent_for_v63")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        raise RuntimeError(f"V63 {label} drifted expected=1 actual={n}")
    return text.replace(old, new, 1)


def replace_function(text: str, start_sig: str, next_sig: str, replacement: str, label: str) -> str:
    start = text.find(start_sig)
    if start < 0:
        raise RuntimeError(f"V63 function missing {label} start={start_sig}")
    end = text.find(next_sig, start + len(start_sig))
    if end < 0:
        raise RuntimeError(f"V63 function missing {label} next={next_sig}")
    return text[:start] + replacement.strip() + "\n\n" + text[end:]


M5_STRUCTURAL_STOP = r'''
bool V63M5RefinedStop(const int d,const double entry,double &stop)
{
   stop=0.0;
   if(!InpV63UseM5Refinement || d==0 || entry<=0.0) return false;
   MqlRates m5[];
   ArraySetAsSeries(m5,true);
   int n=CopyRates(_Symbol,PERIOD_M5,1,180,m5);
   if(n<120) return false;

   double atr=V63ATR(m5,n,14,0);
   double ema20=V63EMA(m5,n,20,0);
   double ema50=V63EMA(m5,n,50,0);
   if(atr<=0.0 || ema20<=0.0 || ema50<=0.0) return false;

   // Risk-zone entry deliberately does NOT require current M5 close to have
   // already reclaimed EMA20. The M5 trend structure is EMA20/EMA50; price
   // proximity to the structural invalidation is handled by the cash-risk band.
   bool trend_ok=(d>0 ? ema20>ema50 : ema20<ema50);
   if(!trend_ok) return false;

   double sh1=0,sh2=0,sl1=0,sl2=0;int shi1=-1,shi2=-1,sli1=-1,sli2=-1;
   V63ConfirmedSwings(m5,n,sh1,shi1,sh2,shi2,sl1,sli1,sl2,sli2);
   if(shi2<0 || sli2<0) return false;

   bool structure_ok=(d>0 ? (sl1>=sl2 || sh1>sh2) : (sh1<=sh2 || sl1<sl2));
   if(!structure_ok) return false;

   if(d>0) stop=sl1-InpV63M5StopAtrBuffer*atr;
   else stop=sh1+InpV63M5StopAtrBuffer*atr;

   if((d>0 && stop>=entry) || (d<0 && stop<=entry)) return false;
   return true;
}
'''

MICRO_AND_QUALITY = r'''
bool V63M1TurnConfirmed(const int d,string &detail)
{
   detail="";
   MqlRates m1[];
   ArraySetAsSeries(m1,true);
   int n1=CopyRates(_Symbol,PERIOD_M1,1,40,m1);
   if(n1<12){detail="m1_history_not_ready";return false;}

   bool turn=(d>0 ?
      (m1[0].close>m1[0].open && m1[0].close>m1[1].close && m1[0].high>=m1[1].high) :
      (m1[0].close<m1[0].open && m1[0].close<m1[1].close && m1[0].low<=m1[1].low));
   if(!turn){detail="m1_turn_not_confirmed";return false;}
   detail="m1_turn_confirmed";
   return true;
}

bool V63EntryQualityPass(const int d,V63Features &f,string &detail)
{
   detail="";
   if(f.h4_trend!=d || f.h1_trend!=d){detail="stale_h4_h1_regime";return false;}

   // V62 week4 showed that slow H4/H1 trend can remain bullish after shorter
   // momentum has already turned. Use existing causal indicators as a veto,
   // rather than adding confluence points that would disguise the conflict.
   if(f.di_dir==-d && f.macd_dir==-d)
   {detail="momentum_double_opposed";return false;}

   if(f.adx<InpV63MinEntryADX && f.m15_trend!=d && f.bos_choch_dir!=d)
   {detail="weak_trend_chop";return false;}

   if(f.m15_trend==-d && f.structure_dir==-d && f.bos_choch_dir==-d)
   {detail="m15_structure_triple_opposed";return false;}

   detail="entry_quality_ok";
   return true;
}
'''

ARM_PENDING = r'''
void V63ArmPending(const int d,V63Features &f,const string why)
{
   if(d==0 || d!=InpV63AllowedDirection) return;

   // A repeated M15 signal may confirm that the setup still exists, but it must
   // never extend the original TTL. This fixes V62's timer-reset defect.
   if(g_v63_pending)
   {
      if(g_v63_pending_dir==d)
      {
         V63PendingEvent("PENDING_REFRESH",d,"first_arm_ttl_preserved",g_v63_pending_reference,
                         g_v63_pending_raw_stop,(double)g_v63_pending_score);
         return;
      }
      V63ClearPending("direction_changed_before_rearm");
   }

   double raw=V63RawM15Stop(d,f);
   MqlTick t;
   if(!SymbolInfoTick(_Symbol,t)) return;
   double entry=(d>0 ? t.ask : t.bid);
   if(raw<=0.0 || (d>0 && raw>=entry) || (d<0 && raw<=entry))
   {
      V63LogDirectionalEval(f,d,why,"invalid_arm_structural_stop",entry,raw,0,0,0,0,0,0,0,"m15");
      return;
   }

   g_v63_pending=true;
   g_v63_pending_dir=d;
   g_v63_pending_features=f;
   g_v63_pending_armed=TimeCurrent();
   g_v63_pending_reference=entry;
   g_v63_pending_raw_stop=raw;
   g_v63_pending_score=(d>0 ? f.long_score : f.short_score);
   V63LogDirectionalEval(f,d,why,"pending_risk_zone_entry",entry,raw,0,0,0,0,0,0,0,"m15");
   V63PendingEvent("PENDING_ARM",d,"first_arm",entry,raw,(double)g_v63_pending_score);
}
'''

MANAGE_PENDING = r'''
void V63ManagePendingEntry()
{
   if(!g_v63_pending || InpV63ScreenOnly) return;
   if(g_v63_pending_dir!=InpV63AllowedDirection){V63ClearPending("direction_mismatch");return;}

   ulong ticket=0;int pd=0;double pe=0,ps=0,pt=0;
   if(V63OwnedPosition(ticket,pd,pe,ps,pt)){V63ClearPending("position_exists");return;}
   if(g_shadow_open){V63ClearPending("shadow_exists");return;}

   if(TimeCurrent()-g_v63_pending_armed>InpV63PendingMaxMinutes*60)
   {V63ClearPending("expired_first_arm_ttl");return;}

   MqlTick tick;
   if(!SymbolInfoTick(_Symbol,tick)) return;
   double px=(g_v63_pending_dir>0 ? tick.bid : tick.ask);
   if((g_v63_pending_dir>0 && px<=g_v63_pending_raw_stop) ||
      (g_v63_pending_dir<0 && px>=g_v63_pending_raw_stop))
   {V63ClearPending("invalidated_before_entry");return;}

   datetime m1bar=iTime(_Symbol,PERIOD_M1,0);
   if(m1bar<=0 || m1bar==g_v63_last_m1_bar) return;
   g_v63_last_m1_bar=m1bar;

   int d=g_v63_pending_dir;

   // Rebuild all slow/medium features at the actual entry decision. H4/H1 must
   // still align. A neutral current selector is allowed during a pullback; only
   // an actual opposite selector invalidates the pending trend setup.
   V63Features cur;
   if(!V63BuildFeatures(cur)) return;
   if(cur.h4_trend!=d || cur.h1_trend!=d)
   {
      V63PendingEvent("ENTRY_VETO",d,"stale_h4_h1_regime",cur.adx,(double)cur.h4_trend,(double)cur.h1_trend);
      V63ClearPending("stale_h4_h1_regime");
      return;
   }
   string current_why="";
   int current_d=V63SelectDirection(cur,current_why);
   if(current_d==-d)
   {
      V63PendingEvent("ENTRY_VETO",d,"opposite_current_selector",(double)current_d,cur.adx,0.0);
      V63ClearPending("opposite_current_selector");
      return;
   }

   string quality="";
   if(!V63EntryQualityPass(d,cur,quality))
   {
      V63PendingEvent("ENTRY_VETO",d,quality,cur.adx,(double)cur.di_dir,(double)cur.macd_dir);
      V63ClearPending(quality);
      return;
   }

   if(!SymbolInfoTick(_Symbol,tick)) return;
   double entry=(d>0 ? tick.ask : tick.bid);
   double stop=0.0,tp=0.0,risk_cash=0.0,risk_pct=0.0,margin_cash=0.0,spread_points=0.0,spread_cash=0.0;
   string reject="";

   // Structural-risk-zone entry: do not enter first and then search for a tight
   // stop. Wait until the CURRENT market price is naturally close enough to a
   // valid M5 structural invalidation for the fixed 0.01 lot risk budget.
   bool feasible=V63BuildStopTarget(d,cur,entry,stop,tp,risk_cash,risk_pct,
                                    margin_cash,spread_points,spread_cash,reject);
   if(!feasible)
   {
      string event=(reject=="structural_risk_cash_cap" || reject=="structural_risk_too_tight" ||
                    reject=="stop_too_far_atr" ? "RISK_ZONE_WAIT" : "REFINE_WAIT");
      V63PendingEvent(event,d,reject,entry,risk_cash,spread_cash);
      return;
   }

   if(g_v63_stop_source!="m5")
   {
      V63PendingEvent("RISK_ZONE_WAIT",d,"m5_structural_stop_not_ready",entry,risk_cash,spread_cash);
      return;
   }

   string m1detail="";
   if(!V63M1TurnConfirmed(d,m1detail))
   {
      V63PendingEvent("REFINE_WAIT",d,m1detail,entry,risk_cash,spread_cash);
      return;
   }

   V63LogDirectionalEval(cur,d,"risk_zone_refined_entry","",entry,stop,tp,risk_cash,risk_pct,
                         margin_cash,spread_points,spread_cash,1,g_v63_stop_source);

   string preflight_detail="";long preflight_retcode=0;
   if(!V63OrderPreflight(d,entry,stop,tp,preflight_detail,preflight_retcode))
   {
      V63PendingEvent("ORDER_PREFLIGHT",d,preflight_detail,entry,stop,(double)preflight_retcode);
      V63ClearPending("preflight_block");
      return;
   }

   g_trade.SetExpertMagicNumber(InpV63Magic);
   g_trade.SetDeviationInPoints(50);
   g_trade.SetTypeFillingBySymbol(_Symbol);
   bool sent=false;
   if(d>0) sent=g_trade.Buy(InpV63FixedLot,_Symbol,0.0,stop,tp,"V63 RISKZONE L");
   else sent=g_trade.Sell(InpV63FixedLot,_Symbol,0.0,stop,tp,"V63 RISKZONE S");

   string send_detail=(sent ? "sent" : "rejected_"+IntegerToString((int)g_trade.ResultRetcode()));
   V63PendingEvent("REFINED_ENTRY",d,send_detail,entry,risk_cash,spread_cash);
   if(sent)
   {
      V63StartShadow(d,entry,stop,risk_cash,g_v63_pending_score);
      g_v63_pending=false;
      g_v63_pending_dir=0;
      g_v63_pending_armed=0;
   }
}
'''

EVALUATE_BAR = r'''
void V63EvaluateBar()
{
   V63Features f;
   bool ready=V63BuildFeatures(f);
   string why=(ready ? "" : "feature_not_ready");
   int d=(ready ? V63SelectDirection(f,why) : 0);
   if(d==0) return;

   if(d!=InpV63AllowedDirection)
   {
      if(g_v63_pending) V63ClearPending("opposite_direction_signal");
      V63LogDirectionalEval(f,d,why,"direction_isolated_out",0,0,0,0,0,0,0,0,0,"none");
      return;
   }
   V63ArmPending(d,f,why);
}
'''

HARD_LOSS_GUARD = r'''
void V63HardCashLossGuard()
{
   if(InpV63ScreenOnly || InpV63EmergencyLossCash<=0.0) return;
   ulong ticket=0;int d=0;double entry=0.0,sl=0.0,tp=0.0;
   if(!V63OwnedPosition(ticket,d,entry,sl,tp)) return;

   MqlTick tick;
   if(!SymbolInfoTick(_Symbol,tick)) return;
   double exitp=(d>0 ? tick.bid : tick.ask);
   ENUM_ORDER_TYPE ot=(d>0 ? ORDER_TYPE_BUY : ORDER_TYPE_SELL);
   double floating=0.0;
   if(!OrderCalcProfit(ot,_Symbol,InpV63FixedLot,entry,exitp,floating)) return;
   if(floating>-InpV63EmergencyLossCash) return;

   g_trade.SetExpertMagicNumber(InpV63Magic);
   bool closed=g_trade.PositionClose(ticket);
   V63Append(V63_EVENTS,TimeToString(TimeCurrent(),TIME_DATE|TIME_MINUTES|TIME_SECONDS)+
      ",HARD_CASH_LOSS,"+IntegerToString(d)+","+(closed?"closed":"close_failed")+","+
      DoubleToString(floating,4)+","+DoubleToString(sl,_Digits)+","+DoubleToString(tp,_Digits));
}
'''

ON_TICK = r'''
void OnTick()
{
   V63UpdateShadow();
   V63HardCashLossGuard();
   V63ManageProfitRatchet();
   V63MaybeSoftLossCut();
   V63ManagePendingEntry();

   datetime bar=iTime(_Symbol,PERIOD_M15,0);
   if(bar<=0 || bar==g_last_m15_bar) return;
   g_last_m15_bar=bar;
   if(g_shadow_open) g_shadow_bars++;

   ulong ticket=0;int d=0;double e=0,s=0,t=0;
   if(V63OwnedPosition(ticket,d,e,s,t)) return;
   if(g_shadow_open) return;
   V63EvaluateBar();
}
'''


def transform(allowed_direction: int) -> str:
    if allowed_direction not in (-1, 1):
        raise ValueError("allowed_direction must be -1 or 1")

    text = parent.transform(allowed_direction)
    text = replace_once(text, '#property version   "62.00"', '#property version   "63.00"', "version")
    text = text.replace("V62", "V63").replace("v62", "v63")
    text = text.replace(r"mt5_quant\\v63_direction_isolated_entry_refinement", V63_ROOT)

    text = replace_once(text, "input long   InpV63Magic = 620062;", "input long   InpV63Magic = 630063;", "magic")
    text = replace_once(text, "input double InpV63PrimaryTargetCash = 3.00;", "input double InpV63PrimaryTargetCash = 3.50;", "target")
    text = replace_once(text, "input double InpV63MinStopRiskCash = 0.75;", "input double InpV63MinStopRiskCash = 0.60;", "min planned risk")
    text = replace_once(text, "input double InpV63MaxStopRiskCash = 1.25;", "input double InpV63MaxStopRiskCash = 1.05;", "max planned risk")
    text = replace_once(
        text,
        "input double InpV63M5RetestAtr = 0.30;\ninput double InpV63M5ReclaimAtr = 0.10;",
        "input double InpV63EmergencyLossCash = 1.10;\n"
        "input double InpV63MinEntryADX = 16.0;",
        "profit-quality inputs",
    )

    text = replace_function(text, "bool V63M5RefinedStop", "bool V63BuildStopTarget", M5_STRUCTURAL_STOP, "M5 structural stop")
    text = replace_function(text, "bool V63MicroEntryReady", "void V63ArmPending", MICRO_AND_QUALITY, "micro and quality")
    text = replace_function(text, "void V63ArmPending", "void V63ManagePendingEntry", ARM_PENDING, "arm pending")
    text = replace_function(text, "void V63ManagePendingEntry", "void V63EvaluateBar", MANAGE_PENDING, "manage pending")
    text = replace_function(text, "void V63EvaluateBar", "int OnInit()", EVALUATE_BAR, "evaluate")
    text = replace_once(text, "void OnTick()", HARD_LOSS_GUARD + "\nvoid OnTick()", "hard loss helper")
    text = replace_function(text, "void OnTick()", "void OnTradeTransaction", ON_TICK, "OnTick")
    text = replace_once(
        text,
        "int OnInit()\n{",
        "int OnInit()\n{\n   if(InpV63EmergencyLossCash<=0.0 || InpV63MinEntryADX<0.0) return INIT_PARAMETERS_INCORRECT;",
        "V63 init guard",
    )

    validate(text, allowed_direction)
    return text


def validate(text: str, allowed_direction: int) -> None:
    required = (
        V63_ROOT,
        "InpV63FixedLot = 0.01",
        "InpV63PrimaryTargetCash = 3.50",
        "InpV63ProfitArmCash = 2.00",
        "InpV63ProfitLockCash = 1.00",
        "InpV63MinStopRiskCash = 0.60",
        "InpV63MaxStopRiskCash = 1.05",
        "InpV63EmergencyLossCash = 1.10",
        "InpV63MinEntryADX = 16.0",
        f"InpV63AllowedDirection = {allowed_direction}",
        "expired_first_arm_ttl",
        "first_arm_ttl_preserved",
        "stale_h4_h1_regime",
        "opposite_current_selector",
        "momentum_double_opposed",
        "weak_trend_chop",
        "RISK_ZONE_WAIT",
        "m5_structural_stop_not_ready",
        "CopyRates(_Symbol,PERIOD_M1,1,40,m1)",
        "V63BuildStopTarget(d,cur,entry",
        "HARD_CASH_LOSS",
        "V63OrderPreflight",
        "g_trade.Buy",
        "g_trade.Sell",
    )
    for token in required:
        if token not in text:
            raise RuntimeError(f"V63 required token missing: {token}")
    if r"mt5_quant\\v63_direction_isolated_entry_refinement" in text:
        raise RuntimeError("V63 stale inherited FILE_COMMON root remains")
    if "InpV63M5RetestAtr" in text or "InpV63M5ReclaimAtr" in text:
        raise RuntimeError("V63 obsolete EMA-retest entry inputs remain")

    arm_start = text.index("void V63ArmPending")
    arm_end = text.index("void V63ManagePendingEntry", arm_start)
    arm_body = text[arm_start:arm_end]
    if arm_body.count("g_v63_pending_armed=TimeCurrent()") != 1:
        raise RuntimeError("V63 first-arm TTL assignment must occur exactly once in ArmPending")
    if arm_body.index("if(g_v63_pending)") > arm_body.index("g_v63_pending_armed=TimeCurrent()"):
        raise RuntimeError("V63 repeated pending guard must precede first-arm timestamp assignment")


def build(output: Path, allowed_direction: int) -> str:
    text = transform(allowed_direction).replace("\n", "\r\n")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8", newline="")
    digest = sha256(output)
    print(f"V63_SOURCE_SHA256={digest}")
    print(f"V63_SOURCE_PATH={output}")
    print(f"V63_ALLOWED_DIRECTION={allowed_direction}")
    print(f"V63_FILE_COMMON_ROOT={V63_ROOT}")
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
