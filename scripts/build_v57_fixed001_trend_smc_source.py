#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

CANDIDATE = "v52_b4_or_b3_trend_bos"
V57_STATE_FILE = r"mt5_quant\\v57_fixed001_trend_smc\\seed_state.csv"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"V57 {label} drifted expected=1 actual={count}")
    return text.replace(old, new, 1)


def replace_in_function_once(text: str, fn: str, next_fn: str, old: str, new: str, label: str) -> str:
    start = text.find(fn)
    if start < 0:
        raise RuntimeError(f"V57 function missing: {fn}")
    end = text.find(next_fn, start + len(fn))
    if end < 0:
        raise RuntimeError(f"V57 next function missing after {fn}: {next_fn}")
    segment = text[start:end]
    count = segment.count(old)
    if count != 1:
        raise RuntimeError(f"V57 {label} drifted in {fn} expected=1 actual={count}")
    segment = segment.replace(old, new, 1)
    return text[:start] + segment + text[end:]


V57_HELPERS = r'''
struct V57EntryFeatures
{
   int trend_h1;
   int trend_h4;
   int structure_dir;
   int bos_choch_dir;
   int fvg_dir;
   int liquidity_sweep_dir;
   int di_dir;
   int macd_dir;
   int score;
   int gate_baseline;
   int gate_trend;
   int gate_trend_adx;
   int gate_trend_structure;
   int gate_balanced;
   int gate_strict;
   double ema50_h1;
   double ema200_h1;
   double ema50_h1_prev;
   double ema20_h4;
   double ema50_h4;
   double atr_h1;
};

double V57EMA(MqlRates &r[],const int count,const int period,const int shift)
{
   if(period<=1 || shift<0 || count<=shift+period) return 0.0;
   int oldest=MathMin(count-1,shift+period*4);
   if(oldest<=shift) return 0.0;
   double a=2.0/(period+1.0);
   double e=r[oldest].close;
   for(int i=oldest-1;i>=shift;--i) e=a*r[i].close+(1.0-a)*e;
   return e;
}

double V57ATR(MqlRates &r[],const int count,const int period,const int shift)
{
   if(period<=0 || shift<0 || count<=shift+period+1) return 0.0;
   double s=0.0;
   for(int i=shift;i<shift+period;++i)
   {
      double pc=r[i+1].close;
      double tr=MathMax(r[i].high-r[i].low,MathMax(MathAbs(r[i].high-pc),MathAbs(r[i].low-pc)));
      s+=tr;
   }
   return s/period;
}

bool V57PivotHigh(MqlRates &r[],const int count,const int idx,const int wing)
{
   if(idx-wing<0 || idx+wing>=count) return false;
   double h=r[idx].high;
   for(int k=1;k<=wing;++k)
      if(r[idx-k].high>=h || r[idx+k].high>h) return false;
   return true;
}

bool V57PivotLow(MqlRates &r[],const int count,const int idx,const int wing)
{
   if(idx-wing<0 || idx+wing>=count) return false;
   double l=r[idx].low;
   for(int k=1;k<=wing;++k)
      if(r[idx-k].low<=l || r[idx+k].low<l) return false;
   return true;
}

void V57ConfirmedSwings(MqlRates &r[],const int count,
                        double &h1,int &hi1,double &h2,int &hi2,
                        double &l1,int &li1,double &l2,int &li2)
{
   h1=0.0; h2=0.0; l1=0.0; l2=0.0;
   hi1=-1; hi2=-1; li1=-1; li2=-1;
   const int wing=2;
   int limit=MathMin(count-wing-1,80);
   for(int i=wing;i<=limit;++i)
   {
      if(hi2<0 && V57PivotHigh(r,count,i,wing))
      {
         if(hi1<0){ h1=r[i].high; hi1=i; }
         else { h2=r[i].high; hi2=i; }
      }
      if(li2<0 && V57PivotLow(r,count,i,wing))
      {
         if(li1<0){ l1=r[i].low; li1=i; }
         else { l2=r[i].low; li2=i; }
      }
      if(hi2>=0 && li2>=0) break;
   }
}

int V57RecentFvgDir(MqlRates &r[],const int count,const double atr)
{
   if(count<10 || atr<=0.0) return 0;
   for(int j=0;j<=4;++j)
   {
      double body=MathAbs(r[j+1].close-r[j+1].open);
      bool displacement=(body>=0.60*atr);
      if(!displacement) continue;
      bool bull=(r[j].low>r[j+2].high && r[j+1].close>r[j+1].open &&
                 (r[j].low-r[j+2].high)>=0.08*atr);
      bool bear=(r[j].high<r[j+2].low && r[j+1].close<r[j+1].open &&
                 (r[j+2].low-r[j].high)>=0.08*atr);
      if(bull) return 1;
      if(bear) return -1;
   }
   return 0;
}

bool V57BuildFeatures(const int ix,V57EntryFeatures &f)
{
   ZeroMemory(f);
   MqlRates h1[],h4[];
   ArraySetAsSeries(h1,true);
   ArraySetAsSeries(h4,true);
   int n1=CopyRates(_Symbol,PERIOD_H1,1,260,h1);
   int n4=CopyRates(_Symbol,PERIOD_H4,1,120,h4);
   if(n1<220 || n4<70) return false;

   f.ema50_h1=V57EMA(h1,n1,50,0);
   f.ema200_h1=V57EMA(h1,n1,200,0);
   f.ema50_h1_prev=V57EMA(h1,n1,50,3);
   f.ema20_h4=V57EMA(h4,n4,20,0);
   f.ema50_h4=V57EMA(h4,n4,50,0);
   f.atr_h1=V57ATR(h1,n1,14,0);
   if(f.ema50_h1<=0 || f.ema200_h1<=0 || f.ema50_h1_prev<=0 ||
      f.ema20_h4<=0 || f.ema50_h4<=0 || f.atr_h1<=0) return false;

   if(f.ema50_h1>f.ema200_h1 && f.ema50_h1>f.ema50_h1_prev) f.trend_h1=1;
   else if(f.ema50_h1<f.ema200_h1 && f.ema50_h1<f.ema50_h1_prev) f.trend_h1=-1;

   if(f.ema20_h4>f.ema50_h4 && h4[0].close>f.ema20_h4) f.trend_h4=1;
   else if(f.ema20_h4<f.ema50_h4 && h4[0].close<f.ema20_h4) f.trend_h4=-1;

   double sh1=0,sh2=0,sl1=0,sl2=0; int shi1=-1,shi2=-1,sli1=-1,sli2=-1;
   V57ConfirmedSwings(h1,n1,sh1,shi1,sh2,shi2,sl1,sli1,sl2,sli2);
   if(shi2>=0 && sli2>=0)
   {
      if(sh1>sh2 && sl1>sl2) f.structure_dir=1;
      else if(sh1<sh2 && sl1<sl2) f.structure_dir=-1;

      if(h1[0].close>sh1) f.bos_choch_dir=1;
      else if(h1[0].close<sl1) f.bos_choch_dir=-1;

      for(int j=0;j<=2;++j)
      {
         if(h1[j].low<sl1 && h1[j].close>sl1){ f.liquidity_sweep_dir=1; break; }
         if(h1[j].high>sh1 && h1[j].close<sh1){ f.liquidity_sweep_dir=-1; break; }
      }
   }
   f.fvg_dir=V57RecentFvgDir(h1,n1,f.atr_h1);

   f.di_dir=(B[ix].entry_plus_di>B[ix].entry_minus_di ? 1 :
             (B[ix].entry_minus_di>B[ix].entry_plus_di ? -1 : 0));
   f.macd_dir=(B[ix].entry_macd_hist>0 ? 1 : (B[ix].entry_macd_hist<0 ? -1 : 0));

   int d=B[ix].direction;
   int score=0;
   if(f.trend_h1==d) score+=3;
   else if(f.trend_h1==-d) score-=3;
   if(f.trend_h4==d) score+=1;
   if(B[ix].entry_adx>=18.0 && f.di_dir==d) score+=1;
   if(f.structure_dir==d) score+=1;
   if(f.bos_choch_dir==d) score+=1;
   if(f.fvg_dir==d) score+=1;
   if(f.liquidity_sweep_dir==d) score+=1;
   if(f.macd_dir==d) score+=1;
   bool rsi_ok=(d>0 ? (B[ix].entry_rsi14>=45.0 && B[ix].entry_rsi14<=68.0)
                     : (B[ix].entry_rsi14>=32.0 && B[ix].entry_rsi14<=55.0));
   if(rsi_ok) score+=1;
   if((d>0 && B[ix].entry_rsi2>=95.0) || (d<0 && B[ix].entry_rsi2<=5.0)) score-=1;
   f.score=score;

   f.gate_baseline=1;
   f.gate_trend=(f.trend_h1==d ? 1 : 0);
   f.gate_trend_adx=(f.gate_trend && B[ix].entry_adx>=18.0 && f.di_dir==d ? 1 : 0);
   f.gate_trend_structure=(f.gate_trend && (f.structure_dir==d || f.bos_choch_dir==d) ? 1 : 0);
   f.gate_balanced=(f.gate_trend && score>=InpV57MinConfluenceScore ? 1 : 0);
   f.gate_strict=(f.gate_trend && score>=InpV57StrictConfluenceScore ? 1 : 0);
   return true;
}

double V57FixedLotRiskCash(const int direction,const double entry,const double stop,const double lot)
{
   ENUM_ORDER_TYPE ot=(direction>0 ? ORDER_TYPE_BUY : ORDER_TYPE_SELL);
   double pnl=0.0;
   if(!OrderCalcProfit(ot,_Symbol,lot,entry,stop,pnl)) return -1.0;
   return MathAbs(pnl);
}

bool V57FixedLotCompatible(const int direction,const double request_px,const double stop,
                           double &lot,double &risk_cash,double &risk_pct,double &margin_cash)
{
   lot=InpV57FixedLot;
   risk_cash=0.0; risk_pct=0.0; margin_cash=0.0;
   double vmin=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MIN);
   double vmax=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MAX);
   double step=SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_STEP);
   if(vmin<=0.0 || vmax<=0.0 || step<=0.0) return false;
   if(lot<vmin-1e-12 || lot>vmax+1e-12) return false;
   double units=(lot-vmin)/step;
   if(MathAbs(units-MathRound(units))>1e-6) return false;

   risk_cash=V57FixedLotRiskCash(direction,request_px,stop,lot);
   if(risk_cash<0.0) return false;
   double eq=AccountInfoDouble(ACCOUNT_EQUITY);
   risk_pct=(eq>0.0 ? 100.0*risk_cash/eq : 0.0);

   ENUM_ORDER_TYPE ot=(direction>0 ? ORDER_TYPE_BUY : ORDER_TYPE_SELL);
   if(!OrderCalcMargin(ot,_Symbol,lot,request_px,margin_cash)) return false;
   double free_margin=AccountInfoDouble(ACCOUNT_MARGIN_FREE);
   if(free_margin<=0.0 || margin_cash>free_margin*(InpV55MaxMarginUsagePct/100.0)) return false;
   return true;
}

void V57EnsureEvalFile()
{
   if(FileIsExist(g_v57_eval_file,FILE_COMMON)) return;
   V55AppendCsv(g_v57_eval_file,"time,direction,virtual_volume,fixed_lot,request_price,stop,tp,feature_ready,trend_h1,trend_h4,structure_dir,bos_choch_dir,fvg_dir,liquidity_sweep_dir,di_dir,macd_dir,score,gate_baseline,gate_trend,gate_trend_adx,gate_trend_structure,gate_balanced,gate_strict,adx,plus_di,minus_di,rsi2,rsi14,macd_hist,risk_cash_fixed001,risk_pct_equity,margin_cash,lot_ok,allow_balanced");
}

bool V57EvaluateEntry(const int ix)
{
   V57EnsureEvalFile();
   V57EntryFeatures f;
   bool ready=V57BuildFeatures(ix,f);
   double request_px=V55ExecutablePrice(B[ix].direction);
   double lot=InpV57FixedLot,risk_cash=-1.0,risk_pct=-1.0,margin_cash=-1.0;
   bool lot_ok=V57FixedLotCompatible(B[ix].direction,request_px,B[ix].stop,lot,risk_cash,risk_pct,margin_cash);
   int allow=(ready && lot_ok && f.gate_balanced ? 1 : 0);

   string row=TimeToString(TimeCurrent(),TIME_DATE|TIME_MINUTES|TIME_SECONDS)+","+
      IntegerToString(B[ix].direction)+","+DoubleToString(B[ix].volume,6)+","+DoubleToString(lot,2)+","+
      DoubleToString(request_px,_Digits)+","+DoubleToString(B[ix].stop,_Digits)+","+DoubleToString(B[ix].tp,_Digits)+","+
      IntegerToString((int)ready)+","+IntegerToString(f.trend_h1)+","+IntegerToString(f.trend_h4)+","+
      IntegerToString(f.structure_dir)+","+IntegerToString(f.bos_choch_dir)+","+IntegerToString(f.fvg_dir)+","+
      IntegerToString(f.liquidity_sweep_dir)+","+IntegerToString(f.di_dir)+","+IntegerToString(f.macd_dir)+","+
      IntegerToString(f.score)+","+IntegerToString(f.gate_baseline)+","+IntegerToString(f.gate_trend)+","+
      IntegerToString(f.gate_trend_adx)+","+IntegerToString(f.gate_trend_structure)+","+
      IntegerToString(f.gate_balanced)+","+IntegerToString(f.gate_strict)+","+
      DoubleToString(B[ix].entry_adx,4)+","+DoubleToString(B[ix].entry_plus_di,4)+","+
      DoubleToString(B[ix].entry_minus_di,4)+","+DoubleToString(B[ix].entry_rsi2,4)+","+
      DoubleToString(B[ix].entry_rsi14,4)+","+DoubleToString(B[ix].entry_macd_hist,6)+","+
      DoubleToString(risk_cash,4)+","+DoubleToString(risk_pct,4)+","+DoubleToString(margin_cash,4)+","+
      IntegerToString((int)lot_ok)+","+IntegerToString(allow);
   V55AppendCsv(g_v57_eval_file,row);
   g_v57_last_score=f.score;
   g_v57_last_risk_cash=risk_cash;
   g_v57_last_risk_pct=risk_pct;
   return allow==1;
}
'''


