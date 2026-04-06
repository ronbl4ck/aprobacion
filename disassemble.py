import os
import marshal
import dis

src_dir = r"d:\PROGRAMACION\APROBACION\SistemaAprobacion.exe_extracted\PYZ.pyz_extracted\src"
out_dir = r"d:\PROGRAMACION\APROBACION\disassembled_src"

os.makedirs(out_dir, exist_ok=True)

def disassemble_pyc(pyc_path, dis_path):
    with open(pyc_path, "rb") as f:
        f.read(16) # Skip magic and timestamp
        code = marshal.load(f)
        
    with open(dis_path, "w", encoding="utf-8") as out_f:
        dis.dis(code, file=out_f)
        
        def dump_code_obj(c, level=1):
            indent = "  " * level
            out_f.write(f"\n{indent}--- CODE OBJ: {c.co_name} ---\n")
            out_f.write(f"{indent}CONSTANTS: {repr(c.co_consts)}\n")
            out_f.write(f"{indent}NAMES: {repr(c.co_names)}\n")
            out_f.write(f"{indent}VARNAMES: {repr(c.co_varnames)}\n")
            out_f.write(f"{indent}FREEVARS: {repr(c.co_freevars)}\n")
            for const in c.co_consts:
                if hasattr(const, 'co_name'):
                    dump_code_obj(const, level + 1)
        
        dump_code_obj(code)

for pyc in os.listdir(src_dir):
    if pyc.endswith(".pyc"):
        pyc_path = os.path.join(src_dir, pyc)
        dis_path = os.path.join(out_dir, pyc.replace(".pyc", ".dis"))
        print(f"Disassembling {pyc} ...")
        try:
            disassemble_pyc(pyc_path, dis_path)
            print(f"  -> Saved to {dis_path}")
        except Exception as e:
            print(f"  -> Error: {e}")

# Also disassemble main.pyc
main_pyc = r"d:\PROGRAMACION\APROBACION\SistemaAprobacion.exe_extracted\main.pyc"
if os.path.exists(main_pyc):
    try:
        disassemble_pyc(main_pyc, os.path.join(out_dir, "main.dis"))
    except Exception as e:
        print(f"Error main.pyc: {e}")
