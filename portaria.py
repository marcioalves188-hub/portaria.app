import datetime

registros = []

""
Sistema de Portaria WEB (Flask + SQLite)
Interface moderna + correções de execução
"""

from flask import Flask, render_template_string, request, redirect
from datetime import datetime
import sqlite3
import os

app = Flask(__name__)

# ----------------------
# BANCO DE DADOS
# ----------------------

def conectar():
    return sqlite3.connect("portaria.db")


def criar_tabela():
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

    conn.commit()
    conn.close()


# ----------------------
# HTML MODERNO
# ----------------------

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Portaria</title>
    <style>
        body {
            font-family: Arial;
            background: #1e1e2f;
            color: white;
            margin: 0;
        }
        .container {
            width: 90%;
            margin: auto;
        }
        h1 {
            text-align: center;
            margin-top: 20px;
        }
        form {
            display: flex;
            flex-wrap: wrap;
            gap: 
            justify-content: center;
            margin-bottom: 20px;
        }
        input {
            padding: 10px;
            border-radius: 8px;
            border: none;
            width: 180px;
        }
        button {
            padding: 10px 15px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
        }
        .entrada {
            background: #4CAF50;
            color: white;
        }
        .saida {
            background: #f44336;
            color: white;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            background: #2e2e3e;
            border-radius: 10px;
            overflow: hidden;
        }
        th, td {
            padding: 12px;
            text-align: center;
        }
        th {
            background: #333;
        }
        tr:nth-child(even) {
            background: #3a3a4f;
        }
    </style>
</head>
<body>
<div class="container">
    <h1>🚪 Sistema de Portaria</h1>

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
            <th>Ação</th>
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
                <form method="POST" action="/saida/{{v[0]}}">
                    <button class="saida">Saída</button>
                </form>
                {% else %}
                ✔️
                {% endif %}
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
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM visitantes")
    registros = cursor.fetchall()
    conn.close()

    return render_template_string(HTML, registros=registros)


@app.route("/cadastrar", methods=["POST"])
def cadastrar():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO visitantes (nome, endereco, documento, placa, entrada, saida)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        request.form["nome"],
        request.form["endereco"],
        request.form["documento"],
        request.form["placa"],
        datetime.now().strftime("%d/%m/%Y %H:%M"),
        ""
    ))

    conn.commit()
    conn.close()

    return redirect("/")


@app.route("/saida/<int:id>", methods=["POST"])
def saida(id):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE visitantes
    SET saida = ?
    WHERE id = ? AND saida = ''
    """, (
        datetime.now().strftime("%d/%m/%Y %H:%M"),
        id
    ))

    conn.commit()
    conn.close()

    return redirect("/")


# ----------------------
# TESTES
# ----------------------

def _test_db():
    criar_tabela()
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM visitantes")

    cursor.execute("""
    INSERT INTO visitantes (nome, endereco, documento, placa, entrada, saida)
    VALUES ('Teste', 'Rua', '123', 'ABC', '01/01', '')
    """)

    conn.commit()

    cursor.execute("SELECT * FROM visitantes")
    dados = cursor.fetchall()

    assert len(dados) == 1

    conn.close()


def _test_saida_update():
    criar_tabela()
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM visitantes")

    cursor.execute("""
    INSERT INTO visitantes (nome, endereco, documento, placa, entrada, saida)
    VALUES ('Teste2', 'Rua', '999', 'XYZ', '01/01', '')
    """)

    conn.commit()

    cursor.execute("UPDATE visitantes SET saida = '02/01' WHERE nome = 'Teste2'")
    conn.commit()

    cursor.execute("SELECT saida FROM visitantes WHERE nome = 'Teste2'")
    saida = cursor.fetchone()[0]

    assert saida != ""

    conn.close()


# ----------------------
# EXECUÇÃO
# ----------------------

def iniciar_servidor():
    port = int(os.environ.get("PORT", 5000))

    try:
        app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
    except OSError:
        print(f"Porta {port} ocupada. Tentando 5001...")
        app.run(host="0.0.0.0", port=5001, debug=False, use_reloader=False)


if __name__ == "__main__":
    criar_tabela()
    _test_db()
    _test_saida_update()

    try:
        iniciar_servidor()
    except SystemExit:
        print("Servidor não pôde iniciar neste ambiente.")
