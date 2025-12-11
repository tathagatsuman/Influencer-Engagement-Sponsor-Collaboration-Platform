from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///iescp.db'
app.config['SECRET_KEY'] = 'mysecret'


db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(15), nullable=False, default='influencer')
    niche = db.Column(db.String(20), nullable=False, default='technology')
    is_flagged = db.Column(db.Boolean, default=False)
    
    influencer_info = db.relationship('InfluencerInfo', backref='user', uselist=False, cascade="all, delete-orphan")
    sent_requests = db.relationship('Request', foreign_keys='Request.sender_id', backref='sent_by', lazy='dynamic', cascade="all, delete-orphan")
    received_requests = db.relationship('Request', foreign_keys='Request.receiver_id', backref='received_by', lazy='dynamic', cascade="all, delete-orphan")
    campaigns = db.relationship('Campaign', backref='sponsor', lazy=True, cascade="all, delete-orphan")


class InfluencerInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    active_status = db.Column(db.String(10), nullable=False, default='active')
    reach = db.Column(db.Integer, nullable=False,default=100000)    


class Campaign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500))
    start_date = db.Column(db.String(12))
    end_date = db.Column(db.String(12))
    budget = db.Column(db.Float)
    niche = db.Column(db.String(20))
    visibility = db.Column(db.String(10))
    goals = db.Column(db.String(500))
    sponsor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    is_flagged = db.Column(db.Boolean, default=False)

    requests = db.relationship('Request', backref='campaign', lazy=True, cascade="all, delete-orphan")


