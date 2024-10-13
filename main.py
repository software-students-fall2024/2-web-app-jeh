import os
from flask import Flask, flash, jsonify, redirect, render_template, request, url_for
from pymongo import MongoClient
from dotenv import load_dotenv
import pymongo
from bson.objectid import ObjectId
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.secret_key = os.getenv('SECRET')

    cxn = pymongo.MongoClient(os.getenv('MONGO_URI'))
    MONGO_URI = os.getenv('MONGO_URI')
    db = cxn[os.getenv('MONGO_DBNAME')]
    MONGO_DBNAME = os.getenv('MONGO_DBNAME')

    try:
        cxn.admin.command("ping")
        print(" *", "Connected to MongoDB")
    except Exception as e:
        print("MongoDB connection error:", e)
    
    #Login manager
    manager = LoginManager()
    manager.init_app(app)
    manager.login_view = 'login'
    #Get user info
    users=db.UserData.find()
    userList=list(users)
    class User(UserMixin):
        def __init__(self, user_data):
            self.id = str(user_data['_id'])
            self.username = user_data['username']

        @staticmethod
        def get(user_id):
            user_data = db.users.find_one({'_id': ObjectId(user_id)})
            return User(user_data) if user_data else None
        pass

    @manager.user_loader
    def user_loader(user_id):
        return User.get(user_id)

    @manager.request_loader
    def request_loader(request):
        username = request.form.get('username')
        if username:
            user_data = db.users.find_one({'username': username})
            if user_data:
                user = User(user_data)
                password = request.form.get('password')
                if check_password_hash(user_data['password'], password):
                    return user
        return None
    
    #Login route
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            user_data = db.users.find_one({'username': username})
            if user_data and check_password_hash(user_data['password'], password):
                user = User(user_data)
                login_user(user)
                flash('Logged in successfully.')
                return redirect(url_for('home'))
            flash('Invalid username or password')
        return render_template('login.html')
    
    #Register route
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            existing_user = db.users.find_one({'username': username})
            if existing_user is None:
                hashed_password = generate_password_hash(password)
                db.users.insert_one({
                    'username': username,
                    'password': hashed_password
                })
                flash('Registration successful. Please log in.')
                return redirect(url_for('login'))
            flash('Username or email already exists')
        return render_template('register.html')
    
    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('You have been logged out.')
        return redirect(url_for('home'))

    #Home route
    @app.route('/', methods=['GET', 'POST'])
    @login_required
    def home():
        restaurants=db.RestaurantData.find().sort('restaurantName')
        restaurant_list = list(restaurants)
        return render_template('index.html', restaurants=restaurant_list)

    #Add data route
    @app.route('/add')
    @login_required
    def add():
        return render_template('add.html')

    #Delete data route
    @app.route('/delete')
    @login_required
    def delete():
        return render_template('delete.html')

    #Edit data route
    @app.route("/edit/<post_id>")
    @login_required
    def edit(post_id):
        restaurant=db.RestaurantData.find_one({"_id": ObjectId(post_id)})
        return render_template('edit.html', restaurant=restaurant)

    #Search data route
    @app.route('/search', methods=['GET'])
    @login_required
    def search():
        query = {}
        nameSearch = request.args.get('resName')
        cuisineSearch = request.args.get('resCuisine')
        userSearch = request.args.get('resUser')
        
        if nameSearch or cuisineSearch or userSearch:
            if nameSearch:
                query['restaurantName'] = {'$regex': nameSearch, '$options': 'i'}
            if cuisineSearch:
                query['cuisine'] = {'$regex': cuisineSearch, '$options': 'i'}
            if userSearch:
                query['username'] = {'$regex': userSearch, '$options': 'i'} 

            restaurants = db.RestaurantData.find(query)
            restaurantList = list(restaurants)
        else:
            restaurantList = []

        return render_template('search.html', restaurants=restaurantList)

    #Handle add data form
    @app.route('/addData', methods=['POST'])
    @login_required
    def addData():
        restaurantData = {
            'username': request.form['username'],
            'restaurantName': request.form['restaurantName'],
            'cuisine': request.form['cuisine'],
            'location': request.form['location'],
            'review': request.form['review']
        }

        #Add recipe data to db
        db.RestaurantData.insert_one(restaurantData)

        #change to a popup on screen
        return jsonify({'message': f"Restaurant '{request.form['restaurantName']}' submitted successfully!"}), 200

    #Handle delete data form
    @app.route('/deleteData', methods=['POST'])
    @login_required
    def deleteData():
        username = request.form['username']
        restaurantName = request.form['restaurantName']
        cuisine = request.form['cuisine']
        deleteRestaurant = db.RestaurantData.delete_one({'username': username, 'restaurantName': restaurantName, 'cuisine': cuisine})
        
        #change to a popup on screen
        if deleteRestaurant.deleted_count == 1: #if deleted ouput result to user
            return f"Restaurant '{restaurantName}' by '{username}' deleted successfully!", 200
        else:
            return f"Restaurant '{restaurantName}' by '{username}' not found / could not be deleted", 404
    
    app.debug = True
    return app

#run
if __name__ == '__main__':
    FLASK_PORT = os.getenv("FLASK_PORT", "5000")
    app = create_app()
    app.run(port=FLASK_PORT)