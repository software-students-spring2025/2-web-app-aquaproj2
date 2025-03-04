##Our Recipe Sharing App
import os
import pymongo
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from bson.objectid import ObjectId
from bson.errors import InvalidId
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

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, user_doc):
        self.user_doc = user_doc

    def get_id(self):
        user_id = str(self.user_doc.get('_id'))
        return user_id
        

@login_manager.user_loader
def load_user(user_id):
    try:
        user_data = users.find_one({'_id': ObjectId(user_id)})
        if user_data:
            return User(user_data)
    except InvalidId:
        pass
    return None

# Helper function to safely convert string to ObjectId
def safe_object_id(id_string):
    try:
        return ObjectId(id_string)
    except (InvalidId, TypeError):
        return None

# Routes
@app.route('/')
def index():
    return render_template('index.html')

# Auth routes
@app.route('/auth/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email').lower()
        password = request.form.get('password')
        
        # Validating login credentials
        cur_user = users.find_one({'email': email, 'password': password})
        if cur_user and cur_user['password'] == password:
            login_user(User(cur_user))
            return redirect(url_for('index'))
        else:
            flash("Incorrect username or password, please try again!")
            return redirect(url_for('login'))
    return render_template('auth/login.html')

@app.route('/auth/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Process registration form
        username = request.form['username'].lower()
        email = request.form['email'].lower()
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        cooking_level = request.form['cooking_skill']
        favorite_cuisine = request.form['favorite_cuisine']

        if password != confirm_password:
            ##Displaying error
            flash("Error: Passwords do not match!")
            return redirect(url_for('register'))
        elif len(password) < 8:
            flash("Error: Password must be greater than length 8")
            return redirect(url_for('register'))
        elif users.find_one({"username": username} or {"email": email}):
            flash("Error: Username or email already taken!")
            return redirect(url_for('register'))
        else:
            ##Creating User
            users.insert_one({
                'username': username, 
                'email': email, 
                'password': password,
                'cookingLevel': cooking_level, 
                'favoriteCuisine': favorite_cuisine, 
                'bio': "",
                'followers': [],
                'following': []
            })

        flash("Account successfully created! Please Log-In")
        return redirect(url_for('login'))
    
    return render_template('auth/register.html')

@app.route('/logout')
@login_required
def logout():
    ##Logging out user from flask-login
    logout_user()
    return redirect(url_for('login'))

# User profile routes
@app.route('/user/profile')
@login_required
def profile():
    # Get current user's data from the database
    user_data = users.find_one({'_id': ObjectId(current_user.get_id())})
    
    # Get user's recipes
    user_recipes = list(recipes.find({'user_id': ObjectId(current_user.get_id())}))
    
    return render_template('user/profile.html', user=user_data, recipes=user_recipes)

@app.route('/user/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    # Get current user data
    user_data = users.find_one({'_id': ObjectId(current_user.get_id())})
    
    if request.method == 'POST':
        # Process form submission
        username = request.form.get('username')
        email = request.form.get('email')
        bio = request.form.get('bio')
        favorite_cuisine = request.form.get('favorite_cuisine')
        cooking_skill = request.form.get('cooking_skill')
        
        # Check if username is taken by someone else
        existing_user = users.find_one({'username': username})
        if existing_user and str(existing_user['_id']) != current_user.get_id():
            flash("Username already taken!")
            return redirect(url_for('edit_profile'))
        
        # Update user data
        users.update_one(
            {'_id': ObjectId(current_user.get_id())},
            {'$set': {
                'username': username,
                'email': email,
                'bio': bio,
                'favoriteCuisine': favorite_cuisine,
                'cookingLevel': cooking_skill
            }}
        )
        
        flash('Profile updated successfully!')
        return redirect(url_for('profile'))
    
    return render_template('user/edit-profile.html', user=user_data)

@app.route('/user/settings', methods=['GET', 'POST'])
@login_required
def settings():
    user_data = users.find_one({'_id': ObjectId(current_user.get_id())})
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'update_username':
            new_username = request.form.get('username')
            if new_username and not users.find_one({'username': new_username, '_id': {'$ne': ObjectId(current_user.get_id())}}):
                users.update_one({'_id': ObjectId(current_user.get_id())}, {'$set': {'username': new_username}})
                flash('Username updated successfully!')
            else:
                flash('Username already taken or invalid!')
                
        elif action == 'update_password':
            new_password = request.form.get('password')
            if new_password and len(new_password) >= 8:
                users.update_one({'_id': ObjectId(current_user.get_id())}, {'$set': {'password': new_password}})
                flash('Password updated successfully!')
            else:
                flash('Password must be at least 8 characters!')
                
        elif action == 'delete_account':
            # Delete user's recipes
            recipes.delete_many({'user_id': ObjectId(current_user.get_id())})
            # Delete user account
            users.delete_one({'_id': ObjectId(current_user.get_id())})
            logout_user()
            flash('Account deleted successfully!')
            return redirect(url_for('login'))
    
    return render_template('user/settings.html', user=user_data)

# Recipe routes
@app.route('/editpage')
@login_required
def editpage():
    # Get user recipes categorized by type
    sweet_recipes = list(recipes.find({'user_id': ObjectId(current_user.get_id()), 'type': 'sweet'}))
    savory_recipes = list(recipes.find({'user_id': ObjectId(current_user.get_id()), 'type': 'savory'}))
    
    return render_template('editpage.html', sweet_recipes=sweet_recipes, savory_recipes=savory_recipes)

@app.route('/recipe')
@app.route('/recipe/<recipe_id>')
def recipe(recipe_id=None):
    recipe_data = None
    author = None
    
    if recipe_id:
        try:
            obj_id = safe_object_id(recipe_id)
            if obj_id:
                # Get the specific recipe from database
                recipe_data = recipes.find_one({'_id': obj_id})
                if recipe_data:
                    # Get recipe author info
                    author = users.find_one({'_id': recipe_data.get('user_id')})
        except Exception as e:
            print(f"Error retrieving recipe: {e}")
    
    # Default recipe if no ID is provided or recipe not found
    return render_template('recipe.html', recipe=recipe_data, author=author)

@app.route('/recipe/add', methods=['GET', 'POST'])
@login_required
def add_recipe():
    if request.method == 'POST':
        name = request.form.get('name')
        ingredients = request.form.get('ingredients', '').split(',')
        instructions = request.form.get('instructions', '').split('\n')
        recipe_type = request.form.get('recipe_type')  # 'sweet' or 'savory'
        cooking_time = request.form.get('cooking_time', '30')
        difficulty = request.form.get('difficulty', 'Intermediate')
        
        # Create new recipe
        new_recipe = {
            'name': name,
            'ingredients': [ingredient.strip() for ingredient in ingredients if ingredient.strip()],
            'instructions': [instruction.strip() for instruction in instructions if instruction.strip()],
            'type': recipe_type,
            'cooking_time': cooking_time,
            'difficulty': difficulty,
            'user_id': ObjectId(current_user.get_id()),
            'created_at': datetime.datetime.now()
        }
        
        recipes.insert_one(new_recipe)
        flash('Recipe added successfully!')
        return redirect(url_for('editpage'))
    
    return redirect(url_for('editpage'))

@app.route('/recipe/edit/<recipe_id>', methods=['GET', 'POST'])
@login_required
def edit_recipe(recipe_id):
    try:
        obj_id = safe_object_id(recipe_id)
        if not obj_id:
            flash('Invalid recipe ID')
            return redirect(url_for('editpage'))
            
        recipe_data = recipes.find_one({'_id': obj_id})
        
        # Check if recipe exists and belongs to current user
        if not recipe_data or str(recipe_data.get('user_id')) != current_user.get_id():
            flash('Recipe not found or you do not have permission to edit it!')
            return redirect(url_for('editpage'))
        
        if request.method == 'POST':
            name = request.form.get('name')
            ingredients = request.form.get('ingredients', '').split(',')
            instructions = request.form.get('instructions', '').split('\n')
            recipe_type = request.form.get('recipe_type')
            cooking_time = request.form.get('cooking_time')
            difficulty = request.form.get('difficulty')
            
            # Update recipe
            recipes.update_one(
                {'_id': obj_id},
                {'$set': {
                    'name': name,
                    'ingredients': [ingredient.strip() for ingredient in ingredients if ingredient.strip()],
                    'instructions': [instruction.strip() for instruction in instructions if instruction.strip()],
                    'type': recipe_type,
                    'cooking_time': cooking_time,
                    'difficulty': difficulty,
                    'updated_at': datetime.datetime.now()
                }}
            )
            
            flash('Recipe updated successfully!')
            return redirect(url_for('recipe', recipe_id=recipe_id))
        
        return render_template('edit_recipe.html', recipe=recipe_data)
    except Exception as e:
        flash(f'Error: {str(e)}')
        return redirect(url_for('editpage'))

@app.route('/recipe/delete/<recipe_id>')
@login_required
def delete_recipe(recipe_id):
    try:
        obj_id = safe_object_id(recipe_id)
        if not obj_id:
            flash('Invalid recipe ID')
            return redirect(url_for('editpage'))
            
        recipe_data = recipes.find_one({'_id': obj_id})
        
        # Check if recipe exists and belongs to current user
        if not recipe_data or str(recipe_data.get('user_id')) != current_user.get_id():
            flash('Recipe not found or you do not have permission to delete it!')
            return redirect(url_for('editpage'))
        
        # Delete recipe
        recipes.delete_one({'_id': obj_id})
        flash('Recipe deleted successfully!')
        return redirect(url_for('editpage'))
    except Exception as e:
        flash(f'Error: {str(e)}')
        return redirect(url_for('editpage'))

# Friends routes
@app.route('/friends/friends-list')
@login_required
def friends_list():
    # Get current user data
    user_data = users.find_one({'_id': ObjectId(current_user.get_id())})
    following_ids = user_data.get('following', [])
    
    # Get friends (users being followed)
    friends = []
    for friend_id in following_ids:
        friend = users.find_one({'_id': ObjectId(friend_id)})
        if friend:
            friend_recipe_count = recipes.count_documents({'user_id': ObjectId(friend_id)})
            friend['recipe_count'] = friend_recipe_count
            friends.append(friend)
    
    # Get suggested friends (users not being followed)
    suggested_friends = []
    potential_friends = users.find({
        '_id': {'$ne': ObjectId(current_user.get_id())},
        '_id': {'$nin': [ObjectId(fid) for fid in following_ids]}
    }).limit(5)
    
    for pf in potential_friends:
        recipe_count = recipes.count_documents({'user_id': pf['_id']})
        pf['recipe_count'] = recipe_count
        suggested_friends.append(pf)
    
    return render_template('friends/friends-list.html', 
                          friends=friends, 
                          suggested_friends=suggested_friends)

@app.route('/friends/friend-profile/<friend_id>')
@login_required
def friend_profile(friend_id=None):
    try:
        # Try to convert friend_id to ObjectId
        obj_id = safe_object_id(friend_id)
        if not obj_id:
            flash('Invalid friend ID')
            return redirect(url_for('friends_list'))
            
        # Get friend data
        friend = users.find_one({'_id': obj_id})
        if not friend:
            flash('Friend not found!')
            return redirect(url_for('friends_list'))
        
        # Get friend's recipes
        friend_recipes = list(recipes.find({'user_id': obj_id}))
        
        # Check if current user is following this friend
        user_data = users.find_one({'_id': ObjectId(current_user.get_id())})
        is_following = obj_id in [ObjectId(fid) for fid in user_data.get('following', [])]
        
        return render_template('friends/friend-profile.html', 
                              friend=friend, 
                              recipes=friend_recipes, 
                              is_following=is_following)
    except Exception as e:
        flash(f'Error: {str(e)}')
        return redirect(url_for('friends_list'))

@app.route('/friends/follow/<friend_id>')
@login_required
def follow_friend(friend_id):
    try:
        obj_id = safe_object_id(friend_id)
        if not obj_id:
            flash('Invalid friend ID')
            return redirect(url_for('friends_list'))
            
        # Update current user's following list
        users.update_one(
            {'_id': ObjectId(current_user.get_id())},
            {'$addToSet': {'following': obj_id}}
        )
        
        # Update friend's followers list
        users.update_one(
            {'_id': obj_id},
            {'$addToSet': {'followers': ObjectId(current_user.get_id())}}
        )
        
        flash('You are now following this user!')
        return redirect(url_for('friend_profile', friend_id=friend_id))
    except Exception as e:
        flash(f'Error: {str(e)}')
        return redirect(url_for('friends_list'))

@app.route('/friends/unfollow/<friend_id>')
@login_required
def unfollow_friend(friend_id):
    try:
        obj_id = safe_object_id(friend_id)
        if not obj_id:
            flash('Invalid friend ID')
            return redirect(url_for('friends_list'))
            
        # Remove from current user's following list
        users.update_one(
            {'_id': ObjectId(current_user.get_id())},
            {'$pull': {'following': obj_id}}
        )
        
        # Remove from friend's followers list
        users.update_one(
            {'_id': obj_id},
            {'$pull': {'followers': ObjectId(current_user.get_id())}}
        )
        
        flash('You have unfollowed this user!')
        return redirect(url_for('friend_profile', friend_id=friend_id))
    except Exception as e:
        flash(f'Error: {str(e)}')
        return redirect(url_for('friends_list'))

@app.route('/friends/friendsrecipe/<recipe_id>')
def friendsrecipe(recipe_id):
    try:
        obj_id = safe_object_id(recipe_id)
        if not obj_id:
            return render_template('friends/friendsrecipe.html')
            
        # Get the specific recipe from database
        recipe_data = recipes.find_one({'_id': obj_id})
        if recipe_data:
            # Get recipe author info
            author = users.find_one({'_id': recipe_data.get('user_id')})
            return render_template('friends/friendsrecipe.html', recipe=recipe_data, author=author)
    except Exception as e:
        print(f"Error retrieving recipe: {e}")
    
    # Default recipe if not found
    return render_template('friends/friendsrecipe.html')

# Search route
@app.route('/search')
@login_required
def search():
    query = request.args.get('q', '')
    
    if not query:
        return render_template('search.html', recipes=[], query='')
    
    # Search for recipes by name or ingredient
    search_results = recipes.find({
        '$or': [
            {'name': {'$regex': query, '$options': 'i'}},
            {'ingredients': {'$regex': query, '$options': 'i'}}
        ]
    })
    
    return render_template('search.html', recipes=list(search_results), query=query)

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