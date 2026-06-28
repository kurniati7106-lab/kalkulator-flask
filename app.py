from flask import Flask, render_template, request, redirect, url_for, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'rahasia-banget-jangan-kasih-orang' 
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///kalkulator.db'
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' 

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    histories = db.relationship('History', backref='owner', lazy=True)

class History(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tanggal = db.Column(db.DateTime, default=datetime.utcnow)
    perhitungan = db.Column(db.String(100), nullable=False) # contoh: "A=4, B=3 | IPK=3.5"
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('Username sudah dipakai')
            return redirect(url_for('register'))
        hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')
        db.session.add(User(username=username, password=hashed_pw))
        db.session.commit()
        flash('Registrasi berhasil! Silakan login.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated: return redirect(url_for('dashboard'))
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Login gagal. Cek username & password.')
    return render_template('index.html')

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    user_history = History.query.filter_by(user_id=current_user.id).order_by(History.tanggal.desc()).limit(5).all()
    return render_template('dashboard.html', hasil=None, history=user_history)

@app.route('/hitung', methods=['POST'])
@login_required
def hitung():
    try:
        # LOGIKA IPK: Rata-rata 2 nilai contoh. Ganti sesuai rumusmu
        nilai1 = float(request.form['nilai1']) 
        nilai2 = float(request.form['nilai2'])
        ipk = (nilai1 + nilai2) / 2 
        
        hasil_str = f"{ipk:.2f}"
        # Simpan ke DB
        perhitungan_txt = f"Nilai: {nilai1}, {nilai2} | IPK: {hasil_str}"
        new_hist = History(perhitungan=perhitungan_txt, owner=current_user)
        db.session.add(new_hist)
        db.session.commit()

    except Exception as e:
        hasil_str = 'Input harus angka'
        
    user_history = History.query.filter_by(user_id=current_user.id).order_by(History.tanggal.desc()).limit(5).all()
    return render_template('dashboard.html', hasil=hasil_str, history=user_history)

with app.app_context():
    db.create_all() 

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
