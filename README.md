# health-tracker
Website to track health related values (currently only blood pressure).

## Install

1. Copy `config.py.skel` to `config.py` and set all configuration variables.
2. Create the database and add users
```py
from main import db
from models import User
db.create_all()

user = User(username='thename', password='thepassword')
db.session.add(user)
db.session.commit()
```
3. Launch WSGI server e.g. with gunicorn
```
gunicorn --workers 4 --bind :5000 main:app
```

