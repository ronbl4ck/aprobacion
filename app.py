import streamlit as st
import os
import io
import datetime
from PIL import Image
from src.pdf_manager import PDFManager
from src.stamp_engine import StampEngine

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Autofirma PDF | Sistema Aprobación",
    page_icon="🖋️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- ESTILOS PERSONALIZADOS (PREMIUM LOOK) ---
st.markdown("""
<style>
    .main {
        background-color: #f8f9fa;
    }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
        background-color: #1a73e8;
        color: white;
        font-weight: bold;
        border: none;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #1557b0;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    .sidebar .sidebar-content {
        background-color: #ffffff;
    }
    h1, h2, h3 {
        color: #1e293b;
    }
    .stExpander {
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        background-color: white;
    }
</style>
""", unsafe_allow_html=True)

# --- INICIALIZACIÓN DE ESTADO ---
if 'pdf_manager' not in st.session_state:
    st.session_state.pdf_manager = PDFManager()
if 'stamp_engine' not in st.session_state:
    st.session_state.stamp_engine = StampEngine()
if 'config' not in st.session_state:
    st.session_state.config = {
        'engineer_name': '',
        'cip_number': '',
        'engineer_type': 'Ingeniero Electricista',
        'apply_sello1': True,
        'apply_sello2': True,
        'cover_scale': 100,
        'body_scale': 100,
        'cover_ranges': [{'start': '1', 'end': '1'}],
        'body_ranges': [{'start': '2', 'end': 'final'}],
        'body_exceptions': '',
        'start_date': datetime.date.today().strftime('%d/%m/%Y'),
        'cover_coords': [100, 100],
        'body_coords': [100, 100]
    }

# --- SIDEBAR: DATOS DEL INGENIERO ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=80)
    st.title("Configuración")
    
    st.subheader("👤 Datos del Ingeniero")
    st.session_state.config['engineer_name'] = st.text_input("Nombre Completo", value=st.session_state.config['engineer_name'])
    st.session_state.config['cip_number'] = st.text_input("Número CIP", value=st.session_state.config['cip_number'])
    st.session_state.config['engineer_type'] = st.text_input("Tipo / Título", value=st.session_state.config['engineer_type'])
    
    st.divider()
    
    st.subheader("🖋️ Firma Digital")
    uploaded_sig = st.file_uploader("Subir Firma (PNG transparente)", type=["png"])
    if uploaded_sig:
        st.session_state.signature_bytes = uploaded_sig.read()
        st.success("Firma cargada")
    else:
        st.info("Sube tu firma para aplicar sellos")

# --- CUERPO PRINCIPAL ---
st.title("🖋️ Autofirma de Documentos PDF")
st.markdown("Carga tu documento y posiciona tus sellos de forma profesional.")

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("📂 Documento y Configuración")
    uploaded_pdf = st.file_uploader("Seleccionar archivo PDF", type=["pdf"])
    
    if uploaded_pdf:
        # Cargar PDF en memoria (solo una vez)
        if 'pdf_bytes' not in st.session_state or st.session_state.pdf_name != uploaded_pdf.name:
            st.session_state.pdf_bytes = uploaded_pdf.read()
            st.session_state.pdf_name = uploaded_pdf.name
            pdf_doc, total_pages = st.session_state.pdf_manager.load_pdf(io.BytesIO(st.session_state.pdf_bytes))
            st.session_state.pdf_doc = pdf_doc
            st.session_state.total_pages = total_pages
        
        st.success(f"Cargado: {st.session_state.pdf_name} ({st.session_state.total_pages} págs)")
        
        st.divider()
        
        with st.expander("⚙️ Parámetros Generales", expanded=True):
            st.session_state.config['start_date'] = st.text_input("Fecha (Sello 1)", value=st.session_state.config['start_date'])
            st.session_state.config['body_exceptions'] = st.text_input("Excepciones Sello 2 (Págs)", value=st.session_state.config['body_exceptions'], help="Ej: 3, 5, 10-12")

        with st.expander("📐 Escalas", expanded=False):
            st.session_state.config['cover_scale'] = st.slider("Escala Sello 1 (%)", 10, 200, st.session_state.config['cover_scale'])
            st.session_state.config['body_scale'] = st.slider("Escala Sello 2 (%)", 10, 200, st.session_state.config['body_scale'])
            
        with st.expander("📑 Configurar Rangos de Páginas", expanded=False):
            st.write("**Sello 1 (Carátula)**")
            st.session_state.config['cover_ranges'] = st.data_editor(st.session_state.config['cover_ranges'], num_rows="dynamic", key="cv_rng")
            
            st.write("**Sello 2 (Cuerpo)**")
            st.session_state.config['body_ranges'] = st.data_editor(st.session_state.config['body_ranges'], num_rows="dynamic", key="bd_rng")

