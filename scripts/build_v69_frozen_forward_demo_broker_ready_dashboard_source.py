#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT = HERE / "build_v69_frozen_forward_demo_dashboard_source.py"
PARENT_DASHBOARD_SHA256 = "5d00901309c949deafbd7c89164257ca2779fdbddc0e570a09cd82a8272875a0"
EXPERT_NAME = "V69FrozenForwardSmokeDashboardLong"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


parent = load(PARENT, "v69_dashboard_parent_for_broker_ready")


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def crlf_bytes(text: str) -> bytes:
    return text.replace("\n", "\r\n").encode("utf-8")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        raise RuntimeError(f"V69 broker dashboard {label} drifted expected=1 actual={n}")
    return text.replace(old, new, 1)


BROKER_HELPERS = r'''
// -----------------------------------------------------------------------------
// Broker capability smoke preflight. This NEVER sends an order. OrderCheck only
// validates the current DEMO account/symbol transport, volume, filling and margin.
// Strategy entry/exit logic remains byte-identical to the frozen parent.
// -----------------------------------------------------------------------------
datetime g_v69d_broker_checked_at=0;
bool g_v69d_broker_ready=false;
string g_v69d_broker_detail="not_checked";
double g_v69d_volume_min=0.0;
double g_v69d_volume_max=0.0;
double g_v69d_volume_step=0.0;
long g_v69d_trade_mode=0;
long g_v69d_filling_mode=0;
long g_v69d_ordercheck_retcode=0;

bool V69DBrokerCapabilityRaw(string &detail,double &vmin,double &vmax,double &vstep,
                             long &trade_mode,long &filling_mode,long &retcode)
{
   detail="";
   retcode=0;
   vmin=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MIN);
   vmax=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MAX);
   vstep=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_STEP);
   trade_mode=SymbolInfoInteger(_Symbol,SYMBOL_TRADE_MODE);
   filling_mode=SymbolInfoInteger(_Symbol,SYMBOL_FILLING_MODE);

   if((ENUM_ACCOUNT_TRADE_MODE)AccountInfoInteger(ACCOUNT_TRADE_MODE)!=ACCOUNT_TRADE_MODE_DEMO)
   { detail="account_not_demo"; return false; }
   if(!TerminalInfoInteger(TERMINAL_TRADE_ALLOWED))
   { detail="terminal_trade_disabled"; return false; }
   if(!MQLInfoInteger(MQL_TRADE_ALLOWED))
   { detail="ea_trade_disabled"; return false; }
   if(trade_mode!=SYMBOL_TRADE_MODE_FULL && trade_mode!=SYMBOL_TRADE_MODE_LONGONLY)
   { detail="symbol_long_not_allowed_"+IntegerToString((int)trade_mode); return false; }
   if(vmin<=0.0 || vmax<=0.0 || vstep<=0.0)
   { detail="volume_spec_invalid"; return false; }

   double lot=InpV64FixedLot;
   if(lot<vmin-1e-9 || lot>vmax+1e-9)
   { detail="lot_out_of_range"; return false; }
   double steps=(lot-vmin)/vstep;
   if(MathAbs(steps-MathRound(steps))>1e-6)
   { detail="lot_not_on_step"; return false; }

   MqlTick tick;
   if(!SymbolInfoTick(_Symbol,tick) || tick.ask<=0.0 || tick.bid<=0.0)
   { detail="tick_unavailable"; return false; }

   MqlTradeRequest req={};
   MqlTradeCheckResult chk={};
   req.action=TRADE_ACTION_DEAL;
   req.magic=InpV64Magic;
   req.symbol=_Symbol;
   req.volume=lot;
   req.type=ORDER_TYPE_BUY;
   req.price=tick.ask;
   req.deviation=50;
   req.type_time=ORDER_TIME_GTC;

   if((filling_mode & SYMBOL_FILLING_FOK)==SYMBOL_FILLING_FOK) req.type_filling=ORDER_FILLING_FOK;
   else if((filling_mode & SYMBOL_FILLING_IOC)==SYMBOL_FILLING_IOC) req.type_filling=ORDER_FILLING_IOC;
   else req.type_filling=ORDER_FILLING_RETURN;

   ResetLastError();
   if(!OrderCheck(req,chk))
   {
      retcode=(long)GetLastError();
      detail="ordercheck_call_failed_"+IntegerToString((int)retcode);
      return false;
   }
   retcode=(long)chk.retcode;
   if(chk.retcode!=0 && chk.retcode!=TRADE_RETCODE_DONE && chk.retcode!=TRADE_RETCODE_PLACED)
   {
      detail="ordercheck_"+IntegerToString((int)chk.retcode)+"_"+chk.comment;
      return false;
   }
   detail="READY";
   return true;
}

void V69DRefreshBrokerCapability()
{
   datetime now=TimeCurrent();
   if(g_v69d_broker_checked_at>0 && now-g_v69d_broker_checked_at<30) return;
   g_v69d_broker_checked_at=now;
   g_v69d_broker_ready=V69DBrokerCapabilityRaw(
      g_v69d_broker_detail,g_v69d_volume_min,g_v69d_volume_max,g_v69d_volume_step,
      g_v69d_trade_mode,g_v69d_filling_mode,g_v69d_ordercheck_retcode);
}
'''


