#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT = HERE / "build_v69_frozen_forward_demo_source.py"
FROZEN_PARENT_SHA256 = "0e3f168fa3de9ea62d7ec12d06efbf4d8d67989815056683a939f1d46d8d5f93"
EXPERT_NAME = "V69FrozenForwardSmokeDashboardLong"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


parent = load(PARENT, "v69_frozen_forward_parent_for_dashboard")


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def crlf_bytes(text: str) -> bytes:
    return text.replace("\n", "\r\n").encode("utf-8")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        raise RuntimeError(f"V69 dashboard {label} drifted expected=1 actual={n}")
    return text.replace(old, new, 1)


DASHBOARD = r'''
// -----------------------------------------------------------------------------
// V69 smoke-validation chart dashboard. UI/telemetry only: no strategy decision,
// order, stop, target, risk, direction, or timing parameter is modified here.
// -----------------------------------------------------------------------------
string V69D_PREFIX="V69D_";
datetime g_v69d_started=0;
long g_v69d_ticks=0;
string V69D_PROGRESS_FILE="mt5_quant\\v69_frozen_forward_demo\\V69_SMOKE_PROGRESS.txt";
string V69D_HEARTBEAT_FILE="mt5_quant\\v69_frozen_forward_demo\\V69_DASHBOARD_HEARTBEAT.txt";

void V69DPanelBase()
{
   string name=V69D_PREFIX+"BG";
   if(ObjectFind(0,name)<0)
   {
      ObjectCreate(0,name,OBJ_RECTANGLE_LABEL,0,0,0);
      ObjectSetInteger(0,name,OBJPROP_CORNER,CORNER_LEFT_UPPER);
      ObjectSetInteger(0,name,OBJPROP_XDISTANCE,5);
      ObjectSetInteger(0,name,OBJPROP_YDISTANCE,5);
      ObjectSetInteger(0,name,OBJPROP_XSIZE,690);
      ObjectSetInteger(0,name,OBJPROP_YSIZE,330);
      ObjectSetInteger(0,name,OBJPROP_BGCOLOR,clrBlack);
      ObjectSetInteger(0,name,OBJPROP_BORDER_COLOR,clrDimGray);
      ObjectSetInteger(0,name,OBJPROP_BACK,false);
      ObjectSetInteger(0,name,OBJPROP_ZORDER,0);
      ObjectSetInteger(0,name,OBJPROP_SELECTABLE,false);
      ObjectSetInteger(0,name,OBJPROP_HIDDEN,true);
   }
}

void V69DLabel(const string key,const string text,const int y,const int size,const color clr)
{
   string name=V69D_PREFIX+key;
   if(ObjectFind(0,name)<0)
   {
      ObjectCreate(0,name,OBJ_LABEL,0,0,0);
      ObjectSetInteger(0,name,OBJPROP_CORNER,CORNER_LEFT_UPPER);
      ObjectSetInteger(0,name,OBJPROP_XDISTANCE,12);
      ObjectSetInteger(0,name,OBJPROP_ZORDER,1);
      ObjectSetInteger(0,name,OBJPROP_SELECTABLE,false);
      ObjectSetInteger(0,name,OBJPROP_HIDDEN,true);
      ObjectSetString(0,name,OBJPROP_FONT,"Consolas");
   }
   ObjectSetInteger(0,name,OBJPROP_YDISTANCE,y);
   ObjectSetInteger(0,name,OBJPROP_FONTSIZE,size);
   ObjectSetInteger(0,name,OBJPROP_COLOR,clr);
   ObjectSetString(0,name,OBJPROP_TEXT,text);
}

string V69DProgressValue(const string key,const string fallback)
{
   int h=FileOpen(V69D_PROGRESS_FILE,FILE_READ|FILE_TXT|FILE_COMMON|FILE_ANSI);
   if(h==INVALID_HANDLE) return fallback;
   string prefix=key+"=";
   string out=fallback;
   while(!FileIsEnding(h))
   {
      string s=FileReadString(h);
      if(StringFind(s,prefix)==0){out=StringSubstr(s,StringLen(prefix));break;}
   }
   FileClose(h);
   return out;
}

double V69DPositionNet(const ulong exit_deal)
{
   if(exit_deal==0) return 0.0;
   long posid=HistoryDealGetInteger(exit_deal,DEAL_POSITION_ID);
   double net=0.0;
   int total=HistoryDealsTotal();
   for(int j=0;j<total;j++)
   {
      ulong d=HistoryDealGetTicket(j);
      if(d==0 || HistoryDealGetInteger(d,DEAL_POSITION_ID)!=posid) continue;
      if(HistoryDealGetString(d,DEAL_SYMBOL)!=_Symbol) continue;
      if((long)HistoryDealGetInteger(d,DEAL_MAGIC)!=InpV64Magic) continue;
      net+=HistoryDealGetDouble(d,DEAL_PROFIT)+HistoryDealGetDouble(d,DEAL_COMMISSION)+
           HistoryDealGetDouble(d,DEAL_SWAP)+HistoryDealGetDouble(d,DEAL_FEE);
   }
   return net;
}

string V69DTradeRow(const ulong exit_deal)
{
   if(exit_deal==0) return "-";
   long posid=HistoryDealGetInteger(exit_deal,DEAL_POSITION_ID);
   datetime close_time=(datetime)HistoryDealGetInteger(exit_deal,DEAL_TIME);
   double exit_price=HistoryDealGetDouble(exit_deal,DEAL_PRICE);
   datetime entry_time=0;double entry_price=0.0;
   int total=HistoryDealsTotal();
   for(int j=0;j<total;j++)
   {
      ulong d=HistoryDealGetTicket(j);
      if(d==0 || HistoryDealGetInteger(d,DEAL_POSITION_ID)!=posid) continue;
      if(HistoryDealGetString(d,DEAL_SYMBOL)!=_Symbol) continue;
      if((long)HistoryDealGetInteger(d,DEAL_MAGIC)!=InpV64Magic) continue;
      long e=HistoryDealGetInteger(d,DEAL_ENTRY);
      if(e==DEAL_ENTRY_IN && (entry_time==0 || (datetime)HistoryDealGetInteger(d,DEAL_TIME)<entry_time))
      {
         entry_time=(datetime)HistoryDealGetInteger(d,DEAL_TIME);
         entry_price=HistoryDealGetDouble(d,DEAL_PRICE);
      }
   }
   int seconds=(entry_time>0 ? (int)(close_time-entry_time) : 0);
   double net=V69DPositionNet(exit_deal);
   return TimeToString(close_time,TIME_DATE|TIME_MINUTES)+"  "+DoubleToString(entry_price,_Digits)+" -> "+
          DoubleToString(exit_price,_Digits)+"  pnl $"+DoubleToString(net,2)+"  dur "+IntegerToString(seconds)+"s";
}

void V69DStats(int &closed,int &wins,int &losses,double &realized,
               string &r1,string &r2,string &r3,string &r4,string &r5)
{
   closed=wins=losses=0;realized=0.0;r1=r2=r3=r4=r5="-";
   if(g_v69d_started<=0 || !HistorySelect(g_v69d_started,TimeCurrent())) return;
   int total=HistoryDealsTotal();
   ulong exits[];ArrayResize(exits,0);
   for(int i=0;i<total;i++)
   {
      ulong deal=HistoryDealGetTicket(i);
      if(deal==0) continue;
      if(HistoryDealGetString(deal,DEAL_SYMBOL)!=_Symbol) continue;
      if((long)HistoryDealGetInteger(deal,DEAL_MAGIC)!=InpV64Magic) continue;
      realized+=HistoryDealGetDouble(deal,DEAL_PROFIT)+HistoryDealGetDouble(deal,DEAL_COMMISSION)+
                HistoryDealGetDouble(deal,DEAL_SWAP)+HistoryDealGetDouble(deal,DEAL_FEE);
      long e=HistoryDealGetInteger(deal,DEAL_ENTRY);
      if(e!=DEAL_ENTRY_OUT && e!=DEAL_ENTRY_OUT_BY) continue;
      int n=ArraySize(exits);ArrayResize(exits,n+1);exits[n]=deal;
   }
   closed=ArraySize(exits);
   for(int k=0;k<closed;k++)
   {
      double net=V69DPositionNet(exits[k]);
      if(net>0) wins++; else if(net<0) losses++;
   }
   if(closed>0) r1=V69DTradeRow(exits[closed-1]);
   if(closed>1) r2=V69DTradeRow(exits[closed-2]);
   if(closed>2) r3=V69DTradeRow(exits[closed-3]);
   if(closed>3) r4=V69DTradeRow(exits[closed-4]);
   if(closed>4) r5=V69DTradeRow(exits[closed-5]);
}

void V69DWriteHeartbeat()
{
   int h=FileOpen(V69D_HEARTBEAT_FILE,FILE_WRITE|FILE_TXT|FILE_COMMON|FILE_ANSI);
   if(h==INVALID_HANDLE) return;
   FileWriteString(h,"time="+TimeToString(TimeCurrent(),TIME_DATE|TIME_MINUTES|TIME_SECONDS)+"\r\n");
   FileWriteString(h,"tick_count="+IntegerToString(g_v69d_ticks)+"\r\n");
   FileWriteString(h,"symbol="+_Symbol+"\r\n");
   FileWriteString(h,"period="+EnumToString((ENUM_TIMEFRAMES)_Period)+"\r\n");
   FileWriteString(h,"account_mode="+IntegerToString((int)AccountInfoInteger(ACCOUNT_TRADE_MODE))+"\r\n");
   FileWriteString(h,"terminal_trade_allowed="+IntegerToString((int)TerminalInfoInteger(TERMINAL_TRADE_ALLOWED))+"\r\n");
   FileWriteString(h,"mql_trade_allowed="+IntegerToString((int)MQLInfoInteger(MQL_TRADE_ALLOWED))+"\r\n");
   FileWriteString(h,"real_money_authorized=0\r\n");
   FileClose(h);
}

void V69DUpdate()
{
   V69DPanelBase();
   int closed=0,wins=0,losses=0;double realized=0.0;
   string r1="-",r2="-",r3="-",r4="-",r5="-";
   V69DStats(closed,wins,losses,realized,r1,r2,r3,r4,r5);
   ulong ticket=0;int d=0;double entry=0,sl=0,tp=0;double floating=0.0;
   bool open=V64OwnedPosition(ticket,d,entry,sl,tp);
   if(open)
   {
      MqlTick tick;
      if(SymbolInfoTick(_Symbol,tick))
      {
         double exitp=(d>0 ? tick.bid : tick.ask);
         ENUM_ORDER_TYPE ot=(d>0 ? ORDER_TYPE_BUY : ORDER_TYPE_SELL);
         if(!OrderCalcProfit(ot,_Symbol,InpV64FixedLot,entry,exitp,floating)) floating=0.0;
      }
   }
   double wr=(closed>0 ? 100.0*wins/closed : 0.0);
   V69DLabel("00","V69 FROZEN FORWARD - DEMO SMOKE VALIDATION",12,11,clrAqua);
   V69DLabel("01","LONG ONLY | XAUUSDm M15 | lot 0.01 | REAL DISABLED",30,9,clrSilver);
   V69DLabel("02","PnL realized $"+DoubleToString(realized,2)+" | floating $"+DoubleToString(floating,2),50,10,(realized+floating>=0?clrLime:clrTomato));
   V69DLabel("03","Closed "+IntegerToString(closed)+" | W "+IntegerToString(wins)+" | L "+IntegerToString(losses)+" | WR "+DoubleToString(wr,1)+"%",70,10,clrWhite);
   V69DLabel("04","Position "+(open?"OPEN":"FLAT")+" | ticks "+IntegerToString(g_v69d_ticks),90,9,clrWhite);
   V69DLabel("05","PROGRESS: "+V69DProgressValue("panel_progress","starting..."),112,9,clrYellow);
   V69DLabel("06","DONE:     "+V69DProgressValue("panel_done","waiting supervisor"),130,8,clrLime);
   V69DLabel("07","NEED:     "+V69DProgressValue("panel_need","runtime heartbeat"),148,8,clrOrange);
   V69DLabel("08","OUTPUT:   "+V69DProgressValue("panel_output","NOT EXPORTED"),166,8,clrAqua);
   V69DLabel("09","Trade #1: "+r1,192,8,clrWhite);
   V69DLabel("10","Trade #2: "+r2,210,8,clrWhite);
   V69DLabel("11","Trade #3: "+r3,228,8,clrWhite);
   V69DLabel("12","Trade #4: "+r4,246,8,clrWhite);
   V69DLabel("13","Trade #5: "+r5,264,8,clrWhite);
   V69DLabel("14","Quick gate: runtime health + 2 closed trades | hard review cap: 48h",292,8,clrSilver);
   ChartRedraw(0);
}

void V69DDelete()
{
   for(int i=ObjectsTotal(0)-1;i>=0;i--)
   {
      string n=ObjectName(0,i);
      if(StringFind(n,V69D_PREFIX)==0) ObjectDelete(0,n);
   }
}
'''


