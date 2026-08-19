#!/usr/bin/env python3
'''Verify frozen V29.2 payload and build hardened V29.3 distribution. Offline only.'''
from __future__ import annotations
import argparse, base64, csv, hashlib, io, re, tempfile, zipfile
from pathlib import Path

DISTRIBUTION_RELEASE = "v29_3_distribution_hardening"
EXPECTED_PAYLOAD_ZIP_SHA256 = "d469f527cb96197ed265c1e1a62c4d3f3f2d220efca0f44fb4478e928f68f334"
FIXED_ZIP_TIME = (2026, 8, 19, 0, 0, 0)

CONTRACTS = {
    "MqlDateTime": {"year","mon","day","hour","min","sec","day_of_week","day_of_year"},
    "MqlRates": {"time","open","high","low","close","tick_volume","spread","real_volume"},
    "MqlTick": {"time","bid","ask","last","volume","time_msc","flags","volume_real"},
}
HELPERS = ("MonthKey","MonthTagFromKey","NewBar","ReadOne","SecondsOfDay")
FORBIDDEN = (
    r"\bOrderSend(?:Async)?\s*\(",
    r"\bCTrade\b",
    r"\bMqlTradeRequest\b",
    r"\bTRADE_ACTION_[A-Z_]+\b",
)

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def decode_archive(path: Path) -> bytes:
    return base64.b64decode(path.read_bytes(), validate=False)

def single_member(names, suffix):
    hits=[n for n in names if n.replace("\\","/").endswith(suffix)]
    if len(hits)!=1:
        raise RuntimeError(f"expected one member ending {suffix!r}, found {hits}")
    return hits[0]

def validate_struct_members(text: str):
    errors=[]
    for typ, allowed in CONTRACTS.items():
        vars=set(re.findall(rf"\b{typ}\s+(?:&\s*)?([A-Za-z_]\w*)\s*(?:\[\s*\])?", text))
        for var in vars:
            pat=rf"\b{re.escape(var)}(?:\s*\[[^\]\r\n]+\])?\s*\.\s*([A-Za-z_]\w*)"
            for m in re.finditer(pat,text):
                if m.group(1) not in allowed:
                    errors.append(f"{typ}.{m.group(1)} via {var}")
    return errors

def validate_payload(raw_zip: bytes):
    actual=sha(raw_zip)
    if actual != EXPECTED_PAYLOAD_ZIP_SHA256:
        raise RuntimeError(f"payload ZIP SHA mismatch expected={EXPECTED_PAYLOAD_ZIP_SHA256} actual={actual}")

    z=zipfile.ZipFile(io.BytesIO(raw_zip))
    names=z.namelist()
    source_name=single_member(names,"/mql5/Experts/AdaptiveExpertLabV1.mq5")
    runner_name=single_member(names,"/scripts/run_adaptive_expert_lab_v1.ps1")
    analyzer_name=single_member(names,"/scripts/analyze_adaptive_expert_bundle.py")
    template_name=single_member(names,"/experiments/adaptive_expert_lab_v1/template.ini")
    chunks_name=single_member(names,"/experiments/adaptive_expert_lab_v1/chunks.csv")
    launcher_name=single_member(names,"/RUN_ADAPTIVE_EXPERT_LAB_V1.cmd")

    source=z.read(source_name).decode("utf-8-sig")
    runner=z.read(runner_name).decode("utf-8-sig")
    analyzer=z.read(analyzer_name).decode("utf-8-sig")
    template=z.read(template_name).decode("utf-8-sig")
    chunks=z.read(chunks_name).decode("utf-8-sig")

    if re.search(r"\.minute\b",source):
        raise RuntimeError("stale V29.1 source detected: .minute")
    if "dt.min!=0" not in source:
        raise RuntimeError("V29.2 dt.min correction marker missing")
    if "#define CANDIDATE_COUNT 12" not in source or "#define BOOK_COUNT 4" not in source:
        raise RuntimeError("candidate/book catalog mismatch")
    for helper in HELPERS:
        if len(re.findall(rf"\b(?:int|string|bool|double|long|void|datetime)\s+{helper}\s*\(",source)) != 1:
            raise RuntimeError(f"helper definition contract failed: {helper}")
    bad=validate_struct_members(source)
    if bad:
        raise RuntimeError("predefined structure member contract failed: " + ", ".join(bad))
    for pat in FORBIDDEN:
        if re.search(pat,source,re.I):
            raise RuntimeError(f"forbidden native execution path: {pat}")
    lower=source.lower()
    for token in ("mqlinfointeger(mql_tester)","tester_only=1","native_broker_orders=0","external_broker_orders=0"):
        if token not in lower:
            raise RuntimeError(f"source safety marker missing: {token}")

    if "SOURCE PREFLIGHT" not in runner or ".minute" not in runner:
        raise RuntimeError("V29.2 runner source-preflight markers missing")
    if "$PSScriptRoot" not in runner:
        raise RuntimeError("runner stable script-root fix missing")

    for token in ("AllowLiveTrading=0","AllowDllImport=0","Symbol=XAUUSDm","Period=M15"):
        if token not in template:
            raise RuntimeError(f"template token missing: {token}")
    if re.search(r"(?m)^\s*Login\s*=\s*\d+",template):
        raise RuntimeError("tracked login found in template")

    rows=list(csv.DictReader(io.StringIO(chunks)))
    if len(rows)!=3 or sum(int(r["months"]) for r in rows)!=18:
        raise RuntimeError("chunk schedule must be 3 chunks / 18 months")
    compile(analyzer,analyzer_name,"exec")
    return z

