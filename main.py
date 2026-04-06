import os, subprocess, sys
print('Iniciando Streamlit')
subprocess.run([sys.executable, '-m', 'streamlit', 'run', 'app.py'])
