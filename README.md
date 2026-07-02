# Sistema de Registro y Control de Servicios en un Cementerio

## Novedades de esta revisión
Esta versión corrige errores funcionales y moderniza el diseño:

**Bugs corregidos**
- Eliminar un **cliente**, **fallecido** o **servicio** que tuviera registros
  dependientes (fallecidos, servicios o pagos asociados) provocaba un error
  interno del servidor (Error 500). Ahora el sistema lo detecta y muestra un
  mensaje claro explicando por qué no se puede eliminar.
- Al editar un servicio y cambiarle el nicho asignado, el nicho anterior se
  quedaba marcado como "Ocupado" para siempre y el nuevo no se marcaba. Ahora
  el estado de los nichos se sincroniza automáticamente al crear, editar o
  eliminar un servicio.
- El selector de "Fallecido" en el formulario de Servicios mostraba a todos
  los fallecidos del sistema en vez de solo los del cliente elegido (el
  endpoint de la API existía pero no se usaba). Ahora se filtra en tiempo
  real al seleccionar el cliente.
- El reporte financiero no convertía correctamente el mes/año recibidos por
  la URL a número.
- La base de datos no se guardaba realmente en `instance/` como decía este
  documento; ahora sí.
- Se activaron las restricciones de llave foránea de SQLite y se agregó un
  manejador de errores global (páginas 404 / 500 personalizadas) como red de
  seguridad ante cualquier caso no previsto.
- Un administrador podía eliminar su propio usuario mientras tenía la sesión
  abierta; ahora está bloqueado.
- No se puede eliminar un nicho que esté ocupado o que tenga servicios en su
  historial.

**Diseño**
- Nueva paleta moderna (verde bosque + dorado) con tipografía Poppins/Inter.
- Sidebar, tarjetas y botones con bordes redondeados, sombras suaves y
  animaciones sutiles al pasar el mouse.
- Nuevo "modo cementerio": una escena nocturna ilustrada (luna, estrellas,
  niebla y siluetas de cruces/lápidas/cipreses), construida en SVG/CSS puro
  para que nunca se rompa por depender de una imagen externa. Se usa en la
  pantalla de inicio de sesión, en el banner de bienvenida del dashboard y
  en las páginas de error.

## Requisitos
- Python 3.8 o superior

## Instalación y ejecución

### 1. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 2. Ejecutar la aplicación
```bash
python app.py
```

### 3. Abrir en el navegador
```
http://localhost:5000
```

## Credenciales por defecto
- **Usuario:** admin
- **Contraseña:** admin123

## Módulos del sistema
- **Clientes** — Registro y gestión de clientes/familiares
- **Fallecidos** — Registro de personas fallecidas
- **Nichos** — Gestión de nichos, mausoleos y osarios
- **Servicios** — Inhumaciones, cremaciones y otros servicios
- **Pagos** — Control de pagos y estados
- **Reportes** — Clientes, Nichos, Financiero, Fallecidos
- **Usuarios** — Gestión de usuarios del sistema (solo admin)

## Base de datos
La base de datos SQLite se crea automáticamente en: `instance/cementerio.db`
Se cargan datos de demostración al iniciar por primera vez.

## Estructura de archivos
```
cementerio/
├── app.py                  # Aplicación principal Flask
├── requirements.txt        # Dependencias
├── static/
│   └── css/
│       └── style.css       # Estilos personalizados
└── templates/
    ├── base.html           # Plantilla base con sidebar
    ├── login.html          # Pantalla de inicio de sesión
    ├── dashboard.html      # Panel principal
    ├── clientes.html       # Lista de clientes
    ├── cliente_form.html   # Formulario cliente
    ├── fallecidos.html     # Lista de fallecidos
    ├── fallecido_form.html # Formulario fallecido
    ├── nichos.html         # Lista de nichos
    ├── nicho_form.html     # Formulario nicho
    ├── servicios.html      # Lista de servicios
    ├── servicio_form.html  # Formulario servicio
    ├── pagos.html          # Lista de pagos
    ├── pago_form.html      # Formulario pago
    ├── reportes.html       # Menú de reportes
    ├── reporte_clientes.html
    ├── reporte_nichos.html
    ├── reporte_financiero.html
    ├── reporte_fallecidos.html
    ├── usuarios.html       # Lista de usuarios
    └── usuario_form.html   # Formulario usuario
```
