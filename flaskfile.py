from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime
from models import db, User, Gig, Application, Notification

app = Flask(__name__)
app.secret_key = 'campus-gig-board-secret-2026'
app.config['SQLALCHEMY_DATABASE_URI']        = 'sqlite:///campus_gig_board.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

STATUS_ORDER  = ['open', 'applied', 'in_progress', 'completed']
STATUS_LABELS = {'open':'OPEN','applied':'APPLIED','in_progress':'IN PROGRESS','completed':'DONE'}
STATUS_EMOJI  = {'open':'🟢','applied':'🔵','in_progress':'🟡','completed':'✅'}

def notify(user_email, message, link='', icon='🔔'):
    db.session.add(Notification(user_email=user_email,message=message,link=link,icon=icon))

def seed_data():
    if Gig.query.count() > 0: return
    demo = User.query.filter_by(email='demo@college.edu').first()
    if not demo:
        demo = User(email='demo@college.edu',username='Demo User',
                    password='demo123',skills_str='Design, Python',upi_id='demo@upi')
        db.session.add(demo); db.session.flush()
    seeds = [
        Gig(title='Design a Hackathon Poster',description='Need a vibrant A3 poster for our college hackathon. Must deliver editable file.',category='Design',bounty=300,deadline='Mar 18',poster_email='demo@college.edu',status='open'),
        Gig(title='Debug My React App',description='Small e-commerce project, 2 broken pages. Need fix + explanation in 1 day.',category='Code',bounty=500,deadline='Mar 17',poster_email='demo@college.edu',status='in_progress'),
        Gig(title='Write a 500-word Blog Post',description='Topic: "AI in Education". SEO-friendly, plagiarism-free, informal tone.',category='Writing',bounty=200,deadline='Mar 19',poster_email='demo@college.edu',status='completed'),
        Gig(title='Create PPT Template',description='10-slide modern presentation template for student club annual meet.',category='Design',bounty=250,deadline='Mar 20',poster_email='demo@college.edu',status='open'),
    ]
    db.session.add_all(seeds); db.session.commit()

with app.app_context():
    db.create_all(); seed_data()

def current_user():
    email = session.get('user')
    return User.query.filter_by(email=email).first() if email else None

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args,**kwargs):
        if not current_user(): flash('Please log in first.'); return redirect(url_for('login'))
        return f(*args,**kwargs)
    return decorated

def get_gig(gig_id): return Gig.query.get(gig_id)
def user_app(gid,em): return Application.query.filter_by(gig_id=gid,applicant_email=em).first()

@app.route('/')
def index(): return redirect(url_for('dashboard') if current_user() else url_for('login'))

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        email=request.form.get('email','').strip().lower(); password=request.form.get('password','')
        user=User.query.filter_by(email=email).first()
        if not user or user.password!=password: flash('Invalid email or password.'); return redirect(url_for('login'))
        session['user']=email; flash('🎉 Welcome back, '+user.username+'!'); return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/register',methods=['GET','POST'])
def register():
    if request.method=='POST':
        email=request.form.get('email','').strip().lower(); username=request.form.get('username','').strip()
        password=request.form.get('password',''); confirm=request.form.get('confirm_password',''); skills=request.form.get('skills','')
        if password!=confirm: flash('Passwords do not match.'); return redirect(url_for('register'))
        if len(password)<6: flash('Password must be at least 6 characters.'); return redirect(url_for('register'))
        if User.query.filter_by(email=email).first(): flash('Email already registered.'); return redirect(url_for('register'))
        db.session.add(User(email=email,username=username,password=password,skills_str=skills))
        db.session.commit(); session['user']=email; flash('🎉 Account created! Welcome, '+username+'!'); return redirect(url_for('dashboard'))
    return render_template('register.html')