VERIFY_PS1 = r'''param()
$ErrorActionPreference='Stop'
$root=$PSScriptRoot
$release=Join-Path $root 'ACTIVE_RESEARCH_RELEASE.txt'
$manifest=Join-Path $root 'PAYLOAD_MANIFEST_SHA256.txt'
$payload=Join-Path $root 'payload'

function Write-DistributionDiagnostic {
  param([string]$Reason,[string]$InnerDiagnostic='')
  try {
    $out=Join-Path $root 'OUTPUT'
    New-Item -ItemType Directory -Force -Path $out | Out-Null
    $tmp=Join-Path ([IO.Path]::GetTempPath()) ('v29_3_diag_'+(Get-Date -Format 'yyyyMMdd_HHmmss'))
    New-Item -ItemType Directory -Force -Path $tmp | Out-Null
    if(Test-Path -LiteralPath $release){Copy-Item -LiteralPath $release -Destination (Join-Path $tmp 'ACTIVE_RESEARCH_RELEASE.txt')}
    Set-Content -LiteralPath (Join-Path $tmp 'distribution_error.txt') -Value $Reason -Encoding UTF8
    if($InnerDiagnostic -and (Test-Path -LiteralPath $InnerDiagnostic)){
      Copy-Item -LiteralPath $InnerDiagnostic -Destination (Join-Path $tmp 'inner_diagnostic.zip')
    }
    $zip=Join-Path $out ('mt5_quant_v29_3_distribution_DIAGNOSTIC_'+(Get-Date -Format 'yyyyMMdd_HHmmss')+'.zip')
    Compress-Archive -Path (Join-Path $tmp '*') -DestinationPath $zip -Force
    Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host ('UPLOAD THIS DIAGNOSTIC ZIP: '+$zip)
  } catch {
    Write-Host ('DIAGNOSTIC PACKAGING ALSO FAILED: '+$_.Exception.Message)
  }
}

try {
  if(-not(Test-Path -LiteralPath $release)){throw 'ACTIVE_RESEARCH_RELEASE.txt missing'}
  if(-not(Test-Path -LiteralPath $manifest)){throw 'PAYLOAD_MANIFEST_SHA256.txt missing'}
  foreach($line in Get-Content -LiteralPath $manifest){
    if([string]::IsNullOrWhiteSpace($line)){continue}
    $parts=$line -split '  ',2
    if($parts.Count -ne 2){throw 'Invalid payload manifest line'}
    $p=Join-Path $payload $parts[1]
    if(-not(Test-Path -LiteralPath $p)){throw ('Payload file missing: '+$parts[1])}
    $actual=(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLower()
    if($actual -ne $parts[0]){throw ('Payload hash mismatch: '+$parts[1])}
  }
  $src=Join-Path $payload 'mql5\Experts\AdaptiveExpertLabV1.mq5'
  $raw=Get-Content -LiteralPath $src -Raw
  if($raw -match '\.minute\b'){throw 'STALE SOURCE BLOCKED: .minute found'}
  if($raw -notmatch 'dt\.min\s*!=\s*0'){throw 'Expected V29.2 dt.min correction missing'}
  Write-Host 'V29.3 DISTRIBUTION PREFLIGHT PASS'
  $launcher=Join-Path $payload 'RUN_ADAPTIVE_EXPERT_LAB_V1.cmd'
  & $launcher
  $rc=$LASTEXITCODE
  if($rc -ne 0){
    $inner=Get-ChildItem -LiteralPath (Join-Path $payload 'OUTPUT') -Filter '*DIAGNOSTIC*.zip' -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    $innerPath=if($inner){$inner.FullName}else{''}
    Write-DistributionDiagnostic -Reason ('Inner V29.2 runner failed exit='+$rc) -InnerDiagnostic $innerPath
    exit $rc
  }
  exit 0
} catch {
  Write-DistributionDiagnostic -Reason $_.Exception.Message
  Write-Host ('V29.3 DISTRIBUTION PREFLIGHT FAILED: '+$_.Exception.Message)
  exit 91
}'''

