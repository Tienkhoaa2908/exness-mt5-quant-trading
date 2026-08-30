#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

EXPERT_NAME = "V59IntegratedBidirectionalRR"
FIXED_LOT = 0.01
MAGIC = 590059

MQL = r'''#property strict
#property version   "59.00"
#property description "V59 integrated bidirectional RR research - TESTER ONLY"

#include <Trade/Trade.mqh>

input long   InpV59Magic = 590059;
input double InpV59FixedLot = 0.01;
input int    InpV59MinDirectionalScore = 8;
input int    InpV59MinScoreEdge = 2;
input double InpV59ActualRR = 3.0;
input double InpV59MaxStopRiskCash = 8.0;
input double InpV59MaxStopATR = 1.50;
input double InpV59StopAtrBuffer = 0.15;
input double InpV59MaxSpreadCash = 0.75;
input double InpV59MaxSpreadRiskPct = 10.0;
input double InpV59MaxMarginUsagePct = 95.0;
input bool   InpV59ScreenOnly = false;
input int    InpV59MaxBarsInTrade = 64;

string V59_ROOT = "mt5_quant\\v59_integrated_bidirectional_rr";
string V59_EVAL = "mt5_quant\\v59_integrated_bidirectional_rr\\V59_ENTRY_EVAL.csv";
string V59_EVENTS = "mt5_quant\\v59_integrated_bidirectional_rr\\V59_EVENTS.csv";
string V59_DEALS = "mt5_quant\\v59_integrated_bidirectional_rr\\V59_DEALS.csv";
string V59_SHADOW = "mt5_quant\\v59_integrated_bidirectional_rr\\V59_SHADOW_RR.csv";
string V59_STATUS = "mt5_quant\\v59_integrated_bidirectional_rr\\V59_STATUS.txt";

CTrade g_trade;
datetime g_last_m15_bar=0;

bool g_shadow_open=false;
int g_shadow_dir=0;
datetime g_shadow_entry_time=0;
double g_shadow_entry=0.0;
double g_shadow_stop=0.0;
double g_shadow_risk_dist=0.0;
double g_shadow_risk_cash=0.0;
int g_shadow_score=0;
int g_shadow_bars=0;
double g_shadow_max_r=-1000.0;
double g_shadow_min_r=1000.0;
bool g_rr2_done=false;
bool g_rr25_done=false;
bool g_rr3_done=false;
double g_rr2=0.0;
double g_rr25=0.0;
double g_rr3=0.0;

struct V59Features
{
   bool ready;
   int h4_trend;
   int h1_trend;
   int m15_trend;
   int structure_dir;
   int bos_choch_dir;
   int fvg_dir;
   int liquidity_sweep_dir;
   int order_block_retest_dir;
   int pullback_dir;
   int di_dir;
   int macd_dir;
   int location_dir;
   double atr15;
   double ema20_m15;
   double ema50_m15;
   double ema20_h1;
   double ema50_h1;
   double ema20_h4;
   double ema50_h4;
   double rsi2;
   double rsi14;
   double plus_di;
   double minus_di;
   double adx;
   double macd;
   double macd_slope;
   double distance_ema_atr;
   double swing_high;
   double swing_low;
   double range_location;
   int long_score;
   int short_score;
};

void V59Append(const string path,const string line)
{
   int h=FileOpen(path,FILE_READ|FILE_WRITE|FILE_TXT|FILE_COMMON|FILE_ANSI);
   if(h==INVALID_HANDLE) return;
   FileSeek(h,0,SEEK_END);
   FileWriteString(h,line+"\r\n");
   FileFlush(h);
   FileClose(h);
}

void V59WriteStatus(const string state,const string detail)
{
   int h=FileOpen(V59_STATUS,FILE_WRITE|FILE_TXT|FILE_COMMON|FILE_ANSI);
   if(h==INVALID_HANDLE) return;
   FileWriteString(h,"state="+state+"\r\n");
   FileWriteString(h,"detail="+detail+"\r\n");
   FileWriteString(h,"symbol="+_Symbol+"\r\n");
   FileWriteString(h,"time="+TimeToString(TimeCurrent(),TIME_DATE|TIME_MINUTES|TIME_SECONDS)+"\r\n");
   FileWriteString(h,"fixed_lot="+DoubleToString(InpV59FixedLot,2)+"\r\n");
   FileWriteString(h,"screen_only="+IntegerToString((int)InpV59ScreenOnly)+"\r\n");
   FileClose(h);
}

double V59EMA(MqlRates &r[],const int count,const int period,const int shift)
{
   if(period<=1 || shift<0 || count<=shift+period) return 0.0;
   int oldest=MathMin(count-1,shift+period*5);
   if(oldest<=shift) return 0.0;
   double a=2.0/(period+1.0);
   double e=r[oldest].close;
   for(int i=oldest-1;i>=shift;--i) e=a*r[i].close+(1.0-a)*e;
   return e;
}

double V59ATR(MqlRates &r[],const int count,const int period,const int shift)
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

double V59RSI(MqlRates &r[],const int count,const int period,const int shift)
{
   if(period<=0 || count<=shift+period+1) return 50.0;
   double gain=0.0,loss=0.0;
   for(int i=shift;i<shift+period;++i)
   {
      double ch=r[i].close-r[i+1].close;
      if(ch>0.0) gain+=ch; else loss-=ch;
   }
   if(loss<=1e-12) return (gain>0.0 ? 100.0 : 50.0);
   double rs=gain/loss;
   return 100.0-(100.0/(1.0+rs));
}

bool V59PivotHigh(MqlRates &r[],const int count,const int idx,const int wing)
{
   if(idx-wing<0 || idx+wing>=count) return false;
   double h=r[idx].high;
   for(int k=1;k<=wing;++k)
      if(r[idx-k].high>=h || r[idx+k].high>h) return false;
   return true;
}

bool V59PivotLow(MqlRates &r[],const int count,const int idx,const int wing)
{
   if(idx-wing<0 || idx+wing>=count) return false;
   double l=r[idx].low;
   for(int k=1;k<=wing;++k)
      if(r[idx-k].low<=l || r[idx+k].low<l) return false;
   return true;
}

void V59ConfirmedSwings(MqlRates &r[],const int count,
                        double &h1,int &hi1,double &h2,int &hi2,
                        double &l1,int &li1,double &l2,int &li2)
{
   h1=0.0;h2=0.0;l1=0.0;l2=0.0;
   hi1=-1;hi2=-1;li1=-1;li2=-1;
   const int wing=2;
   int limit=MathMin(count-wing-1,120);
   for(int i=wing;i<=limit;++i)
   {
      if(hi2<0 && V59PivotHigh(r,count,i,wing))
      {
         if(hi1<0){h1=r[i].high;hi1=i;} else {h2=r[i].high;hi2=i;}
      }
      if(li2<0 && V59PivotLow(r,count,i,wing))
      {
         if(li1<0){l1=r[i].low;li1=i;} else {l2=r[i].low;li2=i;}
      }
      if(hi2>=0 && li2>=0) break;
   }
}

int V59RecentFvgDir(MqlRates &r[],const int count,const double atr)
{
   if(count<12 || atr<=0.0) return 0;
   for(int j=0;j<=5;++j)
   {
      double body=MathAbs(r[j+1].close-r[j+1].open);
      bool displacement=(body>=0.55*atr);
      if(!displacement) continue;
      bool bull=(r[j].low>r[j+2].high && r[j+1].close>r[j+1].open &&
                 (r[j].low-r[j+2].high)>=0.06*atr);
      bool bear=(r[j].high<r[j+2].low && r[j+1].close<r[j+1].open &&
                 (r[j+2].low-r[j].high)>=0.06*atr);
      if(bull) return 1;
      if(bear) return -1;
   }
   return 0;
}

void V59DIADX(MqlRates &r[],const int count,const int period,
              double &plus_di,double &minus_di,double &adx)
{
   plus_di=0.0;minus_di=0.0;adx=0.0;
   if(count<period*2+5) return;
   double dx_sum=0.0;
   int dx_n=0;
   for(int sh=0;sh<period;++sh)
   {
      double tr_sum=0.0,pdm=0.0,mdm=0.0;
      for(int i=sh;i<sh+period;++i)
      {
         double up=r[i].high-r[i+1].high;
         double dn=r[i+1].low-r[i].low;
         double pc=r[i+1].close;
         double tr=MathMax(r[i].high-r[i].low,MathMax(MathAbs(r[i].high-pc),MathAbs(r[i].low-pc)));
         tr_sum+=tr;
         if(up>dn && up>0.0) pdm+=up;
         if(dn>up && dn>0.0) mdm+=dn;
      }
      if(tr_sum<=1e-12) continue;
      double p=100.0*pdm/tr_sum;
      double m=100.0*mdm/tr_sum;
      if(sh==0){plus_di=p;minus_di=m;}
      double den=p+m;
      if(den>1e-12){dx_sum+=100.0*MathAbs(p-m)/den;dx_n++;}
   }
   if(dx_n>0) adx=dx_sum/dx_n;
}

int V59OrderBlockRetestDir(MqlRates &r[],const int count,const int bos_dir,const double atr)
{
   if(count<12 || atr<=0.0 || bos_dir==0) return 0;
   for(int j=2;j<=8;++j)
   {
      if(bos_dir>0 && r[j].close<r[j].open)
      {
         double hi=r[j].high,lo=r[j].low;
         if(r[0].low<=hi+0.10*atr && r[0].close>hi && r[0].close>r[0].open && r[0].low>=lo-0.15*atr)
            return 1;
      }
      if(bos_dir<0 && r[j].close>r[j].open)
      {
         double hi=r[j].high,lo=r[j].low;
         if(r[0].high>=lo-0.10*atr && r[0].close<lo && r[0].close<r[0].open && r[0].high<=hi+0.15*atr)
            return -1;
      }
   }
   return 0;
}

int V59ScoreDirection(const int d,V59Features &f)
{
   int s=0;
   if(f.h4_trend==d) s+=2; else if(f.h4_trend==-d) s-=2;
   if(f.h1_trend==d) s+=3; else if(f.h1_trend==-d) s-=4;
   if(f.m15_trend==d) s+=1; else if(f.m15_trend==-d) s-=1;
   if(f.structure_dir==d) s+=2; else if(f.structure_dir==-d) s-=1;
   if(f.bos_choch_dir==d) s+=2; else if(f.bos_choch_dir==-d) s-=2;
   if(f.fvg_dir==d) s+=1; else if(f.fvg_dir==-d) s-=1;
   if(f.liquidity_sweep_dir==d) s+=2;
   if(f.order_block_retest_dir==d) s+=1;
   if(f.pullback_dir==d) s+=2;
   if(f.adx>=18.0 && f.di_dir==d) s+=1;
   if(f.macd_dir==d && d*f.macd_slope>0.0) s+=1;
   bool rsi14_ok=(d>0 ? (f.rsi14>=42.0 && f.rsi14<=68.0) : (f.rsi14>=32.0 && f.rsi14<=58.0));
   if(rsi14_ok) s+=1;
   if(f.location_dir==d) s+=1;
   bool chased=(d>0 ? (f.rsi2>85.0 || f.distance_ema_atr>1.20)
                     : (f.rsi2<15.0 || f.distance_ema_atr<-1.20));
   if(chased) s-=2;
   return s;
}

bool V59BuildFeatures(V59Features &f)
{
   ZeroMemory(f);
   MqlRates m15[],h1[],h4[];
   ArraySetAsSeries(m15,true);ArraySetAsSeries(h1,true);ArraySetAsSeries(h4,true);
   int n15=CopyRates(_Symbol,PERIOD_M15,1,320,m15);
   int n1=CopyRates(_Symbol,PERIOD_H1,1,260,h1);
   int n4=CopyRates(_Symbol,PERIOD_H4,1,140,h4);
   if(n15<220 || n1<220 || n4<80) return false;

   f.atr15=V59ATR(m15,n15,14,0);
   f.ema20_m15=V59EMA(m15,n15,20,0);
   f.ema50_m15=V59EMA(m15,n15,50,0);
   double ema20_m15_prev=V59EMA(m15,n15,20,3);
   f.ema20_h1=V59EMA(h1,n1,20,0);
   f.ema50_h1=V59EMA(h1,n1,50,0);
   double ema20_h1_prev=V59EMA(h1,n1,20,3);
   f.ema20_h4=V59EMA(h4,n4,20,0);
   f.ema50_h4=V59EMA(h4,n4,50,0);
   double ema20_h4_prev=V59EMA(h4,n4,20,2);
   if(f.atr15<=0.0 || f.ema20_m15<=0.0 || f.ema50_m15<=0.0 ||
      f.ema20_h1<=0.0 || f.ema50_h1<=0.0 || f.ema20_h4<=0.0 || f.ema50_h4<=0.0)
      return false;

   if(f.ema20_h4>f.ema50_h4 && f.ema20_h4>ema20_h4_prev && h4[0].close>f.ema20_h4) f.h4_trend=1;
   else if(f.ema20_h4<f.ema50_h4 && f.ema20_h4<ema20_h4_prev && h4[0].close<f.ema20_h4) f.h4_trend=-1;

   if(f.ema20_h1>f.ema50_h1 && f.ema20_h1>ema20_h1_prev && h1[0].close>f.ema20_h1) f.h1_trend=1;
   else if(f.ema20_h1<f.ema50_h1 && f.ema20_h1<ema20_h1_prev && h1[0].close<f.ema20_h1) f.h1_trend=-1;

   if(f.ema20_m15>f.ema50_m15 && f.ema20_m15>ema20_m15_prev && m15[0].close>f.ema20_m15) f.m15_trend=1;
   else if(f.ema20_m15<f.ema50_m15 && f.ema20_m15<ema20_m15_prev && m15[0].close<f.ema20_m15) f.m15_trend=-1;

   double sh1=0,sh2=0,sl1=0,sl2=0;int shi1=-1,shi2=-1,sli1=-1,sli2=-1;
   V59ConfirmedSwings(m15,n15,sh1,shi1,sh2,shi2,sl1,sli1,sl2,sli2);
   if(shi2<0 || sli2<0) return false;
   f.swing_high=sh1;f.swing_low=sl1;
   if(sh1>sh2 && sl1>sl2) f.structure_dir=1;
   else if(sh1<sh2 && sl1<sl2) f.structure_dir=-1;

   if(m15[0].close>sh1) f.bos_choch_dir=1;
   else if(m15[0].close<sl1) f.bos_choch_dir=-1;

   for(int j=0;j<=3;++j)
   {
      if(m15[j].low<sl1 && m15[j].close>sl1){f.liquidity_sweep_dir=1;break;}
      if(m15[j].high>sh1 && m15[j].close<sh1){f.liquidity_sweep_dir=-1;break;}
   }

   f.fvg_dir=V59RecentFvgDir(m15,n15,f.atr15);
   f.order_block_retest_dir=V59OrderBlockRetestDir(m15,n15,f.bos_choch_dir,f.atr15);

   bool bull_pb=(m15[0].low<=f.ema20_m15+0.15*f.atr15 && m15[0].close>f.ema20_m15 && m15[0].close>m15[0].open);
   bool bear_pb=(m15[0].high>=f.ema20_m15-0.15*f.atr15 && m15[0].close<f.ema20_m15 && m15[0].close<m15[0].open);
   if(bull_pb) f.pullback_dir=1; else if(bear_pb) f.pullback_dir=-1;

   f.rsi2=V59RSI(m15,n15,2,0);
   f.rsi14=V59RSI(m15,n15,14,0);
   V59DIADX(m15,n15,14,f.plus_di,f.minus_di,f.adx);
   f.di_dir=(f.plus_di>f.minus_di ? 1 : (f.minus_di>f.plus_di ? -1 : 0));
   f.macd=V59EMA(m15,n15,12,0)-V59EMA(m15,n15,26,0);
   double macd_prev=V59EMA(m15,n15,12,3)-V59EMA(m15,n15,26,3);
   f.macd_slope=f.macd-macd_prev;
   f.macd_dir=(f.macd>0.0 ? 1 : (f.macd<0.0 ? -1 : 0));
   f.distance_ema_atr=(m15[0].close-f.ema20_m15)/f.atr15;

   double range=sh1-sl1;
   if(range>0.0)
   {
      f.range_location=(m15[0].close-sl1)/range;
      if(f.range_location<=0.55) f.location_dir=1;
      else if(f.range_location>=0.45) f.location_dir=-1;
   }

   f.long_score=V59ScoreDirection(1,f);
   f.short_score=V59ScoreDirection(-1,f);
   f.ready=true;
   return true;
}

int V59SelectDirection(V59Features &f,string &why)
{
   why="no_edge";
   bool long_trigger=(f.bos_choch_dir==1 || f.fvg_dir==1 || f.liquidity_sweep_dir==1 ||
                      f.order_block_retest_dir==1 || (f.pullback_dir==1 && f.m15_trend==1));
   bool short_trigger=(f.bos_choch_dir==-1 || f.fvg_dir==-1 || f.liquidity_sweep_dir==-1 ||
                       f.order_block_retest_dir==-1 || (f.pullback_dir==-1 && f.m15_trend==-1));
   bool long_regime=(f.h1_trend==1 && f.h4_trend!=-1);
   bool short_regime=(f.h1_trend==-1 && f.h4_trend!=1);
   bool long_ok=(long_regime && long_trigger && f.long_score>=InpV59MinDirectionalScore &&
                 f.long_score-f.short_score>=InpV59MinScoreEdge);
   bool short_ok=(short_regime && short_trigger && f.short_score>=InpV59MinDirectionalScore &&
                  f.short_score-f.long_score>=InpV59MinScoreEdge);
   if(long_ok && !short_ok){why="long_edge";return 1;}
   if(short_ok && !long_ok){why="short_edge";return -1;}
   if(long_ok && short_ok)
   {
      if(f.long_score>f.short_score){why="long_tiebreak";return 1;}
      if(f.short_score>f.long_score){why="short_tiebreak";return -1;}
      why="ambiguous";return 0;
   }
   if(!long_regime && !short_regime) why="regime_neutral";
   else if(!long_trigger && !short_trigger) why="no_trigger";
   else why="score_below_threshold";
   return 0;
}

double V59RiskCash(const int d,const double entry,const double stop,const double lot)
{
   ENUM_ORDER_TYPE ot=(d>0 ? ORDER_TYPE_BUY : ORDER_TYPE_SELL);
   double pnl=0.0;
   if(!OrderCalcProfit(ot,_Symbol,lot,entry,stop,pnl)) return -1.0;
   return MathAbs(pnl);
}

double V59SpreadCash(const int d,const double lot,double &spread_points)
{
   MqlTick t;
   spread_points=-1.0;
   if(!SymbolInfoTick(_Symbol,t) || _Point<=0.0) return -1.0;
   spread_points=(t.ask-t.bid)/_Point;
   if(spread_points<0.0) return -1.0;
   ENUM_ORDER_TYPE ot=(d>0 ? ORDER_TYPE_BUY : ORDER_TYPE_SELL);
   double pnl=0.0;
   double entry=(d>0 ? t.ask : t.bid);
   double exitp=(d>0 ? t.bid : t.ask);
   if(!OrderCalcProfit(ot,_Symbol,lot,entry,exitp,pnl)) return -1.0;
   return MathAbs(pnl);
}

bool V59OwnedPosition(ulong &ticket,int &dir,double &entry,double &sl,double &tp)
{
   ticket=0;dir=0;entry=0.0;sl=0.0;tp=0.0;
   for(int i=PositionsTotal()-1;i>=0;--i)
   {
      ulong t=PositionGetTicket(i);
      if(t==0 || !PositionSelectByTicket(t)) continue;
      if(PositionGetString(POSITION_SYMBOL)!=_Symbol) continue;
      if((long)PositionGetInteger(POSITION_MAGIC)!=InpV59Magic) continue;
      ticket=t;
      long pt=PositionGetInteger(POSITION_TYPE);
      dir=(pt==POSITION_TYPE_BUY ? 1 : -1);
      entry=PositionGetDouble(POSITION_PRICE_OPEN);
      sl=PositionGetDouble(POSITION_SL);
      tp=PositionGetDouble(POSITION_TP);
      return true;
   }
   return false;
}

bool V59BuildStopTarget(const int d,V59Features &f,const double entry,
                        double &stop,double &tp,double &risk_cash,double &risk_pct,
                        double &margin_cash,double &spread_points,double &spread_cash,string &reject)
{
   reject="";
   if(d>0) stop=f.swing_low-InpV59StopAtrBuffer*f.atr15;
   else stop=f.swing_high+InpV59StopAtrBuffer*f.atr15;
   if((d>0 && stop>=entry) || (d<0 && stop<=entry)){reject="invalid_structural_stop";return false;}
   double dist=MathAbs(entry-stop);
   double dist_atr=(f.atr15>0.0 ? dist/f.atr15 : 999.0);
   if(dist_atr>InpV59MaxStopATR){reject="stop_too_far_atr";return false;}

   long stops_level=SymbolInfoInteger(_Symbol,SYMBOL_TRADE_STOPS_LEVEL);
   double min_dist=(double)stops_level*_Point;
   if(min_dist>0.0 && dist<min_dist){reject="broker_stop_too_close";return false;}

   risk_cash=V59RiskCash(d,entry,stop,InpV59FixedLot);
   if(risk_cash<=0.0){reject="risk_calc_failed";return false;}
   double eq=AccountInfoDouble(ACCOUNT_EQUITY);
   risk_pct=(eq>0.0 ? 100.0*risk_cash/eq : 0.0);
   if(risk_cash>InpV59MaxStopRiskCash+1e-9){reject="structural_risk_cash_cap";return false;}

   spread_cash=V59SpreadCash(d,InpV59FixedLot,spread_points);
   if(spread_cash<0.0){reject="spread_calc_failed";return false;}
   double spread_allowed=MathMin(InpV59MaxSpreadCash,risk_cash*(InpV59MaxSpreadRiskPct/100.0));
   if(spread_cash>spread_allowed+1e-9){reject="spread_cost_guard";return false;}

   ENUM_ORDER_TYPE ot=(d>0 ? ORDER_TYPE_BUY : ORDER_TYPE_SELL);
   if(!OrderCalcMargin(ot,_Symbol,InpV59FixedLot,entry,margin_cash)){reject="margin_calc_failed";return false;}
   double free_margin=AccountInfoDouble(ACCOUNT_MARGIN_FREE);
   if(free_margin<=0.0 || margin_cash>free_margin*(InpV59MaxMarginUsagePct/100.0))
   {reject="margin_guard";return false;}

   tp=entry+d*InpV59ActualRR*dist;
   if(!MathIsValidNumber(tp) || tp<=0.0){reject="invalid_target";return false;}
   return true;
}

void V59StartShadow(const int d,const double entry,const double stop,const double risk_cash,const int score)
{
   g_shadow_open=true;g_shadow_dir=d;g_shadow_entry_time=TimeCurrent();g_shadow_entry=entry;g_shadow_stop=stop;
   g_shadow_risk_dist=MathAbs(entry-stop);g_shadow_risk_cash=risk_cash;g_shadow_score=score;g_shadow_bars=0;
   g_shadow_max_r=-1000.0;g_shadow_min_r=1000.0;
   g_rr2_done=false;g_rr25_done=false;g_rr3_done=false;g_rr2=0.0;g_rr25=0.0;g_rr3=0.0;
}

void V59FinishShadow(const string reason)
{
   if(!g_shadow_open) return;
   if(!g_rr2_done) g_rr2=(g_shadow_max_r>=2.0 ? 2.0 : -1.0);
   if(!g_rr25_done) g_rr25=(g_shadow_max_r>=2.5 ? 2.5 : -1.0);
   if(!g_rr3_done) g_rr3=(g_shadow_max_r>=3.0 ? 3.0 : -1.0);
   string row=TimeToString(g_shadow_entry_time,TIME_DATE|TIME_MINUTES|TIME_SECONDS)+","+
      TimeToString(TimeCurrent(),TIME_DATE|TIME_MINUTES|TIME_SECONDS)+","+
      IntegerToString(g_shadow_dir)+","+DoubleToString(g_shadow_entry,_Digits)+","+
      DoubleToString(g_shadow_stop,_Digits)+","+DoubleToString(g_shadow_risk_cash,4)+","+
      IntegerToString(g_shadow_score)+","+DoubleToString(g_shadow_max_r,4)+","+
      DoubleToString(g_shadow_min_r,4)+","+DoubleToString(g_rr2,4)+","+
      DoubleToString(g_rr25,4)+","+DoubleToString(g_rr3,4)+","+IntegerToString(g_shadow_bars)+","+reason;
   V59Append(V59_SHADOW,row);
   g_shadow_open=false;
}

void V59UpdateShadow()
{
   if(!g_shadow_open || g_shadow_risk_dist<=0.0) return;
   MqlTick t;
   if(!SymbolInfoTick(_Symbol,t)) return;
   double px=(g_shadow_dir>0 ? t.bid : t.ask);
   double r=(g_shadow_dir*(px-g_shadow_entry))/g_shadow_risk_dist;
   if(r>g_shadow_max_r) g_shadow_max_r=r;
   if(r<g_shadow_min_r) g_shadow_min_r=r;
   if(!g_rr2_done && r>=2.0){g_rr2=2.0;g_rr2_done=true;}
   if(!g_rr25_done && r>=2.5){g_rr25=2.5;g_rr25_done=true;}
   if(!g_rr3_done && r>=3.0){g_rr3=3.0;g_rr3_done=true;}
   if(r<=-1.0)
   {
      if(!g_rr2_done){g_rr2=-1.0;g_rr2_done=true;}
      if(!g_rr25_done){g_rr25=-1.0;g_rr25_done=true;}
      if(!g_rr3_done){g_rr3=-1.0;g_rr3_done=true;}
      V59FinishShadow("structural_stop");
      return;
   }
   if(g_rr2_done && g_rr25_done && g_rr3_done){V59FinishShadow("all_targets_resolved");return;}
   if(g_shadow_bars>=InpV59MaxBarsInTrade){V59FinishShadow("time_exit");return;}
}

void V59EnsureHeaders()
{
   if(!FileIsExist(V59_EVAL,FILE_COMMON))
      V59Append(V59_EVAL,"time,h4_trend,h1_trend,m15_trend,structure_dir,bos_choch_dir,fvg_dir,liquidity_sweep_dir,order_block_retest_dir,pullback_dir,di_dir,macd_dir,location_dir,atr15,rsi2,rsi14,adx,plus_di,minus_di,macd,macd_slope,distance_ema_atr,range_location,long_score,short_score,selected_direction,decision_reason,entry,stop,tp,risk_cash,risk_pct,margin_cash,spread_points,spread_cash,feasible,reject_reason,screen_only");
   if(!FileIsExist(V59_EVENTS,FILE_COMMON))
      V59Append(V59_EVENTS,"time,event,direction,detail,value1,value2,value3");
   if(!FileIsExist(V59_DEALS,FILE_COMMON))
      V59Append(V59_DEALS,"time,deal,entry,deal_type,reason,price,volume,profit,commission,swap,fee");
   if(!FileIsExist(V59_SHADOW,FILE_COMMON))
      V59Append(V59_SHADOW,"entry_time,exit_time,direction,entry,stop,risk_cash,score,max_r,min_r,result_2r,result_2p5r,result_3r,bars,reason");
}

void V59EvaluateBar()
{
   V59Features f;
   bool ready=V59BuildFeatures(f);
   string why=(ready ? "" : "feature_not_ready");
   int d=(ready ? V59SelectDirection(f,why) : 0);

   MqlTick t;
   bool tick_ok=SymbolInfoTick(_Symbol,t);
   double entry=(tick_ok && d!=0 ? (d>0 ? t.ask : t.bid) : 0.0);
   double stop=0.0,tp=0.0,risk_cash=0.0,risk_pct=0.0,margin_cash=0.0,spread_points=0.0,spread_cash=0.0;
   string reject=(d==0 ? why : "");
   bool feasible=false;
   if(d!=0 && tick_ok)
      feasible=V59BuildStopTarget(d,f,entry,stop,tp,risk_cash,risk_pct,margin_cash,spread_points,spread_cash,reject);
   else if(d!=0 && !tick_ok) reject="tick_unavailable";

   string row=TimeToString(TimeCurrent(),TIME_DATE|TIME_MINUTES|TIME_SECONDS)+","+
      IntegerToString(f.h4_trend)+","+IntegerToString(f.h1_trend)+","+IntegerToString(f.m15_trend)+","+
      IntegerToString(f.structure_dir)+","+IntegerToString(f.bos_choch_dir)+","+IntegerToString(f.fvg_dir)+","+
      IntegerToString(f.liquidity_sweep_dir)+","+IntegerToString(f.order_block_retest_dir)+","+
      IntegerToString(f.pullback_dir)+","+IntegerToString(f.di_dir)+","+IntegerToString(f.macd_dir)+","+
      IntegerToString(f.location_dir)+","+DoubleToString(f.atr15,5)+","+DoubleToString(f.rsi2,3)+","+
      DoubleToString(f.rsi14,3)+","+DoubleToString(f.adx,3)+","+DoubleToString(f.plus_di,3)+","+
      DoubleToString(f.minus_di,3)+","+DoubleToString(f.macd,6)+","+DoubleToString(f.macd_slope,6)+","+
      DoubleToString(f.distance_ema_atr,4)+","+DoubleToString(f.range_location,4)+","+
      IntegerToString(f.long_score)+","+IntegerToString(f.short_score)+","+IntegerToString(d)+","+why+","+
      DoubleToString(entry,_Digits)+","+DoubleToString(stop,_Digits)+","+DoubleToString(tp,_Digits)+","+
      DoubleToString(risk_cash,4)+","+DoubleToString(risk_pct,4)+","+DoubleToString(margin_cash,4)+","+
      DoubleToString(spread_points,2)+","+DoubleToString(spread_cash,4)+","+IntegerToString((int)feasible)+","+
      reject+","+IntegerToString((int)InpV59ScreenOnly);
   V59Append(V59_EVAL,row);

   if(d==0 || !feasible) return;
   if(g_shadow_open) return;

   int score=(d>0 ? f.long_score : f.short_score);
   V59StartShadow(d,entry,stop,risk_cash,score);
   V59Append(V59_EVENTS,TimeToString(TimeCurrent(),TIME_DATE|TIME_MINUTES|TIME_SECONDS)+",SIGNAL,"+
      IntegerToString(d)+","+why+","+DoubleToString(risk_cash,4)+","+DoubleToString(spread_cash,4)+","+
      IntegerToString(score));

   if(InpV59ScreenOnly) return;

   ulong ticket=0;int pdir=0;double pe=0,ps=0,pt=0;
   if(V59OwnedPosition(ticket,pdir,pe,ps,pt)) return;

   g_trade.SetExpertMagicNumber(InpV59Magic);
   g_trade.SetDeviationInPoints(50);
   bool sent=false;
   if(d>0) sent=g_trade.Buy(InpV59FixedLot,_Symbol,0.0,stop,tp,"V59 L");
   else sent=g_trade.Sell(InpV59FixedLot,_Symbol,0.0,stop,tp,"V59 S");
   string detail=(sent ? "sent" : "rejected_"+IntegerToString((int)g_trade.ResultRetcode()));
   V59Append(V59_EVENTS,TimeToString(TimeCurrent(),TIME_DATE|TIME_MINUTES|TIME_SECONDS)+",ORDER,"+
      IntegerToString(d)+","+detail+","+DoubleToString(entry,_Digits)+","+DoubleToString(stop,_Digits)+","+
      DoubleToString(tp,_Digits));
}

int OnInit()
{
   if(!MQLInfoInteger(MQL_TESTER))
   {
      Print("V59 REFUSED: STRATEGY TESTER ONLY");
      return INIT_FAILED;
   }
   if(_Period!=PERIOD_M15)
   {
      Print("V59 REFUSED: M15 REQUIRED");
      return INIT_FAILED;
   }
   if(InpV59FixedLot!=0.01 || InpV59ActualRR<2.0 || InpV59ActualRR>3.0 || InpV59MaxStopRiskCash<=0.0)
      return INIT_PARAMETERS_INCORRECT;
   g_trade.SetExpertMagicNumber(InpV59Magic);
   V59EnsureHeaders();
   V59WriteStatus("READY","integrated_bidirectional_rr");
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   if(g_shadow_open) V59FinishShadow("tester_end");
   V59WriteStatus("STOPPED",IntegerToString(reason));
}

void OnTick()
{
   V59UpdateShadow();
   datetime bar=iTime(_Symbol,PERIOD_M15,0);
   if(bar<=0 || bar==g_last_m15_bar) return;
   g_last_m15_bar=bar;
   if(g_shadow_open) g_shadow_bars++;
   ulong ticket=0;int d=0;double e=0,s=0,t=0;
   if(!InpV59ScreenOnly && V59OwnedPosition(ticket,d,e,s,t)) return;
   if(g_shadow_open) return;
   V59EvaluateBar();
}

void OnTradeTransaction(const MqlTradeTransaction &trans,const MqlTradeRequest &request,const MqlTradeResult &result)
{
   if(trans.type!=TRADE_TRANSACTION_DEAL_ADD || trans.deal==0) return;
   if(!HistoryDealSelect(trans.deal)) return;
   if(HistoryDealGetString(trans.deal,DEAL_SYMBOL)!=_Symbol) return;
   if((long)HistoryDealGetInteger(trans.deal,DEAL_MAGIC)!=InpV59Magic) return;
   long entry=HistoryDealGetInteger(trans.deal,DEAL_ENTRY);
   long dtype=HistoryDealGetInteger(trans.deal,DEAL_TYPE);
   long reason=HistoryDealGetInteger(trans.deal,DEAL_REASON);
   double price=HistoryDealGetDouble(trans.deal,DEAL_PRICE);
   double volume=HistoryDealGetDouble(trans.deal,DEAL_VOLUME);
   double profit=HistoryDealGetDouble(trans.deal,DEAL_PROFIT);
   double commission=HistoryDealGetDouble(trans.deal,DEAL_COMMISSION);
   double swap=HistoryDealGetDouble(trans.deal,DEAL_SWAP);
   double fee=HistoryDealGetDouble(trans.deal,DEAL_FEE);
   V59Append(V59_DEALS,TimeToString(TimeCurrent(),TIME_DATE|TIME_MINUTES|TIME_SECONDS)+","+
      IntegerToString((long)trans.deal)+","+IntegerToString(entry)+","+IntegerToString(dtype)+","+
      IntegerToString(reason)+","+DoubleToString(price,_Digits)+","+DoubleToString(volume,2)+","+
      DoubleToString(profit,4)+","+DoubleToString(commission,4)+","+DoubleToString(swap,4)+","+
      DoubleToString(fee,4));
}
'''


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def validate(text: str) -> None:
    required = (
        "STRATEGY TESTER ONLY",
        "InpV59FixedLot = 0.01",
        "InpV59Magic = 590059",
        "V59ScoreDirection(1,f)",
        "V59ScoreDirection(-1,f)",
        "short_regime",
        "long_regime",
        "V59ConfirmedSwings",
        "V59RecentFvgDir",
        "V59OrderBlockRetestDir",
        "V59BuildStopTarget",
        "structural_risk_cash_cap",
        "InpV59ActualRR = 3.0",
        "result_2r,result_2p5r,result_3r",
        "CopyRates(_Symbol,PERIOD_M15,1,320,m15)",
        "CopyRates(_Symbol,PERIOD_H1,1,260,h1)",
        "CopyRates(_Symbol,PERIOD_H4,1,140,h4)",
        "g_trade.Buy",
        "g_trade.Sell",
    )
    for token in required:
        if token not in text:
            raise RuntimeError(f"V59 required token missing: {token}")
    forbidden = (
        "V55RiskBoundVolume",
        "v52_b4_or_b3_trend_bos",
        "g_v57_entry_allowed",
        "PositionClosePartial",
    )
    for token in forbidden:
        if token in text:
            raise RuntimeError(f"V59 forbidden inherited token present: {token}")
    if text.count("{") != text.count("}"):
        raise RuntimeError("V59 MQL brace imbalance")


def build(output: Path) -> str:
    text = MQL.replace("\n", "\r\n")
    validate(text)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8", newline="")
    digest = sha256(output)
    print(f"V59 source built sha256={digest} path={output}")
    return digest


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()
    build(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
