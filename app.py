import os
from flask import Flask, render_template, request, session, redirect, url_for
from newspaper import Article
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from collections import Counter
import psycopg2
import json
from flask_oauthlib.client import OAuth
from werkzeug.urls import url_quote

nltk.download('punkt')
nltk.download('stopwords')

# Initialize Flask app
app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

GOOGLE_CLIENT_ID = '164891454040-p0tnb6nielg8gco0r2kffeioh7e86hq8.apps.googleusercontent.com'
GOOGLE_CLIENT_SECRET = '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'

oauth = OAuth(app)
google = oauth.remote_app(
    'google',
    consumer_key=GOOGLE_CLIENT_ID,
    consumer_secret=GOOGLE_CLIENT_SECRET,
    request_token_params={
        'scope': 'email',
    },
    base_url='https://www.googleapis.com/oauth2/v1/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://accounts.google.com/o/oauth2/token',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
)

# Routes for Google OAuth login
@app.route('/login-google')
def login_google():
    return google.authorize(callback=url_for('authorized_google', _external=True, _scheme='https'))

# Routes for Google OAuth logout
@app.route('/logout-google')
def logout_google():
    session.pop('google_token', None)
    session.pop('admin', None)  # Clear admin session as well
    return redirect(url_for('home'))

# Route for Google OAuth authorized callback
@app.route('/login/authorized-google')
def authorized_google():
    response = google.authorized_response()
    if response is None or response.get('access_token') is None:
        return 'Access denied: reason={} error={}'.format(
            request.args['error_reason'],
            request.args['error_description']
        )

    session['google_token'] = (response['access_token'], '')
    user_info = google.get('userinfo')

    # Check if the user is an admin or has the required credentials
    if user_info.data.get('email') == 'mschundawat2004@gmail.com':
        session['admin'] = True
        return redirect(url_for('history'))
    else:
        return 'You are not authorized.'

@google.tokengetter
def get_google_oauth_token():
    return session.get('google_token')

# Function to clean the text
def clean_text(text):
    words = word_tokenize(text)
    stop_words = set(stopwords.words('english'))
    clean_words = [word.lower() for word in words if word.isalnum() and word.lower() not in stop_words]
    return clean_words

# Function to analyze text with Universal POS tags
def analyze_text(text):
    sentences = sent_tokenize(text)
    num_sentences = len(sentences)
    words = word_tokenize(text)
    num_words = len(words)
    pos_tags = nltk.pos_tag(words)
    universal_tags = [(word, nltk.map_tag('en-ptb', 'universal', tag)) for word, tag in pos_tags]
    pos_counts = Counter(tag for word, tag in universal_tags)
    return num_sentences, num_words, pos_counts

# Function to connect to PostgreSQL database
def connect_to_db():
    conn = psycopg2.connect(
        host = 'dpg-cnm94321hbls739fgst0-a', database = 'newsdp', user = 'newsdp_user', password= '1OzMBGgqXC61A3D0Z3oXkYpnxg83uSzo'
    )
    return conn

def create_table(conn):
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS news_articles (
            id SERIAL PRIMARY KEY,
            url TEXT,
            num_sentences INTEGER,
            num_words INTEGER,
            pos_counts JSON,
            full_text TEXT
        );
    ''')
    conn.commit()
    cur.close()

# Route for home page
@app.route('/')
def home():
    return render_template('index.html')

# Route for processing form submission
@app.route('/process', methods=['POST'])
def process():
    url = request.form['url']
    article = Article(url)
    article.download()
    article.parse()
    text = article.text
    cleaned_text = clean_text(text)
    num_sentences, num_words, pos_counts = analyze_text(text)
    pos_counts_dict = dict(pos_counts)
    pos_counts_json = json.dumps(pos_counts_dict)

    conn = connect_to_db()
    create_table(conn)
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO news_articles (url, num_sentences, num_words, pos_counts, full_text)
        VALUES (%s, %s, %s, %s, %s);
    ''', (url, num_sentences, num_words, pos_counts_json, text))
    conn.commit()
    cur.close()
    conn.close()

    return render_template('result.html', url=url, num_sentences=num_sentences, num_words=num_words, pos_counts=pos_counts, text=text)

# Route for password-based login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'admin' in session:
        return redirect(url_for('history'))

    if request.method == 'POST' and request.form['password'] == '123':
        session['admin'] = True
        return redirect(url_for('history'))

    return render_template('login.html')

# Route for viewing history
@app.route('/history')
def history():
    if 'google_token' not in session and 'admin' not in session:
        # Redirect to Google login if not logged in
        return redirect(url_for('login_google'))

    conn = connect_to_db()
    cur = conn.cursor()
    cur.execute('''
        SELECT * FROM news_articles;
    ''')
    data = cur.fetchall()
    print(data)
    cur.close()
    conn.close()
    return render_template('history.html', data=data)

@app.route('/view-article/<path:url>', methods=['GET'])
def view_article(url):
    if 'google_token' not in session and 'admin' not in session:
        # Redirect to Google login if not logged in
        return redirect(url_for('login_google'))

    conn = connect_to_db()
    cur = conn.cursor()
    cur.execute('''
        SELECT * FROM news_articles WHERE url = %s;
    ''', (url,))
    data = cur.fetchone()
    cur.close()
    conn.close()

    if not data:
        return render_template('error.html', error='Article not found.')

    return render_template('view_article.html', data=data)

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('google_token', None)
    session.pop('admin', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
