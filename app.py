from flask import Flask, redirect, request, jsonify, url_for, render_template, session
from extensions import db
from models import DeviceData
from models import User
import csv
from flask import Response
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from io import BytesIO
from flask import send_file
from reportlab.lib.styles import getSampleStyleSheet
from dotenv import load_dotenv
import os

load_dotenv()



app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")


DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")

app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)


with app.app_context():
    try:
        db.create_all()
        print("Database connection successful and tables verified!")
    except Exception as e:
        print(f"Error creating tables: {e}")



@app.route('/')
def home():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))



@app.route('/login', methods=['GET','POST'])
def login():
    error = None

    if request.method=='POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username, password=password).first()

        if user:
            session['user']=user.username
            return redirect(url_for('dashboard'))
        else:
            error = "Invalid credentials"

    return render_template("login.html",error=error)




@app.route('/api/data', methods=['POST'])
def receive_data():
    data = request.json

    new_data = DeviceData(
        cpu = data['cpu'],
        memory = data['memory'],
        uptime=data['uptime'],
        battery=data['battery'],
        status=data['status']
    )

    db.session.add(new_data)
    db.session.commit()

    return jsonify({"message": "Data stored successfully"})



@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    data = DeviceData.query.order_by(DeviceData.timestamp.desc()).limit(20).all()

    chart_data = [
        {
            "cpu": d.cpu,
            "memory": d.memory,
            "timestamp": d.timestamp.strftime("%H:%M:%S")
        }
        for d in data
    ]

    return render_template('dashboard.html',data=data, chart_data=chart_data)



from datetime import datetime, timedelta, timezone

@app.route('/api/latest')
def get_latest_data():
    filter_type = request.args.get('filter', 'all')

    query = DeviceData.query

    now = datetime.now(timezone.utc)

    if filter_type == '1h':
        query = query.filter(DeviceData.timestamp >= now - timedelta(hours=1))

    elif filter_type == '24h':
        query = query.filter(DeviceData.timestamp >= now - timedelta(hours=24))

    data = query.order_by(DeviceData.timestamp.desc()).limit(50).all()

    result = [
        {
            "id": d.id,
            "cpu": d.cpu,
            "memory": d.memory,
            "uptime": d.uptime,
            "battery": d.battery,
            "status": d.status,
            "timestamp": d.timestamp.strftime("%H:%M:%S")
        }
        for d in data
    ]

    return jsonify(result)


# CSV Download


@app.route('/download/csv')
def download_csv():
    data = DeviceData.query.order_by(DeviceData.timestamp.desc()).all()

    def generate():
        yield 'ID,CPU,Memory,Uptime,Battery,Status,Time\n'

        for d in data:
            yield f"{d.id},{d.cpu},{d.memory},{d.uptime},{d.battery},{d.status},{d.timestamp}\n"

    return Response(generate(), mimetype='text/csv',
                    headers={"Content-Disposition": "attachment;filename=report.csv"})




# PDF Download

@app.route('/download/pdf')
def download_pdf():
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)

    styles = getSampleStyleSheet()

    elements = []

    elements.append(Paragraph("Device Monitoring Report", styles['Title']))
    elements.append(Spacer(1, 12))

    # Table Header
    data = [["ID", "CPU", "Memory", "Uptime", "Battery", "Status", "Time"]]

    rows = DeviceData.query.order_by(DeviceData.timestamp.desc()).all()

    for d in rows:
        data.append([
            d.id,
            f"{d.cpu}%",
            f"{d.memory}%",
            d.uptime,
            f"{d.battery}%",
            d.status,
            str(d.timestamp)
        ])

    table = Table(data)

    style = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.darkblue),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),

        ('ALIGN', (0,0), (-1,-1), 'CENTER'),

        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 10),

        ('BACKGROUND', (0,1), (-1,-1), colors.whitesmoke),

        ('GRID', (0,0), (-1,-1), 1, colors.black)
    ])

    table.setStyle(style)

    elements.append(table)

    doc.build(elements)
    buffer.seek(0)

    return send_file(buffer, as_attachment=True,
                     download_name="device_report.pdf",
                     mimetype='application/pdf')



@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))



if __name__ =='__main__':
  app.run(debug=True)