def transform(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    required_parent = (
        "V56 WEEKLY REAL-TICK REPLAY REFUSED: STRATEGY TESTER REQUIRED",
        "V56_VIRTUAL_OPEN",
        CANDIDATE,
        "void V55OpenFromVirtual()",
        "void V55SyncBrokerWithVirtual()",
        'input long InpV55Magic = 550055;',
    )
    for token in required_parent:
        if token not in text:
            raise RuntimeError(f"V57 parent V56 token missing: {token}")

    text = text.replace("V56 WEEKLY REAL-TICK REPLAY", "V57 FIXED001 TREND-SMC REPLAY")
    text = text.replace("v56_weekly_live_replay", "v57_fixed001_trend_smc")
    text = replace_once(text, 'input long InpV55Magic = 550055;', 'input long InpV55Magic = 570057;', "magic")
    text = replace_once(
        text,
        'input double InpV55MaxMarginUsagePct = 80.0;',
        'input double InpV55MaxMarginUsagePct = 80.0;\n'
        'input double InpV57FixedLot = 0.01;\n'
        'input int InpV57MinConfluenceScore = 5;\n'
        'input int InpV57StrictConfluenceScore = 6;',
        "V57 inputs",
    )
    text = replace_once(
        text,
        'bool g_v56_prev_virtual_open=false;\nint g_v56_prev_virtual_direction=0;',
        'bool g_v56_prev_virtual_open=false;\n'
        'int g_v56_prev_virtual_direction=0;\n'
        'bool g_v57_entry_decided=false;\n'
        'bool g_v57_entry_allowed=false;\n'
        'datetime g_v57_decision_entry_time=0;\n'
        'int g_v57_last_score=0;\n'
        'double g_v57_last_risk_cash=0.0;\n'
        'double g_v57_last_risk_pct=0.0;\n'
        'bool g_v57_daily_limit_reported=false;\n'
        'bool g_v57_dd_limit_reported=false;\n'
        'string g_v57_eval_file="mt5_quant\\\\v57_fixed001_trend_smc\\\\V57_ENTRY_EVAL.csv";',
        "V57 globals",
    )
    text = replace_once(text, "void V55OpenFromVirtual()\n{", V57_HELPERS + "\nvoid V55OpenFromVirtual()\n{", "V57 helper insertion")

    old_open = '''   if(g_v55_halted || !g_v55_accept_new || !B[ix].open || g_v55_open_pending || g_v55_close_pending || !V55RequestCooldownReady()) return;
   if(!V55EntryHealthOk()) return;
   double vv=B[ix].volume;
   double request_px=V55ExecutablePrice(B[ix].direction);
   if(!V55StopsGeometryOk(B[ix].direction,request_px,B[ix].stop,B[ix].tp))
   { V55LogGuard("broker_stop_geometry_guard"); return; }
   double risk_money=0.0,loss_per_lot=0.0;
   double bv=V55RiskBoundVolume(B[ix].direction,vv,request_px,B[ix].stop,risk_money,loss_per_lot);
   if(bv<=0.0){ V55LogGuard("risk_cap_below_min_or_invalid_stop"); return; }'''
    new_open = '''   if(g_v55_halted || !g_v55_accept_new || !B[ix].open || g_v55_open_pending || g_v55_close_pending || !V55RequestCooldownReady()) return;
   if(!g_v57_entry_decided || !g_v57_entry_allowed){ V55LogGuard("v57_model_filter"); return; }
   if(!V55EntryHealthOk()) return;
   double vv=B[ix].volume;
   double request_px=V55ExecutablePrice(B[ix].direction);
   if(!V55StopsGeometryOk(B[ix].direction,request_px,B[ix].stop,B[ix].tp))
   { V55LogGuard("broker_stop_geometry_guard"); return; }
   double bv=InpV57FixedLot,risk_money=0.0,risk_pct=0.0,margin_cash=0.0;
   if(!V57FixedLotCompatible(B[ix].direction,request_px,B[ix].stop,bv,risk_money,risk_pct,margin_cash))
   { V55LogGuard("v57_fixed_lot_or_margin_incompatible"); return; }
   V55AppendCsv(g_v55_events_file,TimeToString(TimeCurrent(),TIME_DATE|TIME_MINUTES|TIME_SECONDS)+
      ",V57_FIXED001_RISK,"+DoubleToString(risk_money,4)+","+DoubleToString(risk_pct,4)+","+
      DoubleToString(margin_cash,4)+","+DoubleToString(AccountInfoDouble(ACCOUNT_EQUITY),4));'''
    text = replace_in_function_once(text, "void V55OpenFromVirtual()", "void V55CloseOwned(", old_open, new_open, "fixed 0.01 open path")
    text = text.replace('"V55 trend_bos"', '"V57 fixed001 trend_smc"')

    sync_marker = '   int owned=V55OwnedPositionCount(ticket,broker_dir,broker_vol);'
    sync_new = '''   if(B[ix].open)
   {
      if(!g_v57_entry_decided || g_v57_decision_entry_time!=B[ix].entry_time)
      {
         g_v57_entry_allowed=V57EvaluateEntry(ix);
         g_v57_entry_decided=true;
         g_v57_decision_entry_time=B[ix].entry_time;
      }
   }
   else
   {
      g_v57_entry_decided=false;
      g_v57_entry_allowed=false;
      g_v57_decision_entry_time=0;
   }
   int owned=V55OwnedPositionCount(ticket,broker_dir,broker_vol);'''
    text = replace_in_function_once(text, "void V55SyncBrokerWithVirtual()", "void V55WriteStatus()", sync_marker, sync_new, "entry decision latch")

    daily_old = '''   if(g_v55_daily_loss_pct>=InpV55DailyLossPct)
   {
      g_v55_force_flatten=true; V55Halt("daily_loss_limit");
   }
   if(g_v55_drawdown_pct>=InpV55MaxDrawdownPct)
   {
      g_v55_force_flatten=true; V55Halt("max_drawdown_limit");
   }'''
    daily_new = '''   if(g_v55_daily_loss_pct>=InpV55DailyLossPct && !g_v57_daily_limit_reported)
   {
      g_v57_daily_limit_reported=true;
      V55AppendCsv(g_v55_events_file,TimeToString(TimeCurrent(),TIME_DATE|TIME_MINUTES|TIME_SECONDS)+
         ",V57_WOULD_HALT,daily_loss_limit,"+DoubleToString(g_v55_daily_loss_pct,4));
   }
   if(g_v55_drawdown_pct>=InpV55MaxDrawdownPct && !g_v57_dd_limit_reported)
   {
      g_v57_dd_limit_reported=true;
      V55AppendCsv(g_v55_events_file,TimeToString(TimeCurrent(),TIME_DATE|TIME_MINUTES|TIME_SECONDS)+
         ",V57_WOULD_HALT,max_drawdown_limit,"+DoubleToString(g_v55_drawdown_pct,4));
   }'''
    text = replace_in_function_once(text, "void V55RefreshRiskState()", "bool V55EntryHealthOk()", daily_old, daily_new, "tester capital-limit telemetry")


    tx_header_old = 'V55AppendCsv(g_v55_transactions_file,"time,type,deal,order,symbol,price,volume,entry,deal_type");'
    tx_header_new = 'V55AppendCsv(g_v55_transactions_file,"time,type,deal,order,symbol,price,volume,entry,deal_type,profit,commission,swap,fee");'
    text = replace_once(text, tx_header_old, tx_header_new, "extended transaction header")

    tx_old = '''   double price=HistoryDealGetDouble(trans.deal,DEAL_PRICE);
   double volume=HistoryDealGetDouble(trans.deal,DEAL_VOLUME);
   string row=TimeToString(TimeLocal(),TIME_DATE|TIME_MINUTES|TIME_SECONDS)+","+IntegerToString((int)trans.type)+","+
      IntegerToString((int)trans.deal)+","+IntegerToString((int)trans.order)+","+symbol+","+DoubleToString(price,_Digits)+","+
      DoubleToString(volume,6)+","+IntegerToString((int)entry)+","+IntegerToString((int)dtype);
   V55AppendCsv(g_v55_transactions_file,row);'''
    tx_new = '''   double price=HistoryDealGetDouble(trans.deal,DEAL_PRICE);
   double volume=HistoryDealGetDouble(trans.deal,DEAL_VOLUME);
   double profit=HistoryDealGetDouble(trans.deal,DEAL_PROFIT);
   double commission=HistoryDealGetDouble(trans.deal,DEAL_COMMISSION);
   double swap=HistoryDealGetDouble(trans.deal,DEAL_SWAP);
   double fee=HistoryDealGetDouble(trans.deal,DEAL_FEE);
   datetime deal_time=(datetime)HistoryDealGetInteger(trans.deal,DEAL_TIME);
   string row=TimeToString(deal_time,TIME_DATE|TIME_MINUTES|TIME_SECONDS)+","+IntegerToString((int)trans.type)+","+
      IntegerToString((int)trans.deal)+","+IntegerToString((int)trans.order)+","+symbol+","+DoubleToString(price,_Digits)+","+
      DoubleToString(volume,6)+","+IntegerToString((int)entry)+","+IntegerToString((int)dtype)+","+
      DoubleToString(profit,4)+","+DoubleToString(commission,4)+","+DoubleToString(swap,4)+","+DoubleToString(fee,4);
   V55AppendCsv(g_v55_transactions_file,row);'''
    text = replace_once(text, tx_old, tx_new, "extended broker PnL transaction telemetry")

    required = (
        "InpV57FixedLot = 0.01",
        "InpV57MinConfluenceScore = 5",
        "InpV57StrictConfluenceScore = 6",
        "V57_ENTRY_EVAL.csv",
        "V57_FIXED001_RISK",
        "V57_WOULD_HALT",
        "DEAL_PROFIT",
        "profit,commission,swap,fee",
        "V57FixedLotCompatible",
        "V57RecentFvgDir",
        "V57ConfirmedSwings",
        "PERIOD_H4",
        "g_v57_entry_decided",
        "v57_model_filter",
        "v57_fixed_lot_or_margin_incompatible",
        'InpV55Magic = 570057',
        "if(!MQLInfoInteger(MQL_TESTER))",
    )
    for token in required:
        if token not in text:
            raise RuntimeError(f"V57 required token missing: {token}")

    forbidden = (
        'InpV55Magic = 550055',
        'double bv=V55RiskBoundVolume(B[ix].direction,vv,request_px,B[ix].stop,risk_money,loss_per_lot);',
        'V55Halt("daily_loss_limit")',
        'V55Halt("max_drawdown_limit")',
    )
    for token in forbidden:
        if token in text:
            raise RuntimeError(f"V57 forbidden token remains: {token}")
    return text


def build(source: Path, output: Path) -> str:
    if not source.is_file():
        raise RuntimeError(f"V57 V56 parent missing: {source}")
    text = source.read_text(encoding="utf-8-sig")
    out = transform(text)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(out.replace("\n", "\r\n").encode("utf-8"))
    digest = sha256(output)
    print(f"V57_SOURCE_SHA256={digest}")
    print("V57_TESTER_ONLY=1")
    print("V57_FIXED_LOT=0.01")
    print("V57_GATE_ACTUAL=trend_smc_balanced")
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
