from flask import Flask, send_from_directory, request, jsonify
from flask_sqlalchemy import SQLAlchemy 
from sqlalchemy import and_, or_,case
from sqlalchemy.orm import aliased
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token, jwt_required, get_jwt_identity, get_jwt
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta
from celery import Celery
from celery.schedules import crontab
from flask_caching import Cache
import pandas as pd
from smtplib import SMTP
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
import os, re


app = Flask(__name__, static_folder='dist')
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///iescp.db'
app.config['SECRET_KEY'] = 'mysecret'
app.config['JWT_SECRET_KEY'] = 'jwt-secret-string'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=15)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(hours=8)

app.config.update(
    broker_url="redis://localhost:6379/0",
    result_backend="redis://localhost:6379/0",
    broker_connection_retry_on_startup=True,
    CACHE_TYPE="RedisCache",
    CACHE_REDIS_URL="redis://localhost:6379/1",
    SMTP_SERVER="smtp.gmail.com",
    SMTP_PORT=587,
    SMTP_USERNAME="22f3002936@ds.study.iitm.ac.in",
    SMTP_PASSWORD="pvvkkeyzufczergt",
    SENDER_EMAIL="22f3002936@ds.study.iitm.ac.in",
)

db = SQLAlchemy(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)
cache = Cache(app)
celery = Celery(app.name, broker=app.config["broker_url"])
celery.conf.update(app.config)

celery.conf.beat_schedule = {
    "send-daily-reminder": {
        "task": "send_daily_reminder",
        "schedule": crontab(hour=9, minute=0)
    },
    "send-monthly-reminder": {
        "task": "send_monthly_reminder",
        "schedule": crontab(day_of_month="1", hour=9, minute=0)
    },
    "clean-expired-tokens": {
        "task": "clean_expired_blacklisted_tokens",
        "schedule": crontab(hour=0, minute=0)
    }
}
celery.conf.timezone = "UTC"

