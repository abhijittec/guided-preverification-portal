from flask import Flask, render_template, request, redirect, session, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from flask import send_file
from flask import session
from flask import redirect
import qrcode

from reportlab.pdfgen import canvas
import os

app = Flask(__name__)

# ==================================================
# CONFIGURATION
# ==================================================

app.config['SECRET_KEY'] = 'secret123'

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root@host.docker.internal/admission_portal'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['UPLOAD_FOLDER'] = 'static/uploads'

db = SQLAlchemy(app)

# ==================================================
# STUDENT MODEL
# ==================================================

class Student(db.Model):

    __tablename__ = 'students'

    id = db.Column(db.Integer, primary_key=True)

    application_no = db.Column(db.String(20))

    student_name = db.Column(db.String(100))

    program = db.Column(db.String(100))

    category = db.Column(db.String(50))

    admission_status = db.Column(db.String(50))

    section_name = db.Column(db.String(20))

    verification_status = db.Column(db.String(30))


# ==================================================
# DOCUMENT MODEL
# ==================================================

class StudentDocument(db.Model):

    __tablename__ = 'student_documents'

    id = db.Column(db.Integer, primary_key=True)

    application_no = db.Column(db.String(20))

    document_name = db.Column(db.String(100))

    file_name = db.Column(db.String(200))

class SelfVerification(db.Model):

    __tablename__ = 'self_verification'

    id = db.Column(db.Integer, primary_key=True)

    application_no = db.Column(db.String(20))

    document_name = db.Column(db.String(100))

    document_clear = db.Column(db.String(10))

    corners_visible = db.Column(db.String(10))

    signature_visible = db.Column(db.String(10))

    original_document = db.Column(db.String(10))

    name_matching = db.Column(db.String(10))
# ==================================================
# HOME PAGE
# ==================================================
class Appointment(db.Model):

    __tablename__ = 'appointments'

    id = db.Column(db.Integer, primary_key=True)

    application_no = db.Column(db.String(20))

    reporting_date = db.Column(db.String(20))

    reporting_time = db.Column(db.String(20))

    booking_status = db.Column(db.String(20))

@app.route('/')
def home():

    return render_template('login.html')
@app.route('/admin_login')
def admin_login():

    return render_template('admin_login.html')
@app.route('/admin_auth', methods=['POST'])
def admin_auth():

    username = request.form['username']

    password = request.form['password']

    admin = Admin.query.filter_by(
        username=username,
        password=password
    ).first()

    if admin:

        session['admin'] = username

        return redirect('/admin')

    else:

        return """

        <h2>Invalid Credentials</h2>

        <a href='/admin_login'>
        Try Again
        </a>

        """
class Admin(db.Model):

    __tablename__ = 'admins'

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(50))

    password = db.Column(db.String(50))
# ==================================================
# VALIDATE STUDENT
# ==================================================

@app.route('/validate', methods=['POST'])
def validate():

    try:

        app_no = request.form['application_no']

        student = Student.query.filter_by(
            application_no=app_no
        ).first()

        if student:

            return f"""

            <html>

            <head>

            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css"
                  rel="stylesheet">

            </head>

            <body class="bg-light">

            <div class="container mt-5">

            <div class="card shadow">

            <div class="card-header bg-success text-white">

            <h3>Validation Successful</h3>

            </div>

            <div class="card-body">

            <h4>{student.student_name}</h4>

            <hr>

            <p>
            <b>Application Number:</b>
            {student.application_no}
            </p>

            <p>
            <b>Program:</b>
            {student.program}
            </p>

            <p>
            <b>Status:</b>
            {student.admission_status}
            </p>

            <p>
            <b>Section:</b>
            {student.section_name}
            </p>

            <br>

            <a href="/upload/{student.application_no}"
               class="btn btn-primary">

               Upload Documents

            </a>

            </div>

            </div>

            </div>

            </body>

            </html>

            """

        else:

            return """

            <h2>Invalid Application Number</h2>

            <a href='/'>Try Again</a>

            """

    except Exception as e:

        return f"""

        <h2>Error</h2>

        <p>{str(e)}</p>

        """


# ==================================================
# UPLOAD PAGE
# ==================================================

@app.route('/upload/<app_no>')
def upload_page(app_no):

    return render_template(
        'upload.html',
        app_no=app_no
    )


# ==================================================
# UPLOAD DOCUMENT
# ==================================================

