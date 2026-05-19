import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# 1. PATH & CONFIG SETUP
PERSISTENT_DIR = "/app/instance" if os.path.exists("/app/instance") else os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(PERSISTENT_DIR, "admission.db")
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

UPLOAD_FOLDER = os.path.join(PERSISTENT_DIR, "uploads")
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 2. DEFINE DB OBJECT FIRST (Crucial Step!)
db = SQLAlchemy(app)

# 3. DEFINE YOUR MODELS NEXT
# (Ensure your Admin model or other models are defined here or imported here)
class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

# 4. RUN APP CONTEXT AFTER DB IS DEFINED
with app.app_context():
    db.create_all()  # Now 'db' exists, so it won't crash!
    
    if not Admin.query.filter_by(username='admin').first():
        admin = Admin(username='admin', password='admin123')
        db.session.add(admin)
        db.session.commit()

# ... rest of your routes (@app.route) ...

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)