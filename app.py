from flask import Flask, render_template, redirect, url_for, request, flash, session
from models import db, Admin, Student, Company, Drive, Application
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY']='placement_secret'
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///database.db'
app.config['UPLOAD_FOLDER']='static/resumes'

db.init_app(app)

login_manager=LoginManager()
login_manager.init_app(app)
login_manager.login_view="login"

# USER LOADER

@login_manager.user_loader
def load_user(user_id):
    role=session.get("role")
    if role=="admin":
        return Admin.query.get(int(user_id))
    elif role=="student":
        return Student.query.get(int(user_id))
    elif role=="company":
        return Company.query.get(int(user_id))
    return None

#LOGIN

@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method=="POST":
        role=request.form["role"]
        email=request.form["email"]
        password=request.form["password"]

        if role=="admin":
            user=Admin.query.filter_by(email=email).first()
        elif role=="student":
            user=Student.query.filter_by(email=email, active=True).first()
        else:
            user=Company.query.filter_by(email=email, active=True).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            session["role"]=role
            return redirect(url_for(f"{role}_dashboard"))

        flash("Invalid Credentials")

    return render_template("login.html")


# LOGOUT 

@app.route("/logout")
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect(url_for("login"))


# for student registration

@app.route("/register_student", methods=["GET", "POST"])
def register_student():
    if request.method=="POST":
        student = Student(
            name=request.form["name"],
            email=request.form["email"],
            password=generate_password_hash(request.form["password"]),
            department=request.form["department"],
            contact=request.form["contact"],
            cgpa=float(request.form["cgpa"])
        )
        db.session.add(student)
        db.session.commit()
        flash("Registered Successfully")
        return redirect(url_for("login"))

    return render_template("register_student.html")


# for company registration

@app.route("/register_company", methods=["GET", "POST"])
def register_company():
    if request.method=="POST":
        company = Company(
            name=request.form["name"],
            email=request.form["email"],
            password=generate_password_hash(request.form["password"]),
            website = request.form["website"],
            hr_contact=request.form["hr_contact"],
            location=request.form["location"]
        )
        db.session.add(company)
        db.session.commit()
        flash("Registration sent for approval")
        return redirect(url_for("login"))

    return render_template("register_company.html")

#-----admin role-----
@app.route("/admin/dashboard")
@login_required
def admin_dashboard():
    if session.get("role")!="admin":
        return redirect(url_for("login"))

    stats = {
        "students":Student.query.count(),
        "companies":Company.query.count(),
        "drives":Drive.query.count(),
        "applications":Application.query.count()
    }

    return render_template("admin/dashboard.html", stats=stats)


# APPROVE COMPANY
@app.route("/approve_company/<int:id>")
@login_required
def approve_company(id):
    company=Company.query.get(id)
    company.approved=True
    db.session.commit()
    return redirect(url_for("manage_companies"))


# BLACKLIST SPECIFIC STUDENTS
@app.route("/deactivate_student/<int:id>")
@login_required
def deactivate_student(id):
    student=Student.query.get(id)
    student.active=False
    db.session.commit()
    return redirect(url_for("manage_students"))

#BLACKLIST SPECIFIC COMPANIES
@app.route("/deactivate_company/<int:id>")
@login_required
def deactivate_company(id):
    company=Company.query.get(id)
    company.active=False
    db.session.commit()
    return redirect(url_for("manage_companies"))


# SEARCH FOR SPECIFIC STUDENT
@app.route("/admin/manage_students")
@login_required
def manage_students():
    
    students=Student.query.all()

    return render_template("admin/manage_students.html", students=students)


# SEARCH FOR SPECIFIC COMPANY
@app.route("/admin/manage_companies")
@login_required
def manage_companies():
    search=request.args.get("search")
    if search:
        companies=Company.query.filter(Company.name.contains(search)).all()
    else:
        companies=Company.query.all()

    return render_template("admin/manage_companies.html", companies=companies)


# APPROVE DRIVE
@app.route("/approve_drive/<int:id>")
@login_required
def approve_drive(id):
    drive=Drive.query.get(id)
    drive.approved = True
    db.session.commit()
    return redirect(url_for("manage_drives"))


@app.route("/admin/manage_drives")
@login_required
def manage_drives():
    drives=Drive.query.all()
    return render_template("admin/manage_drives.html", drives=drives)


@app.route("/admin/applications")
@login_required
def view_applications():

    search=request.args.get("search")

    query=Application.query.join(Student)

    if search:
        query=query.filter(
            (Student.name.contains(search)) |
            (Student.email.contains(search)) |
            (Student.contact.contains(search))
        )

    applications=query.all()

    return render_template("admin/applications.html",
                           applications=applications)


