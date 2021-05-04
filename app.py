from flask import Flask, request, url_for, redirect, render_template, flash, session
from flask_pymongo import PyMongo
import pymongo
from pymongo import MongoClient
from monthblock import MonthBlock
import random, string, base64
from datetime import timedelta, datetime

app = Flask(__name__)
# #app.config['MONGO_URI'] = 'mongodb+srv://parthpatel:parth2911@shopifybackendchallange.dz8by.mongodb.net/YearView?retryWrites=true&w=majority&ssl=true&ssl_cert_reqs=CERT_NONE'
# app.config['MONGO_URI'] = 'mongodb://admin:admin@127.0.0.1:27017/YearView?authSource=admin&connect=false'

mongo_cluster = MongoClient('mongodb+srv://parth:parth2911@cluster0.l2pej.mongodb.net/myFirstDatabase?retryWrites=true&w=majority&ssl=true&ssl_cert_reqs=CERT_NONE') 
mongo_db = mongo_cluster['yearview']
collection = mongo_db['data']

app.secret_key = ''.join(random.choice(string.ascii_letters) for i in range(10))
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=60)

@app.route('/')
def login():

    return render_template('login.html', form_text="Login to YearView", button_text="Login", action='/check')

@app.route('/signup', methods=['GET', 'POST'])
def signup():

    if request.method == "POST":

        password = request.form['password']
        username = request.form['username']
        name = request.form['name']

        if password != request.form['confirm pass']:
 
            flash("Passwords don't match.")
            return redirect(url_for('signup'))

        if collection.find_one({"username": username}):

            flash("Username already exists, please try another one.")
            return redirect(url_for('signup'))
        
        else:

            configure_user = {
                "name" : name,
                "username": username,
                "password": base64.b64encode(password.encode("utf-8")),
                "images": []
                # {
                #     "month": '',
                #     "description": '',
                #     "category": '',
                #     "date": '',
                #     "key"
                # }
            }

            collection.insert_one(configure_user)

        flash("Account Created!")
        return redirect(url_for('login'))

    return render_template('signup.html', form_text="Create Account", button_text="Create", action='/signup')

@app.route('/check', methods=["POST"])
def check():

    username = request.form['username']
    password = request.form['password']

    user = collection.find_one({'username': username})

    if user:
        
        user_pass = base64.b64decode(user['password'])
        decoded_pass = user_pass.decode('utf-8')
        
        if password == decoded_pass:

            session['name'] = user['name']
            session['username'] = user['username'] 
            session['filter'] = "All"
            
            return redirect(url_for('user'))
            
        else:
            
            flash("Incorrect Password.")
            return redirect(url_for('login'))
    
    else:

        flash("Username not found.")
        return redirect(url_for('login'))

@app.route('/user')
def user():
    
    #if there is no user logged in, it will send them back to login page
    if 'name' not in session:

        flash("Please login or create an account.")
        return redirect(url_for('login'))

    name = session.get('name')
    user = collection.find_one({'username': session.get('username')})
    curr_date = datetime.today().strftime('%Y-%m-%d')

    #getting the images the user added today
    today_image_keys = [image['image_key'] for image in user['images'] if image['day'] == curr_date and session.get('filter') in image['image_category'] ]
    today_images = [url_for('file', filename=key) for key in today_image_keys]

    month_images = {'Jan': 0, "Feb": 0, "Mar": 0, "Apr": 0, "May": 0, "Jun": 0, "Jul": 0, "Aug": 0, "Sep": 0, "Oct": 0, "Nov": 0, "Dec": 0}
    
    for image in user['images']:

        if image['month'] in month_images:

            month_images[image['month']] += 1

    blocks = [MonthBlock(month, month_images[month]) for month in list(month_images.keys())]
    
    return render_template('main.html', name=name, images=today_images, blocks=blocks, color='rgb(223, 219, 219)')

@app.route('/user/filter/<image_filter>')
def filter(image_filter):

    session['filter'] = image_filter

    return redirect(url_for('user'))

@app.route('/user/add-image', methods=['POST'])
def add_image():

    if 'user_image' in request.files:

        image = request.files['user_image']
        image_key = ''.join(random.choice(string.ascii_letters) for i in range(10))
        image_config = {
            "image_description": request.form['image_description'],
            "image_category": ["All", request.form['image_category']],
            "image_key": image_key,
            "month": (datetime.now().strftime('%h'))[0:3],
            "day": datetime.today().strftime('%Y-%m-%d')
        }

        collection.update_one(
            {'username': session.get('username')},
            {"$push" : {
                "images": image_config
            }}
        )

        mongo.save_file(image_key, image)

        return redirect(url_for("user"))

@app.route('/user/<filename>')
def file(filename):
    
    return mongo.send_file(filename)

@app.route('/signout')
def signout():

    session.clear()
    return redirect(url_for('login'))
