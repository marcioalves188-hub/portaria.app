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

# ----------------------
# BANCO
# ----------------------
def conectar():
    return sqlite3.connect(DB)

def criar_tabelas():
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
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        documento TEXT,
        placa TEXT,
        foto TEXT,
        entrada TEXT,
        saida TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS ocorrencias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        descricao TEXT,
        data TEXT
    )
    """)

    # usuário padrão
    c.execute("SELECT * FROM usuarios")
    if not c.fetchall():
        c.execute("INSERT INTO usuarios VALUES (1,'admin','123')")

    conn.commit()
    conn.close()

# ----------------------
def agora():
    return datetime.now().strftime("%d/%m/%Y %H:%M")

# ----------------------
# LOGIN
# ----------------------
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

# ----------------------
# HOME
# ----------------------
@app.route("/")
def index():
    if not session.get("logado"):
        return redirect("/login")

    conn = conectar()
    dados = conn.execute("SELECT * FROM visitantes ORDER BY id DESC").fetchall()
    ocorrencias = conn.execute("SELECT * FROM ocorrencias ORDER BY id DESC").fetchall()
    conn.close()

    return render_template_string("""
    <h1>🚪 Portaria Profissional</h1>

    <a href="/logout">Sair</a> |
    <a href="/exportar">Exportar CSV</a>

    <h2>Novo Visitante</h2>
    <form method="POST" action="/cadastrar" enctype="multipart/form-data">
    <input name="nome" placeholder="Nome" required>
    <input name="documento" placeholder="Documento">
    <input name="placa" placeholder="Placa">
    <input type="file" name="foto">
    <button>Cadastrar</button>
    </form>

    <table border=1>
    <tr><th>Nome</th><th>Doc</th><th>Placa</th><th>Foto</th><th>Entrada</th><th>Saída</th><th>Ações</th></tr>

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
    <td>
        {% if not v[6] %}
        <form method="POST" action="/saida/{{v[0]}}" style="display:inline">
            <button>Saída</button>
        </form>
        {% endif %}
        <form method="POST" action="/excluir/{{v[0]}}" style="display:inline">
            <button>Excluir</button>
        </form>
    </td>
    </tr>
    {% endfor %}
    </table>

    <h2>📋 Ocorrências</h2>

    <form method="POST" action="/ocorrencia">
    <input name="nome" placeholder="Nome">
    <input name="descricao" placeholder="Descrição" required>
    <button>Registrar</button>
    </form>

    <table border=1>
    <tr><th>Nome</th><th>Descrição</th><th>Data</th><th>Ação</th></tr>
    {% for o in ocorrencias %}
    <tr>
    <td>{{o[1]}}</td>
    <td>{{o[2]}}</td>
    <td>{{o[3]}}</td>
    <td>
        <form method="POST" action="/excluir_ocorrencia/{{o[0]}}">
        <button>Excluir</button>
        </form>
    </td>
    </tr>
    {% endfor %}
    </table>
    """, dados=dados, ocorrencias=ocorrencias)

# ----------------------
# CADASTRO
# ----------------------
@app.route("/cadastrar", methods=["POST"])
def cadastrar():
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
    """, (nome, doc, placa, foto_nome, agora(), ""))

    conn.commit()
    conn.close()

    return redirect("/")

# ----------------------
@app.route("/saida/<int:id>", methods=["POST"])
def saida(id):
    conn = conectar()
    conn.execute("UPDATE visitantes SET saida=? WHERE id=?", (agora(), id))
    conn.commit()
    conn.close()
    return redirect("/")

# ----------------------
@app.route("/excluir/<int:id>", methods=["POST"])
def excluir(id):
    conn = conectar()
    conn.execute("DELETE FROM visitantes WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/")

# ----------------------
# EXPORTAR CSV
# ----------------------
@app.route("/exportar")
def exportar():
    conn = conectar()
    dados = conn.execute("SELECT * FROM visitantes").fetchall()
    conn.close()

    arquivo = "relatorio.csv"

    with open(arquivo, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Nome","Documento","Placa","Entrada","Saída"])
        for d in dados:
            writer.writerow([d[1], d[2], d[3], d[5], d[6]])

    return send_file(arquivo, as_attachment=True)

# ----------------------
# OCORRÊNCIAS
# ----------------------
@app.route("/ocorrencia", methods=["POST"])
def ocorrencia():
    conn = conectar()
    conn.execute("INSERT INTO ocorrencias VALUES (NULL,?,?,?)",
                 (request.form.get("nome",""),
                  request.form["descricao"],
                  agora()))
    conn.commit()
    conn.close()
    return redirect("/")

@app.route("/excluir_ocorrencia/<int:id>", methods=["POST"])
def excluir_ocorrencia(id):
    conn = conectar()
    conn.execute("DELETE FROM ocorrencias WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/")

# ----------------------
if __name__ == "__main__":
    criar_tabelas()
    app.run(debug=True)
