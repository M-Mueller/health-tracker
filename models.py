from main import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    locale = db.Column(db.String(80), nullable=False)

    blood_pressures = db.relationship('BloodPressure', backref='user', lazy=True)

    is_authenticated = True
    is_active = True
    is_anonymous = False

    def get_id(self):
        return self.id

    def __repr__(self):
        return f'<User {self.username}>'


class BloodPressure(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    systolic = db.Column(db.Integer, nullable=False)
    diastolic = db.Column(db.Integer, nullable=False)
    pulse = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f'<BloodPressure {self.user.username} {self.date.isoformat()} {self.systolic}/{self.diastolic} {self.pulse}>'
