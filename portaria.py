from flask import Flask, render_template_string, request, redirect
from datetime import datetime
import sqlite3
import os

app = Flask(__name__)

# ----------------------
# BANCO
# ----------------------
def conectar():
    return sqlite3.connect("portaria.db")

def criar_tabelas():
    conn = conectar()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS visitantes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        endereco TEXT,
        documento TEXT,
        placa TEXT,
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

    conn.commit()
    conn.close()

# ----------------------
# HORÁRIO
# ----------------------
def agora():
    return datetime.now().strftime("%d/%m/%Y %H:%M")

# ----------------------
# HTML PROFISSIONAL
# ----------------------
HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Portaria</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body {font-family: Arial; background:#f5f6fa; margin:0;}
.container {max-width:1200px; margin:auto; padding:20px;}
h1 {text-align:center; color:#2c3e50;}
.card {background:white; padding:20px; border-radius:10px; margin-top:20px; box-shadow:0 2px 8px rgba(0,0,0,0.1);}
input {padding:10px; margin:5px; border-radius:6px; border:1px solid #ccc;}
button {padding:10px 15px; border:none; border-radius:6px; background:#3498db; color:white; cursor:pointer;}
button:hover {background:#2980b9;}
.delete {background:#e74c3c;}
.saida {background:#f39c12;}
table {width:100%; border-collapse:collapse; margin-top:10px;}
th {background:#3498db; color:white; padding:10px;}
td {padding:8px; border-bottom:1px solid #ddd;}
.paginacao {text-align:center; margin-top:10px;}
.paginacao a {margin:5px; text-decoration:none; background:#ddd; padding:5px 10px; border-radius:5px;}
</style>
</head>
<body>

<div class="container">

<h1>🚪 Controle de Portaria</h1>

<div class="card">
<form method="GET">
<input name="busca" placeholder="Buscar..." value="{{busca}}">
<button>Buscar</button>
</form>
</div>

<div class="card">
<form method="POST" action="/cadastrar">
<input name="nome" placeholder="Nome" required>
<input name="endereco" placeholder="Endereço">
<input name="documento" placeholder="Documento" required>
<input name="placa" placeholder="Placa">
<button>Cadastrar</button>
</form>
</div>

<div class="card">
<table>
<tr>
<th>Nome</th><th>Endereço</th><th>Documento</th><th>Placa</th><th>Entrada</th><th>Saída</th><th>Ações</th>
</tr>

{% for v in registros %}
<tr>
<td>{{v[1]}}</td>
<td>{{v[2]}}</td>
<td>{{v[3]}}</td>
<td>{{v[4]}}</td>
<td>{{v[5]}}</td>
<td>{{v[6]}}</td>
<td>

{% if not v[6] %}
<form method="POST" action="/saida/{{v[0]}}" style="display:inline">
<button class="saida">Saída</button>
</form>
{% endif %}

<form method="POST" action="/excluir/{{v[0]}}" style="display:inline">
<button class="delete">Excluir</button>
</form>

</td>
</tr>
{% endfor %}
</table>

<div class="paginacao">
{% if pagina > 1 %}
<a href="/?pagina={{pagina-1}}&busca={{busca}}">⬅</a>
{% endif %}

<span>Página {{pagina}}</span>

{% if tem_proxima %}
<a href="/?pagina={{pagina+1}}&busca={{busca}}">➡</a>
{% endif %}
</div>

</div>

<div class="card">
<h2>📋 Ocorrências</h2>

<form method="POST" action="/ocorrencia">
<input name="nome" placeholder="Nome">
<input name="descricao" placeholder="Descrição" required>
<button>Registrar</button>
</form>

<table>
<tr><th>Nome</th><th>Descrição</th><th>Data</th><th>Ação</th></tr>

{% for o in ocorrencias %}
<tr>
<td>{{o[1]}}</td>
<td>{{o[2]}}</td>
<td>{{o[3]}}</td>
<td>
<form method="POST" action="/excluir_ocorrencia/{{o[0]}}">
<button class="delete">Excluir</button>
</form>
</td>
</tr>
{% endfor %}
</table>

</div>

</div>
</body>
</html>
"""

# ----------------------
# ROTAS
# ----------------------
@app.route("/")
def index():
    pagina = int(request.args.get("pagina", 1))
    busca = request.args.get("busca", "")
    limite = 10
    offset = (pagina - 1) * limite

    conn = conectar()
    c = conn.cursor()

    termo = f"%{busca}%"

    c.execute("""
    SELECT * FROM visitantes
    WHERE nome LIKE ? OR documento LIKE ? OR placa LIKE ? OR endereco LIKE ?
    ORDER BY id DESC LIMIT ? OFFSET ?
    """, (termo, termo, termo, termo, limite+1, offset))

    dados = c.fetchall()
    tem_proxima = len(dados) > limite
    registros = dados[:limite]

    c.execute("SELECT * FROM ocorrencias ORDER BY id DESC")
    ocorrencias = c.fetchall()

    conn.close()

    return render_template_string(HTML, registros=registros,
                                 pagina=pagina, tem_proxima=tem_proxima,
                                 busca=busca, ocorrencias=ocorrencias)

@app.route("/cadastrar", methods=["POST"])
def cadastrar():
    conn = conectar()
    c = conn.cursor()

    c.execute("INSERT INTO visitantes VALUES (NULL,?,?,?,?,?,?)",
              (request.form["nome"],
               request.form.get("endereco",""),
               request.form["documento"],
               request.form.get("placa",""),
               agora(), ""))

    conn.commit()
    conn.close()
    return redirect("/")

@app.route("/saida/<int:id>", methods=["POST"])
def saida(id):
    conn = conectar()
    c = conn.cursor()

    c.execute("UPDATE visitantes SET saida=? WHERE id=? AND saida=''",
              (agora(), id))

    conn.commit()
    conn.close()
    return redirect("/")

@app.route("/excluir/<int:id>", methods=["POST"])
def excluir(id):
    conn = conectar()
    c = conn.cursor()

    c.execute("DELETE FROM visitantes WHERE id=?", (id,))

    conn.commit()
    conn.close()
    return redirect("/")

@app.route("/ocorrencia", methods=["POST"])
def ocorrencia():
    conn = conectar()
    c = conn.cursor()

    c.execute("INSERT INTO ocorrencias VALUES (NULL,?,?,?)",
              (request.form.get("nome",""),
               request.form["descricao"],
               agora()))

    conn.commit()
    conn.close()
    return redirect("/")

@app.route("/excluir_ocorrencia/<int:id>", methods=["POST"])
def excluir_ocorrencia(id):
    conn = conectar()
    c = conn.cursor()

    c.execute("DELETE FROM ocorrencias WHERE id=?", (id,))

    conn.commit()
    conn.close()
    return redirect("/")

# ----------------------
# START
# ----------------------
if __name__ == "__main__":
    criar_tabelas()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
