import json
import os
import hashlib
import base64

class ProfileManager:
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        self.profiles_file = os.path.join(self.data_dir, "perfiles.json")
        self._ensure_data_dir()
        self.profiles = self._load_profiles()

    def _ensure_data_dir(self):
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def _load_profiles(self):
        if os.path.exists(self.profiles_file):
            try:
                with open(self.profiles_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error cargando perfiles: {e}")
                return {}
        return {}

    def _save_profiles(self):
        try:
            with open(self.profiles_file, "w", encoding="utf-8") as f:
                json.dump(self.profiles, f, indent=4)
        except Exception as e:
            print(f"Error guardando perfiles: {e}")

    def _hash_pin(self, pin: str) -> str:
        return hashlib.sha256(pin.encode('utf-8')).hexdigest()

    def add_profile(self, name, cip, title, signature_bytes, pin, sello2_mode="generate", custom_stamp_bytes=None, tpl_coords=None):
        """Agrega o actualiza un perfil"""
        if tpl_coords is None:
            tpl_coords = {
                "date1": [342, 212],
                "date2": [342, 276],
                "sig": [62, 280],
                "date_scale": 100,
                "sig_scale": 100
            }
        signature_b64 = base64.b64encode(signature_bytes).decode('utf-8') if signature_bytes else ""
        custom_b64 = base64.b64encode(custom_stamp_bytes).decode('utf-8') if custom_stamp_bytes else ""
        pin_hash = self._hash_pin(pin)

        self.profiles[name] = {
            "name": name,
            "cip": cip,
            "title": title,
            "signature_b64": signature_b64,
            "sello2_mode": sello2_mode,
            "custom_stamp_b64": custom_b64,
            "tpl_coords": tpl_coords,
            "pin_hash": pin_hash
        }
        self._save_profiles()
        return True

    def get_profile_names(self):
        return list(self.profiles.keys())

    def authenticate(self, name, pin):
        """Verifica credenciales y devuelve el perfil con los bytes de la firma si es válido"""
        if name not in self.profiles:
            return None
        
        prof = self.profiles[name]
        if prof.get("pin_hash") == self._hash_pin(pin):
            # Decode signature
            sig_b64 = prof.get("signature_b64", "")
            sig_bytes = base64.b64decode(sig_b64) if sig_b64 else None
            
            # Decode custom stamp if exists
            c_b64 = prof.get("custom_stamp_b64", "")
            c_bytes = base64.b64decode(c_b64) if c_b64 else None
            
            return {
                "name": prof["name"],
                "cip": prof.get("cip", ""),
                "title": prof.get("title", ""),
                "signature_bytes": sig_bytes,
                "sello2_mode": prof.get("sello2_mode", "generate"),
                "custom_stamp_bytes": c_bytes,
                "tpl_coords": prof.get("tpl_coords", {})
            }
        return None
