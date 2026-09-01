from flask import Flask, render_template, request, redirect, url_for, session, flash, g
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime

app = Flask(__name__)

app.secret_key = "chave-bem-viver-123"

DATABASE = "banco.db"


# =========================
# BANCO DE DADOS
# =========================

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row

    return g.db


@app.teardown_appcontext
def fechar_banco(exception=None):
    db = g.pop("db", None)

    if db is not None:
        db.close()


def criar_banco():

    db = get_db()

    db.executescript("""
    
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        senha TEXT NOT NULL,
        criado_em TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS diario (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER NOT NULL,
        humor TEXT NOT NULL,
        nota TEXT,
        fatores TEXT,
        criado_em TEXT NOT NULL,

        FOREIGN KEY(usuario_id)
        REFERENCES usuarios(id)
    );

    """)

    db.commit()


@app.before_request
def iniciar_banco():
    criar_banco()


# =========================
# LOGIN OBRIGATÓRIO
# =========================

def login_required(func):

    @wraps(func)
    def wrapper(*args, **kwargs):

        if "usuario_id" not in session:

            flash(
                "Faça login para acessar essa página.",
                "info"
            )

            return redirect(url_for("login"))

        return func(*args, **kwargs)

    return wrapper


# =========================
# USUÁRIO LOGADO
# =========================

@app.context_processor
def usuario_logado():

    usuario = None

    if "usuario_id" in session:

        usuario = get_db().execute(
            """
            SELECT id, nome, email
            FROM usuarios
            WHERE id = ?
            """,
            (session["usuario_id"],)
        ).fetchone()

    return {
        "usuario": usuario
    }


# =========================
# PÁGINA INICIAL
# =========================

@app.route("/")
def index():

    return render_template(
        "index.html"
    )


# =========================
# LOGIN
# =========================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        senha = request.form.get(
            "senha",
            ""
        )

        db = get_db()

        usuario = db.execute(
            """
            SELECT *
            FROM usuarios
            WHERE email = ?
            """,
            (email,)
        ).fetchone()

        if usuario and check_password_hash(
            usuario["senha"],
            senha
        ):

            session.clear()

            session["usuario_id"] = usuario["id"]

            flash(
                f"Bem-vindo(a), {usuario['nome']}!",
                "success"
            )

            return redirect(
                url_for("dashboard")
            )

        flash(
            "E-mail ou senha incorretos.",
            "error"
        )

    return render_template(
        "login.html"
    )


# =========================
# CADASTRO
# =========================

@app.route(
    "/cadastro",
    methods=["GET", "POST"]
)
def cadastro():

    if request.method == "POST":

        nome = request.form.get(
            "nome",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        senha = request.form.get(
            "senha",
            ""
        )

        confirmar = request.form.get(
            "confirmar_senha",
            ""
        )

        if not nome or not email or not senha:

            flash(
                "Preencha todos os campos.",
                "error"
            )

        elif senha != confirmar:

            flash(
                "As senhas não coincidem.",
                "error"
            )

        elif len(senha) < 6:

            flash(
                "A senha deve possuir pelo menos 6 caracteres.",
                "error"
            )

        else:

            db = get_db()

            try:

                senha_hash = generate_password_hash(
                    senha
                )

                db.execute(
                    """
                    INSERT INTO usuarios
                    (nome, email, senha, criado_em)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        nome,
                        email,
                        senha_hash,
                        datetime.now().strftime(
                            "%d/%m/%Y %H:%M"
                        )
                    )
                )

                db.commit()

                flash(
                    "Conta criada com sucesso!",
                    "success"
                )

                return redirect(
                    url_for("login")
                )

            except sqlite3.IntegrityError:

                flash(
                    "Este e-mail já está cadastrado.",
                    "error"
                )

    return render_template(
        "cadastro.html"
    )


# =========================
# DASHBOARD
# =========================

@app.route("/dashboard")
@login_required
def dashboard():

    db = get_db()

    registros = db.execute(
        """
        SELECT *
        FROM diario
        WHERE usuario_id = ?
        ORDER BY id DESC
        LIMIT 5
        """,
        (session["usuario_id"],)
    ).fetchall()

    total = db.execute(
        """
        SELECT COUNT(*) AS total
        FROM diario
        WHERE usuario_id = ?
        """,
        (session["usuario_id"],)
    ).fetchone()["total"]

    return render_template(
        "dashboard.html",
        registros=registros,
        total=total
    )


# =========================
# DIÁRIO EMOCIONAL
# =========================

@app.route(
    "/diario",
    methods=["GET", "POST"]
)
@login_required
def diario():

    db = get_db()

    if request.method == "POST":

        humor = request.form.get(
            "humor"
        )

        nota = request.form.get(
            "nota",
            ""
        ).strip()

        fatores = request.form.getlist(
            "fatores"
        )

        fatores_texto = ", ".join(
            fatores
        )

        if not humor:

            flash(
                "Escolha como você está se sentindo.",
                "error"
            )

        else:

            db.execute(
                """
                INSERT INTO diario
                (
                    usuario_id,
                    humor,
                    nota,
                    fatores,
                    criado_em
                )

                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    session["usuario_id"],
                    humor,
                    nota,
                    fatores_texto,
                    datetime.now().strftime(
                        "%d/%m/%Y %H:%M"
                    )
                )
            )

            db.commit()

            flash(
                "Seu registro foi salvo com carinho 💜",
                "success"
            )

            return redirect(
                url_for("diario")
            )

    registros = db.execute(
        """
        SELECT *
        FROM diario
        WHERE usuario_id = ?
        ORDER BY id DESC
        """,
        (session["usuario_id"],)
    ).fetchall()

    return render_template(
        "diario.html",
        registros=registros
    )


# =========================
# PERFIL
# =========================

@app.route(
    "/perfil",
    methods=["GET", "POST"]
)
@login_required
def perfil():

    db = get_db()

    usuario = db.execute(
        """
        SELECT *
        FROM usuarios
        WHERE id = ?
        """,
        (session["usuario_id"],)
    ).fetchone()

    if request.method == "POST":

        nome = request.form.get(
            "nome",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        if not nome or not email:

            flash(
                "Preencha todos os campos.",
                "error"
            )

        else:

            try:

                db.execute(
                    """
                    UPDATE usuarios
                    SET nome = ?, email = ?
                    WHERE id = ?
                    """,
                    (
                        nome,
                        email,
                        session["usuario_id"]
                    )
                )

                db.commit()

                flash(
                    "Perfil atualizado!",
                    "success"
                )

                return redirect(
                    url_for("perfil")
                )

            except sqlite3.IntegrityError:

                flash(
                    "Este e-mail já está sendo utilizado.",
                    "error"
                )

    return render_template(
        "perfil.html",
        usuario_perfil=usuario
    )


# =========================
# DICAS
# =========================

@app.route("/dicas")
def dicas():

    return render_template(
        "dicas.html"
    )


# =========================
# RESPIRAÇÃO
# =========================

@app.route("/respirar")
def respirar():

    return render_template(
        "respirar.html"
    )


# =========================
# SAIR
# =========================

@app.route("/logout")
def logout():

    session.clear()

    flash(
        "Você saiu da sua conta.",
        "info"
    )

    return redirect(
        url_for("index")
    )


# =========================
# EXECUTAR
# =========================

if __name__ == "__main__":

    app.run(
        debug=True
    )