def send_email_reminder(receiver_mail, subject, body, attachment_path=None, is_html=False):
    message = MIMEMultipart()
    message["From"] = app.config['SENDER_EMAIL']
    message["To"] = receiver_mail
    message["Subject"] = subject
    message.attach(MIMEText(body, "html" if is_html else "plain"))

    if attachment_path:
        with open(attachment_path, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename= {os.path.basename(attachment_path)}")
            message.attach(part)

    with SMTP(app.config['SMTP_SERVER'], app.config['SMTP_PORT']) as server:
        server.starttls()
        server.login(app.config['SMTP_USERNAME'], app.config['SMTP_PASSWORD'])
        server.sendmail(app.config['SENDER_EMAIL'], receiver_mail, message.as_string())
    return


@celery.task(name="send_daily_reminder")
def send_daily_reminder():
    with app.app_context():
        users = User.query.filter(User.role == 'influencer').all()
        for user in users:
            requests = Request.query.filter(Request.receiver_id == user.id, Request.status == 'Pending').all()
            body = f"Hello! {user.name},\n\n"
            if requests:
                body += f"You have {len(requests)} pending requests, Kindly visit our portal and take action on them.\n\nSincerely,\nTeam IESCP."
            else:
                body += f"You have not recieved any requests today, Kindly engage yourself on our portal more and be active, so that you get better engagement on your profile.\n\nSincerely\nTeam IESCP."            
            send_email_reminder(user.username, "Daily Reminder", body)
    return

@celery.task(name="send_monthly_reminder")
def send_monthly_reminder():
    with app.app_context():
        today = datetime.now()
        this_month_start = today.replace(day=1)
        previous_month_end = this_month_start - timedelta(days=1)
        previous_month_start = previous_month_end.replace(day=1)
        users = User.query.filter(User.role == 'sponsor').all()
        for user in users:
            campaigns = Campaign.query.filter(Campaign.sponsor_id == user.id,or_(and_(Campaign.start_date >= previous_month_start, Campaign.start_date <= previous_month_end),and_(Campaign.end_date >= previous_month_start, Campaign.end_date <= previous_month_end))).all()
            sent_requests = []
            received_requests = []
            for campaign in campaigns:
                sent_requests += Request.query.filter(Request.sender_id == user.id, Request.campaign_id == campaign.id).all()
                received_requests += Request.query.filter(Request.receiver_id == user.id, Request.campaign_id == campaign.id).all()
            sent_pending = sum(1 for r in sent_requests if r.status == 'pending')
            sent_accepted = sum(1 for r in sent_requests if r.status == 'accepted')
            sent_rejected = sum(1 for r in sent_requests if r.status == 'rejected')
            received_pending = sum(1 for r in received_requests if r.status == 'pending')
            received_accepted = sum(1 for r in received_requests if r.status == 'accepted')
            received_rejected = sum(1 for r in received_requests if r.status == 'rejected')
            html_body = f"<h1>Monthly Activity Report for {user.name}</h1> <h2>Campaigns:</h2><ul>"
            for campaign in campaigns:
                html_body += f"<li><p><strong>{campaign.name}</strong> (Start: {campaign.start_date}, End: {campaign.end_date})</p> <p>Goal: {campaign.goals}</p> <p>Budget: <strong>{campaign.budget}</strong></p></li>"
            html_body += f"</ul><h2>Report Summary:</h2> <p>Sent Requests: Pending: {sent_pending}, Accepted: {sent_accepted}, Rejected: {sent_rejected}</p> <p>Received Requests: Pending: {received_pending}, Accepted: {received_accepted}, Rejected: {received_rejected}</p>"
            send_email_reminder(user.username,"Monthly Report", html_body, is_html=True)
    return


@celery.task(name="clean_expired_blacklisted_tokens")
def clean_expired_blacklisted_tokens():
    with app.app_context():
        expired_tokens = TokenBlacklist.query.filter(TokenBlacklist.expires < datetime.now()).all()
        if expired_tokens:
            for token in expired_tokens:
                cache.delete(token.jti)
                db.session.delete(token)
            db.session.commit()
    return


@celery.task(name="export_campaigns_as_csv")
def export_campaigns_as_csv(sponsor_id):
    with app.app_context():
        user = User.query.filter(User.id == sponsor_id).first()
        campaigns = Campaign.query.filter(Campaign.sponsor_id == sponsor_id).all()
        if not campaigns:
            body = f"Hello! {user.name},\n\nNo campaigns found for sponsor ID {user.id} and sponsor {user.name}.\n\nBest Regards,\nTeam IESCP."
            attachment_path = None
        else:
            body = f"Hello! {user.name},\n\nHere is the list of campaigns for sponsor ID {user.id} and sponsor {user.name}.\n\nPlease! Find attachment.\n\nBest Regards,\nTeam IESCP."
            data = [{
                'Name': campaign.name,
                'Description': campaign.description,
                'Niche': campaign.niche,
                'Start Date': campaign.start_date.strftime('%Y-%m-%d') if campaign.start_date else '',
                'End Date': campaign.end_date.strftime('%Y-%m-%d') if campaign.end_date else '',
                'Budget': campaign.budget,
                'Visibility': campaign.visibility,
                'Goals': campaign.goals
            } for campaign in campaigns]
            
            df = pd.DataFrame(data)
            csv_file_path = f"campaigns_{sponsor_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            df.to_csv(csv_file_path, index=False, encoding='utf-8')
            attachment_path = csv_file_path
        send_email_reminder(user.username, "Campaigns Report", body, attachment_path)
    return True


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(15), nullable=False, default='influencer')
    niche = db.Column(db.String(20), nullable=False, default='technology')
    is_flagged = db.Column(db.Boolean, default=False)
    isApproved = db.Column(db.Boolean, default=False)
    
    influencer_info = db.relationship('InfluencerInfo', backref='user', uselist=False, cascade="all, delete-orphan")
    sent_requests = db.relationship('Request', foreign_keys='Request.sender_id', backref='sent_by', lazy='dynamic', cascade="all, delete-orphan")
    received_requests = db.relationship('Request', foreign_keys='Request.receiver_id', backref='received_by', lazy='dynamic', cascade="all, delete-orphan")
    campaigns = db.relationship('Campaign', backref='sponsor', lazy=True, cascade="all, delete-orphan")
    
    def to_dict(self, include=None):
        data = {col.name: getattr(self, col.name) for col in self.__table__.columns}
        if include:
            return {key: data[key] for key in include}
        return data


class InfluencerInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    active_status = db.Column(db.String(10), nullable=False, default='active')
    reach = db.Column(db.Integer, nullable=False,default=100000)    
    
    def to_dict(self, include=None):
        data = {col.name: getattr(self, col.name) for col in self.__table__.columns}
        if include:
            return {key: data[key] for key in include}
        return data


class Campaign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500))
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    budget = db.Column(db.Float)
    niche = db.Column(db.String(20))
    visibility = db.Column(db.String(10))
    goals = db.Column(db.String(500))
    sponsor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    is_flagged = db.Column(db.Boolean, default=False)

    requests = db.relationship('Request', backref='campaign', lazy=True, cascade="all, delete-orphan")
    
    def to_dict(self, include=None):
        data = {col.name: getattr(self, col.name) for col in self.__table__.columns}
        if 'start_date' in data:
            data['start_date'] = data['start_date'].strftime("%Y-%m-%d") if data['start_date'] else None
        if 'end_date' in data:
            data['end_date'] = data['end_date'].strftime("%Y-%m-%d") if data['end_date'] else None

        if include:
            return {key: data[key] for key in include}
        return data


class Request(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    request_type = db.Column(db.String(10), nullable=False)
    status = db.Column(db.String(15), default='Pending')
    messages = db.Column(db.String(500))
    
    def to_dict(self, include=None):
        data = {col.name: getattr(self, col.name) for col in self.__table__.columns}
        if include:
            return {key: data[key] for key in include}
        return data
    
    
class TokenBlacklist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), nullable=False, unique=True, index=True)
    token_type = db.Column(db.String(10), nullable=False)
    expires = db.Column(db.DateTime, nullable=False)


