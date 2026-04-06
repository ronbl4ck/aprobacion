import codecs
import io
from PIL import Image, ImageDraw

with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 1. Add session state for ready PDF data
state_init = [
    "if 'pdf_ready_data' not in st.session_state:\n",
    "    st.session_state.pdf_ready_data = None\n",
    "if 'pdf_ready_name' not in st.session_state:\n",
    "    st.session_state.pdf_ready_name = ''\n"
]

# Insert after config_mgr init
for i, line in enumerate(lines):
    if "cfg = st.session_state.config_mgr" in line:
        lines[i+1:i+1] = state_init
        break

# 2. Footprint Preview Logic
footprint_logic = """
        # --- FOOTPRINT PREVIEW (La Huella) ---
        from PIL import ImageDraw
        draw_preview = ImageDraw.Draw(page_img)
        BASE_FACTOR = 0.35
        
        # Determinar coordenadas y tamaño según modo
        f_coords = None
        f_size = (0, 0)
        f_color = (88, 166, 255, 60) # Azul para Sello 1
        
        if "1" in modo_sello:
            f_coords = cfg.get('cover_coords')
            f_size = (624 * BASE_FACTOR * (cfg.get('cover_scale', 100)/100.0), 400 * BASE_FACTOR * (cfg.get('cover_scale', 100)/100.0))
        else:
            f_coords = cfg.get('body_coords')
            f_color = (247, 120, 186, 60) # Rosa para Sello 2
            # Sello 2 dimensions from engine
            if 'signature_bytes' in st.session_state or cfg.get('sello2_mode') == 'custom':
                tmp_sig_p = None
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as ts:
                    ts.write(st.session_state.get('signature_bytes', b''))
                    tmp_sig_p = ts.name
                
                try:
                    sw, sh = st.session_state.stamp_engine.get_body_stamp_size(
                        tmp_sig_p, cfg.get('engineer_name'), cfg.get('cip_number'), cfg.get('engineer_type')
                    )
                    f_size = (sw * BASE_FACTOR * (cfg.get('body_scale', 100)/100.0), sh * BASE_FACTOR * (cfg.get('body_scale', 100)/100.0))
                finally:
                    import os
                    if tmp_sig_p and os.path.exists(tmp_sig_p): os.remove(tmp_sig_p)

        if f_coords:
            fx, fy = f_coords[0] * zoom_level, f_coords[1] * zoom_level
            fw, fh = f_size[0] * zoom_level, f_size[1] * zoom_level
            draw_preview.rectangle([fx, fy, fx + fw, fy + fh], fill=f_color, outline=f_color[:3] + (200,), width=2)
            st.caption(f"📏 Huella del Sello: {int(f_size[0])}x{int(f_size[1])} px (aprox. {int(f_size[0]*25.4/72)}x{int(f_size[1]*25.4/72)} mm)")
"""

# Insert before st_canvas call
for i, line in enumerate(lines):
    if "canvas_result = st_canvas(" in line:
        lines[i:i] = [footprint_logic + "\n"]
        break

# 3. Download persistence logic
# Update generating logic to save to session state
for i, line in enumerate(lines):
    if "if success:" in line:
        # Looking for the success block to add session state saving
        j = i + 1
        while j < len(lines) and not lines[j].strip().startswith("st.download_button"):
            j += 1
        if j < len(lines):
            # Replace download button with session state save
            lines[j:j+7] = [
                "                            st.session_state.pdf_ready_data = out_buffer.getvalue()\n",
                "                            st.session_state.pdf_ready_name = out_name\n",
                "                            st.rerun()\n"
            ]
        break

# 4. Render persistent download button
persistent_download = """
        # --- BOTÓN DE DESCARGA PERSISTENTE ---
        if st.session_state.pdf_ready_data:
            st.divider()
            st.success(f"✅ Documento listo: {st.session_state.pdf_ready_name}")
            st.download_button(
                label="⬇️ Descargar PDF Firmado",
                data=st.session_state.pdf_ready_data,
                file_name=st.session_state.pdf_ready_name,
                mime="application/pdf",
                key="persistent_download_btn",
                use_container_width=True
            )
            if st.button("🗑️ Limpiar Generación", key="btn_clear_pdf"):
                st.session_state.pdf_ready_data = None
                st.rerun()
"""

# Insert before Footer
for i, line in enumerate(lines):
    if "# --- FOOTER ---" in line:
        lines[i:i] = [persistent_download + "\n"]
        break

with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
    print("UX IMPROVEMENTS APPLIED")
