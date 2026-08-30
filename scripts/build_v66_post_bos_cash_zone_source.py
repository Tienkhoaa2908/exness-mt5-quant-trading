#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT = HERE / "build_v65_micro_stop_calibration_source_fixed.py"
V65_ROOT = r"mt5_quant\\v65_micro_stop_calibration"
V66_ROOT = r"mt5_quant\\v66_post_bos_cash_zone"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


parent = load(PARENT, "v65_parent_for_v66")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        raise RuntimeError(f"V66 {label} drifted expected=1 actual={n}")
    return text.replace(old, new, 1)


def replace_function(text: str, start_sig: str, next_sig: str, replacement: str, label: str) -> str:
    start = text.find(start_sig)
    if start < 0:
        raise RuntimeError(f"V66 function missing {label} start={start_sig}")
    end = text.find(next_sig, start + len(start_sig))
    if end < 0:
        raise RuntimeError(f"V66 function missing {label} next={next_sig}")
    return text[:start] + replacement.strip() + "\n\n" + text[end:]


MICRO_STAGE_GLOBALS = r'''

// V66 second-stage execution state. A confirmed closed-M1 BOS owns a fixed
// structural stop; execution waits on real ticks until price reaches a cash-
// feasible zone. First-arm TTL is never reset by repeated candidate calls.
bool g_v66_micro_pending=false;
int g_v66_micro_dir=0;
datetime g_v66_micro_armed=0;
double g_v66_micro_stop=0.0;
int g_v66_micro_arch=V64_ARCH_NONE;
int g_v66_micro_score=0;
string g_v66_micro_wait_reason="";
'''

ARM_PENDING = r'''
void V64ArmPending(const int d,V64Features &f,const string why)
{
   if(d==0 || d!=InpV64AllowedDirection) return;
   if(g_v66_micro_pending)
   {
      V64PendingEvent("PENDING_REFRESH",d,"micro_entry_stage_active",g_v66_micro_stop,
                      (double)(TimeCurrent()-g_v66_micro_armed),(double)g_v66_micro_arch);
      return;
   }

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

MICRO_STAGE_FUNCTIONS = r'''
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
}

void V66ArmMicroPending(const int d,const int arch,const double micro_stop,const int score,
                        const double current_entry,const double current_risk,
                        const double spread_cash,const double ratio)
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
         V64PendingEvent("MICRO_ENTRY_REFRESH",d,"better_structural_stop_ttl_preserved",
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
   V64PendingEvent("MICRO_ENTRY_ARM",d,V64ArchName(arch),current_risk,spread_cash,ratio);
}

void V66MicroWaitEvent(const int d,const string reason,const double risk_cash,
                       const double spread_cash,const double ratio)
{
   if(reason==g_v66_micro_wait_reason) return;
   g_v66_micro_wait_reason=reason;
   V64PendingEvent("MICRO_ENTRY_WAIT",d,reason,risk_cash,spread_cash,ratio);
}

