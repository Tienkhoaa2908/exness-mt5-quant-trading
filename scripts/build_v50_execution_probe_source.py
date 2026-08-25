#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

EXPECTED_PARENT_SHA = "b3b012e856d814d36414e26d120674af864fea2c24db0b53f096fe7ba0a8f599"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def replace_once(text: str, old: str, new: str) -> str:
    n = text.count(old)
    if n != 1:
        raise RuntimeError(f"expected exactly one occurrence, found={n}: {old[:160]!r}")
    return text.replace(old, new, 1)


GLOBALS = r'''
input long InpV50ProbeMagic = 500050;
input int InpV50ProbeTargetRoundTrips = 3;
input int InpV50ProbeHoldSeconds = 45;
input int InpV50ProbeGapSeconds = 60;
input int InpV50ProbeConfirmTimeoutSeconds = 60;
input int InpV50ProbeHardMinutes = 240;
input int InpV50ProtectiveDistancePoints = 1500;
input double InpV50MaxMarginFraction = 0.80;
CTrade g_v50_probe_trade;
bool g_v50_ready=false,g_v50_halted=false,g_v50_final=false,g_v50_open_pending=false,g_v50_close_pending=false;
string g_v50_halt_reason="";
datetime g_v50_start=0,g_v50_pending_since=0,g_v50_open_since=0,g_v50_last_action=0;
int g_v50_round_trips=0,g_v50_requests=0,g_v50_rejects=0,g_v50_duplicates=0;
string g_v50_status_file="mt5_quant\\v50\\V50_EXECUTION_PROBE_STATUS.txt";
string g_v50_final_file="mt5_quant\\v50\\V50_EXECUTION_PROBE_FINAL.txt";
string g_v50_events_file="mt5_quant\\v50\\V50_EXECUTION_PROBE_EVENTS.csv";
string g_v50_transactions_file="mt5_quant\\v50\\V50_EXECUTION_PROBE_TRANSACTIONS.csv";
'''

