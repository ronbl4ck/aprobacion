import fitz
import io
import os
from PIL import Image

class PDFManager:
    def __init__(self):
        pass

    def load_pdf(self, pdf_input):
        """
        Carga el PDF y devuelve el objeto documento y el número de páginas.
        Soporta ruta (str) o stream (BytesIO).
        """
        try:
            if isinstance(pdf_input, (str, bytes, os.PathLike)):
                doc = fitz.open(pdf_input)
            else:
                # Caso Stream (Streamlit)
                doc = fitz.open(stream=pdf_input, filetype="pdf")
            return doc, len(doc)
        except Exception as e:
            print(f"Error cargando PDF: {e}")
            return None, 0

    def get_page_image(self, doc, page_num, zoom=1.0):
        """
        Obtiene la imagen de una página específica para usar en CustomTkinter previsualización.
        page_num es 0-indexed en PyMuPDF.
        Devuelve un objeto PIL.Image
        """
        try:
            page = doc[page_num]
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            return img
        except Exception as e:
            print(f"Error generando imagen de página: {e}")
            return None

    def pil_to_bytes(self, pil_image):
        """Convierte PIL Image a bytes para insertarlo en PDF. """
        img_byte_arr = io.BytesIO()
        pil_image.save(img_byte_arr, format='PNG')
        return img_byte_arr.getvalue()

    def process_and_save(self, doc, cover_img, body_img, config_data, output_target):
        """
        Aplica los sellos en el PDF original.
        config_data = dict con {
            cover_page: <int>,
            body_page_start: <int>,
            body_page_end: <int o 'final'>,
            cover_coords: (x, y),
            body_coords: (x, y)
        }
        """
        cover_bytes = self.pil_to_bytes(cover_img) if cover_img else None
        body_bytes = self.pil_to_bytes(body_img) if body_img else None

        total_pages = len(doc)
        body_ranges = config_data.get('body_ranges', [])
        cover_ranges = config_data.get('cover_ranges', [{'start': '1', 'end': '1'}])
        
        cover_scale = int(config_data.get('cover_scale', 100))
        body_scale = int(config_data.get('body_scale', 100))

        body_exceptions_str = config_data.get('body_exceptions', "")
        exceptions = []
        if body_exceptions_str:
            for x in body_exceptions_str.split(','):
                exceptions.append(int(x.strip()) - 1)

        def is_in_ranges(page_idx, ranges_list):
            if not ranges_list:
                return False
            for rng in ranges_list:
                start = int(rng.get('start', 1)) - 1
                end_str = str(rng.get('end', 'final')).lower()
                if end_str == 'final' or not end_str.isdigit():
                    end = total_pages - 1
                else:
                    end = int(end_str) - 1

                if start <= page_idx <= end:
                    return True
            return False

        try:
            for i in range(total_pages):
                page = doc[i]

                if cover_bytes is not None and is_in_ranges(i, cover_ranges):
                    BASE_FACTOR = 0.35
                    x, y = config_data.get('cover_coords', (0, 0))
                    orig_w, orig_h = cover_img.size
                    w = int(orig_w * BASE_FACTOR * (cover_scale / 100.0))
                    h = int(orig_h * BASE_FACTOR * (cover_scale / 100.0))
                    rect = fitz.Rect(x, y, x + w, y + h)
                    page.insert_image(rect, stream=cover_bytes, keep_proportion=True)

                if body_bytes is not None and is_in_ranges(i, body_ranges) and i not in exceptions:
                    BASE_FACTOR = 0.35
                    x, y = config_data.get('body_coords', (0, 0))
                    orig_w, orig_h = body_img.size
                    w = int(orig_w * BASE_FACTOR * (body_scale / 100.0))
                    h = int(orig_h * BASE_FACTOR * (body_scale / 100.0))
                    rect = fitz.Rect(x, y, x + w, y + h)
                    page.insert_image(rect, stream=body_bytes, keep_proportion=True)

            if isinstance(output_target, str):
                doc.save(output_target)
            else:
                # Caso BytesIO (Streamlit)
                doc.save(output_target)
            
            return True, "El PDF se guardó correctamente."
        except Exception as e:
            return False, f"Error al procesar y guardar: {e}"
