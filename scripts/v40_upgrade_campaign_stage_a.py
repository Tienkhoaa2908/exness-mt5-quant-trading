#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import hashlib
import json
import shutil
import sys

import pandas as pd

SCRIPT_DIR=Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0,str(SCRIPT_DIR))

import v40_upgrade_campaign_stage_a_core as core
from v40_upgrade_campaign_stage_a_core import *  # re-export research contract/helpers for tests


def attach_signal_sources(df: pd.DataFrame, sig: pd.DataFrame, validate: str) -> pd.DataFrame:
    """Attach M15 signal sources without pandas suffix collisions.

    Accepted V38 ``trades.csv`` may already carry ``signal_sources`` while M1
    telemetry may not. Preserve non-empty source metadata already present and
    use the first M15 source only as a fallback. Never create
    ``signal_sources_x`` / ``signal_sources_y``.
    """
    if "signal_sources" not in df.columns:
        return df.merge(sig,on="trade_key",how="left",validate=validate)
    fallback="signal_sources_m15"
    if fallback in df.columns:
        raise RuntimeError(f"unexpected pre-existing column: {fallback}")
    merged=df.merge(
        sig.rename(columns={"signal_sources":fallback}),
        on="trade_key",how="left",validate=validate,
    )
    existing=merged["signal_sources"]
    missing=existing.isna() | existing.astype("string").str.strip().eq("")
    merged.loc[missing,"signal_sources"]=merged.loc[missing,fallback]
    merged=merged.drop(columns=[fallback])
    if "signal_sources_x" in merged.columns or "signal_sources_y" in merged.columns:
        raise RuntimeError("signal_sources suffix collision survived schema adapter")
    return merged


def load_inputs(run: Path, v36_path: Path|None):
    p1,p15,pt=run/"intra_trade_m1_fast.csv",run/"intra_trade_m15.csv",run/"trades.csv"
    for p in (p1,p15,pt):
        if not p.is_file(): raise FileNotFoundError(p)
    m1,m15,trades=pd.read_csv(p1),pd.read_csv(p15),pd.read_csv(pt)
    need_m1={
        "time","candidate","book","entry_time","direction","age_seconds","unrealized_r",
        "mfe_r","mae_r","giveback_from_peak_r","r_delta_1m","tick_count",
        "tick_direction_imbalance","mid_net_move_r","mid_abs_path_r","mid_range_r",
        "spread_mean_points","spread_max_points",
    }
    miss=sorted(need_m1-set(m1.columns))
    if miss: raise RuntimeError(f"V38 M1 columns missing: {miss}")
    need_tr={"candidate","book","entry_time","exit_time","direction","r_multiple","mfe_r","mae_r","giveback_r"}
    miss=sorted(need_tr-set(trades.columns))
    if miss: raise RuntimeError(f"V38 trades columns missing: {miss}")
    for d in (m1,m15,trades):
        d.drop(d[(d.candidate!=core.CONTROL)|(d.book!=core.BOOK)].index,inplace=True)
    if len(trades)!=563:
        raise RuntimeError(f"control trades expected=563 actual={len(trades)}")
    for d in (m1,m15):
        d["time"]=core.ts(d["time"]); d["entry_time"]=core.ts(d["entry_time"]); d["trade_key"]=core.make_key(d)
    trades["entry_time"]=core.ts(trades["entry_time"]); trades["exit_time"]=core.ts(trades["exit_time"]); trades["trade_key"]=core.make_key(trades)
    if trades["trade_key"].duplicated().any(): raise RuntimeError("duplicate trade_key")
    if m1["trade_key"].nunique()!=563:
        raise RuntimeError(f"M1 trade coverage expected=563 actual={m1.trade_key.nunique()}")
    labels=trades[["trade_key","exit_time","r_multiple","mfe_r","mae_r","giveback_r"]].rename(columns={
        "r_multiple":"final_r","mfe_r":"final_mfe_r","mae_r":"final_mae_r","giveback_r":"final_giveback_r"
    })
    m1=m1.merge(labels,on="trade_key",how="inner",validate="many_to_one")
    sig=(m15[["trade_key","time","signal_sources"]].sort_values(["trade_key","time"])
         .groupby("trade_key",as_index=False).first()[["trade_key","signal_sources"]])
    m1=attach_signal_sources(m1,sig,"many_to_one")
    trades=attach_signal_sources(trades,sig,"one_to_one")
    m1["source_family"]=m1["signal_sources"].fillna("").map(core.source_family)
    trades["source_family"]=trades["signal_sources"].fillna("").map(core.source_family)
    m1=m1.sort_values(["trade_key","time"]).reset_index(drop=True)
    g=m1.groupby("trade_key",sort=False)
    for n in (3,5,15):
        m1[f"r_delta_mean_{n}m"]=g["r_delta_1m"].transform(lambda s,n=n:s.rolling(n,min_periods=1).mean())
    m1["r_delta_std_5m"]=g["r_delta_1m"].transform(lambda s:s.rolling(5,min_periods=2).std()).fillna(0)
    m1["r_accel_1m"]=g["r_delta_1m"].diff().fillna(0)
    m1["giveback_delta_1m"]=g["giveback_from_peak_r"].diff().fillna(0)
    m1["tick_count_log1p"]=core.np.log1p(m1["tick_count"].clip(lower=0))
    m1["age_log1p"]=core.np.log1p(m1["age_seconds"].clip(lower=0))
    m1["direction_num"]=m1["direction"].map({"LONG":1.0,"SHORT":-1.0}).fillna(0)
    m1,v36_meta,v36_cal=core.merge_v36_asof(m1,v36_path)
    zone=core.first_passage_labels(m1)
    return m1,zone,trades,{
        "m1_sha256":core.sha256(p1),"m15_sha256":core.sha256(p15),"trades_sha256":core.sha256(pt),
        "m1_rows":int(len(m1)),"control_trades":int(len(trades)),
        "m1_trade_coverage":int(m1.trade_key.nunique()),"zone_rows":int(len(zone)),
        "zone_trades":int(zone.trade_key.nunique()),"v36":v36_meta,
        "signal_source_schema_adapter":"preserve_existing_then_m15_fallback_no_suffix_collision",
    },v36_cal


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def _output_dir_from_argv() -> Path|None:
    try:
        i=sys.argv.index("--output-dir")
        return Path(sys.argv[i+1])
    except (ValueError,IndexError):
        return None

def main() -> None:
    # core.main resolves its module-global load_inputs; replace that one function only.
    core.load_inputs=load_inputs
    core.main()
    out=_output_dir_from_argv()
    if out and out.is_dir():
        core_path=Path(core.__file__).resolve()
        copied=out/"v40_upgrade_campaign_stage_a_core.py"
        shutil.copy2(core_path,copied)
        summary_path=out/"v40_upgrade_campaign_summary.json"
        if summary_path.is_file():
            d=json.loads(summary_path.read_text(encoding="utf-8"))
            d["execution_adapter"]={
                "schema":"v40_windows_signal_source_adapter_v1",
                "entry_sha256":_sha256(Path(__file__).resolve()),
                "core_sha256":_sha256(core_path),
                "rule":"preserve existing non-empty signal_sources, fill blanks from first M15 source, never create _x/_y suffixes",
            }
            summary_path.write_text(json.dumps(d,indent=2,ensure_ascii=False),encoding="utf-8")

if __name__=="__main__":
    main()
