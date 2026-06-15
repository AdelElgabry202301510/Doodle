import os
from flask import Flask, render_template, request, abort
from search_app.data_loader import DataLoader
from search_app.search_engine import SearchEngine
from markupsafe import Markup
import re

root_dir = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, static_folder='static', template_folder='templates')

data_loader = None
search_engine = None

def get_data_loader():
    global data_loader
    if data_loader is None:
        data_loader = DataLoader(root_dir)
    return data_loader


def get_search_engine():
    global search_engine
    if search_engine is None:
        search_engine = SearchEngine(get_data_loader())
    return search_engine


# Jinja filter to highlight query terms in text
def _highlight_filter(text, query):
    if not query or not text:
        return text
    try:
        q = re.escape(query.strip())
        pattern = re.compile(r'(' + q + r')', re.IGNORECASE)
        return Markup(pattern.sub(r'<mark>\1</mark>', text))
    except Exception:
        return text

app.jinja_env.filters['highlight'] = _highlight_filter


@app.route('/autocomplete')
def autocomplete():
    q = request.args.get('q', '')
    suggestions = get_data_loader().get_autocomplete(q, limit=12)
    # return JSON list
    from flask import jsonify
    return jsonify(suggestions)

@app.route('/')
def home():
    query = request.args.get('q', '')
    loader = get_data_loader()
    return render_template(
        'home.html',
        query=query,
        labels=loader.labels,
        suggestions=loader.suggestions,
    )

@app.route('/search')
def search():
    query = request.args.get('q', '').strip()
    results = get_search_engine().search(query)
    return render_template('results.html', query=query, results=results)

@app.route('/article/<int:doc_id>')
def article(doc_id):
    record = get_data_loader().get_record(doc_id)
    if record is None:
        abort(404)
    return render_template('article.html', record=record)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
