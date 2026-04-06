import customtkinter as ctk

from src.config_manager import ConfigManager
from src.stamp_engine import StampEngine
from src.pdf_manager import PDFManager
from src.word_engine import WordEngine
from src.ui.tab_autofirma import TabAutofirma
from src.ui.tab_carta import TabCarta

ctk.set_appearance_mode('System')
ctk.set_default_color_theme('blue')

class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title('Sistema de Aprobación de Factibilidad')
        self.geometry('1100x700')
        
        self.config_manager = ConfigManager()
        self.stamp_engine = StampEngine()
        self.pdf_manager = PDFManager()
        self.word_engine = WordEngine()
        
        self.setup_ui()

    def setup_ui(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.tab_view = ctk.CTkTabview(self)
        self.tab_view.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)

        self.tab_view.add('Autofirma (PDF)')
        self.tab_view.add('Carta Aprobación (Word)')

        self.tab_view.tab('Autofirma (PDF)').grid_rowconfigure(0, weight=1)
        self.tab_view.tab('Autofirma (PDF)').grid_columnconfigure(0, weight=1)

        self.tab_autofirma = TabAutofirma(
            self.tab_view.tab('Autofirma (PDF)'),
            self.config_manager,
            self.stamp_engine,
            self.pdf_manager
        )
        self.tab_autofirma.grid(row=0, column=0, sticky='nsew')

        self.tab_view.tab('Carta Aprobación (Word)').grid_rowconfigure(0, weight=1)
        self.tab_view.tab('Carta Aprobación (Word)').grid_columnconfigure(0, weight=1)

        self.tab_carta = TabCarta(
            self.tab_view.tab('Carta Aprobación (Word)'),
            self.config_manager,
            self.word_engine
        )
        self.tab_carta.grid(row=0, column=0, sticky='nsew')
