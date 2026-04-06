import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.gui import MainApp

if __name__ == '__main__':
    app = MainApp()
    app.mainloop()
