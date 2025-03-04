# Web Application Exercise

A little exercise to build a web application following an agile development process. See the [instructions](instructions.md) for more detail.

Members (Discord)
- John Ma
- Andrew Park
- arkadiuz
- nocmomor

## Product vision statement

RecipeShare is a mobile-friendly social platform that empowers home cooks to discover, share, and personalize recipes based on cuisine types and dietary preferences.

## User stories

1. **As a home cook**, I want to browse recipes by cuisine type so that I can find dishes from cultures I'm interested in.
2. **As a user**, I want to filter recipes by meal type (sweet or savory) so I can find appropriate dishes for different occasions.
3. **As a home cook**, I want to share my recipes with photos so others can see and try my creations.
4. **As a recipe creator**, I want to edit my recipes so I can improve instructions or fix mistakes.
5. **As a recipe creator**, I want to delete my recipes so I can remove content I no longer want to share.
6. **As a user**, I want to search for recipes by ingredient so I can use what I already have in my kitchen.
7. **As a user**, I want to save my favorite recipes so I can easily find them later.
8. **As a user**, I want to comment on recipes to share my experience or ask questions.
9. **As a user**, I want to see cooking time estimates so I can plan my meal preparation.
10. **As a user**, I want to create a profile so I can showcase my recipes and cooking interests.
11. **As a user**, I want to sort recipes by difficulty level so I can find recipes that match my cooking skills.
12. **As a new user**, I want to register an account so I can participate in the community.

[View our user stories on GitHub Issues](https://github.com/software-students-spring2025/2-web-app-aquaproj2/issues)

## Steps necessary to run the software

1. **Clone the repository**:
- git clone https://github.com/software-students-spring2025/2-web-app-aquaproj2.git
- cd 2-web-app-aquaproj2
2. **Create and activate a virtual environment**:
- python -m venv venv
- source venv/bin/activate  # On Windows: venv\Scripts\activate
3. **Install the required dependencies**:
- pip install -r requirements.txt
4. **Create a .env file in the project root directory with our MongoDB connection string**:
- MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority&appName=appname
5. **Run the application**:
- python app.py
6. **Open your browser and navigate to**: **http://127.0.0.1:5000**

## Task boards
- [Sprint 1 Task Board](https://github.com/orgs/software-students-spring2025/projects/53)
- [Sprint 2 Task Board](https://github.com/orgs/software-students-spring2025/projects/109)