@app.route('/logout')
def logout(): session.clear(); flash('Logged out.'); return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    user=current_user(); all_gigs=Gig.query.order_by(Gig.created_at.desc()).all()
    annotated=[]
    for g in all_gigs:
        ao=user_app(g.id,user.email)
        annotated.append({**g.to_dict(),'user_applied':ao is not None,'user_app_status':ao.status if ao else None,'is_poster':g.poster_email==user.email,'applicant_count':Application.query.filter_by(gig_id=g.id).count()})
    done=Gig.query.filter_by(status='completed').all()
    stats={'posted':Gig.query.filter_by(status='open').count(),'completed':len(done),'paid':f"{sum(g.bounty for g in done):,}"}
    return render_template('dashboard.html',gigs=annotated,current_user=user.to_dict(),stats=stats,STATUS_LABELS=STATUS_LABELS,STATUS_EMOJI=STATUS_EMOJI)

@app.route('/post-gig',methods=['POST'])
@login_required
def post_gig():
    user=current_user(); title=request.form.get('title','').strip(); desc=request.form.get('description','').strip()
    cat=request.form.get('category','Other'); bty=request.form.get('bounty',0); dl=request.form.get('deadline','')
    if not title or not desc or not bty or not dl: flash('⚠️ Please fill in all fields.'); return redirect(url_for('dashboard'))
    try: dl_fmt=datetime.strptime(dl,'%Y-%m-%d').strftime('%b %d')
    except: dl_fmt=dl
    gig=Gig(title=title,description=desc,category=cat,bounty=int(bty),deadline=dl_fmt,poster_email=user.email,status='open')
    db.session.add(gig); db.session.commit(); flash('📌 Gig posted!'); return redirect(url_for('dashboard'))

@app.route('/gig/<int:gig_id>')
@login_required
def gig_detail(gig_id):
    user=current_user(); gig=get_gig(gig_id)
    if not gig: flash('Gig not found.'); return redirect(url_for('dashboard'))
    gig_apps=Application.query.filter_by(gig_id=gig_id).all(); ao=user_app(gig_id,user.email)
    is_poster=gig.poster_email==user.email; poster_u=User.query.filter_by(email=gig.poster_email).first()
    return render_template('gig_detail.html',gig=gig.to_dict(),current_user=user.to_dict(),gig_apps=[a.to_dict() for a in gig_apps],app_obj=ao.to_dict() if ao else None,is_poster=is_poster,poster_qr=poster_u.upi_qr_url if poster_u else None,STATUS_LABELS=STATUS_LABELS,STATUS_EMOJI=STATUS_EMOJI,STATUS_ORDER=STATUS_ORDER)

@app.route('/apply/<int:gig_id>',methods=['GET','POST'])
@login_required
def apply(gig_id):
    user=current_user(); gig=get_gig(gig_id)
    if not gig: flash('Gig not found.'); return redirect(url_for('dashboard'))
    if gig.poster_email==user.email: flash('⚠️ Cannot apply to own gig.'); return redirect(url_for('gig_detail',gig_id=gig_id))
    if user_app(gig_id,user.email): flash('Already applied.'); return redirect(url_for('gig_detail',gig_id=gig_id))
    if request.method=='POST':
        db.session.add(Application(gig_id=gig_id,applicant_email=user.email,username=user.username,pitch=request.form.get('pitch','').strip(),portfolio=request.form.get('portfolio','').strip(),timeline=request.form.get('timeline','').strip(),status='applied'))
        if gig.status=='open': gig.status='applied'
        notify(gig.poster_email,f'📨 {user.username} applied to "{gig.title}"',link=f'/gig/{gig_id}/applicants',icon='📨')
        db.session.commit()
        return render_template('success.html',current_user=user.to_dict(),emoji='🚀',title='Application Sent!',message='Your application has been submitted. The gig poster will review it soon.',detail={'Gig':gig.title,'Bounty':f'₹{gig.bounty}','Deadline':gig.deadline,'Status':'🔵 Applied'})
    return render_template('apply.html',gig=gig.to_dict(),current_user=user.to_dict())

