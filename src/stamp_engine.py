import os
import re
from PIL import Image, ImageDraw, ImageFont
from dateutil.relativedelta import relativedelta
from datetime import datetime

class StampEngine:
    def __init__(self):
        pass

    def _get_font(self, size, bold=False):
        # Intentar cargar desde el proyecto local (Portabilidad para Streamlit)
        try:
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if bold:
                font_path = os.path.join(base_path, 'assets', 'fonts', 'arialbd.ttf')
            else:
                font_path = os.path.join(base_path, 'assets', 'fonts', 'arial.ttf')
            
            if os.path.exists(font_path):
                return ImageFont.truetype(font_path, size)
        except Exception:
            pass

        # Fallback a Windows (Local Dev)
        if bold:
            font_path = 'C:/Windows/Fonts/arialbd.ttf'
        else:
            font_path = 'C:/Windows/Fonts/arial.ttf'
        
        try:
            return ImageFont.truetype(font_path, size)
        except IOError:
            return ImageFont.load_default()

    def generate_cover_stamp(self, base_img_path, signature_path, start_date_str, layout_coords=None):
        """
        Sello 1: Carátula
        Combina la base_img_path con la signature_path, y dibuja fechas de inicio y fin.
        """
        if not os.path.exists(base_img_path):
            raise FileNotFoundError(f"No se encontró la plantilla base: {base_img_path}")

        base_img = Image.open(base_img_path).convert('RGBA')
        draw = ImageDraw.Draw(base_img)
        w, h = base_img.size

        end_date_str = ""
        try:
            start_date = datetime.strptime(start_date_str, '%d/%m/%Y')
            end_date = start_date + relativedelta(years=2)
            end_date_str = end_date.strftime('%d/%m/%Y')
        except ValueError:
            try:
                match = re.search(r'\d{4}', start_date_str)
                if match:
                    year = int(match.group())
                    end_date_str = start_date_str.replace(str(year), str(year + 2))
                else:
                    end_date_str = start_date_str + " + 2 años"
            except:
                end_date_str = ""

        if layout_coords is None:
            layout_coords = {}

        date_scale = layout_coords.get('date_scale')
        if not date_scale:
            date_scale = 100

        sig_scale = layout_coords.get('sig_scale')
        if not sig_scale:
            sig_scale = 100

        fecha_ini_coords = layout_coords.get('date1')
        if not fecha_ini_coords:
            fecha_ini_coords = (int(w * 0.55), int(h * 0.53))

        fecha_fin_coords = layout_coords.get('date2')
        if not fecha_fin_coords:
            fecha_fin_coords = (int(w * 0.55), int(h * 0.69))

        font_size = int((h * 0.08) * (date_scale / 100.0))
        font = self._get_font(font_size, bold=True)

        draw.text(fecha_ini_coords, start_date_str, fill='black', font=font)
        draw.text(fecha_fin_coords, end_date_str, fill='black', font=font)

        if signature_path and os.path.exists(signature_path):
            try:
                signature = Image.open(signature_path).convert('RGBA')
                max_width = int(w * 0.35 * (sig_scale / 100.0))
                ratio = max_width / float(signature.size[0])
                new_height = int(float(signature.size[1]) * float(ratio))
                signature = signature.resize((max_width, new_height), Image.LANCZOS)
                
                sig_coords = layout_coords.get('sig')
                if not sig_coords:
                    sig_coords = (int(w * 0.1), int(h * 0.7))
                
                base_img.paste(signature, sig_coords, mask=signature)
            except Exception as e:
                print(f"Error procesando firma para carátula: {e}")

        return base_img

    def generate_body_stamp(self, signature_path, name, cip, tipo, canvas_height=500):
        """
        Sello 2: Resto de hojas (Composición Libre)
        """
        canvas_width = 800
        stamp = Image.new('RGBA', (canvas_width, canvas_height), (255, 255, 255, 0))
        draw = ImageDraw.Draw(stamp)

        font_name = self._get_font(40, bold=True)
        font_title = self._get_font(35, bold=True)
        font_cip = self._get_font(35, bold=True)

        y_offset = 20

        if signature_path and os.path.exists(signature_path):
            try:
                signature = Image.open(signature_path).convert('RGBA')
                max_width = 400
                ratio = max_width / float(signature.size[0])
                new_height = int(float(signature.size[1]) * float(ratio))
                signature = signature.resize((max_width, new_height), Image.LANCZOS)
                
                x_pos = (canvas_width - signature.size[0]) // 2
                stamp.paste(signature, (x_pos, y_offset), mask=signature)
                y_offset += signature.size[1] + 20
            except Exception as e:
                print(f"Error cargando firma Sello 2: {e}")
                y_offset += 50

        def draw_centered_text(text, font, y):
            bbox = draw.textbbox((0, 0), text, font=font)
            w = bbox[2] - bbox[0]
            x = (canvas_width - w) // 2
            draw.text((x, y), text, fill='black', font=font)
            return bbox[3] - bbox[1] + 15

        if name:
            y_offset += draw_centered_text(name, font_name, y_offset)

        if tipo:
            y_offset += draw_centered_text(tipo, font_title, y_offset)
        else:
            y_offset += draw_centered_text('Ingeniero Electricista', font_title, y_offset)

        if cip:
            cip_text = f"N° CIP {cip}"
            y_offset += draw_centered_text(cip_text, font_cip, y_offset)

        bbox = stamp.getbbox()
        if bbox:
            stamp = stamp.crop(bbox)

        return stamp

    def get_body_stamp_size(self, signature_path, name, cip, tipo):
        """
        Versión optimizada que simula el cálculo matemático del ancho x alto
        para el Sello 2 sin renderizar gráficos en Pillow.
        Ahorra sobrecarga de CPU en GUI Canvas previsualizaciones.
        """
        canvas_width = 800
        y_offset = 20
        max_content_width = 0

        if signature_path and os.path.exists(signature_path):
            try:
                with Image.open(signature_path) as tmp_sig:
                    sig_w, sig_h = tmp_sig.size
                max_width = 400
                ratio = max_width / float(sig_w)
                new_height = int(float(sig_h) * ratio)
                y_offset += new_height + 20
                max_content_width = max(max_content_width, max_width)
            except:
                y_offset += 50

        font_name = self._get_font(40, bold=True)
        font_title = self._get_font(35, bold=True)
        font_cip = self._get_font(35, bold=True)

        def get_text_size(text, font):
            if hasattr(font, 'getbbox'):
                bbox = font.getbbox(text)
                return (bbox[2] - bbox[0], bbox[3] - bbox[1])
            return font.getsize(text)

        if name:
            tw, th = get_text_size(name, font_name)
            max_content_width = max(max_content_width, tw)
            y_offset += th + 15

        if tipo:
            tw, th = get_text_size(tipo, font_title)
        else:
            tw, th = get_text_size('Ingeniero Electricista', font_title)
        
        max_content_width = max(max_content_width, tw)
        y_offset += th + 15

        if cip:
            tw, th = get_text_size(f"N° CIP {cip}", font_cip)
            max_content_width = max(max_content_width, tw)
            y_offset += th + 15

        final_height = y_offset
        return max_content_width, final_height
