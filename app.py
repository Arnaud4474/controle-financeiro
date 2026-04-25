from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime
from collections import defaultdict
import os

app = Flask(__name__)
app.secret_key = '123'

# conexão com banco
conn = sqlite3.connect('dados.db', check_same_thread=False)
cursor = conn.cursor()

# criar tabelas
cursor.execute('''
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    senha TEXT
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS transacoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    descricao TEXT,
    valor REAL,
    categoria TEXT,
    data TEXT
)
''')

conn.commit()

# evitar erro se já existir coluna
try:
    cursor.execute("ALTER TABLE transacoes ADD COLUMN categoria TEXT")
except:
    pass

try:
    cursor.execute("ALTER TABLE transacoes ADD COLUMN data TEXT")
except:
    pass


# LOGIN
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        senha = request.form['senha']

        user = cursor.execute(
            "SELECT * FROM usuarios WHERE username=? AND senha=?",
            (username, senha)
        ).fetchone()

        if user:
            session['user_id'] = user[0]
            return redirect('/dashboard')

    return render_template('login.html')


# REGISTRO
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        senha = request.form['senha']

        cursor.execute(
            "INSERT INTO usuarios (username, senha) VALUES (?,?)",
            (username, senha)
        )
        conn.commit()

        return redirect('/')

    return render_template('register.html')


# DASHBOARD
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect('/')

    user_id = session['user_id']

    # salvar nova transação
    if request.method == 'POST':
        descricao = request.form['descricao']
        valor = float(request.form['valor'])
        tipo = request.form['tipo']
        categoria = request.form['categoria']

        if tipo == 'despesa':
            valor = -abs(valor)

        data = datetime.now().strftime('%Y-%m')

        cursor.execute(
            "INSERT INTO transacoes (user_id, descricao, valor, categoria, data) VALUES (?,?,?,?,?)",
            (user_id, descricao, valor, categoria, data)
        )
        conn.commit()

    # filtro por mês
    mes = request.args.get('mes')

    if mes:
        transacoes = cursor.execute(
            "SELECT * FROM transacoes WHERE user_id=? AND data=?",
            (user_id, mes)
        ).fetchall()
    else:
        transacoes = cursor.execute(
            "SELECT * FROM transacoes WHERE user_id=?",
            (user_id,)
        ).fetchall()

    # cálculos
    total = sum(t[3] for t in transacoes)
    receitas = sum(t[3] for t in transacoes if t[3] > 0)
    despesas = abs(sum(t[3] for t in transacoes if t[3] < 0))

    # gráfico por categoria
    categorias = defaultdict(float)

    for t in transacoes:
        if t[3] < 0:
            categorias[t[4]] += abs(t[3])

    labels = list(categorias.keys())
    valores = list(categorias.values())

    return render_template(
        'dashboard.html',
        transacoes=transacoes,
        total=total,
        receitas=receitas,
        despesas=despesas,
        labels=labels,
        valores=valores
    )


# LOGOUT
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


# RODAR LOCAL + ONLINE
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)