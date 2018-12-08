from tlslite import HTTPTLSConnection, HandshakeSettings
settings = HandshakeSettings()
settings.useExperimentalTackExtension = True
h = HTTPTLSConnection("www.google.com", 443, settings=settings)
h.request("GET", "/")
r = h.getresponse()
print(r.read())
