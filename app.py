from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///banco.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)

    humores = db.relationship("Humor", backref="usuario", lazy=True)

class Humor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    humor = db.Column(db.String(50), nullable=False)
    observacao = db.Column(db.String(200))
    id_usuario = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)

with app.app_context():
    db.create_all()

    if Usuario.query.count() == 0:
        usuario = Usuario(nome="Adylla", email="adylla@email.com")
        db.session.add(usuario)
        db.session.commit()

        humor = Humor(
            humor="Feliz",
            observacao="Hoje foi um ótimo dia.",
            id_usuario=usuario.id
        )
        db.session.add(humor)
        db.session.commit()

    print("\nUsuários:")
    usuarios = Usuario.query.all()
    for u in usuarios:
        print(f"{u.id} - {u.nome} - {u.email}")

    print("\nRegistros de Humor:")
    humores = Humor.query.all()
    for h in humores:
        print(f"{h.id} - {h.humor} - {h.observacao} - Usuário: {h.usuario.nome}")

@app.route("/")
def inicio():
    return "Banco funcionando!"

if __name__ == "__main__":
    app.run(debug=True)
