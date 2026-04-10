import datetime

"""
Sistema de Portaria WEB (Flask + SQLite)
VERSÃO PROFISSIONAL (PWA + OFFLINE + SPLASH)
"""

from flask import Flask, render_template_string, request, redirect, send_file
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
# HTML PROFISSIONAL
# ----------------------

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Portaria</title>

    <link rel="manifest" href="/manifest.json">
    <meta name="theme-color" content="#1e1e2f">

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
        }
        form {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
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
        .entrada { background: #4CAF50; }
        .saida { background: #f44336; }
        .excluir { background: #ff9800; }

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
        th { background: #333; }
        tr:nth-child(even) { background: #3a3a4f; }

        #splash {
            position: fixed;
            width: 100%;
            height: 100%;
            background: #1e1e2f;
            display: flex;
            justify-content: center;
            align-items: center;
            font-size: 24px;
            z-index: 9999;
        }
    </style>
</head>
<body>

<div id="splash">🚪 Portaria</div>

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
                <form method="POST" action="/saida/{{v[0]}}" style="display:inline;">
                    <button class="saida">Saída</button>
                </form>
                {% endif %}

                <form method="POST" action="/excluir/{{v[0]}}" style="display:inline;" onsubmit="return confirm('Excluir este registro?')">
                    <button class="excluir">Excluir</button>
                </form>
            </td>
        </tr>
        {% endfor %}
    </table>
</div>

<script>
// Splash
window.onload = () => {
  document.getElementById("splash").style.display = "none";
};

// Service Worker
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/static/sw.js');
}
</script>

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


@app.route("/excluir/<int:id>", methods=["POST"])
def excluir(id):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM visitantes WHERE id = ?", (id,))

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
    criar_tabela()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
