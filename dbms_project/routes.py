from flask import render_template, request, redirect, url_for, flash, send_file, session
import sqlite3
from werkzeug.utils import secure_filename
import os, shutil, zipfile, datetime

from werkzeug.security import generate_password_hash, check_password_hash

from app import app
from forms import *

DATABASE = 'hotel_room_allotment.db'

def check_login():
    if not 'c_id' in session:
        return redirect(url_for('.home'))

@app.route('/logout')
def logout():
    check_login()
    session.clear()
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
                        session['c_id'] = user['c_id']
                        session['name'] = user['name']
                        session['email'] = user['email']
                        return redirect(url_for('.home'))
                    else:
                        flash("Invalid username or password")
                else:
                    flash("Invalid username or password")

        elif 'register' in request.form:
            if registerform.validate_on_submit():
                if registerform.password.data==registerform.repassword.data:
                    #try:
                    hashed_password = generate_password_hash(registerform.password.data, method='sha256')
                    with sqlite3.connect(DATABASE) as con:
                        cur = con.cursor()
                        cur.execute('INSERT INTO CUSTOMER VALUES ("%s","%s","%s","%s","%s","%s");'%
                        (registerform.userid.data, hashed_password, registerform.name.data,
                        registerform.phone.data, registerform.email.data, registerform.aadhar.data,) )
                        con.commit()
                    flash("User created successfully","success")
                    return redirect(url_for('.home'))
                #except:
                #    con.rollback()
                #    flash("Username already exists.","warning")
                else:
                    flash("Re-entered password not matched the password","warning")

    return render_template('login.html', signinform=signinform, registerform = registerform)
