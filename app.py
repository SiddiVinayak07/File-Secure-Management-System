from flask import Flask, request, jsonify, render_template, session, redirect, url_for, send_file
import os
import json
from cosmic_file_locker import CosmicFileLocker
import logging

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = 'cosmic_secret_2025'
locker = CosmicFileLocker()
users_file = 'users.json'

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Load users from JSON file
def load_users():
    try:
        if os.path.exists(users_file):
            with open(users_file, 'r') as f:
                return json.load(f)
        return {}
    except json.JSONDecodeError as e:
        logging.error(f"Failed to decode users.json: {e}")
        return {}
    except IOError as e:
        logging.error(f"IOError loading users.json: {e}")
        return {}

# Save users to JSON file
def save_users(users):
    try:
        os.makedirs(os.path.dirname(users_file) or '.', exist_ok=True)
        with open(users_file, 'w') as f:
            json.dump(users, f, indent=4)
    except IOError as e:
        logging.error(f"Failed to save users.json: {e}")

@app.route('/')
def home():
    if 'user_id' not in session:
        return render_template('index.html')
    return redirect(url_for('lock_file'))

@app.route('/login', methods=['POST'])
def login():
    try:
        user_id = request.form.get('user_id')
        password = request.form.get('password')
        logging.debug(f"Login attempt for user_id: {user_id}")
        if not user_id or not password:
            return jsonify({"status": "error", "message": "User ID and password are required"}), 400
        users = load_users()
        user_data = users.get(user_id)
        if user_data and user_data.get('password') == password:
            session['user_id'] = user_id
            return jsonify({"status": "success", "redirect": url_for('lock_file')})
        return jsonify({"status": "error", "message": "Invalid credentials"}), 401
    except Exception as e:
        logging.error(f"Login error: {e}")
        return jsonify({"status": "error", "message": "Server error"}), 500

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    try:
        if request.method == 'POST':
            user_id = request.form.get('user_id')
            password = request.form.get('password')
            security_question = request.form.get('security_question')
            security_answer = request.form.get('security_answer')
            logging.debug(f"Signup attempt for user_id: {user_id}")
            if not all([user_id, password, security_question, security_answer]):
                return jsonify({"status": "error", "message": "All fields are required"}), 400
            users = load_users()
            if user_id in users:
                return jsonify({"status": "error", "message": "User ID already exists"}), 400
            users[user_id] = {
                'password': password,
                'security_question': security_question,
                'security_answer': security_answer
            }
            save_users(users)
            logging.debug(f"User saved: {users}")
            return jsonify({"status": "success", "redirect": url_for('login_page'), "message": "Signup successful"})
        return render_template('signup.html')
    except Exception as e:
        logging.error(f"Signup error: {e}")
        return jsonify({"status": "error", "message": f"Server error: {str(e)}"}), 500

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    try:
        if request.method == 'POST':
            step = request.form.get('step', 'user_id')
            users = load_users()
            if step == 'user_id':
                user_id = request.form.get('user_id')
                if not user_id:
                    return jsonify({"status": "error", "message": "User ID is required"}), 400
                if user_id in users:
                    return jsonify({
                        "status": "success",
                        "step": "security_question",
                        "security_question": users[user_id]['security_question'],
                        "user_id": user_id  # Pass user_id for the next step
                    })
                return jsonify({"status": "error", "message": "User ID not found"}), 404
            elif step == 'security_question':
                user_id = request.form.get('user_id')
                answer = request.form.get('security_answer')
                if not answer:
                    return jsonify({"status": "error", "message": "Security answer is required"}), 400
                if users.get(user_id, {}).get('security_answer') == answer:
                    return jsonify({"status": "success", "step": "reset_password", "user_id": user_id})
                return jsonify({"status": "error", "message": "Incorrect security answer"}), 401
            return jsonify({"status": "error", "message": "Invalid step"}), 400
        return render_template('forgot-password.html')
    except Exception as e:
        logging.error(f"Forgot password error: {e}")
        return jsonify({"status": "error", "message": f"Server error: {str(e)}"}), 500

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    try:
        if request.method == 'GET':
            user_id = request.args.get('user_id')
            if not user_id or user_id not in load_users():
                return redirect(url_for('forgot_password'))
            return render_template('reset-password.html', user_id=user_id)
        elif request.method == 'POST':
            user_id = request.form.get('user_id')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            if not all([user_id, new_password, confirm_password]):
                return jsonify({"status": "error", "message": "All fields are required"}), 400
            if new_password != confirm_password:
                return jsonify({"status": "error", "message": "Passwords do not match"}), 400
            users = load_users()
            if user_id in users:
                users[user_id]['password'] = new_password
                save_users(users)
                return jsonify({"status": "success", "redirect": url_for('login_page'), "message": "Password reset successful"})
            return jsonify({"status": "error", "message": "User not found"}), 404
    except Exception as e:
        logging.error(f"Reset password error: {e}")
        return jsonify({"status": "error", "message": f"Server error: {str(e)}"}), 500

@app.route('/login-page', methods=['GET'])
def login_page():
    return render_template('login-page.html')