FUNCS = r'''
void V50Append(const string file,const string row)
{
   int h=FileOpen(file,FILE_READ|FILE_WRITE|FILE_TXT|FILE_ANSI|FILE_COMMON);
   if(h==INVALID_HANDLE) return;
   FileSeek(h,0,SEEK_END); FileWriteString(h,row+"\\r\\n"); FileClose(h);
}

int V50ProbePositions(ulong &ticket,int &direction,double &volume)
{
   int n=0; ticket=0; direction=0; volume=0.0;
   for(int i=0;i<PositionsTotal();++i)
   {
      ulong t=PositionGetTicket(i); if(t==0) continue;
      if(PositionGetString(POSITION_SYMBOL)!=_Symbol) continue;
      if((long)PositionGetInteger(POSITION_MAGIC)!=InpV50ProbeMagic) continue;
      n++;
      if(n==1){ ticket=t; direction=((ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE)==POSITION_TYPE_BUY?1:-1); volume=PositionGetDouble(POSITION_VOLUME); }
   }
   return n;
}

bool V50ProbeBusy()
{
   ulong t=0; int d=0; double v=0.0;
   return V50ProbePositions(t,d,v)>0 || g_v50_open_pending || g_v50_close_pending;
}

void V50Halt(const string reason)
{
   if(g_v50_halted) return;
   g_v50_halted=true; g_v50_halt_reason=reason; V49Notify("V50 PROBE HALT "+reason);
}

bool V50RetcodeOk()
{
   uint rc=g_v50_probe_trade.ResultRetcode();
   return rc==TRADE_RETCODE_DONE || rc==TRADE_RETCODE_DONE_PARTIAL || rc==TRADE_RETCODE_PLACED;
}

void V50Record(const string action,const int direction,const double volume,const double request_price,const double sl,const double tp,const double margin,const bool ok)
{
   string row=TimeToString(TimeLocal(),TIME_DATE|TIME_MINUTES|TIME_SECONDS)+","+action+","+IntegerToString(direction)+","+
      DoubleToString(volume,6)+","+DoubleToString(request_price,_Digits)+","+DoubleToString(g_v50_probe_trade.ResultPrice(),_Digits)+","+
      DoubleToString(sl,_Digits)+","+DoubleToString(tp,_Digits)+","+DoubleToString(margin,6)+","+IntegerToString(ok?1:0)+","+
      IntegerToString((int)g_v50_probe_trade.ResultRetcode())+","+g_v50_probe_trade.ResultRetcodeDescription()+","+
      IntegerToString((int)g_v50_probe_trade.ResultOrder())+","+IntegerToString((int)g_v50_probe_trade.ResultDeal());
   V50Append(g_v50_events_file,row);
}

bool V50MarginOk(const int direction,const double volume,const double price,double &margin)
{
   margin=0.0;
   ENUM_ORDER_TYPE type=(direction>0?ORDER_TYPE_BUY:ORDER_TYPE_SELL);
   if(!OrderCalcMargin(type,_Symbol,volume,price,margin)) return false;
   double free_margin=AccountInfoDouble(ACCOUNT_MARGIN_FREE);
   return free_margin>0.0 && margin<=free_margin*InpV50MaxMarginFraction;
}

void V50OpenProbe()
{
   MqlTick tick; if(!SymbolInfoTick(_Symbol,tick) || tick.bid<=0.0 || tick.ask<=tick.bid) return;
   int direction=(g_v50_round_trips%2==0?1:-1);
   double volume=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MIN);
   if(volume<=0.0){ V50Halt("invalid_min_volume"); return; }
   double px=(direction>0?tick.ask:tick.bid),margin=0.0;
   if(!V50MarginOk(direction,volume,px,margin)){ V50Halt("min_volume_margin_insufficient"); return; }
   double dist=MathMax((double)InpV50ProtectiveDistancePoints*_Point,(tick.ask-tick.bid)*10.0);
   double sl=NormalizeDouble(direction>0?tick.bid-dist:tick.ask+dist,_Digits);
   double tp=NormalizeDouble(direction>0?tick.ask+dist:tick.bid-dist,_Digits);
   g_v50_requests++; g_v50_open_pending=true; g_v50_pending_since=TimeLocal(); g_v50_last_action=TimeLocal();
   bool ok=(direction>0?g_v50_probe_trade.Buy(volume,_Symbol,0.0,sl,tp,"V50 execution probe"):g_v50_probe_trade.Sell(volume,_Symbol,0.0,sl,tp,"V50 execution probe"));
   V50Record("PROBE_OPEN",direction,volume,px,sl,tp,margin,ok);
   if(!ok || !V50RetcodeOk()){ g_v50_open_pending=false; g_v50_rejects++; }
}

void V50CloseProbe(const ulong ticket,const int direction,const double volume)
{
   MqlTick tick; if(!SymbolInfoTick(_Symbol,tick)) return;
   double px=(direction>0?tick.bid:tick.ask);
   g_v50_requests++; g_v50_close_pending=true; g_v50_pending_since=TimeLocal(); g_v50_last_action=TimeLocal();
   bool ok=g_v50_probe_trade.PositionClose(ticket,(ulong)InpV49MaxDeviationPoints);
   V50Record("PROBE_CLOSE",direction,volume,px,0.0,0.0,0.0,ok);
   if(!ok || !V50RetcodeOk()){ g_v50_close_pending=false; g_v50_rejects++; }
}

void V50WriteStatus()
{
   ulong t=0; int d=0; double v=0.0; int n=V50ProbePositions(t,d,v);
   int h=FileOpen(g_v50_status_file,FILE_WRITE|FILE_TXT|FILE_ANSI|FILE_COMMON); if(h==INVALID_HANDLE) return;
   string x="schema=v50_execution_probe_status_v1\\r\\n";
   x+="updated_local="+TimeToString(TimeLocal(),TIME_DATE|TIME_MINUTES|TIME_SECONDS)+"\\r\\n";
   x+="ready="+IntegerToString(g_v50_ready?1:0)+"\\r\\naccount_mode=DEMO\\r\\n";
   x+="probe_target_round_trips="+IntegerToString(InpV50ProbeTargetRoundTrips)+"\\r\\nprobe_round_trips="+IntegerToString(g_v50_round_trips)+"\\r\\n";
   x+="probe_requests="+IntegerToString(g_v50_requests)+"\\r\\nprobe_rejects="+IntegerToString(g_v50_rejects)+"\\r\\nprobe_positions="+IntegerToString(n)+"\\r\\n";
   x+="probe_open_pending="+IntegerToString(g_v50_open_pending?1:0)+"\\r\\nprobe_close_pending="+IntegerToString(g_v50_close_pending?1:0)+"\\r\\n";
   x+="probe_halted="+IntegerToString(g_v50_halted?1:0)+"\\r\\nprobe_halt_reason="+g_v50_halt_reason+"\\r\\n";
   x+="strategy_healthy_breadth="+IntegerToString(V48HealthyCount())+"\\r\\nstrategy_round_trips="+IntegerToString(g_v49_round_trips)+"\\r\\n";
   x+="run_id="+g_run_id+"\\r\\nreal_money_authorized=0\\r\\n";
   FileWriteString(h,x); FileClose(h);
}

void V50WriteFinal(const string verdict,const string reason)
{
   if(g_v50_final) return;
   int h=FileOpen(g_v50_final_file,FILE_WRITE|FILE_TXT|FILE_ANSI|FILE_COMMON); if(h==INVALID_HANDLE) return;
   string x="schema=v50_execution_probe_final_v1\\r\\nverdict="+verdict+"\\r\\nreason="+reason+"\\r\\n";
   x+="probe_round_trips="+IntegerToString(g_v50_round_trips)+"\\r\\nprobe_requests="+IntegerToString(g_v50_requests)+"\\r\\nprobe_rejects="+IntegerToString(g_v50_rejects)+"\\r\\n";
   x+="strategy_round_trips="+IntegerToString(g_v49_round_trips)+"\\r\\nstrategy_healthy_breadth="+IntegerToString(V48HealthyCount())+"\\r\\n";
   x+="run_id="+g_run_id+"\\r\\nreal_money_authorized=0\\r\\n";
   FileWriteString(h,x); FileClose(h);
   g_v50_final=true; g_v49_accept_new=false; V49Notify("V50 FINAL "+verdict+" probes="+IntegerToString(g_v50_round_trips));
}

void V50MaybeFinal()
{
   ulong pt=0; int pd=0; double pv=0.0; int pn=V50ProbePositions(pt,pd,pv);
   ulong st=0; int sd=0; double sv=0.0; int sn=V49OwnedPositionCount(st,sd,sv);
   bool flat=(pn==0 && sn==0 && !B[BI(23,3)].open && !g_v50_open_pending && !g_v50_close_pending && !g_v49_open_pending && !g_v49_close_pending);
   if(!flat) return;
   if(g_v50_halted){ V50WriteFinal("HOLD","execution_probe_halted_"+g_v50_halt_reason); return; }
   if(g_v50_round_trips>=InpV50ProbeTargetRoundTrips)
   {
      bool reject_ok=(g_v50_requests==0 || g_v50_rejects*5<=g_v50_requests);
      if(g_v50_duplicates==0 && reject_ok) V50WriteFinal("EXECUTION_PIPELINE_PASS","three_min_volume_demo_round_trips_confirmed");
      else V50WriteFinal("HOLD","probe_reject_or_duplicate_failure");
      return;
   }
   if(g_v50_start>0 && TimeLocal()-g_v50_start>=InpV50ProbeHardMinutes*60) V50WriteFinal("EXECUTION_PROBE_INCOMPLETE","probe_timeout_before_three_round_trips");
}

void V50Step()
{
   if(!g_v50_ready || g_v50_final) return;
   if((ENUM_ACCOUNT_TRADE_MODE)AccountInfoInteger(ACCOUNT_TRADE_MODE)!=ACCOUNT_TRADE_MODE_DEMO){ V50Halt("non_demo_account"); V50MaybeFinal(); return; }
   if(!TerminalInfoInteger(TERMINAL_TRADE_ALLOWED) || !MQLInfoInteger(MQL_TRADE_ALLOWED)){ V50Halt("autotrading_disabled"); V50MaybeFinal(); return; }
   if(TerminalInfoInteger(TERMINAL_DLLS_ALLOWED)){ V50Halt("dll_permission_on"); V50MaybeFinal(); return; }
   ulong t=0; int d=0; double v=0.0; int n=V50ProbePositions(t,d,v);
   if(n>1){ g_v50_duplicates++; V50Halt("duplicate_probe_positions"); V50MaybeFinal(); return; }
   if(g_v50_open_pending && n==1){ g_v50_open_pending=false; if(g_v50_open_since==0) g_v50_open_since=TimeLocal(); }
   if(g_v50_close_pending && n==0) g_v50_close_pending=false;
   if((g_v50_open_pending || g_v50_close_pending) && g_v50_pending_since>0 && TimeLocal()-g_v50_pending_since>InpV50ProbeConfirmTimeoutSeconds)
   { V50Halt(g_v50_open_pending?"probe_open_confirmation_timeout":"probe_close_confirmation_timeout"); V50MaybeFinal(); return; }
   if(n==1)
   {
      if(g_v50_open_since==0) g_v50_open_since=TimeLocal();
      if(TimeLocal()-g_v50_open_since>=InpV50ProbeHoldSeconds) V50CloseProbe(t,d,v);
      V50WriteStatus(); return;
   }
   ulong st=0; int sd=0; double sv=0.0;
   if(B[BI(23,3)].open || g_v49_open_pending || g_v49_close_pending || V49OwnedPositionCount(st,sd,sv)>0){ V50WriteStatus(); return; }
   if(g_v50_round_trips<InpV50ProbeTargetRoundTrips && (g_v50_last_action==0 || TimeLocal()-g_v50_last_action>=InpV50ProbeGapSeconds)) V50OpenProbe();
   V50MaybeFinal(); V50WriteStatus();
}

void V50HandleDeal(const ulong deal)
{
   if(!HistoryDealSelect(deal)) return;
   long entry=HistoryDealGetInteger(deal,DEAL_ENTRY);
   double price=HistoryDealGetDouble(deal,DEAL_PRICE),volume=HistoryDealGetDouble(deal,DEAL_VOLUME);
   string symbol=HistoryDealGetString(deal,DEAL_SYMBOL);
   V50Append(g_v50_transactions_file,TimeToString(TimeLocal(),TIME_DATE|TIME_MINUTES|TIME_SECONDS)+","+IntegerToString((int)deal)+","+symbol+","+DoubleToString(price,_Digits)+","+DoubleToString(volume,6)+","+IntegerToString((int)entry));
   if(entry==DEAL_ENTRY_IN){ g_v50_open_pending=false; g_v50_open_since=TimeLocal(); V49Notify("V50 PROBE OPEN confirmed "+symbol); }
   if(entry==DEAL_ENTRY_OUT || entry==DEAL_ENTRY_OUT_BY)
   {
      g_v50_close_pending=false;
      ulong t=0; int d=0; double v=0.0;
      if(V50ProbePositions(t,d,v)==0){ g_v50_round_trips++; g_v50_open_since=0; g_v50_last_action=TimeLocal(); V49Notify("V50 PROBE CLOSE confirmed roundtrips="+IntegerToString(g_v50_round_trips)); }
   }
   V50MaybeFinal(); V50WriteStatus();
}

bool V50Init()
{
   if((ENUM_ACCOUNT_TRADE_MODE)AccountInfoInteger(ACCOUNT_TRADE_MODE)!=ACCOUNT_TRADE_MODE_DEMO) return false;
   if(_Symbol!="XAUUSDm" || _Period!=PERIOD_M15) return false;
   if(!TerminalInfoInteger(TERMINAL_TRADE_ALLOWED) || !MQLInfoInteger(MQL_TRADE_ALLOWED)) return false;
   if(TerminalInfoInteger(TERMINAL_DLLS_ALLOWED)) return false;
   ulong t=0; int d=0; double v=0.0; if(V50ProbePositions(t,d,v)>0) return false;
   g_v50_probe_trade.SetExpertMagicNumber((ulong)InpV50ProbeMagic);
   g_v50_probe_trade.SetDeviationInPoints(InpV49MaxDeviationPoints);
   g_v50_probe_trade.SetTypeFillingBySymbol(_Symbol);
   FolderCreate("mt5_quant\\v50",FILE_COMMON);
   V50Append(g_v50_events_file,"time,action,direction,volume,request_price,result_price,sl,tp,required_margin,call_ok,retcode,retcode_desc,order,deal");
   V50Append(g_v50_transactions_file,"time,deal,symbol,price,volume,entry");
   g_v50_start=TimeLocal(); g_v50_ready=true; V49Notify("V50 START DEMO execution probe + frozen breadth4"); V50WriteStatus(); return true;
}
'''


