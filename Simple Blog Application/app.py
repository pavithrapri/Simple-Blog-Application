from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3  
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "your_secret_key"  

DATABASE = 'blog_app.db'  

def get_db():
    conn = sqlite3.connect(DATABASE)
    return conn

def create_tables():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            user_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
    """)
    conn.commit()
    conn.close()

# Initialize the database tables
create_tables()

# Routes and functionality

@app.route('/')
def home():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM posts ORDER BY created_at DESC")
    posts = cursor.fetchall()
    conn.close()
    return render_template('index.html', posts=posts)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            return redirect(url_for('dashboard'))
        else:
            return "Invalid login, please try again.", 400
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return "Username already exists!", 400
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM posts WHERE user_id=?", (user_id,))
    posts = cursor.fetchall()
    conn.close()
    return render_template('dashboard.html', posts=posts)

@app.route('/create_post', methods=['GET', 'POST'])
def create_post():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        user_id = session['user_id']

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO posts (title, content, user_id) VALUES (?, ?, ?)", (title, content, user_id))
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))

    return render_template('create_post.html')

@app.route('/post/<int:post_id>')
def view_post(post_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM posts WHERE id=?", (post_id,))
    post = cursor.fetchone()
    conn.close()
    if post:
        return render_template('view_post.html', post=post)
    return "Post not found", 404

@app.route('/edit_post/<int:post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))  

    user_id = session['user_id']  
    conn = get_db()  
    cursor = conn.cursor()

    # Check if the post belongs to the logged-in user
    cursor.execute("SELECT * FROM posts WHERE id=? AND user_id=?", (post_id, user_id))
    post = cursor.fetchone()

    # If the post doesn't belong to the logged-in user, return a permission error
    if not post:
        return "You don't have permission to edit this post", 403

    if request.method == 'POST':  # If the form is submitted via POST method
        title = request.form['title']  # Get the new title from the form
        content = request.form['content']  # Get the new content from the form
        
        cursor.execute("UPDATE posts SET title=?, content=? WHERE id=?", (title, content, post_id))
        conn.commit()  
        conn.close()  
        
        return redirect(url_for('dashboard')) 
    
    conn.close() 
    return render_template('edit_post.html', post=post)


@app.route('/delete_post/<int:post_id>', methods=['POST'])
def delete_post(post_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor()

    # Fetch the post and ensure it belongs to the logged-in user
    cursor.execute("SELECT * FROM posts WHERE id=? AND user_id=?", (post_id, user_id))
    post = cursor.fetchone()

    if not post:
        return "You don't have permission to delete this post", 403  # Permission error if post doesn't belong to the user

    cursor.execute("DELETE FROM posts WHERE id=?", (post_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))  # Redirect to dashboard after deleting

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug=True)
