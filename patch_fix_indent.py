import codecs
with open('app.py', 'r', encoding='utf-8') as f:
    code = f.readlines()

# Find the lines of the hotfix
hotfix_start = -1
hotfix_end = -1
for i, line in enumerate(code):
    if '# --- HOTFIX for streamlit-drawable-canvas + Streamlit 1.40+' in line:
        hotfix_start = i
    if '# --------------------------------------------------------------' in line:
        hotfix_end = i
        break

if hotfix_start != -1 and hotfix_end != -1:
    # Extract hotfix lines
    hotfix_lines = code[hotfix_start:hotfix_end+2] # Including the import line after
    
    # Remove hotfix from original position
    del code[hotfix_start:hotfix_end+2]
    
    # Insert at top (after imports)
    import_end = 0
    for i, line in enumerate(code):
        if line.startswith('import ') or line.startswith('from '):
            import_end = i + 1
    
    # Make sure hotfix has no extra indentation (it currently has none but let's be sure)
    hotfix_lines = [l.lstrip() for l in hotfix_lines]
    
    # Insert the hotfix lines at import_end
    code[import_end:import_end] = ['\n'] + hotfix_lines + ['\n']

with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(code)
    print("FIXED INDENTATION AND MOVED PATCH TO TOP")
