/**
 * Helper de fetch que NUNCA enmascara errores.
 * Distingue: red caída / error HTTP / respuesta no-JSON.
 */
async function pedirJSON(url, opciones = {}) {
    let res;
    try {
        res = await fetch(url, { credentials: "same-origin", ...opciones });
    } catch (err) {
        console.error("[api] Fallo de red:", url, err);
        throw new ErrorApi("No se pudo conectar con el servidor.", 0, err);
    }

    const texto = await res.text();
    let data = null;
    try {
        data = texto ? JSON.parse(texto) : null;
    } catch {
        // El servidor devolvió HTML (típico de un 500 con debug=on)
        console.error(`[api] Respuesta no-JSON (${res.status}) de ${url}:\n`,
                      texto.slice(0, 800));
        throw new ErrorApi(
            res.ok ? "El servidor devolvió una respuesta inesperada."
                   : `Error ${res.status} del servidor. Revisá la consola de Flask.`,
            res.status
        );
    }

    if (!res.ok) {
        const msg = (data && data.mensaje) || `Error ${res.status}`;
        console.warn(`[api] HTTP ${res.status} en ${url}:`, msg);
        throw new ErrorApi(msg, res.status, null, data);
    }
    return data;
}

class ErrorApi extends Error {
    constructor(mensaje, status = 0, causa = null, data = null) {
        super(mensaje);
        this.name = "ErrorApi";
        this.status = status;
        this.causa = causa;
        this.data = data;
    }
}

/** Muestra el error real (no un genérico) y lo loguea completo. */
function reportarError(err, contexto = "") {
    console.error(`[${contexto || "app"}]`, err);
    const msg = (err instanceof ErrorApi)
        ? err.message
        : `Error inesperado: ${err.message}`;
    if (typeof mostrarToast === "function") mostrarToast(msg, "error");
    return msg;
}

window.pedirJSON = pedirJSON;
window.ErrorApi = ErrorApi;
window.reportarError = reportarError;