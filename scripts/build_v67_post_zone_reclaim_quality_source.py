#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT = HERE / "build_v66_post_bos_cash_zone_source_fixed.py"
V66_ROOT = r"mt5_quant\\v66_post_bos_cash_zone"
V67_ROOT = r"mt5_quant\\v67_post_zone_reclaim_quality"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


parent = load(PARENT, "v66_parent_for_v67")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        raise RuntimeError(f"V67 {label} drifted expected=1 actual={n}")
    return text.replace(old, new, 1)


def replace_function(text: str, start_sig: str, next_sig: str, replacement: str, label: str) -> str:
    start = text.find(start_sig)
    if start < 0:
        raise RuntimeError(f"V67 function missing {label} start={start_sig}")
    end = text.find(next_sig, start + len(start_sig))
    if end < 0:
        raise RuntimeError(f"V67 function missing {label} next={next_sig}")
    return text[:start] + replacement.strip() + "\n\n" + text[end:]


V67_GLOBALS = r'''

// V67 does not enter on the first cash-zone touch. The original BOS-owned
// structural stop remains fixed. Price must penetrate deeper into the zone,
// survive without breaching structure, and then print a closed-M1 rejection /
// reclaim before execution is allowed.
bool g_v67_zone_touched=false;
bool g_v67_penetrated=false;
bool g_v67_reversal_confirmed=false;
datetime g_v67_zone_touch_time=0;
datetime g_v67_zone_touch_bar=0;
datetime g_v67_last_confirm_closed_bar=0;
datetime g_v67_reversal_confirmed_at=0;
double g_v67_zone_touch_risk=0.0;
double g_v67_best_risk_cash=DBL_MAX;
double g_v67_zone_extreme=0.0;
double g_v67_confirm_extreme=0.0;
'''


