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


def digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source_bytes(text: str) -> bytes:
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

void V69DLabel(const string key,const string text,const int y,const int size,const color clr)
{
   string name=V69D_PREFIX+key;
   if(ObjectFind(0,name)<0)
   {
      ObjectCreate(0,name,OBJ_LABEL,0,0,0);
      ObjectSetInteger(0,name,OBJPROP_CORNER,CORNER_LEFT_UPPER);
      ObjectSetInteger(0,name,OBJPROP_XDISTANCE,12);
      ObjectSetInteger(0,name,OBJPROP_SELECTABLE,false);
      ObjectSetInteger(0,name,OBJPROP_HIDDEN,true);
      ObjectSetString(0,name,OBJPROP_FONT,"Consolas");
   }
   ObjectSetInteger(0,name,OBJPROP_YDISTANCE,y);
   ObjectSetInteger(0,name,OBJPROP_FONTSIZE,size);
   ObjectSetInteger(0,name,OBJPROP_COLOR,clr);
   ObjectSetString(0,name,OBJPROP_TEXT,text);
}

string V69DReadProgress()
{
   int h=FileOpen(V69D_PROGRESS_FILE,FILE_READ|FILE_TXT|FILE_COMMON|FILE_ANSI);
   if(h==INVALID_HANDLE) return "progress: supervisor starting";
   string out="";
   while(!FileIsEnding(h))
   {
      string s=FileReadString(h);
      if(StringLen(s)<=0) continue;
      if(StringFind(s,"panel_")==0)
      {
         int eq=StringFind(s,"=");
         if(eq>0)
         {
            string v=StringSubstr(s,eq+1);
            if(StringLen(out)>0) out+=" | ";
            out+=v;
         }
      }
   }
   FileClose(h);
   if(StringLen(out)<=0) return "progress: collecting";
   return out;
}

void V69DStats(int &closed,int &wins,int &losses,double &realized,string &recent1,string &recent2,string &recent3)
{
   closed=wins=losses=0;realized=0.0;recent1=recent2=recent3="-";
   if(g_v69d_started<=0 || !HistorySelect(g_v69d_started,TimeCurrent())) return;
   int total=HistoryDealsTotal();
   int recent_n=0;
   for(int i=0;i<total;i++)
   {
      ulong deal=HistoryDealGetTicket(i);
      if(deal==0) continue;
      if(HistoryDealGetString(deal,DEAL_SYMBOL)!=_Symbol) continue;
      if((long)HistoryDealGetInteger(deal,DEAL_MAGIC)!=InpV64Magic) continue;
      double net=HistoryDealGetDouble(deal,DEAL_PROFIT)+HistoryDealGetDouble(deal,DEAL_COMMISSION)+
                 HistoryDealGetDouble(deal,DEAL_SWAP)+HistoryDealGetDouble(deal,DEAL_FEE);
      realized+=net;
      long entry=HistoryDealGetInteger(deal,DEAL_ENTRY);
      if(entry!=DEAL_ENTRY_OUT && entry!=DEAL_ENTRY_OUT_BY) continue;
      closed++;
      if(net>0) wins++; else if(net<0) losses++;
      string row=TimeToString((datetime)HistoryDealGetInteger(deal,DEAL_TIME),TIME_DATE|TIME_MINUTES)+
                 " pnl="+DoubleToString(net,2)+" reason="+
                 IntegerToString((int)HistoryDealGetInteger(deal,DEAL_REASON));
      recent3=recent2;recent2=recent1;recent1=row;recent_n++;
   }
}

