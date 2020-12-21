from flask import Flask, render_template, request, redirect, url_for
import yagmail
import utils
from flask_sqlalchemy import SQLAlchemy

from flask_bcrypt import Bcrypt

# Para iniciar sesión
from flask_login import LoginManager, login_user, current_user, logout_user, login_required, UserMixin

import secrets, os

from PIL import Image

# imports para formularios
from flask_wtf import FlaskForm

from wtforms import StringField, PasswordField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
#import os
#from werkzeug import secure_filename

app = Flask(__name__)
#app.config['UPLOAD_FOLDER'] = './static/images'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///databases/brioche.db'
app.config['SECRET_KEY'] = 'ABCDEFGHI'
db = SQLAlchemy(app)
bcrypt = Bcrypt()

login_manager = LoginManager(app)

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

class Usuario(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key = True)
    nombreUsuario = db.Column(db.String(30), nullable=False)
    apellidoUsuario = db.Column(db.String(30), nullable=False)
    correoElectronico = db.Column(db.String(30), nullable=False, unique=True)
    password = db.Column(db.String(30), nullable=False)
    rolUsuario = db.Column(db.String(30), nullable=False)

    def __repr__(self):
        return f"id:{self.idUsuario}, nombre:{self.nombreUsuario}, password:{self.password}" 