def transform() -> str:
    base = parent.transform()
    base_sha = sha_bytes(crlf_bytes(base))
    if base_sha != FROZEN_PARENT_SHA256:
        raise RuntimeError(f"frozen V69 parent drift expected={FROZEN_PARENT_SHA256} actual={base_sha}")

    text = replace_once(
        base,
        "void OnTick()\n{",
        DASHBOARD + "\n\nvoid OnTick()\n{\n   g_v69d_ticks++;",
        "dashboard helpers/tick counter",
    )
    text = replace_once(
        text,
        "   return INIT_SUCCEEDED;\n}",
        "   g_v69d_started=TimeCurrent();\n   EventSetTimer(1);\n   return INIT_SUCCEEDED;\n}",
        "dashboard successful init",
    )

    deinit_anchor = "void OnDeinit(const int reason)\n{"
    if deinit_anchor in text:
        text = replace_once(text, deinit_anchor, deinit_anchor + "\n   EventKillTimer();\n   V69DDelete();", "dashboard deinit")
    else:
        marker = "void OnTradeTransaction"
        pos = text.find(marker)
        if pos < 0:
            raise RuntimeError("V69 dashboard cannot locate OnTradeTransaction for OnDeinit insertion")
        text = text[:pos] + "void OnDeinit(const int reason)\n{\n   EventKillTimer();\n   V69DDelete();\n}\n\n" + text[pos:]

    text += "\nvoid OnTimer()\n{\n   V69DWriteHeartbeat();\n   V69DUpdate();\n}\n"
    validate(text, base)
    return text


