import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, g

app = Flask(__name__)
app.secret_key = 'your_secret_key'
DATABASE = 'contacts.db'


# Database connection management
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()


# Initialize the database
def init_db():
    db = get_db()
    db.execute('''
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            email TEXT
        )
    ''')
    db.commit()


# Index route to list all contacts
@app.route('/')
def index():
    db = get_db()
    contacts = db.execute('SELECT * FROM contacts').fetchall()
    return render_template('index.html', contacts=contacts)


# Add contact route
@app.route('/add', methods=('GET', 'POST'))
def add_contact():
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        email = request.form['email']

        if not name:
            flash('Name is required!', 'error')
            return render_template('add_contact.html')

        try:
            db = get_db()
            db.execute('INSERT INTO contacts (name, phone, email) VALUES (?, ?, ?)',
                       (name, phone, email))
            db.commit()
            flash('Contact successfully added!', 'success')
            return redirect(url_for('index'))
        except sqlite3.Error as e:
            flash(f'An error occurred: {e}', 'error')
    return render_template('add_contact.html')


# Edit contact route
@app.route('/edit/<int:id>', methods=('GET', 'POST'))
def edit_contact(id):
    db = get_db()
    contact = db.execute('SELECT * FROM contacts WHERE id = ?', (id,)).fetchone()

    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        email = request.form['email']

        if not name:
            flash('Name is required!', 'error')
            return render_template('edit_contact.html', contact=contact)

        try:
            db.execute('UPDATE contacts SET name = ?, phone = ?, email = ? WHERE id = ?',
                       (name, phone, email, id))
            db.commit()
            flash('Contact successfully updated!', 'success')
            return redirect(url_for('index'))
        except sqlite3.Error as e:
            flash(f'An error occurred: {e}', 'error')

    return render_template('edit_contact.html', contact=contact)


# Delete contact route
@app.route('/delete/<int:id>', methods=('POST',))
def delete_contact(id):
    try:
        db = get_db()
        db.execute('DELETE FROM contacts WHERE id = ?', (id,))
        db.commit()
        flash('Contact successfully deleted!', 'success')
    except sqlite3.Error as e:
        flash(f'An error occurred: {e}', 'error')
    return redirect(url_for('index'))


# Initialize the database when the app starts
if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=True)
