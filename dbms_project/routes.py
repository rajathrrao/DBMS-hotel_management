from flask import render_template, request, redirect, url_for, flash, send_file, session
import sqlite3
from werkzeug.utils import secure_filename
import os, shutil
from datetime import date, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

from app import app
from forms import *

DATABASE = 'hotel_room_allotment.db'
interval_time = ' 10:00:00'

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
    session.pop('filter', None)
    session.pop('rooms', None)
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
    con = sqlite3.connect(DATABASE)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute('''SELECT hotel_id, hotel_name, locations, photo, AVG(star) AS avgstar
    FROM HOTEL NATURAL JOIN REVIEW WHERE locations="%s" GROUP BY hotel_id;'''%(location))
    hotels = cur.fetchall()
    con.close()
    return render_template('hotel.html', hotels = hotels)

@app.route('/rooms/<hotel_id>', methods=['GET', 'POST'])
def room(hotel_id):
    if not check_login():
        return redirect(url_for('.home'))
    filterform = FilterForm()
    con = sqlite3.connect(DATABASE)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute('''SELECT DISTINCT type_id, no_beds, wifi, tv, ac FROM TYPE NATURAL JOIN ROOM WHERE hotel_id=%s'''
    %(hotel_id) )
    types = cur.fetchall()
    con.close()
    if request.method == 'GET':
        checkin = str(date.today()+timedelta(days=1))+interval_time
        checkout = str(date.today()+timedelta(days=2))+interval_time
        filterform.checkin.data = str(date.today()+timedelta(days=1))
        filterform.checkout.data = str(date.today()+timedelta(days=2))
        con = sqlite3.connect(DATABASE)
        cur = con.cursor()
        cur.execute('''SELECT room_id,room_no,price,no_beds,wifi,tv,ac FROM ROOM NATURAL JOIN TYPE
        WHERE hotel_id=%s AND room_id NOT IN
        (SELECT room_id FROM RESERVATION
        WHERE NOT ((check_in > '%s' AND check_in >= '%s') OR (check_out <= '%s' AND check_out < '%s')) );'''
        %(hotel_id,checkin,checkout,checkin,checkout) )
        rooms = cur.fetchall()
        col = [column[0] for column in cur.description]
        results = []
        for room in rooms:
            results.append(dict(zip(col, room)))
        session['rooms'] = results
        session['filter'] = {'type':filterform.type.data,'price':str(filterform.price.data),'checkin':str(filterform.checkin.data),'checkout':str(filterform.checkout.data)}
        con.close()
    if request.method == 'POST':
        if 'filter' in request.form:
            if filterform.validate_on_submit():
                type_id = filterform.type.data
                price, checkin, checkout = filterform.price.data, str(filterform.checkin.data)+interval_time, str(filterform.checkout.data)+interval_time
                con = sqlite3.connect(DATABASE)
                con.row_factory = sqlite3.Row
                cur = con.cursor()
                cur.execute('''SELECT room_id,room_no,price,no_beds,wifi,tv,ac FROM ROOM NATURAL JOIN TYPE
                WHERE type_id=%s AND price<=%s AND hotel_id=%s AND room_id NOT IN
                (SELECT room_id FROM RESERVATION
                WHERE NOT ((check_in > '%s' AND check_in >= '%s') OR (check_out <= '%s' AND check_out < '%s')) );'''
                %(type_id,price,hotel_id,checkin,checkout,checkin,checkout) )
                rooms = cur.fetchall()
                col = [column[0] for column in cur.description]
                results = []
                for room in rooms:
                    results.append(dict(zip(col, room)))
                session['rooms'] = results
                session['filter'] = {'type':filterform.type.data,'price':str(filterform.price.data),'checkin':str(filterform.checkin.data),'checkout':str(filterform.checkout.data)}
                con.close()
        elif 'choose' in request.form:
            con = sqlite3.connect(DATABASE)
            cur = con.cursor()
            cur.execute('SELECT hotel_name FROM HOTEL WHERE hotel_id=%s;'%(hotel_id))
            hotel_name = cur.fetchone()[0]
            con.close()
            item = {'room_id':request.form['room_id'], 'room_no':request.form['room_no'], 'price':request.form['price_amt'],
            'check_in':request.form['check_in'], 'check_out':request.form['check_out'], 'hotel_name':hotel_name, 'beds':request.form['beds'],
            'wifi':request.form['wifi'], 'tv':request.form['tv'], 'ac':request.form['ac']}
            if 'cart' in session:
                print("sucess")
                session['cart'].append(item)
            else:
                session['cart']=[item]
        #elif 'delete' in request.form:
        #    session['cart'] = [x for x in session['cart'] if x['room_id']!=request.form['room_id']]
    return render_template('room.html', hotel_id=hotel_id, filterform = filterform, rooms=session['rooms'], types=types,
    filter=session['filter'])
