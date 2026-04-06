import codecs
with open('app.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Add the monkey patch before from streamlit_drawable_canvas import st_canvas
patch = '''
# --- HOTFIX for streamlit-drawable-canvas + Streamlit 1.40+ ---
import streamlit.elements.image as sei
if not hasattr(sei, 'image_to_url'):
    try:
        from streamlit.elements.lib import image_utils
        sei.image_to_url = image_utils.image_to_url
    except ImportError:
        pass
# --------------------------------------------------------------
'''

if 'import streamlit.elements.image as sei' not in code:
    code = code.replace('from streamlit_drawable_canvas import st_canvas', patch + 'from streamlit_drawable_canvas import st_canvas')

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(code)
    print("COMPATIBILITY PATCH APPLIED")
