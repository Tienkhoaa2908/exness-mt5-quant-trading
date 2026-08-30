#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
V60_BUILDER = HERE / "build_v60_small_loss_cash_target_source.py"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


v60 = load(V60_BUILDER, "v60_parent_for_v61")
EXPERT_NAME = "V61ProfitRatchetM5Refinement"
FIXED_LOT = 0.01
MAGIC = 610061


def replace_once(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        raise RuntimeError(f"V61 {label} drifted expected=1 actual={n}")
    return text.replace(old, new, 1)


M5_HELPER = r'''
bool V61M5RefinedStop(const int d,const double entry,double &stop)
{
   stop=0.0;
   if(!InpV61UseM5Refinement || d==0 || entry<=0.0) return false;
   MqlRates m5[];
   ArraySetAsSeries(m5,true);
   int n=CopyRates(_Symbol,PERIOD_M5,1,180,m5);
   if(n<120) return false;

   double atr=V61ATR(m5,n,14,0);
   double ema20=V61EMA(m5,n,20,0);
   double ema50=V61EMA(m5,n,50,0);
   if(atr<=0.0 || ema20<=0.0 || ema50<=0.0) return false;

   bool trend_ok=(d>0 ? (ema20>ema50 && m5[0].close>ema20)
                       : (ema20<ema50 && m5[0].close<ema20));
   if(!trend_ok) return false;

   double sh1=0,sh2=0,sl1=0,sl2=0;int shi1=-1,shi2=-1,sli1=-1,sli2=-1;
   V61ConfirmedSwings(m5,n,sh1,shi1,sh2,shi2,sl1,sli1,sl2,sli2);
   if(shi2<0 || sli2<0) return false;

   bool structure_ok=(d>0 ? (sl1>=sl2 || sh1>sh2) : (sh1<=sh2 || sl1<sl2));
   if(!structure_ok) return false;

   if(d>0) stop=sl1-InpV61M5StopAtrBuffer*atr;
   else stop=sh1+InpV61M5StopAtrBuffer*atr;

   if((d>0 && stop>=entry) || (d<0 && stop<=entry)) return false;
   return true;
}
'''

RATCHET_HELPER = r'''
void V61ManageProfitRatchet()
{
   if(InpV61ScreenOnly || InpV61ProfitArmCash<=0.0 || InpV61ProfitLockCash<=0.0) return;

   ulong ticket=0;int d=0;double entry=0.0,sl=0.0,tp=0.0;
   if(!V61OwnedPosition(ticket,d,entry,sl,tp)) return;

   MqlTick tick;
   if(!SymbolInfoTick(_Symbol,tick)) return;
   double exitp=(d>0 ? tick.bid : tick.ask);
   ENUM_ORDER_TYPE ot=(d>0 ? ORDER_TYPE_BUY : ORDER_TYPE_SELL);
   double floating=0.0;
   if(!OrderCalcProfit(ot,_Symbol,InpV61FixedLot,entry,exitp,floating)) return;
   if(floating+1e-9<InpV61ProfitArmCash) return;

   double lock_price=0.0;
   if(!V61PriceForCashTarget(d,entry,InpV61ProfitLockCash,lock_price)) return;

   long stops_level=SymbolInfoInteger(_Symbol,SYMBOL_TRADE_STOPS_LEVEL);
   long freeze_level=SymbolInfoInteger(_Symbol,SYMBOL_TRADE_FREEZE_LEVEL);
   double broker_buffer=MathMax((double)stops_level,(double)freeze_level)*_Point;

   bool improves=(d>0 ? (lock_price>sl+_Point) : (sl<=0.0 || lock_price<sl-_Point));
   bool geometry=(d>0 ? (lock_price<tick.bid-broker_buffer) : (lock_price>tick.ask+broker_buffer));
   if(!improves || !geometry) return;

   g_trade.SetExpertMagicNumber(InpV61Magic);
   bool modified=g_trade.PositionModify(ticket,lock_price,tp);
   V61Append(V61_EVENTS,TimeToString(TimeCurrent(),TIME_DATE|TIME_MINUTES|TIME_SECONDS)+
      ",PROFIT_LOCK,"+IntegerToString(d)+","+(modified?"modified":"modify_failed")+","+
      DoubleToString(floating,4)+","+DoubleToString(lock_price,_Digits)+","+DoubleToString(tp,_Digits));
}
'''

ORDER_PREFLIGHT = r'''
bool V61OrderPreflight(const int d,const double entry,const double stop,const double tp,
                       string &detail,long &retcode)
{
   detail="";
   retcode=0;
   MqlTradeRequest req={};
   MqlTradeCheckResult chk={};
   req.action=TRADE_ACTION_DEAL;
   req.magic=InpV61Magic;
   req.symbol=_Symbol;
   req.volume=InpV61FixedLot;
   req.type=(d>0 ? ORDER_TYPE_BUY : ORDER_TYPE_SELL);
   req.price=entry;
   req.sl=stop;
   req.tp=tp;
   req.deviation=50;
   req.type_time=ORDER_TIME_GTC;

   long fm=SymbolInfoInteger(_Symbol,SYMBOL_FILLING_MODE);
   if((fm & SYMBOL_FILLING_FOK)==SYMBOL_FILLING_FOK) req.type_filling=ORDER_FILLING_FOK;
   else if((fm & SYMBOL_FILLING_IOC)==SYMBOL_FILLING_IOC) req.type_filling=ORDER_FILLING_IOC;
   else req.type_filling=ORDER_FILLING_RETURN;

   if(!OrderCheck(req,chk))
   {
      retcode=(long)GetLastError();
      detail="ordercheck_call_failed";
      return false;
   }
   retcode=(long)chk.retcode;
   if(chk.retcode!=0 && chk.retcode!=TRADE_RETCODE_DONE && chk.retcode!=TRADE_RETCODE_PLACED)
   {
      detail="ordercheck_"+IntegerToString((int)chk.retcode);
      return false;
   }
   detail="ordercheck_ok";
   return true;
}
'''


def transform() -> str:
    text = v60.transform()
    text = replace_once(text, '#property version   "60.00"', '#property version   "61.00"', "version")
    text = text.replace("V60", "V61").replace("v60", "v61")

    text = replace_once(text, "input long   InpV61Magic = 600060;", "input long   InpV61Magic = 610061;", "magic")
    text = replace_once(
        text,
        "input double InpV61PrimaryTargetCash = 2.00;\n"
        "input double InpV61ShadowTargetCash2 = 2.00;\n"
        "input double InpV61ShadowTargetCash3 = 3.00;\n"
        "input double InpV61ShadowTargetCash4 = 4.00;\n"
        "input double InpV61SoftLossCash = 1.00;\n"
        "input double InpV61MaxStopRiskCash = 1.25;",
        "input double InpV61PrimaryTargetCash = 3.00;\n"
        "input double InpV61ShadowTargetCash2 = 2.00;\n"
        "input double InpV61ShadowTargetCash3 = 3.00;\n"
        "input double InpV61ShadowTargetCash4 = 4.00;\n"
        "input double InpV61ProfitArmCash = 2.00;\n"
        "input double InpV61ProfitLockCash = 1.00;\n"
        "input double InpV61SoftLossCash = 1.00;\n"
        "input double InpV61MinStopRiskCash = 0.75;\n"
        "input double InpV61MaxStopRiskCash = 1.25;",
        "cash target and risk band",
    )
    text = replace_once(
        text,
        "input double InpV61StopAtrBuffer = 0.15;",
        "input double InpV61StopAtrBuffer = 0.15;\n"
        "input bool   InpV61UseM5Refinement = true;\n"
        "input double InpV61M5StopAtrBuffer = 0.10;",
        "m5 inputs",
    )

    text = replace_once(text, "bool V61BuildStopTarget", M5_HELPER + "\nbool V61BuildStopTarget", "m5 helper")

    old_stop = '''   reject="";
   if(d>0) stop=f.swing_low-InpV61StopAtrBuffer*f.atr15;
   else stop=f.swing_high+InpV61StopAtrBuffer*f.atr15;
   if((d>0 && stop>=entry) || (d<0 && stop<=entry)){reject="invalid_structural_stop";return false;}
   double dist=MathAbs(entry-stop);
   double dist_atr=(f.atr15>0.0 ? dist/f.atr15 : 999.0);
   if(dist_atr>InpV61MaxStopATR){reject="stop_too_far_atr";return false;}'''
    new_stop = '''   reject="";
   g_v61_stop_source="m15";
   if(d>0) stop=f.swing_low-InpV61StopAtrBuffer*f.atr15;
   else stop=f.swing_high+InpV61StopAtrBuffer*f.atr15;

   double micro=0.0;
   if(V61M5RefinedStop(d,entry,micro))
   {
      double base_dist=MathAbs(entry-stop);
      double micro_dist=MathAbs(entry-micro);
      if(micro_dist>0.0 && micro_dist<base_dist)
      {
         stop=micro;
         g_v61_stop_source="m5";
      }
   }

   if((d>0 && stop>=entry) || (d<0 && stop<=entry)){reject="invalid_structural_stop";return false;}
   double dist=MathAbs(entry-stop);
   double dist_atr=(f.atr15>0.0 ? dist/f.atr15 : 999.0);
   if(dist_atr>InpV61MaxStopATR){reject="stop_too_far_atr";return false;}'''
    text = replace_once(text, old_stop, new_stop, "stop refinement")

    text = replace_once(
        text,
        "if(risk_cash>InpV61MaxStopRiskCash+1e-9){reject=\"structural_risk_cash_cap\";return false;}",
        "if(risk_cash<InpV61MinStopRiskCash-1e-9){reject=\"structural_risk_too_tight\";return false;}\n"
        "   if(risk_cash>InpV61MaxStopRiskCash+1e-9){reject=\"structural_risk_cash_cap\";return false;}",
        "risk band",
    )

    anchor = "CTrade g_trade;\ndatetime g_last_m15_bar=0;"
    text = replace_once(text, anchor, anchor + '\nstring g_v61_stop_source="";', "stop source global")

    text = replace_once(
        text,
        'reject+","+IntegerToString((int)InpV61ScreenOnly);',
        'reject+","+g_v61_stop_source+","+IntegerToString((int)InpV61ScreenOnly);',
        "eval row stop source",
    )
    text = replace_once(
        text,
        'spread_cash,feasible,reject_reason,screen_only");',
        'spread_cash,feasible,reject_reason,stop_source,screen_only");',
        "eval header stop source",
    )

    text = replace_once(text, '"V61 $2 L"', '"V61 $3RATCHET L"', "long comment")
    text = replace_once(text, '"V61 $2 S"', '"V61 $3RATCHET S"', "short comment")

    text = replace_once(text, "void V61EvaluateBar()", ORDER_PREFLIGHT + "\nvoid V61EvaluateBar()", "ordercheck helper")
    old_send = '''   g_trade.SetExpertMagicNumber(InpV61Magic);
   g_trade.SetDeviationInPoints(50);
   bool sent=false;
   if(d>0) sent=g_trade.Buy(InpV61FixedLot,_Symbol,0.0,stop,tp,"V61 $3RATCHET L");
   else sent=g_trade.Sell(InpV61FixedLot,_Symbol,0.0,stop,tp,"V61 $3RATCHET S");
   string detail=(sent ? "sent" : "rejected_"+IntegerToString((int)g_trade.ResultRetcode()));'''
    new_send = '''   string preflight_detail="";long preflight_retcode=0;
   if(!V61OrderPreflight(d,entry,stop,tp,preflight_detail,preflight_retcode))
   {
      V61Append(V61_EVENTS,TimeToString(TimeCurrent(),TIME_DATE|TIME_MINUTES|TIME_SECONDS)+",ORDER_PREFLIGHT,"+
         IntegerToString(d)+","+preflight_detail+","+DoubleToString(entry,_Digits)+","+
         DoubleToString(stop,_Digits)+","+IntegerToString((int)preflight_retcode));
      return;
   }

   g_trade.SetExpertMagicNumber(InpV61Magic);
   g_trade.SetDeviationInPoints(50);
   g_trade.SetTypeFillingBySymbol(_Symbol);
   bool sent=false;
   if(d>0) sent=g_trade.Buy(InpV61FixedLot,_Symbol,0.0,stop,tp,"V61 $3RATCHET L");
   else sent=g_trade.Sell(InpV61FixedLot,_Symbol,0.0,stop,tp,"V61 $3RATCHET S");
   string detail=(sent ? "sent" : "rejected_"+IntegerToString((int)g_trade.ResultRetcode()));'''
    text = replace_once(text, old_send, new_send, "order preflight")

    text = replace_once(text, "void V61MaybeSoftLossCut()", RATCHET_HELPER + "\nvoid V61MaybeSoftLossCut()", "ratchet helper")
    text = replace_once(
        text,
        "   V61UpdateShadow();\n   V61MaybeSoftLossCut();",
        "   V61UpdateShadow();\n   V61ManageProfitRatchet();\n   V61MaybeSoftLossCut();",
        "ratchet tick hook",
    )

    old_init = '''if(InpV61FixedLot!=0.01 || InpV61PrimaryTargetCash<=0.0 || InpV61MaxStopRiskCash<=0.0 ||
      InpV61SoftLossCash<=0.0 || InpV61SoftLossCash>InpV61MaxStopRiskCash ||
      InpV61ShadowTargetCash2<=0.0 || InpV61ShadowTargetCash3<InpV61ShadowTargetCash2 ||
      InpV61ShadowTargetCash4<InpV61ShadowTargetCash3)'''
    new_init = '''if(InpV61FixedLot!=0.01 || InpV61PrimaryTargetCash<=0.0 ||
      InpV61MinStopRiskCash<=0.0 || InpV61MaxStopRiskCash<InpV61MinStopRiskCash ||
      InpV61ProfitArmCash<=0.0 || InpV61ProfitLockCash<=0.0 || InpV61ProfitLockCash>=InpV61ProfitArmCash ||
      InpV61PrimaryTargetCash<=InpV61ProfitArmCash ||
      InpV61SoftLossCash<=0.0 || InpV61SoftLossCash>InpV61MaxStopRiskCash ||
      InpV61ShadowTargetCash2<=0.0 || InpV61ShadowTargetCash3<InpV61ShadowTargetCash2 ||
      InpV61ShadowTargetCash4<InpV61ShadowTargetCash3)'''
    text = replace_once(text, old_init, new_init, "init contract")
    text = replace_once(text, 'V61WriteStatus("READY","small_loss_cash_target");',
                        'V61WriteStatus("READY","profit_ratchet_m5_refinement");', "status")

    return text


def validate(text: str) -> None:
    required = (
        "STRATEGY TESTER ONLY",
        "InpV61FixedLot = 0.01",
        "InpV61Magic = 610061",
        "InpV61PrimaryTargetCash = 3.00",
        "InpV61ProfitArmCash = 2.00",
        "InpV61ProfitLockCash = 1.00",
        "InpV61MinStopRiskCash = 0.75",
        "InpV61MaxStopRiskCash = 1.25",
        "CopyRates(_Symbol,PERIOD_M5,1,180,m5)",
        "V61M5RefinedStop",
        "structural_risk_too_tight",
        "V61ManageProfitRatchet",
        "PROFIT_LOCK",
        "V61OrderPreflight",
        "OrderCheck(req,chk)",
        "g_trade.SetTypeFillingBySymbol(_Symbol)",
        "f.h1_trend==1 && f.h4_trend==1",
        "f.h1_trend==-1 && f.h4_trend==-1",
        "g_trade.Buy",
        "g_trade.Sell",
    )
    for token in required:
        if token not in text:
            raise RuntimeError(f"V61 required token missing: {token}")
    forbidden = ("V60", "v60", "InpV61PrimaryTargetCash = 2.00", "PositionClosePartial")
    for token in forbidden:
        if token in text:
            raise RuntimeError(f"V61 forbidden token present: {token}")
    if text.count("{") != text.count("}"):
        raise RuntimeError("V61 MQL brace imbalance")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def build(output: Path) -> str:
    text = transform().replace("\n", "\r\n")
    validate(text)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8", newline="")
    digest = sha256(output)
    print(f"V61 source built sha256={digest} path={output}")
    return digest


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True, type=Path)
    args = ap.parse_args()
    build(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
