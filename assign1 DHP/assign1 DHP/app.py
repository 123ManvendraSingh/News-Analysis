from flask import Flask, render_template, request, session, redirect, url_for
from newspaper import Article
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from collections import Counter
import psycopg2
import json
from urllib.parse import unquote


# Initialize Flask app
app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

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
        dbname="newsdatabaseupdated",
        user="postgres",
        password="1857",
        host="localhost",
        port="5432"
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

# Route for password-based login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'admin' in session or 'google_token' in session:
        return redirect(url_for('history'))

    if request.method == 'POST' and request.form['password'] == '123':
        session['admin'] = True
        return redirect(url_for('history'))

    return render_template('login.html')

# Route for viewing history
@app.route('/history', methods=["GET", "POST"])
def history():
    if 'google_token' not in session and 'admin' not in session:
        # Redirect to Google login if not logged in
        return redirect(url_for('login'))

    conn = connect_to_db()
    cur = conn.cursor()
    cur.execute('''
        SELECT * FROM news_articles;
    ''')
    data = cur.fetchall()
    cur.close()
    conn.close()

    return render_template('history.html', data=data)

# Route for logging out
@app.route('/logout', methods=['POST'])
def logout():
    session.pop('admin', None)
    session.pop('google_token', None)
    return redirect(url_for('home'))

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

# Route for demo
@app.route('/process', methods=['GET', 'POST'])
def demo():
    return render_template("demo.html")

@app.route('/view_article', methods=['GET'])
def view_article():
    if request.method == 'GET':
        # Handle GET request data
        article_id = request.args.get('id')
        article_url = request.args.get('url')
        num_sentences = request.args.get('num_sentences')
        num_words = request.args.get('num_words')
        pos_counts = request.args.get('pos_counts')
        text = request.args.get('text')

        # Use these variables as needed in your template
        # data = {
        #     'id': article_id,
        #     'url': article_url,
        #     'num_sentences': num_sentences,
        #     'num_words': num_words,
        #     'pos_counts': pos_counts
        # }
        data=[article_id, article_url, num_sentences, num_words, pos_counts, text]

        return render_template('view_article.html', data=data)



if __name__ == '__main__':
    app.run(debug=True)
