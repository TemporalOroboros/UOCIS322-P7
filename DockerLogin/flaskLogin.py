"""
Flask-Login and Flask-WTF example
"""
from urllib.parse import urlparse, urljoin
from flask import Flask, request, render_template, redirect, url_for, flash, abort
from flask_login import (LoginManager, current_user, login_required,
                         login_user, logout_user, UserMixin,
                         confirm_login, fresh_login_required)
from flask_wtf import FlaskForm as Form
from wtforms import BooleanField, StringField, validators


class LoginForm(Form):
    username = StringField('Username', [
        validators.Length(min=2, max=25,
                          message=u"Huh, little too short for a username."),
        validators.InputRequired(u"Forget something?")])
    remember = BooleanField('Remember me')


def is_safe_url(target):
    """
    :source: https://github.com/fengsp/flask-snippets/blob/master/security/redirect_back.py
    """
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


class User(UserMixin):
    def __init__(self, id, name, fullname):
        self.id = id
        self.name = name
        self.fullname = fullname
        self.dob = "Unknown"
        self.ssn = "Unknown"

    def set_dob(self, dob):
        self.dob = dob
        return self

    def set_ssn(self, ssn):
        self.ssn = ssn
        return self


USERS = {
    1: User(u"1", u"alex", "Alex").set_dob("05-02-1990").set_ssn("235-21-0042"),
    2: User(u"2", u"bob", "Bob").set_dob("10-12-1986").set_ssn("561-84-1235"),
    3: User(u"3", u"jim", "Jim").set_dob("12-01-1965").set_ssn("124-52-4321"),
}

USER_NAMES = dict((u.name, u) for u in USERS.values())

app = Flask(__name__)
app.secret_key = "and the cats in the cradle and the silver spoon"

app.config.from_object(__name__)

login_manager = LoginManager()

login_manager.session_protection = "strong"

login_manager.login_view = "login"
login_manager.login_message = u"Please log in to access this page."

login_manager.refresh_view = "login"
login_manager.needs_refresh_message = (
    u"To protect your account, please reauthenticate to access this page."
)
login_manager.needs_refresh_message_category = "info"


@login_manager.user_loader
def load_user(user_id):
    return USERS[int(user_id)]


login_manager.init_app(app)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/secret")
@login_required
def secret():
    flash("Your date of birth is: {current_user.dob}".format(current_user.dob))
    flash("Your SSN is: {current_user.ssn}".format(current_user.ssn))
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit() and request.method == "POST" and "username" in request.form:
        username = request.form["username"]
        if username in USER_NAMES:
            remember = request.form.get("remember", "false") == "true"
            if login_user(USER_NAMES[username], remember=remember):
                flash("Logged in!")
                flash("I'll remember you") if remember else None
                next = request.args.get("next")
                if not is_safe_url(next):
                    abort(400)
                return redirect(next or url_for('index'))
            else:
                flash("Sorry, but you could not log in.")
        else:
            flash(u"Invalid username.")
    return render_template("login.html", form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out.")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