class Producto(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    imagenProducto = db.Column(db.String(500), default="default.jpg")
    nombreProducto = db.Column(db.String(20), nullable=False)
    precioProducto = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"id:{self.idProducto}, nombre:{self.precioProducto}"

# idOrdenItem idProducto Cantidad ValorUnidad SubTotal

# un OrdenItem esta asociado con una Orden
class OrdenItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    orden_id = db.Column(db.Integer, db.ForeignKey("orden.id"), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey("producto.id"), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    valor_unidad = db.Column(db.Integer, nullable=False)
    subtotal = db.Column(db.Integer, nullable=False)

# Una Orden tiene varios items en el atributo items
class Orden(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    nombreCliente = db.Column(db.String(30))
    items = db.relationship("OrdenItem", backref="orden")
    total = db.Column(db.Integer)
    

# Formularios
class FormularioRegistro(FlaskForm):
    nombre = StringField("Nombre", validators=[DataRequired(), Length(min=2, max=30)])
    apellido = StringField("Apellido", validators=[DataRequired(), Length(min=2, max=30)])
    correo = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Contraseña", validators=[DataRequired(), Length(min=8, max=30)])
    password2 = PasswordField("Confirme su contraseña", validators=[DataRequired(), EqualTo("password")])
    rol= SelectField('Rol', choices=[('Administrador','Administrador'),('Cajero','Cajero'), ('Propietario','Propietario')])
    registrar = SubmitField("Registrar")

    def validate_correo(self, correo):
        user = Usuario.query.filter_by(correoElectronico=correo.data).first()
        if user:
            raise ValidationError(
                "Sorry, that email already exists, please use a different one"
            )
    
class FormularioInicioSesion(FlaskForm):
   
    correo = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Contraseña", validators=[DataRequired(), Length(min=8, max=30)])
    
    ingresar = SubmitField("Ingresar")
    

def home():
    return render_template('home.html')

@app.route('/recuperarcontraseña')
def recuperarcontrasena():
    return render_template('')
#@app.route('/recuperarcontrasena/<correoElectronico>', methods = ['POST'])
#def recuperarcontrasena(correoElectronico):
    #usuario = Usuario.query.filter_by(correoElectronico = correoElectronico)).first()
    #if utils.isEmailValid(correoElectronico):
    #    if utils.isUsernameValid()
#    return 0

#Acceso y Funciones del Administrador

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    # As the file name won't be used, that variable is called _
    _, f_ext = os.path.splitext(form_picture.filename)
    # New picture filename
    picture_fn = random_hex + f_ext
    # Define picture path
    # ============= Si es en linux usar /, si es en windows usar \ ===================
    picture_path = os.path.join(app.root_path, "static/images/products_pics", picture_fn)
    
    i = Image.open(form_picture)
    
    # Save picture
    i.save(picture_path)
    return picture_fn


@app.route('/agregarProductos', methods = ['GET','POST'])
def agregarProductos():
    productos = Producto.query.all()
#    filename = secure_filename(imagenProducto.filename)
    if request.method == "POST":
        nombreProducto = request.form['nombreProducto']
        precioProducto = request.form['precioProducto']
        imagenProducto = request.files['imagenProducto']
        if imagenProducto:
            imagenRuta = save_picture(imagenProducto)
            producto = Producto(nombreProducto = nombreProducto, imagenProducto = imagenRuta, precioProducto = precioProducto)
        else:
            producto = Producto(nombreProducto = nombreProducto, precioProducto = precioProducto)

        db.session.add(producto)
        db.session.commit()
        return redirect(url_for('agregarProductos'))
    return render_template('agregarProductos.html', productos=productos)

@app.route('/eliminarProducto/<idProducto>')
def eliminarProducto(idProducto):
    Producto.query.filter_by(idProducto = int(idProducto)).delete()
    db.session.commit()
    return redirect(url_for('agregarProductos'))

@app.route('/editarproducto/<idProducto>', methods = ['GET', 'POST'])
def editarProducto(idProducto):
    producto = Producto.query.get_or_404(idProducto)
    if request.method == 'POST':
        producto.nombreProducto = request.form['nombreProducto']
        producto.precioProducto = request.form['precioProducto']
        if request.files['imagenProducto']:
            imagenProducto = request.files['imagenProducto']
            imagenRuta = save_picture(imagenProducto)
            producto.imagenProducto = imagenRuta
        
        db.session.commit()
        
        return redirect(url_for('agregarProductos'))

    return render_template('editarproducto.html', producto = producto)



#Interfaz de Cajero
@app.route('/catalogo', methods=["GET", "POST"])
def catalogo():
    productos = Producto.query.all()

    if request.method=="POST":

        cont = 0
        for producto in productos:
            if int(request.form[producto.nombreProducto])==0:
                cont +=1
        if cont != len(productos):
            orden = Orden()
            db.session.add(orden)
            db.session.commit()

            orden = Orden.query.order_by(Orden.id.desc()).first()
            
            for producto in productos:
                cantidad = int(request.form[producto.nombreProducto])
                if cantidad > 0:
                    item = OrdenItem(orden_id=orden.id,
                                        producto_id=producto.id,
                                        cantidad=cantidad,
                                        valor_unidad=producto.precioProducto,
                                        subtotal = cantidad * producto.precioProducto)

                    db.session.add(item)
                    db.session.commit()
            
            total = 0

            if len(orden.items) > 0:
                for item in orden.items:
                    total += item.subtotal
            
            orden.total = total
            db.session.commit()
            return render_template('registrocajero.html', productos=productos, total=total)
       
        
        return redirect(url_for('catalogo'))
        
    return render_template('registrocajero.html', productos=productos, total=0)



# Ruta de registro
@app.route('/registro', methods=["GET", "POST"])
def registro():
    if current_user.is_authenticated and current_user.rolUsuario == "Cajero":
        return redirect(url_for('catalogo'))

    if not(current_user.is_authenticated and current_user.rolUsuario == "Administrador"):
        return redirect(url_for('login'))

    form = FormularioRegistro()
    if form.validate_on_submit():

        cifrada = bcrypt.generate_password_hash(form.password.data).decode('utf-8')

        usuario = Usuario(nombreUsuario=form.nombre.data,
                        apellidoUsuario=form.apellido.data,
                        correoElectronico=form.correo.data,
                        password=cifrada,
                        rolUsuario=form.rol.data)
        db.session.add(usuario)
        db.session.commit()
        return redirect(url_for('registro'))
    
    return render_template('registro.html', form=form)


@app.route('/', methods = ['GET','POST'])
@app.route('/home', methods = ['GET','POST'])
@app.route('/login', methods = ['GET','POST'])
def login():
    form = FormularioInicioSesion()
    if request.method=="POST":
        if form.validate_on_submit():
            
            user = Usuario.query.filter_by(correoElectronico=form.correo.data).first()
            
            if user and bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                # yag = yagmail.SMTP(user.correoElectronico, "DataScience2020")
                # yag.send(to = user.correoElectronico, subject = 'Activar Cuenta', contents = 'Validar Contraseña')
                if (current_user.rolUsuario == "Cajero"):
                    return redirect(url_for("catalogo"))
                elif current_user.rolUsuario == "Administrador":
                    return redirect(url_for("administrador"))

            return redirect(url_for('login'))
    
    return render_template('home.html', form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("login"))
@app.route("/administrador")
def administrador():
    return render_template("administrador.html")

if __name__ == '__main__':
    app.run(debug = True)
