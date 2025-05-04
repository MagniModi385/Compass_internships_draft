from flask import Flask, request, render_template, redirect, url_for, flash, session
import mysql.connector as my
import smtplib
from email.message import EmailMessage


app = Flask(__name__)
app.secret_key = "your_secret_key"  # Required for session & flash messages

# Database connection
mydb = my.connect(
    host="localhost",
    user="root",
    password="",
    database="compass"
)

mycursor = mydb.cursor(dictionary=True)  # Ensure it's in dictionary mode
@app.route('/')
def home():
    return render_template('entry.html')

@app.route('/student_login')
def student_login():
    return render_template('student_login.html')

@app.route('/recruiter_login')
def recruiter_login():
    return render_template('recruiter_login.html')

@app.route('/check_student', methods=['POST'])
def check_student():
    email = request.form['email']
    password = request.form['password']

    # Query the database to check student credentials
    mycursor.execute("SELECT * FROM students WHERE email = %s", (email,))
    student_data = mycursor.fetchone()  # Fetch one matching record
    mycursor.execute("SELECT * FROM internships ORDER BY created_at DESC")
    internships = mycursor.fetchall()  # Fetch all internships added recently

    if student_data:
        stored_password = student_data["password"]  # Get stored password (plain text)

        # Direct string comparison (Since passwords are NOT hashed)
        if stored_password == password:
            session['student_id'] = student_data["student_id"]  # Store student ID in session
            # session['student_data']=student_data
            # return redirect(url_for('student_dashboard',student_data))  # Redirect to student dashboard
            # return render_template("student_dashboard.html",student_name=student_data["student_name"],about=student_data["about"])
            return render_template("student_dashboard.html",student_data=student_data,recent_internships=internships)
        else:
            flash("Invalid password!", "danger")
    else:
        flash("No account found with this email!", "danger")
    
    return redirect(url_for('student_login'))  # Redirect back to login page


@app.route('/check_recruiter', methods=['POST'])
def check_recruiter():
    email = request.form['email']
    password = request.form['password']

    # Query the database to check recruiter credentials
    mycursor.execute("SELECT * FROM recruiters WHERE recruiter_email = %s", (email,))
    recruiter = mycursor.fetchone()  # Fetch one matching record
    
    
    if recruiter:
        stored_password = recruiter['password']  # Get stored password (plain text)

        # Direct string comparison (Since passwords are NOT hashed)
        if stored_password == password:
            session['recruiter_id'] = recruiter['recruiter_id']  # Store recruiter ID in session
            session['company_name'] = recruiter['company_name']
            session['recruiter_name'] = recruiter['recruiter_name']
            session['recruiter_email'] = recruiter['recruiter_email']
            session['recruiter_position'] = recruiter['position']
            return redirect(url_for('recruiter_dashboard'))  # Redirect to recruiter dashboard
        else:
            flash("Invalid password!", "danger")
    else:
        flash("No account found with this email!", "danger")
    
    return redirect(url_for('recruiter_login'))  # Redirect back to login page

# route for recruiter_dashboard
@app.route('/recruiter_dashboard')
def recruiter_dashboard():
    id=session["recruiter_id"]
    mycursor.execute('SELECT * FROM recruiters where recruiter_id=%s',(id,))
    recruiter_data = mycursor.fetchone()  # Fetch one matching record
    
    mycursor.execute("select * from internships where recruiter_id=%s",(id,))
    recruiter_internships = mycursor.fetchall()  # Fetch all internships added recently
    return render_template('recruiter_dashboard.html',recruiter_data=recruiter_data, internships=recruiter_internships)

@app.route('/student_dashboard')
def student_dashboard():
    return render_template('student_dashboard.html')

@app.route('/student_signup')
def student_signup():
    return render_template('student_signup.html')

@app.route('/recruiter_signup')
def recruiter_signup():
    return render_template('recruiter_signup.html')