def convert_users_to_dict(users):
    user_data = []
    for user, reach, active_status in users:
        user_dict = user.to_dict()
        if user_dict['role'] == "influencer":
            influencer_info_dict = { 'reach': reach, 'active_status': active_status }
        else:
            influencer_info_dict = {}
        combined_dict = {**user_dict, **influencer_info_dict}
        user_data.append(combined_dict)
    return user_data


def convert_campaigns_to_dict(campaigns):
    campaign_data = []
    for campaign, sponsor_name, sponsor_username in campaigns:
        campaign_dict = campaign.to_dict()
        sponsor_info_dict = { 'sponsor_name': sponsor_name, 'sponsor_username': sponsor_username }
        combined_dict = {**campaign_dict, **sponsor_info_dict}
        campaign_data.append(combined_dict)
    return campaign_data


def convert_requests_to_dict(requests):
    request_data = []
    for request, campaign_name, sender_name, sender_username, receiver_name, receiver_username in requests:
        request_dict = request.to_dict()
        sender_receiver_dict = { 'campaign_name': campaign_name, 'sender_name': sender_name, 'sender_username': sender_username, 'receiver_name': receiver_name, 'receiver_username': receiver_username }
        combined_dict = { **request_dict, **sender_receiver_dict }
        request_data.append(combined_dict)
    return request_data


def convert_request_sponsor_to_dict(requests):
    request_data = []
    for request, campaign_name, influencer_name, influencer_username, niche, reach, active_status in requests:
        request_dict = request.to_dict()
        campaign_influencer_dict = { 'campaign_name': campaign_name, 'influencer_name': influencer_name, 'influencer_username': influencer_username, 'niche': niche, 'reach': reach, 'active_status': active_status }
        combined_dict = { **request_dict, **campaign_influencer_dict }
        request_data.append(combined_dict)
    return request_data


def convert_request_influencer_to_dict(requests):
    request_data = []
    for request_id, request_type, messages, status, campaign, sponsor_name, sponsor_username in requests:
        request_dict = { 'request_id': request_id, 'request_type': request_type, 'messages': messages, 'status': status }
        campaign_dict = campaign.to_dict()
        campaign_sponsor_dict = { 'sponsor_name': sponsor_name, 'sponsor_username': sponsor_username }
        combined_dict = { **request_dict, **campaign_dict, **campaign_sponsor_dict }
        request_data.append(combined_dict)
    return request_data


def hash_password(password):
    return generate_password_hash(password)


def verify_password(password_hash, password):
    return check_password_hash(password_hash, password)


def is_token_blacklisted(jti):
    if cache.get(jti) is not None:
        return True
    token = TokenBlacklist.query.filter_by(jti=jti).first()
    if token:
        cache.set(jti, token.token_type, timeout=(token.expires - datetime.datetime.now()).total_seconds())
        return True
    return False


@jwt.token_in_blocklist_loader
def check_if_token_is_revoked(jwt_header, jwt_payload):
    jti = jwt_payload["jti"]
    return is_token_blacklisted(jti)


@jwt.revoked_token_loader
def revoked_token_response(jwt_header, jwt_payload):
    return jsonify({"msg": "Token has been revoked"}), 401

@app.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    user_id = get_jwt_identity()
    new_access_token = create_access_token(identity=user_id)
    return jsonify({"access_token": new_access_token}), 200


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def index(path):
    # If the request is for a static file (CSS/JS), serve it normally
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    # For all other paths, serve the index.html so Vue Router can handle it
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    user = User.query.filter_by(username=username).first()
    if user and verify_password(user.password, password):
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        user_dict = user.to_dict()
        if user.role == 'influencer':
            influencer_info = InfluencerInfo.query.filter_by(user_id = user.id).first()
            user_dict['reach'] = influencer_info.reach
            user_dict['active_status'] = influencer_info.active_status
        return jsonify({ "user": user_dict,"access_token": access_token, "refresh_token": refresh_token, 'message': 'Login successful!'}), 200
    return jsonify({"error": "Invalid username or password."}), 401
    

def is_valid_email(email):
    email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(email_regex, email) is not None


def is_valid_password(password):
    password_regex = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'
    return re.match(password_regex, password) is not None