class Request(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    request_type = db.Column(db.String(10), nullable=False)
    status = db.Column(db.String(15), default='Pending')
    messages = db.Column(db.String(500))


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        niche = request.form['niche']
        if User.query.filter_by(username=username).first():
            flash('Username already exists. Please choose a different one.', 'danger')
            return redirect(url_for('register'))
        new_user = User(username=username, password=password, name=name, role=role, niche=niche)
        db.session.add(new_user)
        db.session.commit()
        if role == 'influencer':
            active_status = request.form['active_status']
            reach = int(request.form['reach'])
            influencer_info = InfluencerInfo(user_id=new_user.id, active_status=active_status, reach=reach)
            db.session.add(influencer_info)
            db.session.commit()
        login_user(new_user)
        return redirect(url_for('dashboard'))
    return render_template('register.html')


@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'admin':
        users = User.query.all()
        influencers= User.query.filter_by(role='influencer').all()
        for influencer in influencers:
            influencer_info = InfluencerInfo.query.filter_by(user_id=influencer.id).first()
            influencer.influencer_info = influencer_info
        campaigns = Campaign.query.all()
        requests = Request.query.all()
        return render_template('admin_dashboard.html', users=users, influencers=influencers, campaigns=campaigns, requests=requests)
    
    elif current_user.role == 'sponsor':
        users = User.query.filter_by(role='influencer').all()
        for user in users:
            influencer_info = InfluencerInfo.query.filter_by(user_id=user.id).first()
            user.influencer_info = influencer_info
        campaigns = Campaign.query.filter_by(sponsor_id=current_user.id).all()
        sent_requests = Request.query.filter(Request.sender_id == current_user.id, Request.request_type == 'sponsor').all()
        received_requests = Request.query.filter(Request.receiver_id == current_user.id, Request.request_type == 'influencer').all()
        return render_template('dashboard.html', campaigns=campaigns, sent_requests=sent_requests, received_requests=received_requests, users=users)
    elif current_user.role == 'influencer':
        campaigns = Campaign.query.all()
        sent_requests = Request.query.filter(Request.sender_id == current_user.id, Request.request_type == 'influencer').all()
        received_requests = Request.query.filter(Request.receiver_id == current_user.id, Request.request_type == 'sponsor').all()
        return render_template('dashboard.html', campaigns=campaigns, sent_requests=sent_requests, received_requests=received_requests)
    return render_template('dashboard.html')


@app.route('/admin/flag/user/<int:user_id>', methods=['POST'])
@login_required
def flag_user(user_id):
    if current_user.role != 'admin':
        return redirect(url_for('dashboar'))
    user = User.query.get_or_404(user_id)
    user.is_flagged = True
    db.session.commit()
    flash('User has been flagged.', 'success')
    return redirect(url_for('dashboard'))


@app.route('/admin/unflag/user/<int:user_id>', methods=['POST'])
@login_required
def unflag_user(user_id):
    if current_user.role != 'admin':
        return redirect(url_for('dashboard'))
    user = User.query.get_or_404(user_id)
    user.is_flagged = False
    db.session.commit()
    flash('User has been Unflagged.', 'success')
    return redirect(url_for('dashboard'))


@app.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    if user.role == 'admin':
        flash("Admin can't be deleted.", 'warning')
        return redirect(url_for('dashboard'))
    db.session.delete(user)
    db.session.commit()
    flash(f'User {user.username} has been deleted.', 'success')
    return redirect(url_for('dashboard'))


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/create_campaign', methods=['GET', 'POST'])
@login_required
def create_campaign():
    if current_user.role == 'sponsor' and request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        budget = request.form['budget']
        niche = request.form['niche']
        visibility = request.form['visibility']
        goals = request.form['goals']
        new_campaign = Campaign(name=name, description=description, start_date=start_date, end_date=end_date, budget=budget, niche=niche, visibility=visibility, goals=goals, sponsor_id=current_user.id)
        db.session.add(new_campaign)
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('create_campaign.html')


@app.route('/edit_campaign/<int:campaign_id>', methods=['GET', 'POST'])
@login_required
def edit_campaign(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    if current_user.role == 'sponsor' and campaign.sponsor_id == current_user.id:
        if request.method == 'POST':
            campaign.name = request.form['name']
            campaign.description = request.form['description']
            campaign.start_date = request.form['start_date']
            campaign.end_date = request.form['end_date']
            campaign.budget = request.form['budget']
            campaign.niche = request.form['niche']
            campaign.visibility = request.form['visibility']
            campaign.goals = request.form['goals']
            db.session.commit()
            return redirect(url_for('dashboard'))
        return render_template('edit_campaign.html', campaign=campaign)
    return redirect(url_for('dashboard'))


@app.route('/admin/flag/campaign/<int:campaign_id>', methods=['POST'])
@login_required
def flag_campaign(campaign_id):
    if current_user.role != 'admin':
        return redirect(url_for('dashboard'))
    campaign = Campaign.query.get_or_404(campaign_id)
    campaign.is_flagged = True
    db.session.commit()
    flash('Campaign has been flagged.', 'success')
    return redirect(url_for('dashboard'))


@app.route('/admin/unflag/campaign/<int:campaign_id>', methods=['POST'])
@login_required
def unflag_campaign(campaign_id):
    if current_user.role != 'admin':
        return redirect(url_for('dashboard'))
    campaign = Campaign.query.get_or_404(campaign_id)
    campaign.is_flagged = False
    db.session.commit()
    flash('Campaign has been Unflagged.', 'success')
    return redirect(url_for('dashboard'))


@app.route('/delete_campaign/<int:campaign_id>', methods=['POST'])
@login_required
def delete_campaign(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    if current_user.role != 'admin' and current_user.id != campaign.sponsor_id:
        return redirect(url_for('dashboard'))
    
    db.session.delete(campaign)
    db.session.commit()
    flash(f'Campaign {campaign.name} has been deleted.', 'success')
    return redirect(url_for('dashboard'))


@app.route('/send_request/<int:campaign_id>/<int:receiver_id>', methods=['POST'])
@login_required
def send_request(campaign_id, receiver_id):
    if current_user.role != 'influencer':
        return redirect(url_for('dashboard'))
    
    messages = request.form['messages']
    existing_request = Request.query.filter_by(campaign_id=campaign_id, sender_id=current_user.id, receiver_id=receiver_id, request_type='influencer').first()

    if existing_request:
        flash('You have already sent a request for this campaign.', 'warning')
    else:
        ad_request = Request(campaign_id=campaign_id, sender_id=current_user.id, receiver_id=receiver_id, request_type='influencer', messages=messages)
        db.session.add(ad_request)
        db.session.commit()
        flash('Request sent successfully!', 'success')

    return redirect(url_for('dashboard'))


@app.route('/request_influencer', methods=['POST'])
@login_required
def request_influencer():
    if current_user.role != 'sponsor':
        return redirect(url_for('dashboard'))
    
    campaign_id = request.form.get('campaign_id')
    influencer_id = request.form.get('influencer_id')
    messages = request.form['messages']
    existing_request = Request.query.filter_by(campaign_id=campaign_id, receiver_id=influencer_id, sender_id=current_user.id, request_type='sponsor').first()

    if existing_request:
        flash('You have already sent a request to this influencer for this campaign.', 'warning')
    else:
        ad_request = Request(campaign_id=campaign_id, receiver_id=influencer_id, sender_id=current_user.id, request_type='sponsor', messages=messages)
        db.session.add(ad_request)
        db.session.commit()
        flash('Request sent successfully!', 'success')

    return redirect(url_for('dashboard'))


@app.route('/delete_request/<int:request_id>', methods=['POST'])
@login_required
def delete_request(request_id):
    request = Request.query.get_or_404(request_id)
    if current_user.role != 'admin' and current_user.id != request.sender_id:
        return redirect(url_for('dashboard'))
    
    db.session.delete(request)
    db.session.commit()
    flash('Request has been deleted.', 'success')
    return redirect(url_for('dashboard'))


@app.route('/manage_request/<int:request_id>/<action>', methods=['POST'])
@login_required
def manage_request(request_id, action):    
    ad_request = Request.query.get_or_404(request_id)
    if (current_user.role == 'influencer' and ad_request.request_type == 'sponsor') or (current_user.role == 'sponsor' and ad_request.request_type == 'influencer'):
        if action == 'accept':
            ad_request.status = 'Accepted'
        elif action == 'reject':
            ad_request.status = 'Rejected'
        
        db.session.commit()
        flash(f'Request {action}ed successfully!', 'success')
    return redirect(url_for('dashboard'))


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.name = request.form['name']
        current_user.niche = request.form['niche']
        if current_user.role in ['influencer', 'sponsor']:
            if current_user.role == 'influencer':
                active_status = request.form['active_status']
                reach = int(request.form['reach'])
                influencer_info = InfluencerInfo.query.filter_by(user_id=current_user.id).first()
                influencer_info.active_status = active_status
                influencer_info.reach = reach
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))
    if current_user.role == 'influencer':
        influencer_info = InfluencerInfo.query.filter_by(user_id=current_user.id).first()
        return render_template('profile.html', user=current_user, influencer_info=influencer_info)    
    return render_template('profile.html', user=current_user)
    


if __name__ == '__main__':
    app.run(debug=True)
