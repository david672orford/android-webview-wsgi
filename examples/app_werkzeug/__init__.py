#from __future__ import print_function
import os
import datetime

from werkzeug.wsgi import SharedDataMiddleware
from werkzeug.wrappers import Request, Response
from werkzeug.routing import Map, Rule
from werkzeug.exceptions import NotFound, HTTPException, abort
from jinja2 import Environment, FileSystemLoader

# This replaces Flask
class WsgiDispatcher(object):
	def __init__(self):
		# Tell the templating engine where the templates are.
		self.jinja_env = Environment(
			loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), "templates")),
			autoescape=True
			)
		# Start with an empty URL map, derived classes will add rules.
		self.url_map = Map()

	# The WSGI app
	def __call__(self, environ, start_response):
		request = Request(environ)
		adapter = self.url_map.bind_to_environ(request.environ)
		try:
			endpoint, values = adapter.match()
			response = getattr(self, endpoint)(request, **values)
			response = self.process_response(response)
		except NotFound as e:
			response = self.render_template('error-404.html')
			response.status_code = 404
		except HTTPException as e:
			response = e
		return response(environ, start_response)

	def process_response(self, response):
		return response

	# Fill an HTML template with data.
	def render_template(self, template_name, **context):
		template = self.jinja_env.get_template(template_name)
		return Response(template.render(context), mimetype='text/html')

class OurApp(WsgiDispatcher):
	def __init__(self):
		super(OurApp,self).__init__()
		self.url_map.add(Rule('/', endpoint = 'get_index'))
	def get_index(self, request):
		return self.render_template("index.html", time=str(datetime.datetime.now()))

app = OurApp()
app = SharedDataMiddleware(app, { '/static':  os.path.join(os.path.dirname(__file__), 'static') } )