V67_STAGE_FUNCTIONS = r'''
void V67ResetZoneState()
{
   g_v67_zone_touched=false;
   g_v67_penetrated=false;
   g_v67_reversal_confirmed=false;
   g_v67_zone_touch_time=0;
   g_v67_zone_touch_bar=0;
   g_v67_last_confirm_closed_bar=0;
   g_v67_reversal_confirmed_at=0;
   g_v67_zone_touch_risk=0.0;
   g_v67_best_risk_cash=DBL_MAX;
   g_v67_zone_extreme=0.0;
   g_v67_confirm_extreme=0.0;
}

void V66ClearMicroPending(const string reason)
{
   if(g_v66_micro_pending)
      V64PendingEvent("MICRO_ENTRY_END",g_v66_micro_dir,reason,g_v66_micro_stop,
                      (double)(TimeCurrent()-g_v66_micro_armed),(double)g_v66_micro_arch);
   g_v66_micro_pending=false;
   g_v66_micro_dir=0;
   g_v66_micro_armed=0;
   g_v66_micro_stop=0.0;
   g_v66_micro_arch=V64_ARCH_NONE;
   g_v66_micro_score=0;
   g_v66_micro_wait_reason="";
   V67ResetZoneState();
}

void V66ArmMicroPending(const int d,const int arch,const double micro_stop,const int score,
                        const double current_risk,const double spread_cash,const double ratio)
{
   if(d==0 || micro_stop<=0.0 || !MathIsValidNumber(micro_stop)) return;

   if(g_v66_micro_pending)
   {
      bool better=(d==g_v66_micro_dir &&
                   ((d>0 && micro_stop>g_v66_micro_stop) ||
                    (d<0 && micro_stop<g_v66_micro_stop)));
      if(better)
      {
         g_v66_micro_stop=micro_stop;
         g_v66_micro_arch=arch;
         g_v66_micro_score=score;
         g_v66_micro_wait_reason="";
         V67ResetZoneState();
         V64PendingEvent("MICRO_ENTRY_REFRESH",d,"better_structural_stop_zone_reset_ttl_preserved",
                         current_risk,spread_cash,ratio);
      }
      else
      {
         V64PendingEvent("MICRO_ENTRY_REFRESH",d,"first_micro_arm_ttl_preserved",
                         current_risk,spread_cash,ratio);
      }
      return;
   }

   g_v66_micro_pending=true;
   g_v66_micro_dir=d;
   g_v66_micro_armed=TimeCurrent();
   g_v66_micro_stop=micro_stop;
   g_v66_micro_arch=arch;
   g_v66_micro_score=score;
   g_v66_micro_wait_reason="";
   V67ResetZoneState();
   V64PendingEvent("MICRO_ENTRY_ARM",d,V64ArchName(arch),current_risk,spread_cash,ratio);
}

void V66MicroWaitEvent(const int d,const string reason,const double risk_cash,
                       const double spread_cash,const double ratio)
{
   if(reason==g_v66_micro_wait_reason) return;
   g_v66_micro_wait_reason=reason;
   V64PendingEvent("MICRO_ENTRY_WAIT",d,reason,risk_cash,spread_cash,ratio);
}

bool V67PostZoneReversalConfirmed(const int d,string &detail)
{
   detail="";
   if(!g_v67_zone_touched || !g_v67_penetrated)
   {detail="zone_penetration_not_ready";return false;}

   MqlRates m1[];ArraySetAsSeries(m1,true);
   int n=CopyRates(_Symbol,PERIOD_M1,1,40,m1);
   if(n<20){detail="m1_history_not_ready";return false;}
   if(g_v67_zone_touch_bar>0 && m1[0].time<g_v67_zone_touch_bar)
   {detail="closed_bar_predates_zone_touch";return false;}

   double atr=V64ATR(m1,n,14,0);
   if(atr<=0.0){detail="m1_atr_not_ready";return false;}
   double body=MathAbs(m1[0].close-m1[0].open);
   double range=MathMax(_Point,m1[0].high-m1[0].low);
   if(body<InpV67MinReclaimBodyAtr*atr)
   {detail="reclaim_body_too_small";return false;}
   if(body/range<InpV67MinReclaimBodyFraction)
   {detail="reclaim_body_fraction_weak";return false;}

   double close_loc=(d>0 ? (m1[0].close-m1[0].low)/range : (m1[0].high-m1[0].close)/range);
   if(close_loc<InpV67MinReclaimCloseLocation)
   {detail="reclaim_close_location_weak";return false;}

   bool directional=(d>0 ? m1[0].close>m1[0].open : m1[0].close<m1[0].open);
   if(!directional){detail="reclaim_candle_wrong_direction";return false;}

   bool progress=(d>0 ? m1[0].close>m1[1].close+InpV67PrevCloseBufferAtr*atr
                      : m1[0].close<m1[1].close-InpV67PrevCloseBufferAtr*atr);
   if(!progress){detail="reclaim_no_close_progress";return false;}

   bool reclaimed=(d>0 ? m1[0].close>g_v67_zone_extreme+InpV67ReclaimFromExtremeAtr*atr
                       : m1[0].close<g_v67_zone_extreme-InpV67ReclaimFromExtremeAtr*atr);
   if(!reclaimed){detail="reclaim_distance_from_extreme_weak";return false;}

   detail="post_zone_rejection_reclaim";
   return true;
}

void V66TryMicroEntry()
{
   if(!g_v66_micro_pending || InpV64ScreenOnly) return;
   int d=g_v66_micro_dir;
   if(d!=InpV64AllowedDirection){V66ClearMicroPending("direction_mismatch");return;}

   ulong ticket=0;int pd=0;double pe=0,ps=0,pt=0;
   if(V64OwnedPosition(ticket,pd,pe,ps,pt)){V66ClearMicroPending("position_exists");return;}
   if(TimeCurrent()-g_v66_micro_armed>InpV66MicroEntryTTLMinutes*60)
   {
      V64PendingEvent("MICRO_ENTRY_EXPIRE",d,V64ArchName(g_v66_micro_arch),g_v66_micro_stop,0,0);
      V66ClearMicroPending("expired_first_micro_arm_ttl");
      return;
   }

   MqlTick tick;if(!SymbolInfoTick(_Symbol,tick)) return;
   double invalidation_px=(d>0 ? tick.bid : tick.ask);
   if((d>0 && invalidation_px<=g_v66_micro_stop) || (d<0 && invalidation_px>=g_v66_micro_stop))
   {
      V64PendingEvent("MICRO_ENTRY_INVALIDATE",d,"micro_structural_stop_breached",invalidation_px,g_v66_micro_stop,0);
      V66ClearMicroPending("micro_structural_stop_breached");
      return;
   }

   double entry=(d>0 ? tick.ask : tick.bid);
   double risk_cash=V64RiskCash(d,entry,g_v66_micro_stop,InpV64FixedLot);
   double spread_points=0.0;
   double spread_cash=V64SpreadCash(d,InpV64FixedLot,spread_points);
   double ratio=(spread_cash>0.0 ? risk_cash/spread_cash : 0.0);
   if(risk_cash<=0.0 || !MathIsValidNumber(risk_cash))
   {V64PendingEvent("MICRO_ENTRY_BLOCK",d,"raw_micro_risk_invalid",risk_cash,spread_cash,ratio);V66ClearMicroPending("raw_micro_risk_invalid");return;}

   if(!g_v67_zone_touched)
   {
      if(risk_cash>InpV64MaxStopRiskCash+1e-9)
      {V66MicroWaitEvent(d,"above_reclaim_zone",risk_cash,spread_cash,ratio);return;}

      g_v67_zone_touched=true;
      g_v67_zone_touch_time=TimeCurrent();
      g_v67_zone_touch_bar=iTime(_Symbol,PERIOD_M1,0);
      g_v67_zone_touch_risk=risk_cash;
      g_v67_best_risk_cash=risk_cash;
      g_v67_zone_extreme=invalidation_px;
      g_v66_micro_wait_reason="";
      V64PendingEvent("MICRO_ENTRY_ZONE_TOUCH",d,V64ArchName(g_v66_micro_arch),risk_cash,spread_cash,ratio);
      // Critical V67 contract: first touch can never send an order.
      return;
   }

   bool new_adverse_extreme=(d>0 ? invalidation_px<g_v67_zone_extreme : invalidation_px>g_v67_zone_extreme);
   if(new_adverse_extreme)
   {
      g_v67_zone_extreme=invalidation_px;
      if(g_v67_reversal_confirmed &&
         (d>0 ? invalidation_px<g_v67_confirm_extreme : invalidation_px>g_v67_confirm_extreme))
      {
         g_v67_reversal_confirmed=false;
         g_v67_reversal_confirmed_at=0;
         V64PendingEvent("POST_ZONE_CONFIRM_RESET",d,"new_adverse_extreme_requires_fresh_reclaim",
                         risk_cash,spread_cash,ratio);
      }
   }
   if(risk_cash<g_v67_best_risk_cash) g_v67_best_risk_cash=risk_cash;

   if(!g_v67_penetrated && g_v67_best_risk_cash<=InpV67PenetrationRiskCash+1e-9)
   {
      g_v67_penetrated=true;
      V64PendingEvent("MICRO_ENTRY_PENETRATION",d,V64ArchName(g_v66_micro_arch),
                      g_v67_best_risk_cash,spread_cash,ratio);
   }

   if(!g_v67_penetrated)
   {
      V66MicroWaitEvent(d,"waiting_deeper_zone_penetration",risk_cash,spread_cash,ratio);
      return;
   }

   if(g_v67_reversal_confirmed &&
      TimeCurrent()-g_v67_reversal_confirmed_at>InpV67ConfirmValidityMinutes*60)
   {
      g_v67_reversal_confirmed=false;
      g_v67_reversal_confirmed_at=0;
      V64PendingEvent("POST_ZONE_CONFIRM_RESET",d,"reclaim_confirmation_expired",risk_cash,spread_cash,ratio);
   }

   if(!g_v67_reversal_confirmed)
   {
      datetime closed_bar=iTime(_Symbol,PERIOD_M1,1);
      if(closed_bar<=0 || closed_bar==g_v67_last_confirm_closed_bar) return;
      g_v67_last_confirm_closed_bar=closed_bar;

      string confirm_detail="";
      if(!V67PostZoneReversalConfirmed(d,confirm_detail))
      {
         V64PendingEvent("POST_ZONE_CONFIRM_WAIT",d,confirm_detail,risk_cash,spread_cash,ratio);
         return;
      }

      g_v67_reversal_confirmed=true;
      g_v67_reversal_confirmed_at=TimeCurrent();
      g_v67_confirm_extreme=g_v67_zone_extreme;
      g_v66_micro_wait_reason="";
      V64PendingEvent("POST_ZONE_REVERSAL_CONFIRM",d,confirm_detail,risk_cash,spread_cash,ratio);
   }

   double stop=0,tp=0,risk_pct=0,margin_cash=0,build_spread_points=0,build_spread_cash=0,build_ratio=0;string reject="";
   bool feasible=V64BuildMicroStopTarget(d,entry,g_v66_micro_stop,stop,tp,risk_cash,risk_pct,
                                         margin_cash,build_spread_points,build_spread_cash,build_ratio,reject);
   spread_cash=build_spread_cash;ratio=build_ratio;
   if(!feasible)
   {
      if(reject=="micro_risk_cash_cap")
      {V66MicroWaitEvent(d,"confirmed_above_cash_zone",risk_cash,spread_cash,ratio);return;}
      if(reject=="micro_risk_too_tight" || reject=="broker_stop_too_close")
      {V66MicroWaitEvent(d,"confirmed_near_stop_wait_rebound",risk_cash,spread_cash,ratio);return;}
      if(reject=="micro_risk_spread_ratio_low" || reject=="spread_cost_guard")
      {V66MicroWaitEvent(d,"confirmed_spread_geometry_wait",risk_cash,spread_cash,ratio);return;}
      if(reject=="invalid_micro_structural_stop")
      {V64PendingEvent("MICRO_ENTRY_INVALIDATE",d,reject,entry,g_v66_micro_stop,risk_cash);V66ClearMicroPending(reject);return;}
      V64PendingEvent("MICRO_ENTRY_BLOCK",d,reject,risk_cash,spread_cash,ratio);
      V66ClearMicroPending(reject);
      return;
   }

   // Revalidate the slower causal context at the actual post-reclaim entry tick.
   V64Features cur;if(!V64BuildFeatures(cur)) return;
   if(cur.h4_trend!=d || cur.h1_trend!=d)
   {V64PendingEvent("MICRO_ENTRY_INVALIDATE",d,"stale_h4_h1_regime",cur.adx,(double)cur.h4_trend,(double)cur.h1_trend);V66ClearMicroPending("stale_h4_h1_regime");return;}
   string current_why="";int current_d=V64SelectDirection(cur,current_why);
   if(current_d==-d)
   {V64PendingEvent("MICRO_ENTRY_INVALIDATE",d,"opposite_current_selector",(double)current_d,cur.adx,0);V66ClearMicroPending("opposite_current_selector");return;}
   string quality="";
   if(!V64EntryQualityPass(d,cur,quality))
   {V64PendingEvent("MICRO_ENTRY_INVALIDATE",d,quality,cur.adx,(double)cur.di_dir,(double)cur.macd_dir);V66ClearMicroPending(quality);return;}
   double h1sep=0,h4sep=0,h1slope=0,h4slope=0,eff=0;string tq="";
   if(!V64TrendQualityPass(d,g_v66_micro_arch,tq,h1sep,h4sep,h1slope,h4slope,eff))
   {V64PendingEvent("MICRO_ENTRY_INVALIDATE",d,tq,h1sep,h4sep,eff);V66ClearMicroPending(tq);return;}
   double m5_context_stop=0.0;
   if(!V64M5RefinedStop(d,entry,m5_context_stop))
   {V66MicroWaitEvent(d,"m5_context_wait_after_reclaim",risk_cash,spread_cash,ratio);return;}

   g_v66_micro_wait_reason="";
   V64PendingEvent("POST_ZONE_ENTRY_READY",d,V64ArchName(g_v66_micro_arch),risk_cash,spread_cash,ratio);
   V64LogDirectionalEval(cur,d,"post_zone_reclaim_entry","",entry,stop,tp,risk_cash,risk_pct,
                         margin_cash,build_spread_points,spread_cash,1,"m1_micro_reclaim");

   string preflight_detail="";long preflight_retcode=0;
   if(!V64OrderPreflight(d,entry,stop,tp,preflight_detail,preflight_retcode))
   {V64PendingEvent("ORDER_PREFLIGHT",d,preflight_detail,entry,stop,(double)preflight_retcode);V66ClearMicroPending("preflight_block");return;}

   g_trade.SetExpertMagicNumber(InpV64Magic);g_trade.SetDeviationInPoints(50);g_trade.SetTypeFillingBySymbol(_Symbol);
   bool sent=(d>0 ? g_trade.Buy(InpV64FixedLot,_Symbol,0.0,stop,tp,"V67 RECLAIM L") : g_trade.Sell(InpV64FixedLot,_Symbol,0.0,stop,tp,"V67 RECLAIM S"));
   string send_detail=(sent ? "sent" : "rejected_"+IntegerToString((int)g_trade.ResultRetcode()));
   V64PendingEvent("REFINED_ENTRY",d,send_detail,entry,risk_cash,spread_cash);
   if(sent)
   {
      double shadow_entry=g_trade.ResultPrice();
      if(shadow_entry<=0.0) shadow_entry=entry;
      V64NoiseStart(d,shadow_entry);
      V64PendingEvent("NOISE_SHADOW",d,"actual_fill_anchor",shadow_entry,entry,shadow_entry-entry);
      V66ClearMicroPending("order_sent_after_reclaim");
   }
   else V66ClearMicroPending("order_rejected");
}
'''