def transform() -> str:
    base = parent.transform()
    base_sha = sha_bytes(crlf_bytes(base))
    if base_sha != PARENT_DASHBOARD_SHA256:
        raise RuntimeError(
            f"V69 parent dashboard drift expected={PARENT_DASHBOARD_SHA256} actual={base_sha}"
        )

    text = replace_once(
        base,
        "void V69DWriteHeartbeat()\n{",
        BROKER_HELPERS + "\n\nvoid V69DWriteHeartbeat()\n{\n   V69DRefreshBrokerCapability();",
        "broker helper insertion",
    )
    text = replace_once(
        text,
        '   FileWriteString(h,"mql_trade_allowed="+IntegerToString((int)MQLInfoInteger(MQL_TRADE_ALLOWED))+"\\r\\n");\n'
        '   FileWriteString(h,"real_money_authorized=0\\r\\n");',
        '   FileWriteString(h,"mql_trade_allowed="+IntegerToString((int)MQLInfoInteger(MQL_TRADE_ALLOWED))+"\\r\\n");\n'
        '   FileWriteString(h,"broker_ready="+IntegerToString((int)g_v69d_broker_ready)+"\\r\\n");\n'
        '   FileWriteString(h,"broker_detail="+g_v69d_broker_detail+"\\r\\n");\n'
        '   FileWriteString(h,"volume_min="+DoubleToString(g_v69d_volume_min,4)+"\\r\\n");\n'
        '   FileWriteString(h,"volume_max="+DoubleToString(g_v69d_volume_max,4)+"\\r\\n");\n'
        '   FileWriteString(h,"volume_step="+DoubleToString(g_v69d_volume_step,4)+"\\r\\n");\n'
        '   FileWriteString(h,"symbol_trade_mode="+IntegerToString((int)g_v69d_trade_mode)+"\\r\\n");\n'
        '   FileWriteString(h,"symbol_filling_mode="+IntegerToString((int)g_v69d_filling_mode)+"\\r\\n");\n'
        '   FileWriteString(h,"broker_ordercheck_retcode="+IntegerToString((int)g_v69d_ordercheck_retcode)+"\\r\\n");\n'
        '   FileWriteString(h,"real_money_authorized=0\\r\\n");',
        "heartbeat broker fields",
    )
    text = replace_once(
        text,
        "   V69DPanelBase();\n   int closed=0,wins=0,losses=0;double realized=0.0;",
        "   V69DPanelBase();\n   V69DRefreshBrokerCapability();\n   int closed=0,wins=0,losses=0;double realized=0.0;",
        "panel broker refresh",
    )
    text = replace_once(text, "OBJPROP_YSIZE,330", "OBJPROP_YSIZE,365", "panel height")
    text = replace_once(
        text,
        '   V69DLabel("14","Quick gate: runtime health + 2 closed trades | hard review cap: 48h",292,8,clrSilver);',
        '   string broker_line=(g_v69d_broker_ready ? "BROKER: READY" : "BROKER: BLOCKED")+\n'
        '      " | "+g_v69d_broker_detail+" | lot "+DoubleToString(InpV64FixedLot,2)+\n'
        '      " min "+DoubleToString(g_v69d_volume_min,2)+" step "+DoubleToString(g_v69d_volume_step,2)+\n'
        '      " | check "+IntegerToString((int)g_v69d_ordercheck_retcode);\n'
        '   V69DLabel("15",broker_line,292,8,(g_v69d_broker_ready?clrLime:clrTomato));\n'
        '   V69DLabel("14","Quick gate: broker READY + runtime health + 2 closed trades | hard review cap: 48h",320,8,clrSilver);',
        "panel broker row",
    )

    validate(text, base)
    return text


def validate(text: str, base: str) -> None:
    required = (
        "V69DBrokerCapabilityRaw",
        "V69DRefreshBrokerCapability",
        "SYMBOL_VOLUME_MIN",
        "SYMBOL_VOLUME_MAX",
        "SYMBOL_VOLUME_STEP",
        "SYMBOL_TRADE_MODE",
        "SYMBOL_FILLING_MODE",
        "OrderCheck(req,chk)",
        "broker_ready=",
        "broker_detail=",
        "broker_ordercheck_retcode=",
        "BROKER: READY",
        "BROKER: BLOCKED",
        "lot_out_of_range",
        "lot_not_on_step",
        "terminal_trade_disabled",
        "ea_trade_disabled",
    )
    for token in required:
        if token not in text:
            raise RuntimeError(f"V69 broker dashboard missing token: {token}")

    # The overlay may add one dry-run OrderCheck, but must never add an order send.
    for token in ("g_trade.Buy(", "g_trade.Sell(", "OrderSend(", "OrderSendAsync("):
        if text.count(token) != base.count(token):
            raise RuntimeError(f"V69 broker dashboard changed order-send token count: {token}")

    # Freeze the actual V69 entry/order state machine byte-for-byte.
    start = "void V66TryMicroEntry"
    end = "void V64ManagePendingEntry"
    if start not in text or end not in text or start not in base or end not in base:
        raise RuntimeError("V69 broker dashboard cannot locate frozen entry block")
    base_block = base[base.index(start):base.index(end)]
    text_block = text[text.index(start):text.index(end)]
    if text_block != base_block:
        raise RuntimeError("V69 broker dashboard changed frozen entry state machine")


def build(output: Path) -> str:
    text = transform().replace("\n", "\r\n")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8", newline="")
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    print(f"V69_BROKER_DASHBOARD_SOURCE_SHA256={digest}")
    print(f"V69_BROKER_DASHBOARD_SOURCE_PATH={output}")
    print(f"V69_BROKER_DASHBOARD_PARENT_SHA256={PARENT_DASHBOARD_SHA256}")
    print("V69_BROKER_PREFLIGHT_ORDER_SEND=0")
    print("V69_STRATEGY_CHANGED=0")
    return digest


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()
    build(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
