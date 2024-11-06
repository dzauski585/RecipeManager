from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from recipe_scrapers import scrape_html

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
    return render_template('index.html', meal_recipes=meals, dessert_recipes=desserts, sauce_recipes=sauces)

# Scraping function
def scrape_recipe(url):
    scraper = scrape_html(html=None, org_url=url, online=True, wild_mode=True)

# Extract various parts of the recipe
    title = scraper.title()
    ingredients = scraper.ingredients()
    directions = scraper.instructions()
    cook_time = scraper.total_time()  # Cook and prep time combined
    prep_time = scraper.prep_time()

    return {
        'title': title,
        'ingredients': ingredients,
        'directions': directions,
        'cook_time': cook_time,
        'prep_time': prep_time,
    }

# Route to scrape recipe from URL and display it in the 'edit recipe' format
@app.route('/scrape_recipe', methods=['GET', 'POST'])
def scrape_recipe_page():
    if request.method == 'POST':
        url = request.form['url']
        scraped_data = scrape_recipe(url)
        return render_template('edit_scrape.html', scraped_data=scraped_data)

    return render_template('scrape_recipe.html')

# Route to add the scraped recipe to the database
@app.route('/edit_scrape', methods=['POST'])
def add_scraped_recipe():
    # Print the form data to see what it contains
    print("Form data received:", request.form)

    # Extract data from the form (which contains the scraped data)
    scraped_data = request.form.to_dict()

    # Ensure there's no 'url' key in the submitted form data
    if 'url' in scraped_data:
        print("URL key found in form data:", scraped_data['url'])
        return "Error: URL key shouldn't be in the form data", 400

    
    new_recipe = Recipe(
        title=scraped_data['title'],
        ingredients=scraped_data['ingredients'],
        directions=scraped_data['directions'],
        cook_time=int(scraped_data['cook_time']),
        prep_time=int(scraped_data['prep_time']),
        category=scraped_data['category']
    )

    db.session.add(new_recipe)
    db.session.commit()

    return redirect(url_for('index'))
# Route to view a specific recipe
@app.route('/recipe/<int:id>')
def recipe_detail(id):
    recipe = Recipe.query.get_or_404(id)
    ingredients_list = [
        ingredient.strip() for ingredient in recipe.ingredients.split('\n') if ingredient.strip()
    ]
    return render_template('recipe_detail.html', recipe=recipe, ingredients_list=ingredients_list)

# Route to add a new recipe

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

@app.route('/delete_recipe/<int:id>', methods=['POST'])
def delete_recipe(id):
    recipe = Recipe.query.get_or_404(id)  # Fetch the recipe by ID or return a 404 if not found
    
    try:
        db.session.delete(recipe)  # Delete the recipe from the session
        db.session.commit()  # Commit the transaction to the database
        return redirect(url_for('index'))  # Redirect to the index page after deletion
    except Exception as e:
        db.session.rollback()  # Rollback the session in case of an error
        print(f"Error: {e}")
        return "An error occurred while deleting the recipe.", 500  # Return an error message

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create database tables
    app.run(debug=True)
