##Our Recipe Sharing App
import os
import pymongo
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from bson.objectid import ObjectId
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash, session, get_flashed_messages
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import datetime

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secret key for session management
app.config['TEMPLATES_AUTO_RELOAD'] = True  # Auto reload templates for development

# Load environment variables
load_dotenv()

# Connect to MongoDB Atlas
uri = os.getenv("MONGODB_URI")
client = MongoClient(uri, server_api=ServerApi('1'))

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

# Initialize database and collections
db = client.recipeshare
users = db.users
recipes = db.recipes
##Storing current user
current_user = None
current_recipe = None

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data['_id'])
        self.username = user_data['username']
        self.email = user_data['email']
        self.favorite_cuisine = user_data.get('favorite_cuisine')
        self.cooking_skill = user_data.get('cooking_skill')
        self.bio = user_data.get('bio', '')

    def get_id(self):
        return self.id

@login_manager.user_loader
def load_user(user_id):
    user_data = users.find_one({'_id': ObjectId(user_id)})
    if user_data:
        return User(user_data)
    return None

# Routes
@app.route('/')
def index():
    return render_template('index.html')

# Auth routes
@app.route('/auth/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Validing login credentials
        login_user = users.find_one({'email': email, 'password': password})
        if users.find_one({'email': email, 'password': password}):
            return redirect(url_for('index'), current_user = login_user)
        
    return render_template('auth/login.html')

@app.route('/auth/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Process registration form
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm-password']
        cooking_level = request.form['cooking-level']
        favorite_cuisine = request.form['favorite-cuisine']

        if password != confirm_password and len(password) >= 8:
            ##Needs to display an error message
            pass
        elif users.find_one({"username": username} or {"email": email}):
            ##Needs to display an error message
            pass
        else:
            ##Creating Users
            if favorite_cuisine:
                users.insert_one({'username': username, 'email': email, 'password': password,
                                 'cookingLevel': cooking_level, 'favoriteCuisine': favorite_cuisine})
            else:
                users.insert_one({'username': username, 'email': email, 'password': password,
                                 'cookingLevel': cooking_level})
            return redirect(url_for('login'), current_user = User(users.find_one({'username': username})))
    
    return render_template('auth/register.html')

@app.route('/logout')
def logout():
    # In a real implementation, this would log the user out
    return redirect(url_for('login'))

# User profile routes
@app.route('/user/profile')
def profile():
    # User profile page
    return render_template('user/profile.html')

@app.route('/user/edit-profile', methods=['GET', 'POST'])
def edit_profile(current_user):
    if request.method == 'POST':
        # Process form submission
        req_user = request.form['username'] 
        req_pass = request.form['password'] 

        ##Update username as long as it does not exist
        if req_user and not users.find_one({"username": req_user}):
            ##Might need to display some kind of error message here
            current_user['username'] = req_user
            users.update_one({'_id': current_user['_id']}, {"$set": { 'username':  req_user}})

        ##Update password
        if req_pass and len(req_pass) >= 8:
            current_user['password'] = req_pass
            users.update_one({'_id': current_user['_id']}, {"$set": { 'password':  req_pass}})

        return redirect(url_for('profile'))
    
    return render_template('user/edit-profile.html')

@app.route('/user/settings', methods=['GET', 'POST'])
def settings():
    return render_template('user/settings.html')

# Recipe routes
@app.route('/editpage')
def editpage():
    # Recipe editing page
    return render_template('editpage.html')

@app.route('/recipe')
@app.route('/recipe/<recipe_id>')
def recipe(recipe_id=None):
    # Recipe view page
    # If recipe_id is provided, you could fetch that specific recipe
    # For now, just render the template
    return render_template('recipe.html')

# Friends routes
@app.route('/friends/friends-list')
def friends_list():
    # Friends list page
    return render_template('friends/friends-list.html')

@app.route('/friends/friend-profile')
@app.route('/friends/friend-profile/<friend_id>')
def friend_profile(friend_id=None):
    # Friend profile page
    # If friend_id is provided, you could fetch that specific friend
    return render_template('friends/friend-profile.html')

@app.route('/friends/friendsrecipe')
def friendsrecipe():
    # Friend's recipe page
    return render_template('friends/friendsrecipe.html')

# Debug route - helpful for development
@app.route('/debug')
def debug():
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            "endpoint": rule.endpoint,
            "methods": list(rule.methods),
            "path": str(rule)
        })
    return render_template('debug.html', routes=routes)

# Context processor to make flash messages available in templates
@app.context_processor
def utility_processor():
    def get_messages():
        return get_flashed_messages(with_categories=True)
    
    return dict(get_messages=get_messages)

# Start the app
if __name__ == '__main__':
    app.run(debug=True)
