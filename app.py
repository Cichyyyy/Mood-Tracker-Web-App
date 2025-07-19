import sqlite3
import os
from flask import Flask, render_template, request, redirect, session, url_for, flash
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'tajny_klucz'  # Zmień na własny sekret

# 🔧 Ścieżka bazy
db_path = os.path.join(os.path.dirname(__file__), 'data.db')

@app.route('/')
def index():
    work_id = request.args.get('work_id')
    if not work_id:
        return redirect('/login')

    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()
        c.execute('SELECT timestamp FROM mood_entries WHERE work_id = ? ORDER BY timestamp DESC LIMIT 1', (work_id,))
        last = c.fetchone()

    if last:
        last_time = datetime.fromisoformat(last[0])
        if datetime.now() - last_time < timedelta(hours=24):
            return "Możesz wypełnić ankietę ponownie po 24h."

    return render_template('index.html', work_id=work_id)

@app.route('/submit', methods=['POST'])
def submit():
    work_id = request.form.get('work_id')
    if not work_id:
        return redirect('/login')

    mood = request.form['mood']
    comment = request.form['comment']
    timestamp = datetime.now().isoformat()

    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()
        c.execute('INSERT INTO mood_entries (work_id, mood, comment, timestamp) VALUES (?, ?, ?, ?)',
                  (work_id, mood, comment, timestamp))
        conn.commit()

    return redirect('/login')

@app.template_filter('format_datetime')
def format_datetime(value):
    try:
        dt = datetime.fromisoformat(value)
        return dt.strftime('%d-%m-%Y | %H:%M')
    except:
        return value

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        work_id = request.form['work_id']
        return redirect(url_for('index', work_id=work_id))
    return render_template('login.html')

@app.route('/go_dashboard', methods=['POST'])
def go_dashboard():
    password = request.form.get('admin_pass')
    if password == 'admin123':  # Zmień na silne hasło
        session['admin_logged_in'] = True
        return redirect('/dashboard')
    flash('Błędne hasło do dashboardu.')
    return redirect('/login')

@app.route('/dashboard')
def dashboard():
    if not session.get('admin_logged_in'):
        flash('Dostęp tylko po podaniu hasła.')
        return redirect('/login')

    work_id_filter = request.args.get('work_id', '')
    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()
        if work_id_filter:
            c.execute('''
                SELECT mood, comment, timestamp, work_id, id FROM mood_entries
                WHERE work_id LIKE ?
                ORDER BY timestamp DESC
            ''', ('%' + work_id_filter + '%',))
        else:
            c.execute('SELECT mood, comment, timestamp, work_id, id FROM mood_entries ORDER BY timestamp DESC')
        entries = c.fetchall()
    return render_template('dashboard.html', entries=entries)

@app.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    return redirect('/login')

@app.route('/delete_entries', methods=['POST'])
def delete_entries():
    if not session.get('admin_logged_in'):
        flash('Brak dostępu.')
        return redirect('/login')

    ids = request.form.getlist('delete_ids')
    if ids:
        with sqlite3.connect(db_path) as conn:
            c = conn.cursor()
            c.executemany('DELETE FROM mood_entries WHERE id = ?', [(i,) for i in ids])
            conn.commit()
    return redirect('/dashboard')

@app.route('/edit/<int:entry_id>', methods=['GET', 'POST'])
def edit_entry(entry_id):
    if not session.get('admin_logged_in'):
        flash('Brak dostępu.')
        return redirect('/login')

    if request.method == 'POST':
        mood = request.form['mood']
        comment = request.form['comment']
        with sqlite3.connect(db_path) as conn:
            c = conn.cursor()
            c.execute('UPDATE mood_entries SET mood = ?, comment = ? WHERE id = ?', (mood, comment, entry_id))
            conn.commit()
        return redirect('/dashboard')

    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()
        c.execute('SELECT mood, comment FROM mood_entries WHERE id = ?', (entry_id,))
        entry = c.fetchone()

    if not entry:
        flash('Nie znaleziono wpisu do edycji.')
        return redirect('/dashboard')

    return render_template('edit.html', entry=entry, entry_id=entry_id)

if __name__ == '__main__':
    print(">> Ścieżka bazy danych:", db_path)
    app.run(debug=True)
