from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('events.db')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            object_or_status TEXT NOT NULL,
            location TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            photo_path TEXT
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    conn = sqlite3.connect('events.db')
    conn.row_factory = sqlite3.Row
    events = conn.execute('SELECT * FROM events ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('index.html', events=events)

@app.route('/add_test_event')
def add_test_event():
    conn = sqlite3.connect('events.db')
    conn.execute(
        'INSERT INTO events (object_or_status, location, timestamp, photo_path) VALUES (?, ?, ?, ?)',
        ('Laptop', 'Classroom 101', datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'photos/sample.jpg')
    )
    conn.commit()
    conn.close()
    return redirect('/')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)