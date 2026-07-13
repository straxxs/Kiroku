# KIROKU

> Plataforma web colaborativa de apuntes para la Escuela Técnica Fragata Libertad N°21.

## Descripción

Kiroku es una plataforma desarrollada para que los estudiantes de la Escuela Técnica Fragata Libertad N°21 puedan subir, organizar y consultar apuntes de clase. Reemplaza el intercambio informal de material (WhatsApp, pendrives) centralizando todo en un repositorio único, seguro y estructurado.

## Características

### Funcionales
- **Registro e inicio de sesión** con nombre de usuario o email (bcrypt + JWT, rechaza usuarios bloqueados)
- **Recuperación de contraseña** por email
- **Subida de apuntes** (PDF, imágenes, videos, documentos) con drag & drop
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
- **Doodles animados** de fondo (íconos Lucide SVG)
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
- Botones con borde, estilo post-it, y efecto press

## Stack Tecnológico

| Componente | Tecnología |
|------------|-----------|
| Backend | Python 3.14.5 + Flask |
| Base de datos | MySQL / MariaDB 10.4.32 (XAMPP) |
| Autenticación | bcrypt (hash) + JWT (sesiones HTTP-only) |
| Frontend | HTML5, CSS3, JavaScript vanilla |
| Gráficos | Chart.js v4 |
| Audio | Web Audio API (sonidos generados en código) |
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
│   │   │   ├── apuntes.js      # CRUD apuntes, me gusta, guardados, lightbox
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
│   └── requirements.txt        # Dependencias Python
├── Documentación/              # Docs del proyecto (contrato, requerimientos, etc.)
└── README.md
```

## Instalación y Ejecución

### Prerrequisitos
- [Python 3.10+](https://www.python.org/)
- [XAMPP](https://www.apachefriends.org/) (MySQL/MariaDB)

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

4. Importar la base de datos:
   - Abrir phpMyAdmin → Importar → seleccionar `mitin.sql`

5. Ejecutar la aplicación:
   ```bash
   python app.py
   ```

6. Abrir en el navegador: `http://127.0.0.1:5000`

### Credenciales de prueba

| Usuario | Contraseña | Rol |
|---------|-----------|-----|
| testuser | 1234 | Moderador |
| testuser2 | 1234 | Administrador |
| federico | 1234 | Moderador |
| leon | 1234 | Alumno |

## Deploy en Render (Producción)

1. Crear cuenta gratis en [TiDB Cloud](https://tidbcloud.com), crear cluster Serverless y obtener el connection string
2. Importar `mitin.sql` en TiDB Cloud (consola Chat2Query)
3. Subir el código a GitHub
4. Crear cuenta en [Render](https://render.com) → New Web Service → conectar repo
5. Configurar:
   - **Build**: `pip install -r App/requirements.txt`
   - **Start**: `cd App && gunicorn wsgi:app`
   - **Env vars**: `DATABASE_URL` (connection string de TiDB), `FLASK_DEBUG=0`
6. Abrir la URL generada en el celu

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

- **León Veraldi Rita** (Líder técnico)
- Lucas Hamlin
- Vito Martin
- Matías Hayes
- Thiago Montenegro
- Ramiro Tatone
- Santino Moauro
- Federico Rojas
- Juan Pablo Santisi

## Licencia

Proyecto desarrollado para la Escuela Técnica Fragata Libertad N°21.