# route fro "create_student_acc"
@app.route('/create_student_acc', methods=['POST'])
def create_student_acc():
    try:
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        institute = request.form['institute']
        skills = request.form['skills']
        phone = request.form['phone']
        experience = request.form['experience']
        location = request.form['location']
        interests = request.form.getlist('interest')
        resume = request.files['resume'] if 'resume' in request.files else None

        # Debugging - Print received data
        print("Received Data:", request.form)
        print("Received File:", resume.filename if resume else "No file uploaded")

        # Convert interests list to comma-separated string
        interests_str = ', '.join(interests)

        # # Ensure "resumes" folder exists
        # resume_folder = "resumes"
        # if not os.path.exists(resume_folder):
        #     os.makedirs(resume_folder)

        # # Store resume if uploaded
        # resume_filename = None
        # if resume:
        #     resume_filename = os.path.join(resume_folder, f"{email}_resume.pdf")
        #     resume.save(resume_filename)

        # Hash password before storing
        # password_hashed = bcrypt.generate_password_hash(password).decode('utf-8')

        # Insert into database
        sql = """
            INSERT INTO students (student_name, email, password, institution, skills, phone, 
                                  experience, location, interest) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (name, email, password, institute, skills, phone, experience, location, interests_str)

        mycursor.execute(sql, values)
        mydb.commit()

        flash("Account created successfully! You can now log in.", "success")

        #smtp logic
        sender="dhruvishpatel580@gmail.com"
        receiver=email
        sender_password="ycab iczn dwkm cxdb"

        message = EmailMessage()
        message["From"]= sender
        message["To"]= receiver
        message["Subject"]=" Welcome to Compass! Your Account Has Been Successfully Created"
        
        content= f"""\
        Dear {name},

        We are thrilled to have you on board! Your account has been successfully created on Compass. Below are your account details:

        🔹 Name: {name}
        🔹 Email: {email}
        🔹 Account Type: Student

        You can now log in using your registered email and start exploring our platform.

        For security reasons, please do not share your credentials with anyone. If you have any questions or need assistance, feel free to contact our support team.

        Welcome aboard! 🚀

        Best regards,  
        Compass  
        📧 compass.internships@gmail.com
        """
        message.set_content(content)

        with smtplib.SMTP_SSL("smtp.gmail.com",465) as server:
            server.login(sender,sender_password)
            server.send_message(message)

        return redirect(url_for('student_login'))

    except Exception as e:
        mydb.rollback()
        print(f"Error: {e}")  # Debugging
        flash(f"Error creating account: {str(e)}", "danger")
        return redirect(url_for('student_signup'))

@app.route('/create_recruiter_acc', methods=['POST'])
def create_recruiter_acc():
    try:
        email = request.form['email']
        password = request.form['password']
        name = request.form['name']
        phone = request.form['phone']
        company_name = request.form['company']
        job_posiion = request.form['position']
        location = request.form['location']
        about_company = request.form['about_compnay']

        # Insert into database
        sql = """
            INSERT INTO recruiters (company_name, about_company, location, recruiter_name, recruiter_email, password) 
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        values = (company_name,about_company,location,name,email,password)

        mycursor.execute(sql, values)
        mydb.commit()

        flash("Account created successfully! You can now log in.", "success")

        #smtp logic
        sender="dhruvishpatel580@gmail.com"
        receiver=email
        sender_password="ycab iczn dwkm cxdb"

        message = EmailMessage()
        message["From"]= sender
        message["To"]= receiver
        message["Subject"]=" Welcome to Compass! Your Account Has Been Successfully Created"
        
        content= f"""\
        Dear {name},

        We are thrilled to have you on board! Your account has been successfully created on Compass. Below are your account details:

        🔹 Name: {name}
        🔹 Email: {email}
        🔹 Account Type: Recruiter

        You can now log in using your registered email and start exploring our platform.

        For security reasons, please do not share your credentials with anyone. If you have any questions or need assistance, feel free to contact our support team.

        Welcome aboard! 🚀

        Best regards,  
        Compass  
        📧 compass.internships@gmail.com
        """
        message.set_content(content)

        with smtplib.SMTP_SSL("smtp.gmail.com",465) as server:
            server.login(sender,sender_password)
            server.send_message(message)

        return redirect(url_for('recruiter_login'))

    except Exception as e:
        mydb.rollback()
        print(f"Error: {e}")  # Debugging
        flash(f"Error creating account: {str(e)}", "danger")
        return redirect(url_for('recruiter_signup'))

@app.route('/create_internship', methods=['POST'])
def create_internship():
    try:
        # Example: Fetch recruiter ID in another route
        if 'recruiter_id' in session:
            recruiter_id = session['recruiter_id']
            company_name = session['company_name']
            recruiter_name = session['recruiter_name']
            print(f"Recruiter ID: {recruiter_id} ,company name: {company_name}, recruiter_name: {recruiter_name}")
        else:
            print("No recruiter logged in")

        position = request.form['position']
        location = request.form['location']
        duration = request.form['duration']
        stipend = request.form['stipend']

        # Insert into database
        sql = """
            INSERT INTO internships (recruiter_id,company_name,recruiter_name,position,stipend,duration,location) 
            VALUES ( %s, %s, %s, %s, %s, %s, %s)
        """
        values = (recruiter_id,company_name,recruiter_name,position,stipend,duration,location)

        mycursor.execute(sql, values)
        mydb.commit()

        flash("Internship created successfully!")
        return redirect(url_for('recruiter_dashboard'))

    except Exception as e:
        mydb.rollback()
        print(f"Error: {e}")  # Debugging
        flash(f"Error creating account: {str(e)}", "danger")
        return redirect(url_for('recruiter_login'))
    
if __name__ == '__main__':
    app.run(debug=True)
