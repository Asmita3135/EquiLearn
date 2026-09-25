import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

content = open('member3_full_test.py', encoding='utf-8').read()

# T1-E: missing 'actual' arg
old_e = (
    'record("T1-E", "Complex vocab: difficult words flagged",\n'
    '       ">=5 technical words", f"found {len(found)}: {found}",\n'
    '       PASS if len(found) >= 5 else FAIL)'
)
new_e = (
    'record("T1-E", "Complex vocab: difficult words flagged",\n'
    '       ">=5 technical words",\n'
    '       "difficult_words check",\n'
    '       f"found {len(found)}: {found}",\n'
    '       PASS if len(found) >= 5 else FAIL)'
)
print("T1-E found:", old_e in content)
content = content.replace(old_e, new_e)
open('member3_full_test.py', 'w', encoding='utf-8').write(content)
print("done")