@app.route('/upload_document', methods=['POST'])
def upload_document():

    try:

        app_no = request.form['application_no']

        document_name = request.form['document_name']

        file = request.files['document']

        if file.filename == '':

            return "No file selected"

        filename = secure_filename(file.filename)

        save_path = os.path.join(
            app.config['UPLOAD_FOLDER'],
            filename
        )

        file.save(save_path)

        new_doc = StudentDocument(

            application_no=app_no,

            document_name=document_name,

            file_name=filename
        )

        db.session.add(new_doc)

        db.session.commit()

        return f"""

        <html>

        <head>

        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css"
              rel="stylesheet">

        </head>

        <body class="bg-light">

        <div class="container mt-5">

        <div class="card shadow">

        <div class="card-header bg-success text-white">

        <h3>Document Uploaded Successfully</h3>

        </div>

        <div class="card-body">

        <p><b>Uploaded File:</b> {filename}</p>

        <br>

        <a href='/checklist/{app_no}'
           class="btn btn-primary">

        View Checklist

        </a>

        </div>

        </div>

        </div>

        </body>

        </html>

        """

    except Exception as e:

        return f"""

        <h2>Error</h2>

        <p>{str(e)}</p>

        """


# ==================================================
# CHECKLIST PAGE
# ==================================================

@app.route('/checklist/<app_no>')
def checklist(app_no):

    try:

        student = Student.query.filter_by(
            application_no=app_no
        ).first()

        uploaded_docs = StudentDocument.query.filter_by(
            application_no=app_no
        ).all()

        uploaded_names = []

        for d in uploaded_docs:

            uploaded_names.append(d.document_name)

        required_docs = [

            '10th Marks Card',

            '12th Marks Card',

            'Aadhaar Card',

            'Transfer Certificate',

            'Conduct Certificate'
        ]

        completed = 0

        for doc in required_docs:

            if doc in uploaded_names:

                completed += 1

        total = len(required_docs)

        if completed == total:

            status = "READY"

            color = "success"

        elif completed >= 2:

            status = "PENDING"

            color = "warning"

        else:

            status = "INCOMPLETE"

            color = "danger"

        return render_template(

            'checklist.html',

            student=student,

            required_docs=required_docs,

            uploaded_names=uploaded_names,

            completed=completed,

            total=total,

            status=status,

            color=color
        )

    except Exception as e:

        return f"""

        <h2>Error</h2>

        <p>{str(e)}</p>

        """

@app.route('/self_verify/<app_no>')
def self_verify(app_no):

    return render_template(
        'self_verify.html',
        app_no=app_no
    )

@app.route('/submit_verification', methods=['POST'])
def submit_verification():

    try:

        app_no = request.form['application_no']

        document_name = request.form['document_name']

        document_clear = request.form['document_clear']

        corners_visible = request.form['corners_visible']

        signature_visible = request.form['signature_visible']

        original_document = request.form['original_document']

        name_matching = request.form['name_matching']

        verification = SelfVerification(

            application_no=app_no,

            document_name=document_name,

            document_clear=document_clear,

            corners_visible=corners_visible,

            signature_visible=signature_visible,

            original_document=original_document,

            name_matching=name_matching
        )

        db.session.add(verification)

        db.session.commit()

        # =========================
        # EXCEPTION HANDLING
        # =========================

        warning_messages = []

        if document_clear == "No":
            warning_messages.append(
                "Document is unclear."
            )

        if corners_visible == "No":
            warning_messages.append(
                "All corners are not visible."
            )

        if signature_visible == "No":
            warning_messages.append(
                "Signature or stamp missing."
            )

        if original_document == "No":
            warning_messages.append(
                "Original document required."
            )

        if name_matching == "No":
            warning_messages.append(
                "Name mismatch detected."
            )

        if len(warning_messages) == 0:

            status = "READY"
            color = "success"

        else:

            status = "PENDING CLARIFICATION"
            color = "warning"

        warnings_html = ""

        for w in warning_messages:

            warnings_html += f"<li>{w}</li>"

        return f"""

        <html>

        <head>

        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css"
              rel="stylesheet">

        </head>

        <body class="bg-light">

        <div class="container mt-5">

        <div class="card shadow">

        <div class="card-header bg-{color} text-white">

        <h3>Verification Result</h3>

        </div>

        <div class="card-body">

        <h4>Status: {status}</h4>

        <hr>

        <ul>

        {warnings_html}

        </ul>

        <br>

        <a href="/book_slot/{app_no}"
           class="btn btn-primary">

           Proceed to Appointment Booking

        </a>

        </div>

        </div>

        </div>

        </body>

        </html>

        """

    except Exception as e:

        return f"""

        <h2>Error</h2>

        <p>{str(e)}</p>

 
        """

@app.route('/book_slot/<app_no>')
def book_slot(app_no):

    return render_template(
        'booking.html',
        app_no=app_no
    )

