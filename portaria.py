import datetime

"""
Portaria Parque das Rosas WEB (Flask + SQLite)
VERSÃO ONLINE SIMPLES
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
        endereco TEXT,
        documento TEXT,
        placa TEXT,
        entrada TEXT,
        saida TEXT
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
table{width:100%;margin-top:20px;background:#2e2e3e}
th,td{padding:10px}
</style>
</head>
<body>

<h1>🚪 Portaria Parque das Rosas</h1>

<form method="POST" action="/cadastrar">
<input name="nome" placeholder="Nome" required>
<input name="documento" placeholder="Documento" required>
<input name="placa" placeholder="Placa do veículo">
<button>Cadastrar</button>
</form>

<table>
<tr><th>Nome</th><th>Documento</th><th>Placa</th><th>Entrada</th><th>Saída</th><th>Ação</th></tr>
{% for v in registros %}
<tr>
<td>{{v[1]}}</td>
<td>{{v[3]}}</td>
<td>{{v[4]}}</td>
<td>{{v[5]}}</td>
<td>{{v[6]}}</td>
<td>
<form method="POST" action="/excluir/{{v[0]}}">
<button class="delete">Excluir</button>
</form>
</td>
</tr>
{% endfor %}
</table>

</body>
</html>
"""

# ----------------------
# ROTAS
# ----------------------

@app.route("/")
def index():
    conn = conectar()
    c = conn.cursor()
    c.execute("SELECT * FROM visitantes")
    registros = c.fetchall()
    conn.close()

    return render_template_string(HTML, registros=registros)


@app.route("/cadastrar", methods=["POST"])
def cadastrar():
    conn = conectar()
    c = conn.cursor()

    c.execute("""
    INSERT INTO visitantes(nome,documento,placa,entrada,saida)
    VALUES(?,?,?,?,?)
    """, (
        request.form["nome"],
        request.form["documento"],
        request.form.get("placa", ""),
        agora(),
        ""
    ))

    conn.commit()
    conn.close()

    return redirect("/")


@app.route("/excluir/<int:id>", methods=["POST"])
def excluir(id):
    conn = conectar()
    c = conn.cursor()

    c.execute("DELETE FROM visitantes WHERE id = ?", (id,))

    conn.commit()
    conn.close()

    return redirect("/")

# ----------------------
# TESTES
# ----------------------

def _test_insert():
    criar_tabelas()
    conn = conectar()
    c = conn.cursor()

    c.execute("DELETE FROM visitantes")

    c.execute("INSERT INTO visitantes(nome,documento,placa,entrada,saida) VALUES ('Teste','123','ABC','01/01','')")
    conn.commit()

    c.execute("SELECT * FROM visitantes")
    dados = c.fetchall()

    assert len(dados) == 1
    assert dados[0][4] == 'ABC'

    conn.close()


def _test_delete():
    criar_tabelas()
    conn = conectar()
    c = conn.cursor()

    c.execute("DELETE FROM visitantes")

    c.execute("INSERT INTO visitantes(nome,documento,placa,entrada,saida) VALUES ('Teste','123','ABC','01/01','')")
    conn.commit()

    c.execute("SELECT id FROM visitantes")
    vid = c.fetchone()[0]

    c.execute("DELETE FROM visitantes WHERE id = ?", (vid,))
    conn.commit()

    c.execute("SELECT * FROM visitantes")
    dados = c.fetchall()

    assert len(dados) == 0

    conn.close()

# ----------------------
# EXECUÇÃO
# ----------------------

if __name__ == "__main__":
    criar_tabelas()
    _test_insert()
    _test_delete()

    port=int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0",port=port)
