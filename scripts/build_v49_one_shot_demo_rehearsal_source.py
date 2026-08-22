#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

EXPECTED_PARENT_SHA = "ecb78c603d3426396f3d3f56f35dcdf1b3a0983090a071e2972b6bd9ab9068aa"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def replace_once(text: str, old: str, new: str) -> str:
    n = text.count(old)
    if n != 1:
        raise RuntimeError(f"expected exactly one occurrence, found={n}: {old[:140]!r}")
    return text.replace(old, new, 1)


def build(source: Path, output: Path) -> str:
    actual = sha256(source)
    if actual != EXPECTED_PARENT_SHA:
        raise RuntimeError(f"V49 requires frozen V48 parent expected={EXPECTED_PARENT_SHA} actual={actual}")

    text = source.read_text(encoding="utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")

    # V49 adds only a broker-DEMO execution adapter. The frozen strategy body is inherited.
    text = "#include <Trade/Trade.mqh>\n" + text
    text = text.replace('v48_demo_paper_forward_v2', 'v49_one_shot_demo_rehearsal_v1')
    text = text.replace('V48 DEMO-PAPER', 'V49 DEMO-REHEARSAL')
    text = text.replace('V48_DEMO_PAPER', 'V49_DEMO_REHEARSAL')
    text = text.replace('v48_demo_paper_state.csv', 'v49_demo_rehearsal_state.csv')
    text = text.replace('V48DemoPaperObserver.mq5', 'V49OneShotDemoRehearsal.mq5')
    text = text.replace('V48 PAPER BOT | ', 'V49 DEMO REHEARSAL | ')
    text = text.replace('DEMO FEED / VIRTUAL EXECUTION | BROKER ORDERS 0', 'DEMO BROKER EXECUTION | VIRTUAL INTENT + OWNED MAGIC')
    text = text.replace('broker_orders=0\\r\\nlive_authorized=0', 'broker_demo_orders=1\\r\\nreal_money_authorized=0')
    text = text.replace('native_broker_orders=0', 'native_broker_demo_orders=1')

    globals_marker = 'datetime g_paper_session_start=0;'
    globals_block = r'''datetime g_paper_session_start=0;

input long InpV49Magic = 490049;
input int InpV49MinMarketDays = 3;
input int InpV49MinRoundTrips = 3;
input int InpV49HardCalendarDays = 14;
input int InpV49MaxDeviationPoints = 100;
input int InpV49RequestCooldownSeconds = 30;
input int InpV49ConfirmTimeoutSeconds = 60;
input bool InpV49PushNotifications = true;

CTrade g_v49_trade;
bool g_v49_halted=false;
bool g_v49_accept_new=true;
bool g_v49_final_written=false;
bool g_v49_init_ready=false;
bool g_v49_open_pending=false;
bool g_v49_close_pending=false;
bool g_v49_server_exit_wait=false;
string g_v49_halt_reason="";
datetime g_v49_local_start=0;
datetime g_v49_pending_since=0;
datetime g_v49_server_exit_time=0;
datetime g_v49_last_request_time=0;
string g_v49_last_market_date="";
int g_v49_market_days=0;
int g_v49_round_trips=0;
int g_v49_requests=0;
int g_v49_rejects=0;
int g_v49_duplicate_events=0;
int g_v49_direction_mismatches=0;
string g_v49_status_file="mt5_quant\\v49\\V49_DEMO_REHEARSAL_STATUS.txt";
string g_v49_final_file="mt5_quant\\v49\\V49_DEMO_REHEARSAL_FINAL.txt";
string g_v49_events_file="mt5_quant\\v49\\V49_DEMO_REHEARSAL_EVENTS.csv";
string g_v49_transactions_file="mt5_quant\\v49\\V49_DEMO_REHEARSAL_TRANSACTIONS.csv";'''
    text = replace_once(text, globals_marker, globals_block)

    funcs_marker = 'bool CreateHandles()\n{'
    funcs = r'''void V49AppendCsv(const string file,const string row)
{
   int h=FileOpen(file,FILE_READ|FILE_WRITE|FILE_TXT|FILE_ANSI|FILE_COMMON);
   if(h==INVALID_HANDLE) return;
   FileSeek(h,0,SEEK_END); FileWriteString(h,row+"\r\n"); FileClose(h);
}

void V49Notify(const string msg)
{
   Print(msg);
   if(InpV49PushNotifications)
   {
      ResetLastError();
      if(!SendNotification(msg)) PrintFormat("V49 push notification failed err=%d",GetLastError());
   }
}

void V49Halt(const string reason)
{
   if(!g_v49_halted)
   {
      g_v49_halted=true; g_v49_accept_new=false; g_v49_halt_reason=reason;
      V49Notify("V49 HALT "+reason);
   }
}

double V49NormalizeVolume(const double requested)
{
   double vmin=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MIN);
   double vmax=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MAX);
   double step=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_STEP);
   if(step<=0.0) step=vmin;
   double v=MathMax(vmin,MathMin(vmax,requested));
   if(step>0.0) v=MathFloor(v/step+0.5)*step;
   return MathMax(vmin,MathMin(vmax,v));
}

double V49ExecutablePrice(const int direction)
{
   MqlTick t;
   if(!SymbolInfoTick(_Symbol,t)) return 0.0;
   return direction>0?t.ask:t.bid;
}

int V49OwnedPositionCount(ulong &ticket,int &direction,double &volume)
{
   int n=0; ticket=0; direction=0; volume=0.0;
   for(int i=0;i<PositionsTotal();++i)
   {
      ulong t=PositionGetTicket(i);
      if(t==0) continue;
      if(PositionGetString(POSITION_SYMBOL)!=_Symbol) continue;
      if((long)PositionGetInteger(POSITION_MAGIC)!=InpV49Magic) continue;
      n++;
      if(n==1)
      {
         ticket=t;
         ENUM_POSITION_TYPE pt=(ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);
         direction=(pt==POSITION_TYPE_BUY?1:-1);
         volume=PositionGetDouble(POSITION_VOLUME);
      }
   }
   return n;
}

int V49ForeignSymbolPositions()
{
   int n=0;
   for(int i=0;i<PositionsTotal();++i)
   {
      ulong t=PositionGetTicket(i); if(t==0) continue;
      if(PositionGetString(POSITION_SYMBOL)!=_Symbol) continue;
      if((long)PositionGetInteger(POSITION_MAGIC)!=InpV49Magic) n++;
   }
   return n;
}

bool V49TradeRetcodeOk()
{
   uint rc=g_v49_trade.ResultRetcode();
   return rc==TRADE_RETCODE_DONE || rc==TRADE_RETCODE_DONE_PARTIAL || rc==TRADE_RETCODE_PLACED;
}

void V49RecordRequest(const string action,const int direction,const double virtual_volume,const double broker_volume,const double request_price,const double sl,const double tp,const bool call_ok)
{
   string row=TimeToString(TimeLocal(),TIME_DATE|TIME_MINUTES|TIME_SECONDS)+","+action+","+IntegerToString(direction)+","+
      DoubleToString(virtual_volume,6)+","+DoubleToString(broker_volume,6)+","+DoubleToString(request_price,_Digits)+","+
      DoubleToString(g_v49_trade.ResultPrice(),_Digits)+","+DoubleToString(sl,_Digits)+","+DoubleToString(tp,_Digits)+","+
      IntegerToString(call_ok?1:0)+","+IntegerToString((int)g_v49_trade.ResultRetcode())+","+g_v49_trade.ResultRetcodeDescription()+","+
      IntegerToString((int)g_v49_trade.ResultOrder())+","+IntegerToString((int)g_v49_trade.ResultDeal());
   V49AppendCsv(g_v49_events_file,row);
}

bool V49RequestCooldownReady()
{
   return g_v49_last_request_time==0 || (TimeLocal()-g_v49_last_request_time)>=InpV49RequestCooldownSeconds;
}

void V49OpenFromVirtual()
{
   const int ci=23,bi=3,ix=BI(ci,bi);
   if(g_v49_halted || !g_v49_accept_new || !B[ix].open || g_v49_open_pending || g_v49_close_pending || !V49RequestCooldownReady()) return;
   double vv=B[ix].volume;
   double bv=V49NormalizeVolume(vv);
   double request_px=V49ExecutablePrice(B[ix].direction);
   g_v49_requests++;
   g_v49_open_pending=true;
   g_v49_pending_since=TimeLocal();
   g_v49_last_request_time=TimeLocal();
   bool ok=false;
   if(B[ix].direction>0) ok=g_v49_trade.Buy(bv,_Symbol,0.0,B[ix].stop,B[ix].tp,"V49 breadth4");
   else if(B[ix].direction<0) ok=g_v49_trade.Sell(bv,_Symbol,0.0,B[ix].stop,B[ix].tp,"V49 breadth4");
   V49RecordRequest("OPEN",B[ix].direction,vv,bv,request_px,B[ix].stop,B[ix].tp,ok);
   if(!ok || !V49TradeRetcodeOk())
   {
      g_v49_open_pending=false;
      g_v49_rejects++;
      PrintFormat("V49 broker DEMO open rejected call=%d retcode=%u %s",(int)ok,g_v49_trade.ResultRetcode(),g_v49_trade.ResultRetcodeDescription());
   }
}

void V49CloseOwned(const ulong ticket,const int direction,const double volume)
{
   if(g_v49_close_pending || g_v49_open_pending || !V49RequestCooldownReady()) return;
   double request_px=V49ExecutablePrice(-direction);
   g_v49_requests++;
   g_v49_close_pending=true;
   g_v49_pending_since=TimeLocal();
   g_v49_last_request_time=TimeLocal();
   bool ok=g_v49_trade.PositionClose(ticket,(ulong)InpV49MaxDeviationPoints);
   V49RecordRequest("CLOSE",direction,volume,volume,request_px,0.0,0.0,ok);
   if(!ok || !V49TradeRetcodeOk())
   {
      g_v49_close_pending=false;
      g_v49_rejects++;
      PrintFormat("V49 broker DEMO close rejected call=%d retcode=%u %s",(int)ok,g_v49_trade.ResultRetcode(),g_v49_trade.ResultRetcodeDescription());
   }
}

void V49ObserveMarketDay(const datetime tick_time)
{
   string d=TimeToString(tick_time,TIME_DATE);
   if(d!="" && d!=g_v49_last_market_date)
   {
      g_v49_last_market_date=d; g_v49_market_days++;
      V49AppendCsv(g_v49_events_file,TimeToString(TimeLocal(),TIME_DATE|TIME_MINUTES|TIME_SECONDS)+",MARKET_DAY,"+d);
   }
}

void V49SyncBrokerWithVirtual()
{
   if((ENUM_ACCOUNT_TRADE_MODE)AccountInfoInteger(ACCOUNT_TRADE_MODE)!=ACCOUNT_TRADE_MODE_DEMO){ V49Halt("non_demo_account"); return; }
   if(!TerminalInfoInteger(TERMINAL_TRADE_ALLOWED) || !MQLInfoInteger(MQL_TRADE_ALLOWED)){ V49Halt("autotrading_disabled"); return; }
   if(TerminalInfoInteger(TERMINAL_DLLS_ALLOWED)){ V49Halt("dll_permission_on"); return; }

   const int ci=23,bi=3,ix=BI(ci,bi);
   ulong ticket=0; int broker_dir=0; double broker_vol=0.0;
   int owned=V49OwnedPositionCount(ticket,broker_dir,broker_vol);
   if(owned>1){ g_v49_duplicate_events++; V49Halt("duplicate_owned_positions"); return; }

   if(g_v49_open_pending && owned==1) g_v49_open_pending=false;
   if(g_v49_close_pending && owned==0) g_v49_close_pending=false;
   if((g_v49_open_pending || g_v49_close_pending) && g_v49_pending_since>0 && (TimeLocal()-g_v49_pending_since)>InpV49ConfirmTimeoutSeconds)
   {
      V49Halt(g_v49_open_pending?"open_confirmation_timeout":"close_confirmation_timeout");
      return;
   }

   if(g_v49_server_exit_wait)
   {
      if(!B[ix].open) g_v49_server_exit_wait=false;
      else if((TimeLocal()-g_v49_server_exit_time)>InpV49ConfirmTimeoutSeconds)
      {
         V49Halt("broker_exit_virtual_still_open");
         return;
      }
      else return;
   }

   if(B[ix].open)
   {
      if(owned==0) V49OpenFromVirtual();
      else if(broker_dir!=B[ix].direction){ g_v49_direction_mismatches++; V49Halt("virtual_broker_direction_mismatch"); }
   }
   else if(owned==1)
   {
      V49CloseOwned(ticket,broker_dir,broker_vol);
   }
}

void V49WriteStatus()
{
   const int ci=23,bi=3,ix=BI(ci,bi);
   ulong ticket=0; int broker_dir=0; double broker_vol=0.0;
   int owned=V49OwnedPositionCount(ticket,broker_dir,broker_vol);
   int h=FileOpen(g_v49_status_file,FILE_WRITE|FILE_TXT|FILE_ANSI|FILE_COMMON);
   if(h==INVALID_HANDLE) return;
   string x="schema=v49_demo_rehearsal_status_v1\r\n";
   x+="updated_local="+TimeToString(TimeLocal(),TIME_DATE|TIME_MINUTES|TIME_SECONDS)+"\r\n";
   x+="account_mode="+string((ENUM_ACCOUNT_TRADE_MODE)AccountInfoInteger(ACCOUNT_TRADE_MODE)==ACCOUNT_TRADE_MODE_DEMO?"DEMO":"NON_DEMO")+"\r\n";
   x+="terminal_trade_allowed="+IntegerToString((int)TerminalInfoInteger(TERMINAL_TRADE_ALLOWED))+"\r\n";
   x+="mql_trade_allowed="+IntegerToString((int)MQLInfoInteger(MQL_TRADE_ALLOWED))+"\r\n";
   x+="terminal_dlls_allowed="+IntegerToString((int)TerminalInfoInteger(TERMINAL_DLLS_ALLOWED))+"\r\n";
   x+="magic="+IntegerToString((int)InpV49Magic)+"\r\n";
   x+="market_days="+IntegerToString(g_v49_market_days)+"\r\nround_trips="+IntegerToString(g_v49_round_trips)+"\r\n";
   x+="requests="+IntegerToString(g_v49_requests)+"\r\nrejects="+IntegerToString(g_v49_rejects)+"\r\n";
   x+="duplicate_events="+IntegerToString(g_v49_duplicate_events)+"\r\ndirection_mismatches="+IntegerToString(g_v49_direction_mismatches)+"\r\n";
   x+="open_pending="+IntegerToString(g_v49_open_pending?1:0)+"\r\nclose_pending="+IntegerToString(g_v49_close_pending?1:0)+"\r\n";
   x+="halted="+IntegerToString(g_v49_halted?1:0)+"\r\nhalt_reason="+g_v49_halt_reason+"\r\n";
   x+="accept_new="+IntegerToString(g_v49_accept_new?1:0)+"\r\n";
   x+="virtual_open="+IntegerToString(B[ix].open?1:0)+"\r\nvirtual_direction="+IntegerToString(B[ix].direction)+"\r\n";
   x+="owned_positions="+IntegerToString(owned)+"\r\nbroker_direction="+IntegerToString(broker_dir)+"\r\nbroker_volume="+DoubleToString(broker_vol,6)+"\r\n";
   x+="run_id="+g_run_id+"\r\nrun_folder="+g_run_folder+"\r\n";
   x+="real_money_authorized=0\r\n";
   FileWriteString(h,x); FileClose(h);
}

void V49WriteFinal(const string verdict,const string reason)
{
   if(g_v49_final_written) return;
   int h=FileOpen(g_v49_final_file,FILE_WRITE|FILE_TXT|FILE_ANSI|FILE_COMMON);
   if(h==INVALID_HANDLE) return;
   string x="schema=v49_demo_rehearsal_final_v1\r\n";
   x+="verdict="+verdict+"\r\nreason="+reason+"\r\n";
   x+="market_days="+IntegerToString(g_v49_market_days)+"\r\nround_trips="+IntegerToString(g_v49_round_trips)+"\r\n";
   x+="requests="+IntegerToString(g_v49_requests)+"\r\nrejects="+IntegerToString(g_v49_rejects)+"\r\n";
   x+="duplicate_events="+IntegerToString(g_v49_duplicate_events)+"\r\ndirection_mismatches="+IntegerToString(g_v49_direction_mismatches)+"\r\n";
   x+="halted="+IntegerToString(g_v49_halted?1:0)+"\r\nhalt_reason="+g_v49_halt_reason+"\r\n";
   x+="run_id="+g_run_id+"\r\nreal_money_authorized=0\r\n";
   FileWriteString(h,x); FileClose(h);
   g_v49_final_written=true; g_v49_accept_new=false;
   V49Notify("V49 FINAL "+verdict+" days="+IntegerToString(g_v49_market_days)+" roundtrips="+IntegerToString(g_v49_round_trips));
}

void V49MaybeFinalize()
{
   int calendar_days=(int)((TimeLocal()-g_v49_local_start)/86400)+1;
   bool sample=(g_v49_market_days>=InpV49MinMarketDays && g_v49_round_trips>=InpV49MinRoundTrips);
   if(sample) g_v49_accept_new=false;
   ulong ticket=0; int d=0; double v=0.0; int owned=V49OwnedPositionCount(ticket,d,v);
   const int ci=23,bi=3,ix=BI(ci,bi);
   bool flat=(!B[ix].open && owned==0 && !g_v49_open_pending && !g_v49_close_pending);
   if(!flat) return;

   if(sample)
   {
      bool reject_ok=(g_v49_requests==0 || g_v49_rejects*5<=g_v49_requests);
      if(!g_v49_halted && g_v49_duplicate_events==0 && g_v49_direction_mismatches==0 && reject_ok)
         V49WriteFinal("LIVE_CANDIDATE_READY","one_shot_demo_rehearsal_pass");
      else V49WriteFinal("HOLD","execution_or_reconciliation_failure");
   }
   else if(calendar_days>=InpV49HardCalendarDays)
   {
      V49WriteFinal("INSUFFICIENT_EXECUTION_SAMPLE","hard_calendar_stop_before_minimum_sample");
   }
}

bool V49InitExecution()
{
   if((ENUM_ACCOUNT_TRADE_MODE)AccountInfoInteger(ACCOUNT_TRADE_MODE)!=ACCOUNT_TRADE_MODE_DEMO) return false;
   if(_Symbol!="XAUUSDm" || _Period!=PERIOD_M15) return false;
   if(!TerminalInfoInteger(TERMINAL_TRADE_ALLOWED) || !MQLInfoInteger(MQL_TRADE_ALLOWED)) return false;
   if(TerminalInfoInteger(TERMINAL_DLLS_ALLOWED)) return false;
   if(V49ForeignSymbolPositions()>0) return false;
   ulong t=0; int d=0; double v=0.0;
   if(V49OwnedPositionCount(t,d,v)>1) return false;
   g_v49_trade.SetExpertMagicNumber((ulong)InpV49Magic);
   g_v49_trade.SetDeviationInPoints(InpV49MaxDeviationPoints);
   g_v49_trade.SetTypeFillingBySymbol(_Symbol);
   g_v49_local_start=TimeLocal();
   FolderCreate("mt5_quant\\v49",FILE_COMMON);
   V49AppendCsv(g_v49_events_file,"time,action,direction,virtual_volume,broker_volume,request_price,result_price,sl,tp,call_ok,retcode,retcode_desc,order,deal");
   V49AppendCsv(g_v49_transactions_file,"time,type,deal,order,symbol,price,volume,entry,deal_type");
   V49Notify("V49 START DEMO XAUUSDm M15 breadth4");
   return true;
}

bool CreateHandles()
{'''
    text = replace_once(text, funcs_marker, funcs)

    old_trade_guard = 'if(TerminalInfoInteger(TERMINAL_TRADE_ALLOWED)){ V48WriteInitDiagnostic("REFUSED","terminal_auto_trading_on"); Print("V49 DEMO-REHEARSAL REFUSED: terminal AutoTrading must be OFF"); return INIT_FAILED; }'
    if old_trade_guard not in text:
        old_trade_guard = 'if(TerminalInfoInteger(TERMINAL_TRADE_ALLOWED)){ V48WriteInitDiagnostic("REFUSED","terminal_auto_trading_on"); Print("V48 DEMO-PAPER REFUSED: terminal AutoTrading must be OFF"); return INIT_FAILED; }'
    new_trade_guard = 'if(!TerminalInfoInteger(TERMINAL_TRADE_ALLOWED) || !MQLInfoInteger(MQL_TRADE_ALLOWED)){ V48WriteInitDiagnostic("REFUSED","demo_autotrading_not_enabled"); Print("V49 DEMO-REHEARSAL REFUSED: AutoTrading must be enabled for DEMO broker execution"); return INIT_FAILED; }'
    text = replace_once(text, old_trade_guard, new_trade_guard)

    init_marker = 'WriteManifest(); WriteLatest(); WritePaperStatus(); UpdatePaperDashboard(); EventSetTimer(30);'
    init_repl = 'if(!V49InitExecution()){ V48WriteInitDiagnostic("REFUSED","v49_execution_preflight_failed"); return INIT_FAILED; }\n   WriteManifest(); WriteLatest(); WritePaperStatus(); V49WriteStatus(); UpdatePaperDashboard(); EventSetTimer(30);\n   g_v49_init_ready=true;'
    text = replace_once(text, init_marker, init_repl)

    deinit_marker = 'EventKillTimer();\n   SaveAdaptiveState(); WritePaperStatus(); WriteManifest(); WriteLatest();'
    deinit_repl = 'EventKillTimer();\n   if(g_v49_init_ready){ SaveAdaptiveState(); WritePaperStatus(); V49WriteStatus(); WriteManifest(); WriteLatest(); }'
    text = replace_once(text, deinit_marker, deinit_repl)

    timer_marker = 'void OnTimer()\n{\n   SaveAdaptiveState(); WritePaperStatus(); WriteManifest(); WriteLatest(); UpdatePaperDashboard();\n}'
    timer_repl = 'void OnTimer()\n{\n   if(g_v49_init_ready){ V49SyncBrokerWithVirtual(); V49MaybeFinalize(); SaveAdaptiveState(); WritePaperStatus(); V49WriteStatus(); WriteManifest(); WriteLatest(); UpdatePaperDashboard(); }\n}'
    text = replace_once(text, timer_marker, timer_repl)

    tick_marker = 'ProcessExits(tick);\n   UpdatePaperDashboard();\n   g_prev_tick=tick; g_have_prev_tick=true;'
    tick_repl = 'ProcessExits(tick);\n   V49ObserveMarketDay(tick.time);\n   V49SyncBrokerWithVirtual();\n   V49MaybeFinalize();\n   V49WriteStatus();\n   UpdatePaperDashboard();\n   g_prev_tick=tick; g_have_prev_tick=true;'
    text = replace_once(text, tick_marker, tick_repl)

    text += r'''

void OnTradeTransaction(const MqlTradeTransaction &trans,const MqlTradeRequest &request,const MqlTradeResult &result)
{
   if(trans.type!=TRADE_TRANSACTION_DEAL_ADD || trans.deal==0) return;
   if(!HistoryDealSelect(trans.deal)) return;
   if((long)HistoryDealGetInteger(trans.deal,DEAL_MAGIC)!=InpV49Magic) return;
   string symbol=HistoryDealGetString(trans.deal,DEAL_SYMBOL);
   if(symbol!=_Symbol) return;
   long entry=HistoryDealGetInteger(trans.deal,DEAL_ENTRY);
   long dtype=HistoryDealGetInteger(trans.deal,DEAL_TYPE);
   double price=HistoryDealGetDouble(trans.deal,DEAL_PRICE);
   double volume=HistoryDealGetDouble(trans.deal,DEAL_VOLUME);
   string row=TimeToString(TimeLocal(),TIME_DATE|TIME_MINUTES|TIME_SECONDS)+","+IntegerToString((int)trans.type)+","+
      IntegerToString((int)trans.deal)+","+IntegerToString((int)trans.order)+","+symbol+","+DoubleToString(price,_Digits)+","+
      DoubleToString(volume,6)+","+IntegerToString((int)entry)+","+IntegerToString((int)dtype);
   V49AppendCsv(g_v49_transactions_file,row);

   if(entry==DEAL_ENTRY_IN)
   {
      g_v49_open_pending=false;
      V49Notify("V49 DEMO OPEN confirmed "+symbol+" @ "+DoubleToString(price,_Digits));
   }
   if(entry==DEAL_ENTRY_OUT || entry==DEAL_ENTRY_OUT_BY)
   {
      g_v49_close_pending=false;
      ulong t=0; int d=0; double v=0.0;
      if(V49OwnedPositionCount(t,d,v)==0)
      {
         g_v49_round_trips++;
         const int ci=23,bi=3,ix=BI(ci,bi);
         if(B[ix].open){ g_v49_server_exit_wait=true; g_v49_server_exit_time=TimeLocal(); }
         V49Notify("V49 DEMO CLOSE confirmed "+symbol+" @ "+DoubleToString(price,_Digits)+" roundtrips="+IntegerToString(g_v49_round_trips));
         V49MaybeFinalize();
      }
   }
   V49WriteStatus();
}
'''

    required = (
        '#include <Trade/Trade.mqh>',
        'ACCOUNT_TRADE_MODE_DEMO',
        'CTrade g_v49_trade',
        'V49SyncBrokerWithVirtual',
        'g_v49_open_pending',
        'g_v49_close_pending',
        'OnTradeTransaction',
        'SendNotification',
        'V49WriteFinal("LIVE_CANDIDATE_READY"',
        'real_money_authorized=0',
        'v46_hl10_thr0p05_breadth4',
    )
    for token in required:
        if token not in text:
            raise RuntimeError(f"V49 required token missing: {token}")

    forbidden = ('ACCOUNT_TRADE_MODE_REAL)==', 'real_money_authorized=1', 'Martingale', 'martingale')
    for token in forbidden:
        if token in text:
            raise RuntimeError(f"V49 forbidden token present: {token}")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8", newline="\n")
    digest = sha256(output)
    print(f"V49 source built sha256={digest} parent_sha256={actual} path={output}")
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
