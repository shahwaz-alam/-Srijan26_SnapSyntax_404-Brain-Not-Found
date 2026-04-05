from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# ═══════════════════════════════════════════════════
#  USER
# ═══════════════════════════════════════════════════
class User(db.Model):
    __tablename__ = 'users'

    id         = db.Column(db.Integer,     primary_key=True)
    email      = db.Column(db.String(120), unique=True, nullable=False)
    username   = db.Column(db.String(80),  nullable=False)
    password   = db.Column(db.String(200), nullable=False)
    bio        = db.Column(db.Text,        default='')
    skills_str = db.Column(db.String(300), default='')
    upi_id     = db.Column(db.String(100), default='')
    earned     = db.Column(db.Integer,     default=0)
    completed  = db.Column(db.Integer,     default=0)
    created_at = db.Column(db.DateTime,    default=datetime.utcnow)

    posted_gigs   = db.relationship('Gig', backref='poster_user', lazy=True,
                                    foreign_keys='Gig.poster_email')
    applications  = db.relationship('Application', backref='applicant_user', lazy=True,
                                    foreign_keys='Application.applicant_email')
    notifications = db.relationship('Notification', backref='recipient', lazy=True,
                                    foreign_keys='Notification.user_email',
                                    cascade='all, delete-orphan')

    @property
    def skills(self):
        return [s.strip() for s in self.skills_str.split(',') if s.strip()]

    @property
    def posted_count(self):
        return Gig.query.filter_by(poster_email=self.email).count()

    @property
    def applied_count(self):
        return Application.query.filter_by(applicant_email=self.email).count()

    @property
    def unread_count(self):
        return Notification.query.filter_by(user_email=self.email, is_read=False).count()

    @property
    def upi_qr_url(self):
        if not self.upi_id:
            return None
        import urllib.parse
        upi_link = (f"upi://pay?pa={urllib.parse.quote(self.upi_id)}"
                    f"&pn={urllib.parse.quote(self.username)}&cu=INR")
        return ("https://api.qrserver.com/v1/create-qr-code/"
                f"?size=200x200&data={urllib.parse.quote(upi_link, safe='')}")

    def to_dict(self):
        return {
            'id': self.id, 'email': self.email, 'username': self.username,
            'bio': self.bio, 'skills': self.skills, 'skills_str': self.skills_str,
            'upi_id': self.upi_id, 'upi_qr_url': self.upi_qr_url,
            'earned': self.earned, 'completed': self.completed,
            'posted': self.posted_count, 'applied': self.applied_count,
            'unread_count': self.unread_count,
        }

    def __repr__(self): return f'<User {self.email}>'


# ═══════════════════════════════════════════════════
#  GIG
# ═══════════════════════════════════════════════════
class Gig(db.Model):
    __tablename__ = 'gigs'

    id           = db.Column(db.Integer,     primary_key=True)
    title        = db.Column(db.String(200), nullable=False)
    description  = db.Column(db.Text,        nullable=False)
    category     = db.Column(db.String(50),  nullable=False, default='Other')
    bounty       = db.Column(db.Integer,     nullable=False)
    deadline     = db.Column(db.String(30),  nullable=False)
    poster_email = db.Column(db.String(120), db.ForeignKey('users.email'), nullable=False)
    status       = db.Column(db.String(20),  nullable=False, default='open')
    created_at   = db.Column(db.DateTime,    default=datetime.utcnow)

    applications = db.relationship('Application', backref='gig', lazy=True,
                                   cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id, 'title': self.title, 'description': self.description,
            'category': self.category, 'bounty': self.bounty,
            'deadline': self.deadline, 'poster': self.poster_email, 'status': self.status,
        }

    def __repr__(self): return f'<Gig {self.id}: {self.title}>'


# ═══════════════════════════════════════════════════
#  APPLICATION
# ═══════════════════════════════════════════════════
class Application(db.Model):
    __tablename__ = 'applications'

    id              = db.Column(db.Integer,     primary_key=True)
    gig_id          = db.Column(db.Integer,     db.ForeignKey('gigs.id'),     nullable=False)
    applicant_email = db.Column(db.String(120), db.ForeignKey('users.email'), nullable=False)
    username        = db.Column(db.String(80),  nullable=False)
    pitch           = db.Column(db.Text,         default='')
    portfolio       = db.Column(db.String(300),  default='')
    timeline        = db.Column(db.String(200),  default='')
    status          = db.Column(db.String(20),   default='applied')
    applied_at      = db.Column(db.DateTime,     default=datetime.utcnow)

    @property
    def applied_at_fmt(self):
        return self.applied_at.strftime('%b %d, %H:%M') if self.applied_at else ''

    def to_dict(self):
        return {
            'id': self.id, 'gig_id': self.gig_id, 'applicant': self.applicant_email,
            'username': self.username, 'pitch': self.pitch,
            'portfolio': self.portfolio, 'timeline': self.timeline,
            'status': self.status, 'applied_at': self.applied_at_fmt,
        }

    def __repr__(self): return f'<Application gig={self.gig_id} by={self.applicant_email}>'


# ═══════════════════════════════════════════════════
#  NOTIFICATION
# ═══════════════════════════════════════════════════
class Notification(db.Model):
    __tablename__ = 'notifications'

    id         = db.Column(db.Integer,     primary_key=True)
    user_email = db.Column(db.String(120), db.ForeignKey('users.email'), nullable=False)
    message    = db.Column(db.String(300), nullable=False)
    link       = db.Column(db.String(200), default='')
    icon       = db.Column(db.String(10),  default='🔔')
    is_read    = db.Column(db.Boolean,     default=False)
    created_at = db.Column(db.DateTime,    default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id, 'message': self.message, 'link': self.link,
            'icon': self.icon, 'is_read': self.is_read,
            'created_at': self.created_at.strftime('%b %d, %H:%M'),
        }

    def __repr__(self): return f'<Notification {self.id} → {self.user_email}>'