@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    name = data.get('name')
    role = data.get('role', 'influencer')
    niche = data.get('niche', 'technology')
    
    if not username or len(username) > 50 or not is_valid_email(username):
        return jsonify({"error": "Invalid or missing 'email'. Must be a valid email address and 50 characters or less."}), 400
    if not password or len(password) < 8 or not is_valid_password(password):
        return jsonify({"error": "Invalid or missing 'password'. Must be at least 8 characters long."}), 400
    if not name or len(name) > 50:
        return jsonify({"error": "Invalid or missing 'name'. Must be 50 characters or less."}), 400
    if role not in ['influencer', 'sponsor', 'admin']:
        return jsonify({"error": "Invalid 'role'. Must be one of ['influencer', 'sponsor', 'admin']."}), 400
    if niche not in ['automobiles', 'beverages', 'education', 'fashion', 'food', 'real estates', 'sports', 'technology']:
        return jsonify({"error": "Invalid 'niche'. Must be one of ['automobiles', 'beverages', 'education', 'fashion', 'food', 'real estates', 'sports', 'technology']."}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already exists."}), 400   

    new_user = User(username=username, password=hash_password(password), name=name, role=role, niche=niche)
    db.session.add(new_user)
    db.session.commit()
    if role == 'influencer':
        active_status = data.get('active_status', 'active')
        reach = int(data.get('reach', 100000))
        if active_status not in ['active', 'inactive']:
            return jsonify({"error": "Invalid 'active_status'. Must be 'active' or 'inactive'."}), 400
        try:
            reach = int(reach)
            if reach < 0:
                raise ValueError
        except ValueError:
            return jsonify({"error": "Invalid 'reach'. Must be a positive integer."}), 400
        influencer_info = InfluencerInfo(user_id=new_user.id, active_status=active_status, reach=reach)
        db.session.add(influencer_info)
        db.session.commit()
    user = User.query.filter_by(username=username).first()
    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))
    user = user.to_dict()
    if user['role'] == 'influencer':
            influencer_info = InfluencerInfo.query.filter_by(user_id = user['id']).first()
            user['reach'] = influencer_info.reach
            user['active_status'] = influencer_info.active_status
    return jsonify({"user": user, "access_token": access_token, "refresh_token": refresh_token,"message": "User registered successfully!"}), 201
   

def get_dashboard_cache_key(user_id, role):
    return f'dashboard_{user_id}_{role}'


@app.route('/dashboard')
@jwt_required()
@cache.cached(timeout=300, key_prefix=lambda: get_dashboard_cache_key(get_jwt_identity(), User.query.get_or_404(get_jwt_identity()).role))
def dashboard():
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    if user.role == 'admin':
        users = db.session.query(User, case((User.role == 'influencer', InfluencerInfo.reach), else_=None).label('reach'), case((User.role == 'influencer', InfluencerInfo.active_status), else_=None).label('active_status')).outerjoin(InfluencerInfo, User.id == InfluencerInfo.user_id).all()
        campaigns = db.session.query(Campaign, User.name.label('sponsor_name'), User.username.label('sponsor_username')).join(User, Campaign.sponsor_id == User.id).all()
        Sender = aliased(User)
        Receiver = aliased(User)
        requests = db.session.query(Request, Campaign.name.label('campaign_name'), Sender.name.label('sender_name'), Sender.username.label('sender_username'), Receiver.name.label('receiver_name'), Receiver.username.label('receiver_username')).join(Campaign, Request.campaign_id == Campaign.id).join(Sender, Request.sender_id == Sender.id).join(Receiver, Request.receiver_id == Receiver.id).all()
        
        user_data = convert_users_to_dict(users)
        campaign_data = convert_campaigns_to_dict(campaigns)
        request_data = convert_requests_to_dict(requests)
        
        return jsonify({"users": user_data, "campaigns": campaign_data, "requests": request_data}), 200
    
    elif user.role == 'sponsor':
        influencers = db.session.query(User, InfluencerInfo.reach.label('reach'), InfluencerInfo.active_status.label('active_status')).join(InfluencerInfo, User.id == InfluencerInfo.user_id).filter(User.role == 'influencer').all()
        campaigns = db.session.query(Campaign).filter(Campaign.sponsor_id == user.id).all()
        sent_requests = db.session.query(Request, Campaign.name.label('campaign_name'), User.name.label('influencer_name'), User.username.label('influencer_username'), User.niche.label('niche'), InfluencerInfo.reach.label('reach'), InfluencerInfo.active_status.label('active_status') ).join(Campaign, Request.campaign_id == Campaign.id).join(User, Request.receiver_id == User.id).join(InfluencerInfo, User.id == InfluencerInfo.user_id).filter(Request.sender_id == user.id, Request.request_type == 'sponsor').all()
        received_requests = db.session.query(Request, Campaign.name.label('campaign_name'), User.name.label('influencer_name'), User.username.label('influencer_username'), User.niche.label('niche'), InfluencerInfo.reach.label('reach'), InfluencerInfo.active_status.label('active_status') ).join(Campaign, Request.campaign_id == Campaign.id).join(User, Request.sender_id == User.id).join(InfluencerInfo, User.id == InfluencerInfo.user_id).filter(Request.receiver_id == user.id, Request.request_type == 'influencer').all()
    
        influencer_data = convert_users_to_dict(influencers)
        campaign_data = [item.to_dict() for item in campaigns]
        sent_request_data = convert_request_sponsor_to_dict(sent_requests)
        received_request_data = convert_request_sponsor_to_dict(received_requests)
    
        return jsonify({"influencers": influencer_data, "campaigns": campaign_data, "sent_requests": sent_request_data, "recieved_requests": received_request_data}), 200
    
    elif user.role == 'influencer':
        campaigns = db.session.query(Campaign, User.name.label('sponsor_name'), User.username.label('sponsor_username')).join(User, Campaign.sponsor_id == User.id).all()
        sent_requests = db.session.query(Request.id.label('request_id'), Request.request_type.label('request_type'), Request.messages.label('messages'), Request.status.label('status'), Campaign, User.name.label('sponsor_name'), User.username.label('sponsor_username')).join(Campaign, Request.campaign_id == Campaign.id).join(User, Request.receiver_id == User.id).filter(Request.sender_id == user.id, Request.request_type == 'influencer').all()
        received_requests =  db.session.query(Request.id.label('request_id'), Request.request_type.label('request_type'), Request.messages.label('messages'), Request.status.label('status'), Campaign, User.name.label('sponsor_name'), User.username.label('sponsor_username')).join(Campaign, Request.campaign_id == Campaign.id).join(User, Request.sender_id == User.id).filter(Request.receiver_id == user.id, Request.request_type == 'sponsor').all()
        
        campaign_data = convert_campaigns_to_dict(campaigns)
        sent_request_data = convert_request_influencer_to_dict(sent_requests)
        received_request_data = convert_request_influencer_to_dict(received_requests)
    
        return jsonify({"campaigns": campaign_data, "sent_requests": sent_request_data, "recieved_requests": received_request_data}), 200
    
    return jsonify({"error": "Unauthorized request denied."}), 401


