from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)

# 🔧 Ustal ścieżkę absolutną do pliku bazy danych
db_path = os.path.join(os.path.dirname(__file__), 'data.db')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    mood = request.form['mood']
    comment = request.form['comment']
    timestamp = datetime.now().isoformat()

    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()
        c.execute('INSERT INTO mood_entries (mood, comment, timestamp) VALUES (?, ?, ?)',
                  (mood, comment, timestamp))
        conn.commit()

    return redirect('/dashboard')

@app.route('/dashboard')
def dashboard():
    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()
        c.execute('SELECT mood, comment, timestamp FROM mood_entries ORDER BY timestamp DESC')
        entries = c.fetchall()
    return render_template('dashboard.html', entries=entries)

if __name__ == '__main__':
    print(">> Ścieżka bazy danych:", db_path)
    app.run(debug=True)
