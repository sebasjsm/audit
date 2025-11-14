# server.py — FastAPI para exponer JSON de Autofill
# Ejecuta:  uvicorn server:app --host 0.0.0.0 --port 8001 --reload
# Requisitos:  pip install fastapi uvicorn pydantic

import os
import re
import json
import time
import random
import string
import getpass
import tempfile
import subprocess
from datetime import datetime
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

# =============== Configuración básica ===============
APP_PORT = int(os.getenv("AUTOFILL_API_PORT", "8001"))
ALLOWED_ORIGINS = json.loads(os.getenv(
    "AUTOFILL_CORS",
    "[\"http://localhost:4200\",\"http://127.0.0.1:4200\",\"http://192.168.10.217\",\"http://192.168.10.217:4200\"]"
))
STORE_DIR = os.path.abspath(os.getenv("AUTOFILL_STORE", "json_store"))
os.makedirs(STORE_DIR, exist_ok=True)

app = FastAPI(title="Auditoria Autofill API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==== Importa tus módulos si existen en el mismo directorio ====
try:
    import aplicaciones  # debe exponer: verificar_aplicaciones(texto: str) -> bool/str
except Exception:
    aplicaciones = None

try:
    import pc_info  # funciones varias de info del equipo
except Exception:
    pc_info = None

try:
    import limpieza  # utilidades (no obligatorio para el API)
except Exception:
    limpieza = None

# =================== Vinculación por código (EXE -> API -> Angular) ===================

LINK_TTL = 300  # 5 min
PENDING: Dict[str, dict] = {}  # code -> {ts:int, path:str|None}

class PushBody(BaseModel):
    code: str
    payload: dict

def _new_code(n=6) -> str:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(random.choice(alphabet) for _ in range(n))

def _cleanup_links():
    now = int(time.time())
    for k, v in list(PENDING.items()):
        if now - v.get("ts", 0) > LINK_TTL:
            PENDING.pop(k, None)

@app.get("/link/start")
def link_start():
    _cleanup_links()
    code = _new_code()
    PENDING[code] = {"ts": int(time.time()), "path": None}
    return {"ok": True, "code": code, "expires_in": LINK_TTL}

@app.post("/link/push")
def link_push(body: PushBody):
    _cleanup_links()
    info = PENDING.get(body.code)
    if not info:
        raise HTTPException(status_code=404, detail="Código inválido o expirado")

    # guardamos snapshot en disco y marcamos listo
    name = f"link-{body.code}.json"
    fpath = os.path.join(STORE_DIR, name)
    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(body.payload, f, ensure_ascii=False, indent=2)

    info["path"] = fpath
    return {"ok": True}

@app.get("/link/poll/{code}")
def link_poll(code: str):
    _cleanup_links()
    info = PENDING.get(code)
    if not info:
        return {"ok": False, "error": "Código inválido o expirado"}

    fpath = info.get("path")
    if not fpath or not os.path.isfile(fpath):
        # aún no llegó el push del EXE
        return {"ok": False, "error": "Pendiente"}

    # leemos y consumimos una sola vez
    with open(fpath, "r", encoding="utf-8") as f:
        data = json.load(f)
    try:
        os.remove(fpath)
    except Exception:
        pass
    PENDING.pop(code, None)

    # El front ya sabe normalizar esta estructura
    return {"ok": True, "datos": data}

# =================== Helpers ===================

def _only_digits(v: Any) -> str:
    s = str(v or "")
    m = re.findall(r"\d+", s)
    return "".join(m) if m else ""

def _to_iso_date(v: Any) -> str:
    """Convierte 'DD/MM/YYYY' o 'YYYY-MM-DD' a 'YYYY-MM-DD'"""
    if not v:
        return ""
    s = str(v).strip()
    m_iso = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", s)
    if m_iso:
        return s
    m_dmy = re.match(r"^(\d{2})[/-](\d{2})[/-](\d{4})$", s)
    if m_dmy:
        dd, mm, yyyy = m_dmy.groups()
        return f"{yyyy}-{mm}-{dd}"
    return datetime.now().strftime("%Y-%m-%d")

def _safe_call(func, default=None, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except Exception:
        return default

def _detect_office() -> Optional[str]:
    if not aplicaciones or not hasattr(aplicaciones, "verificar_aplicaciones"):
        return None
    for name in ["microsoft 365", "office", "libreoffice"]:
        ok = _safe_call(aplicaciones.verificar_aplicaciones, False, name)
        if ok:
            return name.title()
    return None

def _detect_antivirus() -> Optional[str]:
    if not aplicaciones or not hasattr(aplicaciones, "verificar_aplicaciones"):
        return None
    candidatos = [
        "defender", "eset", "kaspersky", "avast", "avg",
        "bitdefender", "norton", "mcafee", "trend micro",
    ]
    for name in candidatos:
        ok = _safe_call(aplicaciones.verificar_aplicaciones, False, name)
        if ok:
            return name.title()
    return None

def _pc_value(name: str) -> str:
    """Obtiene un valor de pc_info.* si está disponible; devuelve '' si falla."""
    if not pc_info:
        return ""
    fn = getattr(pc_info, name, None)
    if not callable(fn):
        return ""
    val = _safe_call(fn, "")
    return str(val or "")

def _parse_memory_to_gb(s: str) -> int:
    s_low = str(s or "").lower()
    nums = re.findall(r"[\d.]+", s_low)
    if not nums:
        return 0
    val = float(nums[0])
    if "mb" in s_low or val > 256:
        return int(round(val / 1024))
    return int(round(val))

# =================== Construcción del payload (para /autofill) ===================

def build_autofill_payload() -> Dict[str, Any]:
    hostname = _pc_value("get_hostname") or os.environ.get("COMPUTERNAME", "")
    usuario = getpass.getuser()
    dominio = os.environ.get("USERDOMAIN", "")
    usuario_dominio = f"{dominio}\\{usuario}" if dominio else usuario

    so_nombre = _pc_value("get_computer_os")
    arquitectura = _pc_value("get_computer_architecture")
    bits = "64" if "64" in arquitectura else ("32" if arquitectura else "")

    payload: Dict[str, Any] = {
        "equipo": {
            "nombreEquipo": hostname,
            "usuarioDominio": usuario_dominio,
            "modelo": _pc_value("get_computer_model"),
            "serialEquipo": _pc_value("get_serial_number"),
            "placaEquipo": "",
            "tipoProcesador": _pc_value("get_computer_processor"),
            "direccionIp": _pc_value("get_ip_address"),
            "puntoRed": "",
            "antivirus": _detect_antivirus() or "",
            "sistemaOperativo": so_nombre,
            "bitsSO": bits,
            "capacidadMemoria": _parse_memory_to_gb(_pc_value("get_total_memory")),
        },
        "componentesHardware": {
            "cpuMarca": _pc_value("get_computer_brand"),
            "cpuSerie": _pc_value("get_serial_number"),
            "cpuPlaca": "",
            "monitorMarca": "",
            "monitorSerie": "",
            "monitorPlaca": "",
            "tecladoMarca": "",
            "tecladoSerie": "",
            "tecladoPlaca": "",
            "mouseMarca": "",
            "mouseSerie": "",
            "mousePlaca": "",
        },
        "verificacionesTecnicas": [
            {"id": 1, "valor": True,  "detalle": "Acrobat Reader"},
            {"id": 2, "valor": _safe_call(aplicaciones.verificar_aplicaciones, False, "winrar"), "detalle": "WinRAR/ZIP"} if aplicaciones else {"id": 2, "valor": False, "detalle": ""},
            {"id": 3, "valor": bool(_detect_office()), "detalle": _detect_office() or ""},
            {"id": 4, "valor": bool(_detect_antivirus()), "detalle": _detect_antivirus() or ""},
            {"id": 6, "valor": True,  "detalle": _pc_value("is_dhcp_enabled")},
        ],
        "verificacionesUsuario": [
            {"id": 18, "valor": True, "detalle": "Conexión OK"},
            {"id": 22, "valor": True, "detalle": "Audio funcional"},
        ],
        "datosAdicionales": {
            "fecha": _to_iso_date(datetime.now().strftime("%d/%m/%Y")),
            "tecnicoDatic": usuario_dominio,
            "ticketNro": "",
            "monitorMarca": "", "monitorSerie": "", "monitorPlaca": "",
            "cpuMarca": _pc_value("get_computer_brand"),
            "cpuSerie": _pc_value("get_serial_number"),
            "cpuPlaca": "",
            "tecladoMarca": "", "tecladoSerie": "", "tecladoPlaca": "",
            "mouseMarca": "",   "mouseSerie": "",   "mousePlaca": "",
        },
    }

    if payload["equipo"].get("capacidadMemoria"):
        try:
            val = float(payload["equipo"]["capacidadMemoria"])
            payload["equipo"]["capacidadMemoria"] = int(round(val))
        except Exception:
            pass

    return payload

# =================== Endpoints utilitarios ===================

@app.get("/ping")
def ping():
    return {"ok": True, "ts": datetime.utcnow().isoformat()}

@app.get("/autofill")
def get_autofill() -> Dict[str, Any]:
    """Genera el JSON en caliente desde los módulos locales y lo devuelve (del SERVIDOR)."""
    return build_autofill_payload()

@app.post("/upload")
def upload_json(file: UploadFile = File(...)) -> Dict[str, Any]:
    """Sube un JSON y lo deja disponible para lectura posterior."""
    if not file.filename.lower().endswith(".json"):
        raise HTTPException(status_code=400, detail="Sólo se aceptan archivos .json")

    contents = file.file.read()
    try:
        data = json.loads(contents.decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=400, detail="JSON inválido")

    base = os.path.basename(file.filename)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    safe_name = f"{ts}-{re.sub(r'[^a-zA-Z0-9_.-]', '_', base)}"
    fpath = os.path.join(STORE_DIR, safe_name)

    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return {"ok": True, "filename": safe_name, "url": f"/files/{safe_name}"}

@app.get("/files")
def list_files() -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    for name in sorted(os.listdir(STORE_DIR)):
        if name.lower().endswith(".json"):
            out.append({"name": name, "url": f"/files/{name}"})
    return out

@app.get("/files/{name}")
def get_file(name: str):
    fpath = os.path.join(STORE_DIR, name)
    if not (os.path.isfile(fpath) and fpath.lower().endswith('.json')):
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    return FileResponse(fpath, media_type="application/json", filename=name)

# ========= (Opcional) Guardar a disco un snapshot del autofill =========
@app.post("/autofill/save")
def save_autofill(now: Optional[bool] = Query(True, description="Si True, genera y guarda un JSON nuevo")) -> Dict[str, Any]:
    data = build_autofill_payload() if now else {}
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    name = f"autofill-{ts}.json"
    path = os.path.join(STORE_DIR, name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return {"ok": True, "filename": name, "url": f"/files/{name}"}

# ========== (Opcional) Endpoints legacy: ejecutar EXE en el servidor ==========
# Mantén comentados para evitar confusión en el front:
# @app.post("/ejecutar-auditoria")
# def ejecutar_auditoria(): ...
# @app.post("/ejecutar-auditoria-json")
# def ejecutar_auditoria_json(): ...
