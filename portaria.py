import datetime

"""
Portaria Parque das Rosas WEB (Flask + SQLite)
COM PAGINAÇÃO + BUSCA + OCORRÊNCIAS
"""

from flask import Flask, render_template_string, request, redirect
from datetime import datetime
import sqlite3
import os
from zoneinfo import ZoneInfo

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
    return datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y %H:%M")

# ----------------------
# HTML
# ----------------------

HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Portaria Parque das Rosas</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{font-family:Arial;background:#1e1e2f;color:white;text-align:center}
input,button{padding:10px;border-radius:8px;border:none;margin:5px}
button{background:#4CAF50;color:white}
.delete{background:#f44336}
.saida{background:#ff9800}
table{width:100%;margin-top:20px;background:#2e2e3e}
th,td{padding:10px}
.paginacao a{color:white;margin:5px;text-decoration:none}
.section{margin-top:40px}
</style>
</head>
<body>

<h1>🚪 Portaria Parque das Rosas</h1>

<!-- BUSCA -->
<form method="GET" action="/">
<input name="busca" placeholder="Buscar nome/documento/placa">
<button>Buscar</button>
</form>

<!-- CADASTRO -->
<form method="POST" action="/cadastrar">
<input name="nome" placeholder="Nome" required>
<input name="documento" placeholder="Documento" required>
<input name="placa" placeholder="Placa">
<button>Cadastrar</button>
</form>

<!-- TABELA VISITANTES -->
<table>
<tr><th>Nome</th><th>Documento</th><th>Placa</th><th>Entrada</th><th>Saída</th><th>Ações</th></tr>
{% for v in registros %}
<tr>
<td>{{v[1]}}</td>
<td>{{v[2]}}</td>
<td>{{v[3]}}</td>
<td>{{v[4]}}</td>
<td>{{v[5]}}</td>
<td>
{% if not v[5] %}
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
<a href="/?pagina={{pagina-1}}&busca={{busca}}">⬅️</a>
{% endif %}
<span>Página {{pagina}}</span>
{% if tem_proxima %}
<a href="/?pagina={{pagina+1}}&busca={{busca}}">➡️</a>
{% endif %}
</div>

<!-- OCORRÊNCIAS -->
<div class="section">
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

    query = "SELECT * FROM visitantes WHERE nome LIKE ? OR documento LIKE ? OR placa LIKE ? ORDER BY id DESC LIMIT ? OFFSET ?"
    termo = f"%{busca}%"

    c.execute(query, (termo, termo, termo, limite + 1, offset))
    dados = c.fetchall()

    tem_proxima = len(dados) > limite
    registros = dados[:limite]

    c.execute("SELECT * FROM ocorrencias ORDER BY id DESC")
    ocorrencias = c.fetchall()

    conn.close()

    return render_template_string(HTML, registros=registros, pagina=pagina, tem_proxima=tem_proxima, busca=busca, ocorrencias=ocorrencias)


@app.route("/cadastrar", methods=["POST"])
def cadastrar():
    conn = conectar()
    c = conn.cursor()

    c.execute("INSERT INTO visitantes(nome,documento,placa,entrada,saida) VALUES(?,?,?,?,?)",
              (request.form["nome"], request.form["documento"], request.form.get("placa", ""), agora(), ""))

    conn.commit()
    conn.close()

    return redirect("/")


@app.route("/saida/<int:id>", methods=["POST"])
def registrar_saida(id):
    conn = conectar()
    c = conn.cursor()

    c.execute("UPDATE visitantes SET saida=? WHERE id=? AND saida=''", (agora(), id))

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

    c.execute("INSERT INTO ocorrencias(nome,descricao,data) VALUES(?,?,?)",
              (request.form.get("nome", ""), request.form["descricao"], agora()))

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
# TESTES
# ----------------------

def _test_busca():
    criar_tabelas()
    conn = conectar()
    c = conn.cursor()

    c.execute("DELETE FROM visitantes")

    c.execute("INSERT INTO visitantes(nome,documento,placa,entrada,saida) VALUES ('Joao','123','ABC','01/01','')")
    conn.commit()

    c.execute("SELECT * FROM visitantes WHERE nome LIKE '%Joao%'")
    dados = c.fetchall()

    assert len(dados) == 1

    conn.close()


def _test_ocorrencia():
    criar_tabelas()
    conn = conectar()
    c = conn.cursor()

    c.execute("DELETE FROM ocorrencias")

    c.execute("INSERT INTO ocorrencias(nome,descricao,data) VALUES ('Teste','Algo','01/01')")
    conn.commit()

    c.execute("SELECT * FROM ocorrencias")
    dados = c.fetchall()

    assert len(dados) == 1

    conn.close()

# ----------------------
# EXECUÇÃO
# ----------------------

if __name__ == "__main__":
    criar_tabelas()
    _test_busca()
    _test_ocorrencia()

    port=int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0",port=port)