void V66TryMicroEntry()
{
   if(!g_v66_micro_pending || InpV64ScreenOnly) return;
   int d=g_v66_micro_dir;
   if(d!=InpV64AllowedDirection){V66ClearMicroPending("direction_mismatch");return;}

   ulong ticket=0;int pd=0;double pe=0,ps=0,pt=0;
   if(V64OwnedPosition(ticket,pd,pe,ps,pt)){V66ClearMicroPending("position_exists");return;}
   if(TimeCurrent()-g_v66_micro_armed>InpV66MicroEntryTTLMinutes*60)
   {V64PendingEvent("MICRO_ENTRY_EXPIRE",d,V64ArchName(g_v66_micro_arch),g_v66_micro_stop,0,0);V66ClearMicroPending("expired_first_micro_arm_ttl");return;}

   MqlTick tick;if(!SymbolInfoTick(_Symbol,tick)) return;
   double invalidation_px=(d>0 ? tick.bid : tick.ask);
   if((d>0 && invalidation_px<=g_v66_micro_stop) || (d<0 && invalidation_px>=g_v66_micro_stop))
   {V64PendingEvent("MICRO_ENTRY_INVALIDATE",d,"micro_structural_stop_breached",invalidation_px,g_v66_micro_stop,0);V66ClearMicroPending("micro_structural_stop_breached");return;}

   double entry=(d>0 ? tick.ask : tick.bid);
   double stop=0,tp=0,risk_cash=0,risk_pct=0,margin_cash=0,spread_points=0,spread_cash=0,ratio=0;string reject="";
   bool feasible=V64BuildMicroStopTarget(d,entry,g_v66_micro_stop,stop,tp,risk_cash,risk_pct,
                                         margin_cash,spread_points,spread_cash,ratio,reject);
   if(!feasible)
   {
      if(reject=="micro_risk_cash_cap")
      {V66MicroWaitEvent(d,"above_cash_zone",risk_cash,spread_cash,ratio);return;}
      if(reject=="micro_risk_too_tight" || reject=="broker_stop_too_close")
      {V66MicroWaitEvent(d,"near_stop_wait_rebound",risk_cash,spread_cash,ratio);return;}
      if(reject=="micro_risk_spread_ratio_low" || reject=="spread_cost_guard")
      {V66MicroWaitEvent(d,"spread_geometry_wait",risk_cash,spread_cash,ratio);return;}
      if(reject=="invalid_micro_structural_stop")
      {V64PendingEvent("MICRO_ENTRY_INVALIDATE",d,reject,entry,g_v66_micro_stop,risk_cash);V66ClearMicroPending(reject);return;}
      V64PendingEvent("MICRO_ENTRY_BLOCK",d,reject,risk_cash,spread_cash,ratio);
      V66ClearMicroPending(reject);
      return;
   }

   // Price is now naturally inside the cash-feasible zone for the original
   // structural stop. Revalidate the causal context at the actual entry tick.
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
   {V66MicroWaitEvent(d,"m5_context_wait",risk_cash,spread_cash,ratio);return;}

   g_v66_micro_wait_reason="";
   V64PendingEvent("MICRO_ENTRY_ZONE_TOUCH",d,V64ArchName(g_v66_micro_arch),risk_cash,spread_cash,ratio);
   V64LogDirectionalEval(cur,d,"post_bos_cash_zone_entry","",entry,stop,tp,risk_cash,risk_pct,
                         margin_cash,spread_points,spread_cash,1,"m1_micro_zone");

   string preflight_detail="";long preflight_retcode=0;
   if(!V64OrderPreflight(d,entry,stop,tp,preflight_detail,preflight_retcode))
   {V64PendingEvent("ORDER_PREFLIGHT",d,preflight_detail,entry,stop,(double)preflight_retcode);V66ClearMicroPending("preflight_block");return;}

   g_trade.SetExpertMagicNumber(InpV64Magic);g_trade.SetDeviationInPoints(50);g_trade.SetTypeFillingBySymbol(_Symbol);
   bool sent=(d>0 ? g_trade.Buy(InpV64FixedLot,_Symbol,0.0,stop,tp,"V66 CASHZONE L") : g_trade.Sell(InpV64FixedLot,_Symbol,0.0,stop,tp,"V66 CASHZONE S"));
   string send_detail=(sent ? "sent" : "rejected_"+IntegerToString((int)g_trade.ResultRetcode()));
   V64PendingEvent("REFINED_ENTRY",d,send_detail,entry,risk_cash,spread_cash);
   if(sent)
   {
      double shadow_entry=g_trade.ResultPrice();
      if(shadow_entry<=0.0) shadow_entry=entry;
      V64NoiseStart(d,shadow_entry);
      V64PendingEvent("NOISE_SHADOW",d,"actual_fill_anchor",shadow_entry,entry,shadow_entry-entry);
      V66ClearMicroPending("order_sent");
   }
   else V66ClearMicroPending("order_rejected");
}
'''

MANAGE_PENDING = r'''
void V64ManagePendingEntry()
{
   if(!g_v64_pending || InpV64ScreenOnly || g_v66_micro_pending) return;
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
   double m5_context_stop=0.0;
   if(!V64M5RefinedStop(d,entry,m5_context_stop))
   {V64PendingEvent("M5_CONTEXT_WAIT",d,"m5_structure_not_ready",entry,0,0);return;}

   string micro="";double micro_stop=0.0;
   if(!V64MicroTriggerConfirmed(d,g_v64_pending_arch,micro,micro_stop))
   {V64PendingEvent("REFINE_WAIT",d,micro,entry,0,0);return;}

   double stop=0,tp=0,risk_cash=0,risk_pct=0,margin_cash=0,spread_points=0,spread_cash=0,ratio=0;string reject="";
   bool feasible_now=V64BuildMicroStopTarget(d,entry,micro_stop,stop,tp,risk_cash,risk_pct,
                                              margin_cash,spread_points,spread_cash,ratio,reject);
   V64PendingEvent("MICRO_CANDIDATE",d,V64ArchName(g_v64_pending_arch),risk_cash,spread_cash,ratio);

   int arch=g_v64_pending_arch;
   int score=g_v64_pending_score;
   V66ArmMicroPending(d,arch,micro_stop,score,entry,risk_cash,spread_cash,ratio);
   // Stage one is complete. Stage-two first-arm TTL now owns the setup.
   g_v64_pending=false;g_v64_pending_dir=0;g_v64_pending_armed=0;g_v64_pending_arch=V64_ARCH_NONE;
   V66TryMicroEntry();
}
'''

ON_TICK = r'''
void OnTick()
{
   V64UpdateNoiseShadows();
   V64HardCashLossGuard();
   V64ManageProfitRatchet();
   V64MaybeSoftLossCut();
   V66TryMicroEntry();
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
    text = replace_once(text, '#property version   "65.00"', '#property version   "66.00"', "version")
    text = text.replace('V64 integrated bidirectional RR research - TESTER ONLY', 'V66 post-BOS cash-zone research - TESTER ONLY')
    text = replace_once(text, "input long   InpV64Magic = 650065;", "input long   InpV64Magic = 660066;", "magic")
    text = replace_once(text, "input int    InpV64PendingMaxMinutes = 240;", "input int    InpV64PendingMaxMinutes = 240;\ninput int    InpV66MicroEntryTTLMinutes = 30;", "micro-entry TTL")

    nroot = text.count(V65_ROOT)
    if nroot < 1:
        raise RuntimeError("V66 inherited V65 FILE_COMMON root missing")
    text = text.replace(V65_ROOT, V66_ROOT)
    if V65_ROOT in text:
        raise RuntimeError("V66 stale V65 FILE_COMMON root remains")

    anchor = 'string V64_NOISE_FILE=V64_ROOT+"\\\\V64_NOISE_SHADOW.csv";'
    text = replace_once(text, anchor, anchor + MICRO_STAGE_GLOBALS, "micro stage globals")
    text = replace_function(text, "void V64ArmPending", "void V64ManagePendingEntry", ARM_PENDING, "arm pending")
    text = replace_function(text, "void V64ManagePendingEntry", "void V64EvaluateBar", MICRO_STAGE_FUNCTIONS + "\n\n" + MANAGE_PENDING, "manage pending")
    text = replace_function(text, "void OnTick", "void OnTradeTransaction", ON_TICK, "OnTick")

    validate(text, allowed_direction)
    return text


def validate(text: str, allowed_direction: int) -> None:
    required = (
        V66_ROOT,
        "InpV64Magic = 660066",
        "InpV66MicroEntryTTLMinutes = 30",
        "InpV64FixedLot = 0.01",
        "InpV64MaxStopRiskCash = 1.25",
        "InpV64EmergencyLossCash = 1.20",
        "InpV64PrimaryTargetCash = 3.50",
        "InpV64MinRiskSpreadRatio = 4.0",
        f"InpV64AllowedDirection = {allowed_direction}",
        "MICRO_ENTRY_ARM",
        "MICRO_ENTRY_WAIT",
        "MICRO_ENTRY_ZONE_TOUCH",
        "MICRO_ENTRY_INVALIDATE",
        "MICRO_ENTRY_EXPIRE",
        "expired_first_micro_arm_ttl",
        "near_stop_wait_rebound",
        "above_cash_zone",
        "m1_micro_zone",
        "V66TryMicroEntry();",
        "V64NoiseStart(d,shadow_entry)",
        "IntegerToString(g_v64_noise[k].id)",
    )
    for token in required:
        if token not in text:
            raise RuntimeError(f"V66 generated source missing token: {token}")
    if V65_ROOT in text:
        raise RuntimeError("V66 generated source contains stale V65 root")
    if "LongToString(" in text:
        raise RuntimeError("V66 generated source reintroduced unsupported LongToString")

    manage = text[text.index("void V64ManagePendingEntry"):text.index("void V64EvaluateBar")]
    if manage.index("V64MicroTriggerConfirmed") > manage.index("V66ArmMicroPending"):
        raise RuntimeError("V66 micro trigger must precede stage-two arm")
    tick = text[text.index("void OnTick"):text.index("void OnTradeTransaction")]
    if tick.index("V66TryMicroEntry") > tick.index("V64ManagePendingEntry"):
        raise RuntimeError("V66 real-tick cash-zone stage must run before M1 stage-one management")


def build(output: Path, allowed_direction: int) -> str:
    text = transform(allowed_direction).replace("\n", "\r\n")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8", newline="")
    digest = sha256(output)
    print(f"V66_SOURCE_SHA256={digest}")
    print(f"V66_SOURCE_PATH={output}")
    print(f"V66_ALLOWED_DIRECTION={allowed_direction}")
    print(f"V66_FILE_COMMON_ROOT={V66_ROOT}")
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
