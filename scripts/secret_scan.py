#!/usr/bin/env python3
from __future__ import annotations
import re, sys
from pathlib import Path

SUFFIXES={'.py','.ps1','.cmd','.bat','.ini','.mq5','.mqh','.json','.yaml','.yml','.toml','.cfg','.conf'}
SKIP={'secret_scan.py'}
PATTERNS={
 'tracked_login_ini':re.compile(r'(?im)^\s*Login\s*=\s*\d{5,}\s*$'),
 'tracked_login_ps':re.compile(r'''(?im)\$Login\s*=\s*["']?\d{5,}["']?'''),
 'tracked_login_arg':re.compile(r'(?i)(?:^|\s)-Login\s+\d{5,}(?:\s|$)'),
 'password_assignment':re.compile(r'''(?im)^\s*(?:password|passwd)\s*[:=]\s*["']?[^"'\s#;]{6,}'''),
 'token_assignment':re.compile(r'''(?im)^\s*(?:api[_-]?key|access[_-]?token|refresh[_-]?token|secret)\s*[:=]\s*["']?[^"'\s#;]{8,}'''),
}
def main():
 root=Path(sys.argv[1] if len(sys.argv)>1 else '.').resolve()
 findings=[]
 for p in root.rglob('*'):
  if not p.is_file() or p.name in SKIP or p.suffix.lower() not in SUFFIXES: continue
  if any(x in {'.git','__pycache__','.pytest_cache'} for x in p.parts): continue
  try: text=p.read_text(encoding='utf-8-sig')
  except UnicodeDecodeError: continue
  for name,pat in PATTERNS.items():
   for m in pat.finditer(text):
    findings.append((p,text.count('\n',0,m.start())+1,name))
 for p,line,name in findings:
  print(f'SECRET_SCAN_FAIL {name} {p}:{line}',file=sys.stderr)
 if findings: return 2
 print('SECRET_SCAN_PASS'); return 0
if __name__=='__main__': raise SystemExit(main())
