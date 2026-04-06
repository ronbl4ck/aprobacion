import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import os
import sys
import datetime

from src.ui.layout_editor import LayoutEditorWindow
from src.ui.config_sellos import ConfigSello1Window, ConfigSello2Window

class TabAutofirma(ctk.CTkFrame):
    def __init__(self, parent, config_manager, stamp_engine, pdf_manager):
        super().__init__(parent, fg_color="transparent")
        self.config_manager = config_manager
        self.stamp_engine = stamp_engine
        self.pdf_manager = pdf_manager
        self.pdf_path = None
        self.pdf_doc = None
        self.total_pages = 0
        self.current_preview_page = 0
        self.preview_image_pil = None
        self.preview_image_tk = None
        self.canvas_scale = 1.0
        self.rect_id = None
        self.current_stamp_type = tk.StringVar(value="cover")
        self.cover_coords = self.config_manager.get("cover_coords", [100, 100])
        self.body_coords = self.config_manager.get("body_coords", [100, 100])
        self.setup_ui()
        self.load_profile()

    def setup_ui(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)

        self.left_panel = ctk.CTkScrollableFrame(self, width=350, corner_radius=0)
        self.left_panel.grid(row=0, column=0, sticky="nsew")

        lbl_title = ctk.CTkLabel(self.left_panel, text="CONFIGURACIÓN (PDF)", font=ctk.CTkFont(size=20, weight="bold"))
        lbl_title.pack(pady=20, padx=10)

        lbl_dnd_hint = ctk.CTkLabel(self.left_panel, text="(Puedes arrastrar tu PDF aquí)", font=ctk.CTkFont(size=12, slant="italic"), text_color="gray")
        lbl_dnd_hint.pack(pady=(0, 10))

        frame_files = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        frame_files.pack(fill="x", padx=20, pady=5)

        self.btn_load_pdf = ctk.CTkButton(frame_files, text="Cargar Archivo PDF", command=self.action_load_pdf)
        self.btn_load_pdf.pack(fill="x", pady=5)
        self.lbl_pdf_info = ctk.CTkLabel(frame_files, text="Ningún PDF cargado (0 págs)", text_color="gray")
        self.lbl_pdf_info.pack(pady=(0, 10))

        f_date = ctk.CTkFrame(frame_files, fg_color="transparent")
        f_date.pack(fill="x", pady=5)
        ctk.CTkLabel(f_date, text="Fecha Sello 1 (DD/MM/YYYY):").pack(anchor="w")

        f_date_inner = ctk.CTkFrame(f_date, fg_color="transparent")
        f_date_inner.pack(fill="x")
        self.entry_start_date = ctk.CTkEntry(f_date_inner, width=120)
        self.entry_start_date.pack(side="left", padx=(0, 5))
        btn_today = ctk.CTkButton(f_date_inner, text="Hoy", width=40, command=self.set_today)
        btn_today.pack(side="left")

        ctk.CTkLabel(self.left_panel, text="Aplicación de Sellos", font=ctk.CTkFont(weight="bold")).pack(pady=(15, 0), padx=20, anchor="w")

        f_sello1 = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        f_sello1.pack(fill="x", padx=20, pady=5)
        self.var_apply_sello1 = ctk.BooleanVar(value=self.config_manager.get("apply_sello1", True))
        chk1 = ctk.CTkCheckBox(f_sello1, text="Aplicar Sello 1 (Carátula/V°B°)", variable=self.var_apply_sello1, command=self.on_toggle_sellos)
        chk1.pack(side="left", pady=5)
        btn_cfg1 = ctk.CTkButton(f_sello1, text="⚙️ Configurar", width=80, fg_color="gray30", command=self.open_config_sello1)
        btn_cfg1.pack(side="right")

        f_sello2 = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        f_sello2.pack(fill="x", padx=20, pady=5)
        self.var_apply_sello2 = ctk.BooleanVar(value=self.config_manager.get("apply_sello2", True))
        chk2 = ctk.CTkCheckBox(f_sello2, text="Aplicar Sello 2 (Cuerpo)", variable=self.var_apply_sello2, command=self.on_toggle_sellos)
        chk2.pack(side="left", pady=5)
        btn_cfg2 = ctk.CTkButton(f_sello2, text="⚙️ Configurar", width=80, fg_color="gray30", command=self.open_config_sello2)
        btn_cfg2.pack(side="right")

        ctk.CTkLabel(self.left_panel, text="Modo Previsualización", font=ctk.CTkFont(weight="bold")).pack(pady=(15, 5), padx=20, anchor="w")
        frame_radio = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        frame_radio.pack(fill="x", padx=20, pady=0)
        self.radio_cover = ctk.CTkRadioButton(frame_radio, text="Posicionar Carátula", variable=self.current_stamp_type, value="cover", command=self.update_preview)
        self.radio_cover.pack(pady=5, anchor="w")
        self.radio_body = ctk.CTkRadioButton(frame_radio, text="Posicionar Cuerpo", variable=self.current_stamp_type, value="body", command=self.update_preview)
        self.radio_body.pack(pady=5, anchor="w")

        self.btn_export = ctk.CTkButton(self.left_panel, text="Procesar y Exportar", fg_color="green", hover_color="darkgreen", height=40, font=ctk.CTkFont(weight="bold"), command=self.action_export)
        self.btn_export.pack(fill="x", padx=20, pady=(20, 5))
        self.lbl_watermark = ctk.CTkLabel(self.left_panel, text="© L.Navarrete", text_color="gray", font=ctk.CTkFont(size=10, slant="italic"))
        self.lbl_watermark.pack(pady=(0, 20))

        self.right_panel = ctk.CTkFrame(self, corner_radius=0)
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        frame_paginator = ctk.CTkFrame(self.right_panel, height=40)
        frame_paginator.pack(fill="x", side="top", pady=(0, 10))
        self.btn_prev_page = ctk.CTkButton(frame_paginator, text="<", width=40, command=self.action_prev_page)
        self.btn_prev_page.pack(side="left", padx=5, pady=5)
        self.lbl_page_num = ctk.CTkLabel(frame_paginator, text="Página 0 / 0")
        self.lbl_page_num.pack(side="left", padx=10, pady=5)
        self.btn_next_page = ctk.CTkButton(frame_paginator, text=">", width=40, command=self.action_next_page)
        self.btn_next_page.pack(side="left", padx=5, pady=5)
        self.btn_zoom_in = ctk.CTkButton(frame_paginator, text="Zoom +", width=60, command=self.action_zoom_in)
        self.btn_zoom_in.pack(side="right", padx=5, pady=5)
        self.btn_zoom_out = ctk.CTkButton(frame_paginator, text="Zoom -", width=60, command=self.action_zoom_out)
        self.btn_zoom_out.pack(side="right", padx=5, pady=5)

        self.canvas_panel = ctk.CTkFrame(self.right_panel)
        self.canvas_panel.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(self.canvas_panel, bg="gray20", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Button-1>", self.on_canvas_click)

        try:
            import windnd
            def on_drop(files):
                if files:
                    path = files[0].decode('gbk', errors='ignore')
                    if path.lower().endswith('.pdf'):
                        self.load_pdf_from_path(path)
                    else:
                        messagebox.showwarning("Formato Inválido", "Por favor arrastra un archivo PDF.")
            self.after(500, lambda: windnd.hook_dropfiles(self.winfo_toplevel().winfo_id(), func=on_drop))
        except ImportError:
            pass

    def open_config_sello1(self):
        ConfigSello1Window(self, self.config_manager, on_close_callback=self.update_preview)

    def open_config_sello2(self):
        ConfigSello2Window(self, self.config_manager, on_close_callback=self.update_preview)

    def on_toggle_sellos(self):
        self.config_manager.config['apply_sello1'] = self.var_apply_sello1.get()
        self.config_manager.config['apply_sello2'] = self.var_apply_sello2.get()
        self.config_manager.save_config()
        self.update_preview()

    def set_today(self):
        from datetime import datetime
        self.entry_start_date.delete(0, "end")
        self.entry_start_date.insert(0, datetime.today().strftime("%d/%m/%Y"))

    def load_profile(self):
        tpl_path = self.get_resource_path("assets/plantilla_caratula.png")
        self.config_manager.set("template_path", tpl_path)
        self.entry_start_date.insert(0, self.config_manager.get("start_date", ""))

    def save_profile(self):
        self.config_manager.config['start_date'] = self.entry_start_date.get()
        self.config_manager.config['cover_coords'] = self.cover_coords
        self.config_manager.config['body_coords'] = self.body_coords
        self.config_manager.save_config()

    def get_resource_path(self, relative_path):
        import sys
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        return os.path.join(base_path, relative_path)

    def action_load_template(self):
        pass

    def action_edit_template_layout(self):
        base_template = self.get_resource_path("assets/plantilla_caratula.png")
        if not os.path.exists(base_template):
            messagebox.showwarning("Atención", f"No se encontró la plantilla default en {base_template}.")
            return
        LayoutEditorWindow(self, self.config_manager, base_template)

    def action_load_signature(self):
        path = filedialog.askopenfilename(title="Seleccionar Firma PNG", filetypes=[("PNG transparent", "*.png")])
        if path:
            self.config_manager.set("signature_path", path)
            self.lbl_sig_path.configure(text=f"...{path[-25:]}")

    def load_pdf_from_path(self, path):
        if path and os.path.exists(path):
            self.pdf_path = path
            self.pdf_doc, self.total_pages = self.pdf_manager.load_pdf(path)
            if self.total_pages > 0:
                self.lbl_pdf_info.configure(text=f"Cargado: {os.path.basename(path)} ({self.total_pages} págs)")
                self.current_preview_page = 0
                self.update_preview()
            else:
                messagebox.showerror("Error", "No se pudo cargar el archivo PDF.")

    def action_load_pdf(self):
        path = filedialog.askopenfilename(title="Seleccionar PDF a sellar", filetypes=[("Archivos PDF", "*.pdf")])
        if path:
            self.load_pdf_from_path(path)

    def action_prev_page(self):
        if self.total_pages > 0 and self.current_preview_page > 0:
            self.current_preview_page -= 1
            self.update_preview()

    def action_next_page(self):
        if self.total_pages > 0 and self.current_preview_page < self.total_pages - 1:
            self.current_preview_page += 1
            self.update_preview()

    def action_zoom_in(self):
        self.canvas_scale += 0.2
        self.update_preview()

    def action_zoom_out(self):
        if self.canvas_scale > 0.4:
            self.canvas_scale -= 0.2
            self.update_preview()

    def action_preview_cover_stamp_from_popup(self, popup):
        self.save_profile()
        sig_path = self.config_manager.get("signature_path")
        start_date = self.config_manager.get("start_date", "")
        base_template = self.get_resource_path("assets/plantilla_caratula.png")
        if not os.path.exists(base_template):
            popup.attributes('-topmost', False)
            messagebox.showwarning("Falta Plantilla", f"Falta plantilla principal en: {base_template}")
            popup.attributes('-topmost', True)
            return

        layout_cfg = {
            "date1": self.config_manager.get("tpl_date1_coords"),
            "date2": self.config_manager.get("tpl_date2_coords"),
            "sig": self.config_manager.get("tpl_sig_coords"),
            "date_scale": self.config_manager.get("tpl_date_scale", 100),
            "sig_scale": self.config_manager.get("tpl_sig_scale", 100)
        }

        cover_img = self.stamp_engine.generate_cover_stamp(base_template, sig_path, start_date, layout_coords=layout_cfg)
        top = ctk.CTkToplevel(self)
        top.title("Previsualización Sello Carátula")
        top.geometry("600x400")
        top.attributes('-topmost', True)
        tk_img = ImageTk.PhotoImage(cover_img)
        lbl = ctk.CTkLabel(top, image=tk_img, text='')
        lbl.pack(expand=True, padx=20, pady=20)

    def update_preview(self):
        if not self.pdf_doc: return
        self.lbl_page_num.configure(text=f"Página {self.current_preview_page + 1} / {self.total_pages}")
        self.preview_image_pil = self.pdf_manager.get_page_image(self.pdf_doc, self.current_preview_page, zoom=self.canvas_scale)
        if not self.preview_image_pil: return
        self.preview_image_tk = ImageTk.PhotoImage(self.preview_image_pil)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self.preview_image_tk)
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
        self.draw_ghost_rect()

    def on_canvas_click(self, event):
        if not self.pdf_doc: return
        real_x = int(event.x / self.canvas_scale)
        real_y = int(event.y / self.canvas_scale)
        mode = self.current_stamp_type.get()
        if mode == "cover":
            self.cover_coords = [real_x, real_y]
        else:
            self.body_coords = [real_x, real_y]
        self.save_profile()
        self.draw_ghost_rect()

    def get_stamp_size(self, mode):
        cover_scale = int(self.config_manager.get("cover_scale", 100))
        body_scale = int(self.config_manager.get("body_scale", 100))
        BASE_FACTOR = 0.35

        if mode == "cover":
            tpl_path = self.get_resource_path("assets/plantilla_caratula.png")
            w, h = 300, 150
            if os.path.exists(tpl_path):
                try:
                    with Image.open(tpl_path) as img:
                        w, h = img.size
                except Exception:
                    pass
            return (int(w * BASE_FACTOR * (cover_scale / 100.0)), int(h * BASE_FACTOR * (cover_scale / 100.0)))
        else:
            if self.config_manager.get("sello2_mode") == "custom":
                c_path = self.config_manager.get("sello2_custom_path", "")
                cw, ch = 300, 150
                if c_path and os.path.exists(c_path):
                    try:
                        with Image.open(c_path) as img:
                            cw, ch = img.size
                    except Exception:
                        pass
                w, h = cw, ch
            else:
                try:
                    w, h = self.stamp_engine.get_body_stamp_size(
                        self.config_manager.get("signature_path"),
                        self.config_manager.get("engineer_name", ""),
                        self.config_manager.get("cip_number", ""),
                        self.config_manager.get("engineer_type", "")
                    )
                except Exception:
                    w, h = 400, 250
            return (int(w * BASE_FACTOR * (body_scale / 100.0)), int(h * BASE_FACTOR * (body_scale / 100.0)))

    def draw_ghost_rect(self):
        if self.rect_id:
            self.canvas.delete(self.rect_id)
        mode = self.current_stamp_type.get()
        w, h = self.get_stamp_size(mode)

        if mode == "cover":
            cx, cy = self.cover_coords
        else:
            cx, cy = self.body_coords
        
        color = 'blue' if mode == "cover" else 'red'
        x, y, w, h = cx * self.canvas_scale, cy * self.canvas_scale, w * self.canvas_scale, h * self.canvas_scale
        self.rect_id = self.canvas.create_rectangle(x, y, x + w, y + h, outline=color, width=2, dash=(4, 4))

    def action_export(self):
        if not self.pdf_doc or not self.pdf_path:
            messagebox.showwarning("Atención", "Cargue un PDF primero.")
            return

        self.save_profile()
        base, ext = os.path.splitext(self.pdf_path)
        out_path = f"{base}_firmado{ext}"

        sig_path = self.config_manager.get("signature_path")
        name = self.config_manager.get("engineer_name", "")
        cip = self.config_manager.get("cip_number", "")
        tipo = self.config_manager.get("engineer_type", "")
        start_date = self.config_manager.get("start_date", "")

        base_template = self.get_resource_path("assets/plantilla_caratula.png")
        if not os.path.exists(base_template):
            os.makedirs(os.path.dirname(base_template), exist_ok=True)
            tmp_img = Image.new("RGBA", (300, 150), "white")
            from PIL import ImageDraw
            d = ImageDraw.Draw(tmp_img)
            d.rectangle([0, 0, 299, 149], outline="black", width=2)
            d.text((10, 120), "V°B° ________________", fill="black")
            tmp_img.save(base_template)

        layout_cfg = {
            "date1": self.config_manager.get("tpl_date1_coords"),
            "date2": self.config_manager.get("tpl_date2_coords"),
            "sig": self.config_manager.get("tpl_sig_coords"),
            "date_scale": self.config_manager.get("tpl_date_scale", 100),
            "sig_scale": self.config_manager.get("tpl_sig_scale", 100)
        }

        cover_img = None
        if self.config_manager.get("apply_sello1", True):
            cover_img = self.stamp_engine.generate_cover_stamp(base_template, sig_path, start_date, layout_coords=layout_cfg)

        body_img = None
        if self.config_manager.get("apply_sello2", True):
            if self.config_manager.get("sello2_mode") == "custom":
                c_path = self.config_manager.get("sello2_custom_path", "")
                if c_path and os.path.exists(c_path):
                    body_img = Image.open(c_path).convert("RGBA")
            else:
                body_img = self.stamp_engine.generate_body_stamp(sig_path, name, cip, tipo)

        try:
            success, msg = self.pdf_manager.process_and_save(self.pdf_doc, cover_img, body_img, self.config_manager.config, out_path)
            if success:
                messagebox.showinfo("Éxito", f"¡Documento firmado exitosamente!\nGuardado en:\n{out_path}")
            else:
                messagebox.showerror("Error", msg)
        except Exception as e:
            messagebox.showerror("Error Severo", str(e))
