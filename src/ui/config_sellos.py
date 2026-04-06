import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
import os
from datetime import datetime

class RangeEditorFrame(ctk.CTkFrame):
    def __init__(self, parent, show_exceptions=False):
        super().__init__(parent, fg_color='transparent')
        self.show_exceptions = show_exceptions
        self.lista_entradas_rangos = []
        
        self.frame_list = ctk.CTkFrame(self, fg_color='transparent')
        self.frame_list.pack(fill='x', pady=2)
        
        btn_add = ctk.CTkButton(self, text='+ Nuevo Rango', fg_color='transparent', border_width=1, command=self.add_rango)
        btn_add.pack(pady=5, anchor='w')
        
        if self.show_exceptions:
            ctk.CTkLabel(self, text='Páginas Excepción (Ej. 2, 5, 7-9):').pack(anchor='w', pady=(10, 0))
            self.entry_exceptions = ctk.CTkEntry(self, placeholder_text='Num. de páginas separadas por comas')
            self.entry_exceptions.pack(fill='x', pady=2)
            
    def add_rango(self, def_start='', def_end=''):
        f_rng = ctk.CTkFrame(self.frame_list, fg_color='transparent')
        f_rng.pack(fill='x', pady=2)
        
        ctk.CTkLabel(f_rng, text='De pág:').grid(row=0, column=0, sticky='w', pady=2)
        entry_s = ctk.CTkEntry(f_rng, width=45)
        entry_s.grid(row=0, column=1, sticky='w', padx=2, pady=2)
        if def_start:
            entry_s.insert(0, def_start)
            
        ctk.CTkLabel(f_rng, text='a:').grid(row=0, column=2, sticky='w', padx=2, pady=2)
        entry_e = ctk.CTkEntry(f_rng, width=45, placeholder_text='final')
        entry_e.grid(row=0, column=3, sticky='w', padx=2, pady=2)
        if def_end:
            entry_e.insert(0, def_end)
            
        val_tuple = (entry_s, entry_e)
        
        btn_del = ctk.CTkButton(
            f_rng, text='X', width=25, fg_color='red', hover_color='darkred',
            command=lambda f=f_rng, e=val_tuple: self.del_rango(f, e)
        )
        btn_del.grid(row=0, column=4, padx=(5, 0))
        
        self.lista_entradas_rangos.append(val_tuple)

    def del_rango(self, frame, obj_tuple):
        if obj_tuple in self.lista_entradas_rangos:
            self.lista_entradas_rangos.remove(obj_tuple)
        frame.destroy()

    def get_ranges(self):
        ranges = []
        for e_start, e_end in self.lista_entradas_rangos:
            r_start = e_start.get().strip()
            r_end = e_end.get().strip()
            if r_start:
                ranges.append({'start': r_start, 'end': r_end if r_end else 'final'})
        return ranges

    def get_exceptions(self):
        if self.show_exceptions:
            return self.entry_exceptions.get().strip()
        return ''

    def set_exceptions(self, text):
        if self.show_exceptions and text:
            self.entry_exceptions.insert(0, text)

