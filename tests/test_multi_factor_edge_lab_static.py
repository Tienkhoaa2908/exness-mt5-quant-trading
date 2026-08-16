from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
MQL = (ROOT / 'mql5/Experts/MultiFactorEdgeLabV1.mq5').read_text(encoding='utf-8')
RUNNER = (ROOT / 'scripts/run_multi_factor_edge_lab_v1.ps1').read_text(encoding='utf-8')
TEMPLATE = (ROOT / 'experiments/multi_factor_edge_lab_v1/template.ini').read_text(encoding='utf-8')
CHUNKS = (ROOT / 'experiments/multi_factor_edge_lab_v1/chunks.csv').read_text(encoding='utf-8')


def test_live_and_native_order_paths_are_absent():
    lower = MQL.lower()
    assert 'ordersend(' not in lower
    assert 'ctrade' not in lower
    assert 'native_broker_orders=0' in lower
    assert 'external_broker_orders=0' in lower
    assert 'tester_only=1' in lower


def test_catalog_and_books_are_bounded():
    assert '#define CANDIDATE_COUNT 32' in MQL
    assert '#define BOOK_COUNT 4' in MQL
    for family in [
        'ema_h1', 'trend20_h1', 'rsi2_h1', 'macd_h1',
        'donchian55_h1', 'bb_rsi', 'liquidity_sweep_h1', 'bos_fvg_h1'
    ]:
        assert family in MQL
    for variant in ['base', 'quality', 'quality_streak', 'quality_streak_late20']:
        assert variant in MQL


def test_targeted_streak_guard_not_generic_risk_escalation():
    assert 'profit_streak_count>=2' in MQL
    assert 'barsSince<16' in MQL
    assert 'C[i].rearm_profit_atr=streak ? 0.50 : 0.0;' in MQL
    assert 'usd40_r1p0_cent' in MQL
    assert 'cent_std_equiv_min=0.0001' in MQL
    assert 'conservative_margin_leverage=200' in MQL


def test_quality_indicators_present():
    for token in ['iRSI(', 'iMACD(', 'iADX(', 'iBands(', 'hAtr50']:
        assert token in MQL


def test_template_safety_and_no_tracked_login():
    assert 'AllowLiveTrading=0' in TEMPLATE
    assert 'AllowDllImport=0' in TEMPLATE
    assert 'Symbol=XAUUSDm' in TEMPLATE
    assert 'Period=M15' in TEMPLATE
    assert 'Leverage=1:200' in TEMPLATE
    assert re.search(r'^Login=', TEMPLATE, flags=re.MULTILINE) is None


def test_runner_is_one_run_three_bounded_chunks_one_zip():
    assert '[int]$MaxChunkMinutes = 30' in RUNNER
    assert "'candidate_count=32'" in RUNNER
    assert "'book_count=4'" in RUNNER
    assert "'month_count=18'" in RUNNER
    assert "'chunk_count=3'" in RUNNER
    assert 'bundle_manifest_sha256.txt' in RUNNER
    assert 'Compress-Archive' in RUNNER
    assert 'Service is not available' in RUNNER
    assert 'not synchronized with trade server' in RUNNER
    assert re.search(r"\$Login\s*=\s*''", RUNNER)
    assert '414181578' not in RUNNER


def test_three_chunk_schedule_covers_18_full_months():
    lines = [x for x in CHUNKS.strip().splitlines() if x]
    assert len(lines) == 4
    assert lines[1].startswith('2025_h1,2025.02.01,2025.08.01')
    assert lines[2].startswith('2025h2_2026m1,2025.08.01,2026.02.01')
    assert lines[3].startswith('2026_feb_jul,2026.02.01,2026.08.01')
