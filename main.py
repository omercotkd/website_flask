from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms.fields import StringField, SubmitField
from wtforms.validators import DataRequired
import requests

movie_api_key = "1c43ec8b09e94f5db4c18c4b4cc6d0ee"
movie_api_url = "https://api.themoviedb.org/3/search/movie"

# app configs
app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)

app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///movies-collection.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db = SQLAlchemy(app)


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(500), nullable=False, unique=True)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(500), nullable=False)


db.create_all()


# forms config
class EditForm(FlaskForm):
    new_rating = StringField("Your Rating out of 10 e.g. 7.5", validators=[DataRequired()])
    new_review = StringField("Your Review", validators=[DataRequired()])
    submit = SubmitField('Save Changes')


class AddForm(FlaskForm):
    movie_name = StringField("Enter the movie name:", validators=[DataRequired()])
    submit = SubmitField('Add movie')


# website routs
@app.route("/")
def home():
    all_movies = Movie.query.order_by(Movie.rating).all()
    for index in range(len(all_movies)):
        all_movies[index].ranking = len(all_movies) - index

    db.session.commit()
    return render_template("index.html", movies=all_movies)


@app.route("/edit", methods=["GET", "POST"])
def edit_review():
    form = EditForm()
    movie_id = request.args.get("id")
    movie_to_edit = Movie.query.get(int(movie_id))
    # checks if new data was added to the form and if so will update the movie
    if form.validate_on_submit():
        movie_to_edit.rating = float(request.form["new_rating"])
        movie_to_edit.review = request.form["new_review"]
        db.session.commit()
        return redirect(url_for('home'))

    return render_template("edit.html", form=form, movie=movie_to_edit)


@app.route("/delete", methods=["GET", "POST"])
def delete_movie():
    # delete a movie we selected from the db
    movie_id = request.args.get("id")
    movie_to_delete = Movie.query.get(int(movie_id))
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for('home'))


@app.route("/add-movie", methods=["GET", "POST"])
def find_movie():
    form = AddForm()
    if form.validate_on_submit():
        movie_name = request.form["movie_name"]
        params = {
            "api_key": movie_api_key,
            "query": movie_name
        }
        movies = requests.get(movie_api_url, params=params).json()['results']
        return render_template("select.html", movies=movies)
    return render_template("add.html", form=form)


@app.route("/find-movie", methods=["GET", "POST"])
def add_movie():
    # get the movie we selected data
    movie_api_id = request.args.get("id")
    params = {
        "api_key": movie_api_key,
    }
    data = requests.get(f"https://api.themoviedb.org/3/movie/{movie_api_id}", params=params).json()
    # add the movie data to the db
    new_movie = Movie(
        title=data["original_title"],
        year=data["release_date"].split("-")[0],
        img_url=f"https://image.tmdb.org/t/p/w500{data['poster_path']}",
        description=data["overview"]
    )
    db.session.add(new_movie)
    db.session.commit()

    # point us to the edit review on that movie
    return redirect(url_for('edit_review', id=new_movie.id))


if __name__ == '__main__':
    app.run(debug=True)
