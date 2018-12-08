import sys

from flask import Flask, render_template
import traceback

app = Flask(__name__)

@app.route('/')
def index():
	return render_template('index.html')

@app.route('/page1')
def page1():
	return render_template('page1.html')

@app.route('/page2')
def page2():
	return render_template('page2.html')

@app.errorhandler(Exception)
def error(e):
	traceback.print_exc()
	return e

