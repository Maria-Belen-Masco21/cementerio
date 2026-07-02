from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from sqlalchemy import event
from sqlalchemy.engine import Engine
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, date
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')
os.makedirs(INSTANCE_DIR, exist_ok=True)

app = Flask(__name__, instance_relative_config=True)
app.config['SECRET_KEY'] = 'cementerio_secret_key_2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(INSTANCE_DIR, 'cementerio.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# Activa las restricciones de llave foranea en SQLite (vienen desactivadas
# por defecto) para que la integridad referencial se respete siempre.
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

# ============ MODELOS ============

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    nombre = db.Column(db.String(120), nullable=False)
    rol = db.Column(db.String(20), default='operador')
    activo = db.Column(db.Boolean, default=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ci = db.Column(db.String(20), unique=True, nullable=False)
    nombre_completo = db.Column(db.String(150), nullable=False)
    direccion = db.Column(db.String(200))
    telefono = db.Column(db.String(20))
    correo = db.Column(db.String(100))
    estado = db.Column(db.String(20), default='Activo')
    fallecidos = db.relationship('Fallecido', backref='cliente', lazy=True)
    servicios = db.relationship('Servicio', backref='cliente', lazy=True)


class Fallecido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    fecha_fallecimiento = db.Column(db.Date, nullable=False)
    causa_muerte = db.Column(db.String(200))
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    certificado_defuncion = db.Column(db.String(50))
    observaciones = db.Column(db.Text)
    servicios = db.relationship('Servicio', backref='fallecido', lazy=True)


class Nicho(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), unique=True, nullable=False)
    tipo = db.Column(db.String(50), nullable=False)
    ubicacion = db.Column(db.String(100))
    estado = db.Column(db.String(20), default='Disponible')
    observaciones = db.Column(db.Text)
    servicios = db.relationship('Servicio', backref='nicho', lazy=True)


class Servicio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    fallecido_id = db.Column(db.Integer, db.ForeignKey('fallecido.id'), nullable=False)
    nicho_id = db.Column(db.Integer, db.ForeignKey('nicho.id'))
    fecha_servicio = db.Column(db.Date, nullable=False)
    tipo_servicio = db.Column(db.String(50), nullable=False)
    costo = db.Column(db.Float, nullable=False)
    observaciones = db.Column(db.Text)
    pagos = db.relationship('Pago', backref='servicio', lazy=True)


