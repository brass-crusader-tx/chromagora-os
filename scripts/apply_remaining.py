#!/usr/bin/env python3
"""Apply remaining Supabase migrations (8+) with rate-limit handling."""

import httpx
import os
import re
import time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv('apps/api/.env')

supabase_url = os.environ.get('SUPABASE_URL', '')
project_ref = supabase_url.split('//')[1].split('.')[0] if '//' in supabase_url else ''
access_token = os.environ.get('SUPABASE_ACCESS_TOKEN', '')

if not access_token or not project_ref:
    print("ERROR: SUPABASE_ACCESS_TOKEN or SUPABASE_URL not set")
    exit(1)

api_base = f'https://api.supabase.com/v1/projects/{project_ref}/database/query'
headers = {
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json',
}

client = httpx.Client(timeout=30)
migrations_dir = Path('migrations')

total_ok = 0
total_skip = 0
total_fail = 0

for i in range(8, 23):
    pattern = f'{i:06d}_*.sql'
    files = list(migrations_dir.glob(pattern))
    if not files:
        continue
    
    fp = files[0]
    print(f'\n=== {fp.name} ===')
    sql = fp.read_text()
    
    # Split on semicolons not inside dollar quotes
    stmts = []
    current = []
    in_dollar = False
    for line in sql.split('\n'):
        stripped = line.strip()
        if not current and (stripped.startswith('--') or not stripped):
            continue
        
        if not in_dollar:
            if '$$' in line:
                in_dollar = True
            current.append(line)
            if stripped.endswith(';'):
                stmts.append('\n'.join(current).strip())
                current = []
        else:
            current.append(line)
            if '$$' in line:
                in_dollar = False
                stmts.append('\n'.join(current).strip())
                current = []
    
    for stmt in stmts:
        if not stmt or stmt.startswith('--'):
            continue
        
        success = False
        for attempt in range(3):
            try:
                r = client.post(api_base, headers=headers, json={'query': stmt})
                if r.status_code in (200, 201):
                    print(f'  OK: {stmt[:60]}')
                    total_ok += 1
                    success = True
                    break
                elif r.status_code == 429:
                    wait = 5 * (attempt + 1)
                    print(f'  Rate limited, waiting {wait}s...')
                    time.sleep(wait)
                    continue
                elif 'already exists' in r.text or '42710' in r.text:
                    print(f'  SKIP (exists): {stmt[:60]}')
                    total_skip += 1
                    success = True
                    break
                else:
                    print(f'  FAIL ({r.status_code}): {stmt[:60]}')
                    print(f'    {r.text[:100]}')
                    total_fail += 1
                    success = True
                    break
            except Exception as e:
                print(f'  ERROR: {e}')
                total_fail += 1
                success = True
                break
        
        if not success:
            print(f'  FAIL (rate limit exhausted): {stmt[:60]}')
            total_fail += 1
        
        time.sleep(0.3)

print(f'\n{"="*50}')
print(f'Migration complete:')
print(f'  Executed: {total_ok}')
print(f'  Skipped:  {total_skip}')
print(f'  Failures: {total_fail}')
