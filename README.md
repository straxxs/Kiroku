# KIROKU

> Plataforma web colaborativa de apuntes para la Escuela Técnica Fragata Libertad N°21.

## Descripción

Kiroku es una plataforma desarrollada para que los estudiantes de la Escuela Técnica Fragata Libertad N°21 puedan subir, organizar y consultar apuntes de clase. Reemplaza el intercambio informal de material (WhatsApp, pendrives) centralizando todo en un repositorio único, seguro y estructurado.

## Características

### Funcionales
- **Registro e inicio de sesión** con nombre de usuario o email (bcrypt + JWT)
- **Recuperación de contraseña** por email
- **Subida de apuntes** (PDF, imágenes, videos, documentos) con drag & drop
- **Transcripción automática de apuntes manuscritos** con IA (ver sección dedicada más abajo)
- **Búsqueda avanzada** por materia, fecha, autor y palabras clave
- **Descarga de archivos** directa
- **Vista previa de archivos** en apuntes (imágenes, PDF embebido, video)
- **Valoraciones** con sistema de estrellas (1-5) y botón "Me Gusta"
- **Sistema de guardados** para apuntes favoritos
- **Aprobación de contenido** por moderadores (pendiente → aprobado/rechazado)
- **Panel de administración**: gestión de usuarios (bloquear/activar, asignar roles)
- **Dashboard de estadísticas** con gráficos (Chart.js): métricas, ranking de colaboradores
- **Estadísticas por curso**: resumen, heatmap de actividad, ranking de colaboradores, top valorados
- **Sistema de auditoría** (logs con usuario, acción, timestamp)
- **Perfiles** con selección de avatar e información del curso
- **Código de invitación** para unirse a cursos (formato XXXX-XXXX)
- **Modales custom** (kirokuConfirm / kirokuEdit) con estilo post-it
- **Efectos de sonido** sutiles (Web Audio API) en interacciones clave
- **Doodles animados** de fondo (emoji flotantes)
- **Diseño responsive** optimizado para móvil

### Roles
| Rol | Permisos |
|-----|----------|
| Alumno | Subir apuntes, buscar, valorar, descargar, guardar |
| Moderador | Aprobar/rechazar contenido, gestionar materias de su curso, ver estadísticas del curso |
| Administrador | Gestión total de usuarios, roles y estadísticas |

### Estética visual
- Diseño **post-it** con papel de fondo, cintas adhesivas y sombras
- Tipografías **Kalam** (headings) + **Nunito** (body)
- Paleta: celeste, amarillo, verde, rojo, violeta
- Botones con borde, rotación sutil, y efecto press

## Transcripción automática de apuntes (IA)

Cuando alguien sube una foto de un apunte manuscrito, Kiroku intenta leer el texto automáticamente y lo deja disponible debajo de la imagen (con un desplegable "Ver texto transcripto"). Esto corre de forma **asíncrona**: el apunte se sube y aparece al instante como siempre, y la transcripción se completa sola en segundo plano unos segundos después, sin que nadie tenga que esperar.