void V69DUpdate()
{
   int closed=0,wins=0,losses=0;double realized=0.0;string r1="-",r2="-",r3="-";
   V69DStats(closed,wins,losses,realized,r1,r2,r3);
   ulong ticket=0;int d=0;double entry=0,sl=0,tp=0;double floating=0.0;
   bool open=V64OwnedPosition(ticket,d,entry,sl,tp);
   if(open)
   {
      MqlTick tick;
      if(SymbolInfoTick(_Symbol,tick))
      {
         double exitp=(d>0 ? tick.bid : tick.ask);
         ENUM_ORDER_TYPE ot=(d>0 ? ORDER_TYPE_BUY : ORDER_TYPE_SELL);
         OrderCalcProfit(ot,_Symbol,InpV64FixedLot,entry,exitp,floating);
      }
   }
   int total=closed;
   double wr=(total>0 ? 100.0*wins/total : 0.0);
   V69DLabel("00","V69 FROZEN FORWARD - DEMO SMOKE VALIDATION",12,11,clrAqua);
   V69DLabel("01","LONG ONLY | XAUUSDm M15 | lot 0.01 | REAL DISABLED",30,9,clrSilver);
   V69DLabel("02","PnL realized $"+DoubleToString(realized,2)+" | floating $"+DoubleToString(floating,2),50,10,(realized+floating>=0?clrLime:clrTomato));
   V69DLabel("03","Closed "+IntegerToString(closed)+" | W "+IntegerToString(wins)+" | L "+IntegerToString(losses)+" | WR "+DoubleToString(wr,1)+"%",70,10,clrWhite);
   V69DLabel("04","Position "+(open?"OPEN":"FLAT")+" | ticks "+IntegerToString((int)MathMin(g_v69d_ticks,2147483647)),90,9,clrWhite);
   V69DLabel("05",V69DReadProgress(),112,9,clrYellow);
   V69DLabel("06","Recent #1: "+r1,138,8,clrWhite);
   V69DLabel("07","Recent #2: "+r2,156,8,clrWhite);
   V69DLabel("08","Recent #3: "+r3,174,8,clrWhite);
   V69DLabel("09","Goal: runtime health + 2 closed trades; hard review cap 48h",198,8,clrSilver);
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
    base_sha = digest_bytes(source_bytes(base))
    if base_sha != FROZEN_PARENT_SHA256:
        raise RuntimeError(f"frozen V69 parent drift expected={FROZEN_PARENT_SHA256} actual={base_sha}")

    text = replace_once(base, "void OnTick()\n{", DASHBOARD + "\n\nvoid OnTick()\n{\n   g_v69d_ticks++;", "dashboard helpers/tick counter")

    init_anchor = "int OnInit()\n{"
    text = replace_once(text, init_anchor, init_anchor + "\n   g_v69d_started=TimeCurrent();\n   EventSetTimer(1);", "dashboard init")

    deinit_anchor = "void OnDeinit(const int reason)\n{"
    if deinit_anchor in text:
        text = replace_once(text, deinit_anchor, deinit_anchor + "\n   EventKillTimer();\n   V69DDelete();", "dashboard deinit")
    else:
        marker = "void OnTradeTransaction"
        pos = text.find(marker)
        if pos < 0:
            raise RuntimeError("V69 dashboard cannot locate OnTradeTransaction for OnDeinit insertion")
        deinit = "void OnDeinit(const int reason)\n{\n   EventKillTimer();\n   V69DDelete();\n}\n\n"
        text = text[:pos] + deinit + text[pos:]

    timer = "\nvoid OnTimer()\n{\n   V69DUpdate();\n}\n"
    text += timer
    validate(text, base)
    return text


def validate(text: str, base: str) -> None:
    required = (
        "V69 FROZEN FORWARD - DEMO SMOKE VALIDATION",
        "V69_SMOKE_PROGRESS.txt",
        "EventSetTimer(1)",
        "void OnTimer()",
        "V69DUpdate();",
        "HistoryDealsTotal()",
        "REAL DISABLED",
        "Goal: runtime health + 2 closed trades; hard review cap 48h",
        "ACCOUNT_TRADE_MODE_DEMO",
        "const bool V69ForwardRealMoneyAuthorized=false;",
        "InpV64AllowedDirection = 1",
        "InpV64Magic = 690169",
    )
    for token in required:
        if token not in text:
            raise RuntimeError(f"V69 dashboard required token missing: {token}")
    for forbidden in ("V69ForwardRealMoneyAuthorized=true", "InpV64AllowedDirection = -1"):
        if forbidden in text:
            raise RuntimeError(f"V69 dashboard forbidden token present: {forbidden}")

    # Critical strategy contract: order/state snippets from the frozen parent must
    # remain byte-identical. Dashboard code may only surround lifecycle/UI hooks.
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
