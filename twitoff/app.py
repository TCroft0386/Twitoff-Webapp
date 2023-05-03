from flask import Flask, render_template, request
from os import getenv
from twitoff.predict import predict_user
from .models import DB, User, Tweet
from .twitter import add_or_update_user, vectorize_tweet

# Create a "factory" for serving up the app when it is launched 
def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = getenv('DATABASE_URI')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    DB.init_app(app)

    @app.route("/")
    def home():
        users = User.query.all()
        print(users, flush=True)
        return render_template('base.html', title="home", users=users)

    @app.route('/reset')
    def reset():
        DB.drop_all()
        DB.create_all()
        tweet1_vector = vectorize_tweet('Wow...')
        sayer = User(id=1, username='sayer')
        tweet1 = Tweet(
            id=1, text='Wow...',
            user=sayer, vect=tweet1_vector)
        DB.session.add(sayer)
        DB.session.add(tweet1)
        DB.session.commit()
        return render_template('base.html', title='Reset DB')

    @app.route('/update')
    def update():
        usernames = [usr.username for usr in User.query.all()]
        for username in usernames:
            add_or_update_user(username)
        return render_template('base.html', title='Update')

    @app.route('/user', methods=['POST'])
    @app.route('/user/<username>', methods=['GET'])
    def user(username=None, message=''):
        if request.method == 'GET':
            tweets = User.query.filter(User.username == username).one().tweets
        if request.method == 'POST':
            tweets = []
            try:
                username = request.values['user_name']
                add_or_update_user(username)
                message = f'User "{username}" was successfully added.'
            except Exception as e:
                message = f'Error adding {username}: {e}'
        return render_template(
            'user.html',
            title=username,
            tweets=tweets,
            message=message
        )

    @app.route('/compare', methods=['POST'])
    def compare():
        user0 = request.values['user0']
        user1 = request.values['user1']
        if user0 == user1:
            message = 'Cannot compare a user to themselves'
        else:
            text = request.values['tweet_text']
            prediction = predict_user(user0, user1, text)
            message = '"{}" is more likely to be said by {} than {}.'.format(
                text,
                user1 if prediction else user0,
                user0 if prediction else user1
            )
        return render_template('prediction.html', title='Prediction', message=message)

    return app