@app.route('/sponsor/export_csv_report', methods=['GET'], endpoint='export_csv_report')
@jwt_required()
def export_csv_report():
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    if user.role == 'sponsor':
        try:
            export_campaigns_as_csv.delay(user.id)
            return jsonify({"message": "Success, Export is initiated. You will receive an email with the report shortly."}), 200
        except Exception as e:
            return jsonify({"error": f"Unexpected error occurred: {str(e)}"}), 500
    return jsonify({"error": "Unauthorized request denied."}), 403
    

@app.route('/admin/approve_sponsor/<int:user_id>', methods=['PUT'], endpoint='manage_sponsor')
@jwt_required()
def approve_sponsor(user_id):
    admin_id = get_jwt_identity()
    user = User.query.get_or_404(admin_id)
    if user.role != 'admin':
        return jsonify({"error": "Unauthorized request denied."}), 403
    sponsor = User.query.get_or_404(user_id)
    if sponsor.role != 'admin' and sponsor.role != 'influencer' and not sponsor.isApproved:
        sponsor.isApproved = True
        db.session.commit()
        cache.delete(get_dashboard_cache_key(user.id, 'admin'))
    else:
        return jsonify({"error": "Unauthorized request denied."}), 400
    return jsonify({"message": "Success, Sponsor approved."}), 200
    
    
@app.route('/admin/flag_user/user/<int:user_id>', methods=['PUT'], endpoint='flag_user_by_id')
@jwt_required()
def flag_user(user_id):
    admin_id = get_jwt_identity()
    user = User.query.get_or_404(admin_id)
    if user.role != 'admin':
        return jsonify({"error": "Unauthorized request denied."}), 403
    user_to_be_flagged = User.query.get_or_404(user_id)
    if user_to_be_flagged.role != 'admin' and not user_to_be_flagged.is_flagged:
        user_to_be_flagged.is_flagged = True
        db.session.commit()
        cache.delete(get_dashboard_cache_key(user.id, 'admin'))
    else:
        return jsonify({"error": "Unauthorized request denied."}), 400
    return jsonify({"message": "Success, User flagged."}), 200


@app.route('/admin/unflag_user/user/<int:user_id>', methods=['PUT'],  endpoint='unflag_user_by_id')
@jwt_required()
def unflag_user(user_id):
    admin_id = get_jwt_identity()
    user = User.query.get_or_404(admin_id)
    if user.role != 'admin':
        return jsonify({"error": "Unauthorized request denied."}), 403
    user_to_be_unflagged = User.query.get_or_404(user_id)
    if user_to_be_unflagged.role != 'admin' and user_to_be_unflagged.is_flagged:
        user_to_be_unflagged.is_flagged = False
        db.session.commit()
        cache.delete(get_dashboard_cache_key(user.id, 'admin'))
    else:
        return jsonify({"error": "Unauthorized request denied."}), 400
    return jsonify({"message": "Success, User unflagged."}), 200


@app.route('/delete_user/<int:user_id>', methods=['DELETE'], endpoint='delete_user_by_id')
@jwt_required()
def delete_user(user_id):
    admin_id = get_jwt_identity()
    user = User.query.get_or_404(admin_id)
    if user.role != 'admin':
        return jsonify({"error": "Unauthorized request denied."}), 403
    user_to_be_deleted = User.query.get_or_404(user_id)
    if user_to_be_deleted.role != 'admin':
        db.session.delete(user_to_be_deleted)
        db.session.commit()
        cache.delete(get_dashboard_cache_key(user.id, 'admin'))
    else:
        return jsonify({"error": "Unauthorized request denied."}), 400
    return jsonify({"message": "Success, User Deleted."}), 200


