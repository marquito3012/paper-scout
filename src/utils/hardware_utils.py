import subprocess
import shutil

def detect_gpu() -> dict:
    """
    Detecta si hay una GPU disponible (NVIDIA o AMD).
    
    Returns:
        Dict con 'found' (bool), 'type' (str) y 'name' (str).
    """
    result = {"found": False, "type": None, "name": "CPU only"}
    
    # 1. Probar NVIDIA (nvidia-smi)
    if shutil.which("nvidia-smi"):
        try:
            output = subprocess.check_output(
                ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"], 
                encoding="utf-8"
            )
            result["found"] = True
            result["type"] = "nvidia"
            result["name"] = output.strip().split("\n")[0]
            return result
        except:
            pass
            
    # 2. Probar AMD (lspci + look for AMD/ATI)
    try:
        lspci = subprocess.check_output(["lspci"], encoding="utf-8").lower()
        if "vga compatible controller" in lspci and ("amd" in lspci or "ati" in lspci):
            # Intentar obtener nombre más específico
            import re
            match = re.search(r"vga compatible controller: (.+)", lspci)
            result["found"] = True
            result["type"] = "amd"
            result["name"] = match.group(1).split("[")[0].strip() if match else "AMD Radeon GPU"
            return result
    except:
        pass
        
    return result
