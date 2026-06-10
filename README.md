# Sistema de Registro y Control de Servicios en un Cementerio

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