def validate(text: str, base: str) -> None:
    required = (
        "V69 FROZEN FORWARD - DEMO SMOKE VALIDATION",
        "V69_SMOKE_PROGRESS.txt",
        "V69_DASHBOARD_HEARTBEAT.txt",
        "EventSetTimer(1)",
        "void OnTimer()",
        "V69DWriteHeartbeat();",
        "V69DUpdate();",
        "HistoryDealsTotal()",
        "V69DPositionNet",
        "OBJ_RECTANGLE_LABEL",
        "PROGRESS:",
        "OUTPUT:",
        "Trade #5:",
        "hard review cap: 48h",
        "ACCOUNT_TRADE_MODE_DEMO",
        "const bool V69ForwardRealMoneyAuthorized=false;",
        "InpV64AllowedDirection = 1",
        "InpV64Magic = 690169",
        "IntegerToString(g_v69d_ticks)",
        "if(!OrderCalcProfit(",
    )
    for token in required:
        if token not in text:
            raise RuntimeError(f"V69 dashboard required token missing: {token}")
    for forbidden in ("V69ForwardRealMoneyAuthorized=true", "InpV64AllowedDirection = -1", "LongToString("):
        if forbidden in text:
            raise RuntimeError(f"V69 dashboard forbidden token present: {forbidden}")

    for sig, nxt in (
        ("void V66TryMicroEntry", "void V64ManagePendingEntry"),
        ("void V64ManagePendingEntry", "void V64EvaluateBar"),
        ("bool V64BuildStopTarget", "void V64ArmPending"),
    ):
        a0=base.find(sig);a1=base.find(nxt,a0+1);b0=text.find(sig);b1=text.find(nxt,b0+1)
        if min(a0,a1,b0,b1)<0 or base[a0:a1] != text[b0:b1]:
            raise RuntimeError(f"V69 dashboard changed frozen strategy block {sig}")


def build(output: Path) -> str:
    text = transform().replace("\n", "\r\n")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8", newline="")
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    print(f"V69_DASHBOARD_SOURCE_SHA256={digest}")
    print(f"V69_DASHBOARD_SOURCE_PATH={output}")
    print(f"V69_DASHBOARD_FROZEN_PARENT_SHA256={FROZEN_PARENT_SHA256}")
    print("V69_DASHBOARD_STRATEGY_CHANGED=0")
    return digest


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()
    build(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())