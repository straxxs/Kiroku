-- ============================================================
-- KIROKU · MIGRACIÓN: Transcripción OCR de apuntes manuscritos
-- Archivo: migracion_ocr.sql
-- Idempotente: se puede ejecutar más de una vez.
-- ============================================================

USE `apuntes_db`;

START TRANSACTION;

-- Guarda el texto que la IA de OCR (Ollama + minicpm-v) leyó de cada
-- imagen subida. NULL mientras no se subió imagen, o mientras la
-- transcripción todavía no terminó (se genera en segundo plano).
ALTER TABLE `archivo_apunte`
  ADD COLUMN IF NOT EXISTS `texto_transcripto` TEXT DEFAULT NULL AFTER `tipo`;

COMMIT;

-- Verificación
SHOW COLUMNS FROM `archivo_apunte` LIKE 'texto_transcripto';