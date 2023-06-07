from app import app
from flask import render_template

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/opinion_extraction')
def extract():
    return render_template('opinion_extraction.html')

@app.route('/product_list')
def product_list():
    return render_template('product_list.html')

@app.route('/name/',defaults={'name': "Anonim"})
@app.route('/name/<name>')
def name(name):
    return f"Hello, {name}!"