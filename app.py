from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = '123'

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
    valor REAL
)
''')

conn.commit()


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


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect('/')

    user_id = session['user_id']

    if request.method == 'POST':
        descricao = request.form['descricao']
        valor = float(request.form['valor'])
        tipo = request.form['tipo']

        if tipo == 'despesa':
            valor = -abs(valor)

        cursor.execute(
            "INSERT INTO transacoes (user_id, descricao, valor) VALUES (?,?,?)",
            (user_id, descricao, valor)
        )
        conn.commit()

    transacoes = cursor.execute(
        "SELECT * FROM transacoes WHERE user_id=?",
        (user_id,)
    ).fetchall()

    total = sum(t[3] for t in transacoes)
    receitas = sum(t[3] for t in transacoes if t[3] > 0)
    despesas = abs(sum(t[3] for t in transacoes if t[3] < 0))

    return render_template(
        'dashboard.html',
        transacoes=transacoes,
        total=total,
        receitas=receitas,
        despesas=despesas
    )


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


if __name__ == '__main__':
    app.run(debug=True)