#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

SOURCE = r'''#property strict
#property version   "69.91"
#property description "V69 DEMO-only actual execution probe. Opens and immediately closes one 0.01 XAUUSDm BUY using isolated magic."

#include <Trade/Trade.mqh>

const bool V69ProbeRealMoneyAuthorized=false;
const long V69ProbeMagic=699901;
const double V69ProbeLot=0.01;
const string V69ProbeRoot="mt5_quant\\v69_demo_execution_probe";
const string V69ProbeFile="mt5_quant\\v69_demo_execution_probe\\V69_DEMO_EXECUTION_PROBE.txt";

CTrade g_probe;
int g_state=0;
ulong g_ticket=0;
datetime g_started=0;
datetime g_opened_at=0;
long g_check_last_error=0;
long g_check_retcode=0;
string g_check_comment="";
long g_open_retcode=0;
string g_open_comment="";
long g_close_retcode=0;
string g_close_comment="";
double g_open_price=0.0;
double g_close_price=0.0;

void V69ProbeWrite(const string state,const string detail)
{
   FolderCreate(V69ProbeRoot,FILE_COMMON);
   int h=FileOpen(V69ProbeFile,FILE_WRITE|FILE_TXT|FILE_ANSI|FILE_COMMON);
   if(h==INVALID_HANDLE) return;
   FileWriteString(h,"state="+state+"\r\n");
   FileWriteString(h,"detail="+detail+"\r\n");
   FileWriteString(h,"symbol="+_Symbol+"\r\n");
   FileWriteString(h,"period="+EnumToString((ENUM_TIMEFRAMES)_Period)+"\r\n");
   FileWriteString(h,"demo_only=1\r\n");
   FileWriteString(h,"real_money_authorized=0\r\n");
   FileWriteString(h,"lot="+DoubleToString(V69ProbeLot,2)+"\r\n");
   FileWriteString(h,"magic="+IntegerToString((int)V69ProbeMagic)+"\r\n");
   FileWriteString(h,"balance="+DoubleToString(AccountInfoDouble(ACCOUNT_BALANCE),2)+"\r\n");
   FileWriteString(h,"equity="+DoubleToString(AccountInfoDouble(ACCOUNT_EQUITY),2)+"\r\n");
   FileWriteString(h,"free_margin="+DoubleToString(AccountInfoDouble(ACCOUNT_MARGIN_FREE),2)+"\r\n");
   FileWriteString(h,"check_last_error="+IntegerToString((int)g_check_last_error)+"\r\n");
   FileWriteString(h,"check_retcode="+IntegerToString((int)g_check_retcode)+"\r\n");
   FileWriteString(h,"check_comment="+g_check_comment+"\r\n");
   FileWriteString(h,"open_retcode="+IntegerToString((int)g_open_retcode)+"\r\n");
   FileWriteString(h,"open_comment="+g_open_comment+"\r\n");
   FileWriteString(h,"close_retcode="+IntegerToString((int)g_close_retcode)+"\r\n");
   FileWriteString(h,"close_comment="+g_close_comment+"\r\n");
   FileWriteString(h,"open_price="+DoubleToString(g_open_price,_Digits)+"\r\n");
   FileWriteString(h,"close_price="+DoubleToString(g_close_price,_Digits)+"\r\n");
   FileWriteString(h,"ticket="+IntegerToString((int)g_ticket)+"\r\n");
   FileWriteString(h,"started="+TimeToString(g_started,TIME_DATE|TIME_SECONDS)+"\r\n");
   FileWriteString(h,"updated="+TimeToString(TimeCurrent(),TIME_DATE|TIME_SECONDS)+"\r\n");
   FileClose(h);
}

bool V69ProbeFindPosition(ulong &ticket)
{
   for(int i=PositionsTotal()-1;i>=0;i--)
   {
      ulong t=PositionGetTicket(i);
      if(t==0 || !PositionSelectByTicket(t)) continue;
      if(PositionGetString(POSITION_SYMBOL)!=_Symbol) continue;
      if((long)PositionGetInteger(POSITION_MAGIC)!=V69ProbeMagic) continue;
      ticket=t;
      return true;
   }
   ticket=0;
   return false;
}

bool V69ProbePreflight(string &detail)
{
   detail="";
   if((ENUM_ACCOUNT_TRADE_MODE)AccountInfoInteger(ACCOUNT_TRADE_MODE)!=ACCOUNT_TRADE_MODE_DEMO)
   { detail="account_not_demo"; return false; }
   if(!TerminalInfoInteger(TERMINAL_CONNECTED))
   { detail="terminal_not_connected"; return false; }
   if(!AccountInfoInteger(ACCOUNT_TRADE_ALLOWED) || !AccountInfoInteger(ACCOUNT_TRADE_EXPERT))
   { detail="account_trade_not_allowed"; return false; }
   if(!TerminalInfoInteger(TERMINAL_TRADE_ALLOWED) || !MQLInfoInteger(MQL_TRADE_ALLOWED))
   { detail="terminal_or_ea_trade_not_allowed"; return false; }
   if(_Symbol!="XAUUSDm")
   { detail="wrong_symbol_"+_Symbol; return false; }

   double vmin=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MIN);
   double vmax=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MAX);
   double vstep=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_STEP);
   if(vmin<=0.0 || vmax<=0.0 || vstep<=0.0)
   { detail="invalid_volume_contract"; return false; }
   if(V69ProbeLot<vmin-1e-9 || V69ProbeLot>vmax+1e-9)
   { detail="lot_out_of_range"; return false; }
   double steps=(V69ProbeLot-vmin)/vstep;
   if(MathAbs(steps-MathRound(steps))>1e-6)
   { detail="lot_not_on_step"; return false; }

   MqlTick tick;
   if(!SymbolInfoTick(_Symbol,tick) || tick.ask<=0.0 || tick.bid<=0.0)
   { detail="tick_unavailable"; return false; }

   long filling=SymbolInfoInteger(_Symbol,SYMBOL_FILLING_MODE);
   long execution=SymbolInfoInteger(_Symbol,SYMBOL_TRADE_EXEMODE);
   MqlTradeRequest req={};
   MqlTradeCheckResult chk={};
   req.action=TRADE_ACTION_DEAL;
   req.magic=V69ProbeMagic;
   req.symbol=_Symbol;
   req.volume=V69ProbeLot;
   req.type=ORDER_TYPE_BUY;
   if(execution==SYMBOL_TRADE_EXECUTION_REQUEST || execution==SYMBOL_TRADE_EXECUTION_INSTANT)
   {
      req.price=tick.ask;
      req.deviation=50;
   }
   if((filling & SYMBOL_FILLING_FOK)==SYMBOL_FILLING_FOK) req.type_filling=ORDER_FILLING_FOK;
   else if((filling & SYMBOL_FILLING_IOC)==SYMBOL_FILLING_IOC) req.type_filling=ORDER_FILLING_IOC;
   else if(execution!=SYMBOL_TRADE_EXECUTION_MARKET) req.type_filling=ORDER_FILLING_RETURN;
   else { detail="unsupported_filling"; return false; }

   ResetLastError();
   bool ok=OrderCheck(req,chk);
   g_check_last_error=(long)GetLastError();
   g_check_retcode=(long)chk.retcode;
   g_check_comment=chk.comment;
   if(!ok)
   {
      detail="ordercheck_failed_last_"+IntegerToString((int)g_check_last_error)+
             "_srv_"+IntegerToString((int)g_check_retcode)+"_"+g_check_comment;
      return false;
   }
   detail="READY";
   return true;
}

void V69ProbeFinish(const string state,const string detail,const int terminal_code)
{
   g_state=(state=="PASS" ? 2 : -1);
   V69ProbeWrite(state,detail);
   Print("V69 DEMO EXECUTION PROBE ",state,": ",detail,
         " open_retcode=",g_open_retcode," close_retcode=",g_close_retcode," ticket=",g_ticket);
   bool accepted=TerminalClose(terminal_code);
   Print("V69 DEMO EXECUTION PROBE TerminalClose accepted=",accepted);
   return;
}

void V69ProbeFail(const string detail){ V69ProbeFinish("FAIL",detail,92); }
void V69ProbePass(){ V69ProbeFinish("PASS","actual_demo_open_and_close_verified",0); }

void V69ProbeProcess()
{
   if(g_state==2 || g_state<0) return;
   if((ENUM_ACCOUNT_TRADE_MODE)AccountInfoInteger(ACCOUNT_TRADE_MODE)!=ACCOUNT_TRADE_MODE_DEMO)
   { V69ProbeFail("demo_guard_failed"); return; }

   if(g_state==0)
   {
      string pre="";
      if(!V69ProbePreflight(pre))
      { V69ProbeFail(pre); return; }

      ulong existing=0;
      if(V69ProbeFindPosition(existing))
      { V69ProbeFail("existing_probe_position_detected"); return; }

      g_probe.SetExpertMagicNumber(V69ProbeMagic);
      g_probe.SetTypeFillingBySymbol(_Symbol);
      g_probe.SetAsyncMode(false);
      ResetLastError();
      bool opened=g_probe.Buy(V69ProbeLot,_Symbol,0.0,0.0,0.0,"V69 DEMO EXEC PROBE");
      g_open_retcode=(long)g_probe.ResultRetcode();
      g_open_comment=g_probe.ResultRetcodeDescription();
      g_open_price=g_probe.ResultPrice();
      if(!opened)
      {
         V69ProbeFail("buy_failed_ret_"+IntegerToString((int)g_open_retcode)+"_"+g_open_comment);
         return;
      }
      g_opened_at=TimeCurrent();
      g_state=1;
      V69ProbeWrite("OPENED","waiting_immediate_close");
   }

   if(g_state==1)
   {
      ulong ticket=0;
      if(!V69ProbeFindPosition(ticket))
      {
         if(TimeCurrent()-g_opened_at>10)
            V69ProbeFail("opened_but_probe_position_not_found");
         return;
      }
      g_ticket=ticket;
      g_probe.SetExpertMagicNumber(V69ProbeMagic);
      g_probe.SetTypeFillingBySymbol(_Symbol);
      g_probe.SetAsyncMode(false);
      bool closed=g_probe.PositionClose(ticket,50);
      g_close_retcode=(long)g_probe.ResultRetcode();
      g_close_comment=g_probe.ResultRetcodeDescription();
      g_close_price=g_probe.ResultPrice();
      if(!closed)
      {
         if(TimeCurrent()-g_opened_at>30)
            V69ProbeFail("close_failed_ret_"+IntegerToString((int)g_close_retcode)+"_"+g_close_comment);
         else
            V69ProbeWrite("CLOSE_RETRY","ret_"+IntegerToString((int)g_close_retcode)+"_"+g_close_comment);
         return;
      }
      ulong remaining=0;
      if(V69ProbeFindPosition(remaining))
      {
         V69ProbeWrite("CLOSE_RETRY","position_still_present_after_close");
         return;
      }
      V69ProbePass();
      return;
   }
}

int OnInit()
{
   g_started=TimeCurrent();
   if((ENUM_ACCOUNT_TRADE_MODE)AccountInfoInteger(ACCOUNT_TRADE_MODE)!=ACCOUNT_TRADE_MODE_DEMO)
   {
      V69ProbeWrite("FAIL","DEMO_ACCOUNT_REQUIRED");
      TerminalClose(93);
      return INIT_FAILED;
   }
   if(_Symbol!="XAUUSDm")
   {
      V69ProbeWrite("FAIL","XAUUSDm_REQUIRED");
      TerminalClose(94);
      return INIT_FAILED;
   }
   EventSetTimer(1);
   V69ProbeWrite("STARTING","awaiting_first_tick");
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason){ EventKillTimer(); }
void OnTimer(){ V69ProbeProcess(); }
void OnTick(){ V69ProbeProcess(); }
'''


