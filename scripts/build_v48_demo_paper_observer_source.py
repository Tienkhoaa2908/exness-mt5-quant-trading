#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

EXPECTED_PARENT_SHA = "7685dd83f576841532970d43e21fda80c896c407f313edae1fb12b0b39387e44"
EXPECTED_OUTPUT_SHA = "ecb78c603d3426396f3d3f56f35dcdf1b3a0983090a071e2972b6bd9ab9068aa"
FORBIDDEN = ("OrderSend(", "OrderSendAsync(", "CTrade", "trade.Buy(", "trade.Sell(", "#import")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def replace_once(text: str, old: str, new: str) -> str:
    n = text.count(old)
    if n != 1:
        raise RuntimeError(f"expected exactly one occurrence, found={n}: {old[:140]!r}")
    return text.replace(old, new, 1)


def build(source: Path, output: Path) -> str:
    actual_parent = sha256(source)
    if actual_parent != EXPECTED_PARENT_SHA:
        raise RuntimeError(f"V47 parent SHA mismatch expected={EXPECTED_PARENT_SHA} actual={actual_parent}")

    text = source.read_text(encoding="utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
    for bad in FORBIDDEN:
        if bad in text:
            raise RuntimeError(f"forbidden native/external execution path in parent: {bad}")

    text = replace_once(text,
        '#define MT5Q_RELEASE_ID "v47_forward_regime_shadow_v1"',
        '#define MT5Q_RELEASE_ID "v48_demo_paper_forward_v2"')
    text = replace_once(text,
        'input string InpOutputTag = "v47_forward_regime_shadow_v1";',
        'input string InpOutputTag = "v48_demo_paper_forward_v2";')
    text = replace_once(text,
        'input string InpAdaptiveStateFile = "mt5_quant\\\\inputs\\\\v30_ml_dl_feature_lake_state.csv";',
        'input string InpAdaptiveStateFile = "mt5_quant\\\\paper\\\\v48_demo_paper_state.csv";')
    text = replace_once(text,
        'string g_latest_file="mt5_quant\\\\ML_DL_FEATURE_LAKE_LATEST.txt";',
        'string g_latest_file="mt5_quant\\\\paper\\\\V48_DEMO_PAPER_LATEST.txt";\nstring g_paper_status_file="mt5_quant\\\\paper\\\\V48_DEMO_PAPER_STATUS.txt";\nstring g_paper_init_file="mt5_quant\\\\paper\\\\V48_DEMO_PAPER_INIT.txt";\ndatetime g_paper_session_start=0;')

    text = replace_once(text,
        'x+="format=mt5_quant_v47_forward_regime_shadow_v1\\r\\n";',
        'x+="format=mt5_quant_v48_demo_paper_forward_v2\\r\\n";')
    text = replace_once(text,
        'x+="source_file=V47ForwardRegimeShadowLab.mq5\\r\\n";',
        'x+="source_file=V48DemoPaperObserver.mq5\\r\\n";')
    text = replace_once(text,
        'x+="tester_only=1\\r\\nnative_broker_orders=0\\r\\nexternal_broker_orders=0\\r\\n";',
        'x+="tester_only=0\\r\\ndemo_paper_only=1\\r\\nreal_account_forbidden=1\\r\\nterminal_trade_permission_required_off=1\\r\\nterminal_dll_permission_required_off=1\\r\\nnative_broker_orders=0\\r\\nexternal_broker_orders=0\\r\\n";')
    text = replace_once(text,
        'x+="v47_forward_regime_shadow=1\\r\\nv47_primary_logic_changed=0\\r\\nv47_shadow_adx_di_only=1\\r\\nv47_live_authorized=0\\r\\n";',
        'x+="v47_forward_regime_shadow=1\\r\\nv47_primary_logic_changed=0\\r\\nv47_shadow_adx_di_only=1\\r\\nv47_live_authorized=0\\r\\n";\n   x+="v48_demo_paper_forward=1\\r\\nv48_dashboard=1\\r\\nv48_primary_logic_changed=0\\r\\nv48_primary_candidate=v46_hl10_thr0p05_breadth4\\r\\nv48_paper_book=usd40_r1p0_cent_continuous\\r\\nv48_broker_orders=0\\r\\nv48_live_authorized=0\\r\\n";')

    status_marker = 'bool CreateHandles()\n{'
    status_block = r'''int V48HealthyCount()
{
   int healthy=0;
   for(int e=0;e<EXPERT_COUNT;++e) if(g_ewma_hl10[e]>=0.05) healthy++;
   return healthy;
}

string V48DirectionText(const int d)
{
   if(d>0) return "LONG";
   if(d<0) return "SHORT";
   return "FLAT";
}

void V48WriteInitDiagnostic(const string stage,const string reason)
{
   int h=FileOpen(g_paper_init_file,FILE_WRITE|FILE_TXT|FILE_ANSI|FILE_COMMON);
   if(h==INVALID_HANDLE) return;
   string x="";
   x+="schema=v48_demo_paper_init_v2\r\n";
   x+="updated="+TimeToString(TimeCurrent(),TIME_DATE|TIME_MINUTES|TIME_SECONDS)+"\r\n";
   x+="stage="+stage+"\r\nreason="+reason+"\r\n";
   x+="symbol="+_Symbol+"\r\nperiod="+PeriodText()+"\r\n";
   x+="account_trade_mode="+IntegerToString((int)AccountInfoInteger(ACCOUNT_TRADE_MODE))+"\r\n";
   x+="account_server="+AccountInfoString(ACCOUNT_SERVER)+"\r\n";
   x+="terminal_connected="+IntegerToString((int)TerminalInfoInteger(TERMINAL_CONNECTED))+"\r\n";
   x+="terminal_trade_allowed="+IntegerToString((int)TerminalInfoInteger(TERMINAL_TRADE_ALLOWED))+"\r\n";
   x+="mql_trade_allowed="+IntegerToString((int)MQLInfoInteger(MQL_TRADE_ALLOWED))+"\r\n";
   x+="terminal_dlls_allowed="+IntegerToString((int)TerminalInfoInteger(TERMINAL_DLLS_ALLOWED))+"\r\n";
   x+="mql_dlls_allowed="+IntegerToString((int)MQLInfoInteger(MQL_DLLS_ALLOWED))+"\r\n";
   x+="broker_orders=0\r\nlive_authorized=0\r\n";
   FileWriteString(h,x); FileClose(h);
}

double V48PaperEquity(double &px,double &openR,double &openPnl)
{
   const int ci=23, bi=3, ix=BI(ci,bi);
   px=0.0; openR=0.0; openPnl=0.0;
   MqlTick tick;
   if(B[ix].open && SymbolInfoTick(_Symbol,tick))
   {
      px=(B[ix].direction>0?tick.bid:tick.ask);
      openR=PriceR(B[ix],px);
      openPnl=UnrealizedPnl(B[ix],px);
   }
   return B[ix].balance+openPnl;
}

void UpdatePaperDashboard()
{
   const int ci=23, bi=3, ix=BI(ci,bi);
   double px=0.0,openR=0.0,openPnl=0.0;
   double equity=V48PaperEquity(px,openR,openPnl);
   string pos=V48DirectionText(B[ix].direction);
   string x="V48 PAPER BOT | "+_Symbol+" "+PeriodText()+"\n";
   x+="DEMO FEED / VIRTUAL EXECUTION | BROKER ORDERS 0\n";
   x+="State: RUNNING   Breadth: "+IntegerToString(V48HealthyCount())+"/5\n";
   x+="Balance: $"+DoubleToString(B[ix].balance,2)+"   Equity: $"+DoubleToString(equity,2)+"\n";
   x+="Max DD: "+DoubleToString(B[ix].max_mtm_dd_pct,2)+"%   Month trades: "+IntegerToString((int)B[ix].trades)+"\n";
   x+="Position: "+pos;
   if(B[ix].open)
   {
      x+="   Open R: "+DoubleToString(openR,2)+"R   PnL: $"+DoubleToString(openPnl,2)+"\n";
      x+="Entry: "+DoubleToString(B[ix].entry,_Digits)+"   Now: "+DoubleToString(px,_Digits)+"\n";
      x+="SL: "+DoubleToString(B[ix].stop,_Digits)+"   TP: "+DoubleToString(B[ix].tp,_Digits);
   }
   else x+="\nWaiting for breadth4 opportunity";
   x+="\nHeartbeat: "+TimeToString(TimeCurrent(),TIME_DATE|TIME_MINUTES|TIME_SECONDS);
   x+="\nREAL MONEY AUTHORIZED: NO";
   Comment(x);
}

void WritePaperStatus()
{
   const int ci=23, bi=3, ix=BI(ci,bi);
   double px=0.0,openR=0.0,openPnl=0.0;
   double equity=V48PaperEquity(px,openR,openPnl);
   int h=FileOpen(g_paper_status_file,FILE_WRITE|FILE_TXT|FILE_ANSI|FILE_COMMON);
   if(h==INVALID_HANDLE) return;
   string x="";
   x+="schema=v48_demo_paper_status_v2\r\n";
   x+="updated="+TimeToString(TimeCurrent(),TIME_DATE|TIME_MINUTES|TIME_SECONDS)+"\r\n";
   x+="session_start="+TimeToString(g_paper_session_start,TIME_DATE|TIME_MINUTES|TIME_SECONDS)+"\r\n";
   x+="symbol="+_Symbol+"\r\nperiod="+PeriodText()+"\r\n";
   x+="account_mode=DEMO\r\nreal_account_forbidden=1\r\nbroker_orders=0\r\nlive_authorized=0\r\n";
   x+="terminal_trade_allowed="+IntegerToString((int)TerminalInfoInteger(TERMINAL_TRADE_ALLOWED))+"\r\n";
   x+="mql_trade_allowed="+IntegerToString((int)MQLInfoInteger(MQL_TRADE_ALLOWED))+"\r\n";
   x+="terminal_dlls_allowed="+IntegerToString((int)TerminalInfoInteger(TERMINAL_DLLS_ALLOWED))+"\r\n";
   x+="mql_dlls_allowed="+IntegerToString((int)MQLInfoInteger(MQL_DLLS_ALLOWED))+"\r\n";
   x+="candidate="+C[ci].name+"\r\nbook="+BookName(bi)+"\r\n";
   x+="healthy_hl10_count="+IntegerToString(V48HealthyCount())+"\r\n";
   for(int e=0;e<EXPERT_COUNT;++e) x+="hl10_expert_"+IntegerToString(e)+"="+DoubleToString(g_ewma_hl10[e],10)+"\r\n";
   x+="balance="+DoubleToString(B[ix].balance,6)+"\r\n";
   x+="equity="+DoubleToString(equity,6)+"\r\n";
   x+="unrealized_pnl="+DoubleToString(openPnl,6)+"\r\n";
   x+="current_price="+DoubleToString(px,_Digits)+"\r\n";
   x+="max_mtm_dd_pct="+DoubleToString(B[ix].max_mtm_dd_pct,4)+"\r\n";
   x+="closed_trades_this_month="+IntegerToString((int)B[ix].trades)+"\r\n";
   x+="sum_r_this_month="+DoubleToString(B[ix].sum_r,6)+"\r\n";
   x+="position_open="+IntegerToString(B[ix].open?1:0)+"\r\n";
   x+="direction="+V48DirectionText(B[ix].direction)+"\r\n";
   x+="entry="+DoubleToString(B[ix].entry,_Digits)+"\r\n";
   x+="stop="+DoubleToString(B[ix].stop,_Digits)+"\r\n";
   x+="tp="+DoubleToString(B[ix].tp,_Digits)+"\r\n";
   x+="volume="+DoubleToString(B[ix].volume,4)+"\r\n";
   x+="open_r="+DoubleToString(openR,6)+"\r\n";
   x+="run_id="+g_run_id+"\r\nrun_folder="+g_run_folder+"\r\n";
   FileWriteString(h,x); FileClose(h);
}

bool CreateHandles()
{'''
    text = replace_once(text, status_marker, status_block)

    old_oninit = r'''int OnInit()
{
   if(!MQLInfoInteger(MQL_TESTER)){ Print("MlDlFeatureLakeV1 TESTER-ONLY"); return INIT_FAILED; }
   if(InpAtrBars<=0 || InpMaxSpreadAtrFraction<0) return INIT_PARAMETERS_INCORRECT;
   BuildCatalog(); LoadAdaptiveState(); if(!V34InitTape()) return INIT_FAILED; if(!CreateHandles()) return INIT_FAILED;
   ResetMonthState();
   g_run_id=MakeRunId(); g_run_folder="mt5_quant\\runs\\"+g_run_id; FolderCreate(g_run_folder,FILE_COMMON);
   g_monthly_summary_file=MonthlySummaryFile(); g_trades_file=TradesFile(); g_bar_features_file=BarFeaturesFile(); g_manifest_file=ManifestFile(); EnsureFiles();
   PrintFormat("V47_FORWARD_REGIME_SHADOW START %s %s candidates=%d books=%d",_Symbol,PeriodText(),CANDIDATE_COUNT,BOOK_COUNT);
   return INIT_SUCCEEDED;
}'''
    new_oninit = r'''int OnInit()
{
   V48WriteInitDiagnostic("ENTER","");
   if(MQLInfoInteger(MQL_TESTER)){ V48WriteInitDiagnostic("REFUSED","tester_mode"); Print("V48 DEMO-PAPER refuses tester mode; use frozen V46 for historical tests"); return INIT_FAILED; }
   if((ENUM_ACCOUNT_TRADE_MODE)AccountInfoInteger(ACCOUNT_TRADE_MODE)!=ACCOUNT_TRADE_MODE_DEMO){ V48WriteInitDiagnostic("REFUSED","real_or_non_demo_account"); Print("V48 DEMO-PAPER REFUSED: DEMO ACCOUNT REQUIRED"); return INIT_FAILED; }
   if(TerminalInfoInteger(TERMINAL_TRADE_ALLOWED)){ V48WriteInitDiagnostic("REFUSED","terminal_auto_trading_on"); Print("V48 DEMO-PAPER REFUSED: terminal AutoTrading must be OFF"); return INIT_FAILED; }
   if(TerminalInfoInteger(TERMINAL_DLLS_ALLOWED)){ V48WriteInitDiagnostic("REFUSED","terminal_dll_permission_on"); Print("V48 DEMO-PAPER REFUSED: terminal DLL permission must be OFF"); return INIT_FAILED; }
   if(InpAtrBars<=0 || InpMaxSpreadAtrFraction<0){ V48WriteInitDiagnostic("REFUSED","invalid_parameters"); return INIT_PARAMETERS_INCORRECT; }
   BuildCatalog(); LoadAdaptiveState();
   if(!V34InitTape()){ V48WriteInitDiagnostic("REFUSED","v34_tape_init_failed"); return INIT_FAILED; }
   if(!CreateHandles()){ V48WriteInitDiagnostic("REFUSED","indicator_handle_init_failed"); return INIT_FAILED; }
   ResetMonthState();
   g_paper_session_start=TimeCurrent();
   g_run_id=MakeRunId(); g_run_folder="mt5_quant\\runs\\"+g_run_id; FolderCreate(g_run_folder,FILE_COMMON);
   g_monthly_summary_file=MonthlySummaryFile(); g_trades_file=TradesFile(); g_bar_features_file=BarFeaturesFile(); g_manifest_file=ManifestFile(); EnsureFiles();
   WriteManifest(); WriteLatest(); WritePaperStatus(); UpdatePaperDashboard(); EventSetTimer(30);
   V48WriteInitDiagnostic("READY","");
   PrintFormat("V48_DEMO_PAPER START %s %s candidates=%d books=%d",_Symbol,PeriodText(),CANDIDATE_COUNT,BOOK_COUNT);
   return INIT_SUCCEEDED;
}'''
    text = replace_once(text, old_oninit, new_oninit)

    old_deinit = r'''void OnDeinit(const int reason)
{
   if(g_have_prev_tick && g_month_key>0) FinalizeMonth(g_prev_tick);
   SaveAdaptiveState(); WriteManifest(); WriteLatest();
   Rel(hEma10); Rel(hEma20); Rel(hEma50); Rel(hEma200); Rel(hEma300); Rel(hAtr); Rel(hAtr50);
   Rel(hH1Ema50); Rel(hH1Ema200); Rel(hRsi2); Rel(hRsi14); Rel(hMacd); Rel(hAdx); Rel(hBands);
   if(g_v34_tape_handle!=INVALID_HANDLE){ FileClose(g_v34_tape_handle); g_v34_tape_handle=INVALID_HANDLE; }
   PrintFormat("V47_FORWARD_REGIME_SHADOW DONE months=%d",(int)g_months_written);
}'''
    new_deinit = r'''void OnDeinit(const int reason)
{
   EventKillTimer();
   SaveAdaptiveState(); WritePaperStatus(); WriteManifest(); WriteLatest();
   V48WriteInitDiagnostic("STOPPED",IntegerToString(reason));
   Rel(hEma10); Rel(hEma20); Rel(hEma50); Rel(hEma200); Rel(hEma300); Rel(hAtr); Rel(hAtr50);
   Rel(hH1Ema50); Rel(hH1Ema200); Rel(hRsi2); Rel(hRsi14); Rel(hMacd); Rel(hAdx); Rel(hBands);
   if(g_v34_tape_handle!=INVALID_HANDLE){ FileClose(g_v34_tape_handle); g_v34_tape_handle=INVALID_HANDLE; }
   Comment("");
   PrintFormat("V48_DEMO_PAPER STOP reason=%d months=%d",reason,(int)g_months_written);
}

void OnTimer()
{
   SaveAdaptiveState(); WritePaperStatus(); WriteManifest(); WriteLatest(); UpdatePaperDashboard();
}'''
    text = replace_once(text, old_deinit, new_deinit)
    text = replace_once(text,
        '   ProcessExits(tick);\n   g_prev_tick=tick; g_have_prev_tick=true;',
        '   ProcessExits(tick);\n   UpdatePaperDashboard();\n   g_prev_tick=tick; g_have_prev_tick=true;')

    required = (
        '#define MT5Q_RELEASE_ID "v48_demo_paper_forward_v2"',
        'InpAdaptiveStateFile = "mt5_quant\\\\paper\\\\v48_demo_paper_state.csv"',
        'ACCOUNT_TRADE_MODE_DEMO',
        'TERMINAL_TRADE_ALLOWED',
        'TERMINAL_DLLS_ALLOWED',
        'V48 DEMO-PAPER REFUSED: DEMO ACCOUNT REQUIRED',
        'V48WriteInitDiagnostic',
        'UpdatePaperDashboard',
        'Comment(x)',
        'demo_paper_only=1',
        'real_account_forbidden=1',
        'v48_dashboard=1',
        'v48_broker_orders=0',
        'v48_live_authorized=0',
        'EventSetTimer(30)',
        'void OnTimer()',
        'V48_DEMO_PAPER_STATUS.txt',
        'V48_DEMO_PAPER_INIT.txt',
        '#define CANDIDATE_COUNT 26',
        'v46_hl10_thr0p05_breadth4',
    )
    for token in required:
        if token not in text:
            raise RuntimeError(f"V48 required token missing: {token}")

    # Validate generated MQL semantics instead of relying on Python-source whitespace.
    on_tick_start = text.find('void OnTick()')
    if on_tick_start < 0:
        raise RuntimeError('V48 generated OnTick missing')
    on_tick = text[on_tick_start:]
    ix_exits = on_tick.find('ProcessExits(tick);')
    ix_dash = on_tick.find('UpdatePaperDashboard();')
    ix_prev = on_tick.find('g_prev_tick=tick')
    if not (0 <= ix_exits < ix_dash < ix_prev):
        raise RuntimeError('V48 generated OnTick dashboard control flow invalid')

    on_timer_start = text.find('void OnTimer()')
    if on_timer_start < 0 or on_timer_start >= on_tick_start:
        raise RuntimeError('V48 generated OnTimer missing or misplaced')
    on_timer = text[on_timer_start:on_tick_start]
    if 'UpdatePaperDashboard();' not in on_timer:
        raise RuntimeError('V48 generated OnTimer dashboard control flow invalid')

    on_init_start = text.find('int OnInit()')
    on_deinit_start = text.find('void OnDeinit')
    if on_init_start < 0 or on_deinit_start <= on_init_start:
        raise RuntimeError('V48 generated OnInit missing or misplaced')
    on_init = text[on_init_start:on_deinit_start]
    ix_init_dash = on_init.find('UpdatePaperDashboard();')
    ix_timer_set = on_init.find('EventSetTimer(30);')
    if not (0 <= ix_init_dash < ix_timer_set):
        raise RuntimeError('V48 generated OnInit dashboard control flow invalid')

    if 'FinalizeMonth(g_prev_tick);' in text[text.index('void OnDeinit'):text.index('void OnTick')]:
        raise RuntimeError("V48 OnDeinit must not fabricate an EOM close")

    for bad in FORBIDDEN:
        if bad in text:
            raise RuntimeError(f"forbidden native/external execution path introduced: {bad}")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(text.replace("\n", "\r\n").encode("utf-8"))
    actual = sha256(output)
    if actual != EXPECTED_OUTPUT_SHA:
        raise RuntimeError(f"V48 output SHA mismatch expected={EXPECTED_OUTPUT_SHA} actual={actual}")
    print(f"V48 demo-paper source PASS sha256={actual} path={output}")
    return actual


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True)
    ap.add_argument("--output", required=True)
    a = ap.parse_args()
    build(Path(a.source), Path(a.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
