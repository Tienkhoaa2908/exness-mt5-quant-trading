#!/usr/bin/env python3
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BUILDER = REPO / "scripts" / "build_v54_production_readiness_source.py"
RUNNER = REPO / "runtime" / "v54_production_readiness" / "RUN_V54_PRODUCTION_READINESS.py"
PACKAGER = REPO / "runtime" / "v54_production_readiness" / "PACKAGE_V54_EVIDENCE.py"
ADR = REPO / "docs" / "adr" / "ADR-056-v54-production-readiness-safety-envelope.md"


def need(text: str, *tokens: str) -> None:
    for token in tokens:
        assert token in text, token


def main() -> int:
    b = BUILDER.read_text(encoding="utf-8")
    r = RUNNER.read_text(encoding="utf-8")
    p = PACKAGER.read_text(encoding="utf-8")
    a = ADR.read_text(encoding="utf-8")

    need(
        b,
        'CANDIDATE = "v52_b4_or_b3_trend_bos"',
        'V53_BUILDER',
        'InpV54Magic = 540054',
        'InpV54MaxRiskPct = 0.50',
        'InpV54DailyLossPct = 2.00',
        'InpV54MaxDrawdownPct = 6.00',
        'InpV54MaxSpreadPoints = 150',
        'InpV54MaxTickAgeSeconds = 15',
        'InpV54MaxStrategyStateAgeSeconds = 30',
        'InpV54MaxConsecutiveRejects = 3',
        'V54RiskBoundVolume',
        'OrderCalcProfit',
        'TERMINAL_CONNECTED',
        'stale_strategy_state',
        'stale_tick',
        'spread_guard',
        'broker_reject_limit',
        'owned_position_missing_sltp',
        'duplicate_owned_positions',
        'V54ForeignSymbolPositions',
        'V54OwnedPositionCount',
        'V54SyncBrokerWithVirtual',
        'OnTradeTransaction',
        'SendNotification',
        'ACCOUNT_TRADE_MODE_DEMO',
        'production_activation=DISABLED_DEMO_SAFE',
        'real_money_authorized=0',
    )
    need(
        r,
        'EXPECTED_BRANCH = "agent/v54-production-readiness-hardening"',
        'working tree must be clean',
        'MetaEditor 0/0 + EX5',
        'V54_PRODUCTION_READINESS_STATUS.txt',
        'production_activation") == "DISABLED_DEMO_SAFE"',
        'MAX_OWNED_STRATEGY_POSITIONS=1',
        'REAL_MONEY_AUTHORIZED=0',
        'V53_NATURAL_MAPPING=NOT_OBSERVED',
    )
    need(
        p,
        'schema": "v54_immutable_evidence_v1"',
        'Snapshot is now immutable input',
        'ZIP CRC failure',
        'manifest mismatch',
        'V52R_ACCEPTED_ZIP_SHA256',
        'V53_ACCEPTED_ZIP_SHA256',
    )
    need(
        a,
        'RESEARCH_CANDIDATE=v52_b4_or_b3_trend_bos',
        'V53_NATURAL_MAPPING=NOT_OBSERVED',
        'PRODUCTION_ACTIVATION=DISABLED_DEMO_SAFE',
        'no Martingale',
        'no grid',
        'no doubling after loss',
    )

    # The builder intentionally names forbidden generated-output tokens in its guard.
    # The operator runner itself must not contain any real-account enable switch or credential path.
    for forbidden in (
        "ACCOUNT_TRADE_MODE_REAL",
        "real_money_authorized=1",
        "PRODUCTION_ACTIVATION=ENABLED",
        "password=",
        "login=",
    ):
        assert forbidden not in r, forbidden
    need(b, 'forbidden = (', '"ACCOUNT_TRADE_MODE_REAL"', '"real_money_authorized=1"')

    print("PASS candidate_frozen_v52r")
    print("PASS risk_cap_and_loss_guards")
    print("PASS disconnect_spread_stale_state_guards")
    print("PASS ownership_reconciliation_sltp_contract")
    print("PASS immutable_snapshot_evidence")
    print("PASS demo_safe_activation_boundary")
    print("V54 production-readiness static tests PASS count=6")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
