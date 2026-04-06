import codecs
with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_patch = [
    "# --- HOTFIX for streamlit-drawable-canvas + Streamlit 1.40+ ---\n",
    "import streamlit.elements.image as sei\n",
    "try:\n",
    "    from streamlit.elements.lib import image_utils\n",
    "    _real_image_to_url = image_utils.image_to_url\n",
    "    def wrapped_image_to_url(image_data, layout_config, *args, **kwargs):\n",
    "        if isinstance(layout_config, int):\n",
    "            from dataclasses import dataclass\n",
    "            @dataclass\n",
    "            class FakeConfig:\n",
    "                width: int\n",
    "                use_column_width: bool = False\n",
    "            return _real_image_to_url(image_data, FakeConfig(width=layout_config), *args, **kwargs)\n",
    "        return _real_image_to_url(image_data, layout_config, *args, **kwargs)\n",
    "    sei.image_to_url = wrapped_image_to_url\n",
    "except Exception:\n",
    "    pass\n",
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
    print("FINAL COMPATIBILITY PATCH APPLIED")