#company role

@app.route("/company/dashboard")
@login_required
def company_dashboard():
    if session.get("role")!="company":
        return redirect(url_for("login"))

    drives = Drive.query.filter_by(company_id=current_user.id).all()
    return render_template("company/dashboard.html", drives=drives, company=current_user)

# COMPANY CREATING A DRIVE
@app.route("/company/create_drive", methods=["GET", "POST"])
@login_required
def create_drive():
    if not current_user.approved:
        flash("Company not approved yet.")
        return redirect(url_for("company_dashboard"))

    if request.method == "POST":
        drive = Drive(
            role=request.form["role"],
            eligibility = request.form["eligibility"],
            ctc=request.form["ctc"],
            deadline=datetime.strptime(request.form["deadline"], "%Y-%m-%d"),
            description=request.form["description"],
            company_id=current_user.id
        )
        db.session.add(drive)
        db.session.commit()
        flash("Drive Created. Waiting for admin approval.")
        return redirect(url_for("company_dashboard"))

    return render_template("company/create_drive.html")

#FOR EDITING A DRIVE ALREADY CREATED
@app.route("/company/edit_drive/<int:id>", methods=["GET", "POST"])
@login_required
def edit_drive(id):

    drive = Drive.query.get_or_404(id)

    if drive.company_id!=current_user.id:
        return redirect(url_for("company_dashboard"))

    if request.method=="POST":
        drive.role=request.form["role"]
        drive.ctc=request.form["ctc"]
        drive.deadline=datetime.strptime(request.form["deadline"], "%Y-%m-%d")
        drive.description=request.form["description"]

        db.session.commit()
        flash("Drive Updated Successfully")
        return redirect(url_for("company_dashboard"))
        print("EDIT ROUTE WORKING")
    return render_template("company/edit_drive.html", drive=drive)

# CLOSE A DRIVE
@app.route("/company/close_drive/<int:id>")
@login_required
def close_drive(id):

    drive=Drive.query.get_or_404(id)

    if drive.company_id!=current_user.id:
        return redirect(url_for("company_dashboard"))

    drive.closed=True
    db.session.commit()

    flash("Drive Closed Successfully")
    return redirect(url_for("company_dashboard"))

#VIEW APPLICANTS FOR A PARTICULAR DRIVE
@app.route("/company/applicants/<int:id>")
@login_required
def view_applicants(id):
    applications=Application.query.filter_by(drive_id=id).all()
    return render_template("company/applicants.html", applications=applications)

#UPDATE THE STATUS OF STUDENTS
@app.route("/update_status/<int:id>/<status>")
@login_required
def update_status(id, status):
    app_obj=Application.query.get(id)
    app_obj.status=status
    db.session.commit()
    return redirect(request.referrer)

# student role

@app.route("/student/dashboard")
@login_required
def student_dashboard():
    drives=Drive.query.filter_by(approved=True, closed=False).all()
    applied=Application.query.filter_by(student_id=current_user.id).all()
    return render_template("student/dashboard.html", drives=drives, applied=applied)

# applying to a drive
@app.route("/apply/<int:id>")
@login_required
def apply_drive(id):
    existing = Application.query.filter_by(
        student_id=current_user.id,
        drive_id=id
    ).first()

    if existing:
        flash("Already applied!")
        return redirect(url_for("student_dashboard"))

    application=Application(
        student_id=current_user.id,
        drive_id=id
    )
    db.session.add(application)
    db.session.commit()
    flash("Applied Successfully")
    return redirect(url_for("student_dashboard"))

# view history of applications
@app.route("/student/history")
@login_required
def history():
    applications=Application.query.filter_by(student_id=current_user.id).all()
    return render_template("student/history.html", applications=applications)

# to edit the student's profile
@app.route("/student/edit_profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    if request.method=="POST":
        current_user.name=request.form["name"]
        current_user.department=request.form["department"]
        current_user.contact=request.form["contact"]
        current_user.cgpa=float(request.form["cgpa"])

        file=request.files.get("resume")
        if file:
            filename=file.filename
            path=os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(path)
            current_user.resume=filename

        db.session.commit()
        flash("Profile Updated")
        return redirect(url_for("student_dashboard"))

    return render_template("student/edit_profile.html", student=current_user)


with app.app_context():
    db.create_all()
    if not Admin.query.first():
        admin = Admin(
            email="admin@placement.com",
            password=generate_password_hash("admin123")
        )
        db.session.add(admin)
        db.session.commit()
# =====================================================

if __name__ == "__main__":
    app.run(debug=True)