def build(source: Path, output: Path) -> str:
    actual = sha256(source)
    if actual != EXPECTED_PARENT_SHA:
        raise RuntimeError(f"V50 requires accepted V49 source expected={EXPECTED_PARENT_SHA} actual={actual}")
    text = source.read_text(encoding="utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("v49_one_shot_demo_rehearsal_v1", "v50_execution_probe_v1")
    text = text.replace("V49OneShotDemoRehearsal.mq5", "V50ExecutionProbe.mq5")
    text = text.replace("v49_demo_rehearsal_state.csv", "v50_execution_probe_state.csv")
    text = text.replace("V49 DEMO REHEARSAL | ", "V50 DEMO EXECUTION PROBE | ")
    text = replace_once(text, "CTrade g_v49_trade;", "CTrade g_v49_trade;\n" + GLOBALS.strip())
    marker = "bool CreateHandles()\n{"
    text = replace_once(text, marker, FUNCS.strip() + "\n\n" + marker)
    sync = "void V49SyncBrokerWithVirtual()\n{"
    text = replace_once(text, sync, sync + "\n   if(V50ProbeBusy()) return;")
    text = replace_once(text,
        'if(!V49InitExecution()){ V48WriteInitDiagnostic("REFUSED","v49_execution_preflight_failed"); return INIT_FAILED; }',
        'if(!V49InitExecution() || !V50Init()){ V48WriteInitDiagnostic("REFUSED","v50_execution_probe_preflight_failed"); return INIT_FAILED; }')
    text = replace_once(text,
        "if(g_v49_init_ready){ V49SyncBrokerWithVirtual(); V49MaybeFinalize(); SaveAdaptiveState(); WritePaperStatus(); V49WriteStatus(); WriteManifest(); WriteLatest(); UpdatePaperDashboard(); }",
        "if(g_v49_init_ready){ V50Step(); V49SyncBrokerWithVirtual(); V49MaybeFinalize(); V50WriteStatus(); SaveAdaptiveState(); WritePaperStatus(); V49WriteStatus(); WriteManifest(); WriteLatest(); UpdatePaperDashboard(); }")
    text = replace_once(text,
        "V49ObserveMarketDay(tick.time);\n   V49SyncBrokerWithVirtual();\n   V49MaybeFinalize();\n   V49WriteStatus();",
        "V49ObserveMarketDay(tick.time);\n   V50Step();\n   V49SyncBrokerWithVirtual();\n   V49MaybeFinalize();\n   V50WriteStatus();\n   V49WriteStatus();")
    text = replace_once(text,
        "if((long)HistoryDealGetInteger(trans.deal,DEAL_MAGIC)!=InpV49Magic) return;",
        "long v50_magic=(long)HistoryDealGetInteger(trans.deal,DEAL_MAGIC);\n   if(v50_magic==InpV50ProbeMagic){ V50HandleDeal(trans.deal); return; }\n   if(v50_magic!=InpV49Magic) return;")
    for token in ("InpV50ProbeMagic = 500050", "InpV50ProbeTargetRoundTrips = 3", "OrderCalcMargin", "SYMBOL_VOLUME_MIN", "EXECUTION_PIPELINE_PASS", "if(V50ProbeBusy()) return;", "ACCOUNT_TRADE_MODE_DEMO", "real_money_authorized=0"):
        if token not in text: raise RuntimeError(f"V50 required token missing: {token}")
    for token in ("ACCOUNT_TRADE_MODE_REAL", "real_money_authorized=1", "Martingale", "martingale"):
        if token in text: raise RuntimeError(f"V50 forbidden token present: {token}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8", newline="\n")
    digest=sha256(output); print(f"V50 source built sha256={digest} parent_sha256={actual} path={output}"); return digest


def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument("--source",required=True); ap.add_argument("--output",required=True); ns=ap.parse_args(); build(Path(ns.source),Path(ns.output)); return 0


if __name__ == "__main__": raise SystemExit(main())