@app.route('/gig/<int:gig_id>/update-status',methods=['POST'])
@login_required
def update_gig_status(gig_id):
    user=current_user(); gig=get_gig(gig_id)
    if not gig or gig.poster_email!=user.email: flash('⚠️ Not authorised.'); return redirect(url_for('dashboard'))
    new_s=request.form.get('status','').strip()
    if new_s not in STATUS_ORDER: flash('⚠️ Invalid status.'); return redirect(url_for('gig_detail',gig_id=gig_id))
    old_s=gig.status; gig.status=new_s
    if new_s=='completed' and old_s!='completed':
        acc=Application.query.filter_by(gig_id=gig_id,status='accepted').first()
        if acc:
            w=User.query.filter_by(email=acc.applicant_email).first()
            if w: w.earned+=gig.bounty; w.completed+=1; notify(w.email,f'🎉 Gig "{gig.title}" complete! ₹{gig.bounty} earned.',link=f'/gig/{gig_id}',icon='🎉')
    for a in Application.query.filter_by(gig_id=gig_id).all():
        if a.applicant_email!=user.email: notify(a.applicant_email,f'📊 "{gig.title}" → {STATUS_LABELS[new_s]}',link=f'/gig/{gig_id}',icon='📊')
    db.session.commit(); flash(f'✅ Status → {STATUS_LABELS[new_s]}!'); return redirect(url_for('gig_detail',gig_id=gig_id))

@app.route('/gig/<int:gig_id>/accept/<int:app_id>',methods=['POST'])
@login_required
def accept_applicant(gig_id,app_id):
    user=current_user(); gig=get_gig(gig_id)
    if not gig or gig.poster_email!=user.email: flash('⚠️ Not authorised.'); return redirect(url_for('dashboard'))
    for a in Application.query.filter_by(gig_id=gig_id).all():
        if a.id==app_id: a.status='accepted'; notify(a.applicant_email,f'🎉 Accepted for "{gig.title}"!',link=f'/gig/{gig_id}',icon='🎉')
        else: a.status='rejected'; notify(a.applicant_email,f'😔 Not selected for "{gig.title}".',link=f'/gig/{gig_id}',icon='😔')
    gig.status='in_progress'; db.session.commit(); flash('🎉 Applicant accepted!'); return redirect(url_for('gig_detail',gig_id=gig_id))

@app.route('/gig/<int:gig_id>/applicants')
@login_required
def applicants(gig_id):
    user=current_user(); gig=get_gig(gig_id)
    if not gig: flash('Gig not found.'); return redirect(url_for('dashboard'))
    if gig.poster_email!=user.email: flash('⚠️ Poster only.'); return redirect(url_for('gig_detail',gig_id=gig_id))
    gig_apps=Application.query.filter_by(gig_id=gig_id).order_by(Application.applied_at.desc()).all()
    return render_template('applicants.html',gig=gig.to_dict(),current_user=user.to_dict(),gig_apps=[a.to_dict() for a in gig_apps],STATUS_LABELS=STATUS_LABELS,STATUS_EMOJI=STATUS_EMOJI)

@app.route('/my-gigs')
@login_required
def my_gigs():
    user=current_user(); gigs=Gig.query.filter_by(poster_email=user.email).order_by(Gig.created_at.desc()).all()
    enriched=[{**g.to_dict(),'applicant_count':Application.query.filter_by(gig_id=g.id).count()} for g in gigs]
    return render_template('my_gigs.html',gigs=enriched,current_user=user.to_dict(),STATUS_LABELS=STATUS_LABELS,STATUS_EMOJI=STATUS_EMOJI)

