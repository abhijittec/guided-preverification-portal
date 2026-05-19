import os
from flask import Flask
# ... your other imports (SQLAlchemy, etc.) ...

app = Flask(__name__)

# Clean production-ready SQLite URI
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///admission.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Ensure tables and a default admin user exist
with app.app_context():
    db.create_all()
    # Replace 'Admin' with your actual Admin model name if different
    if not Admin.query.filter_by(username='admin').first():
        admin = Admin(username='admin', password='admin123') 
        db.session.add(admin)
        db.session.commit()

if __name__ == '__main__':
    # Bind to 0.0.0.0 so Docker and Render can route external traffic to your app
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False) # Turn off debug mode in production