@app.route('/confirm_booking', methods=['POST'])
def confirm_booking():

    try:

        app_no = request.form['application_no']

        reporting_date = request.form['reporting_date']

        reporting_time = request.form['reporting_time']

        # =====================================
        # SLOT LIMIT CHECK
        # MAX 5 STUDENTS PER SLOT
        # =====================================

        existing = Appointment.query.filter_by(
            reporting_date=reporting_date,
            reporting_time=reporting_time
        ).count()

        if existing >= 5:

            return f"""

            <h2>Slot Full</h2>

            <p>
            Please select another slot.
            </p>

            <a href='/book_slot/{app_no}'>
            Go Back
            </a>

            """

        booking = Appointment(

            application_no=app_no,

            reporting_date=reporting_date,

            reporting_time=reporting_time,

            booking_status='CONFIRMED'
        )

        db.session.add(booking)

        db.session.commit()

        return f"""

        <html>

        <head>

        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css"
              rel="stylesheet">

        </head>

        <body class="bg-light">

        <div class="container mt-5">

        <div class="card shadow">

        <div class="card-header bg-success text-white">

        <h3>Appointment Confirmed</h3>

        </div>

        <div class="card-body">

        <h4>Reporting Summary</h4>

        <hr>

        <p>
        <b>Application Number:</b>
        {app_no}
        </p>

        <p>
        <b>Reporting Date:</b>
        {reporting_date}
        </p>

        <p>
        <b>Reporting Time:</b>
        {reporting_time}
        </p>

        <p>
        <b>Status:</b>
        CONFIRMED
        </p>

        <br>

        <a href="/download_summary/{app_no}"
            class="btn btn-primary">

        Download PDF Summary

        </a>

        Download / Print Summary

        </button>

        </div>

        </div>

        </div>

        </body>

        </html>

        """

    except Exception as e:

        return f"""

        <h2>Error</h2>

        <p>{str(e)}</p>

        """

@app.route('/admin')
def admin_dashboard():

    try:

        if 'admin' not in session:

            return redirect('/admin_login')

        search = request.args.get('search')

        status = request.args.get('status')

        query = Student.query

        # ==================================
        # SEARCH BY APPLICATION NUMBER
        # ==================================

        if search:

            query = query.filter(
                Student.application_no.contains(search)
            )

        # ==================================
        # FILTER BY STATUS
        # ==================================

        if status:

            query = query.filter_by(
                verification_status=status
            )

        students = query.all()

        appointments = Appointment.query.all()

        documents = StudentDocument.query.all()

        return render_template(

            'admin_dashboard.html',

            students=students,

            appointments=appointments,

            documents=documents
        )

    except Exception as e:

        return f"""

        <h2>Error</h2>

        <p>{str(e)}</p>

        """

@app.route('/approve/<app_no>')
def approve_student(app_no):

    student = Student.query.filter_by(
        application_no=app_no
    ).first()

    student.verification_status = 'APPROVED'

    db.session.commit()

    return f"""

    <h2>Student Approved</h2>

    <a href='/admin'>

    Back to Dashboard

    </a>

    """

@app.route('/reject/<app_no>')
def reject_student(app_no):

    student = Student.query.filter_by(
        application_no=app_no
    ).first()

    student.verification_status = 'REJECTED'

    db.session.commit()

    return f"""

    <h2>Student Rejected</h2>

    <a href='/admin'>

    Back to Dashboard

    </a>

    """

@app.route('/download_summary/<app_no>')
def download_summary(app_no):

    try:

        student = Student.query.filter_by(
            application_no=app_no
        ).first()

        appointment = Appointment.query.filter_by(
            application_no=app_no
        ).first()

        # ===================================
        # QR CODE GENERATION
        # ===================================

        qr_data = f"""

        Application Number: {student.application_no}

        Name: {student.student_name}

        Reporting Date: {appointment.reporting_date}

        Reporting Time: {appointment.reporting_time}

        """

        qr = qrcode.make(qr_data)

        qr_path = f"static/qrcodes/{app_no}.png"

        qr.save(qr_path)

        # ===================================
        # PDF GENERATION
        # ===================================

        pdf_path = f"{app_no}_summary.pdf"

        c = canvas.Canvas(pdf_path)

        c.setFont("Helvetica-Bold", 18)

        c.drawString(
            150,
            800,
            "Reporting Summary"
        )

        c.setFont("Helvetica", 12)

        c.drawString(
            50,
            740,
            f"Application Number: {student.application_no}"
        )

        c.drawString(
            50,
            710,
            f"Student Name: {student.student_name}"
        )

        c.drawString(
            50,
            680,
            f"Program: {student.program}"
        )

        c.drawString(
            50,
            650,
            f"Reporting Date: {appointment.reporting_date}"
        )

        c.drawString(
            50,
            620,
            f"Reporting Time: {appointment.reporting_time}"
        )

        c.drawString(
            50,
            590,
            f"Verification Status: {student.verification_status}"
        )

        # ===================================
        # ADD QR IMAGE
        # ===================================

        c.drawImage(
            qr_path,
            400,
            620,
            width=120,
            height=120
        )

        c.save()

        return send_file(
            pdf_path,
            as_attachment=True
        )

    except Exception as e:

        return f"""

        <h2>Error</h2>

        <p>{str(e)}</p>

        """
# ==================================================
# RUN APPLICATION
# ==================================================

if __name__ == '__main__':

        app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )