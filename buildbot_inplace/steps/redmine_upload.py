""" Buildbot inplace config
(C) Copyright 2015-2018 HicknHack Software GmbH

The original code can be found at:
https://github.com/hicknhack-software/buildbot-inplace-config

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from buildbot.process.buildstep import BuildStep, SUCCESS, SKIPPED
from buildbot.steps.shell import ShellCommand, SetPropertyFromCommand
from buildbot.util import flatten
from buildbot import config

from twisted.internet import defer
from twisted.internet import reactor

from zope.interface import implementer

from twisted.web.iweb import IBodyProducer
from twisted.web.client import Agent
from twisted.web.client import FileBodyProducer
from twisted.web.client import readBody
from twisted.web.http_headers import Headers

import json
import os.path
import errno
from base64 import b64encode

@implementer(IBodyProducer)
class StringProducer(object):
    def __init__(self, body):
        self.body = body
        self.length = len(body)

    def startProducing(self, consumer):
        consumer.write(self.body)
        return defer.succeed(None)

    def pauseProducing(self):
        pass

    def stopProducing(self):
        pass

class RedmineUpload(BuildStep):

	renderables = ['products']

	def __init__(self, project, products, product_dir, redmine_identifier, *args, **kwargs):
		self.project = project
		self.products = products
		self.product_dir = product_dir
        #super(RedmineUpload, self).__init__(*args, **kwargs)
		BuildStep.__init__(self, *args, **kwargs)

		self.redmine_url = project.redmine_url
		self.redmine_identifier = redmine_identifier
		
		self.auth_header = [b"Basic " + b64encode(b"{}:{}".format(project.redmine_username, project.redmine_password))]

	def _upload_file(self, file):
		header = Headers({
			'Content-Type': ['application/octet-stream'],
			'authorization' : self.auth_header,
		})

		agent = Agent(reactor)
		producer = FileBodyProducer(file)

		return agent.request('POST', self.redmine_url + '/uploads.json', header, producer)

	@defer.inlineCallbacks
	def _check_filename_available(self, filename):
		header = Headers({
			'Content-Type': ['application/json'],
			'authorization' : self.auth_header,
		})
		
		agent = Agent(reactor)

		url = self.redmine_url + "/projects/" + self.redmine_identifier + "/files.json"
		response = yield agent.request('GET', url, header)
		responseBody = yield readBody(response)
		for file in json.loads(responseBody)["files"]:
			if file["filename"] == filename:
				defer.returnValue(False)

		defer.returnValue(True)

	def _upload_token(self, filename, token):
		header = Headers({
			'Content-Type': ['application/json'],
			'authorization' : self.auth_header,
		})
		
		agent = Agent(reactor)

		upload = json.dumps(
		{ "file" : {
			"token": token,
			"filename": filename,
			#description:
			#version_id:
		}})

		producer = StringProducer(upload)
		url = self.redmine_url + "/projects/" + self.redmine_identifier + "/files.json"
		return agent.request('POST', url, header, producer)


	@defer.inlineCallbacks
	def run(self):
		log = yield self.addLog('redmine_upload', 't')
		log.addContent("Uploading files to Redmine instance at %s\n" % self.redmine_url)

		skipped = True
		
		for product in self.products:
			try:
				buildnumber = self.getProperty('buildnumber')
				filename = os.path.basename(product)
				base, ext = os.path.splitext(filename)
				filename_versioned = "%s-%s%s" % (base, buildnumber, ext)

				with open(os.path.join(self.product_dir, filename), "rb") as f:
					log.addContent("Checking for filename \"%s\" on server...\n" % filename_versioned)
					available = yield self._check_filename_available(filename_versioned)
					if not available:
						log.addContent("File \"%s\" already exists, skipping...\n" % filename_versioned)
						continue
					
					skipped = False

					log.addContent("Uploading File %s\n" % filename_versioned)
					response = yield self._upload_file(f)
					# except/errcallback if this is not 20X
					responseBody = yield readBody(response)
					print "Got HTTP Response %s\n" % responseBody
					token = json.loads(responseBody)["upload"]["token"]
					log.addContent("Uploaded File %s, spawned token %s\n" % (filename_versioned, token))

					yield self._upload_token(filename_versioned, token)
			except IOError, e:
				if e.errno == errno.EISDIR:
					log.addContent("Skipping directory %s\n" % product)
				else:
					raise e

		defer.returnValue(SKIPPED if skipped else SUCCESS)
