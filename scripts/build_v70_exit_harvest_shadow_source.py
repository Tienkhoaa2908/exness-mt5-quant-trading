#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT = HERE / "build_v69_confirm_separation_retest_source.py"
V69_ROOT = r"mt5_quant\\v69_confirm_separation_retest"
V70_ROOT = r"mt5_quant\\v70_exit_harvest_research"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


parent = load(PARENT, "v69_parent_for_v70_exit_shadow")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        raise RuntimeError(f"V70 {label} drifted expected=1 actual={n}")
    return text.replace(old, new, 1)


EXIT_SHADOW = r'''
struct V70ExitShadowState
{
   bool active;
   ulong ticket;
   int dir;
   datetime started;
   double entry;
   double max_pnl;
   double min_pnl;

   bool baseline_armed;
   bool baseline_triggered;

   bool early_armed;
   bool early_triggered;

   bool mid_armed;
   bool mid_triggered;

   bool tiered_armed;
   bool tiered_upgraded;
   bool tiered_triggered;
};

V70ExitShadowState g_v70_exit_shadow;

void V70ShadowEvent(const string event_name,const int d,const string detail,
                    const double v1,const double v2,const double v3)
{
   V64PendingEvent(event_name,d,detail,v1,v2,v3);
}

void V70ResetExitShadow()
{
   ZeroMemory(g_v70_exit_shadow);
}

void V70StartExitShadow(const ulong ticket,const int d,const double entry)
{
   V70ResetExitShadow();
   g_v70_exit_shadow.active=true;
   g_v70_exit_shadow.ticket=ticket;
   g_v70_exit_shadow.dir=d;
   g_v70_exit_shadow.started=TimeCurrent();
   g_v70_exit_shadow.entry=entry;
   g_v70_exit_shadow.max_pnl=0.0;
   g_v70_exit_shadow.min_pnl=0.0;
   V70ShadowEvent("V70_EXIT_SHADOW_START",d,"actual_position_lifetime",entry,(double)ticket,0.0);
}

void V70FinishExitShadow(const string detail)
{
   if(!g_v70_exit_shadow.active) return;
   double duration=(double)(TimeCurrent()-g_v70_exit_shadow.started);
   V70ShadowEvent("V70_EXIT_SHADOW_END",g_v70_exit_shadow.dir,detail,
                  g_v70_exit_shadow.max_pnl,g_v70_exit_shadow.min_pnl,duration);
   V70ResetExitShadow();
}

void V70MaybeTriggerPolicy(const string name,const int d,const double pnl,
                           const double floor_cash,bool &triggered)
{
   if(triggered || pnl>floor_cash+1e-9) return;
   triggered=true;
   V70ShadowEvent("V70_EXIT_POLICY_TRIGGER",d,name,pnl,floor_cash,g_v70_exit_shadow.max_pnl);
}

void V70UpdateExitHarvestShadow()
{
   ulong ticket=0;int d=0;double entry=0.0,sl=0.0,tp=0.0;
   bool owned=V64OwnedPosition(ticket,d,entry,sl,tp);

   if(!owned)
   {
      if(g_v70_exit_shadow.active) V70FinishExitShadow("actual_position_closed");
      return;
   }

   if(!g_v70_exit_shadow.active || g_v70_exit_shadow.ticket!=ticket)
   {
      if(g_v70_exit_shadow.active) V70FinishExitShadow("ticket_changed");
      V70StartExitShadow(ticket,d,entry);
   }

   MqlTick tick;
   if(!SymbolInfoTick(_Symbol,tick)) return;
   double exitp=(d>0 ? tick.bid : tick.ask);
   ENUM_ORDER_TYPE ot=(d>0 ? ORDER_TYPE_BUY : ORDER_TYPE_SELL);
   double pnl=0.0;
   if(!OrderCalcProfit(ot,_Symbol,InpV64FixedLot,entry,exitp,pnl)) return;

   g_v70_exit_shadow.max_pnl=MathMax(g_v70_exit_shadow.max_pnl,pnl);
   g_v70_exit_shadow.min_pnl=MathMin(g_v70_exit_shadow.min_pnl,pnl);

   // Policy 0: idealized current V61/V69 cash floor, used as a validation lane.
   if(!g_v70_exit_shadow.baseline_armed && pnl>=2.00-1e-9)
   {
      g_v70_exit_shadow.baseline_armed=true;
      V70ShadowEvent("V70_EXIT_POLICY_ARM",d,"BASELINE_200_100",pnl,1.00,g_v70_exit_shadow.max_pnl);
   }
   if(g_v70_exit_shadow.baseline_armed)
      V70MaybeTriggerPolicy("BASELINE_200_100",d,pnl,1.00,g_v70_exit_shadow.baseline_triggered);

   // Policy 1: early small positive floor. Research-only counterfactual.
   if(!g_v70_exit_shadow.early_armed && pnl>=1.00-1e-9)
   {
      g_v70_exit_shadow.early_armed=true;
      V70ShadowEvent("V70_EXIT_POLICY_ARM",d,"EARLY_100_025",pnl,0.25,g_v70_exit_shadow.max_pnl);
   }
   if(g_v70_exit_shadow.early_armed)
      V70MaybeTriggerPolicy("EARLY_100_025",d,pnl,0.25,g_v70_exit_shadow.early_triggered);

   // Policy 2: less aggressive early protection.
   if(!g_v70_exit_shadow.mid_armed && pnl>=1.50-1e-9)
   {
      g_v70_exit_shadow.mid_armed=true;
      V70ShadowEvent("V70_EXIT_POLICY_ARM",d,"MID_150_050",pnl,0.50,g_v70_exit_shadow.max_pnl);
   }
   if(g_v70_exit_shadow.mid_armed)
      V70MaybeTriggerPolicy("MID_150_050",d,pnl,0.50,g_v70_exit_shadow.mid_triggered);

   // Policy 3: add an early floor while preserving the inherited +2 -> +1 upgrade.
   if(!g_v70_exit_shadow.tiered_armed && pnl>=1.00-1e-9)
   {
      g_v70_exit_shadow.tiered_armed=true;
      V70ShadowEvent("V70_EXIT_POLICY_ARM",d,"TIERED_100_025_200_100",pnl,0.25,g_v70_exit_shadow.max_pnl);
   }
   if(g_v70_exit_shadow.tiered_armed && !g_v70_exit_shadow.tiered_upgraded && pnl>=2.00-1e-9)
   {
      g_v70_exit_shadow.tiered_upgraded=true;
      V70ShadowEvent("V70_EXIT_POLICY_UPGRADE",d,"TIERED_100_025_200_100",pnl,1.00,g_v70_exit_shadow.max_pnl);
   }
   if(g_v70_exit_shadow.tiered_armed)
   {
      double tiered_floor=(g_v70_exit_shadow.tiered_upgraded ? 1.00 : 0.25);
      V70MaybeTriggerPolicy("TIERED_100_025_200_100",d,pnl,tiered_floor,g_v70_exit_shadow.tiered_triggered);
   }
}
'''