class ConfigSello1Window(ctk.CTkToplevel):
    def __init__(self, parent, config_manager, on_close_callback=None):
        super().__init__(parent)
        self.title('Configuración Sello 1 (Carátula)')
        self.geometry('450x550')
        self.main_tab = parent
        self.config_manager = config_manager
        self.on_close_callback = on_close_callback
        
        self.attributes('-topmost', True)
        self.protocol('WM_DELETE_WINDOW', self.on_close)
        
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        f_top = ctk.CTkFrame(self, fg_color='transparent')
        f_top.grid(row=0, column=0, sticky='ew', padx=20, pady=10)
        
        ctk.CTkLabel(f_top, text='Escala (%):').grid(row=1, column=0, sticky='w', pady=5)
        self.entry_scale = ctk.CTkEntry(f_top, width=60)
        self.entry_scale.grid(row=1, column=1, sticky='w', padx=10, pady=5)
        
        ctk.CTkLabel(self, text='Rangos de Páginas para aplicar este sello:', font=ctk.CTkFont(weight='bold')).grid(row=1, column=0, sticky='w', padx=20, pady=(10, 0))
        
        self.range_editor = RangeEditorFrame(self, show_exceptions=False)
        self.range_editor.grid(row=2, column=0, sticky='nsew', padx=20, pady=5)
        
        self.f_firma = ctk.CTkFrame(self)
        self.f_firma.grid(row=3, column=0, sticky='ew', padx=20, pady=10)
        
        btn_load_sig = ctk.CTkButton(self.f_firma, text='Seleccionar Firma PNG', command=self.load_signature)
        btn_load_sig.pack(pady=5)
        
        self.lbl_sig_path = ctk.CTkLabel(self.f_firma, text='Sin firma', text_color='gray')
        self.lbl_sig_path.pack()
        
        btn_edit_layout = ctk.CTkButton(self.f_firma, text='Editar Layout Sello', command=self.edit_layout)
        btn_edit_layout.pack(pady=5)
        
        btn_preview = ctk.CTkButton(self.f_firma, text='👁️ Previsualizar Sello', command=self.preview_stamp)
        btn_preview.pack(pady=5)
        
        btn_save = ctk.CTkButton(self, text='Guardar y Cerrar', command=self.on_close)
        btn_save.grid(row=4, column=0, pady=10)

    def load_data(self):
        self.entry_scale.insert(0, str(self.config_manager.get('cover_scale', '100')))
        ranges = self.config_manager.get('cover_ranges', [{'start': '1', 'end': '1'}])
        
        for w in self.range_editor.frame_list.winfo_children():
            w.destroy()
        self.range_editor.lista_entradas_rangos.clear()
        
        for rng in ranges:
            self.range_editor.add_rango(rng.get('start', ''), rng.get('end', ''))
            
        sig_path = self.config_manager.get('signature_path', '')
        if sig_path and os.path.exists(sig_path):
            self.lbl_sig_path.configure(text=f"...{sig_path[-25:]}")

    def load_signature(self):
        self.attributes('-topmost', False)
        path = filedialog.askopenfilename(title='Seleccionar Firma PNG', filetypes=[('PNG transparent', '*.png')])
        self.attributes('-topmost', True)
        if path:
            self.config_manager.set('signature_path', path)
            self.lbl_sig_path.configure(text=f"...{path[-25:]}")

    def edit_layout(self):
        from src.ui.layout_editor import LayoutEditorWindow
        base_template = self.main_tab.get_resource_path('assets/plantilla_caratula.png')
        if not os.path.exists(base_template):
            self.attributes('-topmost', False)
            from tkinter import messagebox
            messagebox.showwarning('Atención', f"No se encontró la plantilla default en {base_template}.")
            self.attributes('-topmost', True)
            return
        LayoutEditorWindow(self, self.config_manager, base_template)

    def preview_stamp(self):
        try:
            val = int(self.entry_scale.get())
        except:
            val = 100
        self.config_manager.config['cover_scale'] = val
        self.main_tab.action_preview_cover_stamp_from_popup(self)

    def on_close(self):
        try:
            val = int(self.entry_scale.get())
        except:
            val = 100
        self.config_manager.config['cover_scale'] = val
        self.config_manager.config['cover_ranges'] = self.range_editor.get_ranges()
        self.config_manager.save_config()
        if self.on_close_callback:
            self.on_close_callback()
        self.destroy()

