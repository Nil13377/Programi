from flask import Flask, render_template, request, flash, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import bcrypt
from io import BytesIO
import base64
                

app = Flask(__name__)
app.secret_key = "e5b0c3f8a9d4e7f1c2b3a8d9f0e1d4c5" 
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///scooters.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    profile_str = db.Column(db.Text())
    email = db.Column(db.String(100), nullable=False, unique=True)
    name = db.Column(db.String(100), nullable=False)
    surname = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(128), nullable=False)

    def set_password(self, raw_password):
        self.password = bcrypt.hashpw(raw_password.encode("utf-8"), bcrypt.gensalt())

    def check_password(self, raw_password):
        return bcrypt.checkpw(raw_password.encode("utf-8"), self.password)

class Scooter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    vrsta = db.Column(db.Integer, nullable=False)
    prostornina = db.Column(db.Integer, nullable=False)
    znamka = db.Column(db.String(100), nullable=False)
    model = db.Column(db.String(100), nullable=False)
    registracija = db.Column(db.String(100), nullable=False)
    cena = db.Column(db.Integer, nullable=False)
    prevozeni = db.Column(db.Integer, nullable=False)
    opis = db.Column(db.Text)

    user = db.relationship("User", backref=db.backref("scooters", lazy=True))

class ScooterImg(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    scooter_id = db.Column(db.Integer, db.ForeignKey("scooter.id"), nullable=False)
    img_str = db.Column(db.Text())

    scooter = db.relationship("Scooter", backref=db.backref("images"), lazy=True)

with app.app_context():
    db.create_all()

@app.route("/")
def home():
    user_id = session.get("user_id")
    if user_id:
        user = User.query.get(user_id)
        if user:
            profile_picture = f"data:image/png;base64,{user.profile_str}" if user.profile_str else None
            return render_template("home.html", profile_picture=profile_picture)
        else:
            session.clear()
            flash("Vaša seja je potekla ali uporabnik ne obstaja. Prijavite se znova.", "error")
            return redirect(url_for("login"))
    else:
        return render_template("home.html", profile_picture=None)

@app.route("/register", methods=["GET", "POST"])
def register():
    
    if request.method == "POST":
        email = request.form.get("email")
        name = request.form.get("name")
        surname = request.form.get("surname")
        password = request.form.get("password")

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("e-poštni naslov je v uporabi. Uporabite drug naslov ali pa se prijavite.", "error")
            return redirect(url_for("register"))

        new_user = User(email=email, name=name, surname=surname)
        new_user.set_password(password)

        try:
            db.session.add(new_user)
            db.session.commit()
            flash("Registracija uspešna! Sedaj se lahko prijavite.", "success")
            return redirect(url_for("login"))
        except Exception as e:
            db.session.rollback()
            flash("prišlo je do napake pri registraciji. Poskusite znova.", "error")
            return redirect(url_for("register"))
        
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            session["user_id"] = user.id
            session["user_email"] = user.email
            session["user_name"] = user.name
            session["user_surname"] = user.surname
            flash("Prijava uspšna! Dobrodošli", "success")
            print(session)
            return redirect(url_for("profile"))
        else:
            flash("Neveljaven e-poštni naslov ali geslo. Poskusite znova.", "error")
            return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/profile", methods=["GET", "POST"])
def profile():
    if not session.get("user_email"):
        flash("Za dostop do profila se morate prijaviti.", "error")
        return redirect(url_for("login"))
    
    user = User.query.get(session["user_id"])
    
    if request.method == "POST":
        img = request.files.get("profile_picture")
        if img:
            buffered = BytesIO()
            img.save(buffered)
            img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
            user.profile_str = img_str
            db.session.commit()
            flash("Profilna slika je bila uspešno posodobljena.", "success")
        else:
            flash("Nalaganje slike ni uspelo. Poskusite znova.", "error")

    user_ads = Scooter.query.filter_by(user_id=user.id).all()

    profile_picture = f"data:image/png;base64,{user.profile_str}" if user.profile_str else "static/default-profile.png"
    return render_template("profile.html", profile_picture=profile_picture, user_ads=user_ads)

@app.route("/logout")
def logout():
    session.clear()
    flash("Uspešno ste se odjavili.", "success")
    return redirect(url_for("home"))

@app.route("/listing", methods=["GET", "POST"])
def listing():
    if session["user_id"]:
        user = User.query.get(session["user_id"])
        if request.method == "POST":
            vrsta = request.form.get("vrsta")
            prostornina = request.form.get("prostornina")
            znamka = request.form.get("znamka")
            model = request.form.get("model")
            registracija = request.form.get("registracija")
            opis = request.form.get("opis")
            cena = request.form.get("cena")
            prevozeni = request.form.get("prevozeni")
            images = request.files.getlist("images")

            new_scooter = Scooter(
                user_id = user.id,
                vrsta = vrsta,
                prostornina = prostornina,
                znamka = znamka,
                model = model,
                registracija = registracija,
                opis = opis,
                cena = cena,
                prevozeni = prevozeni
            )
            
            db.session.add(new_scooter)
            db.session.commit()

            for img in images:
                if img:
                    buffered = BytesIO()
                    img.save(buffered)
                    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
                    scooter_image = ScooterImg(
                        scooter_id = new_scooter.id,
                        img_str = img_str
                    )
                    db.session.add(scooter_image)
            db.session.commit()
            flash("Oglas je bil uspešno dodan.", "success")
            return redirect(url_for("profile"))
    else:
        flash("Za objavo oglasa se morate prijaviti.", "error")
        redirect(url_for("login"))
    profile_picture = f"data:image/png;base64,{user.profile_str}" if user.profile_str else "static/default-profile.png"
    return render_template("listing.html", profile_picture=profile_picture)
@app.post("/results")
def results():
    return render_template("results.html") 

if __name__ == "__main__":
    app.run(debug=True)