@app.route('/my-applications')
@login_required
def my_applications():
    user=current_user(); raw_apps=Application.query.filter_by(applicant_email=user.email).order_by(Application.applied_at.desc()).all()
    enriched=[]
    for a in raw_apps:
        g=get_gig(a.gig_id); d=a.to_dict()
        d.update({'gig_title':g.title if g else 'Deleted','gig_deadline':g.deadline if g else '—','gig_bounty':g.bounty if g else 0,'gig_status':g.status if g else '—','gig_category':g.category if g else '—'})
        enriched.append(d)
    return render_template('my_applications.html',apps=enriched,current_user=user.to_dict(),STATUS_LABELS=STATUS_LABELS,STATUS_EMOJI=STATUS_EMOJI)

@app.route('/notifications')
@login_required
def notifications():
    user=current_user(); notifs=Notification.query.filter_by(user_email=user.email).order_by(Notification.created_at.desc()).all()
    for n in notifs: n.is_read=True
    db.session.commit()
    return render_template('notifications.html',notifications=[n.to_dict() for n in notifs],current_user=user.to_dict())

@app.route('/notifications/clear',methods=['POST'])
@login_required
def clear_notifications():
    user=current_user(); Notification.query.filter_by(user_email=user.email).delete(); db.session.commit()
    flash('🗑️ All notifications cleared.'); return redirect(url_for('notifications'))

@app.route('/leaderboard')
@login_required
def leaderboard():
    from sqlalchemy import func
    user=current_user()
    top_earners=User.query.filter(User.earned>0).order_by(User.earned.desc()).limit(10).all()
    top_workers=User.query.filter(User.completed>0).order_by(User.completed.desc()).limit(10).all()
    top_posters_raw=db.session.query(Gig.poster_email,func.count(Gig.id).label('gig_count'),func.sum(Gig.bounty).label('total_bounty')).group_by(Gig.poster_email).order_by(func.count(Gig.id).desc()).limit(10).all()
    top_posters=[{'username':User.query.filter_by(email=r.poster_email).first().username if User.query.filter_by(email=r.poster_email).first() else r.poster_email,'gig_count':r.gig_count,'total_bounty':r.total_bounty or 0} for r in top_posters_raw]
    return render_template('leaderboard.html',current_user=user.to_dict(),top_earners=top_earners,top_workers=top_workers,top_posters=top_posters)

@app.route('/help')
def help_faq():
    user=current_user()
    return render_template('help.html',current_user=user.to_dict() if user else None)

@app.route('/profile',methods=['GET','POST'])
@login_required
def profile():
    user=current_user()
    if request.method=='POST':
        user.username=request.form.get('username',user.username).strip(); user.bio=request.form.get('bio','').strip()
        user.skills_str=request.form.get('skills',''); user.upi_id=request.form.get('upi_id','').strip()
        db.session.commit(); flash('💾 Profile updated!'); return redirect(url_for('profile'))
    my_gigs_list=Gig.query.filter_by(poster_email=user.email).order_by(Gig.created_at.desc()).all()
    raw_apps=Application.query.filter_by(applicant_email=user.email).order_by(Application.applied_at.desc()).all()
    my_apps=[]
    for a in raw_apps:
        d=a.to_dict(); g=get_gig(a.gig_id)
        d.update({'gig_title':g.title if g else 'Deleted','gig_deadline':g.deadline if g else '—','gig_bounty':g.bounty if g else 0,'gig_status':g.status if g else '—'})
        my_apps.append(d)
    return render_template('profile.html',current_user=user.to_dict(),user_stats={'posted':user.posted_count,'applied':user.applied_count,'completed':user.completed,'earned':user.earned},my_gigs=[g.to_dict() for g in my_gigs_list],my_apps=my_apps,STATUS_LABELS=STATUS_LABELS,STATUS_EMOJI=STATUS_EMOJI)

@app.route('/about')
def about():
    user=current_user()
    return render_template('about.html',current_user=user.to_dict() if user else None)

if __name__=='__main__':
    app.run(debug=True)
