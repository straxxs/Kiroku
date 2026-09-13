"""
Transcripción de manuscrita para apuntes de KIROKU.

Usa un modelo de visión corriendo localmente vía Ollama (minicpm-v),
en vez de librerías pesadas de Python (torch/transformers) — solo
depende de 'requests', así que no complica la instalación del resto
del equipo.

Requisitos en la máquina de cada desarrollador (ver setup.ps1):
    1. Ollama instalado y corriendo (http://localhost:11434)
    2. Modelo descargado: ollama pull minicpm-v

Esto NO se deployea a producción (Render) — es solo para uso local
del equipo mientras desarrollan/prueban.
"""
import re
import base64
import requests

URL_OLLAMA = "http://localhost:11434/api/generate"
MODELO = "minicpm-v"
TIMEOUT_SEGUNDOS = 120

PROMPT_TRANSCRIPCION = (
    "Transcribe todo el texto manuscrito que aparece en esta imagen, "
    "exactamente como está escrito, palabra por palabra, respetando "
    "los saltos de línea originales. Devolvé ÚNICAMENTE el texto "
    "transcripto, tal cual aparece en la imagen. No agregues títulos, "
    "subtítulos, notas, aclaraciones, comentarios, ni ningún texto "
    "que no esté escrito literalmente en la imagen. No uses formato "
    "markdown ni asteriscos."
)


def _limpiar(texto):
    """Saca etiquetas tipo '**Título:**' que el modelo a veces agrega
    aunque el prompt le pida que no lo haga."""
    texto = re.sub(r"^\s*\*\*[^*\n]+\*\*:?\s*", "", texto, flags=re.MULTILINE)
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip().strip('"\'')


def transcribir(ruta_absoluta):
    """
    Transcribe el texto manuscrito de una imagen.

    Parámetros:
        ruta_absoluta: ruta completa en disco de la imagen ya guardada.

    Devuelve:
        str con el texto transcripto, o None si Ollama no está
        disponible / el modelo no está descargado (falla silenciosa,
        pensada para no romper la subida del apunte).
    """
    try:
        with open(ruta_absoluta, "rb") as f:
            imagen_base64 = base64.b64encode(f.read()).decode("utf-8")

        respuesta = requests.post(
            URL_OLLAMA,
            json={
                "model": MODELO,
                "prompt": PROMPT_TRANSCRIPCION,
                "images": [imagen_base64],
                "stream": False,
                "options": {"temperature": 0},
            },
            timeout=TIMEOUT_SEGUNDOS,
        )
        if respuesta.status_code != 200:
            print(f"[transcriptor] Ollama devolvió {respuesta.status_code}: {respuesta.text[:200]}")
            return None

        texto = respuesta.json().get("response", "")
        return _limpiar(texto) or None

    except requests.exceptions.ConnectionError:
        print("[transcriptor] No se pudo conectar a Ollama (¿está corriendo? "
              "ver setup.ps1). Se omite la transcripción de esta imagen.")
        return None
    except Exception as e:
        print(f"[transcriptor] Error al transcribir: {e}")
        return None


def transcribir_y_guardar(id_archivo, ruta_absoluta):
    """
    Pensada para correr en un hilo aparte (threading.Thread), llamada
    desde app.py justo después de guardar una imagen subida. Transcribe
    y guarda el resultado en la BD sin bloquear la respuesta al usuario.
    """
    # Import acá adentro (no arriba del archivo) para evitar import
    # circular entre apuntes.py y transcriptor.py.
    from modulos.apuntes import actualizar_texto_transcripto

    texto = transcribir(ruta_absoluta)
    if texto:
        actualizar_texto_transcripto(id_archivo, texto)