@app.route('/logout_refresh', methods=['POST'], endpoint='loggig_out_user_refresh_token_invalidation')
@jwt_required(refresh=True)
def logout_refresh():
    user_id = get_jwt_identity()
    jti = get_jwt()["jti"]
    token_type = get_jwt()["type"]
    expires = datetime.fromtimestamp(get_jwt()["exp"])
    if expires > datetime.now():
        revoked_token = TokenBlacklist(jti=jti, token_type=token_type, expires=expires)
        db.session.add(revoked_token)
        db.session.commit()
        timeout = int(max((expires - datetime.now()).total_seconds(), 0))
        if timeout > 0:
            cache.set(jti, token_type, timeout=timeout)
        cache.delete(get_dashboard_cache_key(user_id, 'admin'))
        cache.delete(get_dashboard_cache_key(user_id, 'sponsor'))
        cache.delete(get_dashboard_cache_key(user_id, 'influencer'))
    return jsonify({"message": "Refresh token revoked"}), 200

@app.route('/logout', methods=['POST'], endpoint='loggig_out_user_access_token_invalidation')
@jwt_required()
def logout():
    user_id = get_jwt_identity()
    jti = get_jwt()["jti"]
    token_type = get_jwt()["type"]
    expires = datetime.fromtimestamp(get_jwt()["exp"])
    if expires > datetime.now():
        revoked_token = TokenBlacklist(jti=jti, token_type=token_type, expires=expires)
        db.session.add(revoked_token)
        db.session.commit()
        timeout = int(max((expires - datetime.now()).total_seconds(), 0))
        if timeout > 0:
            cache.set(jti, token_type, timeout=timeout)
        cache.delete(get_dashboard_cache_key(user_id, 'admin'))
        cache.delete(get_dashboard_cache_key(user_id, 'sponsor'))
        cache.delete(get_dashboard_cache_key(user_id, 'influencer'))
    return jsonify({"message": "Successfully logged out"}), 200


def validate_campaign_data(data):
    errors = {}
    name = data.get('name')
    if not name or not isinstance(name, str) or len(name) > 100:
        errors['name'] = "Name is required, should be a string, and less than 100 characters."
    description = data.get('description')
    if description and (not isinstance(description, str) or len(description) > 500):
        errors['description'] = "Description should be a string and less than 500 characters."
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    date_format = "%Y-%m-%d"
    try:
        if start_date:
            datetime.strptime(start_date, date_format)
        if end_date:
            datetime.strptime(end_date, date_format)
        if start_date and end_date and start_date > end_date:
            errors['date_range'] = "Start date must be before the end date."
    except ValueError:
        errors['date_format'] = "Dates should be in 'YYYY-MM-DD' format."
    budget = data.get('budget')
    if budget is not None:
        try:
            budget = float(budget)
            if budget < 0:
                errors['budget'] = "Budget must be a positive number."
        except ValueError:
            errors['budget'] = "Budget should be a number."
    niche = data.get('niche')
    if niche and niche not in ['automobiles', 'beverages', 'education', 'fashion', 'food', 'real estates', 'sports', 'technology']:
        errors['niche'] = "Niche should Must be one of ['automobiles', 'beverages', 'education', 'fashion', 'food', 'real estates', 'sports', 'technology']."
    visibility = data.get('visibility')
    if visibility not in ["public", "private"]:
        errors['visibility'] = "Visibility should be 'public' or 'private'."
    goals = data.get('goals')
    if goals and (not isinstance(goals, str) or len(goals) > 500):
        errors['goals'] = "Goals should be a string and less than 500 characters."
    return errors


@app.route('/create_campaign', methods=['POST'], endpoint='create_campaign')
@jwt_required()
def create_campaign():
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    if user.role == 'sponsor' and user.isApproved:
        errors = validate_campaign_data(data)
        if errors:
            return jsonify(errors), 400
        name=data.get('name')
        description=data.get('description')
        try:
            start_date = datetime.strptime(data.get('start_date'), "%Y-%m-%d")
            end_date = datetime.strptime(data.get('end_date'), "%Y-%m-%d")
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400
        budget=data.get('budget')
        niche=data.get('niche')
        visibility=data.get('visibility')
        goals=data.get('goals')    
        new_campaign = Campaign(name=name, description=description, start_date=start_date, end_date=end_date, budget=budget, niche=niche, visibility=visibility, goals=goals, sponsor_id=user.id)
        db.session.add(new_campaign)
        db.session.commit()
        cache.delete(get_dashboard_cache_key(user_id, 'sponsor'))
    else:
        return jsonify({"error": "Unauthorized request denied."}), 403
    return jsonify({'message': 'Campaign created successfully!'}), 201


