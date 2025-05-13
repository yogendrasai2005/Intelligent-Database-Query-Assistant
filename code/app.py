from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
import mysql.connector
import requests
import re
import uuid
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here')

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', 'jaihanuman'),
    'database': os.getenv('DB_NAME', 'chat_history_db')
}

# Initialize database with users table
def init_db():
    try:
        connection = mysql.connector.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            use_pure=True
        )
        cursor = connection.cursor()
        
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
        cursor.execute(f"USE {DB_CONFIG['database']}")
        
        # Create history table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INT AUTO_INCREMENT PRIMARY KEY,
            session_id VARCHAR(36) NOT NULL,
            question_number INT NOT NULL,
            question TEXT NOT NULL,
            result TEXT,
            sql_query TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            INDEX (session_id)
        )
        """)
        
        # Create users table (without password hashing)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(50) NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        connection.commit()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Error initializing database: {str(e)}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

init_db()

# Database helper function
def get_db_connection():
    return mysql.connector.connect(
        host=DB_CONFIG['host'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        database=DB_CONFIG['database'],
        use_pure=True
    )

# User management functions
def create_user(username, email, password):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        cursor.execute("""
        INSERT INTO users (username, email, password)
        VALUES (%s, %s, %s)
        """, (username, email, password))
        
        connection.commit()
        return cursor.lastrowid
    except mysql.connector.Error as err:
        print(f"Error creating user: {err}")
        raise
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

def get_user_by_username(username):
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("""
        SELECT * FROM users WHERE username = %s
        """, (username,))
        
        return cursor.fetchone()
    except mysql.connector.Error as err:
        print(f"Error getting user: {err}")
        return None
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

# SQL Conversion
def convert_to_sql_groq(nl_query, api_key):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama3-70b-8192",
        "messages": [
            {"role": "system", "content": "You are an assistant that converts English to SQL queries."},
            {"role": "user", "content": f"Convert this to SQL: {nl_query}"}
        ],
        "temperature": 0.2
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        
        result = response.json()
        raw_output = result["choices"][0]["message"]["content"].strip()

        matches = re.findall(r"```(?:sql)?\s*(.*?)\s*```", raw_output, re.DOTALL | re.IGNORECASE)
        if matches:
            sql_output = matches[0].strip()
        else:
            sql_output = raw_output.splitlines()[0].strip()

        print("🧠 Cleaned SQL:", sql_output)
        return sql_output
    except Exception as e:
        raise Exception(f"Error converting to SQL: {str(e)}")

# SQL Execution
def execute_sql_query(sql_query, db_config):
    try:
        connection = mysql.connector.connect(
            host=db_config['host'],
            user=db_config['username'],
            password=db_config['password'],
            database=db_config['database'],
            use_pure=True,
            connection_timeout=10
        )
        cursor = connection.cursor()
        cursor.execute(sql_query)

        if cursor.with_rows:
            result = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return {"columns": columns, "rows": result}
        else:
            connection.commit()
            return {"columns": [], "rows": [["✅ Query executed successfully."]]}
    except Exception as e:
        return {"columns": [], "rows": [[f"❌ Error: {str(e)}"]]}
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

# History Management
def save_to_history(session_id, question_number, question, result, sql_query):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        cursor.execute("""
        INSERT INTO history (session_id, question_number, question, result, sql_query)
        VALUES (%s, %s, %s, %s, %s)
        """, (session_id, question_number, question, str(result), sql_query))
        
        connection.commit()
        print(f"💾 Saved to history: Session {session_id}, Q{question_number}")
    except Exception as e:
        print(f"❌ Error saving to history: {str(e)}")
        raise
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

def get_history(session_id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("""
        SELECT question_number, question, result, sql_query, created_at
        FROM history
        WHERE session_id = %s
        ORDER BY question_number ASC
        """, (session_id,))
        
        return cursor.fetchall()
    except Exception as e:
        print(f"❌ Error getting history: {str(e)}")
        return []
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

def get_all_sessions():
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("""
        SELECT DISTINCT session_id, MAX(created_at) as last_activity
        FROM history
        GROUP BY session_id
        ORDER BY last_activity DESC
        """)
        
        return cursor.fetchall()
    except Exception as e:
        print(f"❌ Error getting sessions: {str(e)}")
        return []
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

# Routes
@app.route("/")
def home():
    return render_template("landingpage.html")

@app.route("/signup", methods=['GET', 'POST'])
def signup():
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Basic validation
        if not username or not email or not password:
            flash('All fields are required', 'error')
            return redirect(url_for('signup'))
        
        # Check if username or email already exists
        existing_user = get_user_by_username(username)
        if existing_user:
            flash('Username already taken', 'error')
            return redirect(url_for('signup'))
        
        try:
            # Create new user (password stored as plain text)
            user_id = create_user(username, email, password)
            
            # Log the user in
            session['user_id'] = user_id
            session['username'] = username
            flash('Account created successfully!', 'success')
            return redirect(url_for('index'))
        except mysql.connector.Error as err:
            flash('Error creating account. Please try again.', 'error')
            return redirect(url_for('signup'))
    
    return render_template("signup.html")

@app.route("/login", methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Please enter both username and password', 'error')
            return redirect(url_for('login'))
        
        user = get_user_by_username(username)
        
        # Check if user exists and password matches (plain text comparison)
        if not user or user['password'] != password:
            flash('Invalid username or password', 'error')
            return redirect(url_for('login'))
        
        # Login successful
        session['user_id'] = user['id']
        session['username'] = user['username']
        flash('Logged in successfully!', 'success')
        return redirect(url_for('index'))
    
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

@app.route("/index")
def index():
    if 'user_id' not in session:
        flash('Please login to access this page', 'error')
        return redirect(url_for('login'))
    return render_template("index.html")

@app.route("/convert", methods=["POST"])
def convert():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
        
    data = request.get_json()

    try:
        nl_query = data.get("query")
        api_key = data.get("apiKey")
        session_id = data.get("sessionId", str(uuid.uuid4()))
        question_number = data.get("questionNumber", 1)
        
        db_config = {
            "host": data.get("host", DB_CONFIG['host']),
            "username": data.get("username", DB_CONFIG['user']),
            "password": data.get("password", DB_CONFIG['password']),
            "database": data.get("database", DB_CONFIG['database'])
        }

        if not nl_query:
            return jsonify({"error": "Query is required"}), 400
        if not api_key:
            return jsonify({"error": "API key is required"}), 400

        sql_query = convert_to_sql_groq(nl_query, api_key)
        result = execute_sql_query(sql_query, db_config)
        
        save_to_history(session_id, question_number, nl_query, result, sql_query)
        
        return jsonify({
            "sql": sql_query,
            "result": result,
            "questionNumber": question_number + 1,
            "sessionId": session_id
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/history", methods=["GET"])
def get_chat_history():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
        
    session_id = request.args.get("sessionId")
    if not session_id:
        return jsonify({"error": "sessionId parameter is required"}), 400
    
    history = get_history(session_id)
    return jsonify(history)

@app.route("/sessions", methods=["GET"])
def get_all_chat_sessions():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
        
    sessions = get_all_sessions()
    return jsonify(sessions)

@app.route("/test-connection", methods=["POST"])
def test_connection():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
        
    data = request.get_json()
    
    try:
        connection = mysql.connector.connect(
            host=data.get("host", DB_CONFIG['host']),
            user=data.get("username", DB_CONFIG['user']),
            password=data.get("password", DB_CONFIG['password']),
            database=data.get("database", DB_CONFIG['database']),
            connection_timeout=5
        )
        return jsonify({"status": "success", "message": "Connection successful"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    finally:
        if 'connection' in locals() and connection.is_connected():
            connection.close()

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)