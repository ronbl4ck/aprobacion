import customtkinter as ctk
import datetime
import json
import os
from tkinter import filedialog, messagebox
import re
from dateutil.relativedelta import relativedelta
import threading

class TabCarta(ctk.CTkFrame):
    def __init__(self, parent, config_manager, word_engine):
        super().__init__(parent, fg_color='transparent')
        self.config_manager = config_manager
        self.word_engine = word_engine
        self.ubicaciones_cache = {}
        self.ingenieros_cache = []
        self.setup_ui()
        self.setup_logic()

    def setup_logic(self):
        hoy = datetime.datetime.now()
        fecha_str = f"{hoy.day:02d}/{hoy.month:02d}/{hoy.year}"
        self.entry_fecha_sys.insert(0, fecha_str)
        self.load_databases()
        self.entry_fecha_sys.bind('<KeyRelease>', lambda e: self.on_date_typing(e, self.entry_fecha_sys))
        self.entry_fecha_carta.bind('<KeyRelease>', lambda e: self.on_date_typing(e, self.entry_fecha_carta))
        
        def on_inicio_change(e):
            self.on_date_typing(e, self.entry_fecha_inicio)
            self.on_fecha_inicio_change(e)
            
        self.entry_fecha_inicio.bind('<KeyRelease>', on_inicio_change)

    def load_databases(self):
        ubi_path = 'ubicaciones.json'
        if os.path.exists(ubi_path):
            try:
                with open(ubi_path, 'r', encoding='utf-8') as f:
                    self.ubicaciones_cache = json.load(f)
            except Exception:
                pass
        
        if self.ubicaciones_cache:
            dists = list(self.ubicaciones_cache.keys())
            self.combo_distrito.configure(values=dists)
        else:
            self.combo_distrito.configure(values=['Ej. Lima'])
            self.combo_distrito.set('')

        ing_path = 'ingenieros.json'
        if os.path.exists(ing_path):
            try:
                with open(ing_path, 'r', encoding='utf-8') as f:
                    self.ingenieros_cache = json.load(f)
            except Exception:
                pass

        if self.ingenieros_cache:
            nombres = [ing['nombre'] for ing in self.ingenieros_cache]
        else:
            nombres = ['- Vacío -']
            
        self.combo_revisor.configure(values=nombres)
        self.combo_proyectista.configure(values=nombres)
        
        if hasattr(self, 'combo_civil_rev'):
            self.combo_civil_rev.configure(values=nombres)
        if hasattr(self, 'combo_civil_proy'):
            self.combo_civil_proy.configure(values=nombres)

    def on_date_typing(self, event, entry_widget):
        if event.keysym in ('BackSpace', 'Delete', 'Left', 'Right'):
            return
        texto = entry_widget.get().replace('/', '')
        if not texto.isdigit() and texto != '':
            entry_widget.delete(0, 'end')
            entry_widget.insert(0, texto[:-1] if texto else '')
            return
        if len(texto) > 8:
            texto = texto[:8]
        formateado = ''
        for i, char in enumerate(str(texto)):
            if i == 2 or i == 4:
                formateado += '/'
            formateado += char
        entry_widget.delete(0, 'end')
        entry_widget.insert(0, formateado)

    def setup_ui(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=4)
        self.grid_columnconfigure(1, weight=1)

        self.left_panel = ctk.CTkScrollableFrame(self, corner_radius=0)
        self.left_panel.grid(row=0, column=0, sticky='nsew', padx=(0, 5))

        lbl_title = ctk.CTkLabel(self.left_panel, text='ASISTENTE DE CARTA DE APROBACIÓN', font=ctk.CTkFont(size=20, weight='bold'))
        lbl_title.pack(pady=(20, 10), padx=20)

        self.build_bloque_generales()
        self.build_bloque_ubicacion()
        self.build_bloque_fechas()
        self.build_bloque_ingenieros()
        self.build_bloque_planos()

        self.right_panel = ctk.CTkFrame(self, corner_radius=0)
        self.right_panel.grid(row=0, column=1, sticky='nsew', padx=(5, 0))

        lbl_resume = ctk.CTkLabel(self.right_panel, text='ACCIONES', font=ctk.CTkFont(size=18, weight='bold'))
        lbl_resume.pack(pady=(20, 10), padx=20)

        self.btn_export = ctk.CTkButton(self.right_panel, text='Generar Documento Word', fg_color='blue', hover_color='darkblue', height=50, font=ctk.CTkFont(weight='bold'), command=self.action_generar_word)
        self.btn_export.pack(fill='x', padx=20, pady=(20, 10))

        self.lbl_watermark = ctk.CTkLabel(self.right_panel, text='© L.Navarrete', text_color='gray', font=ctk.CTkFont(size=10, slant='italic'))
        self.lbl_watermark.pack(pady=(0, 20))

    def build_bloque_generales(self):
        lbl = ctk.CTkLabel(self.left_panel, text='1. Datos Generales y Fechas', font=ctk.CTkFont(weight='bold', size=14))
        lbl.pack(pady=(15, 5), padx=20, anchor='w')

        f_generales = ctk.CTkFrame(self.left_panel)
        f_generales.pack(fill='x', padx=20, pady=5)

        self.entry_atc = ctk.CTkEntry(f_generales, placeholder_text='Num ATC (Ej. 0100)')
        self.entry_atc.grid(row=0, column=0, sticky='ew', padx=10, pady=10)

        self.entry_referencia = ctk.CTkEntry(f_generales, placeholder_text='Referencia')
        self.entry_referencia.grid(row=0, column=1, sticky='ew', padx=10, pady=10)

        self.entry_fecha_sys = ctk.CTkEntry(f_generales, placeholder_text='Fecha Emisión (DD/MM/AAAA)')
        self.entry_fecha_sys.grid(row=1, column=0, columnspan=2, sticky='ew', padx=10, pady=10)

        f_generales.grid_columnconfigure(0, weight=1)
        f_generales.grid_columnconfigure(1, weight=1)

    def build_bloque_ubicacion(self):
        lbl = ctk.CTkLabel(self.left_panel, text='2. Solicitud, Cliente y Ubicación', font=ctk.CTkFont(weight='bold', size=14))
        lbl.pack(pady=(15, 5), padx=20, anchor='w')

        f_ubi = ctk.CTkFrame(self.left_panel)
        f_ubi.pack(fill='x', padx=20, pady=5)

        self.entry_solicitud = ctk.CTkEntry(f_ubi, placeholder_text='Solicitud (Ej. Aprobación de Subsistema...)')
        self.entry_solicitud.grid(row=0, column=0, columnspan=2, sticky='ew', padx=10, pady=10)

        self.entry_dirigido = ctk.CTkEntry(f_ubi, placeholder_text='Dirigido A (Empresa o Persona)')
        self.entry_dirigido.grid(row=1, column=0, sticky='ew', padx=10, pady=(10, 2))

        self.entry_cliente = ctk.CTkEntry(f_ubi, placeholder_text='Cliente (Propietario)')
        self.entry_cliente.grid(row=1, column=1, sticky='ew', padx=10, pady=(10, 2))

        self.var_mismo_cliente = ctk.BooleanVar(value=False)
        self.chk_cliente = ctk.CTkCheckBox(f_ubi, text='Mismo que Dirigido', variable=self.var_mismo_cliente, command=self.on_chk_cliente)
        self.chk_cliente.grid(row=2, column=1, sticky='w', padx=10, pady=(0, 10))

        self.entry_direccion = ctk.CTkEntry(f_ubi, placeholder_text='Dirección de la Carta')
        self.entry_direccion.grid(row=3, column=0, sticky='ew', padx=10, pady=(10, 2))

        self.entry_direccion_proyecto = ctk.CTkEntry(f_ubi, placeholder_text='Dirección Real del Proyecto')
        self.entry_direccion_proyecto.grid(row=3, column=1, sticky='ew', padx=10, pady=(10, 2))

        self.var_misma_dir = ctk.BooleanVar(value=False)
        self.chk_direccion = ctk.CTkCheckBox(f_ubi, text='Misma Dirección', variable=self.var_misma_dir, command=self.on_chk_dir)
        self.chk_direccion.grid(row=4, column=1, sticky='w', padx=10, pady=(0, 10))

        self.combo_distrito = ctk.CTkComboBox(f_ubi, values=['Cargando...'], command=self.on_distrito_change)
        self.combo_distrito.grid(row=5, column=0, sticky='ew', padx=10, pady=10)
        self.combo_distrito.bind('<KeyRelease>', self.on_distrito_type)

        self.entry_departamento = ctk.CTkEntry(f_ubi, placeholder_text='Departamento (Ej. Lima)')
        self.entry_departamento.grid(row=5, column=1, sticky='ew', padx=10, pady=10)

        f_ubi.grid_columnconfigure(0, weight=1)
        f_ubi.grid_columnconfigure(1, weight=1)

    def build_bloque_fechas(self):
        lbl = ctk.CTkLabel(self.left_panel, text='3. Fechas del Proyecto (Carta e Inicio)', font=ctk.CTkFont(weight='bold', size=14))
        lbl.pack(pady=(15, 5), padx=20, anchor='w')

        f_fec = ctk.CTkFrame(self.left_panel)
        f_fec.pack(fill='x', padx=20, pady=5)

        self.entry_fecha_carta = ctk.CTkEntry(f_fec, placeholder_text='Fecha Carta (DD/MM/YYYY)')
        self.entry_fecha_carta.grid(row=0, column=0, sticky='ew', padx=10, pady=10)

        self.entry_fecha_inicio = ctk.CTkEntry(f_fec, placeholder_text='Fecha Inicio (DD/MM/YYYY)')
        self.entry_fecha_inicio.grid(row=0, column=1, sticky='ew', padx=10, pady=(10, 2))

        self.entry_fecha_fin = ctk.CTkEntry(f_fec, placeholder_text='Fecha Fin (Automático)', state='disabled')
        self.entry_fecha_fin.grid(row=0, column=2, sticky='ew', padx=10, pady=10)

        self.var_usar_f_hoy = ctk.BooleanVar(value=False)
        self.chk_f_hoy = ctk.CTkCheckBox(f_fec, text='Igualar a Fecha Emisión', variable=self.var_usar_f_hoy, command=self.on_chk_fecha_hoy)
        self.chk_f_hoy.grid(row=1, column=1, sticky='w', padx=10, pady=(0, 10))

        f_fec.grid_columnconfigure(0, weight=1)
        f_fec.grid_columnconfigure(1, weight=1)
        f_fec.grid_columnconfigure(2, weight=1)

    def build_bloque_ingenieros(self):
        lbl = ctk.CTkLabel(self.left_panel, text='4. Base de Ingenieros', font=ctk.CTkFont(weight='bold', size=14))
        lbl.pack(pady=(15, 5), padx=20, anchor='w')

        f_ing = ctk.CTkFrame(self.left_panel)
        f_ing.pack(fill='x', padx=20, pady=5)

        f_rev = ctk.CTkFrame(f_ing, fg_color='transparent')
        f_rev.pack(fill='x', padx=10, pady=(10, 5))
        f_rev.grid_columnconfigure(0, weight=2)
        f_rev.grid_columnconfigure(1, weight=1)
        f_rev.grid_columnconfigure(2, weight=1)

        self.combo_revisor = ctk.CTkComboBox(f_rev, values=[''], command=self.on_revisor_change)
        self.combo_revisor.grid(row=0, column=0, sticky='ew', padx=(0, 5))
        self.combo_revisor.bind('<KeyRelease>', self.on_revisor_type)

        self.entry_revisor_cip = ctk.CTkEntry(f_rev, placeholder_text='CIP Revisor')
        self.entry_revisor_cip.grid(row=0, column=1, sticky='ew', padx=(0, 5))

        self.entry_revisor_tipo = ctk.CTkEntry(f_rev, placeholder_text='Tipo (Ej. Ing. Electricista)')
        self.entry_revisor_tipo.grid(row=0, column=2, sticky='ew')

        f_proy = ctk.CTkFrame(f_ing, fg_color='transparent')
        f_proy.pack(fill='x', padx=10, pady=(5, 10))
        f_proy.grid_columnconfigure(0, weight=2)
        f_proy.grid_columnconfigure(1, weight=1)

        self.combo_proyectista = ctk.CTkComboBox(f_proy, values=[''], command=self.on_proyectista_change)
        self.combo_proyectista.grid(row=0, column=0, sticky='ew', padx=(0, 5))
        self.combo_proyectista.bind('<KeyRelease>', self.on_proyectista_type)

        self.entry_proyectista_cip = ctk.CTkEntry(f_proy, placeholder_text='CIP Proyectista')
        self.entry_proyectista_cip.grid(row=0, column=1, sticky='ew')

        f_chk_civil_rev = ctk.CTkFrame(f_ing, fg_color='transparent')
        f_chk_civil_rev.pack(fill='x', padx=10, pady=(5, 5))
        self.var_tiene_civil_rev = ctk.BooleanVar(value=False)
        self.chk_civil_rev = ctk.CTkCheckBox(f_chk_civil_rev, text='Incluir Ingeniero Civil (Revisor)', variable=self.var_tiene_civil_rev, command=self.on_chk_civil_rev)
        self.chk_civil_rev.pack(anchor='w')

        self.f_civil_rev = ctk.CTkFrame(f_ing, fg_color='transparent')
        self.f_civil_rev.grid_columnconfigure(0, weight=2)
        self.f_civil_rev.grid_columnconfigure(1, weight=1)
        self.f_civil_rev.grid_columnconfigure(2, weight=1)

        self.combo_civil_rev = ctk.CTkComboBox(self.f_civil_rev, values=[''], command=self.on_civil_rev_change)
        self.combo_civil_rev.grid(row=0, column=0, sticky='ew', padx=(0, 5))
        self.combo_civil_rev.bind('<KeyRelease>', self.on_civil_rev_type)
        
        self.entry_civil_rev_cip = ctk.CTkEntry(self.f_civil_rev, placeholder_text='CIP Ing. Civil (Rev)')
        self.entry_civil_rev_cip.grid(row=0, column=1, sticky='ew', padx=(0, 5))

        self.entry_civil_rev_planos = ctk.CTkEntry(self.f_civil_rev, placeholder_text='Planos Civiles (Ej. OC-01)')
        self.entry_civil_rev_planos.grid(row=0, column=2, sticky='ew')

        f_chk_civil_proy = ctk.CTkFrame(f_ing, fg_color='transparent')
        f_chk_civil_proy.pack(fill='x', padx=10, pady=(5, 5))
        self.var_tiene_civil_proy = ctk.BooleanVar(value=False)
        self.chk_civil_proy = ctk.CTkCheckBox(f_chk_civil_proy, text='Incluir Ingeniero Civil (Proyectista)', variable=self.var_tiene_civil_proy, command=self.on_chk_civil_proy)
        self.chk_civil_proy.pack(anchor='w')

        self.f_civil_proy = ctk.CTkFrame(f_ing, fg_color='transparent')
        self.f_civil_proy.grid_columnconfigure(0, weight=2)
        self.f_civil_proy.grid_columnconfigure(1, weight=1)

        self.combo_civil_proy = ctk.CTkComboBox(self.f_civil_proy, values=[''], command=self.on_civil_proy_change)
        self.combo_civil_proy.grid(row=0, column=0, sticky='ew', padx=(0, 5))
        self.combo_civil_proy.bind('<KeyRelease>', self.on_civil_proy_type)

        self.entry_civil_proy_cip = ctk.CTkEntry(self.f_civil_proy, placeholder_text='CIP Ing. Civil (Proy)')
        self.entry_civil_proy_cip.grid(row=0, column=1, sticky='ew', padx=(0, 5))


    def build_bloque_planos(self):
        lbl = ctk.CTkLabel(self.left_panel, text='5. Listado de Planos', font=ctk.CTkFont(weight='bold', size=14))
        lbl.pack(pady=(15, 5), padx=20, anchor='w')

        self.frame_planos_list = ctk.CTkFrame(self.left_panel, fg_color='transparent')
        self.frame_planos_list.pack(fill='x', padx=20, pady=0)

        self.lista_entradas_planos = []
        self.agregar_cajon_plano()

        btn_add = ctk.CTkButton(self.left_panel, text='+ Agregar Plano Adicional', fg_color='transparent', border_width=1, command=self.agregar_cajon_plano)
        btn_add.pack(pady=10, padx=20, anchor='w')

    def on_chk_cliente(self):
        if self.var_mismo_cliente.get():
            self.entry_cliente.delete(0, 'end')
            self.entry_cliente.insert(0, self.entry_dirigido.get())
            self.entry_cliente.configure(state='disabled')
        else:
            self.entry_cliente.configure(state='normal')

    def on_chk_dir(self):
        if self.var_misma_dir.get():
            self.entry_direccion_proyecto.delete(0, 'end')
            self.entry_direccion_proyecto.insert(0, self.entry_direccion.get())
            self.entry_direccion_proyecto.configure(state='disabled')
        else:
            self.entry_direccion_proyecto.configure(state='normal')

    def on_chk_civil_rev(self):
        if self.var_tiene_civil_rev.get():
            self.f_civil_rev.pack(fill='x', padx=10, pady=(0, 10))
        else:
            self.f_civil_rev.pack_forget()

    def on_chk_civil_proy(self):
        if self.var_tiene_civil_proy.get():
            self.f_civil_proy.pack(fill='x', padx=10, pady=(0, 10))
        else:
            self.f_civil_proy.pack_forget()

    def on_chk_fecha_hoy(self):
        if self.var_usar_f_hoy.get():
            self.entry_fecha_inicio.delete(0, 'end')
            self.entry_fecha_inicio.insert(0, self.entry_fecha_sys.get())
            self.entry_fecha_inicio.configure(state='disabled')
            self.calcular_fecha_fin(self.entry_fecha_sys.get())
        else:
            self.entry_fecha_inicio.configure(state='normal')

    def on_fecha_inicio_change(self, e):
        self.calcular_fecha_fin(self.entry_fecha_inicio.get())

    def calcular_fecha_fin(self, str_fecha_inicio):
        self.entry_fecha_fin.configure(state='normal')
        self.entry_fecha_fin.delete(0, 'end')
        match = re.search('(\\d{2})[-/](\\d{2})[-/](\\d{4})', str_fecha_inicio)
        if match:
            try:
                d, m, y = map(int, match.groups())
                dt_inicio = datetime.datetime(y, m, d)
                dt_fin = dt_inicio + relativedelta(years=2)
                self.entry_fecha_fin.insert(0, dt_fin.strftime('%d/%m/%Y'))
            except Exception:
                pass
        self.entry_fecha_fin.configure(state='disabled')

    def on_distrito_type(self, e):
        current_text = self.combo_distrito.get()
        if current_text in self.ubicaciones_cache:
            self.on_distrito_change(current_text)

    def on_distrito_change(self, choice):
        if choice in self.ubicaciones_cache:
            self.entry_departamento.delete(0, 'end')
            self.entry_departamento.insert(0, self.ubicaciones_cache[choice])

    def save_new_ubicacion_cache(self):
        dist_actual = self.combo_distrito.get()
        dep_actual = self.entry_departamento.get()
        if dist_actual and dep_actual:
            if dist_actual not in self.ubicaciones_cache or self.ubicaciones_cache[dist_actual] != dep_actual:
                self.ubicaciones_cache[dist_actual] = dep_actual
                try:
                    with open('ubicaciones.json', 'w', encoding='utf-8') as f:
                        json.dump(self.ubicaciones_cache, f, indent=4, ensure_ascii=False)
                except Exception:
                    pass

    def on_revisor_type(self, e):
        nm = self.combo_revisor.get()
        if nm in [i['nombre'] for i in self.ingenieros_cache]:
            self.on_revisor_change(nm)

    def on_revisor_change(self, choice):
        for ing in self.ingenieros_cache:
            if ing['nombre'] == choice:
                self.entry_revisor_cip.delete(0, 'end')
                self.entry_revisor_cip.insert(0, ing['cip'])
                if 'tipo' in ing:
                    self.entry_revisor_tipo.delete(0, 'end')
                    self.entry_revisor_tipo.insert(0, ing['tipo'])
                break

    def on_proyectista_type(self, e):
        nm = self.combo_proyectista.get()
        if nm in [i['nombre'] for i in self.ingenieros_cache]:
            self.on_proyectista_change(nm)

    def on_proyectista_change(self, choice):
        for ing in self.ingenieros_cache:
            if ing['nombre'] == choice:
                self.entry_proyectista_cip.delete(0, 'end')
                self.entry_proyectista_cip.insert(0, ing['cip'])
                break

    def on_civil_rev_type(self, e):
        nm = self.combo_civil_rev.get()
        if nm in [i['nombre'] for i in self.ingenieros_cache]:
            self.on_civil_rev_change(nm)
            
    def on_civil_rev_change(self, choice):
        for ing in self.ingenieros_cache:
            if ing['nombre'] == choice:
                self.entry_civil_rev_cip.delete(0, 'end')
                self.entry_civil_rev_cip.insert(0, ing['cip'])
                break

    def on_civil_proy_type(self, e):
        nm = self.combo_civil_proy.get()
        if nm in [i['nombre'] for i in self.ingenieros_cache]:
            self.on_civil_proy_change(nm)

    def on_civil_proy_change(self, choice):
        for ing in self.ingenieros_cache:
            if ing['nombre'] == choice:
                self.entry_civil_proy_cip.delete(0, 'end')
                self.entry_civil_proy_cip.insert(0, ing['cip'])
                break

    def save_new_ingenieros_cache(self, nombre, cip, rev_or_proy, tipo=''):
        if not nombre or not cip:
            return
        exist = next((i for i in self.ingenieros_cache if i['nombre'] == nombre), None)
        if exist:
            exist['cip'] = cip
            if tipo:
                exist['tipo'] = tipo
        else:
            if tipo:
                tipo_final = tipo
            elif rev_or_proy == 'revisor':
                tipo_final = 'Ingeniero'
            else:
                tipo_final = 'Ingeniero Proyectista'
            self.ingenieros_cache.append({'nombre': nombre, 'cip': cip, 'tipo': tipo_final})

        try:
            with open('ingenieros.json', 'w', encoding='utf-8') as f:
                json.dump(self.ingenieros_cache, f, indent=4, ensure_ascii=False)
        except Exception:
            pass

    def agregar_cajon_plano(self):
        num = len(self.lista_entradas_planos) + 1
        f_plano = ctk.CTkFrame(self.frame_planos_list, fg_color='transparent')
        f_plano.pack(fill='x', pady=2)
        f_plano.grid_columnconfigure(0, weight=1)
        
        entry = ctk.CTkEntry(f_plano, placeholder_text=f'Nombre del Plano {num} (Ej. IE-01)')
        entry.grid(row=0, column=0, sticky='ew', padx=(0, 5))
        
        btn_del = ctk.CTkButton(f_plano, text='X', width=30, fg_color='red', hover_color='darkred', command=lambda f=f_plano, e=entry: self.eliminar_cajon_plano(f, e))
        btn_del.grid(row=0, column=1)
        
        self.lista_entradas_planos.append(entry)

    def eliminar_cajon_plano(self, frame, entry):
        if entry in self.lista_entradas_planos:
            self.lista_entradas_planos.remove(entry)
            frame.destroy()

    def get_resource_path(self, relative_path):
        import sys
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        return os.path.join(base_path, relative_path)

    def action_generar_word(self):
        self.save_new_ubicacion_cache()
        self.save_new_ingenieros_cache(self.combo_revisor.get(), self.entry_revisor_cip.get(), 'revisor', self.entry_revisor_tipo.get())
        self.save_new_ingenieros_cache(self.combo_proyectista.get(), self.entry_proyectista_cip.get(), 'proyectista')
        
        if self.var_tiene_civil_rev.get():
            self.save_new_ingenieros_cache(self.combo_civil_rev.get(), self.entry_civil_rev_cip.get(), 'revisor', 'Ingeniero Civil')
        if self.var_tiene_civil_proy.get():
            self.save_new_ingenieros_cache(self.combo_civil_proy.get(), self.entry_civil_proy_cip.get(), 'proyectista', 'Ingeniero Civil')

        template_base_path = self.get_resource_path('assets/plantilla_carta.docx')
        if not os.path.exists(template_base_path):
            messagebox.showwarning('Falta Plantilla', f'No se encontró la plantilla base en {template_base_path}. Por favor, asegúrate de colocarla antes de exportar.')
            return

        planos = [p.get().strip() for p in self.lista_entradas_planos if p.get().strip()]
        if not planos:
            messagebox.showwarning('Faltan Planos', 'Debes ingresar al menos un (1) plano en la lista.')
            return

        atc_val = self.entry_atc.get().strip()
        if not atc_val:
            atc_val = '0000'

        export_path = filedialog.asksaveasfilename(defaultextension=".docx", initialfile=f"PD-{atc_val}-2026.docx", filetypes=[("Word Document", "*.docx")])
        if not export_path:
            return

        context = {
            'FECHA_HOY_CORTA': self.entry_fecha_sys.get(),
            'ATC': atc_val,
            'REFERENCIA': self.entry_referencia.get(),
            'SOLICITUD': self.entry_solicitud.get(),
            'DIRIGIDO': self.entry_dirigido.get(),
            'CLIENTE': self.entry_cliente.get(),
            'DIRECCION_CARTA': self.entry_direccion.get(),
            'DIRECCION_PROYECTO': self.entry_direccion_proyecto.get(),
            'DISTRITO': self.combo_distrito.get(),
            'DEPARTAMENTO': self.entry_departamento.get(),
            'FECHA_CARTA': self.entry_fecha_carta.get(),
            'FECHA_INICIO': self.entry_fecha_inicio.get(),
            'FECHA_FIN_CALCULADA': self.entry_fecha_fin.get(),
            'REVISOR_NOMBRE': self.combo_revisor.get(),
            'REVISOR_CIP': self.entry_revisor_cip.get(),
            'REVISOR_TIPO': self.entry_revisor_tipo.get(),
            'PROYECTISTA_NOMBRE': self.combo_proyectista.get(),
            'PROYECTISTA_CIP': self.entry_proyectista_cip.get(),
            'TIENE_ING_CIVIL_REV': self.var_tiene_civil_rev.get(),
            'NOMBRE_ING_CIVIL_REV': self.combo_civil_rev.get() if self.var_tiene_civil_rev.get() else '',
            'CIP_ING_CIVIL_REV': self.entry_civil_rev_cip.get() if self.var_tiene_civil_rev.get() else '',
            'PLANOS_CIVILES': self.entry_civil_rev_planos.get() if self.var_tiene_civil_rev.get() else '',
            'TIENE_ING_CIVIL_PROY': self.var_tiene_civil_proy.get(),
            'NOMBRE_ING_CIVIL_PROY': self.combo_civil_proy.get() if self.var_tiene_civil_proy.get() else '',
            'CIP_ING_CIVIL_PROY': self.entry_civil_proy_cip.get() if self.var_tiene_civil_proy.get() else '',
            'LISTA_PLANOS': planos
        }

        success, msg = self.word_engine.generar_documento(template_base_path, export_path, context)
        if success:
            def convert_to_pdf(docx_path, pdf_path):
                try:
                    from docx2pdf import convert
                    pdf_path = docx_path.replace('.docx', '.pdf')
                    convert(docx_path, pdf_path)
                    self.after(0, lambda: messagebox.showinfo('Éxito', f"{msg}\n\nTambién se ha generado automáticamente una versión PDF en la misma carpeta."))
                except ImportError:
                    self.after(0, lambda: messagebox.showinfo('Éxito', f"{msg}\n\nOpcional: Instala 'docx2pdf' (pip install docx2pdf) para habilitar la auto-exportación a PDF."))
                except Exception as e:
                    print(f"Error convirtiendo a PDF: {e}")
                    self.after(0, lambda: messagebox.showinfo('Éxito', msg))

            threading.Thread(target=convert_to_pdf, args=(export_path, export_path), daemon=True).start()
        else:
            messagebox.showerror('Error', msg)