@app.route('/lock', methods=['GET', 'POST'], endpoint='lock_file')
def lock_file():
    if 'user_id' not in session:
        return redirect(url_for('home'))
    if request.method == 'POST':
        try:
            user_id = session['user_id']
            password = request.form.get('password')
            file = request.files.get('file')
            if not file or not password:
                return jsonify({"status": "error", "message": "Password and file are required"}), 400
            file_path = os.path.join("uploads", file.filename).replace('\\', '/')
            os.makedirs(os.path.dirname(file_path) or '.', exist_ok=True)
            file.save(file_path)
            logging.debug(f"Attempting to lock file: {file_path} for user: {user_id}")
            file_name = locker.lock_file(user_id, password, file_path)
            if file_name:
                logging.debug(f"File locked successfully: {file_name}")
                return jsonify({"status": "success", "file_name": file_name, "message": "File locked successfully"})
            else:
                logging.error(f"Locking failed for file: {file_path} with no specific error logged")
                return jsonify({"status": "error", "message": "Failed to lock file"}), 400
        except Exception as e:
            logging.exception(f"Lock file error: {e}")
            return jsonify({"status": "error", "message": f"Locking failed: {str(e)}"}), 500
    return render_template('lock.html')

@app.route('/list', methods=['GET', 'POST'], endpoint='list_files')
def list_files():
    if 'user_id' not in session:
        return redirect(url_for('home'))
    if request.method == 'POST':
        try:
            user_id = session['user_id']
            password = request.form.get('password')
            if not password:
                return jsonify({"status": "error", "message": "Password is required"}), 400
            users = load_users()
            if users.get(user_id, {}).get('password') == password:
                files = locker.list_files(user_id)
                return jsonify({"status": "success", "files": files if files else []})
            return jsonify({"status": "error", "message": "Invalid password"}), 401
        except Exception as e:
            logging.error(f"List files error: {e}")
            return jsonify({"status": "error", "message": f"Server error: {str(e)}"}), 500
    return render_template('list.html')

@app.route('/retrieve', methods=['POST'])
def retrieve_file():
    if 'user_id' not in session:
        return jsonify({"status": "error", "message": "Login required"}), 401
    try:
        user_id = session['user_id']
        password = request.form.get('password')
        file_name = request.form.get('file_name')
        if not password or not file_name:
            return jsonify({"status": "error", "message": "Password and file name are required"}), 400
        users = load_users()
        if users.get(user_id, {}).get('password') == password:
            content = locker.retrieve_file(file_name, user_id, password)
            if content:
                temp_file = f"temp_{file_name}"
                with open(temp_file, 'wb') as f:
                    f.write(content)
                return send_file(temp_file, as_attachment=True, download_name=file_name.replace('.enc', ''))
            return jsonify({"status": "error", "message": "File not found or decryption failed"}), 404
        return jsonify({"status": "error", "message": "Invalid password"}), 401
    except Exception as e:
        logging.error(f"Retrieve file error: {e}")
        return jsonify({"status": "error", "message": f"Server error: {str(e)}"}), 500

@app.route('/delete', methods=['POST'])
def delete_file():
    if 'user_id' not in session:
        return jsonify({"status": "error", "message": "Login required"}), 401
    try:
        user_id = session['user_id']
        password = request.form.get('password')
        file_name = request.form.get('file_name')
        logging.debug(f"Attempting to delete file: {file_name} for user: {user_id}")
        if not password or not file_name:
            return jsonify({"status": "error", "message": "Password and file name are required"}), 400
        users = load_users()
        if users.get(user_id, {}).get('password') == password:
            if locker.delete_file(file_name, user_id, password):
                logging.debug(f"Successfully deleted file: {file_name}")
                return jsonify({"status": "success", "message": f"{file_name} moved to recycle bin"})
            else:
                logging.error(f"Failed to delete file: {file_name} - check file existence or permissions")
                return jsonify({"status": "error", "message": "Failed to delete file"}), 400
        return jsonify({"status": "error", "message": "Invalid password"}), 401
    except Exception as e:
        logging.exception(f"Delete file error: {e}")  # Log full traceback
        return jsonify({"status": "error", "message": f"Server error: {str(e)}"}), 500

@app.route('/recycle', methods=['GET', 'POST'], endpoint='recycle_bin')
def recycle_bin():
    if 'user_id' not in session:
        return redirect(url_for('home'))
    if request.method == 'POST':
        try:
            user_id = session['user_id']
            password = request.form.get('password')
            if not password:
                return jsonify({"status": "error", "message": "Password is required"}), 400
            users = load_users()
            if users.get(user_id, {}).get('password') == password:
                files = locker.list_recycle_bin(user_id)
                return jsonify({"status": "success", "files": files if files else []})
            return jsonify({"status": "error", "message": "Invalid password"}), 401
        except Exception as e:
            logging.error(f"Recycle bin error: {e}")
            return jsonify({"status": "error", "message": f"Server error: {str(e)}"}), 500
    return render_template('recycle.html')

@app.route('/restore', methods=['POST'])
def restore_file():
    if 'user_id' not in session:
        return jsonify({"status": "error", "message": "Login required"}), 401
    try:
        user_id = session['user_id']
        password = request.form.get('password')
        file_name = request.form.get('file_name')
        if not password or not file_name:
            return jsonify({"status": "error", "message": "Password and file name are required"}), 400
        users = load_users()
        if users.get(user_id, {}).get('password') == password and locker.restore_file(file_name, user_id, password):
            return jsonify({"status": "success", "message": f"{file_name} restored"})
        return jsonify({"status": "error", "message": "Failed to restore file"}), 400
    except Exception as e:
        logging.error(f"Restore file error: {e}")
        return jsonify({"status": "error", "message": f"Server error: {str(e)}"}), 500

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)