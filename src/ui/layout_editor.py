import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import os

class LayoutEditorWindow(ctk.CTkToplevel):
    def __init__(self, parent, config_manager, base_template):
        super().__init__(parent)
        self.config = config_manager
        self.base_template = base_template
        
        self.title('Editar Coordenadas Internas (Sello 1)')
        self.geometry('800x600')
        self.attributes('-topmost', True)
        
        self.temp_coords = {
            'date1': self.config.get('tpl_date1_coords'),
            'date2': self.config.get('tpl_date2_coords'),
            'sig': self.config.get('tpl_sig_coords')
        }
        self.markers = {}
        self.setup_ui()

    def setup_ui(self):
        lbl_inst = ctk.CTkLabel(self, text='Doble Clic directo en la imagen para capturar la posición del elemento seleccionado:')
        lbl_inst.pack(pady=10)
        
        self.current_mode = tk.StringVar(value='date1')
        frame_radio = ctk.CTkFrame(self, fg_color='transparent')
        frame_radio.pack(pady=5)
        
        ctk.CTkRadioButton(frame_radio, text='Fecha Inicio', variable=self.current_mode, value='date1').pack(side='left', padx=10)
        ctk.CTkRadioButton(frame_radio, text='Fecha Fin', variable=self.current_mode, value='date2').pack(side='left', padx=10)
        ctk.CTkRadioButton(frame_radio, text='Firma', variable=self.current_mode, value='sig').pack(side='left', padx=10)
        
        frame_scales = ctk.CTkFrame(self, fg_color='transparent')
        frame_scales.pack(pady=5)
        
        ctk.CTkLabel(frame_scales, text='Escala Textos (%):').pack(side='left', padx=5)
        self.entry_date_scale = ctk.CTkEntry(frame_scales, width=50)
        self.entry_date_scale.insert(0, str(self.config.get('tpl_date_scale') or 100))
        self.entry_date_scale.pack(side='left', padx=5)
        
        ctk.CTkLabel(frame_scales, text='Escala Firma (%):').pack(side='left', padx=(15, 5))
        self.entry_sig_scale = ctk.CTkEntry(frame_scales, width=50)
        self.entry_sig_scale.insert(0, str(self.config.get('tpl_sig_scale') or 100))
        self.entry_sig_scale.pack(side='left', padx=5)
        
        canvas_frame = ctk.CTkScrollableFrame(self)
        canvas_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        self.img_pil = Image.open(self.base_template)
        self.tk_img = ImageTk.PhotoImage(self.img_pil)
        
        self.cv = tk.Canvas(canvas_frame, width=self.img_pil.width, height=self.img_pil.height, bg='gray')
        self.cv.pack(expand=True)
        self.cv.create_image(0, 0, anchor='nw', image=self.tk_img)
        
        self.draw_markers()
        
        self.cv.bind('<Double-Button-1>', self.on_click)
        self.entry_date_scale.bind('<KeyRelease>', self.draw_markers)
        self.entry_sig_scale.bind('<KeyRelease>', self.draw_markers)
        
        btn_save = ctk.CTkButton(self, text='Guardar Coordenadas', fg_color='blue', command=self.save_and_close)
        btn_save.pack(pady=10)

    def draw_markers(self, event=None):
        for m in list(self.markers.values()):
            self.cv.delete(m)
        self.markers.clear()
        
        try:
            d_scale = int(self.entry_date_scale.get() or 100)
        except:
            d_scale = 100
            
        try:
            s_scale = int(self.entry_sig_scale.get() or 100)
        except:
            s_scale = 100
            
        font_size = int(self.img_pil.height * 0.08 * d_scale / 100.0)
        if font_size < 1:
            font_size = 12
            
        sig_w = int(self.img_pil.width * 0.35 * s_scale / 100.0)
        sig_h = int(sig_w * 0.4)
        
        for key, val in self.temp_coords.items():
            if val and isinstance(val, (list, tuple)) and len(val) >= 2:
                x, y = val[0], val[1]
                if key in ('date1', 'date2'):
                    color = 'red' if key == 'date1' else 'blue'
                    m_text = self.cv.create_text(x, y, text='DD/MM/YYYY', anchor='nw', fill=color, font=('Arial', font_size, 'bold'))
                    bbox = self.cv.bbox(m_text)
                    if bbox:
                        m_bg = self.cv.create_rectangle(bbox, outline=color, width=2, dash=(4, 4))
                        self.markers[f"{key}_bg"] = m_bg
                    self.markers[key] = m_text
                else:
                    color = 'green'
                    sig_w_calc = sig_w
                    sig_h_calc = sig_h
                    sig_txt = 'ÁREA FIRMA'
                    
                    try:
                        s_path = self.config.get('signature_path')
                        if s_path and os.path.exists(s_path):
                            tmp_s = Image.open(s_path)
                            r = sig_w / float(tmp_s.size[0])
                            sig_h_calc = int(float(tmp_s.size[1]) * r)
                            sig_txt = f"ÁREA FIRMA ({tmp_s.size[0]}x{tmp_s.size[1]})"
                    except:
                        pass
                        
                    m_rect = self.cv.create_rectangle(x, y, x + sig_w_calc, y + sig_h_calc, outline=color, width=2, dash=(4, 4))
                    m_text = self.cv.create_text(x + 5, y + 5, text=sig_txt, anchor='nw', fill=color, font=('Arial', max(10, int(font_size / 2)), 'bold'))
                    self.markers[key] = m_rect
                    self.markers[f"{key}_text"] = m_text

    def on_click(self, e):
        mode = self.current_mode.get()
        self.temp_coords[mode] = [e.x, e.y]
        self.draw_markers()

    def save_and_close(self):
        self.config.set('tpl_date1_coords', self.temp_coords['date1'])
        self.config.set('tpl_date2_coords', self.temp_coords['date2'])
        self.config.set('tpl_sig_coords', self.temp_coords['sig'])
        try:
            self.config.set('tpl_date_scale', int(self.entry_date_scale.get() or 100))
            self.config.set('tpl_sig_scale', int(self.entry_sig_scale.get() or 100))
        except:
            pass
            
        self.destroy()
        
        if hasattr(self.master, 'attributes'):
            self.master.attributes('-topmost', False)
        messagebox.showinfo('Guardado', 'Coordenadas guardadas correctamente.')
        if hasattr(self.master, 'attributes'):
            self.master.attributes('-topmost', True)