def transform(allowed_direction: int) -> str:
    if allowed_direction not in (-1, 1):
        raise ValueError("allowed_direction must be -1 or 1")
    text = parent.transform(allowed_direction)
    text = replace_once(text, '#property version   "66.00"', '#property version   "67.00"', "version")
    text = text.replace('V66 post-BOS cash-zone research - TESTER ONLY', 'V67 post-zone reclaim quality research - TESTER ONLY')
    text = replace_once(text, "input long   InpV64Magic = 660066;", "input long   InpV64Magic = 670067;", "magic")
    text = replace_once(text, "input double InpV64MaxStopRiskCash = 1.25;", "input double InpV64MaxStopRiskCash = 1.10;", "planned-risk headroom")
    text = replace_once(
        text,
        "input int    InpV66MicroEntryTTLMinutes = 30;",
        "input int    InpV66MicroEntryTTLMinutes = 30;\n"
        "input double InpV67PenetrationRiskCash = 0.92;\n"
        "input double InpV67MinReclaimBodyAtr = 0.18;\n"
        "input double InpV67MinReclaimBodyFraction = 0.45;\n"
        "input double InpV67MinReclaimCloseLocation = 0.65;\n"
        "input double InpV67PrevCloseBufferAtr = 0.02;\n"
        "input double InpV67ReclaimFromExtremeAtr = 0.12;\n"
        "input int    InpV67ConfirmValidityMinutes = 5;",
        "post-zone reclaim inputs",
    )

    nroot = text.count(V66_ROOT)
    if nroot < 1:
        raise RuntimeError("V67 inherited V66 FILE_COMMON root missing")
    text = text.replace(V66_ROOT, V67_ROOT)
    if V66_ROOT in text:
        raise RuntimeError("V67 stale V66 FILE_COMMON root remains")

    text = replace_once(
        text,
        'string g_v66_micro_wait_reason="";',
        'string g_v66_micro_wait_reason="";' + V67_GLOBALS,
        "V67 zone globals",
    )
    text = replace_function(
        text,
        "void V66ClearMicroPending",
        "void V64ManagePendingEntry",
        V67_STAGE_FUNCTIONS,
        "post-zone stage",
    )

    validate(text, allowed_direction)
    return text


