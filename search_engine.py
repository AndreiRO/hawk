import rdatabase
import flask
from flask import jsonify


app   = flask.Flask(__name__)
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = 'abracadabra'

@app.route('/')
def root():
	return flask.render_template('home.html')

@app.route('/do-search', methods = ['POST'])
def do_search():
	if flask.request.method == 'POST':
		words = flask.request.form['words']
		flask.session['words'] = words
	return flask.redirect(flask.url_for('results_page'))
	
@app.route('/results_page')
def results_page():
	words = flask.session.get('words')
	split_words = words.split()

	db = rdatabase.Database()
	links = db.search(split_words)

	return flask.render_template('results_page.html', links=links)

@app.route('/results')
def results():
	words = flask.request.args.get('words', 'sava');
	split_words = words.split()

	db = rdatabase.Database()
	links = db.search(split_words)

	return jsonify(links=links)

if __name__ == '__main__':
	app.run()
