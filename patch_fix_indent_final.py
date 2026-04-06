import codecs

with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Fix the nesting issue: st_canvas should always be called, even if f_coords is None
# We need to find the block we added and fix the indentation of st_canvas and following lines

start_block = -1
end_block = -1
for i, line in enumerate(lines):
    if "# --- FOOTPRINT PREVIEW (La Huella) ---" in line:
        start_block = i
    if "key=\"canvas_main\"," in line:
        end_block = i
        # We find the end of the st_canvas call
        while j < len(lines) and not lines[j].strip().startswith(")"):
            j += 1
        end_block = j
        break

# Actually, I'll just rewrite the whole preview block for safety
# First, let's find the start of the cp1/cp2/cp3 part again to be sure
start_preview = -1
for i, line in enumerate(lines):
    if "with col_preview:" in line:
        start_preview = i
        break

if start_preview != -1:
    # Let's find the end of the footer or something to replace the whole middle section correctly
    end_preview = -1
    for i in range(start_preview, len(lines)):
        if "# --- BOTÓN DE GENERACIÓN ---" in line:
            end_preview = i
            break
    
    # It's safer to just patch specifically the indentation of the st_canvas block
    # Locate the "if f_coords:" line
    for i in range(start_preview, len(lines)):
        if "if f_coords:" in lines[i]:
            # The next few lines are indented
            # We want to un-indent the st_canvas call (which starts around line 478 in viewed snippet)
            pass

# Optimized Patching Script
patch_script = """
import codecs
with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Correcting the indentation of st_canvas (it was nested in if f_coords:)
old_text = '''        if f_coords:
            fx, fy = f_coords[0] * zoom_level, f_coords[1] * zoom_level
            fw, fh = f_size[0] * zoom_level, f_size[1] * zoom_level
            draw_preview.rectangle([fx, fy, fx + fw, fy + fh], fill=f_color, outline=f_color[:3] + (200,), width=2)
            st.caption(f"📏 Huella del Sello: {int(f_size[0])}x{int(f_size[1])} px (aprox. {int(f_size[0]*25.4/72)}x{int(f_size[1]*25.4/72)} mm)")

            canvas_result = st_canvas('''

new_text = '''        if f_coords:
            fx, fy = f_coords[0] * zoom_level, f_coords[1] * zoom_level
            fw, fh = f_size[0] * zoom_level, f_size[1] * zoom_level
            draw_preview.rectangle([fx, fy, fx + fw, fy + fh], fill=f_color, outline=f_color[:3] + (200,), width=2)
            st.caption(f"📏 Huella del Sello: {int(f_size[0])}x{int(f_size[1])} px (aprox. {int(f_size[0]*25.4/72)}x{int(f_size[1]*25.4/72)} mm)")

        canvas_result = st_canvas('''

# Also need to fix the rest of the canvas_result block indentation
content = content.replace(old_text, new_text)

# Fixing the end of the canvas block which was also indented
content = content.replace('                key="canvas_main",\\n            )', '            key="canvas_main",\\n        )')

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
"""

with open('fix_indent.py', 'w', encoding='utf-8') as f:
    f.write(patch_script)

import subprocess
subprocess.run(['python', 'fix_indent.py'])