@app.route('/edit_campaign/<int:campaign_id>', methods=['PUT'], endpoint='edit_campaign')
@jwt_required()
def edit_campaign(campaign_id):
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    campaign = Campaign.query.get_or_404(campaign_id)
    if user.role == 'sponsor' and campaign.sponsor_id == user.id:
        data = request.get_json()
        errors = validate_campaign_data(data)
        if errors:
            return jsonify(errors), 400
        campaign.name = data.get('name')
        campaign.description = data.get('description')
        try:
            campaign.start_date = datetime.strptime(data.get('start_date'), "%Y-%m-%d")
            campaign.end_date = datetime.strptime(data.get('end_date'), "%Y-%m-%d")
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400
        campaign.budget = data.get('budget')
        campaign.niche = data.get('niche')
        campaign.visibility = data.get('visibility')
        campaign.goals = data.get('goals')
        db.session.commit()  
        cache.delete(get_dashboard_cache_key(user_id, 'sponsor'))
    else:
        return jsonify({"error": "Unauthorized request denied."}), 403
    return jsonify({'message': 'Campaign updated successfully!'}), 200


@app.route('/admin/flag_campaign/campaign/<int:campaign_id>', methods=['PUT'], endpoint='flag_campaign_by_id')
@jwt_required()
def flag_campaign(campaign_id):
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    if user.role != 'admin':
        return jsonify({"error": "Unauthorized request denied."}), 401
    campaign = Campaign.query.get_or_404(campaign_id)
    campaign.is_flagged = True
    db.session.commit()
    cache.delete(get_dashboard_cache_key(user.id, 'admin'))
    return jsonify({"message": "Success, Campaign flagged."}), 200


@app.route('/admin/unflag_campaign/campaign/<int:campaign_id>', methods=['PUT'], endpoint='unflag_campaign_by_id')
@jwt_required()
def unflag_campaign(campaign_id):
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    if user.role != 'admin':
        return jsonify({"error": "Unauthorized request denied."}), 403
    campaign = Campaign.query.get_or_404(campaign_id)
    campaign.is_flagged = False
    db.session.commit()
    cache.delete(get_dashboard_cache_key(user.id, 'admin'))
    return jsonify({"message": "Success, Campaign unflagged."}), 200


@app.route('/delete_campaign/<int:campaign_id>', methods=['DELETE'], endpoint='delete_campaign_by_id')
@jwt_required()
def delete_campaign(campaign_id):
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    campaign = Campaign.query.get_or_404(campaign_id)
    if user.role != 'admin' and user.id != campaign.sponsor_id:
        return jsonify({"error": "Unauthorized request denied."}), 403    
    db.session.delete(campaign)
    db.session.commit()
    cache.delete(get_dashboard_cache_key(user.id, 'admin'))
    cache.delete(get_dashboard_cache_key(user.id, 'sponsor'))    
    return jsonify({"message": "Success, Campaign deleted."}), 200


@app.route('/send_request/<int:campaign_id>/<int:receiver_id>', methods=['POST'], endpoint='send_request_to_sponsor')
@jwt_required()
def send_request(campaign_id, receiver_id):
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    if user.role != 'influencer':
        return jsonify({"error": "Unauthorized request denied."}), 403          
    else:
        data = request.get_json()
        if 'messages' in data and (not isinstance(data['messages'], str) or len(data['messages']) > 1000):
            return jsonify({"error": "Messages should be a string and less than 1000 characters."}), 400
        messages = data.get('messages')
        campaign = Campaign.query.filter_by(id=campaign_id, sponsor_id=receiver_id).first()
        if not campaign:
            return jsonify({"error": "Requested campaign not found for the given receiver ID."}), 404
    existing_request = Request.query.filter_by(campaign_id=campaign_id, sender_id=user.id, receiver_id=receiver_id, request_type='influencer').first()
    if existing_request:
        return jsonify({"error": "Send request already exist."}), 409
    ad_request = Request(campaign_id=campaign_id, sender_id=user.id, receiver_id=receiver_id, request_type='influencer', messages=messages)
    db.session.add(ad_request)
    db.session.commit()
    cache.delete(get_dashboard_cache_key(user.id, 'influencer'))
    return jsonify({"message": "Success, Request sent successfully!"}), 200


@app.route('/request_influencer', methods=['POST'], endpoint='send_request_to_influencer')
@jwt_required()
def request_influencer():
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    if user.role != 'sponsor':
        return jsonify({"error": "Unauthorized request denied."}), 403   
    data = request.get_json()    
    campaign_id = data.get('campaign_id')
    if not db.session.get(Campaign, campaign_id):
        return jsonify({"error": "Campaign not found with request campaign ID."}), 404
    influencer_id = data.get('influencer_id')
    if not db.session.get(User, influencer_id):
        return jsonify({"error": "Receiver not found with requested influencer ID."}), 404
    if 'messages' in data and (not isinstance(data['messages'], str) or len(data['messages']) > 1000):
            return jsonify({"error": "Messages should be a string and less than 1000 characters."}), 400
    messages = data.get('messages')    
    existing_request = Request.query.filter_by(campaign_id=campaign_id, receiver_id=influencer_id, sender_id=user.id, request_type='sponsor').first()
    if existing_request:
        return jsonify({"error": "Send request already exist."}), 409
    else:
        ad_request = Request(campaign_id=campaign_id, receiver_id=influencer_id, sender_id=user.id, request_type='sponsor', messages=messages)
        db.session.add(ad_request)
        db.session.commit()
        cache.delete(get_dashboard_cache_key(user.id, 'sponsor'))
    return jsonify({"message": "Success, Request sent successfully!"}), 200


