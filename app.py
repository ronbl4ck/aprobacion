import streamlit as st
import os
import io
import json
import datetime
from PIL import Image
from src.pdf_manager import PDFManager
from src.stamp_engine import StampEngine
from src.config_manager import ConfigManager

# --- HOTFIX for streamlit-drawable-canvas + Streamlit 1.40+ ---
import streamlit.elements.image as sei
try:
    from streamlit.elements.lib import image_utils
    _real_image_to_url = image_utils.image_to_url
    def wrapped_image_to_url(image_data, layout_config, *args, **kwargs):
        if isinstance(layout_config, int):
            from dataclasses import dataclass
            @dataclass
            class FakeConfig:
                width: int
                use_column_width: bool = False
            return _real_image_to_url(image_data, FakeConfig(width=layout_config), *args, **kwargs)
        return _real_image_to_url(image_data, layout_config, *args, **kwargs)
    sei.image_to_url = wrapped_image_to_url
except Exception:
    pass
# --------------------------------------------------------------
from streamlit_drawable_canvas import st_canvas


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
st.set_page_config(
    page_title="Autofirma PDF | Sistema Aprobación",
    page_icon="🖋️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- GOOGLE FONTS (Inter) ---
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
""", unsafe_allow_html=True)

# --- ESTILOS PREMIUM ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    *, html, body, [class*="st-"] {
        font-family: 'Inter', sans-serif !important;
    }

    .main { background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%); }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d1117 0%, #161b22 100%);
        border-right: 1px solid rgba(48, 54, 61, 0.6);
    }
    section[data-testid="stSidebar"] * {
        color: #c9d1d9 !important;
    }
    section[data-testid="stSidebar"] .stTextInput > div > div > input,
    section[data-testid="stSidebar"] .stSelectbox > div > div {
        background-color: #21262d !important;
        border: 1px solid #30363d !important;
        color: #c9d1d9 !important;
        border-radius: 8px;
    }

    h1 { 
        background: linear-gradient(90deg, #58a6ff, #bc8cff, #f778ba);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700 !important;
        letter-spacing: -0.5px;
    }
    h2, h3 { color: #c9d1d9 !important; font-weight: 600 !important; }
    p, span, label, div { color: #8b949e; }

    .stButton > button {
        width: 100%;
        border-radius: 10px;
        height: 3em;
        font-weight: 600 !important;
        border: none;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-size: 0.85em;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(88, 166, 255, 0.25);
    }

    .stDownloadButton > button {
        background: linear-gradient(135deg, #238636, #2ea043) !important;
        color: white !important;
        border-radius: 10px !important;
        height: 3.2em;
        font-weight: 700 !important;
        border: none !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .stDownloadButton > button:hover {
        background: linear-gradient(135deg, #2ea043, #3fb950) !important;
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(46, 160, 67, 0.35) !important;
    }

    .stExpander {
        border: 1px solid #30363d !important;
        border-radius: 12px !important;
        background-color: rgba(22, 27, 34, 0.6) !important;
        backdrop-filter: blur(10px);
    }
    .stExpander summary {
        color: #c9d1d9 !important;
        font-weight: 600 !important;
    }

    div[data-testid="stFileUploader"] {
        border: 2px dashed #30363d !important;
        border-radius: 12px !important;
        background: rgba(22, 27, 34, 0.4) !important;
        transition: border-color 0.3s;
    }
    div[data-testid="stFileUploader"]:hover {
        border-color: #58a6ff !important;
    }

    .stSlider > div > div > div > div {
        background: linear-gradient(90deg, #58a6ff, #bc8cff) !important;
    }

    .stRadio > div { gap: 0.5rem; }
    .stRadio label {
        background: rgba(22, 27, 34, 0.6) !important;
        border: 1px solid #30363d !important;
        border-radius: 8px !important;
        padding: 8px 16px !important;
        transition: all 0.2s !important;
    }
    .stRadio label:hover {
        border-color: #58a6ff !important;
        background: rgba(88, 166, 255, 0.1) !important;
    }

    .glass-card {
        background: rgba(22, 27, 34, 0.7);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(48, 54, 61, 0.6);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }

    .metric-card {
        background: linear-gradient(135deg, rgba(88, 166, 255, 0.1), rgba(188, 140, 255, 0.1));
        border: 1px solid rgba(88, 166, 255, 0.2);
        border-radius: 12px;
        padding: 1rem 1.5rem;
        text-align: center;
    }
    .metric-card h3 { font-size: 2rem !important; color: #58a6ff !important; margin: 0 !important; }
    .metric-card p { font-size: 0.8rem; color: #8b949e; margin: 0; }

    .footer-text {
        text-align: center;
        color: #484f58;
        font-size: 0.75rem;
        padding: 2rem 0 1rem 0;
        border-top: 1px solid #21262d;
        margin-top: 2rem;
    }

    div[data-testid="stImage"] {
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid #30363d;
    }
</style>
""", unsafe_allow_html=True)


