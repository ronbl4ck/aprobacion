import codecs
with open('main.py', 'r', encoding='utf-8') as f:
    code = f.read()

code = code.replace(" 🖋️ Sistema de Aprobación - Autofirma PDF", " Sistema de Aprobacion - Autofirma PDF")
code = code.replace(" 🚀 Inicializando Streamlit en puerto 8501...", " Inicializando Streamlit en puerto 8501...")

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(code)
    print("MAIN PATCHED")
