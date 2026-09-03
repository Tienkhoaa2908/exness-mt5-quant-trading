#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import importlib.util
import io
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "scripts" / "audit_v70_baseline_drift_against_accepted_v69.py"


def load():
    spec = importlib.util.spec_from_file_location("v70_baseline_drift_audit_test", AUDIT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def csv_text(exit_price: float, exit_profit: float) -> str:
    out = io.StringIO()
    w = csv.DictWriter(out, fieldnames=["time", "entry", "price", "profit", "commission", "swap", "fee", "reason"])
    w.writeheader()
    w.writerow({"time": "2025.09.01 00:00:01", "entry": 0, "price": 3500, "profit": 0, "commission": 0, "swap": 0, "fee": 0, "reason": 0})
    w.writerow({"time": "2025.09.01 00:01:01", "entry": 1, "price": exit_price, "profit": exit_profit, "commission": -0.05, "swap": 0, "fee": 0, "reason": 4})
    return out.getvalue()


def test_same_exit_time_price_drift_is_not_accounting_drift() -> None:
    m = load()
    a = {"time": "2025.09.01 00:01:01", "price": "3501.00", "profit": "1.00", "commission": "-0.05", "swap": "0", "fee": "0", "reason": "4"}
    b = dict(a)
    b["price"] = "3500.93"
    b["profit"] = "0.93"
    assert m.classify_pair(a, b) == "EXIT_PRICE_DRIFT"
    assert abs(m.legacy_pnl(b) - m.legacy_pnl(a) + 0.07) < 1e-9


def test_audit_uses_hash_pinned_accepted_zip_and_local_v70_deals() -> None:
    m = load()
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        zpath = repo / "runtime" / "v69_confirm_separation_retest" / "OUTPUT_V69" / "v69_confirm_separation_retest_research.zip"
        zpath.parent.mkdir(parents=True)
        with zipfile.ZipFile(zpath, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for month in m.MONTHS:
                zf.writestr(
                    f"runtime/v69_confirm_separation_retest/OUTPUT_V69/holdout_{month}_long/V64_DEALS.csv",
                    csv_text(3501.00, 1.00) if month == "2025_09" else csv_text(3500.00, 0.00).splitlines()[0] + "\n",
                )
        digest = hashlib.sha256(zpath.read_bytes()).hexdigest()
        m.ACCEPTED_V69_ZIP_SHA256 = digest
        for month in m.MONTHS:
            p = repo / "runtime" / "v70_exit_harvest_research" / "OUTPUT_V70" / f"holdout_{month}_long" / "V64_DEALS.csv"
            p.parent.mkdir(parents=True, exist_ok=True)
            if month == "2025_09":
                p.write_text(csv_text(3500.93, 0.93), encoding="utf-8")
            else:
                p.write_text(csv_text(3500.00, 0.00).splitlines()[0] + "\n", encoding="utf-8")
        result = m.audit(repo, zpath)
        assert result["accepted_trades"] == 1
        assert result["v70_trades"] == 1
        assert result["classification"] == "SAME_EXIT_TIMES_VALUE_DRIFT"
        assert abs(result["delta_usd"] + 0.07) < 1e-9
        assert result["difference_classes"] == {"EXIT_PRICE_DRIFT": 1}


def test_audit_script_is_read_only_and_pins_accepted_v69_hash() -> None:
    src = AUDIT.read_text(encoding="utf-8")
    assert "e35306d604fe07ec6e2606e51c49c699b3c029be93b859e48abf74bc970f2acb" in src
    for forbidden in ("terminal64.exe", "metaeditor64.exe", "PositionModify", ".Buy(", ".Sell("):
        assert forbidden not in src


if __name__ == "__main__":
    tests = [obj for name, obj in sorted(globals().items()) if name.startswith("test_") and callable(obj)]
    for fn in tests:
        fn()
        print(f"PASS {fn.__name__}")
    print(f"V70 baseline drift audit tests PASS count={len(tests)}")
