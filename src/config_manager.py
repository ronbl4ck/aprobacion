import json
import os

class ConfigManager:
    __slots__ = ('config', 'config_file')

    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.config = {
            "signature_path": "",
            "engineer_name": "",
            "cip_number": "",
            "cover_coords": [100, 100],
            "body_coords": [100, 100],
            "cover_page": 1,
            "body_page_start": 2,
            "body_page_end": "",
            "start_date": "",
            "template_path": "",
            "cover_scale": 100,
            "body_scale": 100,
            "tpl_date1_coords": None,
            "tpl_date2_coords": None,
            "tpl_sig_coords": None,
            "tpl_date_scale": 100,
            "tpl_sig_scale": 100
        }
        self.load_config()

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.config.update(data)
            except Exception as e:
                print(f"Error cargando config: {e}")

    def save_config(self):
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error guardando config: {e}")

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self.save_config()
