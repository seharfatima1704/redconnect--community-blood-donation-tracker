import os
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message

# -------------------------------------------------
# App and Config
# -------------------------------------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'redconnect.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Mail (placeholder config; customize for real notifications)
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'localhost')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 25))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'false').lower() == 'true'
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'no-reply@redconnect.local')

mail = Mail(app)
db = SQLAlchemy(app)

# -------------------------------------------------
# Models
# -------------------------------------------------
class Donor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(30), nullable=False)
    blood_group = db.Column(db.String(5), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=True)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=True)
    available = db.Column(db.Boolean, default=True)
    last_donation_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def eligible(self) -> bool:
        if not self.available:
            return False
        if self.last_donation_date is None:
            return True
        return datetime.utcnow().date() - self.last_donation_date >= timedelta(days=90)


class BloodRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_name = db.Column(db.String(120), nullable=False)
    contact_person = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(30), nullable=False)
    blood_group_needed = db.Column(db.String(5), nullable=False)
    units_required = db.Column(db.Integer, nullable=False)
    hospital_name = db.Column(db.String(150), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# -------------------------------------------------
# Seed Data
# -------------------------------------------------

def seed_data():
    if Donor.query.first():
        return
    donors = [
        Donor(full_name='Aisha Khan', email='aisha@example.com', phone='9000000001', blood_group='A+', date_of_birth=datetime(1995,5,1).date(), city='Lahore', state='Punjab', available=True, last_donation_date=(datetime.utcnow() - timedelta(days=120)).date()),
        Donor(full_name='Rahul Mehta', email='rahul@example.com', phone='9000000002', blood_group='O-', date_of_birth=datetime(1992,3,14).date(), city='Mumbai', state='MH', available=True, last_donation_date=(datetime.utcnow() - timedelta(days=45)).date()),
        Donor(full_name='Sara Ali', email='sara@example.com', phone='9000000003', blood_group='B+', date_of_birth=datetime(1998,9,21).date(), city='Karachi', state='Sindh', available=False, last_donation_date=None),
        Donor(full_name='John Doe', email='john@example.com', phone='9000000004', blood_group='AB+', date_of_birth=datetime(1989,1,10).date(), city='Delhi', state='DL', available=True, last_donation_date=None),
    ]
    db.session.add_all(donors)
    requests = [
        BloodRequest(patient_name='Imran Khan', contact_person='Nadia', email='nadia@example.com', phone='9111111111', blood_group_needed='O-', units_required=2, hospital_name='City Hospital', city='Lahore'),
        BloodRequest(patient_name='Priya Sharma', contact_person='Vikram', email='vikram@example.com', phone='9222222222', blood_group_needed='A+', units_required=1, hospital_name='General Care', city='Mumbai'),
    ]
    db.session.add_all(requests)
    db.session.commit()

# -------------------------------------------------
# Helpers
# -------------------------------------------------
BLOOD_GROUPS = ['A+', 'A-', 'B+', 'B-', 'O+', 'O-', 'AB+', 'AB-']


def count_blood_group_availability():
    result = {}
    for bg in BLOOD_GROUPS:
        count = Donor.query.filter_by(blood_group=bg, available=True).all()
        eligible_count = sum(1 for d in count if d.eligible())
        result[bg] = {'total': len(count), 'eligible': eligible_count}
    return result


def send_notifications(donors, blood_request):
    # Placeholder: log to console; configure Flask-Mail/Twilio for real use
    try:
        for d in donors:
            app.logger.info(f"Notify {d.full_name} ({d.email}/{d.phone}) about request {blood_request.id}")
        # Example email if configured
        if app.config['MAIL_SERVER'] != 'localhost' and app.config.get('MAIL_USERNAME'):
            recipients = [d.email for d in donors if d.email]
            if recipients:
                msg = Message(subject='RedConnect: Blood Request Match', recipients=recipients,
                              body=f"A patient in {blood_request.city} needs {blood_request.blood_group_needed}. Please check RedConnect.")
                mail.send(msg)
    except Exception as e:
        app.logger.warning(f"Notification send failed: {e}")

# -------------------------------------------------
# Routes
# -------------------------------------------------
@app.context_processor
def inject_now():
    return {"datetime": datetime}

@app.route('/')
def home():
    total_donors = Donor.query.count()
    total_requests = BloodRequest.query.count()
    cities_served = db.session.query(Donor.city).distinct().count()
    lives_saved = total_requests  # simple proxy for demo
    return render_template('index.html', total_donors=total_donors, lives_saved=lives_saved, cities_served=cities_served)


@app.route('/donor/register', methods=['GET', 'POST'])
def donor_register():
    if request.method == 'POST':
        try:
            full_name = request.form.get('full_name')
            email = request.form.get('email')
            phone = request.form.get('phone')
            blood_group = request.form.get('blood_group')
            dob = request.form.get('date_of_birth')
            city = request.form.get('city')
            state = request.form.get('state')
            available = request.form.get('available') == 'on'
            last_donation_date = request.form.get('last_donation_date')

            donor = Donor(
                full_name=full_name,
                email=email,
                phone=phone,
                blood_group=blood_group,
                date_of_birth=datetime.strptime(dob, '%Y-%m-%d').date() if dob else None,
                city=city,
                state=state,
                available=available,
                last_donation_date=datetime.strptime(last_donation_date, '%Y-%m-%d').date() if last_donation_date else None,
            )
            db.session.add(donor)
            db.session.commit()
            flash('Thank you for registering as a donor!','success')
            return redirect(url_for('home'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {e}','danger')
    return render_template('donor_register.html', blood_groups=BLOOD_GROUPS)


@app.route('/request', methods=['GET', 'POST'])
def request_blood():
    if request.method == 'POST':
        try:
            br = BloodRequest(
                patient_name=request.form.get('patient_name'),
                contact_person=request.form.get('contact_person'),
                email=request.form.get('email'),
                phone=request.form.get('phone'),
                blood_group_needed=request.form.get('blood_group_needed'),
                units_required=int(request.form.get('units_required', '1')),
                hospital_name=request.form.get('hospital_name'),
                city=request.form.get('city'),
            )
            db.session.add(br)
            db.session.commit()

            # Auto-match eligible donors in same city and blood group
            matched = Donor.query.filter_by(blood_group=br.blood_group_needed, city=br.city, available=True).all()
            eligible_matched = [d for d in matched if d.eligible()]
            send_notifications(eligible_matched, br)

            flash('Request submitted. We will notify eligible donors.','success')
            return redirect(url_for('home'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {e}','danger')
    return render_template('request_blood.html', blood_groups=BLOOD_GROUPS)


@app.route('/donors', methods=['GET'])
def find_donors():
    blood_group = request.args.get('blood_group', '')
    city = request.args.get('city', '')
    query = Donor.query.filter_by(available=True)
    if blood_group:
        query = query.filter_by(blood_group=blood_group)
    if city:
        query = query.filter(Donor.city.ilike(f"%{city}%"))
    donors = [d for d in query.all() if d.eligible()]
    return render_template('find_donors.html', donors=donors, blood_groups=BLOOD_GROUPS, selected_bg=blood_group, selected_city=city)


@app.route('/dashboard')
def dashboard():
    total_donors = Donor.query.count()
    eligible_donors = sum(1 for d in Donor.query.all() if d.eligible())
    total_requests = BloodRequest.query.count()
    availability = count_blood_group_availability()
    return render_template('dashboard.html', total_donors=total_donors, eligible_donors=eligible_donors, total_requests=total_requests, availability=availability)


# -------------------------------------------------
# CLI / Startup
# -------------------------------------------------
with app.app_context():
    db.create_all()
    seed_data()


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
