from app import create_app, db
from app.models import Usuario, Rol, Departamento, Ticket

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'Usuario': Usuario,
        'Rol': Rol,
        'Departamento': Departamento,
        'Ticket': Ticket
    }

if __name__ == '__main__':
    app.run(debug=True)