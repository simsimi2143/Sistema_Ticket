from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SelectField, BooleanField, SubmitField, IntegerField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Optional
from app.models import Usuario, Rol, Departamento
from flask_wtf.file import FileField, FileAllowed, FileSize

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    remember_me = BooleanField('Recordarme')
    submit = SubmitField('Iniciar Sesión')

class RegistrationForm(FlaskForm):
    name = StringField('Nombre Completo', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirmar Contraseña', 
                                    validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Registrarse')
    
    def validate_email(self, email):
        user = Usuario.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Este email ya está registrado. Por favor use otro.')

class TicketForm(FlaskForm):
    name = StringField('Título del Ticket', validators=[DataRequired(), Length(min=5, max=200)])
    description = TextAreaField('Descripción', validators=[DataRequired()])
    detalles_fallo = TextAreaField('Detalles del Fallo (opcional)')
    
    # Campo para imagen con validación de tamaño
    image = FileField('Imagen Adjunta', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Solo se permiten imágenes (JPG, JPEG, PNG, GIF)!'),
        FileSize(max_size=5 * 1024 * 1024, message='La imagen no debe exceder los 5MB')
    ])
    
    estado = SelectField('Estado', choices=[
        ('Abierto', 'Abierto'),
        ('En Progreso', 'En Progreso'),
        ('Resuelto', 'Resuelto'),
        ('Cerrado', 'Cerrado')
    ])
    user_asigned = SelectField('Asignar a', coerce=int)
    prioridad = SelectField('Prioridad', 
                            choices=[('Baja', 'Baja'), ('Media', 'Media'), ('Alta', 'Alta')], 
                            default='Media',
                            validators=[DataRequired()])
    submit = SubmitField('Guardar Ticket')



class DepartmentForm(FlaskForm):
    depth_name = StringField('Nombre del Departamento', validators=[DataRequired(), Length(min=2, max=100)])
    description = TextAreaField('Descripción')
    status = BooleanField('Activo', default=True)
    submit = SubmitField('Guardar Departamento')
    
# ... (tus formularios existentes) ...

class UserForm(FlaskForm):
    name = StringField('Nombre Completo', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[Optional(), Length(min=6)])
    confirm_password = PasswordField('Confirmar Contraseña', 
                                    validators=[EqualTo('password', message='Las contraseñas deben coincidir')])
    id_rol = SelectField('Rol', coerce=int, validators=[DataRequired()])
    depth_id = SelectField('Departamento', coerce=int, validators=[Optional()])
    status = BooleanField('Activo', default=True)
    submit = SubmitField('Guardar Usuario')
    
    def validate_email(self, email):
        # Excluir el usuario actual al validar email único
        user_id = getattr(self, 'user_id', None)
        query = Usuario.query.filter_by(email=email.data)
        if user_id:
            query = query.filter(Usuario.id_user != user_id)
        if query.first():
            raise ValidationError('Este email ya está registrado. Por favor use otro.')

class DepartmentForm(FlaskForm):
    depth_name = StringField('Nombre del Departamento', validators=[DataRequired(), Length(min=2, max=100)])
    description = TextAreaField('Descripción')
    status = BooleanField('Activo', default=True)
    submit = SubmitField('Guardar Departamento')

class RoleForm(FlaskForm):
    rol_name = StringField('Nombre del Rol', validators=[DataRequired(), Length(min=2, max=50)])
    description = TextAreaField('Descripción')
    perm_tickets = SelectField('Permiso Tickets', 
                               choices=[(0, 'No Access'), (1, 'Read'), (2, 'Read/Write')], 
                               coerce=int, default=1)
    perm_users = SelectField('Permiso Usuarios', 
                             choices=[(0, 'No Access'), (1, 'Read'), (2, 'Read/Write')], 
                             coerce=int, default=0)
    perm_departments = SelectField('Permiso Departamentos', 
                                   choices=[(0, 'No Access'), (1, 'Read'), (2, 'Read/Write')], 
                                   coerce=int, default=0)
    perm_admin = SelectField('Permiso Administración', 
                             choices=[(0, 'No Access'), (1, 'Read'), (2, 'Read/Write')], 
                             coerce=int, default=0)
    status = BooleanField('Activo', default=True)
    submit = SubmitField('Guardar Rol')    