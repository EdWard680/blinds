from sync_controller import SyncController

from jsonrpclib.SimpleJSONRPCServer import SimpleJSONRPCServer, SimpleJSONRPCRequestHandler
from http.server import SimpleHTTPRequestHandler

import os
import threading
import base64
import socket
import logging
import time
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class RequestHandler(SimpleHTTPRequestHandler, SimpleJSONRPCRequestHandler):
	pass

class AuthHandler(RequestHandler):
	KEY = ''

	def do_HEAD(self):
		''' head method '''
		self.send_response(200)
		self.send_header('Content-type', 'text/html')
		self.end_headers()

	def do_authhead(self):
		''' do authentication '''
		self.send_response(401)
		self.send_header('WWW-Authenticate', 'Basic realm=\"Test\"')
		self.send_header('Content-type', 'text/html')
		self.end_headers()
	
	def authenticate(self):
		''' Present frontpage with user authentication. '''
		
		tok = self.headers.get('Authorization')
		if tok is None:
			self.do_authhead()
			self.wfile.write(b'no auth header received')
			return False
		elif tok.encode('ascii') == b'Basic '+ self.KEY:
			return True
		else:
			self.do_authhead()
			self.wfile.write(tok.encode('ascii'))
			self.wfile.write(b'not authenticated')
			logger.info("Failed to authenticate%s", tok)
			return False
		
		return False

	def do_GET(self):
		if self.authenticate():
			SimpleHTTPRequestHandler.do_GET(self)
	
	def do_POST(self):
		if self.authenticate():
			SimpleJSONRPCRequestHandler.do_POST(self)

def start_server(controller, host='', port=80, handler=AuthHandler):
	web_dir = os.path.join(os.path.dirname(__file__), "web")
	os.chdir(web_dir)
	
	def daily_command(name, hour, minute, cmd_str, args = ()):
		logger.debug("daily_command(%s, %i, %i, %s, %s)", name, hour, minute, cmd_str, str(args))
		then = datetime.today().replace(hour=hour, minute=minute)
		
		if then < datetime.now():
			then += timedelta(days=1)
			logger.debug("Scheduling for tomorrow")
		
		logger.debug("Scheduling for %s", str(then))
		
		t = time.mktime(then.timetuple())
		
		controller.schedule_recurring(name, t, 24*60*60, cmd_str, args)
	
	server = SimpleJSONRPCServer((host, port), handler)
	server.register_instance(controller)
	server.register_function(daily_command)
	
	thread = threading.Thread(target=server.serve_forever)
	thread.start()
	
	return thread

# Starts the public server on port 80
def start_public_server(controller, key):
	AuthHandler.KEY = base64.b64encode(key)
	logger.info("Starting public server")
	return start_server(controller)

# Starts server to run on local network
def start_local_server(controller, port=8080):
	host = '0.0.0.0'
	logger.info("Starting local server bound to %s:%i", str(host), port)
	start_server(controller, host, port, RequestHandler)
