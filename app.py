import os
import requests
from flask import Flask, session, redirect, request, url_for, render_template
from flask_session import Session
from requests_oauthlib import OAuth2Session
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import create_engine, exc
from sqlalchemy.sql import text

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
engine = create_engine("mysql+pymysql://c391tujwolvmij5a:tqkzvprrc96kcm2g@frwahxxknm9kwy6c.cbetxkdyhwsb.us-east-1.rds.amazonaws.com:3306/rjb11pca4j89kh0x")
# engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
app.secret_key = os.urandom(24)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

OURA_CLIENT_ID     = os.getenv('OURA_CLIENT_ID')
OURA_CLIENT_SECRET = os.getenv('OURA_CLIENT_SECRET')

OURA_AUTH_URL = 'https://cloud.ouraring.com/oauth/authorize'
OURA_TOKEN_URL = 'https://api.ouraring.com/oauth/token'

global user_str

@app.route('/login', methods = ['POST'])
def oura_login():
    """Login to the Oura cloud.
    This will redirect to the login page 
    of the OAuth provider in our case the 
    Oura cloud's login page

    """

    if request.method == 'POST':
       
        global user_str
        user_str = request.form['fname']
       
    oura_session = OAuth2Session(OURA_CLIENT_ID)
    # URL for Oura's authorization page for specific client
    authorization_url, state = oura_session.authorization_url(OURA_AUTH_URL)
    print(state)
    session['oauth_state'] = state
    print(session['oauth_state'])
    return redirect(authorization_url)


@app.route('/callback')
def callback():
    """Callback page
    Get the acces_token from response url from Oura. 
    Redirect to the sleep data page.
    """
    oura_session = OAuth2Session(OURA_CLIENT_ID, state=session['oauth_state'])
    session['oauth'] = oura_session.fetch_token(
                        OURA_TOKEN_URL,
                        client_secret=OURA_CLIENT_SECRET,
                        authorization_response=request.url)
    print(session['oauth'])
    return redirect(url_for('.sleep'))

@app.route('/sleep')
def sleep():
    oauth_access_token = session['oauth']['access_token']
    # add 
    oauth_refresh_token = session['oauth']['refresh_token']

    # Add token to the database
    # save_token = user_token(user_id = user_str,access_token = oauth_access_token, refresh_token = oauth_refresh_token)
    user = db.execute(text(f"SELECT * FROM tokens WHERE user_id = '{user_str}'"))
    if not len([item for item in user]):
    # add 
        db.execute(text(f"INSERT INTO tokens (user_id, access_token, refresh_token) VALUES ('{user_str}', '{oauth_access_token}', '{oauth_refresh_token}')"))
    else:
        db.execute(text(f"UPDATE tokens SET access_token = '{oauth_access_token}'  WHERE user_id = '{user_str}'"))
        db.execute(text(f"UPDATE tokens SET refresh_token = '{oauth_refresh_token}'  WHERE user_id = '{user_str}'"))
    db.commit()
    with open('user_tokens.txt', 'a') as f:
        f.write(user_str +': ' + oauth_access_token + oauth_refresh_token + '\n')
    return  render_template('exit.html')

@app.route('/')
def home():
    """Welcome page of the sleep data app.
    """
    return render_template('welcome.html') # "<h1>Welcome to your Oura app</h1>"

if __name__ == "__main__":
    app.run(debug=False, host='0.0.0.0', port='9090')
    # with app.test_request_context():
    #     print(url_for('index'))
    #     print(url_for('login'))
    #     print(url_for('login', next='/'))
        # print(url_for('profile', username='John Doe'))