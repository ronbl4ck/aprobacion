import datetime
import io
import os
import tempfile

import streamlit as st
import streamlit.elements.image as sei
from PIL import Image, ImageDraw

from src.config_manager import ConfigManager
from src.pdf_manager import PDFManager
from src.stamp_engine import StampEngine
from src.profile_manager import ProfileManager


# PARCHE DE COMPATIBILIDAD PARA VERSIONES NUEVAS DE STREAMLIT
try:
    from streamlit.elements.lib import image_utils
    _real_image_to_url = image_utils.image_to_url

    def wrapped_image_to_url(image_data, layout_config, *args, **kwargs):
        # Si envian un numero (int) en vez de un objeto config, lo envolvemos
        if isinstance(layout_config, int):
            from dataclasses import dataclass
            @dataclass
            class FakeConfig:
                width: int
                use_column_width: bool = False
                use_container_width: bool = False
            return _real_image_to_url(image_data, FakeConfig(width=layout_config), *args, **kwargs)
        return _real_image_to_url(image_data, layout_config, *args, **kwargs)

    sei.image_to_url = wrapped_image_to_url
except Exception:
    pass

from streamlit_drawable_canvas import st_canvas


import numpy as np

def process_transparency(img_bytes, threshold=240, clean=False):
    if not clean:
        return img_bytes

    img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
    data = np.array(img)
    
    r, g, b, a = data[:,:,0], data[:,:,1], data[:,:,2], data[:,:,3]
    
    avg = (r.astype(int) + g.astype(int) + b.astype(int)) / 3.0
    
    mask_white = (r >= threshold) & (g >= threshold) & (b >= threshold)
    data[mask_white, 3] = 0
    
    mask_soft = (~mask_white) & (avg > threshold - 30)
    alpha_vals = 255 * ((threshold - avg[mask_soft]) / 30.0)
    data[mask_soft, 3] = np.maximum(0, alpha_vals).astype(np.uint8)
    
    new_img = Image.fromarray(data, "RGBA")
    out = io.BytesIO()
    new_img.save(out, format="PNG")
    return out.getvalue()


def get_body_preview_size(cfg):
    base_factor = 0.35

    if cfg.get("sello2_mode") == "custom" and "custom_stamp_bytes" in st.session_state:
        custom_img = Image.open(io.BytesIO(st.session_state.custom_stamp_bytes)).convert("RGBA")
        return (
            custom_img.size[0] * base_factor * (cfg.get("body_scale", 100) / 100.0),
            custom_img.size[1] * base_factor * (cfg.get("body_scale", 100) / 100.0),
        )

    if "signature_bytes" not in st.session_state:
        return (0, 0)

    tmp_sig_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_sig:
            tmp_sig.write(st.session_state.signature_bytes)
            tmp_sig_path = tmp_sig.name

        sw, sh = st.session_state.stamp_engine.get_body_stamp_size(
            tmp_sig_path,
            cfg.get("engineer_name"),
            cfg.get("cip_number"),
            cfg.get("engineer_type"),
        )
        return (
            sw * base_factor * (cfg.get("body_scale", 100) / 100.0),
            sh * base_factor * (cfg.get("body_scale", 100) / 100.0),
        )
    finally:
        if tmp_sig_path and os.path.exists(tmp_sig_path):
            os.remove(tmp_sig_path)




