from flask import Flask, render_template_string, request, redirect, session, send_file
from datetime import datetime
import sqlite3
import os
import csv

app = Flask(__name__)
app.secret_key = "portaria_super_segura"

DB = "portaria.db"
UPLOAD = "static/fotos"

if not os.path.exists(UPLOAD):
    os.makedirs(UPLOAD)

# -------------------------
# BANCO
# -------------------------
def conectar():
    return sqlite3.connect(DB)

def criar():
    conn = conectar()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY,
        user TEXT,
        senha TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS visitantes (
        id INTEGER PRIMARY KEY,
        nome TEXT,
        documento TEXT,
        placa TEXT,
        foto TEXT,
        entrada TEXT,
        saida TEXT
    )
    """)

    # usuário padrão
    c.execute("SELECT * FROM usuarios")
    if not c.fetchall():
        c.execute("INSERT INTO usuarios VALUES (1,'admin','123')")

    conn.commit()
    conn.close()

# -------------------------
# LOGIN
# -------------------------
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        user = request.form["user"]
        senha = request.form["senha"]

        conn = conectar()
        c = conn.cursor()
        c.execute("SELECT * FROM usuarios WHERE user=? AND senha=?", (user, senha))

        if c.fetchone():
            session["logado"] = True
            return redirect("/")
        else:
            return "Login inválido"

    return """
    <h2>Login Portaria</h2>
    <form method="POST">
    <input name="user" placeholder="Usuário"><br>
    <input name="senha" type="password" placeholder="Senha"><br>
    <button>Entrar</button>
    </form>
    """

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# -------------------------
# HOME
# -------------------------
@app.route("/")
def index():
    if not session.get("logado"):
        return redirect("/login")

    conn = conectar()
    dados = conn.execute("SELECT * FROM visitantes ORDER BY id DESC").fetchall()

    return render_template_string("""
    <h1>🚪 Portaria Profissional</h1>

    <a href="/logout">Sair</a> |
    <a href="/exportar">Exportar</a>

    <h2>Novo Visitante</h2>
    <form method="POST" action="/add" enctype="multipart/form-data">
    <input name="nome" placeholder="Nome" required>
    <input name="documento" placeholder="Documento">
    <input name="placa" placeholder="Placa">
    <input type="file" name="foto">
    <button>Cadastrar</button>
    </form>

    <table border=1>
    <tr><th>Nome</th><th>Doc</th><th>Placa</th><th>Foto</th><th>Entrada</th><th>Saída</th></tr>

    {% for v in dados %}
    <tr>
    <td>{{v[1]}}</td>
    <td>{{v[2]}}</td>
    <td>{{v[3]}}</td>
    <td>
    {% if v[4] %}
        <img src="/static/fotos/{{v[4]}}" width="60">
    {% endif %}
    </td>
    <td>{{v[5]}}</td>
    <td>{{v[6]}}</td>
    </tr>
    {% endfor %}
    </table>
    """, dados=dados)

# -------------------------
# CADASTRO
# -------------------------
@app.route("/add", methods=["POST"])
def add():
    if not session.get("logado"):
        return redirect("/login")

    nome = request.form["nome"]
    doc = request.form.get("documento","")
    placa = request.form.get("placa","")

    foto_nome = ""
    foto = request.files.get("foto")

    if foto and foto.filename:
        foto_nome = f"{datetime.now().timestamp()}.jpg"
        foto.save(os.path.join(UPLOAD, foto_nome))

    conn = conectar()
    conn.execute("""
    INSERT INTO visitantes (nome,documento,placa,foto,entrada,saida)
    VALUES (?,?,?,?,?,?)
    """, (nome, doc, placa, foto_nome, datetime.now(), ""))

    conn.commit()
    return redirect("/")

# -------------------------
# EXPORTAR CSV
# -------------------------
@app.route("/exportar")
def exportar():
    conn = conectar()
    dados = conn.execute("SELECT * FROM visitantes").fetchall()

    arquivo = "relatorio.csv"

    with open(arquivo, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Nome","Documento","Placa","Entrada","Saída"])
        for d in dados:
            writer.writerow([d[1], d[2], d[3], d[5], d[6]])

    return send_file(arquivo, as_attachment=True)

# -------------------------
# START
# -------------------------
if __name__ == "__main__":
    criar()
    app.run(debug=True)