class Pago(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    servicio_id = db.Column(db.Integer, db.ForeignKey('servicio.id'), nullable=False)
    fecha_pago = db.Column(db.Date, nullable=False)
    monto = db.Column(db.Float, nullable=False)
    metodo_pago = db.Column(db.String(50))
    estado = db.Column(db.String(20), default='Pendiente')
    observaciones = db.Column(db.Text)


# ============ DECORADORES ============

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# ============ RUTAS AUTH ============

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = Usuario.query.filter_by(username=username).first()
        if user and user.check_password(password) and user.activo:
            session['user_id'] = user.id
            session['username'] = user.username
            session['nombre'] = user.nombre
            session['rol'] = user.rol
            return redirect(url_for('dashboard'))
        flash('Usuario o contraseña incorrectos', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ============ DASHBOARD ============

@app.route('/dashboard')
@login_required
def dashboard():
    clientes = Cliente.query.count()
    fallecidos = Fallecido.query.count()
    servicios = Servicio.query.count()
    pagos_hoy = Pago.query.filter_by(fecha_pago=date.today()).count()
    return render_template('dashboard.html',
                           clientes=clientes,
                           fallecidos=fallecidos,
                           servicios=servicios,
                           pagos_hoy=pagos_hoy)


# ============ CLIENTES CRUD ============

@app.route('/clientes')
@login_required
def clientes():
    q = request.args.get('q', '')
    if q:
        lista = Cliente.query.filter(
            (Cliente.nombre_completo.ilike(f'%{q}%')) |
            (Cliente.ci.ilike(f'%{q}%'))
        ).all()
    else:
        lista = Cliente.query.all()
    return render_template('clientes.html', clientes=lista, q=q)

@app.route('/clientes/nuevo', methods=['GET', 'POST'])
@login_required
def cliente_nuevo():
    if request.method == 'POST':
        if Cliente.query.filter_by(ci=request.form['ci']).first():
            flash('Ya existe un cliente con ese CI', 'danger')
            return redirect(url_for('clientes'))
        c = Cliente(
            ci=request.form['ci'],
            nombre_completo=request.form['nombre_completo'],
            direccion=request.form.get('direccion'),
            telefono=request.form.get('telefono'),
            correo=request.form.get('correo'),
            estado=request.form.get('estado', 'Activo')
        )
        db.session.add(c)
        db.session.commit()
        flash('Cliente registrado correctamente', 'success')
        return redirect(url_for('clientes'))
    return render_template('cliente_form.html', cliente=None)

@app.route('/clientes/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def cliente_editar(id):
    c = Cliente.query.get_or_404(id)
    if request.method == 'POST':
        c.ci = request.form['ci']
        c.nombre_completo = request.form['nombre_completo']
        c.direccion = request.form.get('direccion')
        c.telefono = request.form.get('telefono')
        c.correo = request.form.get('correo')
        c.estado = request.form.get('estado', 'Activo')
        db.session.commit()
        flash('Cliente actualizado', 'success')
        return redirect(url_for('clientes'))
    return render_template('cliente_form.html', cliente=c)

@app.route('/clientes/eliminar/<int:id>', methods=['POST'])
@login_required
def cliente_eliminar(id):
    c = Cliente.query.get_or_404(id)
    if c.fallecidos or c.servicios:
        flash('No se puede eliminar: el cliente tiene fallecidos o servicios '
              'registrados a su nombre. Elimine o reasigne esos registros primero.', 'danger')
        return redirect(url_for('clientes'))
    db.session.delete(c)
    db.session.commit()
    flash('Cliente eliminado', 'warning')
    return redirect(url_for('clientes'))


# ============ FALLECIDOS CRUD ============

@app.route('/fallecidos')
@login_required
def fallecidos():
    q = request.args.get('q', '')
    if q:
        lista = Fallecido.query.filter(Fallecido.nombre.ilike(f'%{q}%')).all()
    else:
        lista = Fallecido.query.order_by(Fallecido.fecha_fallecimiento.desc()).all()
    return render_template('fallecidos.html', fallecidos=lista, q=q)

@app.route('/fallecidos/nuevo', methods=['GET', 'POST'])
@login_required
def fallecido_nuevo():
    clientes_lista = Cliente.query.filter_by(estado='Activo').all()
    if request.method == 'POST':
        f = Fallecido(
            nombre=request.form['nombre'],
            fecha_fallecimiento=datetime.strptime(request.form['fecha_fallecimiento'], '%Y-%m-%d').date(),
            causa_muerte=request.form.get('causa_muerte'),
            cliente_id=request.form['cliente_id'],
            certificado_defuncion=request.form.get('certificado_defuncion'),
            observaciones=request.form.get('observaciones')
        )
        db.session.add(f)
        db.session.commit()
        flash('Fallecido registrado', 'success')
        return redirect(url_for('fallecidos'))
    return render_template('fallecido_form.html', fallecido=None, clientes=clientes_lista)

@app.route('/fallecidos/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def fallecido_editar(id):
    f = Fallecido.query.get_or_404(id)
    clientes_lista = Cliente.query.filter_by(estado='Activo').all()
    if request.method == 'POST':
        f.nombre = request.form['nombre']
        f.fecha_fallecimiento = datetime.strptime(request.form['fecha_fallecimiento'], '%Y-%m-%d').date()
        f.causa_muerte = request.form.get('causa_muerte')
        f.cliente_id = request.form['cliente_id']
        f.certificado_defuncion = request.form.get('certificado_defuncion')
        f.observaciones = request.form.get('observaciones')
        db.session.commit()
        flash('Fallecido actualizado', 'success')
        return redirect(url_for('fallecidos'))
    return render_template('fallecido_form.html', fallecido=f, clientes=clientes_lista)

@app.route('/fallecidos/eliminar/<int:id>', methods=['POST'])
@login_required
def fallecido_eliminar(id):
    f = Fallecido.query.get_or_404(id)
    if f.servicios:
        flash('No se puede eliminar: este fallecido tiene servicios registrados. '
              'Elimine primero esos servicios.', 'danger')
        return redirect(url_for('fallecidos'))
    db.session.delete(f)
    db.session.commit()
    flash('Fallecido eliminado', 'warning')
    return redirect(url_for('fallecidos'))


# ============ NICHOS CRUD ============

@app.route('/nichos')
@login_required
def nichos():
    q = request.args.get('q', '')
    if q:
        lista = Nicho.query.filter(
            (Nicho.codigo.ilike(f'%{q}%')) | (Nicho.ubicacion.ilike(f'%{q}%'))
        ).all()
    else:
        lista = Nicho.query.all()
    return render_template('nichos.html', nichos=lista, q=q)

@app.route('/nichos/nuevo', methods=['GET', 'POST'])
@login_required
def nicho_nuevo():
    if request.method == 'POST':
        if Nicho.query.filter_by(codigo=request.form['codigo']).first():
            flash('Ya existe un nicho con ese código', 'danger')
            return redirect(url_for('nichos'))
        n = Nicho(
            codigo=request.form['codigo'],
            tipo=request.form['tipo'],
            ubicacion=request.form.get('ubicacion'),
            estado=request.form.get('estado', 'Disponible'),
            observaciones=request.form.get('observaciones')
        )
        db.session.add(n)
        db.session.commit()
        flash('Nicho registrado', 'success')
        return redirect(url_for('nichos'))
    return render_template('nicho_form.html', nicho=None)

@app.route('/nichos/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def nicho_editar(id):
    n = Nicho.query.get_or_404(id)
    if request.method == 'POST':
        n.codigo = request.form['codigo']
        n.tipo = request.form['tipo']
        n.ubicacion = request.form.get('ubicacion')
        n.estado = request.form.get('estado', 'Disponible')
        n.observaciones = request.form.get('observaciones')
        db.session.commit()
        flash('Nicho actualizado', 'success')
        return redirect(url_for('nichos'))
    return render_template('nicho_form.html', nicho=n)

@app.route('/nichos/eliminar/<int:id>', methods=['POST'])
@login_required
def nicho_eliminar(id):
    n = Nicho.query.get_or_404(id)
    if n.estado == 'Ocupado' or n.servicios:
        flash('No se puede eliminar: el nicho está ocupado o tiene servicios '
              'asociados en su historial.', 'danger')
        return redirect(url_for('nichos'))
    db.session.delete(n)
    db.session.commit()
    flash('Nicho eliminado', 'warning')
    return redirect(url_for('nichos'))


# ============ SERVICIOS CRUD ============

@app.route('/servicios')
@login_required
def servicios():
    q = request.args.get('q', '')
    if q:
        lista = Servicio.query.join(Fallecido).filter(Fallecido.nombre.ilike(f'%{q}%')).all()
    else:
        lista = Servicio.query.order_by(Servicio.fecha_servicio.desc()).all()
    return render_template('servicios.html', servicios=lista, q=q)

@app.route('/servicios/nuevo', methods=['GET', 'POST'])
@login_required
def servicio_nuevo():
    clientes_lista = Cliente.query.filter_by(estado='Activo').all()
    fallecidos_lista = Fallecido.query.all()
    nichos_lista = Nicho.query.filter_by(estado='Disponible').all()
    if request.method == 'POST':
        nicho_id = request.form.get('nicho_id') or None
        nicho_id = int(nicho_id) if nicho_id else None
        s = Servicio(
            cliente_id=request.form['cliente_id'],
            fallecido_id=request.form['fallecido_id'],
            nicho_id=nicho_id,
            fecha_servicio=datetime.strptime(request.form['fecha_servicio'], '%Y-%m-%d').date(),
            tipo_servicio=request.form['tipo_servicio'],
            costo=float(request.form['costo']),
            observaciones=request.form.get('observaciones')
        )
        if nicho_id:
            nicho = Nicho.query.get(nicho_id)
            if nicho:
                nicho.estado = 'Ocupado'
        db.session.add(s)
        db.session.commit()
        flash('Servicio registrado', 'success')
        return redirect(url_for('servicios'))
    return render_template('servicio_form.html', servicio=None,
                           clientes=clientes_lista, fallecidos=fallecidos_lista, nichos=nichos_lista)

@app.route('/servicios/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def servicio_editar(id):
    s = Servicio.query.get_or_404(id)
    clientes_lista = Cliente.query.all()
    fallecidos_lista = Fallecido.query.all()
    nichos_lista = Nicho.query.all()
    if request.method == 'POST':
        nuevo_nicho_id = request.form.get('nicho_id') or None
        nuevo_nicho_id = int(nuevo_nicho_id) if nuevo_nicho_id else None
        if nuevo_nicho_id != s.nicho_id:
            # Libera el nicho anterior (si tenía uno)
            if s.nicho_id:
                nicho_anterior = Nicho.query.get(s.nicho_id)
                if nicho_anterior:
                    nicho_anterior.estado = 'Disponible'
            # Ocupa el nuevo nicho (si se asignó uno)
            if nuevo_nicho_id:
                nicho_nuevo = Nicho.query.get(nuevo_nicho_id)
                if nicho_nuevo:
                    nicho_nuevo.estado = 'Ocupado'
        s.cliente_id = request.form['cliente_id']
        s.fallecido_id = request.form['fallecido_id']
        s.nicho_id = nuevo_nicho_id
        s.fecha_servicio = datetime.strptime(request.form['fecha_servicio'], '%Y-%m-%d').date()
        s.tipo_servicio = request.form['tipo_servicio']
        s.costo = float(request.form['costo'])
        s.observaciones = request.form.get('observaciones')
        db.session.commit()
        flash('Servicio actualizado', 'success')
        return redirect(url_for('servicios'))
    return render_template('servicio_form.html', servicio=s,
                           clientes=clientes_lista, fallecidos=fallecidos_lista, nichos=nichos_lista)

@app.route('/servicios/eliminar/<int:id>', methods=['POST'])
@login_required
def servicio_eliminar(id):
    s = Servicio.query.get_or_404(id)
    if s.pagos:
        flash('No se puede eliminar: este servicio tiene pagos registrados. '
              'Elimine primero esos pagos.', 'danger')
        return redirect(url_for('servicios'))
    if s.nicho_id:
        nicho = Nicho.query.get(s.nicho_id)
        if nicho:
            nicho.estado = 'Disponible'
    db.session.delete(s)
    db.session.commit()
    flash('Servicio eliminado', 'warning')
    return redirect(url_for('servicios'))


# ============ PAGOS CRUD ============

@app.route('/pagos')
@login_required
def pagos():
    q = request.args.get('q', '')
    lista = Pago.query.order_by(Pago.fecha_pago.desc()).all()
    return render_template('pagos.html', pagos=lista, q=q)

@app.route('/pagos/nuevo', methods=['GET', 'POST'])
@login_required
def pago_nuevo():
    servicios_lista = Servicio.query.all()
    if request.method == 'POST':
        p = Pago(
            servicio_id=request.form['servicio_id'],
            fecha_pago=datetime.strptime(request.form['fecha_pago'], '%Y-%m-%d').date(),
            monto=float(request.form['monto']),
            metodo_pago=request.form.get('metodo_pago'),
            estado=request.form.get('estado', 'Pendiente'),
            observaciones=request.form.get('observaciones')
        )
        db.session.add(p)
        db.session.commit()
        flash('Pago registrado', 'success')
        return redirect(url_for('pagos'))
    return render_template('pago_form.html', pago=None, servicios=servicios_lista)

@app.route('/pagos/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def pago_editar(id):
    p = Pago.query.get_or_404(id)
    servicios_lista = Servicio.query.all()
    if request.method == 'POST':
        p.servicio_id = request.form['servicio_id']
        p.fecha_pago = datetime.strptime(request.form['fecha_pago'], '%Y-%m-%d').date()
        p.monto = float(request.form['monto'])
        p.metodo_pago = request.form.get('metodo_pago')
        p.estado = request.form.get('estado', 'Pendiente')
        p.observaciones = request.form.get('observaciones')
        db.session.commit()
        flash('Pago actualizado', 'success')
        return redirect(url_for('pagos'))
    return render_template('pago_form.html', pago=p, servicios=servicios_lista)

@app.route('/pagos/eliminar/<int:id>', methods=['POST'])
@login_required
def pago_eliminar(id):
    p = Pago.query.get_or_404(id)
    db.session.delete(p)
    db.session.commit()
    flash('Pago eliminado', 'warning')
    return redirect(url_for('pagos'))


# ============ REPORTES ============

@app.route('/reportes')
@login_required
def reportes():
    return render_template('reportes.html')

@app.route('/reportes/clientes')
@login_required
def reporte_clientes():
    lista = Cliente.query.all()
    return render_template('reporte_clientes.html', clientes=lista, fecha=date.today())

@app.route('/reportes/nichos')
@login_required
def reporte_nichos():
    lista = Nicho.query.all()
    total = len(lista)
    disponibles = sum(1 for n in lista if n.estado == 'Disponible')
    ocupados = sum(1 for n in lista if n.estado == 'Ocupado')
    mausoleos = sum(1 for n in lista if n.tipo == 'Mausoleo')
    return render_template('reporte_nichos.html', nichos=lista, total=total,
                           disponibles=disponibles, ocupados=ocupados, mausoleos=mausoleos, fecha=date.today())

@app.route('/reportes/financiero')
@login_required
def reporte_financiero():
    mes = int(request.args.get('mes') or date.today().month)
    anio = int(request.args.get('anio') or date.today().year)
    pagos_mes = Pago.query.filter(
        db.extract('month', Pago.fecha_pago) == mes,
        db.extract('year', Pago.fecha_pago) == anio
    ).all()
    total_ingresos = sum(p.monto for p in pagos_mes if p.estado == 'Pagado')
    return render_template('reporte_financiero.html', pagos=pagos_mes,
                           total_ingresos=total_ingresos, mes=mes, anio=anio, fecha=date.today())

@app.route('/reportes/fallecidos')
@login_required
def reporte_fallecidos():
    lista = Fallecido.query.order_by(Fallecido.fecha_fallecimiento.desc()).all()
    return render_template('reporte_fallecidos.html', fallecidos=lista, fecha=date.today())


# ============ USUARIOS CRUD ============

@app.route('/usuarios')
@login_required
def usuarios():
    if session.get('rol') != 'admin':
        flash('Acceso denegado', 'danger')
        return redirect(url_for('dashboard'))
    lista = Usuario.query.all()
    return render_template('usuarios.html', usuarios=lista)

@app.route('/usuarios/nuevo', methods=['GET', 'POST'])
@login_required
def usuario_nuevo():
    if session.get('rol') != 'admin':
        flash('Acceso denegado', 'danger')
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        if Usuario.query.filter_by(username=request.form['username']).first():
            flash('El nombre de usuario ya existe', 'danger')
            return redirect(url_for('usuarios'))
        u = Usuario(
            username=request.form['username'],
            nombre=request.form['nombre'],
            rol=request.form.get('rol', 'operador'),
            activo=True
        )
        u.set_password(request.form['password'])
        db.session.add(u)
        db.session.commit()
        flash('Usuario creado', 'success')
        return redirect(url_for('usuarios'))
    return render_template('usuario_form.html', usuario=None)

@app.route('/usuarios/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def usuario_editar(id):
    if session.get('rol') != 'admin':
        flash('Acceso denegado', 'danger')
        return redirect(url_for('dashboard'))
    u = Usuario.query.get_or_404(id)
    if request.method == 'POST':
        u.username = request.form['username']
        u.nombre = request.form['nombre']
        u.rol = request.form.get('rol', 'operador')
        u.activo = 'activo' in request.form
        if request.form.get('password'):
            u.set_password(request.form['password'])
        db.session.commit()
        flash('Usuario actualizado', 'success')
        return redirect(url_for('usuarios'))
    return render_template('usuario_form.html', usuario=u)

@app.route('/usuarios/eliminar/<int:id>', methods=['POST'])
@login_required
def usuario_eliminar(id):
    if session.get('rol') != 'admin':
        flash('Acceso denegado', 'danger')
        return redirect(url_for('dashboard'))
    u = Usuario.query.get_or_404(id)
    if u.id == session.get('user_id'):
        flash('No puede eliminar su propio usuario mientras tiene una sesión activa.', 'danger')
        return redirect(url_for('usuarios'))
    db.session.delete(u)
    db.session.commit()
    flash('Usuario eliminado', 'warning')
    return redirect(url_for('usuarios'))


# ============ MANEJO DE ERRORES ============

@app.errorhandler(IntegrityError)
def handle_integrity_error(e):
    db.session.rollback()
    flash('No se pudo completar la operación porque el registro tiene datos '
          'relacionados en otras secciones del sistema.', 'danger')
    return redirect(request.referrer or url_for('dashboard'))

@app.errorhandler(404)
def handle_404(e):
    return render_template('error.html', codigo=404,
                           mensaje='La página que buscas no existe.'), 404

@app.errorhandler(500)
def handle_500(e):
    db.session.rollback()
    return render_template('error.html', codigo=500,
                           mensaje='Ocurrió un error interno en el servidor.'), 500


# ============ API AJAX ============

@app.route('/api/fallecidos_por_cliente/<int:cliente_id>')
@login_required
def fallecidos_por_cliente(cliente_id):
    lista = Fallecido.query.filter_by(cliente_id=cliente_id).all()
    return jsonify([{'id': f.id, 'nombre': f.nombre} for f in lista])


# ============ INICIALIZAR BD ============

def init_db():
    db.create_all()
    if not Usuario.query.filter_by(username='admin').first():
        admin = Usuario(username='admin', nombre='Administrador', rol='admin')
        admin.set_password('admin123')
        db.session.add(admin)

    if not Cliente.query.first():
        clientes_demo = [
            Cliente(ci='1234567', nombre_completo='Juan Pérez Gómez', direccion='Av. Los Andes #123', telefono='71234567', correo='juanperez@gmail.com', estado='Activo'),
            Cliente(ci='2345678', nombre_completo='María López Torres', direccion='Calle Sucre #456', telefono='72345678', correo='marialopez@gmail.com', estado='Activo'),
            Cliente(ci='3456789', nombre_completo='Carlos Fernández', direccion='Av. América #789', telefono='73456789', correo='cfernandez@gmail.com', estado='Activo'),
            Cliente(ci='4567890', nombre_completo='Ana Morales', direccion='Calle Junín #321', telefono='74567890', correo='anam@gmail.com', estado='Activo'),
            Cliente(ci='5678901', nombre_completo='Luis Ramírez', direccion='Av. Bolívar #654', telefono='75678901', correo='lramirez@gmail.com', estado='Activo'),
        ]
        for c in clientes_demo:
            db.session.add(c)
        db.session.flush()

        fallecidos_demo = [
            Fallecido(nombre='Pedro Sánchez López', fecha_fallecimiento=date(2024,5,12), causa_muerte='Paro Cardiaco', cliente_id=1, certificado_defuncion='CD-2024-1256'),
            Fallecido(nombre='María Flores Vda. de Ruiz', fecha_fallecimiento=date(2024,5,10), causa_muerte='Insuf. Respiratoria', cliente_id=2, certificado_defuncion='CD-2024-1255'),
            Fallecido(nombre='Carlos Díaz Romero', fecha_fallecimiento=date(2024,5,9), causa_muerte='Accidente Cerebrovascular', cliente_id=3, certificado_defuncion='CD-2024-1254'),
        ]
        for f in fallecidos_demo:
            db.session.add(f)
        db.session.flush()

        nichos_demo = [
            Nicho(codigo='N-001-01-01', tipo='Nicho Individual', ubicacion='Sección A - Fila 1 - Col 1', estado='Ocupado'),
            Nicho(codigo='N-001-01-02', tipo='Nicho Individual', ubicacion='Sección A - Fila 1 - Col 2', estado='Disponible'),
            Nicho(codigo='N-001-01-03', tipo='Nicho Individual', ubicacion='Sección A - Fila 1 - Col 3', estado='Disponible'),
            Nicho(codigo='N-002-01-04', tipo='Nicho Individual', ubicacion='Sección A - Fila 1 - Col 4', estado='Ocupado'),
            Nicho(codigo='M-001-01', tipo='Mausoleo', ubicacion='Sección B - Fila 1', estado='Disponible'),
        ]
        for n in nichos_demo:
            db.session.add(n)
        db.session.flush()

        servicios_demo = [
            Servicio(cliente_id=1, fallecido_id=1, nicho_id=1, fecha_servicio=date(2024,5,13), tipo_servicio='Inhumación', costo=1500.0, observaciones='Servicio completo'),
            Servicio(cliente_id=2, fallecido_id=2, nicho_id=4, fecha_servicio=date(2024,5,12), tipo_servicio='Cremación', costo=2000.0),
            Servicio(cliente_id=3, fallecido_id=3, nicho_id=None, fecha_servicio=date(2024,5,11), tipo_servicio='Inhumación', costo=1500.0),
        ]
        for s in servicios_demo:
            db.session.add(s)
        db.session.flush()

        pagos_demo = [
            Pago(servicio_id=1, fecha_pago=date(2024,5,13), monto=1500.0, metodo_pago='Efectivo', estado='Pagado', observaciones='Pago completo'),
            Pago(servicio_id=2, fecha_pago=date(2024,5,12), monto=2000.0, metodo_pago='Transferencia', estado='Pagado'),
            Pago(servicio_id=3, fecha_pago=date(2024,5,11), monto=1500.0, metodo_pago='Efectivo', estado='Pendiente'),
        ]
        for p in pagos_demo:
            db.session.add(p)

    db.session.commit()


if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=True)
