#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
V53_BUILDER = HERE / "build_v53_trend_bos_demo_confirmation_source.py"
CANDIDATE = "v52_b4_or_b3_trend_bos"
V52R_ACCEPTED_ZIP_SHA256 = "4eddfce34c25b915e921a35e993f68f0a78644f3d6055bfa26180ba60ec9762c"
V53_ACCEPTED_ZIP_SHA256 = "602115bc6161e8947835c43033a1899637cc8a288f5192b2631acd6a6dd629db"


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
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"expected exactly one occurrence found={count}: {old[:160]!r}")
    return text.replace(old, new, 1)


def harden(text: str) -> str:
    text = text.replace("V53", "V54").replace("v53", "v54")
    text = text.replace("530053", "540054")
    text = text.replace("V54TrendBosDemoConfirmation.mq5", "V54ProductionReadiness.mq5")
    text = text.replace("v54_trend_bos_demo_confirmation_v1", "v54_production_readiness_hardening_v1")
    text = text.replace("V54 TREND+BOS DEMO", "V54 PRODUCTION READINESS")
    text = text.replace("V54 TREND+BOS DEMO | ", "V54 PRODUCTION READINESS | ")
    text = text.replace("mt5_quant\\\\v54\\\\V54_DEMO_REHEARSAL_STATUS.txt", "mt5_quant\\\\v54\\\\V54_PRODUCTION_READINESS_STATUS.txt")
    text = text.replace("mt5_quant\\\\v54\\\\V54_DEMO_REHEARSAL_FINAL.txt", "mt5_quant\\\\v54\\\\V54_PRODUCTION_READINESS_FINAL.txt")
    text = text.replace("mt5_quant\\\\v54\\\\V54_DEMO_REHEARSAL_EVENTS.csv", "mt5_quant\\\\v54\\\\V54_PRODUCTION_READINESS_EVENTS.csv")
    text = text.replace("mt5_quant\\\\v54\\\\V54_DEMO_REHEARSAL_TRANSACTIONS.csv", "mt5_quant\\\\v54\\\\V54_PRODUCTION_READINESS_TRANSACTIONS.csv")
    text = text.replace("schema=v54_trend_bos_demo_status_v1", "schema=v54_production_readiness_status_v1")

    text = replace_once(text, "input bool InpV54PushNotifications = true;", r'''input bool InpV54PushNotifications = true;

// Capital protection. V54 never scales above the inherited virtual volume.
input double InpV54MaxRiskPct = 0.50;
input double InpV54DailyLossPct = 2.00;
input double InpV54MaxDrawdownPct = 6.00;
input int InpV54MaxSpreadPoints = 150;
input int InpV54MaxTickAgeSeconds = 15;
input int InpV54MaxStrategyStateAgeSeconds = 30;
input int InpV54MaxConsecutiveRejects = 3;''')

    text = replace_once(text, "bool g_v54_close_pending=false;", r'''bool g_v54_close_pending=false;
bool g_v54_force_flatten=false;
int g_v54_consecutive_rejects=0;
string g_v54_entry_block_reason="";
datetime g_v54_last_strategy_tick_local=0;
int g_v54_risk_day_key=0;
double g_v54_day_start_equity=0.0;
double g_v54_peak_equity=0.0;
double g_v54_daily_loss_pct=0.0;
double g_v54_drawdown_pct=0.0;''')

    old_normalize = r'''double V54NormalizeVolume(const double requested)
{
   double vmin=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MIN);
   double vmax=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MAX);
   double step=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_STEP);
   if(step<=0.0) step=vmin;
   double v=MathMax(vmin,MathMin(vmax,requested));
   if(step>0.0) v=MathFloor(v/step+0.5)*step;
   return MathMax(vmin,MathMin(vmax,v));
}'''
    new_normalize = r'''double V54FloorVolume(const double requested)
{
   double vmin=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MIN);
   double vmax=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MAX);
   double step=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_STEP);
   if(vmin<=0.0 || vmax<=0.0 || requested<vmin) return 0.0;
   if(step<=0.0) step=vmin;
   double v=MathMin(vmax,requested);
   v=MathFloor((v+1e-12)/step)*step;
   if(v<vmin) return 0.0;
   return MathMin(vmax,v);
}

double V54RiskBoundVolume(const int direction,const double requested,const double entry,const double stop,double &risk_money,double &loss_per_lot)
{
   risk_money=0.0; loss_per_lot=0.0;
   if(direction==0 || requested<=0.0 || entry<=0.0 || stop<=0.0) return 0.0;
   if((direction>0 && stop>=entry) || (direction<0 && stop<=entry)) return 0.0;
   ENUM_ORDER_TYPE ot=(direction>0?ORDER_TYPE_BUY:ORDER_TYPE_SELL);
   double one_lot=0.0;
   ResetLastError();
   if(!OrderCalcProfit(ot,_Symbol,1.0,entry,stop,one_lot)) return 0.0;
   loss_per_lot=MathAbs(one_lot);
   double equity=AccountInfoDouble(ACCOUNT_EQUITY);
   if(loss_per_lot<=0.0 || equity<=0.0) return 0.0;
   double budget=equity*(InpV54MaxRiskPct/100.0);
   double cap=budget/loss_per_lot;
   double bounded=MathMin(requested,cap);
   double v=V54FloorVolume(bounded);
   if(v<=0.0) return 0.0;
   risk_money=v*loss_per_lot;
   return v;
}'''
    text = replace_once(text, old_normalize, new_normalize)

    helpers = r'''int V54DayKey()
{
   MqlDateTime dt; ZeroMemory(dt);
   datetime now=TimeTradeServer();
   if(now<=0) now=TimeCurrent();
   if(!TimeToStruct(now,dt)) return 0;
   return dt.year*10000+dt.mon*100+dt.day;
}

string V54RiskGlobal(const string suffix,const int day_key)
{
   return "V54."+IntegerToString((int)InpV54Magic)+"."+_Symbol+"."+IntegerToString(day_key)+"."+suffix;
}

void V54LogGuard(const string reason)
{
   if(reason==g_v54_entry_block_reason) return;
   g_v54_entry_block_reason=reason;
   V54AppendCsv(g_v54_events_file,TimeToString(TimeLocal(),TIME_DATE|TIME_MINUTES|TIME_SECONDS)+",GUARD,"+reason);
}

void V54RefreshRiskState()
{
   double equity=AccountInfoDouble(ACCOUNT_EQUITY);
   if(equity<=0.0){ g_v54_force_flatten=true; V54Halt("invalid_account_equity"); return; }
   int key=V54DayKey();
   if(key<=0){ g_v54_force_flatten=true; V54Halt("invalid_server_day"); return; }
   string start_key=V54RiskGlobal("day_start_equity",key);
   string peak_key=V54RiskGlobal("peak_equity",key);
   if(key!=g_v54_risk_day_key)
   {
      g_v54_risk_day_key=key;
      if(GlobalVariableCheck(start_key)) g_v54_day_start_equity=GlobalVariableGet(start_key);
      else { g_v54_day_start_equity=equity; GlobalVariableSet(start_key,equity); }
      if(GlobalVariableCheck(peak_key)) g_v54_peak_equity=GlobalVariableGet(peak_key);
      else { g_v54_peak_equity=equity; GlobalVariableSet(peak_key,equity); }
   }
   if(equity>g_v54_peak_equity)
   {
      g_v54_peak_equity=equity;
      GlobalVariableSet(peak_key,equity);
   }
   g_v54_daily_loss_pct=(g_v54_day_start_equity>0.0?100.0*(g_v54_day_start_equity-equity)/g_v54_day_start_equity:0.0);
   g_v54_drawdown_pct=(g_v54_peak_equity>0.0?100.0*(g_v54_peak_equity-equity)/g_v54_peak_equity:0.0);
   if(g_v54_daily_loss_pct>=InpV54DailyLossPct)
   {
      g_v54_force_flatten=true; V54Halt("daily_loss_limit");
   }
   if(g_v54_drawdown_pct>=InpV54MaxDrawdownPct)
   {
      g_v54_force_flatten=true; V54Halt("max_drawdown_limit");
   }
}

bool V54EntryHealthOk()
{
   if(g_v54_halted || g_v54_force_flatten) return false;
   if(!TerminalInfoInteger(TERMINAL_CONNECTED)){ V54LogGuard("terminal_disconnected"); return false; }
   if(g_v54_last_strategy_tick_local<=0 || (TimeLocal()-g_v54_last_strategy_tick_local)>InpV54MaxStrategyStateAgeSeconds)
   { V54LogGuard("stale_strategy_state"); return false; }
   MqlTick t;
   if(!SymbolInfoTick(_Symbol,t)){ V54LogGuard("tick_unavailable"); return false; }
   datetime server_now=TimeTradeServer(); if(server_now<=0) server_now=TimeCurrent();
   if(t.time<=0 || (server_now-t.time)>InpV54MaxTickAgeSeconds){ V54LogGuard("stale_tick"); return false; }
   if(_Point<=0.0){ V54LogGuard("invalid_point"); return false; }
   double spread_points=(t.ask-t.bid)/_Point;
   if(spread_points<0.0 || spread_points>InpV54MaxSpreadPoints){ V54LogGuard("spread_guard"); return false; }
   if(V54ForeignSymbolPositions()>0){ g_v54_force_flatten=true; V54Halt("foreign_symbol_position"); return false; }
   V54LogGuard("");
   return true;
}

bool V54OwnedProtectionOk(const ulong ticket)
{
   if(ticket==0 || !PositionSelectByTicket(ticket)) return false;
   double sl=PositionGetDouble(POSITION_SL);
   double tp=PositionGetDouble(POSITION_TP);
   return sl>0.0 && tp>0.0;
}

void V54OpenFromVirtual()
{'''
    text = replace_once(text, "void V54OpenFromVirtual()\n{", helpers)

    text = replace_once(text, r'''   double vv=B[ix].volume;
   double bv=V54NormalizeVolume(vv);
   double request_px=V54ExecutablePrice(B[ix].direction);
   g_v54_requests++;''', r'''   if(!V54EntryHealthOk()) return;
   double vv=B[ix].volume;
   double request_px=V54ExecutablePrice(B[ix].direction);
   double risk_money=0.0,loss_per_lot=0.0;
   double bv=V54RiskBoundVolume(B[ix].direction,vv,request_px,B[ix].stop,risk_money,loss_per_lot);
   if(bv<=0.0){ V54LogGuard("risk_cap_below_min_or_invalid_stop"); return; }
   g_v54_requests++;''')

    text = replace_once(text, r'''   if(!ok || !V54TradeRetcodeOk())
   {
      g_v54_open_pending=false;
      g_v54_rejects++;
      PrintFormat("V54 broker DEMO open rejected call=%d retcode=%u %s",(int)ok,g_v54_trade.ResultRetcode(),g_v54_trade.ResultRetcodeDescription());
   }''', r'''   if(!ok || !V54TradeRetcodeOk())
   {
      g_v54_open_pending=false;
      g_v54_rejects++; g_v54_consecutive_rejects++;
      PrintFormat("V54 broker DEMO open rejected call=%d retcode=%u %s",(int)ok,g_v54_trade.ResultRetcode(),g_v54_trade.ResultRetcodeDescription());
      if(g_v54_consecutive_rejects>=InpV54MaxConsecutiveRejects) V54Halt("broker_reject_limit");
   }
   else g_v54_consecutive_rejects=0;''')

    text = replace_once(text, r'''   if(!ok || !V54TradeRetcodeOk())
   {
      g_v54_close_pending=false;
      g_v54_rejects++;
      PrintFormat("V54 broker DEMO close rejected call=%d retcode=%u %s",(int)ok,g_v54_trade.ResultRetcode(),g_v54_trade.ResultRetcodeDescription());
   }''', r'''   if(!ok || !V54TradeRetcodeOk())
   {
      g_v54_close_pending=false;
      g_v54_rejects++; g_v54_consecutive_rejects++;
      PrintFormat("V54 broker DEMO close rejected call=%d retcode=%u %s",(int)ok,g_v54_trade.ResultRetcode(),g_v54_trade.ResultRetcodeDescription());
      if(g_v54_consecutive_rejects>=InpV54MaxConsecutiveRejects) V54Halt("broker_reject_limit");
   }
   else g_v54_consecutive_rejects=0;''')

    text = replace_once(text, r'''   int owned=V54OwnedPositionCount(ticket,broker_dir,broker_vol);
   if(owned>1){ g_v54_duplicate_events++; V54Halt("duplicate_owned_positions"); return; }''', r'''   int owned=V54OwnedPositionCount(ticket,broker_dir,broker_vol);
   if(owned>1){ g_v54_duplicate_events++; g_v54_force_flatten=true; V54Halt("duplicate_owned_positions"); return; }
   V54RefreshRiskState();
   if(V54ForeignSymbolPositions()>0)
   {
      g_v54_force_flatten=true; V54Halt("foreign_symbol_position_runtime");
      if(owned==1) V54CloseOwned(ticket,broker_dir,broker_vol);
      return;
   }
   if(!TerminalInfoInteger(TERMINAL_CONNECTED)){ V54LogGuard("terminal_disconnected"); return; }
   if(g_v54_last_strategy_tick_local<=0){ V54LogGuard("awaiting_fresh_strategy_tick"); return; }
   if(owned==1 && !V54OwnedProtectionOk(ticket)){ g_v54_force_flatten=true; V54Halt("owned_position_missing_sltp"); }
   if(g_v54_force_flatten)
   {
      if(owned==1) V54CloseOwned(ticket,broker_dir,broker_vol);
      return;
   }''')

    text = replace_once(text, r'''   V54ObserveMarketDay(tick.time);
   V54SyncBrokerWithVirtual();''', r'''   V54ObserveMarketDay(tick.time);
   g_v54_last_strategy_tick_local=TimeLocal();
   V54SyncBrokerWithVirtual();''')

    text = text.replace("V54MaybeFinalize();", "")

    auth_line = r'''   x+="real_money_authorized=0\r\n";'''
    telemetry = r'''   x+="real_money_authorized=0\r\n";
   x+="production_activation=DISABLED_DEMO_SAFE\r\n";
   x+="candidate=v52_b4_or_b3_trend_bos\r\n";
   x+="connected="+IntegerToString((int)TerminalInfoInteger(TERMINAL_CONNECTED))+"\r\n";
   x+="entry_block_reason="+g_v54_entry_block_reason+"\r\n";
   x+="force_flatten="+IntegerToString(g_v54_force_flatten?1:0)+"\r\n";
   x+="consecutive_rejects="+IntegerToString(g_v54_consecutive_rejects)+"\r\n";
   x+="day_start_equity="+DoubleToString(g_v54_day_start_equity,2)+"\r\n";
   x+="peak_equity="+DoubleToString(g_v54_peak_equity,2)+"\r\n";
   x+="daily_loss_pct="+DoubleToString(g_v54_daily_loss_pct,4)+"\r\n";
   x+="drawdown_pct="+DoubleToString(g_v54_drawdown_pct,4)+"\r\n";'''
    if text.count(auth_line) < 1:
        raise RuntimeError("V54 authorization telemetry marker missing")
    text = text.replace(auth_line, telemetry)

    text = replace_once(text, r'''   if((ENUM_ACCOUNT_TRADE_MODE)AccountInfoInteger(ACCOUNT_TRADE_MODE)!=ACCOUNT_TRADE_MODE_DEMO) return false;
   if(_Symbol!="XAUUSDm" || _Period!=PERIOD_M15) return false;''', r'''   if((ENUM_ACCOUNT_TRADE_MODE)AccountInfoInteger(ACCOUNT_TRADE_MODE)!=ACCOUNT_TRADE_MODE_DEMO) return false;
   if(_Symbol!="XAUUSDm" || _Period!=PERIOD_M15) return false;
   if(InpV54MaxRiskPct<=0.0 || InpV54MaxRiskPct>1.0) return false;
   if(InpV54DailyLossPct<=0.0 || InpV54MaxDrawdownPct<=0.0 || InpV54DailyLossPct>InpV54MaxDrawdownPct) return false;
   if(InpV54MaxSpreadPoints<=0 || InpV54MaxTickAgeSeconds<=0 || InpV54MaxStrategyStateAgeSeconds<=0 || InpV54MaxConsecutiveRejects<=0) return false;''')

    required = (CANDIDATE, "InpV54Magic = 540054", "ACCOUNT_TRADE_MODE_DEMO", "real_money_authorized=0", "production_activation=DISABLED_DEMO_SAFE", "InpV54MaxRiskPct = 0.50", "V54RiskBoundVolume", "OrderCalcProfit", "InpV54DailyLossPct = 2.00", "InpV54MaxDrawdownPct = 6.00", "InpV54MaxSpreadPoints = 150", "TERMINAL_CONNECTED", "stale_strategy_state", "stale_tick", "broker_reject_limit", "owned_position_missing_sltp", "duplicate_owned_positions", "V54SyncBrokerWithVirtual", "OnTradeTransaction", "SendNotification")
    for token in required:
        if token not in text:
            raise RuntimeError(f"V54 required token missing: {token}")
    forbidden = ("ACCOUNT_TRADE_MODE_REAL", "real_money_authorized=1", "production_activation=ENABLED", "Martingale", "martingale")
    for token in forbidden:
        if token in text:
            raise RuntimeError(f"V54 forbidden token present: {token}")
    return text


def build(source: Path, output: Path) -> str:
    v53 = load(V53_BUILDER, "v53_builder_for_v54")
    with tempfile.TemporaryDirectory(prefix="v54_prod_ready_") as td:
        staged = Path(td) / "V53Stage.mq5"
        v53.build(source, staged)
        text = staged.read_text(encoding="utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
        hardened = harden(text)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(hardened.replace("\n", "\r\n").encode("utf-8"))
    digest = sha256(output)
    print(f"V54_SOURCE_SHA256={digest}")
    print(f"V54_CANDIDATE={CANDIDATE}")
    print(f"V54_V52R_ACCEPTED_ZIP_SHA256={V52R_ACCEPTED_ZIP_SHA256}")
    print(f"V54_V53_ACCEPTED_ZIP_SHA256={V53_ACCEPTED_ZIP_SHA256}")
    print("V54_PRODUCTION_ACTIVATION=DISABLED_DEMO_SAFE")
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