def validate(text: str, allowed_direction: int) -> None:
    required = (
        V67_ROOT,
        "InpV64Magic = 670067",
        "InpV64FixedLot = 0.01",
        "InpV64MaxStopRiskCash = 1.10",
        "InpV64EmergencyLossCash = 1.20",
        "InpV64PrimaryTargetCash = 3.50",
        "InpV64MinRiskSpreadRatio = 4.0",
        "InpV67PenetrationRiskCash = 0.92",
        "InpV67MinReclaimBodyAtr = 0.18",
        "InpV67ConfirmValidityMinutes = 5",
        f"InpV64AllowedDirection = {allowed_direction}",
        "MICRO_ENTRY_ZONE_TOUCH",
        "MICRO_ENTRY_PENETRATION",
        "POST_ZONE_CONFIRM_WAIT",
        "POST_ZONE_REVERSAL_CONFIRM",
        "POST_ZONE_CONFIRM_RESET",
        "POST_ZONE_ENTRY_READY",
        "post_zone_rejection_reclaim",
        "first touch can never send an order",
        "m1_micro_reclaim",
        "V67 RECLAIM",
        "V64NoiseStart(d,shadow_entry)",
    )
    for token in required:
        if token not in text:
            raise RuntimeError(f"V67 generated source missing token: {token}")
    if V66_ROOT in text:
        raise RuntimeError("V67 generated source contains stale V66 FILE_COMMON root")
    if "LongToString(" in text:
        raise RuntimeError("V67 generated source contains invalid MQL LongToString")

    stage = text[text.index("void V66TryMicroEntry"):text.index("void V64ManagePendingEntry")]
    touch = stage.index('V64PendingEvent("MICRO_ENTRY_ZONE_TOUCH"')
    touch_return = stage.index("return;", touch)
    preflight = stage.index("V64OrderPreflight")
    confirm = stage.index("V67PostZoneReversalConfirmed")
    if not (touch < touch_return < confirm < preflight):
        raise RuntimeError("V67 first-touch/reclaim/preflight ordering drifted")
    if "MathMax(g_v66_micro_stop" in stage or "MathMin(g_v66_micro_stop" in stage:
        raise RuntimeError("V67 must not clamp the structural stop")


def build(output: Path, allowed_direction: int) -> str:
    text = transform(allowed_direction).replace("\n", "\r\n")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8", newline="")
    digest = sha256(output)
    print(f"V67_SOURCE_SHA256={digest}")
    print(f"V67_SOURCE_PATH={output}")
    print(f"V67_ALLOWED_DIRECTION={allowed_direction}")
    print(f"V67_FILE_COMMON_ROOT={V67_ROOT}")
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