st.set_page_config(
    page_title="Autofirma PDF | Sistema de Aprobacion",
    page_icon="P",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, .main, .main button, .main input, .main textarea, .main select,
    .main label, .main p, .main span, .main li, .main div:not([data-testid]),
    section[data-testid="stSidebar"], section[data-testid="stSidebar"] button,
    section[data-testid="stSidebar"] input, section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] p {
        font-family: 'Inter', sans-serif !important;
    }

    .material-symbols-rounded,
    .material-icons,
    [data-testid="icon"],
    section[data-testid="stSidebar"] button span,
    section[data-testid="stSidebar"] button i,
    [data-testid="stExpanderToggleIcon"] span,
    [data-testid="stExpanderToggleIcon"] i {
        font-family: "Material Symbols Rounded", "Material Icons" !important;
    }

    .main {
        background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%);
    }

    .main p, .main li, .main span {
        color: #8b949e;
    }

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

    h2, h3 {
        color: #c9d1d9 !important;
        font-weight: 600 !important;
    }

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

    .stExpander {
        border: 1px solid #30363d !important;
        border-radius: 12px !important;
        background-color: rgba(22, 27, 34, 0.6) !important;
        backdrop-filter: blur(10px);
    }

    .stExpander summary {
        color: #c9d1d9 !important;
        font-weight: 600 !important;
        display: flex !important;
        align-items: center !important;
        gap: 0.5rem !important;
        line-height: 1.3 !important;
    }

    .stExpander summary p {
        margin: 0 !important;
        color: #c9d1d9 !important;
    }

    .stExpander summary svg {
        flex: 0 0 auto !important;
        margin-right: 0.25rem !important;
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

    .stRadio > div {
        gap: 0.5rem;
    }

    .stRadio label {
        background: rgba(22, 27, 34, 0.6) !important;
        border: 1px solid #30363d !important;
        border-radius: 8px !important;
        padding: 8px 16px !important;
        transition: all 0.2s !important;
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

    .metric-card h3 {
        font-size: 2rem !important;
        color: #58a6ff !important;
        margin: 0 !important;
    }

    .metric-card p {
        font-size: 0.8rem;
        color: #8b949e;
        margin: 0;
    }

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
""",
    unsafe_allow_html=True,
)

if "config_mgr" not in st.session_state:
    st.session_state.config_mgr = ConfigManager()
if "pdf_manager" not in st.session_state:
    st.session_state.pdf_manager = PDFManager()
if "stamp_engine" not in st.session_state:
    st.session_state.stamp_engine = StampEngine()
if "pdf_ready_data" not in st.session_state:
    st.session_state.pdf_ready_data = None
if "pdf_ready_name" not in st.session_state:
    st.session_state.pdf_ready_name = ""
if "canvas_nonce" not in st.session_state:
    st.session_state.canvas_nonce = 0
if "layout_canvas_nonce" not in st.session_state:
    st.session_state.layout_canvas_nonce = 0
if "profile_mgr" not in st.session_state:
    st.session_state.profile_mgr = ProfileManager()
if "active_profile" not in st.session_state:
    st.session_state.active_profile = None

cfg = st.session_state.config_mgr

with st.sidebar:
    st.markdown("### Autofirma")
    st.caption("Sistema de Aprobacion de Factibilidad")
    st.divider()
    
    prof_mgr = st.session_state.profile_mgr



    if st.session_state.active_profile:
        st.markdown("##### Limpieza de Fondo")
        clean_bg = st.checkbox(
            "Remover fondo blanco",
            value=cfg.get("clean_bg", False),
            key="chk_bg",
            help="Convierte fondos blancos a transparentes.",
        )
        bg_threshold = 240
        if clean_bg:
            bg_threshold = st.slider("Sensibilidad del blanco", 150, 255, int(cfg.get("bg_threshold", 240)), key="slider_bg")
        if clean_bg != cfg.get("clean_bg", False):
            cfg.set("clean_bg", clean_bg)
        if clean_bg and float(bg_threshold) != float(cfg.get("bg_threshold", 240.0)):
            cfg.set("bg_threshold", bg_threshold)

        if "raw_signature_bytes" in st.session_state:
            st.session_state.signature_bytes = process_transparency(
                st.session_state.raw_signature_bytes,
                threshold=bg_threshold,
                clean=clean_bg,
            )
            st.image(Image.open(io.BytesIO(st.session_state.signature_bytes)), caption="Firma actual procesada", width="stretch")
        else:
            st.info("Este perfil no tiene firma pura subida.")

        if cfg.get("sello2_mode") == "custom" and "raw_custom_stamp_bytes" in st.session_state:
            st.session_state.custom_stamp_bytes = process_transparency(
                st.session_state.raw_custom_stamp_bytes,
                threshold=bg_threshold,
                clean=clean_bg,
            )
            st.image(Image.open(io.BytesIO(st.session_state.custom_stamp_bytes)), caption="Sello Completo procesado", width="stretch")

        st.divider()



st.title("Autofirma de Documentos PDF")
st.markdown(
    '<p style="color: #8b949e; font-size: 1.05rem; margin-top: -10px;">'
    "Carga tu documento, posiciona tus sellos y genera tu PDF firmado en segundos."
    "</p>",
    unsafe_allow_html=True,
)

col_m1, col_m2, col_m3, col_m4 = st.columns(4)
has_active_profile = bool(st.session_state.active_profile)
metric_name = cfg.get("engineer_name", "-") if has_active_profile else "-"
metric_cip = cfg.get("cip_number", "-") if has_active_profile else "-"
metric_pages = st.session_state.get("total_pages", 0) if has_active_profile else 0
metric_status = "Listo" if (has_active_profile and "signature_bytes" in st.session_state and metric_pages > 0) else (
    "Pendiente" if has_active_profile else "Sin perfil"
)
with col_m1:
    st.markdown(
        f'<div class="metric-card"><h3>{metric_name or "-"}</h3><p>Ingeniero</p></div>',
        unsafe_allow_html=True,
    )
with col_m2:
    st.markdown(
        f'<div class="metric-card"><h3>{metric_cip or "-"}</h3><p>No. CIP</p></div>',
        unsafe_allow_html=True,
    )
with col_m3:
    pages_loaded = metric_pages
    st.markdown(f'<div class="metric-card"><h3>{metric_pages}</h3><p>Paginas</p></div>', unsafe_allow_html=True)
with col_m4:
    st.markdown(f'<div class="metric-card"><h3>{metric_status}</h3><p>Estado</p></div>', unsafe_allow_html=True)

if not st.session_state.active_profile:
    st.markdown('<div class="glass-card" style="padding: 2rem; margin-top: 2rem;">', unsafe_allow_html=True)
    tab_login, tab_register = st.tabs(["Ingresar", "Registrar Nuevo Perfil"])
    
    prof_mgr = st.session_state.profile_mgr
    
    with tab_login:
        profile_names = prof_mgr.get_profile_names()
        st.subheader("Acceso de Ingeniero")
        if not profile_names:
            st.info("No hay perfiles creados. Ve a 'Registrar Nuevo Perfil'.")
        else:
            sel_prof = st.selectbox("Seleccionar Perfil", ["-- Seleccionar --"] + profile_names, key="sel_prof_login")
            if sel_prof != "-- Seleccionar --":
                pin_input = st.text_input("PIN (6 digitos)", type="password", key="pin_login")
                if st.button("Ingresar", key="btn_login", type="primary"):
                    auth_data = prof_mgr.authenticate(sel_prof, pin_input)
                    if auth_data:
                        st.session_state.active_profile = auth_data["name"]
                        cfg.set("engineer_name", auth_data["name"])
                        cfg.set("cip_number", auth_data["cip"])
                        cfg.set("engineer_type", auth_data["title"])
                        cfg.set("sello2_mode", auth_data.get("sello2_mode", "generate"))
                        
                        if "tpl_coords" in auth_data:
                            cfg.config["tpl_date1_coords"] = auth_data["tpl_coords"].get("date1")
                            cfg.config["tpl_date2_coords"] = auth_data["tpl_coords"].get("date2")
                            cfg.config["tpl_sig_coords"] = auth_data["tpl_coords"].get("sig")
                            cfg.config["tpl_date_scale"] = auth_data["tpl_coords"].get("date_scale", 100)
                            cfg.config["tpl_sig_scale"] = auth_data["tpl_coords"].get("sig_scale", 100)
                            cfg.save_config()

                        if auth_data.get("signature_bytes"):
                            st.session_state.raw_signature_bytes = auth_data["signature_bytes"]
                        if auth_data.get("custom_stamp_bytes"):
                            st.session_state.raw_custom_stamp_bytes = auth_data["custom_stamp_bytes"]
                        st.rerun()
                    else:
                        st.error("PIN incorrecto.")
                        
    with tab_register:
        st.subheader("Crear Nuevo Perfil de Ingeniero")
        col_rg1, col_rg2 = st.columns([1, 1.2])
        with col_rg1:
            new_prof_name = st.text_input("Nombre Completo", key="new_prof_name")
            new_prof_cip = st.text_input("No. CIP", key="new_prof_cip")
            new_prof_title = st.text_input("Titulo Profesional", value="Ingeniero Electricista", key="new_prof_title")
            new_prof_pin = st.text_input("PIN (6 digitos)", type="password", key="new_prof_pin")
            st.markdown("**Firma y Sellos**")
            new_prof_sig = st.file_uploader("Firma Pura (Para Caratula)", type=["png", "jpg", "jpeg"], key="new_prof_sig")
            
            s_mode = st.radio("Sello 2 (Cuerpo)", ["Generar Automatico", "Usar Sello Completo"], key="new_prof_mode")
            new_prof_custom = None
            if "Completo" in s_mode:
                new_prof_custom = st.file_uploader("Imagen Sello Completo", type=["png", "jpg", "jpeg"], key="new_prof_custom")
            
            st.markdown("**Procesamiento de imagen**")
            rg_clean_bg = st.checkbox("Procesar transparencia permanentemente (Quitar fondo blanco)", value=True, help="Guardara las firmas en formato transparente para asegurar el mejor rendimiento del visor.")
            rg_bg_threshold = 240
            if rg_clean_bg:
                rg_bg_threshold = st.slider("Sensibilidad del blanco (Filtro inicial)", 150, 255, 240, key="rg_bg_slider")
                
        with col_rg2:
            st.markdown("**Editor de Layout (Caratula Sello 1)**")
            base_tpl_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "plantilla_caratula.png")
            if not os.path.exists(base_tpl_path):
                base_tpl_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "plantilla_caratula.png")
            
            if os.path.exists(base_tpl_path):
                tpl_img = Image.open(base_tpl_path).convert("RGBA")
                
                edit_mode = st.radio("Mover:", ["Firma", "Fecha Inicial", "Fecha Final"], horizontal=True, key="rg_edit_mode")
                stroke_color = "#f778ba" if "Firma" in edit_mode else ("#58a6ff" if "Inicial" in edit_mode else "#50fa7b")
                st.caption("Ajusta la posicion haciendo clic en la imagen.")
                
                # Default coords
                if "rg_tpl_coords" not in st.session_state:
                    st.session_state.rg_tpl_coords = {
                        "date1": [int(tpl_img.size[0]*0.55), int(tpl_img.size[1]*0.53)],
                        "date2": [int(tpl_img.size[0]*0.55), int(tpl_img.size[1]*0.69)],
                        "sig": [int(tpl_img.size[0]*0.1), int(tpl_img.size[1]*0.7)],
                        "date_scale": 100,
                        "sig_scale": 100
                    }

                preview_img = tpl_img.copy()
                preview_draw = ImageDraw.Draw(preview_img, "RGBA")
                display_scale = 0.8

                coords = st.session_state.rg_tpl_coords
                date_scale = coords.get("date_scale", 100)
                sig_scale = coords.get("sig_scale", 100)

                date_font_size = int((tpl_img.size[1] * 0.08) * (date_scale / 100.0))
                date_box_w = max(int(date_font_size * 4.8), 90)
                date_box_h = max(int(date_font_size * 1.25), 24)

                sig_w = int(tpl_img.size[0] * 0.35 * (sig_scale / 100.0))
                sig_h = max(int(sig_w * 0.38), 30)
                if new_prof_sig:
                    try:
                        sig_preview = Image.open(io.BytesIO(new_prof_sig.getvalue()))
                        ratio = sig_w / float(sig_preview.size[0])
                        sig_h = max(int(float(sig_preview.size[1]) * ratio), 30)
                    except Exception:
                        pass

                overlay_specs = [
                    ("sig", (247, 120, 186, 70), (247, 120, 186), (sig_w, sig_h), "Firma"),
                    ("date1", (88, 166, 255, 70), (88, 166, 255), (date_box_w, date_box_h), "Fecha Inicial"),
                    ("date2", (80, 250, 123, 70), (80, 250, 123), (date_box_w, date_box_h), "Fecha Final"),
                ]

                for key_name, fill_rgba, outline_rgb, (box_w, box_h), label in overlay_specs:
                    box_coords = coords.get(key_name)
                    if not box_coords:
                        continue
                    x0, y0 = box_coords
                    x1, y1 = x0 + box_w, y0 + box_h
                    preview_draw.rectangle([x0, y0, x1, y1], fill=fill_rgba, outline=outline_rgb, width=3)
                    preview_draw.text((x0 + 6, max(y0 - 22, 0)), label, fill=outline_rgb)

                canvas_result = st_canvas(
                    fill_color="rgba(255, 165, 0, 0.3)",
                    stroke_width=4,
                    stroke_color=stroke_color,
                    background_image=preview_img,
                    update_streamlit=True,
                    height=int(preview_img.size[1] * display_scale), # scale down a bit to fit on screen
                    width=int(preview_img.size[0] * display_scale),
                    drawing_mode="point",
                    point_display_radius=8,
                    key=f"canvas_rg_tpl_{edit_mode}_{st.session_state.layout_canvas_nonce}",
                )
                
                if canvas_result.json_data is not None:
                    objects = canvas_result.json_data.get("objects", [])
                    if objects:
                        last_point = objects[-1]
                        # adjust back scale
                        px, py = int(last_point["left"] / display_scale), int(last_point["top"] / display_scale)
                        if "Firma" in edit_mode:
                            st.session_state.rg_tpl_coords["sig"] = [px, py]
                        elif "Inicial" in edit_mode:
                            st.session_state.rg_tpl_coords["date1"] = [px, py]
                        elif "Final" in edit_mode:
                            st.session_state.rg_tpl_coords["date2"] = [px, py]
                        st.session_state.layout_canvas_nonce += 1
                        st.rerun()
                
                col_scale1, col_scale2 = st.columns(2)
                with col_scale1:
                    st.session_state.rg_tpl_coords["sig_scale"] = st.slider("Escala Firma (%)", 50, 200, st.session_state.rg_tpl_coords["sig_scale"], key="rg_scale_sig")
                with col_scale2:
                    st.session_state.rg_tpl_coords["date_scale"] = st.slider("Escala Fechas (%)", 50, 200, st.session_state.rg_tpl_coords["date_scale"], key="rg_scale_date")
            else:
                st.error("No se encontro assets/plantilla_caratula.png")

        if st.button("Crear y Guardar Perfil", key="btn_save_prof", type="primary"):
            if not new_prof_name or not new_prof_pin or len(new_prof_pin) < 4:
                st.error("Nombre y PIN valido (min 4 digitos) requeridos.")
            else:
                sig_bytes = new_prof_sig.read() if new_prof_sig else None
                if sig_bytes and rg_clean_bg:
                    sig_bytes = process_transparency(sig_bytes, threshold=rg_bg_threshold, clean=True)

                c_bytes = new_prof_custom.read() if new_prof_custom else None
                if c_bytes and rg_clean_bg:
                    c_bytes = process_transparency(c_bytes, threshold=rg_bg_threshold, clean=True)
                s2_val = "custom" if "Completo" in s_mode else "generate"
                
                tpl_coords = st.session_state.get("rg_tpl_coords")
                prof_mgr.add_profile(
                    new_prof_name, new_prof_cip, new_prof_title, sig_bytes, new_prof_pin, 
                    sello2_mode=s2_val, custom_stamp_bytes=c_bytes, tpl_coords=tpl_coords
                )
                st.success("Perfil creado exitosamente. Ve a la pestana 'Ingresar'.")
                if "rg_tpl_coords" in st.session_state:
                    del st.session_state.rg_tpl_coords
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

col_config, col_preview = st.columns([1, 2])

with col_config:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("Documento PDF")
    uploaded_pdf = st.file_uploader("Seleccionar archivo PDF", type=["pdf"], key="pdf_uploader")

    if uploaded_pdf:
        if "pdf_bytes" not in st.session_state or st.session_state.get("pdf_name") != uploaded_pdf.name:
            st.session_state.pdf_bytes = uploaded_pdf.read()
            st.session_state.pdf_name = uploaded_pdf.name
            pdf_doc, total_pages, planos_idx = st.session_state.pdf_manager.load_pdf(io.BytesIO(st.session_state.pdf_bytes))
            # REINICIAR RANGOS POR DEFECTO AL CARGAR NUEVO ARCHIVO
            cfg.config["cover_ranges"] = [{"start": "1", "end": "1"}]
            cfg.config["body_ranges"] = [{"start": "2", "end": "final"}]
            cfg.config["plano_page_settings"] = {}
            cfg.config["page_custom_coords"] = {}
            cfg.save_config()

            st.session_state.pdf_doc = pdf_doc
            st.session_state.total_pages = total_pages
            st.session_state.planos_idx = planos_idx
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    with st.expander("Fecha del Sello 1", expanded=True):
        today_str = datetime.date.today().strftime("%d/%m/%Y")
        saved_date = cfg.get("start_date", "")
        
        def set_today():
            cfg.set("start_date", today_str)
            st.session_state["start_date_input"] = today_str

        if "start_date_input" not in st.session_state:
            st.session_state["start_date_input"] = saved_date if saved_date else today_str

        start_date = st.text_input("Fecha (DD/MM/YYYY)", key="start_date_input")
        st.button("Usar Fecha de Hoy", key="btn_today", on_click=set_today)
        
        if start_date != cfg.get("start_date", ""):
            cfg.set("start_date", start_date)

    with st.expander("Sellos a Aplicar", expanded=True):
        cfg.config["apply_sello1"] = st.checkbox(
            "Aplicar Sello 1 (Caratula / V.B.)",
            value=cfg.get("apply_sello1", True),
            key="chk_s1",
        )
        cfg.config["apply_sello2"] = st.checkbox(
            "Aplicar Sello 2 (Cuerpo)",
            value=cfg.get("apply_sello2", True),
            key="chk_s2",
        )

    with st.expander("Escalas", expanded=False):
        cfg.config["cover_scale"] = st.slider("Escala Sello 1 (%)", 10, 200, int(cfg.get("cover_scale", 100) or 100), key="slider_cover_scale")
        cfg.config["body_scale"] = st.slider("Escala Sello 2 (%)", 10, 200, int(cfg.get("body_scale", 100) or 100), key="slider_body_scale")

    with st.expander("Rangos de Paginas", expanded=False):
        st.markdown("**Sello 1 (Caratula)**")
        cover_ranges_raw = cfg.get("cover_ranges", [{"start": "1", "end": "1"}]) or [{"start": "1", "end": "1"}]
        cfg.config["cover_ranges"] = st.data_editor(
            cover_ranges_raw,
            num_rows="dynamic",
            key="de_cover_ranges",
            column_config={
                "start": st.column_config.TextColumn("Desde Pag"),
                "end": st.column_config.TextColumn("Hasta Pag"),
            },
        )

        st.markdown("**Sello 2 (Cuerpo)**")
        body_ranges_raw = cfg.get("body_ranges", [{"start": "2", "end": "final"}]) or [{"start": "2", "end": "final"}]
        cfg.config["body_ranges"] = st.data_editor(
            body_ranges_raw,
            num_rows="dynamic",
            key="de_body_ranges",
            column_config={
                "start": st.column_config.TextColumn("Desde Pag"),
                "end": st.column_config.TextColumn("Hasta Pag"),
            },
        )
        cfg.config["body_exceptions"] = st.text_input(
            "Excepciones Sello 2 (paginas a excluir)",
            value=cfg.get("body_exceptions", ""),
            help="Ej: 3, 5, 10",
            key="body_exc",
        )

    cfg.save_config()

with col_preview:
    if uploaded_pdf and "pdf_doc" in st.session_state:
        st.subheader("Previsualizacion")

        cp1, cp2, cp3 = st.columns([1, 2, 1])
        with cp1:
            zoom_level = st.selectbox("Zoom", [0.5, 0.8, 1.0, 1.2, 1.5, 2.0], index=2, key="zoom_select")
        with cp2:
            page_num = st.number_input(
                "Navegador de paginas:",
                min_value=1,
                max_value=st.session_state.total_pages,
                value=1,
                step=1,
                help="Escribe el numero y presiona Enter para saltar directamente.",
                key="page_nav",
            )
        with cp3:
            modo_sello = st.radio("Posicionar:", ["Sello 1", "Sello 2"], horizontal=True, key="stamp_mode")

        page_idx = page_num - 1
        raw_page_img = st.session_state.pdf_manager.get_page_image(st.session_state.pdf_doc, page_idx, zoom=zoom_level)
        
        # --- PREVENCION DE HOJAS EN BLANCO (DIAGNOSTICO Y LIMITADOR DE MEMORIA) ---
        if raw_page_img is None:
            st.error(f"Error critico: PyMuPDF devolvio una imagen nula para la pagina {page_idx+1}.")
        else:
            print(f"[DEBUG RENDERING] Pagina {page_idx+1} | Zoom: {zoom_level} | Formato orig: {raw_page_img.mode} | Tamano orig: {raw_page_img.size}")
            
        MAX_CANVAS_DIM = 900
        render_scale = 1.0
        page_img = raw_page_img
        if raw_page_img:
            if raw_page_img.size[0] > MAX_CANVAS_DIM or raw_page_img.size[1] > MAX_CANVAS_DIM:
                ratio_w = MAX_CANVAS_DIM / float(raw_page_img.size[0])
                ratio_h = MAX_CANVAS_DIM / float(raw_page_img.size[1])
                render_scale = min(ratio_w, ratio_h)
                new_w = int(raw_page_img.size[0] * render_scale)
                new_h = int(raw_page_img.size[1] * render_scale)
                page_img = raw_page_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        plano_page_settings = cfg.get("plano_page_settings", {}) or {}
        current_page_settings = plano_page_settings.get(str(page_idx), {}) or {}
        is_plano = bool(current_page_settings.get("is_plano", False))

        st.markdown("**Ajustes de la pagina actual**")
        plano_col1, plano_col2 = st.columns(2)
        with plano_col1:
            ui_is_plano = st.checkbox(
                "Tratar esta pagina como Plano",
                value=is_plano,
                key=f"plano_chk_{page_idx}",
                help="El Sello Plano usara la imagen de Sello 1, pero anulara el Sello 2 (Cuerpo) en esta pagina.",
            )
        with plano_col2:
            ui_page_scale = st.slider(
                "Escala de Sello Plano (%)",
                10, 200, 
                int(current_page_settings.get("page_scale", cfg.get("cover_scale", 100))),
                disabled=not ui_is_plano,
                key=f"plano_scale_{page_idx}"
            )
            
        if ui_is_plano != is_plano or (ui_is_plano and ui_page_scale != current_page_settings.get("page_scale")):
            current_page_settings["is_plano"] = ui_is_plano
            if ui_is_plano:
                current_page_settings["page_scale"] = ui_page_scale
                current_page_settings["apply_sello2"] = False
                current_page_settings["apply_sello1"] = True
            plano_page_settings[str(page_idx)] = current_page_settings
            cfg.config["plano_page_settings"] = plano_page_settings
            cfg.save_config()
            st.rerun()

        if page_img:
            if is_plano:
                st.warning("Esta pagina esta marcada como **PLANO**. El Sello 2 ha sido omitido.")
            else:
                st.info(f"Haz clic en la imagen para posicionar el **{modo_sello}**")

            draw_preview = ImageDraw.Draw(page_img)
            f_coords = None
            f_color = (88, 166, 255, 60)

            if "1" in modo_sello:
                if is_plano and current_page_settings.get("cover_coords"):
                    f_coords = current_page_settings["cover_coords"]
                    st.caption("Usando posicion especifica del Sello Plano para esta pagina.")
                else:
                    f_coords = cfg.get("cover_coords")
                
                c_scale = current_page_settings.get("page_scale", cfg.get("cover_scale", 100)) if is_plano else cfg.get("cover_scale", 100)
                f_size = (
                    624 * 0.35 * (c_scale / 100.0),
                    400 * 0.35 * (c_scale / 100.0),
                )
            else:
                if is_plano and current_page_settings.get("body_coords"):
                    f_coords = current_page_settings["body_coords"]
                    st.caption("Usando posicion especifica para esta pagina.")
                else:
                    page_custom_coords = cfg.get("page_custom_coords", {})
                    if str(page_idx) in page_custom_coords:
                        f_coords = page_custom_coords[str(page_idx)]
                        st.caption("Usando posicion especifica para esta pagina.")
                    else:
                        f_coords = cfg.get("body_coords")
                f_color = (247, 120, 186, 60)
                f_size = get_body_preview_size(cfg)

            if f_coords:
                fx, fy = (f_coords[0] * zoom_level) * render_scale, (f_coords[1] * zoom_level) * render_scale
                fw, fh = (f_size[0] * zoom_level) * render_scale, (f_size[1] * zoom_level) * render_scale
                draw_preview.rectangle([fx, fy, fx + fw, fy + fh], fill=f_color, outline=f_color[:3] + (200,), width=2)
                st.caption(
                    f"Huella del sello: {int(f_size[0])}x{int(f_size[1])} px "
                    f"(aprox. {int(f_size[0] * 25.4 / 72)}x{int(f_size[1] * 25.4 / 72)} mm)"
                )

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
                key=f"canvas_main_{modo_sello}_{page_num}_{zoom_level}_{st.session_state.canvas_nonce}",
            )

            if canvas_result.json_data is not None:
                objects = canvas_result.json_data.get("objects", [])
                if objects:
                    last_point = objects[-1]
                    real_x = (last_point["left"] / render_scale) / zoom_level
                    real_y = (last_point["top"] / render_scale) / zoom_level
                    if "1" in modo_sello:
                        if is_plano:
                            plano_page_settings = cfg.get("plano_page_settings", {}) or {}
                            current_page_settings = plano_page_settings.get(str(page_idx), {}) or {}
                            current_page_settings["cover_coords"] = [real_x, real_y]
                            plano_page_settings[str(page_idx)] = current_page_settings
                            cfg.config["plano_page_settings"] = plano_page_settings
                        else:
                            cfg.config["cover_coords"] = [real_x, real_y]
                    else:
                        if is_plano:
                            plano_page_settings = cfg.get("plano_page_settings", {}) or {}
                            current_page_settings = plano_page_settings.get(str(page_idx), {}) or {}
                            current_page_settings["body_coords"] = [real_x, real_y]
                            plano_page_settings[str(page_idx)] = current_page_settings
                            cfg.config["plano_page_settings"] = plano_page_settings
                        else:
                            cfg.config["body_coords"] = [real_x, real_y]
                    cfg.save_config()
                    st.session_state.canvas_nonce += 1
                    st.session_state.last_saved_coords = (int(real_x), int(real_y))
                    st.rerun()

        st.markdown("")
        if st.button("Generar PDF Firmado", type="primary", key="btn_generate"):
            if "signature_bytes" not in st.session_state and cfg.get("sello2_mode") != "custom":
                st.error("Debes subir tu firma digital primero.")
            else:
                with st.status("Procesando PDF...", expanded=True) as status:
                    tmp_sig_path = None
                    try:
                        if "signature_bytes" in st.session_state:
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_sig:
                                tmp_sig.write(st.session_state.signature_bytes)
                                tmp_sig_path = tmp_sig.name

                        base_path = os.path.dirname(os.path.abspath(__file__))
                        tpl_path = os.path.join(base_path, "assets", "plantilla_caratula.png")
                        layout_cfg = {
                            "date1": cfg.get("tpl_date1_coords"),
                            "date2": cfg.get("tpl_date2_coords"),
                            "sig": cfg.get("tpl_sig_coords"),
                            "date_scale": cfg.get("tpl_date_scale", 100),
                            "sig_scale": cfg.get("tpl_sig_scale", 100),
                        }

                        st.write("Generando sellos...")

                        cover_img = None
                        if cfg.get("apply_sello1", True):
                            if not os.path.exists(tpl_path):
                                st.warning(f"Plantilla de caratula no encontrada en: {tpl_path}")
                            else:
                                cover_img = st.session_state.stamp_engine.generate_cover_stamp(
                                    tpl_path,
                                    tmp_sig_path,
                                    cfg.get("start_date", ""),
                                    layout_coords=layout_cfg,
                                )

                        body_img = None
                        if cfg.get("apply_sello2", True):
                            if cfg.get("sello2_mode") == "custom" and "custom_stamp_bytes" in st.session_state:
                                body_img = Image.open(io.BytesIO(st.session_state.custom_stamp_bytes)).convert("RGBA")
                            elif tmp_sig_path:
                                body_img = st.session_state.stamp_engine.generate_body_stamp(
                                    tmp_sig_path,
                                    cfg.get("engineer_name", ""),
                                    cfg.get("cip_number", ""),
                                    cfg.get("engineer_type", "Ingeniero Electricista"),
                                )

                        st.write("Ensamblando documento...")

                        fresh_doc, _, _ = st.session_state.pdf_manager.load_pdf(io.BytesIO(st.session_state.pdf_bytes))
                        out_buffer = io.BytesIO()
                        success, msg = st.session_state.pdf_manager.process_and_save(
                            fresh_doc,
                            cover_img,
                            body_img,
                            cfg.config,
                            out_buffer,
                        )

                        if success:
                            status.update(label="PDF generado con exito", state="complete")
                            st.session_state.pdf_ready_data = out_buffer.getvalue()
                            st.session_state.pdf_ready_name = os.path.splitext(st.session_state.pdf_name)[0] + "_firmado.pdf"
                            st.rerun()
                        else:
                            st.error(f"Error: {msg}")
                    except Exception as e:
                        st.error(f"Error critico: {e}")
                    finally:
                        if tmp_sig_path and os.path.exists(tmp_sig_path):
                            os.remove(tmp_sig_path)
    else:
        st.markdown(
            """
        <div class="glass-card" style="text-align:center; padding: 4rem 2rem;">
            <h2 style="color: #58a6ff !important;">Sube un PDF para comenzar</h2>
            <p style="color: #8b949e; font-size: 1.1rem;">
                Arrastra o selecciona tu documento en el panel izquierdo.<br>
                Luego posiciona tus sellos con un clic.
            </p>
        </div>
        """,
            unsafe_allow_html=True,
        )

if st.session_state.pdf_ready_data:
    st.divider()
    st.success(f"Documento listo: {st.session_state.pdf_ready_name}")
    st.download_button(
        label="Descargar PDF Firmado",
        data=st.session_state.pdf_ready_data,
        file_name=st.session_state.pdf_ready_name,
        mime="application/pdf",
        key="persistent_download_btn"
    )
    if st.button("Limpiar Generacion", key="btn_clear_pdf"):
        st.session_state.pdf_ready_data = None
        st.session_state.pdf_ready_name = ""
        st.rerun()

if "last_saved_coords" in st.session_state:
    x, y = st.session_state.last_saved_coords
    st.success(f"Coordenadas guardadas: **X={x}, Y={y}**")
    del st.session_state.last_saved_coords

st.markdown(
    '<div class="footer-text">(c) L.Navarrete · Sistema de Aprobacion de Factibilidad · Powered by Streamlit</div>',
    unsafe_allow_html=True,
)