Para que esto funcione hace falta [Ollama](https://ollama.com) corriendo en tu compu, con el modelo `minicpm-v` descargado — es la IA que efectivamente "lee" la imagen. Es gratis y corre 100% local, sin mandar nada a internet.

**Esto es solo para desarrollo/uso local**, no está pensado para el deploy en Render: cada persona que clona el repo la tiene disponible en su propia máquina si sigue el paso de instalación de Ollama de más abajo. Si no la instalás, no pasa nada grave — Kiroku funciona igual, simplemente esa imagen se queda sin transcripción.

## Stack Tecnológico

| Componente | Tecnología |
|------------|-----------|
| Backend | Python 3.14.5 + Flask |
| Base de datos | MySQL / MariaDB 10.4.32 (XAMPP) |
| Autenticación | bcrypt (hash) + JWT (sesiones HTTP-only) |
| Frontend | HTML5, CSS3, JavaScript vanilla |
| Gráficos | Chart.js v4 |
| Audio | Web Audio API (sonidos generados en código) |
| IA de transcripción | Ollama + minicpm-v (local, opcional, solo desarrollo) |
| Servidor | Flask dev server / Gunicorn (producción) |
| Hosting | Render (producción) + TiDB Cloud Serverless (DB) |

## Estructura del Proyecto

```
Proyecto Mitingay/
├── App/
│   ├── app.py                  # Rutas principales (Flask)
│   ├── wsgi.py                 # Entry point para Gunicorn (Render)
│   ├── db/
│   │   └── conexion.py         # Conexión a MySQL (soporta DATABASE_URL)
│   ├── modulos/
│   │   ├── auth.py             # Registro, login, JWT, bcrypt
│   │   ├── usuarios.py         # CRUD usuarios, roles, estado, ascender/descender
│   │   ├── cursos.py           # CRUD cursos, códigos de invitación
│   │   ├── materias.py         # CRUD materias
│   │   ├── apuntes.py          # CRUD apuntes y archivos
│   │   ├── transcriptor.py     # Transcripción OCR de manuscrita (IA vía Ollama)
│   │   ├── valoraciones.py     # Estrellas, guardados, me gusta
│   │   ├── busqueda.py         # Búsqueda avanzada
│   │   ├── estadisticas.py     # Métricas, rankings, stats por curso
│   │   ├── recuperacion.py     # Tokens de recuperación
│   │   ├── validacion.py       # Validación de contraseña, usuario, email
│   │   ├── auditoria.py        # Logs de auditoría
│   │   └── profesores.py       # Gestión de profesores
│   ├── templates/              # HTML (Jinja2)
│   ├── static/
│   │   ├── css/
│   │   │   ├── styles.css      # Estilos base (login, registro, home)
│   │   │   └── panel.css       # Estilos del panel (post-it, cards, heatmap, responsive)
│   │   ├── js/
│   │   │   ├── apuntes.js      # CRUD apuntes, me gusta, guardados, lightbox, transcripción
│   │   │   ├── curso.js        # Gestión de curso, alumnos, pendientes, previews
│   │   │   ├── home.js         # Unirse/crear curso, salir
│   │   │   ├── admin.js        # Panel de administración
│   │   │   ├── busqueda.js     # Búsqueda avanzada
│   │   │   ├── modal.js        # kirokuConfirm() y kirokuEdit()
│   │   │   ├── sounds.js       # Efectos de sonido (Web Audio API)
│   │   │   ├── toast.js        # Notificaciones toast
│   │   │   ├── avatar.js       # Selección de avatar + escapeHtml
│   │   │   ├── topbar.js       # Dropdown del perfil
│   │   │   └── ...             # Otros módulos JS
│   │   ├── img/
│   │   │   └── logo.png        # Logo KIROKU
│   │   └── uploads/            # Avatares y archivos subidos
│   ├── mitin.sql               # Script de inicialización de DB
│   ├── migracion_ocr.sql       # Migración: columna de texto transcripto
│   └── requirements.txt        # Dependencias Python
├── Documentación/              # Docs del proyecto (contrato, requerimientos, etc.)
└── README.md
```

## Instalación y Ejecución

### Prerrequisitos
- [Python 3.10+](https://www.python.org/)
- [XAMPP](https://www.apachefriends.org/) (MySQL/MariaDB)
- [Ollama](https://ollama.com) — opcional, solo si querés que funcione la transcripción de apuntes manuscritos

### Pasos

1. Clonar el repositorio:
   ```bash
   git clone https://github.com/straxxs/Apuntec.git
   cd Apuntec/App
   ```

2. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

3. Iniciar MySQL (desde XAMPP Control Panel).

4. Importar la base de datos — son varios archivos porque el proyecto fue creciendo de a etapas, y cada uno depende del anterior, así que hay que correrlos **en este orden** (todos son idempotentes: si por error corrés uno dos veces, no rompe nada):
   - Abrir phpMyAdmin → Importar → `mitin.sql` (la base con las tablas originales y los datos de prueba)
   - `migracion.sql` (agrega el login por email y la auditoría)
   - `migracion_sin_likes.sql` (pasa el sistema a multi-curso y saca los "me gusta")
   - `migracion_comentarios.sql` (agrega los comentarios en los apuntes)
   - `migracion_gamificacion.sql` (XP, niveles y logros — necesita que ya estén corridas las dos anteriores)
   - `migracion_calendario.sql` (calendario académico — también necesita las anteriores)
   - `migracion_ocr.sql` (agrega dónde se guarda el texto transcripto por IA — este es el único paso ligado a la funcionalidad nueva de este README)

5. Si querés que la transcripción de apuntes manuscritos funcione, instalá Ollama y bajate el modelo que usamos:
   - Descargalo de [ollama.com](https://ollama.com) e instalalo como cualquier programa (en Windows también podés correr `irm https://ollama.com/install.ps1 | iex` desde PowerShell)
   - Una vez instalado, corré `ollama pull minicpm-v` en una terminal (pesa unos 5GB, así que puede tardar un rato la primera vez)
   - Este paso es opcional: si no lo hacés, Kiroku funciona igual, simplemente los apuntes con imagen no van a tener el texto transcripto

6. Ejecutar la aplicación:
   ```bash
   python app.py
   ```

7. Abrir en el navegador: `http://127.0.0.1:5000`

### Credenciales de prueba

| Usuario | Contraseña | Rol |
|---------|-----------|-----|
| testuser | 1234 | Moderador |
| testuser2 | 1234 | Administrador |
| federico | 1234 | Moderador |
| leon | 1234 | Alumno |

## Deploy en Render (Producción)

1. Crear cuenta gratis en [TiDB Cloud](https://tidbcloud.com), crear cluster Serverless y obtener el connection string
2. Importar en TiDB Cloud (consola Chat2Query) `mitin.sql` y las migraciones correspondientes, en el mismo orden que en la instalación local — **menos `migracion_ocr.sql`**, que es la única ligada a la transcripción con IA y no hace falta en producción (aunque tampoco molesta si se corre, la columna simplemente queda sin usar)
3. Subir el código a GitHub
4. Crear cuenta en [Render](https://render.com) → New Web Service → conectar repo
5. Configurar:
   - **Build**: `pip install -r App/requirements.txt`
   - **Start**: `cd App && gunicorn wsgi:app`
   - **Env vars**: `DATABASE_URL` (connection string de TiDB), `FLASK_DEBUG=0`
6. Abrir la URL generada en el celu

> Nota: la transcripción con IA (Ollama) no está pensada para correr en Render — es una funcionalidad de desarrollo local. En producción, esa parte simplemente queda inactiva y el resto de Kiroku funciona con normalidad.

## Requerimientos Cubiertos

| ID | Requerimiento | Estado |
|----|--------------|--------|
| RF-01 | Registro de usuario | ✅ |
| RF-02 | Inicio de sesión | ✅ |
| RF-03 | Recuperación de contraseña | ✅ (simulado) |
| RF-04 | Subir apuntes | ✅ |
| RF-05 | Buscar y filtrar | ✅ |
| RF-06 | Descargar apuntes | ✅ |
| RF-07 | Valorar apuntes | ✅ |
| RF-08 | Aprobar contenido | ✅ |
| RF-09 | Gestionar usuarios | ✅ |
| RF-10 | Ver estadísticas | ✅ |
| RNF-01 | Respuesta < 3s | ✅ |
| RNF-02 | bcrypt + JWT | ✅ |
| RNF-08 | Auditoría / trazabilidad | ✅ |

## Equipo

- **Matías Hayes** (Líder técnico)
- Lucas Hamlin
- Vito Martin
- Thiago Montenegro
- Ramiro Tatone
- Santino Moauro
- Federico Rojas
- Juan Pablo Santisi

## Licencia

Proyecto desarrollado para la Escuela Técnica Fragata Libertad N°21.