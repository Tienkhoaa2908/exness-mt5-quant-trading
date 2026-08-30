#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

CANDIDATE = "v52_b4_or_b3_trend_bos"
FIXED_LOT = 0.01


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        raise RuntimeError(f"V58 {label} drifted expected=1 actual={n}")
    return text.replace(old, new, 1)


def transform(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    text = replace_once(
        text,
        'input int InpV57StrictConfluenceScore = 6;',
        '''input int InpV57StrictConfluenceScore = 6;
input double InpV58PullbackRsi2MaxLong = 80.0;
input double InpV58PullbackRsi2MinShort = 20.0;
input double InpV58MaxSpreadCash = 0.75;
input double InpV58MaxSpreadRiskPct = 5.0;
input double InpV58MaxMarginUsagePct = 95.0;''',
        "inputs",
    )
    text = replace_once(text, 'input long InpV55Magic = 570057;', 'input long InpV55Magic = 580058;', "magic")
    text = text.replace("v57_fixed001_trend_smc", "v58_fixed001_pullback_trend_cost")

    text = replace_once(
        text,
        'string g_v57_eval_file="mt5_quant\\\\v58_fixed001_pullback_trend_cost\\\\V57_ENTRY_EVAL.csv";',
        '''string g_v57_eval_file="mt5_quant\\\\v58_fixed001_pullback_trend_cost\\\\V57_ENTRY_EVAL.csv";
string g_v58_eval_file="mt5_quant\\\\v58_fixed001_pullback_trend_cost\\\\V58_ENTRY_EVAL.csv";
double g_v58_last_risk_cash=0.0;
double g_v58_last_spread_cash=0.0;
double g_v58_last_spread_points=0.0;
int g_v58_last_direction=0;''',
        "globals",
    )

    text = replace_once(
        text,
        'margin_cash>free_margin*(InpV55MaxMarginUsagePct/100.0)',
        'margin_cash>free_margin*(InpV58MaxMarginUsagePct/100.0)',
        "fixed-lot margin threshold",
    )

    marker = "\nvoid V57EnsureEvalFile()\n"
    if text.count(marker) != 1:
        raise RuntimeError(f"V58 helper insertion marker drifted actual={text.count(marker)}")

    helper = r'''
int V58FastTrendDir(const ENUM_TIMEFRAMES tf,const int fast_period,const int slow_period)
{
   MqlRates r[];
   ArraySetAsSeries(r,true);
   int need=MathMax(120,slow_period*5+10);
   int n=CopyRates(_Symbol,tf,1,need,r);
   if(n<slow_period+10) return 0;
   double ef=V57EMA(r,n,fast_period,0);
   double es=V57EMA(r,n,slow_period,0);
   double ef_prev=V57EMA(r,n,fast_period,3);
   if(ef<=0.0 || es<=0.0 || ef_prev<=0.0) return 0;
   if(ef>es && ef>ef_prev && r[0].close>ef) return 1;
   if(ef<es && ef<ef_prev && r[0].close<ef) return -1;
   return 0;
}

double V58SpreadCashNow(const int direction,const double lot,double &spread_points)
{
   spread_points=-1.0;
   MqlTick t;
   if(!SymbolInfoTick(_Symbol,t) || _Point<=0.0 || lot<=0.0) return -1.0;
   spread_points=(t.ask-t.bid)/_Point;
   if(spread_points<0.0) return -1.0;
   ENUM_ORDER_TYPE ot=(direction>0 ? ORDER_TYPE_BUY : ORDER_TYPE_SELL);
   double pnl=0.0;
   double entry=(direction>0 ? t.ask : t.bid);
   double exitp=(direction>0 ? t.bid : t.ask);
   if(!OrderCalcProfit(ot,_Symbol,lot,entry,exitp,pnl)) return -1.0;
   return MathAbs(pnl);
}

bool V58SpreadCostOk()
{
   double sp=0.0;
   double cash=V58SpreadCashNow(g_v58_last_direction,InpV57FixedLot,sp);
   g_v58_last_spread_points=sp;
   g_v58_last_spread_cash=cash;
   if(cash<0.0 || sp<0.0) return false;
   double risk_cap=(g_v58_last_risk_cash>0.0
      ? g_v58_last_risk_cash*(InpV58MaxSpreadRiskPct/100.0)
      : InpV58MaxSpreadCash);
   double allowed=MathMin(InpV58MaxSpreadCash,risk_cap);
   return cash<=allowed+1e-9;
}

void V58EnsureEvalFile()
{
   if(FileIsExist(g_v58_eval_file,FILE_COMMON)) return;
   V55AppendCsv(g_v58_eval_file,
      "time,direction,fixed_lot,request_price,stop,tp,feature_ready,trend_h1,trend_h4,"
      "fast_trend_h1,fast_trend_m15,structure_dir,bos_choch_dir,fvg_dir,liquidity_sweep_dir,"
      "adx,plus_di,minus_di,rsi2,rsi14,macd_hist,score,risk_cash_fixed001,risk_pct_equity,"
      "margin_cash,spread_points_entry,spread_cash_entry,spread_risk_pct,lot_ok,"
      "gate_baseline,gate_pullback80,gate_pullback70,gate_pullback80_no_opposite,"
      "gate_fast_h1_pullback80,gate_fast_both_pullback80,gate_fast_both_pullback80_no_opposite,"
      "allow_actual");
}

bool V58EvaluateEntry(const int ix)
{
   V58EnsureEvalFile();
   V57EntryFeatures f;
   bool ready=V57BuildFeatures(ix,f);
   int d=B[ix].direction;
   int fast_h1=V58FastTrendDir(PERIOD_H1,20,50);
   int fast_m15=V58FastTrendDir(PERIOD_M15,20,50);

   double request_px=V55ExecutablePrice(d);
   double lot=InpV57FixedLot,risk_cash=-1.0,risk_pct=-1.0,margin_cash=-1.0;
   bool lot_ok=V57FixedLotCompatible(d,request_px,B[ix].stop,lot,risk_cash,risk_pct,margin_cash);

   double spread_points=-1.0;
   double spread_cash=V58SpreadCashNow(d,lot,spread_points);
   double spread_risk_pct=(risk_cash>0.0 && spread_cash>=0.0 ? 100.0*spread_cash/risk_cash : -1.0);

   bool pullback80=(d>0 ? B[ix].entry_rsi2<=InpV58PullbackRsi2MaxLong
                         : B[ix].entry_rsi2>=InpV58PullbackRsi2MinShort);
   bool pullback70=(d>0 ? B[ix].entry_rsi2<=70.0 : B[ix].entry_rsi2>=30.0);
   bool no_opposite=(f.bos_choch_dir!=-d && f.fvg_dir!=-d && f.liquidity_sweep_dir!=-d);

   int gate_baseline=(ready && lot_ok ? 1 : 0);
   int gate_pullback80=(gate_baseline && pullback80 ? 1 : 0);
   int gate_pullback70=(gate_baseline && pullback70 ? 1 : 0);
   int gate_pullback80_no_opposite=(gate_pullback80 && no_opposite ? 1 : 0);
   int gate_fast_h1_pullback80=(gate_pullback80 && fast_h1==d ? 1 : 0);
   int gate_fast_both_pullback80=(gate_fast_h1_pullback80 && fast_m15!=-d ? 1 : 0);
   int gate_fast_both_pullback80_no_opposite=(gate_fast_both_pullback80 && no_opposite ? 1 : 0);

   int allow_actual=gate_pullback80;

   g_v58_last_risk_cash=risk_cash;
   g_v58_last_direction=d;
   g_v58_last_spread_cash=spread_cash;
   g_v58_last_spread_points=spread_points;

   string row=TimeToString(TimeCurrent(),TIME_DATE|TIME_MINUTES|TIME_SECONDS)+","+
      IntegerToString(d)+","+DoubleToString(lot,2)+","+DoubleToString(request_px,_Digits)+","+
      DoubleToString(B[ix].stop,_Digits)+","+DoubleToString(B[ix].tp,_Digits)+","+
      IntegerToString((int)ready)+","+IntegerToString(f.trend_h1)+","+IntegerToString(f.trend_h4)+","+
      IntegerToString(fast_h1)+","+IntegerToString(fast_m15)+","+IntegerToString(f.structure_dir)+","+
      IntegerToString(f.bos_choch_dir)+","+IntegerToString(f.fvg_dir)+","+IntegerToString(f.liquidity_sweep_dir)+","+
      DoubleToString(B[ix].entry_adx,4)+","+DoubleToString(B[ix].entry_plus_di,4)+","+
      DoubleToString(B[ix].entry_minus_di,4)+","+DoubleToString(B[ix].entry_rsi2,4)+","+
      DoubleToString(B[ix].entry_rsi14,4)+","+DoubleToString(B[ix].entry_macd_hist,6)+","+
      IntegerToString(f.score)+","+DoubleToString(risk_cash,4)+","+DoubleToString(risk_pct,4)+","+
      DoubleToString(margin_cash,4)+","+DoubleToString(spread_points,2)+","+DoubleToString(spread_cash,4)+","+
      DoubleToString(spread_risk_pct,4)+","+IntegerToString((int)lot_ok)+","+
      IntegerToString(gate_baseline)+","+IntegerToString(gate_pullback80)+","+IntegerToString(gate_pullback70)+","+
      IntegerToString(gate_pullback80_no_opposite)+","+IntegerToString(gate_fast_h1_pullback80)+","+
      IntegerToString(gate_fast_both_pullback80)+","+IntegerToString(gate_fast_both_pullback80_no_opposite)+","+
      IntegerToString(allow_actual);
   V55AppendCsv(g_v58_eval_file,row);
   return allow_actual==1;
}
'''
    text = text.replace(marker, "\n" + helper + marker, 1)

    text = replace_once(
        text,
        'g_v57_entry_allowed=V57EvaluateEntry(ix);',
        'g_v57_entry_allowed=V58EvaluateEntry(ix);',
        "entry evaluator route",
    )
    text = replace_once(
        text,
        'V55LogGuard("v57_model_filter")',
        'V55LogGuard("v58_model_filter")',
        "model-filter reason",
    )

    old_spread = '''   double spread_points=(t.ask-t.bid)/_Point;
   if(spread_points<0.0 || spread_points>InpV55MaxSpreadPoints){ V55LogGuard("spread_guard"); return false; }'''
    new_spread = '''   double spread_points=(t.ask-t.bid)/_Point;
   if(spread_points<0.0){ V55LogGuard("invalid_spread"); return false; }
   if(!V58SpreadCostOk())
   {
      V55LogGuard("spread_cost_guard");
      V55AppendCsv(g_v55_events_file,TimeToString(TimeCurrent(),TIME_DATE|TIME_MINUTES|TIME_SECONDS)+
         ",V58_SPREAD_BLOCK,"+DoubleToString(g_v58_last_spread_points,2)+","+
         DoubleToString(g_v58_last_spread_cash,4)+","+DoubleToString(g_v58_last_risk_cash,4));
      return false;
   }'''
    text = replace_once(text, old_spread, new_spread, "spread-cost guard")

    old_risk_event = '''   V55AppendCsv(g_v55_events_file,TimeToString(TimeCurrent(),TIME_DATE|TIME_MINUTES|TIME_SECONDS)+
      ",V57_FIXED001_RISK,"+DoubleToString(risk_money,4)+","+DoubleToString(risk_pct,4)+","+
      DoubleToString(margin_cash,4)+","+DoubleToString(AccountInfoDouble(ACCOUNT_EQUITY),4));'''
    new_risk_event = '''   double v58_sp=0.0;
   double v58_sc=V58SpreadCashNow(B[ix].direction,bv,v58_sp);
   V55AppendCsv(g_v55_events_file,TimeToString(TimeCurrent(),TIME_DATE|TIME_MINUTES|TIME_SECONDS)+
      ",V58_FIXED001_ATTEMPT,"+DoubleToString(risk_money,4)+","+DoubleToString(risk_pct,4)+","+
      DoubleToString(margin_cash,4)+","+DoubleToString(AccountInfoDouble(ACCOUNT_EQUITY),4)+","+
      DoubleToString(v58_sp,2)+","+DoubleToString(v58_sc,4));'''
    text = replace_once(text, old_risk_event, new_risk_event, "order-attempt telemetry")
    text = text.replace("V57 fixed001 trend_smc", "V58 fixed001 pullback80")

    required = (
        "InpV57FixedLot = 0.01",
        "InpV58PullbackRsi2MaxLong = 80.0",
        "InpV58MaxSpreadCash = 0.75",
        "InpV58MaxSpreadRiskPct = 5.0",
        "InpV58MaxMarginUsagePct = 95.0",
        "InpV55Magic = 580058",
        "V58_ENTRY_EVAL.csv",
        "V58FastTrendDir",
        "PERIOD_M15",
        "gate_pullback80",
        "gate_fast_both_pullback80_no_opposite",
        "V58SpreadCostOk",
        "V58_SPREAD_BLOCK",
        "V58_FIXED001_ATTEMPT",
        "V58EvaluateEntry(ix)",
        "v58_model_filter",
        "if(!MQLInfoInteger(MQL_TESTER))",
    )
    for token in required:
        if token not in text:
            raise RuntimeError(f"V58 required token missing: {token}")

    forbidden = (
        "InpV55Magic = 570057",
        'V55LogGuard("v57_model_filter")',
        'spread_points>InpV55MaxSpreadPoints',
        "g_v57_entry_allowed=V57EvaluateEntry(ix);",
        "V57 fixed001 trend_smc",
    )
    for token in forbidden:
        if token in text:
            raise RuntimeError(f"V58 forbidden token remains: {token}")
    return text


def build(source: Path, output: Path) -> str:
    if not source.is_file():
        raise RuntimeError(f"V58 V57 parent missing: {source}")
    out = transform(source.read_text(encoding="utf-8-sig"))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(out.replace("\n", "\r\n").encode("utf-8"))
    digest = sha256(output)
    print(f"V58_SOURCE_SHA256={digest}")
    print("V58_TESTER_ONLY=1")
    print("V58_FIXED_LOT=0.01")
    print("V58_ACTUAL_GATE=pullback80")
    print("V58_SPREAD_GUARD=cost_based")
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