# --- INICIALIZACIÓN DE ESTADO ---
if 'config_mgr' not in st.session_state:
    st.session_state.config_mgr = ConfigManager()

if 'pdf_manager' not in st.session_state:
    st.session_state.pdf_manager = PDFManager()

if 'stamp_engine' not in st.session_state:
    st.session_state.stamp_engine = StampEngine()

cfg = st.session_state.config_mgr
if 'pdf_ready_data' not in st.session_state:
    st.session_state.pdf_ready_data = None
if 'pdf_ready_name' not in st.session_state:
    st.session_state.pdf_ready_name = ''


# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### 🖋️ Autofirma")
    st.caption("Sistema de Aprobación de Factibilidad")
    st.divider()

    st.markdown("##### 👤 Datos del Ingeniero")
    new_name = st.text_input("Nombre Completo", value=cfg.get("engineer_name", ""), key="sb_name")
    new_cip = st.text_input("Número CIP", value=cfg.get("cip_number", ""), key="sb_cip")
    new_type = st.text_input("Título Profesional", value=cfg.get("engineer_type", "Ingeniero Electricista"), key="sb_type")

    # Guardar cambios  
    if new_name != cfg.get("engineer_name", ""):
        cfg.set("engineer_name", new_name)
    if new_cip != cfg.get("cip_number", ""):
        cfg.set("cip_number", new_cip)
    if new_type != cfg.get("engineer_type", "Ingeniero Electricista"):
        cfg.set("engineer_type", new_type)

    st.divider()

    st.markdown("##### ✨ Limpieza de Fondo")
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
        st.info("Sube tu firma (PNG/JPG) para generar sellos")

    st.divider()

    # Modo Sello 2
    st.markdown("##### ⚙️ Modo Sello 2")
    sello2_mode = st.radio(
        "Tipo de Sello para Cuerpo:",
        ["Generar (Nombre + CIP)", "Imagen Pre-diseñada"],
        index=0 if cfg.get("sello2_mode", "generate") == "generate" else 1,
        key="sello2_mode_radio",
        horizontal=True
    )
    if "Pre-diseñada" in sello2_mode:
        cfg.set("sello2_mode", "custom")
        custom_stamp = st.file_uploader("Subir Sello Pre-diseñado", type=["png", "jpg", "jpeg"], key="custom_stamp_uploader")
        if custom_stamp:
            st.session_state.raw_custom_stamp_bytes = custom_stamp.read()
            st.success("Sello personalizado cargado")
        if 'raw_custom_stamp_bytes' in st.session_state:
            st.session_state.custom_stamp_bytes = process_transparency(st.session_state.raw_custom_stamp_bytes, threshold=bg_threshold, clean=clean_bg)
            st.caption("Sello procesado:")
            st.image(Image.open(io.BytesIO(st.session_state.custom_stamp_bytes)), use_container_width=True)
    else:
        cfg.set("sello2_mode", "generate")


