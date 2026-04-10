import datetime

"""
Portaria Parque das Rosas WEB (Flask + SQLite)
OFFLINE COMPLETO (SALVA SEM INTERNET + SINCRONIZA)
"""

from flask import Flask, render_template_string, request, redirect, send_file, jsonify
from datetime import datetime
import sqlite3
import os
from zoneinfo import ZoneInfo

app = Flask(__name__)

# ----------------------
# STATIC + SERVICE WORKER
# ----------------------

if not os.path.exists('static'):
    os.makedirs('static')

sw_path = os.path.join('static','sw.js')
if not os.path.exists(sw_path):
    with open(sw_path,'w') as f:
        f.write("""
self.addEventListener('install', e => self.skipWaiting());
self.addEventListener('fetch', () => {});
""")

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
        data TEXT,
        descricao TEXT
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
# HTML COM OFFLINE
# ----------------------

HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Portaria Parque das Rosas</title>
<meta name="theme-color" content="#1e1e2f">
<style>
body{font-family:Arial;background:#1e1e2f;color:white}
button{padding:10px;border-radius:8px;border:none}
input,textarea{padding:10px;border-radius:8px;border:none}
</style>
</head>
<body>
<h1>🚪 Portaria Parque das Rosas</h1>

<form id="formCadastro">
<input name="nome" placeholder="Nome" required>
<input name="documento" placeholder="Documento" required>
<button>Cadastrar</button>
</form>

<h3 id="status"></h3>

<script>

// FILA OFFLINE
function salvarOffline(tipo,dados){
    let fila = JSON.parse(localStorage.getItem("fila") || "[]");
    fila.push({tipo,dados});
    localStorage.setItem("fila", JSON.stringify(fila));
}

// ENVIAR FILA
async function sincronizar(){
    let fila = JSON.parse(localStorage.getItem("fila") || "[]");

    if(fila.length===0) return;

    for(let item of fila){
        await fetch("/sync",{
            method:"POST",
            headers:{"Content-Type":"application/json"},
            body:JSON.stringify(item)
        });
    }

    localStorage.removeItem("fila");
}

// DETECTAR ONLINE
window.addEventListener("online", sincronizar);

// CADASTRO

document.getElementById("formCadastro").onsubmit = async (e)=>{
    e.preventDefault();

    let dados = Object.fromEntries(new FormData(e.target));

    if(navigator.onLine){
        await fetch("/sync",{
            method:"POST",
            headers:{"Content-Type":"application/json"},
            body:JSON.stringify({tipo:"cadastro",dados})
        });
        document.getElementById("status").innerText = "✅ Enviado";
    }else{
        salvarOffline("cadastro",dados);
        document.getElementById("status").innerText = "📴 Salvo offline";
    }

    e.target.reset();
};

</script>
</body>
</html>
"""

# ----------------------
# ROTAS
# ----------------------

@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/sync", methods=["POST"])
def sync():

    data = request.get_json()

    conn = conectar()
    c = conn.cursor()

    if data["tipo"] == "cadastro":
        d = data["dados"]
        c.execute("""
        INSERT INTO visitantes(nome,documento,entrada,saida)
        VALUES(?,?,?,?)
        """,(d.get("nome"), d.get("documento"), agora(), ""))

    conn.commit()
    conn.close()

    return jsonify({"status":"ok"})


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
