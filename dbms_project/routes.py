from flask import render_template, request, redirect, url_for, flash, send_file, session
import sqlite3
from werkzeug.utils import secure_filename
import os, shutil, zipfile, datetime

from werkzeug.security import generate_password_hash, check_password_hash

from app import app
from forms import *

DATABASE = 'hotel_room_allotment.db'

def check_login():
    if session.get('logged_in') != True:
        flash('Please Login')
        return False
    else:
        return True

@app.route('/logout')
def logout():
    if not check_login():
        return redirect(url_for('.home'))
    session.pop('logged_in', None)
    session.pop('c_id', None)
    session.pop('name', None)
    session.pop('email', None)
    return redirect(url_for('.home'))

@app.route('/')
@app.route('/home', methods=['GET', 'POST'])
def home():
    signinform = SigninForm()
    registerform = RegisterForm()
    if request.method == 'POST':
        if 'signin' in request.form:
            if signinform.validate_on_submit():
                con = sqlite3.connect(DATABASE)
                con.row_factory = sqlite3.Row
                cur = con.cursor()
                cur.execute('SELECT c_id, name, email, password FROM CUSTOMER WHERE c_id="%s";'%(signinform.userid.data))
                user = cur.fetchone()
                con.close()
                if user:
                    if check_password_hash(user['password'], signinform.password.data):
                        session['logged_in'] = True
                        session['c_id'] = user['c_id']
                        session['name'] = user['name']
                        session['email'] = user['email']
                        return redirect(url_for('.dashboard'))
                    else:
                        flash("Invalid username or password")
                else:
                    flash("Invalid username or password")

        elif 'register' in request.form:
            if registerform.validate_on_submit():
                if registerform.password.data==registerform.repassword.data:
                    try:
                        hashed_password = generate_password_hash(registerform.password.data, method='sha256')
                        with sqlite3.connect(DATABASE) as con:
                            cur = con.cursor()
                            cur.execute('INSERT INTO CUSTOMER VALUES ("%s","%s","%s","%s","%s","%s");'%
                            (registerform.userid.data, hashed_password, registerform.name.data,
                            registerform.phone.data, registerform.email.data, registerform.aadhar.data,) )
                            con.commit()
                        flash("User created successfully","success")
                        return redirect(url_for('.home'))
                    except:
                        con.rollback()
                        flash("Username already exists.","warning")
                else:
                    flash("Re-entered password not matched the password","warning")

    return render_template('login.html', signinform=signinform, registerform = registerform)

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if not check_login():
        return redirect(url_for('.home'))
    con = sqlite3.connect(DATABASE)
    cur = con.cursor()
    cur.execute('SELECT DISTINCT locations FROM HOTEL;')
    locations = cur.fetchall()
    con.close()
    if request.method == "POST":
        if 'search' in request.form:
            return redirect(url_for('.hotel', location = request.form['location']))
    return render_template('dashboard.html', locations = locations)

@app.route('/hotel/<location>')
def hotel(location):
    if not check_login():
        return redirect(url_for('.home'))

    return render_template('hotel.html')
