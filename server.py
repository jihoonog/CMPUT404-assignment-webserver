#  coding: utf-8 
# There are for the date header
from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime

import socketserver
import os
import mimetypes

# Copyright 2013 Abram Hindle, Eddie Antonio Santos
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#
# Furthermore it is derived from the Python documentation examples thus
# some of the code is Copyright © 2001-2013 Python Software
# Foundation; All Rights Reserved
#
# http://docs.python.org/2/library/socketserver.html
#
# run: python freetests.py

# try: curl -v -X GET http://127.0.0.1:8080/

# Define global constants
WWW_DIR = os.getcwd() + "/www"

class HTTPRequestHandler():
    """
    This is a HTTP request handler that will generate a HTTP server response based on the request given by the user
    """
    def __init__(self, request):
        """
        This will parse the request into a request type and request path  
        """
        # Define our status code and phrases
        self.status_code_phrase = {200: "OK", 301: "Moved Permanently", 403: "Forbidden", 404: "Not Found", 405: "Method Not Allowed"}

        request = request.decode().split()
        self.request_type = request[0]
        self.request_path = request[1]

    def _build_response(self, status_code, headers={}, body=""):
        """
        This is a private helper function that will generate the response to return to the user.
        """
        # Create the status line in the beginning of our response
        response = "HTTP/1.1 {} {}\r\n".format(status_code, self.status_code_phrase[status_code])

        # Add the header information to the response
        if headers:
            for key, value in headers.items():
                response += "{}: {}\r\n".format(key, value)

        # Finally add our body to the reponse
        response += "\r\n" + str(body)


        return response

    def process_request(self):
        """
        This will process the request based on the request type and request path of the class's instance.
        
        The date header code is from Florian Bosch here
        https://stackoverflow.com/questions/225086/rfc-1123-date-representation-in-python
        """
        # Get the date timestamp
        now = datetime.now()
        stamp = mktime(now.timetuple())
        timestamp =  str(format_date_time(stamp))
        
        # Create the response header for the response
        # These headers SHOULD be used for all requests
        response_header_response = {
            "Connection": "close",
            "Date": timestamp,
        }
        
        # If it's not a GET request return 405
        if self.request_type != "GET":
            response_header_response["Content-Length"] = 0
            return self._build_response(405, headers=response_header_response)    

        request_path = WWW_DIR + self.request_path
        # If the request path is a directory then show index.html
        if self.request_path[-1] == "/":
            request_path = request_path + "index.html"

        # This will get the absolute path of the request path
        realpath = os.path.realpath(request_path)
        # Check if the request path is within /www
        if request_path not in realpath:
            response_header_response["Content-Length"] = 0
            return self._build_response(404)
        
        try:
            with open(realpath, 'r') as file:
                response_header_response["Content-Length"] = os.path.getsize(realpath)
                # Return the content at the path with a 200 code
                return self._build_response(200, {"Content-Type": mimetypes.guess_type(realpath)[0]}, file.read())
        except IsADirectoryError:
            # If the path is a directory then send a redirect response
            response_header_response["Content-Length"] = 0
            return self._build_response(301, {"Location": self.request_path + "/"})
        except FileNotFoundError:
            # If file is not found return a file not found response
            response_header_response["Content-Length"] = 0
            return self._build_response(404)
class MyWebServer(socketserver.BaseRequestHandler):
    
    def handle(self):
        self.data = self.request.recv(1024).strip()
        print ("Got a request of: %s\n" % self.data)
        http_response = HTTPRequestHandler(self.data).process_request()
        self.request.sendall(bytearray(http_response,'utf-8'))

if __name__ == "__main__":
    HOST, PORT = "localhost", 8080

    socketserver.TCPServer.allow_reuse_address = True
    # Create the server, binding to localhost on port 8080
    server = socketserver.TCPServer((HOST, PORT), MyWebServer)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()
