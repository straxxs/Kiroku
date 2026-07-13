// ---------- Efectos de sonido (Web Audio API, sin archivos) ----------
const _audioCtx = new (window.AudioContext || window.webkitAudioContext)();

function _playTone(freq, dur, type, vol) {
    const osc = _audioCtx.createOscillator();
    const gain = _audioCtx.createGain();
    osc.type = type;
    osc.frequency.setValueAtTime(freq, _audioCtx.currentTime);
    gain.gain.setValueAtTime(vol, _audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, _audioCtx.currentTime + dur);
    osc.connect(gain);
    gain.connect(_audioCtx.destination);
    osc.start();
    osc.stop(_audioCtx.currentTime + dur);
}

function sonidoPop() {
    _playTone(800, 0.1, "sine", 0.15);
    setTimeout(() => _playTone(1200, 0.06, "sine", 0.1), 30);
}

function sonidoLike() {
    _playTone(523, 0.08, "sine", 0.12);
    setTimeout(() => _playTone(784, 0.1, "sine", 0.12), 60);
    setTimeout(() => _playTone(1047, 0.12, "sine", 0.08), 120);
}

function sonidoEnviar() {
    _playTone(440, 0.08, "triangle", 0.1);
    setTimeout(() => _playTone(660, 0.1, "triangle", 0.08), 70);
}

function sonidoExito() {
    _playTone(523, 0.1, "sine", 0.1);
    setTimeout(() => _playTone(659, 0.1, "sine", 0.1), 80);
    setTimeout(() => _playTone(784, 0.15, "sine", 0.1), 160);
}

function sonidoError() {
    _playTone(300, 0.15, "sawtooth", 0.06);
    setTimeout(() => _playTone(200, 0.2, "sawtooth", 0.04), 100);
}

function sonidoHover() {
    _playTone(600, 0.03, "sine", 0.02);
}

(function () {
    let _lastHover = 0;
    let _lastEl = null;
    document.addEventListener("mouseover", function (e) {
        const el = e.target.closest("a, button, .btn, .btn-megusta, .perfil-avatar");
        if (!el || el === _lastEl) return;
        _lastEl = el;
        const now = performance.now();
        if (now - _lastHover < 80) return;
        _lastHover = now;
        if (typeof sonidoHover === "function") sonidoHover();
    });
    document.addEventListener("mouseout", function (e) {
        const el = e.target.closest("a, button, .btn, .btn-megusta, .perfil-avatar");
        if (el && !el.contains(e.relatedTarget)) _lastEl = null;
    });
})();
