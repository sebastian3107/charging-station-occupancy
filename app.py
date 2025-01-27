from flask import Flask, render_template, request, make_response, redirect, abort
from datetime import datetime, timedelta
import pytz
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///charging_stations.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class ChargingStation(db.Model):
    station_id = db.Column(db.String(5), primary_key=True)
    status = db.Column(db.String(10), default='Free')
    occupied_by = db.Column(db.String(50))
    license_plate = db.Column(db.String(20))
    timestamp = db.Column(db.DateTime)

# Create database tables on first run
with app.app_context():
    db.create_all()
    
    # Populate initial stations if empty
    if not db.session.query(ChargingStation).first():
        stations = [
            '1.1', '1.2', '2.1', '2.2', '3.1', '3.2',
            '4.1', '4.2', '5.1', '5.2', '6.1', '6.2', 
            '7.1', '7.2'
        ]
        for station in stations:
            db.session.add(ChargingStation(station_id=station))
        db.session.commit()

def get_german_time():
    return datetime.now(pytz.timezone('Europe/Berlin'))

@app.route('/', methods=['GET', 'POST'])
@app.route('/station/<station_id>', methods=['GET', 'POST'])
def index(station_id=None):
    nickname = request.cookies.get('nickname', '')
    license_plate = request.cookies.get('license_plate', '')
    
    if station_id and not db.session.get(ChargingStation, station_id):
        abort(404)
    
    if request.method == 'POST':
        station_id = request.form['station_id']
        action = request.form['action']
        nickname = request.form.get('nickname', nickname)
        license_plate = request.form.get('license_plate', license_plate)
        
        station = db.session.get(ChargingStation, station_id)
        if not station:
            print("No station returned for ID:", station_id)
            return redirect('/')
        
        if action == 'occupy':
            station.status = 'Occupied'
            station.occupied_by = nickname
            station.license_plate = license_plate or None
            station.timestamp = get_german_time()
        elif action == 'free':
            station.status = 'Free'
            station.occupied_by = None
            station.license_plate = None
            station.timestamp = get_german_time()
            
        db.session.commit()
        
        resp = make_response(redirect(f'/station/{station_id}?active_tab=stations'))
        resp.set_cookie('nickname', nickname, max_age=timedelta(days=365))
        resp.set_cookie('license_plate', license_plate or '', max_age=timedelta(days=365))
        return resp
    
    charging_stations = db.session.query(ChargingStation).all()
    return render_template('index.html', 
                         charging_stations=charging_stations,
                         nickname=nickname,
                         license_plate=license_plate,
                         station_id=station_id)

@app.route('/update-user-info', methods=['POST'])
def update_user_info():
    nickname = request.form['nickname']
    license_plate = request.form['license_plate']
    resp = make_response(redirect('/'))
    resp.set_cookie('nickname', nickname, max_age=timedelta(days=365))
    resp.set_cookie('license_plate', license_plate, max_age=timedelta(days=365))
    return resp

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(debug=True)