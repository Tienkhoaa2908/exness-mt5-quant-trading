#!/usr/bin/env python3
from __future__ import annotations

import csv
import importlib.util
from datetime import datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
V45_BASE = REPO / "runtime" / "v45_multiyear_validation" / "RUN_V45_MULTIYEAR_ONE_SHOT.py"
PRIMARY = "v46_hl10_thr0p05_breadth4"
BOOK = "usd40_r1p0_cent_continuous"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None: raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod


base = load_module(V45_BASE, "v45_base_v48_status")


def kv(path: Path) -> dict[str, str]:
    out = {}
    if not path.is_file(): return out
    for line in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        if "=" in line:
            k, v = line.split("=", 1); out[k.strip()] = v.strip()
    return out


def weekdays_inclusive(start: datetime, end: datetime) -> int:
    d = start.date(); e = end.date(); n = 0
    while d <= e:
        if d.weekday() < 5: n += 1
        d += timedelta(days=1)
    return n


def trade_stats(path: Path) -> dict:
    rows = []
    if path.is_file():
        with path.open("r", encoding="utf-8-sig", newline="") as fh:
            for r in csv.DictReader(fh):
                if r.get("candidate") == PRIMARY and r.get("book") == BOOK:
                    rows.append(r)
    rs = []
    for r in rows:
        try: rs.append(float(r.get("r_multiple", "") or 0.0))
        except ValueError: pass
    gp = sum(x for x in rs if x > 0); gl = -sum(x for x in rs if x < 0)
    pf = gp / gl if gl > 0 else (999.0 if gp > 0 else 0.0)
    return {"closed": len(rs), "sum_r": sum(rs), "pf": pf, "last": rows[-1] if rows else None}


def main() -> int:
    _, common, _, _ = base.locate_mt5()
    paper = common / "mt5_quant" / "paper"
    status_path = paper / "V48_DEMO_PAPER_STATUS.txt"
    latest_path = paper / "V48_DEMO_PAPER_LATEST.txt"
    init_path = paper / "V48_DEMO_PAPER_INIT.txt"
    s = kv(status_path); latest = kv(latest_path); init = kv(init_path)

    if not s:
        print("=== V48 DEMO-PAPER STATUS ===")
        print("STATUS=NOT_READY")
        if init:
            for key in ("updated", "stage", "reason", "symbol", "period", "account_trade_mode", "account_server", "terminal_connected", "terminal_trade_allowed", "mql_trade_allowed", "terminal_dlls_allowed", "mql_dlls_allowed", "broker_orders", "live_authorized"):
                print(f"INIT_{key.upper()}={init.get(key,'')}")
            if init.get("stage") == "REFUSED":
                print("DECISION=FIX_STARTUP_GUARD_AND_RESTART")
            else:
                print("DECISION=WAIT_OR_CHECK_ATTACH_DIAGNOSTICS")
        else:
            print(f"INIT_DIAGNOSTIC_MISSING={init_path}")
            print("DECISION=EA_NOT_ATTACHED_OR_NOT_INITIALIZED")
        print("REAL_MONEY_AUTHORIZED=0")
        return 2

    run_folder = latest.get("run_folder") or s.get("run_folder", "")
    run_dir = common / Path(run_folder.replace("\\", "/")) if run_folder else None
    trades = run_dir / "trades.csv" if run_dir else Path("__missing__")
    ts = trade_stats(trades)

    try: start = datetime.strptime(s["session_start"], "%Y.%m.%d %H:%M:%S")
    except Exception: start = datetime.now()
    now = datetime.now()
    weekdays = weekdays_inclusive(start, now)
    calendar_days = (now.date() - start.date()).days + 1

    dd = float(s.get("max_mtm_dd_pct", "0") or 0.0)
    closed = int(ts["closed"]); sum_r = float(ts["sum_r"]); pf = float(ts["pf"])
    ready = weekdays >= 10 and closed >= 20
    hard_timeout = calendar_days >= 30
    risk_hold = dd > 10.0 or (closed >= 20 and (sum_r < -5.0 or pf < 0.80))

    print("=== V48 DEMO-PAPER STATUS ===")
    for key in (
        "updated", "session_start", "account_mode", "terminal_trade_allowed", "mql_trade_allowed",
        "terminal_dlls_allowed", "mql_dlls_allowed", "candidate", "book", "healthy_hl10_count",
        "balance", "equity", "unrealized_pnl", "current_price", "max_mtm_dd_pct", "position_open",
        "direction", "entry", "stop", "tp", "open_r", "run_id"
    ):
        print(f"{key.upper()}={s.get(key,'')}")
    print(f"RUN_FOLDER={run_folder}")
    print(f"PAPER_CLOSED_TRADES={closed}")
    print(f"PAPER_SUM_R={sum_r:.6f}")
    print(f"PAPER_PF_R={pf:.6f}")
    print(f"ELAPSED_WEEKDAYS_APPROX={weekdays}")
    print(f"ELAPSED_CALENDAR_DAYS={calendar_days}")
    print(f"FINITE_GATE_READY={1 if ready else 0}")
    print(f"HARD_30D_STOP={1 if hard_timeout else 0}")
    print(f"RISK_HOLD={1 if risk_hold else 0}")
    print("BROKER_ORDERS=0")
    print("REAL_MONEY_AUTHORIZED=0")

    if risk_hold:
        print("DECISION=HOLD")
    elif ready or hard_timeout:
        print("DECISION=READY_FOR_OPERATIONAL_REVIEW")
    else:
        print("DECISION=CONTINUE_FINITE_PAPER_CAMPAIGN")
    return 0


if __name__ == "__main__":
    try: raise SystemExit(main())
    except Exception as exc:
        print(f"FATAL: {type(exc).__name__}: {exc}")
        raise
