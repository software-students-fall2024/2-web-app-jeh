from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient

app = Flask(__name__)

#MongoDB connection
mongo_uri = "mongodb+srv://recipeUser:RECIPE@recipecluster.red1l.mongodb.net/?retryWrites=true&w=majority&appName=RecipeCluster"
client = MongoClient(mongo_uri)
db = client["RecipeCluster"] 

#Home route
@app.route('/')
def index():
    return render_template('index.html')

#Add data route
@app.route('/add')
def add():
    return render_template('add.html')

#Delete data route
@app.route('/delete')
def delete():
    return render_template('delete.html')

#Edit data route
@app.route('/edit')
def edit():
    return render_template('edit.html')

#Search data route
@app.route('/search')
def search():
    
    nameSearch = request.args.get('restaurantName')
    cuisineSearch = request.args.get('restaurantCuisine')
    locationSearch = request.args.get('restaurantLocation')
    query = {}
    if nameSearch:
        query['name'] = {'$regex': nameSearch, '$options': 'i'}
    if cuisineSearch:
        query['cuisine'] = {'$regex': cuisineSearch, '$options': 'i'}
    if locationSearch:
        query['location'] = {'$regex': locationSearch, '$options': 'i'}
    restaurants = db.RestaurantCluster.find(query)
    restaurantList = list(restaurants)
    return render_template('search.html', restaurants=restaurantList)

#View all data route
@app.route('/view')
def view():
    recipes=db.RecipeCluster.find()
    recipe_list = list(recipes)
    return render_template('view.html', recipes=recipe_list)

#Handle add data form
@app.route('/addData', methods=['POST'])
def addData():
    recipeData = {
        'authorName': request.form['authorName'],
        'recipeTitle': request.form['recipeTitle'],
        'servings': request.form['servings'],
        'time': request.form['time'],
        'ingredients': request.form['ingredients'],
        'instructions': request.form['instructions']
    }

    #if we want to write to json
    #with open('recipes.json', 'a') as file:
        #json.dump(recipeData, file)
        #file.write("\n")

    #Add recipe data to db
    db.RecipeCluster.insert_one(recipeData)

    #change to a popup on screen
    return jsonify({'message': f"Recipe '{request.form['recipeTitle']}' submitted successfully!"}), 200

#Handle delete data form
@app.route('/deleteData', methods=['POST'])
def deleteData():
    authorName = request.form['authorName']
    recipeTitle = request.form['recipeTitle']
    deleteRecipe = db.RecipeCluster.delete_one({'authorName': authorName, 'recipeTitle': recipeTitle})
    
    #change to a popup on screen
    if deleteRecipe.deleted_count==1: #if deleted ouput result to user
        return f"Recipe '{recipeTitle}' by '{authorName}' deleted successfully!", 200
    else:
        return f"Recipe '{recipeTitle}' by '{authorName}' not found / could not be deleted", 404

#run
if __name__ == '__main__':
    app.run(debug=True)
