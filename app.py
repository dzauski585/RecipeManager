import requests
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from recipe_scrapers import scrape_html  # Import the scraping library

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///recipes.db'  # Update with your actual database URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define the Recipe model
class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    ingredients = db.Column(db.Text, nullable=False)
    directions = db.Column(db.Text, nullable=False)
    cook_time = db.Column(db.Integer, nullable=False)
    prep_time = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(50), nullable=False)

# Route to display all recipes, categorized
@app.route('/')
def index():
    meals = Recipe.query.filter_by(category='Meal').all()
    desserts = Recipe.query.filter_by(category='Dessert').all()
    sauces = Recipe.query.filter_by(category='Sauce').all()
    return render_template('index.html', meals=meals, desserts=desserts, sauces=sauces)

# Route to view a specific recipe
@app.route('/recipe/<int:id>')
def recipe_detail(id):
    recipe = Recipe.query.get_or_404(id)
    ingredients_list = [
        ingredient.strip() for ingredient in recipe.ingredients.split('\n') if ingredient.strip()
    ]
    return render_template('recipe_detail.html', recipe=recipe, ingredients_list=ingredients_list)

# Route to add a new recipe
# Route to display the 'Add Recipe' page
@app.route('/add_recipe', methods=['GET', 'POST'])
def add_recipe():
    if request.method == 'POST':
        title = request.form['title']
        ingredients = request.form['ingredients']
        directions = request.form['directions']
        cook_time = request.form['cook_time']
        prep_time = request.form['prep_time']
        category = request.form['category']

        # Create a new Recipe object
        new_recipe = Recipe(
            title=title,
            ingredients=ingredients,
            directions=directions,
            cook_time=int(cook_time),  # Ensure it's an integer
            prep_time=int(prep_time),  # Ensure it's an integer
            category=category
        )

        # Add the recipe to the database and commit
        db.session.add(new_recipe)
        db.session.commit()

        # Redirect to the index page after the recipe is added
        return redirect(url_for('index'))

    # If the request is GET, render the 'Add Recipe' page
    return render_template('add_recipe.html')

# Route to display the index page with all recipes

# Route for scraping recipes from a URL

# Route to edit a recipe
@app.route('/edit_recipe/<int:id>', methods=['GET', 'POST'])
def edit_recipe(id):
    recipe = Recipe.query.get_or_404(id)
    if request.method == 'POST':
        recipe.title = request.form['title']
        recipe.ingredients = request.form['ingredients']
        recipe.directions = request.form['directions']
        recipe.category = request.form['category']

        try:
            recipe.cook_time = int(request.form['cook_time']) if request.form['cook_time'] else None
            recipe.prep_time = int(request.form['prep_time']) if request.form['prep_time'] else None
        except ValueError:
            return "Cook time and prep time must be valid integers.", 400

        db.session.commit()
        return redirect(url_for('index'))

    return render_template('edit_recipe.html', recipe=recipe)



if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create database tables
    app.run(debug=True)