def build(output: Path) -> str:
    text = SOURCE.replace("\n", "\r\n")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8", newline="")
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    print(f"V69_DEMO_EXECUTION_PROBE_SOURCE_SHA256={digest}")
    print(f"V69_DEMO_EXECUTION_PROBE_SOURCE_PATH={output}")
    print("V69_DEMO_EXECUTION_PROBE_LOT=0.01")
    print("V69_DEMO_EXECUTION_PROBE_REAL_MONEY_AUTHORIZED=0")
    return digest


def validate() -> None:
    required = (
        "ACCOUNT_TRADE_MODE_DEMO",
        "XAUUSDm",
        "V69ProbeLot=0.01",
        "V69ProbeMagic=699901",
        "OrderCheck(req,chk)",
        "g_probe.Buy(V69ProbeLot",
        "g_probe.PositionClose(ticket,50)",
        "actual_demo_open_and_close_verified",
        "V69ProbeRealMoneyAuthorized=false",
        "TerminalClose(terminal_code)",
    )
    for token in required:
        if token not in SOURCE:
            raise RuntimeError(f"probe source missing {token}")
    if "Sell(" in SOURCE or "REAL_ACCOUNT" in SOURCE:
        raise RuntimeError("probe source contains forbidden direction/real marker")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()
    validate()
    build(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