class ConfigSello2Window(ctk.CTkToplevel):
    def __init__(self, parent, config_manager, on_close_callback=None):
        super().__init__(parent)
        self.title('Configuración Sello 2 (Cuerpo)')
        self.geometry('500x600')
        self.config_manager = config_manager
        self.on_close_callback = on_close_callback
        
        self.attributes('-topmost', True)
        self.protocol('WM_DELETE_WINDOW', self.on_close)
        
        self.setup_ui()
        self.load_data()
        self.update_mode_ui()

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        f_top = ctk.CTkFrame(self, fg_color='transparent')
        f_top.grid(row=0, column=0, sticky='ew', padx=20, pady=10)
        
        self.mode_var = tk.StringVar(value=self.config_manager.get('sello2_mode', 'generate'))
        
        r1 = ctk.CTkRadioButton(f_top, text='Generar Texto (Nombre y CIP)', variable=self.mode_var, value='generate', command=self.update_mode_ui)
        r1.grid(row=0, column=0, sticky='w', pady=5, padx=5)
        
        r2 = ctk.CTkRadioButton(f_top, text='Sello Pre-Diseñado (Solo Imagen)', variable=self.mode_var, value='custom', command=self.update_mode_ui)
        r2.grid(row=1, column=0, sticky='w', pady=5, padx=5)
        
        self.f_generate = ctk.CTkFrame(f_top)
        self.f_generate.grid(row=2, column=0, columnspan=2, sticky='ew', pady=10)
        
        btn_load_sig2 = ctk.CTkButton(self.f_generate, text='Seleccionar Firma Base PNG', command=self.load_signature)
        btn_load_sig2.pack(pady=5)
        
        self.lbl_sig_path = ctk.CTkLabel(self.f_generate, text='Sin firma', text_color='gray')
        self.lbl_sig_path.pack()
        
        self.entry_name = ctk.CTkEntry(self.f_generate, placeholder_text='Nombre Completo')
        self.entry_name.pack(fill='x', padx=10, pady=5)
        
        self.entry_cip = ctk.CTkEntry(self.f_generate, placeholder_text='Número CIP')
        self.entry_cip.pack(fill='x', padx=10, pady=5)
        
        self.entry_tipo = ctk.CTkEntry(self.f_generate, placeholder_text='Tipo (Ej. Ing. Electricista)')
        self.entry_tipo.pack(fill='x', padx=10, pady=5)
        
        self.f_custom = ctk.CTkFrame(f_top)
        self.f_custom.grid(row=2, column=0, columnspan=2, sticky='ew', pady=10)
        
        btn_load_custom = ctk.CTkButton(self.f_custom, text='Cargar Imagen del Sello', command=self.load_custom_stamp)
        btn_load_custom.pack(pady=5)
        
        self.lbl_custom_path = ctk.CTkLabel(self.f_custom, text='Ningún sello cargado', text_color='gray', wraplength=400)
        self.lbl_custom_path.pack(pady=5)
        
        f_scale = ctk.CTkFrame(self, fg_color='transparent')
        f_scale.grid(row=1, column=0, sticky='ew', padx=20, pady=5)
        
        ctk.CTkLabel(f_scale, text='Escala (%):').pack(side='left', padx=5)
        self.entry_scale = ctk.CTkEntry(f_scale, width=60)
        self.entry_scale.pack(side='left', padx=5)
        
        ctk.CTkLabel(self, text='Rangos y Excepciones para Sello 2:', font=ctk.CTkFont(weight='bold')).grid(row=2, column=0, sticky='w', padx=20, pady=(10, 0))
        
        self.range_editor = RangeEditorFrame(self, show_exceptions=True)
        self.range_editor.grid(row=3, column=0, sticky='nsew', padx=20, pady=5)
        
        btn_save = ctk.CTkButton(self, text='Guardar y Cerrar', command=self.on_close)
        btn_save.grid(row=4, column=0, pady=20)

    def update_mode_ui(self):
        if self.mode_var.get() == 'generate':
            self.f_generate.grid()
            self.f_custom.grid_remove()
        else:
            self.f_generate.grid_remove()
            self.f_custom.grid()

    def load_custom_stamp(self):
        self.attributes('-topmost', False)
        path = filedialog.askopenfilename(title='Seleccionar Sello Pre-Diseñado PNG', filetypes=[('PNG transparent', '*.png')])
        self.attributes('-topmost', True)
        if path:
            self.config_manager.set('sello2_custom_path', path)
            self.lbl_custom_path.configure(text=f"...{path[-35:]}")

    def load_signature(self):
        self.attributes('-topmost', False)
        path = filedialog.askopenfilename(title='Seleccionar Firma Base PNG', filetypes=[('PNG transparent', '*.png')])
        self.attributes('-topmost', True)
        if path:
            self.config_manager.set('signature_path', path)
            self.lbl_sig_path.configure(text=f"...{path[-25:]}")

    def load_data(self):
        self.entry_name.insert(0, self.config_manager.get('engineer_name', ''))
        self.entry_cip.insert(0, self.config_manager.get('cip_number', ''))
        self.entry_tipo.insert(0, self.config_manager.get('engineer_type', 'Ingeniero Electricista'))
        
        s_path = self.config_manager.get('signature_path', '')
        if s_path and os.path.exists(s_path):
            self.lbl_sig_path.configure(text=f"...{s_path[-25:]}")
            
        c_path = self.config_manager.get('sello2_custom_path', '')
        if c_path and os.path.exists(c_path):
            self.lbl_custom_path.configure(text=f"...{c_path[-35:]}")
            
        self.entry_scale.insert(0, str(self.config_manager.get('body_scale', '100')))
        
        ranges = self.config_manager.get('body_ranges', [{'start': '2', 'end': 'final'}])
        for w in self.range_editor.frame_list.winfo_children():
            w.destroy()
        self.range_editor.lista_entradas_rangos.clear()
        
        for rng in ranges:
            self.range_editor.add_rango(rng.get('start', ''), rng.get('end', ''))
            
        self.range_editor.set_exceptions(self.config_manager.get('body_exceptions', ''))

    def on_close(self):
        self.config_manager.config['engineer_name'] = self.entry_name.get()
        self.config_manager.config['cip_number'] = self.entry_cip.get()
        self.config_manager.config['engineer_type'] = self.entry_tipo.get()
        self.config_manager.config['sello2_mode'] = self.mode_var.get()
        try:
            val = int(self.entry_scale.get())
        except:
            val = 100
        self.config_manager.config['body_scale'] = val
        
        self.config_manager.config['body_ranges'] = self.range_editor.get_ranges()
        self.config_manager.config['body_exceptions'] = self.range_editor.get_exceptions()
        
        self.config_manager.save_config()
        if self.on_close_callback:
            self.on_close_callback()
        self.destroy()