# --- CUERPO PRINCIPAL ---
st.title("🖋️ Autofirma de Documentos PDF")
st.markdown('<p style="color: #8b949e; font-size: 1.05rem; margin-top: -10px;">Carga tu documento, posiciona tus sellos y genera tu PDF firmado en segundos.</p>', unsafe_allow_html=True)

# --- MÉTRICAS ---
col_m1, col_m2, col_m3, col_m4 = st.columns(4)
with col_m1:
    st.markdown(f'<div class="metric-card"><h3>{cfg.get("engineer_name", "—") or "—"}</h3><p>Ingeniero</p></div>', unsafe_allow_html=True)
with col_m2:
    st.markdown(f'<div class="metric-card"><h3>{cfg.get("cip_number", "—") or "—"}</h3><p>N° CIP</p></div>', unsafe_allow_html=True)
with col_m3:
    pages_loaded = st.session_state.get("total_pages", 0)
    st.markdown(f'<div class="metric-card"><h3>{pages_loaded}</h3><p>Páginas</p></div>', unsafe_allow_html=True)
with col_m4:
    status_text = "✅ Listo" if ('signature_bytes' in st.session_state and pages_loaded > 0) else "⏳ Pendiente"
    st.markdown(f'<div class="metric-card"><h3>{status_text}</h3><p>Estado</p></div>', unsafe_allow_html=True)

st.markdown("")

# --- LAYOUT PRINCIPAL ---
col_config, col_preview = st.columns([1, 2])

with col_config:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("📂 Documento PDF")
    uploaded_pdf = st.file_uploader("Seleccionar archivo PDF", type=["pdf"], key="pdf_uploader")

    if uploaded_pdf:
        if 'pdf_bytes' not in st.session_state or st.session_state.get('pdf_name') != uploaded_pdf.name:
            st.session_state.pdf_bytes = uploaded_pdf.read()
            st.session_state.pdf_name = uploaded_pdf.name
            pdf_doc, total_pages = st.session_state.pdf_manager.load_pdf(io.BytesIO(st.session_state.pdf_bytes))
            st.session_state.pdf_doc = pdf_doc
            st.session_state.total_pages = total_pages
            st.rerun()

        st.success(f"📄 **{st.session_state.pdf_name}** — {st.session_state.total_pages} páginas")
    st.markdown('</div>', unsafe_allow_html=True)

    # --- FECHA ---
    with st.expander("📅 Fecha del Sello 1", expanded=True):
        today_str = datetime.date.today().strftime('%d/%m/%Y')
        saved_date = cfg.get("start_date", "")
        start_date = st.text_input("Fecha (DD/MM/YYYY)", value=saved_date if saved_date else today_str, key="start_date_input")
        if st.button("📆 Usar Fecha de Hoy", key="btn_today"):
            cfg.set("start_date", today_str)
            st.rerun()
        if start_date != cfg.get("start_date", ""):
            cfg.set("start_date", start_date)

    # --- SELLOS ON/OFF ---
    with st.expander("🖋️ Sellos a Aplicar", expanded=True):
        apply_s1 = st.checkbox("Aplicar Sello 1 (Carátula / V°B°)", value=cfg.get("apply_sello1", True), key="chk_s1")
        apply_s2 = st.checkbox("Aplicar Sello 2 (Cuerpo)", value=cfg.get("apply_sello2", True), key="chk_s2")
        cfg.config['apply_sello1'] = apply_s1
        cfg.config['apply_sello2'] = apply_s2

    # --- ESCALAS ---
    with st.expander("📐 Escalas", expanded=False):
        cover_scale = st.slider("Escala Sello 1 (%)", 10, 200, int(cfg.get("cover_scale", 100)), key="slider_cover_scale")
        body_scale = st.slider("Escala Sello 2 (%)", 10, 200, int(cfg.get("body_scale", 100)), key="slider_body_scale")
        cfg.config['cover_scale'] = cover_scale
        cfg.config['body_scale'] = body_scale

    # --- RANGOS DE PÁGINAS ---
    with st.expander("📑 Rangos de Páginas", expanded=False):
        st.markdown("**Sello 1 (Carátula)**")
        cover_ranges_raw = cfg.get("cover_ranges", [{"start": "1", "end": "1"}])
        if not cover_ranges_raw:
            cover_ranges_raw = [{"start": "1", "end": "1"}]
        cover_ranges = st.data_editor(
            cover_ranges_raw,
            num_rows="dynamic",
            key="de_cover_ranges",
            column_config={
                "start": st.column_config.TextColumn("Desde Pág"),
                "end": st.column_config.TextColumn("Hasta Pág"),
            }
        )
        cfg.config['cover_ranges'] = cover_ranges

        st.markdown("**Sello 2 (Cuerpo)**")
        body_ranges_raw = cfg.get("body_ranges", [{"start": "2", "end": "final"}])
        if not body_ranges_raw:
            body_ranges_raw = [{"start": "2", "end": "final"}]
        body_ranges = st.data_editor(
            body_ranges_raw,
            num_rows="dynamic",
            key="de_body_ranges",
            column_config={
                "start": st.column_config.TextColumn("Desde Pág"),
                "end": st.column_config.TextColumn("Hasta Pág"),
            }
        )
        cfg.config['body_ranges'] = body_ranges

        body_exceptions = st.text_input(
            "Excepciones Sello 2 (páginas a excluir)",
            value=cfg.get("body_exceptions", ""),
            help="Ej: 3, 5, 10",
            key="body_exc"
        )
        cfg.config['body_exceptions'] = body_exceptions

    # --- GUARDAR CONFIG ---
    cfg.save_config()


