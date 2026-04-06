import codecs
with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_patch = [
    "# --- HOTFIX for streamlit-drawable-canvas + Streamlit 1.40+ ---\n",
    "import streamlit.elements.image as sei\n",
    "if not hasattr(sei, 'image_to_url'):\n",
    "    try:\n",
    "        from streamlit.elements.lib import image_utils\n",
    "        sei.image_to_url = image_utils.image_to_url\n",
    "    except ImportError:\n",
    "        pass\n",
    "# --------------------------------------------------------------\n",
    "from streamlit_drawable_canvas import st_canvas\n"
]

start = -1
end = -1
for i, line in enumerate(lines):
    if '# --- HOTFIX for streamlit-drawable-canvas + Streamlit 1.40+' in line:
        start = i
    if '# --------------------------------------------------------------' in line:
        end = i
        break

if start != -1 and end != -1:
    lines[start:end+2] = new_patch

with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
    print("PATCH INDENTATION FIXED")
