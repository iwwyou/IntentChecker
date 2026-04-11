import json, sys
sys.stdout.reconfigure(encoding='utf-8')

with open('evaluation/RQ3/outputs/numscout/run1/summary.json', encoding='utf-8') as f:
    results = json.load(f)

print(f'{"case_id":<40} {"status":<15} {"time":>18} {"det":<6} {"patterns"}')
print('-' * 110)
for r in sorted(results, key=lambda x: x.get('time', 0), reverse=True):
    cid = r.get('case_id', '?')
    if r.get('result') == 'flatten_failed':
        print(f'{cid:<40} {"FLATTEN_FAIL":<15} {"n/a":>18} {"n/a":<6}')
        continue
    status = r.get('status', '?')
    t = r.get('time', 0)
    det = 'Y' if r.get('detected', False) else 'N'
    pats = r.get('detected_patterns', [])
    if t > 60:
        t_str = f'{t:.0f}s ({t/60:.1f}m)'
    else:
        t_str = f'{t:.1f}s'
    print(f'{cid:<40} {status:<15} {t_str:>18} {det:<6} {pats}')

# Summary
ok = [r for r in results if r.get('status') == 'ok']
timeout = [r for r in results if r.get('status') == 'timeout']
flatten = [r for r in results if r.get('result') == 'flatten_failed']
detected = [r for r in results if r.get('detected')]
print(f'\nTotal: {len(results)}, OK: {len(ok)}, Timeout: {len(timeout)}, Flatten fail: {len(flatten)}, Detected: {len(detected)}')
