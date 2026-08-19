from pathlib import Path
import base64, hashlib, importlib.util, io, zipfile

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/verify_and_build_v29_release.py"

def load():
    spec=importlib.util.spec_from_file_location("v29build",SCRIPT)
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m

def fixture_archive(tmp_path):
    src="""#property strict
#define CANDIDATE_COUNT 12
#define BOOK_COUNT 4
int MonthKey(){return 1;} string MonthTagFromKey(){return "x";}
bool NewBar(){return true;} bool ReadOne(){return true;} int SecondsOfDay(){return 0;}
void x(){MqlDateTime dt; if(dt.min!=0){} MqlRates r[]; double a=r[0].close; MqlTick t; double b=t.bid;}
void OnInit(){MQLInfoInteger(MQL_TESTER);}
string s="tester_only=1 native_broker_orders=0 external_broker_orders=0";
"""
    runner="$PSScriptRoot\nSOURCE PREFLIGHT\nif($raw -match '\\.minute\\b'){}\n"
    template="[Tester]\nSymbol=XAUUSDm\nPeriod=M15\nAllowLiveTrading=0\nAllowDllImport=0\n"
    chunks="tag,from,to,months\na,x,x,6\nb,x,x,6\nc,x,x,6\n"
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,"w",zipfile.ZIP_DEFLATED) as z:
        p="v29_release/"
        z.writestr(p+"mql5/Experts/AdaptiveExpertLabV1.mq5",src)
        z.writestr(p+"scripts/run_adaptive_expert_lab_v1.ps1",runner)
        z.writestr(p+"scripts/analyze_adaptive_expert_bundle.py","x=1\n")
        z.writestr(p+"experiments/adaptive_expert_lab_v1/template.ini",template)
        z.writestr(p+"experiments/adaptive_expert_lab_v1/chunks.csv",chunks)
        z.writestr(p+"RUN_ADAPTIVE_EXPERT_LAB_V1.cmd","@echo off\n")
    raw=buf.getvalue()
    path=tmp_path/"payload.b64"; path.write_bytes(base64.b64encode(raw))
    return path,raw

def test_validate_and_build_wrapper(tmp_path):
    m=load()
    path,raw=fixture_archive(tmp_path)
    m.EXPECTED_PAYLOAD_ZIP_SHA256=hashlib.sha256(raw).hexdigest()
    z=m.validate_payload(raw)
    assert z.namelist()
    out=m.build(path,tmp_path/"dist")
    assert out.is_file()
    with zipfile.ZipFile(out) as final:
        names=final.namelist()
        assert any(n.endswith("/ACTIVE_RESEARCH_RELEASE.txt") for n in names)
        assert any(n.endswith("/VERIFY_AND_RUN.ps1") for n in names)
        assert any(n.endswith("/PAYLOAD_MANIFEST_SHA256.txt") for n in names)

def test_rejects_stale_minute(tmp_path):
    m=load()
    path,raw=fixture_archive(tmp_path)
    src=io.BytesIO(raw)
    out=io.BytesIO()
    with zipfile.ZipFile(src) as zin, zipfile.ZipFile(out,"w",zipfile.ZIP_DEFLATED) as zout:
        for info in zin.infolist():
            body=zin.read(info.filename)
            if info.filename.endswith("/mql5/Experts/AdaptiveExpertLabV1.mq5"):
                body=body.replace(b"dt.min!=0",b"dt.minute!=0")
            zout.writestr(info.filename,body)
    bad=out.getvalue()
    m.EXPECTED_PAYLOAD_ZIP_SHA256=hashlib.sha256(bad).hexdigest()
    try:
        m.validate_payload(bad)
    except Exception:
        pass
    else:
        raise AssertionError("stale .minute payload was not rejected")

def test_build_is_deterministic(tmp_path):
    m=load()
    path,raw=fixture_archive(tmp_path)
    m.EXPECTED_PAYLOAD_ZIP_SHA256=hashlib.sha256(raw).hexdigest()
    a=m.build(path,tmp_path/'dist_a')
    b=m.build(path,tmp_path/'dist_b')
    assert hashlib.sha256(a.read_bytes()).digest() == hashlib.sha256(b.read_bytes()).digest()


def test_rejects_native_order_path(tmp_path):
    m=load()
    _,raw=fixture_archive(tmp_path)
    src=io.BytesIO(raw); out=io.BytesIO()
    with zipfile.ZipFile(src) as zin, zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as zout:
        for info in zin.infolist():
            body=zin.read(info.filename)
            if info.filename.endswith('/mql5/Experts/AdaptiveExpertLabV1.mq5'):
                body += b'\nvoid bad(){ MqlTradeRequest r; }\n'
            zout.writestr(info.filename,body)
    bad=out.getvalue(); m.EXPECTED_PAYLOAD_ZIP_SHA256=hashlib.sha256(bad).hexdigest()
    try:
        m.validate_payload(bad)
    except Exception:
        pass
    else:
        raise AssertionError('native order path was not rejected')
