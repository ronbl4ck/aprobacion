import codecs
import io
with open('app.py.bak', 'r', encoding='utf-8') as f:
    code = f.read()

insert_code = '''
def process_transparency(img_bytes, threshold=240, clean=False):
    if not clean: return img_bytes
    from PIL import Image
    import io
    img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
    data = img.getdata()
    new_data = []
    for item in data:
        if item[0] >= threshold and item[1] >= threshold and item[2] >= threshold:
            new_data.append((255, 255, 255, 0))
        else:
            avg = (item[0] + item[1] + item[2]) / 3
            if avg > threshold - 30:
                alpha = int(255 * ((threshold - avg) / 30))
                new_data.append((item[0], item[1], item[2], max(0, alpha)))
            else: new_data.append(item)
    img.putdata(new_data)
    out = io.BytesIO()
    img.save(out, format="PNG")
    return out.getvalue()

# --- CONFIGURACIÓN DE PÁGINA ---
'''
code = code.replace('# --- CONFIGURACIÓN DE PÁGINA ---', insert_code.strip())

old_sig = '''st.markdown("##### ✍️ Firma Digital")
    uploaded_sig = st.file_uploader("Subir Firma (PNG transparente)", type=["png"], key="sig_uploader")
    if uploaded_sig:
        st.session_state.signature_bytes = uploaded_sig.read()
        uploaded_sig.seek(0)
        sig_img = Image.open(uploaded_sig)
        st.image(sig_img, caption="Firma cargada", use_container_width=True)
    elif 'signature_bytes' in st.session_state:
        sig_img = Image.open(io.BytesIO(st.session_state.signature_bytes))
        st.image(sig_img, caption="Firma actual", use_container_width=True)
    else:
        st.info("Sube tu firma PNG para generar los sellos")'''

new_sig = '''st.markdown("##### ✨ Limpieza de Fondo")
    clean_bg = st.checkbox("🪄 Remover fondo blanco", value=cfg.get("clean_bg", False), key="chk_bg", help="Convierte fondos blancos a transparentes.")
    bg_threshold = 240
    if clean_bg:
        bg_threshold = st.slider("Sensibilidad de Blanco", 150, 255, int(cfg.get("bg_threshold", 240)), key="slider_bg")
    if clean_bg != cfg.get("clean_bg", False): cfg.set("clean_bg", clean_bg)
    if clean_bg and float(bg_threshold) != float(cfg.get("bg_threshold", 240.0)): cfg.set("bg_threshold", bg_threshold)

    st.markdown("##### ✍️ Firma Digital")
    uploaded_sig = st.file_uploader("Subir Firma", type=["png", "jpg", "jpeg"], key="sig_uploader")
    if uploaded_sig:
        st.session_state.raw_signature_bytes = uploaded_sig.read()
        uploaded_sig.seek(0)
    if 'raw_signature_bytes' in st.session_state:
        st.session_state.signature_bytes = process_transparency(st.session_state.raw_signature_bytes, threshold=bg_threshold, clean=clean_bg)
        st.image(Image.open(io.BytesIO(st.session_state.signature_bytes)), caption="Firma Procesada", use_container_width=True)
    elif 'signature_bytes' in st.session_state:
        st.image(Image.open(io.BytesIO(st.session_state.signature_bytes)), caption="Firma actual", use_container_width=True)
    else:
        st.info("Sube tu firma (PNG/JPG) para generar sellos")'''
code = code.replace(old_sig, new_sig)

old_custom = '''if "Pre-diseñada" in sello2_mode:
        cfg.set("sello2_mode", "custom")
        custom_stamp = st.file_uploader("Subir Sello Pre-diseñado (PNG)", type=["png"], key="custom_stamp_uploader")
        if custom_stamp:
            st.session_state.custom_stamp_bytes = custom_stamp.read()
            st.success("Sello personalizado cargado")
    else:'''
new_custom = '''if "Pre-diseñada" in sello2_mode:
        cfg.set("sello2_mode", "custom")
        custom_stamp = st.file_uploader("Subir Sello Pre-diseñado", type=["png", "jpg", "jpeg"], key="custom_stamp_uploader")
        if custom_stamp:
            st.session_state.raw_custom_stamp_bytes = custom_stamp.read()
            st.success("Sello personalizado cargado")
        if 'raw_custom_stamp_bytes' in st.session_state:
            st.session_state.custom_stamp_bytes = process_transparency(st.session_state.raw_custom_stamp_bytes, threshold=bg_threshold, clean=clean_bg)
            st.caption("Sello procesado:")
            st.image(Image.open(io.BytesIO(st.session_state.custom_stamp_bytes)), use_container_width=True)
    else:'''
code = code.replace(old_custom, new_custom)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(code)
    print("PATCH APPLIED SUCCESSFULLY")