RUN_CMD = r'''@echo off
setlocal
cd /d "%~dp0"
echo ============================================================
echo V29.3 DISTRIBUTION HARDENING
echo TESTER ONLY - REAL-MONEY LIVE TRADING FORBIDDEN
echo ============================================================
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0VERIFY_AND_RUN.ps1"
set RC=%ERRORLEVEL%
echo.
if not "%RC%"=="0" echo FAILED exit=%RC%
pause
exit /b %RC%
'''

def manifest_for_payload(root: Path):
    lines=[]
    for p in sorted(x for x in (root/"payload").rglob("*") if x.is_file()):
        lines.append(f"{sha(p.read_bytes())}  {p.relative_to(root/'payload').as_posix()}")
    return "\n".join(lines)+"\n"

def zip_deterministic(root: Path, out: Path):
    with zipfile.ZipFile(out,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in sorted(x for x in root.rglob("*") if x.is_file()):
            rel=(Path(root.name)/p.relative_to(root)).as_posix()
            info=zipfile.ZipInfo(rel,FIXED_ZIP_TIME)
            info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=0o100644<<16
            z.writestr(info,p.read_bytes())

def build(archive_b64: Path, output: Path):
    raw=decode_archive(archive_b64)
    z=validate_payload(raw)
    output.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="v29_3_dist_") as td:
        root=Path(td)/f"mt5_quant_{DISTRIBUTION_RELEASE}"
        payload=root/"payload"
        payload.mkdir(parents=True)
        names=[n for n in z.namelist() if not n.endswith("/")]
        prefixes={n.split("/",1)[0] for n in names if "/" in n}
        if len(prefixes)!=1:
            raise RuntimeError(f"unexpected payload roots: {prefixes}")
        prefix=next(iter(prefixes))+"/"
        for n in names:
            if not n.startswith(prefix):
                raise RuntimeError(f"payload member outside root: {n}")
            rel=n[len(prefix):]
            dst=payload/rel
            dst.parent.mkdir(parents=True,exist_ok=True)
            dst.write_bytes(z.read(n))

        (root/"ACTIVE_RESEARCH_RELEASE.txt").write_text(
            f"distribution_release={DISTRIBUTION_RELEASE}\n"
            "strategy_payload_release=v29_2_adaptive_expert\n"
            f"payload_zip_sha256={EXPECTED_PAYLOAD_ZIP_SHA256}\n"
            "stale_releases_forbidden=v29.0,v29.1\n"
            "real_money_live_trading=forbidden\n",encoding="utf-8")
        (root/"VERIFY_AND_RUN.ps1").write_text(VERIFY_PS1,encoding="utf-8")
        (root/"RUN_ADAPTIVE_EXPERT_LAB_V1.cmd").write_text(RUN_CMD,encoding="utf-8")
        (root/"PAYLOAD_MANIFEST_SHA256.txt").write_text(manifest_for_payload(root),encoding="ascii")
        out=output/f"mt5_quant_{DISTRIBUTION_RELEASE}_one_click.zip"
        zip_deterministic(root,out)
    out_sha=sha(out.read_bytes())
    (output/(out.stem+".sha256.txt")).write_text(out_sha+"  "+out.name+"\n",encoding="ascii")
    print(f"BUILD_PASS release={DISTRIBUTION_RELEASE} sha256={out_sha} zip={out}")
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--archive",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--verify-only",action="store_true")
    ns=ap.parse_args()
    raw=decode_archive(ns.archive)
    validate_payload(raw)
    print(f"VERIFY_PASS payload_sha256={sha(raw)}")
    if not ns.verify_only:
        build(ns.archive,ns.output)
    return 0

if __name__=="__main__":
    raise SystemExit(main())
