import datetime
import sqlite3
from math import ceil
from urllib.parse import urlparse, urljoin
from io import BytesIO
from flask import Flask, render_template, request, g, send_file, redirect, url_for, make_response, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = b'E\xbdv\xf0\xbd7\x0b\xf9\xce.\x94\xcerx5\xcd'
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


from models import User, BloodPressure


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


@app.route('/')
def index():
    # there is nothing at the index page yet
    return redirect(url_for('blood_pressure'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            username = str(request.form['username'])
            password = str(request.form['password'])

            user = User.query.filter_by(username=username).first()
            if not user:
                raise ValueError('Unknown user', username)
            if not user.password == password:
                raise ValueError('Invalid password', password)

            login_user(user)

            next = request.args.get('next')
            if not is_safe_url(next):
                return abort(400)

            return redirect(next or url_for('index'))
        except (KeyError, ValueError) as e:
            app.logger.error('Invalid login: %s', e)
            return render_template('login.html', message=f'Invalid username or password')
    else:
        return render_template('login.html')


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/blood_pressure', methods=['GET', 'POST'], defaults={'key': None})
@app.route('/blood_pressure/<int:key>', methods=['DELETE'])
@login_required
def blood_pressure(key):
    ROWS_PER_PAGE = 10;

    total_pages = ceil(BloodPressure.query.count() / ROWS_PER_PAGE)

    active_page = 1
    if 'page' in request.args:
        try:
            active_page = int(request.args['page'])
        except:
            pass
    active_page = max(1, min(active_page, total_pages))

    if request.method == 'POST':
        try:
            date = datetime.date.fromisoformat(request.form['date'])
            hour = int(request.form['hour'])
            minute = int(request.form['minute'])
            systolic = int(request.form['systolic'])
            diastolic = int(request.form['diastolic'])

            measurement = BloodPressure(
                user=current_user,
                date=datetime.datetime(date.year, date.month, date.day, hour, minute),
                systolic=systolic,
                diastolic=diastolic,
            )
            db.session.add(measurement)
            db.session.commit()

            app.logger.info('Added new BloodPressure %s', measurement)

            return redirect(url_for('blood_pressure'))
        except ValueError as e:
            app.logger.error('Invalid form data: %s', e)
            return redirect(url_for(
                'blood_pressure',
                page=active_page,
                message="""Something went wrong when adding the new measurement. Please make sure all fields are set to valid values and try again."""
            ))
    elif request.method == 'DELETE':
        measurement = BloodPressure.query.get(key)
        if measurement:
            if measurement.user != current_user:
                return make_response("You are not allowed to delete this entry", 403)

            app.logger.info('Deleting BloodPressure %s', measurement)
            db.session.delete(measurement)
            db.session.commit()
            return make_response(jsonify({}), 204)
        else:
            app.logger.info('Could not find BloodPressure with id %s for deletion', key)
            return make_response("Entry not found", 404)
    else:
        message = ''
        if 'message' in request.args:
            try:
                message = str(request.args['message'])
            except:
                pass

        rows = BloodPressure.query.with_parent(current_user)[0:ROWS_PER_PAGE]
        return render_template(
            'blood_pressure.html',
            header=('Date', 'SYS', 'DIA'),
            rows=[(row.id, row.date.strftime('%A, %d. %B %Y'), row.systolic, row.diastolic) for row in rows],
            total_pages=total_pages,
            active_page=active_page,
            message=message,
        )



@app.route('/blood_pressure/csv')
@login_required
def blood_pressure_csv():
    rows = [
        (row.date.isoformat(), row.systolic, row.diastolic)
        for row in BloodPressure.query.filter_by(user=current_user)
    ]
    return send_csv('blood_pressure', ['date', 'systolic', 'diastolic'], rows)


def send_csv(name, headers, rows):
    csv = BytesIO()
    for row in [headers] + rows:
        line = ''
        for col in row:
            line = line + str(col) + ';'
        line = line + '\n'
        csv.write(line.encode('utf-8'))
    csv.seek(0)
    return send_file(csv, mimetype='text/csv', as_attachment=True, attachment_filename=name + '.csv')


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
