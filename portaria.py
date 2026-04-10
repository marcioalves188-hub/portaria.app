import datetime

"""
Portaria Parque das Rosas WEB (Flask + SQLite)
VERSÃO PROFISSIONAL (BUSCA + OCORRÊNCIAS + PAGINAÇÃO)
"""

from flask import Flask, render_template_string, request, redirect, send_file
from datetime import datetime
import sqlite3
import os
from zoneinfo import ZoneInfo

app = Flask(__name__)

# ----------------------
# BANCO DE DADOS
# ----------------------

def conectar():
    return sqlite3.connect("portaria.db")


def criar_tabelas():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
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

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ocorrencias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data TEXT,
        descricao TEXT
    )
    """)

    conn.commit()
    conn.close()

# ----------------------
# HORÁRIO BRASIL
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

<style>
body {font-family: Arial;background:#1e1e2f;color:white;margin:0}
.container{width:95%;margin:auto}
h1{text-align:center}
form{display:flex;flex-wrap:wrap;gap:10px;justify-content:center;margin-bottom:20px}
input,textarea{padding:10px;border-radius:8px;border:none}
button{padding:10px 15px;border:none;border-radius:8px;cursor:pointer}

.entrada{background:#4CAF50}
.saida{background:#f44336}
.excluir{background:#ff9800}
.buscar{background:#2196F3}
.ocorrencia{background:#9C27B0}

.excluir-oc{background:#e91e63}

table{width:100%;border-collapse:collapse;background:#2e2e3e}
th,td{padding:10px;text-align:center}
th{background:#333}
tr:nth-child(even){background:#3a3a4f}

.oc-box{
background:#2e2e3e;
padding:15px;
border-radius:10px;
margin-top:30px
}
</style>
</head>

<body>

<div class="container">

<h1>🚪 Portaria Parque das Rosas</h1>

<form method="GET" action="/">
<input name="q" placeholder="Buscar nome, documento ou placa" value="{{busca}}">
<button class="buscar">Buscar</button>
</form>

<form method="POST" action="/cadastrar">
<input name="nome" placeholder="Nome" required>
<input name="endereco" placeholder="Endereço">
<input name="documento" placeholder="CPF/RG" required>
<input name="placa" placeholder="Placa">
<button class="entrada">Cadastrar</button>
</form>

<table>
<tr>
<th>Nome</th>
<th>Documento</th>
<th>Placa</th>
<th>Entrada</th>
<th>Saída</th>
<th>Ações</th>
</tr>

{% for v in registros %}
<tr>
<td>{{v[1]}}</td>
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

<form method="POST" action="/excluir/{{v[0]}}" style="display:inline" onsubmit="return confirm('Excluir registro?')">
<button class="excluir">Excluir</button>
</form>

</td>
</tr>
{% endfor %}

</table>

<br>

<div style="text-align:center">
{% if pagina>1 %}
<a href="/?page={{pagina-1}}">⬅ Anterior</a>
{% endif %}

Página {{pagina}}

<a href="/?page={{pagina+1}}">Próxima ➡</a>
</div>


<div class="oc-box">
<h2>📋 Ocorrências</h2>

<form method="POST" action="/ocorrencia">
<textarea name="descricao" placeholder="Registrar ocorrência" required style="width:100%"></textarea>
<br><br>
<button class="ocorrencia">Registrar Ocorrência</button>
</form>

<table>
<tr>
<th>Data</th>
<th>Descrição</th>
<th>Ação</th>
</tr>

{% for o in ocorrencias %}
<tr>
<td>{{o[1]}}</td>
<td>{{o[2]}}</td>
<td>
<form method="POST" action="/excluir_ocorrencia/{{o[0]}}" onsubmit="return confirm('Excluir ocorrência?')">
<button class="excluir-oc">Excluir</button>
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

    busca = request.args.get("q","")
    pagina = int(request.args.get("page",1))
    limite = 50
    offset = (pagina-1)*limite

    conn = conectar()
    cursor = conn.cursor()

    if busca:
        cursor.execute("""
        SELECT * FROM visitantes
        WHERE nome LIKE ? OR documento LIKE ? OR placa LIKE ?
        LIMIT ? OFFSET ?
        """,(f"%{busca}%",f"%{busca}%",f"%{busca}%",limite,offset))
    else:
        cursor.execute("SELECT * FROM visitantes LIMIT ? OFFSET ?",(limite,offset))

    registros = cursor.fetchall()

    cursor.execute("SELECT * FROM ocorrencias ORDER BY id DESC LIMIT 20")
    ocorrencias = cursor.fetchall()

    conn.close()

    return render_template_string(HTML,registros=registros,busca=busca,pagina=pagina,ocorrencias=ocorrencias)


@app.route("/cadastrar",methods=["POST"])
def cadastrar():

    conn=conectar()
    cursor=conn.cursor()

    cursor.execute("""
    INSERT INTO visitantes(nome,endereco,documento,placa,entrada,saida)
    VALUES(?,?,?,?,?,?)
    """,(
        request.form["nome"],
        request.form["endereco"],
        request.form["documento"],
        request.form["placa"],
        agora(),
        ""
    ))

    conn.commit()
    conn.close()

    return redirect("/")


@app.route("/saida/<int:id>",methods=["POST"])
def saida(id):

    conn=conectar()
    cursor=conn.cursor()

    cursor.execute("UPDATE visitantes SET saida=? WHERE id=?",(agora(),id))

    conn.commit()
    conn.close()

    return redirect("/")


@app.route("/excluir/<int:id>",methods=["POST"])
def excluir(id):

    conn=conectar()
    cursor=conn.cursor()

    cursor.execute("DELETE FROM visitantes WHERE id=?",(id,))

    conn.commit()
    conn.close()

    return redirect("/")


@app.route("/ocorrencia",methods=["POST"])
def ocorrencia():

    conn=conectar()
    cursor=conn.cursor()

    cursor.execute("INSERT INTO ocorrencias(data,descricao) VALUES(?,?)",(
        agora(),
        request.form["descricao"]
    ))

    conn.commit()
    conn.close()

    return redirect("/")


@app.route("/excluir_ocorrencia/<int:id>",methods=["POST"])
def excluir_ocorrencia(id):

    conn=conectar()
    cursor=conn.cursor()

    cursor.execute("DELETE FROM ocorrencias WHERE id=?",(id,))

    conn.commit()
    conn.close()

    return redirect("/")


@app.route("/manifest.json")
def manifest():
    return send_file("manifest.json")


# ----------------------
# EXECUÇÃO
# ----------------------

if __name__ == "__main__":

    criar_tabelas()

    port=int(os.environ.get("PORT",5000))

    app.run(host="0.0.0.0",port=port)