# --- PREVISUALIZACIÓN ---
with col_preview:
    if uploaded_pdf and 'pdf_doc' in st.session_state:
        st.subheader("👁️ Previsualización")

        # Paginación y Zoom
        cp1, cp2, cp3 = st.columns([1, 2, 1])
        with cp1:
            zoom_level = st.selectbox("Zoom", [0.8, 1.0, 1.2, 1.5, 2.0], index=1, key="zoom_select")
        with cp2:
            page_num = st.number_input(
                "Página:",
                min_value=1,
                max_value=st.session_state.total_pages,
                value=1,
                step=1,
                key="page_nav"
            )
        with cp3:
            modo_sello = st.radio(
                "Posicionar:",
                ["Sello 1", "Sello 2"],
                horizontal=True,
                key="stamp_mode"
            )

        # Renderizar página
        page_idx = page_num - 1
        page_img = st.session_state.pdf_manager.get_page_image(st.session_state.pdf_doc, page_idx, zoom=zoom_level)

        if page_img:
            

            st.info(f"🎯 Haz clic en la imagen para posicionar el **{modo_sello}**")


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

            canvas_result = st_canvas(
                fill_color="rgba(88, 166, 255, 0.15)",
                stroke_width=2,
                stroke_color="#58a6ff" if "1" in modo_sello else "#f778ba",
                background_image=page_img,
                update_streamlit=True,
                height=page_img.size[1],
                width=page_img.size[0],
                drawing_mode="point",
                point_display_radius=6,
                key="canvas_main",
            )

            if canvas_result.json_data is not None:
                objects = canvas_result.json_data.get("objects", [])
                if len(objects) > 0:
                    last_point = objects[-1]
                    real_x = last_point["left"] / zoom_level
                    real_y = last_point["top"] / zoom_level

                    if "1" in modo_sello:
                        cfg.config['cover_coords'] = [real_x, real_y]
                    else:
                        cfg.config['body_coords'] = [real_x, real_y]
                    cfg.save_config()

                    st.success(f"📍 Coordenadas guardadas: **X={int(real_x)}, Y={int(real_y)}**")

        # --- BOTÓN DE GENERACIÓN ---
        st.markdown("")
        if st.button("🚀 Generar PDF Firmado", type="primary", use_container_width=True, key="btn_generate"):
            if 'signature_bytes' not in st.session_state and cfg.get("sello2_mode") != "custom":
                st.error("⚠️ Debes subir tu firma digital primero (Sidebar → Firma Digital).")
            else:
                with st.status("⚙️ Procesando PDF...", expanded=True) as status:
                    import tempfile

                    # Guardar firma temporalmente
                    tmp_sig_path = None
                    if 'signature_bytes' in st.session_state:
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_sig:
                            tmp_sig.write(st.session_state.signature_bytes)
                            tmp_sig_path = tmp_sig.name

                    try:
                        base_path = os.path.dirname(os.path.abspath(__file__))
                        tpl_path = os.path.join(base_path, "assets", "plantilla_caratula.png")

                        layout_cfg = {
                            "date1": cfg.get("tpl_date1_coords"),
                            "date2": cfg.get("tpl_date2_coords"),
                            "sig": cfg.get("tpl_sig_coords"),
                            "date_scale": cfg.get("tpl_date_scale", 100),
                            "sig_scale": cfg.get("tpl_sig_scale", 100)
                        }

                        st.write("🔨 Generando sellos...")

                        # Sello 1 (Carátula)
                        cover_img = None
                        if cfg.get("apply_sello1", True):
                            if not os.path.exists(tpl_path):
                                st.warning(f"Plantilla de carátula no encontrada en: {tpl_path}")
                            else:
                                cover_img = st.session_state.stamp_engine.generate_cover_stamp(
                                    tpl_path, tmp_sig_path,
                                    cfg.get("start_date", ""),
                                    layout_coords=layout_cfg
                                )

                        # Sello 2 (Cuerpo)
                        body_img = None
                        if cfg.get("apply_sello2", True):
                            if cfg.get("sello2_mode") == "custom" and 'custom_stamp_bytes' in st.session_state:
                                body_img = Image.open(io.BytesIO(st.session_state.custom_stamp_bytes)).convert("RGBA")
                            elif tmp_sig_path:
                                body_img = st.session_state.stamp_engine.generate_body_stamp(
                                    tmp_sig_path,
                                    cfg.get("engineer_name", ""),
                                    cfg.get("cip_number", ""),
                                    cfg.get("engineer_type", "Ingeniero Electricista")
                                )

                        st.write("📎 Ensamblando documento...")

                        # Recargar PDF fresco
                        fresh_doc, _ = st.session_state.pdf_manager.load_pdf(io.BytesIO(st.session_state.pdf_bytes))
                        out_buffer = io.BytesIO()

                        success, msg = st.session_state.pdf_manager.process_and_save(
                            fresh_doc, cover_img, body_img,
                            cfg.config, out_buffer
                        )

                        if success:
                            status.update(label="✅ ¡PDF Generado con éxito!", state="complete")
                            out_name = os.path.splitext(st.session_state.pdf_name)[0] + "_firmado.pdf"

                            st.session_state.pdf_ready_data = out_buffer.getvalue()
                            st.session_state.pdf_ready_name = out_name
                            st.rerun()
                        else:
                            st.error(f"Error: {msg}")

                    except Exception as e:
                        st.error(f"Error crítico: {e}")
                    finally:
                        if tmp_sig_path and os.path.exists(tmp_sig_path):
                            os.remove(tmp_sig_path)

    else:
        st.markdown("""
        <div class="glass-card" style="text-align:center; padding: 4rem 2rem;">
            <h2 style="color: #58a6ff !important;">📄 Sube un PDF para comenzar</h2>
            <p style="color: #8b949e; font-size: 1.1rem;">
                Arrastra o selecciona tu documento en el panel izquierdo.<br>
                Luego posiciona tus sellos con un clic.
            </p>
        </div>
        """, unsafe_allow_html=True)



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

# --- FOOTER ---
st.markdown('<div class="footer-text">© L.Navarrete · Sistema de Aprobación de Factibilidad · Powered by Streamlit</div>', unsafe_allow_html=True)
