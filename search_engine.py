import rdatabase
import flask
from flask import jsonify

app   = flask.Flask(__name__)
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = 'abracadabra'

@app.route('/')
def root():
	return flask.render_template('home.html')

@app.route('/results_page')
def results_page():

	words = flask.request.args.get('words')
	
	_from = int(flask.request.args.get('from', '0'))
	_to   = int(flask.request.args.get('to', '30'))	
	split_words = words.split()

	db = rdatabase.Database()
	links = db.search(split_words, _from, _to)
	
	return flask.render_template('results_page.html', links=links)

@app.route('/results')
def results():
	words = flask.request.args.get('words','sava');
	_from = int(flask.request.args.get('from', '0'))
	_to   = int(flask.request.args.get('to', '15'))

	split_words = words.split()

	db = rdatabase.Database()
	links = db.search(split_words, _from, _to)
	

	return jsonify(links=links)

@app.route('/suggest_spelling', methods=['POST'])
def suggest_spelling():
	fragment = flask.request.form['fragment']
	word = fragment.split()[-1]
	
	db = rdatabase.Database()
	suggestions = db.suggest_spelling(word)
	
	return jsonify(suggestions=suggestions)

@app.template_filter()
def words():
	return flask.request.args.get('words')

@app.template_filter()
def previous_from():
	current_from = int(flask.request.args.get('from'))
	_from = current_from - 30 if current_from-30 >= 0 else current_from

	return _from

@app.template_filter()
def previous_to():
	current_to = int(flask.request.args.get('to'))
	_to        = current_to - 30 if current_to-30 >= 30 else current_to

	return _to

@app.template_filter()
def next_from():
	return int(flask.request.args.get('from'))+30

@app.template_filter()
def next_to():
	return int(flask.request.args.get('to'))+30

app.jinja_env.globals.update(words=words)
app.jinja_env.globals.update(previous_from=previous_from)
app.jinja_env.globals.update(previous_to=previous_to)
app.jinja_env.globals.update(next_from=next_from)
app.jinja_env.globals.update(next_to=next_to)

if __name__ == '__main__':
	app.run( port=8080)

