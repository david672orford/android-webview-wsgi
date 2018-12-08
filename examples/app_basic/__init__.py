def app(environ, start_response):
	start_response("200 OK", [])
	return ["Hello World!"]
