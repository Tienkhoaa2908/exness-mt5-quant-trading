from pathlib import Path
import base64,hashlib,io,re,tarfile

ROOT=Path(__file__).resolve().parents[1]
MODEL=ROOT/'models'/'v31_ai_router'
REL=MODEL/'release'/'v31_model_release.tar.gz.b64'
ARCHIVE_SHA='fbcf83f04d2e8661bc36ebba2bea66c172cbc4c08d4b13e74df45a8b9174b9e7'
raw=base64.b64decode(REL.read_text(encoding='ascii'))
assert hashlib.sha256(raw).hexdigest()==ARCHIVE_SHA
with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as tf:
    def read(name):
        f=tf.extractfile('./'+name) or tf.extractfile(name)
        assert f is not None,name
        return f.read().decode('utf-8')
    SRC=read('V31AiRouterLabV1.mq5')
    DATA=read('V31AiModelData.mqh')
    SVM=read('V31AiSvmWeights.mqh')
    NN=read('V31AiNnWeights.mqh')
    RFF=read('V31AiRffWeights.mqh')

def vals(text,name):
    m=re.search(rf'const\s+(?:double|float)\s+{name}\s*\[[^\]]+\]\s*=\s*\{{(.*?)\}};',text,re.S)
    assert m,name
    return [v for v in m.group(1).replace('\n',' ').split(',') if v.strip()]

def test_v31_safety_and_catalog():
    assert '#define MT5Q_RELEASE_ID "v31_ai_router_lab_v1"' in SRC
    assert '#define BASE_CANDIDATE_COUNT 12' in SRC
    assert '#define AI_NN_CI 12' in SRC and '#define AI_SVM_CI 13' in SRC and '#define AI_RFF_CI 14' in SRC
    assert '#define CANDIDATE_COUNT 15' in SRC
    assert 'MQLInfoInteger(MQL_TESTER)' in SRC
    for t in ['OrderSend(','OrderSendAsync(','CTrade','trade.Buy(','trade.Sell(','PositionOpen(']: assert t not in SRC
    assert 'research_stop_risk_ceiling_pct=1.0' in SRC
    assert 'research_target_start_capital_usd=40' in SRC
    assert 'research_target_monthly_return_pct=15' in SRC

def test_model_shapes_and_thresholds():
    assert '#define V31_AI_NUMERIC_DIM 61' in DATA and '#define V31_AI_CANDIDATE_DIM 12' in DATA and '#define V31_AI_INPUT_DIM 73' in DATA
    for n in ['V31_MED','V31_LO','V31_HI','V31_MEAN','V31_STD']: assert len(vals(DATA,n))==61
    assert len(vals(NN,'V31_NN_W1'))==96*73 and len(vals(NN,'V31_NN_B1'))==96
    assert len(vals(NN,'V31_NN_W2'))==48*96 and len(vals(NN,'V31_NN_B2'))==48
    assert len(vals(NN,'V31_NN_W3'))==24*48 and len(vals(NN,'V31_NN_B3'))==24 and len(vals(NN,'V31_NN_WO'))==24
    assert len(vals(SVM,'V31_SVM_W'))==73
    assert '#define V31_RFF_COMPONENTS 384' in RFF and len(vals(RFF,'V31_RFF_W'))==73*384 and len(vals(RFF,'V31_RFF_OFFSET'))==384 and len(vals(RFF,'V31_RFF_COEF'))==384
    assert 'const double V31_NN_THRESHOLD=0.15744125843048096;' in DATA
    assert 'const double V31_SVM_THRESHOLD=-0.10337714735872365;' in DATA
    assert 'const double V31_RFF_THRESHOLD=' in RFF

def test_candidate_mapping_and_router_controls():
    body=re.search(r'int V31CandidateOneHotIndex\(const int ci\)\s*\{(.*?)\n\}',SRC,re.S).group(1)
    found={int(a):int(b) for a,b in re.findall(r'if\(ci==(\d+)\) return (\d+);',body)}
    assert found=={11:0,9:1,10:2,7:3,8:4,2:5,0:6,1:7,4:8,6:9,5:10,3:11}
    assert 'ci!=6' in SRC
    assert 'V31NnScore(xi)' in SRC and 'V31SvmScore(xi)' in SRC and 'V31RffScore(xi)' in SRC

def test_manifest_contract():
    assert 'format=mt5_quant_v31_ai_router_lab_v1' in SRC
    assert 'candidate_count="+IntegerToString(CANDIDATE_COUNT)' in SRC
    assert 'base_candidate_count="+IntegerToString(BASE_CANDIDATE_COUNT)' in SRC
    assert 'ai_models=distilled_relu_nn,linear_svr,rff_rbf_kernel_ridge' in SRC
    assert 'ai_train_labels_before=2025-07-01' in SRC and 'ai_threshold_calibration_month=2025_07_scores_only' in SRC
    assert 'ai_holdout_start=2025-08-01' in SRC and 'ai_holdout_end=2026-08-01' in SRC

def test_source_strings_are_line_closed():
    for no,line in enumerate(SRC.splitlines(),1):
        q=0; esc=False
        for ch in line:
            if esc: esc=False; continue
            if ch=='\\': esc=True; continue
            if ch=='"': q^=1
        assert q==0, f'unclosed string on physical line {no}'

def test_deployment_hashes():
    assert hashlib.sha256(SRC.encode()).hexdigest()=='cef304997fc342740c15101d64a610d6265a4835a4cb601a741113868a078f0f'
    assert hashlib.sha256(DATA.encode()).hexdigest()=='44c8edd55fc5a1b18fe5ec5d0a3454d95600f23d8c3f06ae6048e1c4d16211f3'
    assert hashlib.sha256(SVM.encode()).hexdigest()=='8b94f800959b32465302a8eb50c58fff82071368cf3310788c4c3fdb9cebf650'
    assert hashlib.sha256(NN.encode()).hexdigest()=='6e977ff55b9ae7ddf5ffa8103642fa882a6a47cdc2ef0f9fe6f16582e242c8f3'
    assert hashlib.sha256(RFF.encode()).hexdigest()=='36905a57761ec216e2ca92ac87a2a9a23bd241bace4a86a87124ccb6f2ffe710'
