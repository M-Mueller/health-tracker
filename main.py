import datetime
import sqlite3
from math import ceil
from io import BytesIO
from flask import Flask, render_template, request, g, send_file, redirect, url_for
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


from models import User, BloodPressure


def format_date(date):
    return datetime.date.fromisoformat(date).strftime('%A, %d. %B %Y')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/blood_pressure')
def blood_pressure():
    ROWS_PER_PAGE = 10;

    total_pages = ceil(BloodPressure.query.count() / ROWS_PER_PAGE)

    active_page = 1
    if 'page' in request.args:
        try:
            active_page = int(request.args['page'])
        except:
            pass
    active_page = max(1, min(active_page, total_pages))

    user = User.query.first_or_404()
    rows = BloodPressure.query.with_parent(user)[0:ROWS_PER_PAGE]
    return render_template(
        'blood_pressure.html',
        header=('Date', 'SYS', 'DIA'),
        rows=[(row.id, row.date.strftime('%A, %d. %B %Y'), row.systolic, row.diastolic) for row in rows],
        total_pages=total_pages,
        active_page=active_page,
    )


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


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