def transform() -> str:
    text = parent.transform(1)
    text = replace_once(text, '#property version   "69.00"', '#property version   "70.00"', "version")
    text = replace_once(text, "input long   InpV64Magic = 690069;", "input long   InpV64Magic = 700070;", "magic")
    if text.count(V69_ROOT) < 1:
        raise RuntimeError("V70 inherited V69 FILE_COMMON root missing")
    text = text.replace(V69_ROOT, V70_ROOT)
    text = text.replace("V69 SEP RETEST L", "V70 EXIT SHADOW L")

    text = replace_once(text, "void OnTick()", EXIT_SHADOW + "\nvoid OnTick()", "exit shadow helper")
    text = replace_once(
        text,
        "   V64UpdateNoiseShadows();",
        "   V64UpdateNoiseShadows();\n   V70UpdateExitHarvestShadow();",
        "true in-position shadow tick hook",
    )

    required = (
        '#property version   "70.00"',
        "InpV64Magic = 700070",
        V70_ROOT,
        "InpV64AllowedDirection = 1",
        "InpV64FixedLot = 0.01",
        "InpV64PrimaryTargetCash = 3.50",
        "InpV64ProfitArmCash = 2.00",
        "InpV64ProfitLockCash = 1.00",
        "V69MinConfirmSeparationRiskCash = 1.30",
        "V69MinConfirmAgeSeconds = 30",
        "V70_EXIT_SHADOW_START",
        "V70_EXIT_SHADOW_END",
        "BASELINE_200_100",
        "EARLY_100_025",
        "MID_150_050",
        "TIERED_100_025_200_100",
    )
    for token in required:
        if token not in text:
            raise RuntimeError(f"V70 required token missing: {token}")
    if "InpV64AllowedDirection = -1" in text:
        raise RuntimeError("V70 exit-harvest research must remain LONG only")
    return text


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(transform(), encoding="utf-8", newline="\n")
    print(f"WROTE={args.output}")
    print(f"SHA256={sha256(args.output)}")
    print("V70_ENTRY_SEMANTICS_CHANGED=0")
    print("V70_REAL_EXIT_SEMANTICS_CHANGED=0")
    print("V70_EXIT_COUNTERFACTUAL_SHADOW_ONLY=1")
    print("V70_SHORT_ENABLED=0")
    print("REAL_MONEY_AUTHORIZED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
