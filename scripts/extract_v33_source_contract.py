#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, pathlib, re

EXPECTED='4222120de5ded19ab7da172ad4c1e65d2a54b8bac7491fcd7927685b17b09a05'
PATTERNS=[
    r'\bBookRisk', r'\bOpenBook\b', r'\bCloseBook\b', r'\bUpdate.*Book', r'\bManage.*Book',
    r'\bProcess.*Book', r'\bpeak_r\b', r'\bmfe_r\b', r'\bmae_r\b', r'\bgiveback_r\b',
    r'\binitial_stop\b', r'\bfinal_stop\b', r'\brisk_cash\b', r'\bBookInitial\b'
]

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--terminal-root',required=True)
    ap.add_argument('--output',required=True)
    a=ap.parse_args()
    root=pathlib.Path(a.terminal_root)
    matches=[]
    for p in root.glob('*/MQL5/Experts/mt5_quant/MlDlFeatureLakeV1.mq5'):
        if p.is_file() and sha(p)==EXPECTED: matches.append(p)
    if len(matches)!=1: raise RuntimeError(f'exact accepted V30 source matches={len(matches)}')
    p=matches[0]; lines=p.read_text(encoding='utf-8-sig').splitlines()
    hit=set()
    for i,line in enumerate(lines):
        if any(re.search(x,line,re.I) for x in PATTERNS):
            for j in range(max(0,i-12),min(len(lines),i+28)): hit.add(j)
    ordered=sorted(hit)
    if len(ordered)>900: raise RuntimeError(f'source contract extraction unexpectedly large lines={len(ordered)}')
    out=pathlib.Path(a.output); out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('w',encoding='utf-8',newline='\n') as f:
        f.write(f'source={p}\nsha256={EXPECTED}\nmatched_lines={len(ordered)}\n\n')
        prev=None
        for j in ordered:
            if prev is None or j>prev+1: f.write(f'\n--- lines {j+1} ---\n')
            f.write(f'{j+1:05d}: {lines[j]}\n'); prev=j
    print(f'V33 source-contract extraction PASS lines={len(ordered)} -> {out}')

if __name__=='__main__': main()