with col2:
    if uploaded_pdf and 'pdf_doc' in st.session_state:
        st.subheader("👁️ Previsualización y Sellado")
        
        # Selector de Página
        page_num = st.number_input("Página actual:", 1, st.session_state.total_pages, 1) - 1
        
        # Renderizar página
        page_img = st.session_state.pdf_manager.get_page_image(st.session_state.pdf_doc, page_num, zoom=1.5)
        
        if page_img:
            # Seleccionar modo de sellado
            modo_sello = st.radio("Modo de Posicionamiento:", ["Posicionar Sello 1", "Posicionar Sello 2"], horizontal=True)
            
            st.info(f"Haz clic en la imagen para posicionar el **{'Sello 1' if '1' in modo_sello else 'Sello 2'}**")
            
            # --- CANVAS FASE 3 ---
            from streamlit_drawable_canvas import st_canvas
            
            canvas_result = st_canvas(
                fill_color="rgba(255, 165, 0, 0.3)",
                stroke_width=2,
                stroke_color="#ff0000",
                background_image=page_img,
                update_streamlit=True,
                height=page_img.size[1],
                width=page_img.size[0],
                drawing_mode="point",
                point_display_radius=5,
                key="canvas",
            )
            
            if canvas_result.json_data is not None:
                objects = canvas_result.json_data["objects"]
                if len(objects) > 0:
                    last_point = objects[-1]
                    real_x = last_point["left"] / 1.5
                    real_y = last_point["top"] / 1.5
                    
                    if "1" in modo_sello:
                        st.session_state.config['cover_coords'] = [real_x, real_y]
                    else:
                        st.session_state.config['body_coords'] = [real_x, real_y]
                    
                    st.success(f"Coordenadas guardadas: X={int(real_x)}, Y={int(real_y)}")

        if st.button("🚀 Generar y Descargar PDF Firmado"):
            if not uploaded_sig:
                st.error("Debes subir tu firma digital primero.")
            else:
                with st.status("Procesando PDF...", expanded=True) as status:
                    st.write("Generando sellos...")
                    
                    # Guardar firma temporalmente
                    import tempfile
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_sig:
                        tmp_sig.write(st.session_state.signature_bytes)
                        tmp_sig_path = tmp_sig.name
                    
                    try:
                        # Rutas
                        base_path = os.getcwd()
                        tpl_path = os.path.join(base_path, "assets", "plantilla_caratula.png")
                        
                        # Configuración Sellos
                        layout_cfg = {
                            "date1": (int(300 * 0.55), int(150 * 0.53)), # Default approx
                            "date2": (int(300 * 0.55), int(150 * 0.69)),
                            "sig": (int(300 * 0.1), int(150 * 0.7)),
                            "date_scale": 100,
                            "sig_scale": 100
                        }
                        
                        st.write("Ensamblando documento...")
                        cover_img = None
                        if st.session_state.config['apply_sello1']:
                            cover_img = st.session_state.stamp_engine.generate_cover_stamp(
                                tpl_path, tmp_sig_path, st.session_state.config['start_date'], layout_coords=layout_cfg
                            )
                        
                        body_img = None
                        if st.session_state.config['apply_sello2']:
                            body_img = st.session_state.stamp_engine.generate_body_stamp(
                                tmp_sig_path, 
                                st.session_state.config['engineer_name'], 
                                st.session_state.config['cip_number'], 
                                st.session_state.config['engineer_type']
                            )
                        
                        # Procesar PDF
                        out_pdf_buffer = io.BytesIO()
                        success, msg = st.session_state.pdf_manager.process_and_save(
                            st.session_state.pdf_doc, 
                            cover_img, 
                            body_img, 
                            st.session_state.config, 
                            out_pdf_buffer
                        )
                        
                        if success:
                            status.update(label="¡PDF Generado con éxito!", state="complete")
                            st.download_button(
                                label="⬇️ Descargar PDF Firmado",
                                data=out_pdf_buffer.getvalue(),
                                file_name=f"{os.path.splitext(uploaded_pdf.name)[0]}_firmado.pdf",
                                mime="application/pdf"
                            )
                        else:
                            st.error(msg)
                            
                    except Exception as e:
                        st.error(f"Error crítico: {e}")
                    finally:
                        if os.path.exists(tmp_sig_path):
                            os.remove(tmp_sig_path)

    else:
        st.info("Sube un PDF para comenzar con la previsualización.")

st.markdown("---")
st.caption("© L.Navarrete | Herramienta de Aprobación de Proyectos")
