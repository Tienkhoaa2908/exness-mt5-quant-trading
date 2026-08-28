#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
V54_BUILDER = HERE / "build_v54_production_readiness_source.py"
CANDIDATE = "v52_b4_or_b3_trend_bos"
REAL_ARM_CODE = "V55_REAL_ARMED"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def replace_once(text: str, old: str, new: str) -> str:
    n = text.count(old)
    if n != 1:
        raise RuntimeError(f"expected exactly one occurrence found={n}: {old[:180]!r}")
    return text.replace(old, new, 1)


def transform(text: str) -> str:
    # V55 is a thin production envelope on top of V54. Alpha and execution mapping
    # stay inherited; this stage only removes account-type coupling and adds
    # account/broker-aware preflight semantics.
    text = text.replace("V54", "V55").replace("v54", "v55")
    text = text.replace("540054", "550055")
    text = text.replace("V55ProductionReadiness.mq5", "V55AccountAgnosticProduction.mq5")
    text = text.replace("v55_production_readiness_hardening_v1", "v55_account_agnostic_production_v1")
    text = text.replace("schema=v55_production_readiness_status_v1", "schema=v55_account_agnostic_status_v1")
    text = text.replace("V55 PRODUCTION READINESS | ", "V55 ACCOUNT-AGNOSTIC PROD | ")

    text = replace_once(
        text,
        "input bool InpV55PushNotifications = true;",
        r'''input bool InpV55PushNotifications = true;

// Same EA binary is valid on DEMO and REAL. REAL can observe/reconcile by default,
// but opening new real-money risk requires both explicit inputs below.
input bool InpV55AllowRealAccount = false;
input string InpV55RealArmCode = "";
input double InpV55MaxMarginUsagePct = 80.0;''',
    )

    text = replace_once(
        text,
        "bool g_v55_force_flatten=false;",
        r'''bool g_v55_force_flatten=false;
long g_v55_init_login=0;
ENUM_ACCOUNT_TRADE_MODE g_v55_init_account_mode=ACCOUNT_TRADE_MODE_DEMO;
bool g_v55_real_entry_epoch_ready=false;''',
    )

    account_helpers = r'''string V55AccountModeName()
{
   ENUM_ACCOUNT_TRADE_MODE m=(ENUM_ACCOUNT_TRADE_MODE)AccountInfoInteger(ACCOUNT_TRADE_MODE);
   if(m==ACCOUNT_TRADE_MODE_DEMO) return "DEMO";
   if(m==ACCOUNT_TRADE_MODE_REAL) return "REAL";
   if(m==ACCOUNT_TRADE_MODE_CONTEST) return "CONTEST";
   return "UNKNOWN";
}

bool V55SupportedAccountMode()
{
   ENUM_ACCOUNT_TRADE_MODE m=(ENUM_ACCOUNT_TRADE_MODE)AccountInfoInteger(ACCOUNT_TRADE_MODE);
   return m==ACCOUNT_TRADE_MODE_DEMO || m==ACCOUNT_TRADE_MODE_REAL;
}

bool V55RealExecutionAuthorized()
{
   return (ENUM_ACCOUNT_TRADE_MODE)AccountInfoInteger(ACCOUNT_TRADE_MODE)==ACCOUNT_TRADE_MODE_REAL
      && InpV55AllowRealAccount
      && InpV55RealArmCode=="V55_REAL_ARMED";
}

bool V55NewRiskAuthorized()
{
   ENUM_ACCOUNT_TRADE_MODE m=(ENUM_ACCOUNT_TRADE_MODE)AccountInfoInteger(ACCOUNT_TRADE_MODE);
   if(m==ACCOUNT_TRADE_MODE_DEMO) return true;
   if(m==ACCOUNT_TRADE_MODE_REAL) return V55RealExecutionAuthorized();
   return false;
}

string V55ActivationMode()
{
   ENUM_ACCOUNT_TRADE_MODE m=(ENUM_ACCOUNT_TRADE_MODE)AccountInfoInteger(ACCOUNT_TRADE_MODE);
   if(m==ACCOUNT_TRADE_MODE_DEMO) return "DEMO_ACTIVE";
   if(m==ACCOUNT_TRADE_MODE_REAL && V55RealExecutionAuthorized()) return "REAL_ARMED";
   if(m==ACCOUNT_TRADE_MODE_REAL) return "REAL_OBSERVE_ONLY";
   return "BLOCKED_ACCOUNT_MODE";
}

bool V55AccountIdentityStable()
{
   return g_v55_init_login==(long)AccountInfoInteger(ACCOUNT_LOGIN)
      && g_v55_init_account_mode==(ENUM_ACCOUNT_TRADE_MODE)AccountInfoInteger(ACCOUNT_TRADE_MODE);
}

bool V55StopsGeometryOk(const int direction,const double entry,const double sl,const double tp)
{
   if(direction==0 || entry<=0.0 || sl<=0.0 || tp<=0.0 || _Point<=0.0) return false;
   if(direction>0 && !(sl<entry && tp>entry)) return false;
   if(direction<0 && !(sl>entry && tp<entry)) return false;
   long stops=SymbolInfoInteger(_Symbol,SYMBOL_TRADE_STOPS_LEVEL);
   if(stops<0) return false;
   double min_dist=(double)stops*_Point;
   if(MathAbs(entry-sl)+1e-12<min_dist) return false;
   if(MathAbs(tp-entry)+1e-12<min_dist) return false;
   return true;
}

'''
    text = replace_once(text, "int V55DayKey()\n{", account_helpers + "int V55DayKey()\n{")

    old_risk_key = r'''string V55RiskGlobal(const string suffix,const int day_key)
{
   return "V55."+IntegerToString((int)InpV55Magic)+"."+_Symbol+"."+IntegerToString(day_key)+"."+suffix;
}'''
    new_risk_key = r'''string V55RiskGlobal(const string suffix,const int day_key)
{
   return "V55."+IntegerToString((long)AccountInfoInteger(ACCOUNT_LOGIN))+"."+
      IntegerToString((int)InpV55Magic)+"."+_Symbol+"."+IntegerToString(day_key)+"."+suffix;
}'''
    text = replace_once(text, old_risk_key, new_risk_key)

    # Daily loss resets on the broker/server day. Max drawdown must not reset daily:
    # day_key=0 creates one persistent, account+magic+symbol scoped high-water mark.
    text = replace_once(
        text,
        '   string peak_key=V55RiskGlobal("peak_equity",key);',
        '   string peak_key=V55RiskGlobal("peak_equity",0);',
    )

    text = replace_once(
        text,
        r'''   risk_money=v*loss_per_lot;
   return v;''',
        r'''   double margin=0.0;
   ResetLastError();
   if(!OrderCalcMargin(ot,_Symbol,v,entry,margin)) return 0.0;
   double free_margin=AccountInfoDouble(ACCOUNT_MARGIN_FREE);
   if(margin<0.0 || free_margin<=0.0) return 0.0;
   if(margin>free_margin*(InpV55MaxMarginUsagePct/100.0)) return 0.0;
   risk_money=v*loss_per_lot;
   return v;''',
    )

    text = replace_once(
        text,
        r'''   if(g_v55_halted || g_v55_force_flatten) return false;''',
        r'''   if(g_v55_halted || g_v55_force_flatten) return false;
   if(!V55NewRiskAuthorized()){ V55LogGuard("new_risk_not_authorized"); return false; }''',
    )

    text = replace_once(
        text,
        r'''   double request_px=V55ExecutablePrice(B[ix].direction);
   double risk_money=0.0,loss_per_lot=0.0;''',
        r'''   double request_px=V55ExecutablePrice(B[ix].direction);
   if(!V55StopsGeometryOk(B[ix].direction,request_px,B[ix].stop,B[ix].tp))
   { V55LogGuard("broker_stop_geometry_guard"); return; }
   double risk_money=0.0,loss_per_lot=0.0;''',
    )

    text = replace_once(
        text,
        r'''   if((ENUM_ACCOUNT_TRADE_MODE)AccountInfoInteger(ACCOUNT_TRADE_MODE)!=ACCOUNT_TRADE_MODE_DEMO){ V55Halt("non_demo_account"); return; }''',
        r'''   if(!V55AccountIdentityStable()){ g_v55_force_flatten=true; V55Halt("account_identity_changed_restart_required"); return; }
   if(!V55SupportedAccountMode()){ g_v55_force_flatten=true; V55Halt("unsupported_account_mode"); return; }''',
    )

    # A REAL startup must observe a clean flat epoch before its first new broker entry.
    # This prevents a virtual position inherited from a DEMO/trial session from being
    # materialized late as fresh real-money exposure. An already-owned REAL position is
    # still reconciled normally after restart; the latch only blocks owned==0 entry.
    text = replace_once(
        text,
        r'''   if(B[ix].open)
   {
      if(owned==0) V55OpenFromVirtual();''',
        r'''   if(g_v55_init_account_mode==ACCOUNT_TRADE_MODE_REAL && !g_v55_real_entry_epoch_ready)
   {
      if(owned==0 && !B[ix].open)
      {
         g_v55_real_entry_epoch_ready=true;
         V55LogGuard("");
         V55AppendCsv(g_v55_events_file,TimeToString(TimeLocal(),TIME_DATE|TIME_MINUTES|TIME_SECONDS)+",REAL_ENTRY_EPOCH_READY,flat_observed");
      }
      else if(owned==0 && B[ix].open)
      {
         V55LogGuard("real_activation_waiting_for_flat");
         return;
      }
   }

   if(B[ix].open)
   {
      if(owned==0) V55OpenFromVirtual();''',
    )

    text = replace_once(
        text,
        r'''   if((ENUM_ACCOUNT_TRADE_MODE)AccountInfoInteger(ACCOUNT_TRADE_MODE)!=ACCOUNT_TRADE_MODE_DEMO) return false;
   if(_Symbol!="XAUUSDm" || _Period!=PERIOD_M15) return false;''',
        r'''   if(!V55SupportedAccountMode()) return false;
   if(_Symbol!="XAUUSDm" || _Period!=PERIOD_M15) return false;
   if(InpV55MaxMarginUsagePct<=0.0 || InpV55MaxMarginUsagePct>95.0) return false;''',
    )

    # Pin account identity at initialization. Changing login or DEMO/REAL mode while
    # the EA is running requires a clean restart and cannot open new risk.
    text = replace_once(
        text,
        r'''   g_v55_trade.SetExpertMagicNumber((ulong)InpV55Magic);''',
        r'''   g_v55_init_login=(long)AccountInfoInteger(ACCOUNT_LOGIN);
   g_v55_init_account_mode=(ENUM_ACCOUNT_TRADE_MODE)AccountInfoInteger(ACCOUNT_TRADE_MODE);
   g_v55_real_entry_epoch_ready=(g_v55_init_account_mode==ACCOUNT_TRADE_MODE_DEMO);
   if(g_v55_init_account_mode==ACCOUNT_TRADE_MODE_REAL && !V55RealExecutionAuthorized()) g_v55_accept_new=false;
   g_v55_trade.SetExpertMagicNumber((ulong)InpV55Magic);''',
    )

    old_mode = r'''   x+="account_mode="+string((ENUM_ACCOUNT_TRADE_MODE)AccountInfoInteger(ACCOUNT_TRADE_MODE)==ACCOUNT_TRADE_MODE_DEMO?"DEMO":"NON_DEMO")+"\r\n";'''
    text = replace_once(text, old_mode, r'''   x+="account_mode="+V55AccountModeName()+"\r\n";''')

    text = text.replace(
        r'''   x+="real_money_authorized=0\r\n";''',
        r'''   x+="real_money_authorized="+IntegerToString(V55RealExecutionAuthorized()?1:0)+"\r\n";''',
    )
    text = text.replace(
        r'''   x+="production_activation=DISABLED_DEMO_SAFE\r\n";''',
        r'''   x+="production_activation="+V55ActivationMode()+"\r\n";
   x+="real_entry_epoch_ready="+IntegerToString(g_v55_real_entry_epoch_ready?1:0)+"\r\n";''',
    )

    telemetry_marker = r'''   x+="candidate=v52_b4_or_b3_trend_bos\r\n";'''
    telemetry_extra = telemetry_marker + r'''
   x+="account_leverage="+IntegerToString((long)AccountInfoInteger(ACCOUNT_LEVERAGE))+"\r\n";
   x+="symbol_volume_min="+DoubleToString(SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MIN),8)+"\r\n";
   x+="symbol_volume_max="+DoubleToString(SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MAX),8)+"\r\n";
   x+="symbol_volume_step="+DoubleToString(SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_STEP),8)+"\r\n";
   x+="symbol_stops_level="+IntegerToString((long)SymbolInfoInteger(_Symbol,SYMBOL_TRADE_STOPS_LEVEL))+"\r\n";
   x+="symbol_freeze_level="+IntegerToString((long)SymbolInfoInteger(_Symbol,SYMBOL_TRADE_FREEZE_LEVEL))+"\r\n";'''
    if telemetry_marker not in text:
        raise RuntimeError("V55 candidate telemetry marker missing")
    text = text.replace(telemetry_marker, telemetry_extra)

    text = text.replace("broker DEMO open rejected", "broker open rejected")
    text = text.replace("broker DEMO close rejected", "broker close rejected")
    text = text.replace(" DEMO OPEN confirmed ", " OPEN confirmed ")
    text = text.replace(" DEMO CLOSE confirmed ", " CLOSE confirmed ")
    text = text.replace(
        'V55Notify("V55 START DEMO XAUUSDm M15 breadth4");',
        'V55Notify("V55 START "+V55ActivationMode()+" XAUUSDm M15 trend_bos");',
    )

    required = (
        CANDIDATE,
        "InpV55Magic = 550055",
        "InpV55AllowRealAccount = false",
        'InpV55RealArmCode = ""',
        'InpV55RealArmCode=="V55_REAL_ARMED"',
        "ACCOUNT_TRADE_MODE_DEMO",
        "ACCOUNT_TRADE_MODE_REAL",
        "V55NewRiskAuthorized",
        "REAL_OBSERVE_ONLY",
        "REAL_ARMED",
        "account_identity_changed_restart_required",
        "g_v55_real_entry_epoch_ready",
        "real_activation_waiting_for_flat",
        "REAL_ENTRY_EPOCH_READY",
        "real_entry_epoch_ready=",
        "V55StopsGeometryOk",
        "SYMBOL_TRADE_STOPS_LEVEL",
        "OrderCalcProfit",
        "OrderCalcMargin",
        "ACCOUNT_MARGIN_FREE",
        "InpV55MaxMarginUsagePct = 80.0",
        "V55RiskGlobal",
        'V55RiskGlobal("peak_equity",0)',
        "ACCOUNT_LOGIN",
        "V55SyncBrokerWithVirtual",
        "OnTradeTransaction",
        "SendNotification",
    )
    for token in required:
        if token not in text:
            raise RuntimeError(f"V55 required token missing: {token}")

    forbidden = (
        "non_demo_account",
        "production_activation=DISABLED_DEMO_SAFE",
        "Martingale",
        "martingale",
    )
    for token in forbidden:
        if token in text:
            raise RuntimeError(f"V55 forbidden token present: {token}")

    return text


def build(source: Path, output: Path) -> str:
    v54 = load(V54_BUILDER, "v54_builder_for_v55")
    with tempfile.TemporaryDirectory(prefix="v55_account_agnostic_") as td:
        staged = Path(td) / "V54Stage.mq5"
        v54.build(source, staged)
        text = staged.read_text(encoding="utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
        final = transform(text)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(final.replace("\n", "\r\n").encode("utf-8"))
    digest = sha256(output)
    print(f"V55_SOURCE_SHA256={digest}")
    print(f"V55_CANDIDATE={CANDIDATE}")
    print("V55_ACCOUNT_MODEL=DEMO_AND_REAL_SAME_BINARY")
    print("V55_REAL_DEFAULT=OBSERVE_ONLY")
    print(f"V55_REAL_ARM_CODE={REAL_ARM_CODE}")
    return digest


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True)
    ap.add_argument("--output", required=True)
    ns = ap.parse_args()
    build(Path(ns.source), Path(ns.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