@app.route('/update_request/<int:request_id>', methods=['PUT'], endpoint='edit_request')
@jwt_required()
def update_request(request_id):
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    ad_request = Request.query.get_or_404(request_id)
    if ad_request.sender_id != user.id:
        return jsonify({"error": "Unauthorized request denied."}), 403
    data = request.get_json()
    if user.role == 'influencer':
        if 'messages' in data and (not isinstance(data['messages'], str) or len(data['messages']) > 1000):
            return jsonify({"error": "Messages should be a string and less than 1000 characters."}), 400
        messages = data.get('messages')
        ad_request.messages = messages
    elif user.role == 'sponsor':
        campaign_id = data.get('campaign_id')
        if not db.session.get(Campaign, campaign_id):
            return jsonify({"error": "Enter a valid campaign ID."}), 404
        if 'messages' in data and (not isinstance(data['messages'], str) or len(data['messages']) > 1000):
            return jsonify({"error": "Messages should be a string and less than 1000 characters."}), 400
        messages = data.get('messages')
        ad_request.campaign_id = campaign_id
        ad_request.messages = messages
    db.session.commit()
    cache.delete(get_dashboard_cache_key(user.id, 'influencer'))
    cache.delete(get_dashboard_cache_key(user.id, 'sponsor'))
    return jsonify({"message": "Success, Request Updated..."}), 200      


@app.route('/delete_request/<int:request_id>', methods=['DELETE'], endpoint='delete_request')
@jwt_required()
def delete_request(request_id):
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    request = Request.query.get_or_404(request_id)
    if user.role != 'admin' and user.id != request.sender_id:
        return jsonify({"error": "Unauthorized request denied."}), 403      
    db.session.delete(request)
    db.session.commit()
    cache.delete(get_dashboard_cache_key(user.id, 'admin'))
    cache.delete(get_dashboard_cache_key(user.id, 'sponsor'))
    cache.delete(get_dashboard_cache_key(user.id, 'influencer'))
    return jsonify({"message": "Success, Campaign deleted."}), 200


@app.route('/manage_request/<int:request_id>/<action>', methods=['PUT'], endpoint='manage_request')
@jwt_required()
def manage_request(request_id, action):  
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)  
    ad_request = Request.query.get_or_404(request_id)
    print(user, ad_request)
    if user.id == ad_request.receiver_id:
        if action == 'accept':
            ad_request.status = 'Accepted'
        elif action == 'reject':
            ad_request.status = 'Rejected'
        else:
            return jsonify({"error": "Manage Request should be one of ['accept', 'reject']"}), 400        
        db.session.commit()
        cache.delete(get_dashboard_cache_key(user.id, 'sponsor'))
        cache.delete(get_dashboard_cache_key(user.id, 'influencer'))        
    else:
        return jsonify({"error": "Unauthorized request denied."}), 403
    return jsonify({"message": f'Success, Request {action}ed successfully!'}), 200


@app.route('/profile', methods=['PUT'], endpoint='update_profile')
@jwt_required()
def profile():
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    influencer_info = InfluencerInfo.query.filter_by(user_id=user.id).first()   
    if user.role == 'admin':
        return jsonify({"error": "Unauthorized request denied."}), 403   
    data = request.get_json()
    name = data.get('name')
    niche = data.get('niche')
    if not name or len(name) > 50:
        return jsonify({"error": "Invalid or missing 'name'. Must be 50 characters or less."}), 400
    if niche not in ['automobiles', 'beverages', 'education', 'fashion', 'food', 'real estates', 'sports', 'technology']:
        return jsonify({"error": "Invalid 'niche'. Must be one of ['automobiles', 'beverages', 'education', 'fashion', 'food', 'real estates', 'sports', 'technology']."}), 400
    user.name = name
    user.niche = niche
    if user.role == 'influencer':
        active_status = data.get('active_status', 'active')
        reach = int(data.get('reach', 100000))
        if active_status not in ['active', 'inactive']:
            return jsonify({"error": "Invalid 'active_status'. Must be 'active' or 'inactive'."}), 400
        try:
            reach = int(reach)
            if reach < 0:
                raise ValueError
        except ValueError:
            return jsonify({"error": "Invalid 'reach'. Must be a positive integer."}), 400
        influencer_info.active_status = active_status
        influencer_info.reach = int(reach)
    db.session.commit()
    return jsonify({"message": "Success, Profile updated successfully."}), 200
    

if __name__ == '__main__':
    app.run(debug=True)
