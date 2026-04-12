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
# HTML (SEU MESMO)
# ----------------------
HTML = """COLE AQUI SEU HTML (o que você mandou está perfeito)"""

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
    """, (termo, termo, termo, termo, limite + 1, offset))

    dados = c.fetchall()

    tem_proxima = len(dados) > limite
    registros = dados[:limite]

    c.execute("SELECT * FROM ocorrencias ORDER BY id DESC")
    ocorrencias = c.fetchall()

    conn.close()

    return render_template_string(HTML,
        registros=registros,
        pagina=pagina,
        tem_proxima=tem_proxima,
        busca=busca,
        ocorrencias=ocorrencias
    )

# ✅ CADASTRAR
@app.route("/cadastrar", methods=["POST"])
def cadastrar():
    conn = conectar()
    c = conn.cursor()

    c.execute("""
    INSERT INTO visitantes(nome,endereco,documento,placa,entrada,saida)
    VALUES(?,?,?,?,?,?)
    """, (
        request.form["nome"],
        request.form.get("endereco", ""),
        request.form["documento"],
        request.form.get("placa", ""),
        agora(),
        ""
    ))

    conn.commit()
    conn.close()

    return redirect("/")

# ✅ SAÍDA
@app.route("/saida/<int:id>", methods=["POST"])
def registrar_saida(id):
    conn = conectar()
    c = conn.cursor()

    c.execute("""
    UPDATE visitantes SET saida=? 
    WHERE id=? AND saida=''
    """, (agora(), id))

    conn.commit()
    conn.close()

    return redirect("/")

# ✅ EXCLUIR VISITANTE
@app.route("/excluir/<int:id>", methods=["POST"])
def excluir(id):
    conn = conectar()
    c = conn.cursor()

    c.execute("DELETE FROM visitantes WHERE id=?", (id,))

    conn.commit()
    conn.close()

    return redirect("/")

# ✅ OCORRÊNCIA
@app.route("/ocorrencia", methods=["POST"])
def ocorrencia():
    conn = conectar()
    c = conn.cursor()

    c.execute("""
    INSERT INTO ocorrencias(nome,descricao,data)
    VALUES(?,?,?)
    """, (
        request.form.get("nome", ""),
        request.form["descricao"],
        agora()
    ))

    conn.commit()
    conn.close()

    return redirect("/")

# ✅ EXCLUIR OCORRÊNCIA
@app.route("/excluir_ocorrencia/<int:id>", methods=["POST"])
def excluir_ocorrencia(id):
    conn = conectar()
    c = conn.cursor()

    c.execute("DELETE FROM ocorrencias WHERE id=?", (id,))

    conn.commit()
    conn.close()

    return redirect("/")

# ----------------------
# EXECUÇÃO
# ----------------------
if __name__ == "__main__":
    criar_tabelas()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
