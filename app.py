from flask import Flask, render_template, request, redirect, session, url_for, flash
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
import os
import csv

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Upload folder
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# MySQL connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="#Sweety143",
    database="gadget_test_db"
)
cursor = db.cursor(dictionary=True)

# ---------------------- ROUTES ----------------------

# Home Page
@app.route('/')
def home():
    return render_template('home.html')

# Registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        email = request.form['email']
        username = request.form['username']
        password = generate_password_hash(request.form['password'])

        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        existing_user = cursor.fetchone()
        if existing_user:
            flash("Username already exists. Please choose another.")
            return redirect('/register')

        cursor.execute("INSERT INTO users (name, phone, email, username, password) VALUES (%s, %s, %s, %s, %s)",
                       (name, phone, email, username, password))
        db.commit()
        flash("Registration successful. Please log in.")
        return redirect('/login')
    return render_template('register.html')

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect('/')
        else:
            flash("Invalid username or password")
            return redirect('/login')
    return render_template('login.html')

# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# Test Page
@app.route('/test')
def test():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('test.html')

# Test Result
@app.route('/result', methods=['POST'])
def result():
    if 'user_id' not in session:
        return redirect('/login')

    total_score = 0
    for i in range(1, 11):  
        answer = request.form.get(f'q{i}')
        if answer and answer.isdigit():
            total_score += int(answer)

    if total_score < 6:
        result_text = "Stage 1: No Impact of Gadget Addiction"
    elif total_score < 12:
        result_text = "Stage 2: Moderate Usage with Minor Impact"
    elif total_score < 18:
        result_text = "Stage 3: Frequent Usage with Noticeable Impact"
    else:
        result_text = "Stage 4: High Usage with Significant Impact"

    cursor.execute("INSERT INTO results (user_id, score, result) VALUES (%s, %s, %s)",
                   (session['user_id'], total_score, result_text))
    db.commit()

    return render_template('result.html', score=total_score, result=result_text)

# Dashboard
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    cursor.execute("SELECT score, result, timestamp FROM results WHERE user_id = %s ORDER BY timestamp DESC",
                   (session['user_id'],))
    results = cursor.fetchall()
    return render_template('dashboard.html', results=results)

# File Upload & Bulk Prediction
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'user_id' not in session:
        return redirect('/login')

    predictions = []

    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)

        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if file:
            # ✅ Create Upload Folder if not Exists
            upload_folder = os.path.join('static', 'uploads')
            os.makedirs(upload_folder, exist_ok=True)

            # ✅ Save File
            filename = file.filename
            filepath = os.path.join(upload_folder, filename)
            file.save(filepath)

            # ✅ Process CSV File
            try:
                with open(filepath, newline='') as csvfile:
                    reader = csv.DictReader(csvfile)
                    for row in reader:
                        try:
                            score = sum(int(row[f'q{i}']) for i in range(1, 11))
                            if score < 6:
                                result = "Stage 1: No Impact"
                            elif score < 12:
                                result = "Stage 2: Moderate Impact"
                            elif score < 18:
                                result = "Stage 3: Noticeable Impact"
                            else:
                                result = "Stage 4: Significant Impact"
                            predictions.append({'score': score, 'result': result})
                        except Exception as e:
                            predictions.append({'score': 'Invalid', 'result': f'Error: {e}'})
            except Exception as e:
                flash(f"Failed to process CSV: {e}")
                return redirect(request.url)

    return render_template('upload.html', predictions=predictions)

# ---------------------- RUN ----------------------
if __name__ == '__main__':
    app.run(debug=True)
