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

from twisted.internet import defer
from twisted.internet import reactor

from zope.interface import implementer

from twisted.web.iweb import IBodyProducer
from twisted.web.client import Agent
from twisted.web.client import FileBodyProducer
from twisted.web.client import readBody
from twisted.web.http_headers import Headers

from uritemplate import URITemplate

import json
import posixpath
import ntpath
import errno


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


class GithubUpload(BuildStep):
    github_release_url = URITemplate("https://api.github.com/repos{/owner,repo}/releases")

    renderables = ['products']

    def __init__(self, project, products, product_dir, deploy_config, *args, **kwargs):
        self.project = project
        self.products = products
        self.product_dir = product_dir

        self.release_url = self.github_release_url.expand(
            owner=deploy_config['owner'],
            repo=deploy_config['repo'])

        self.release_config = deploy_config['release']

        self.auth_header = Headers({
            'Authorization': ["token " + project.github_token],
            'User-Agent': ["hicknhack-software/buildbot-inplace-config"]
        })

        BuildStep.__init__(self, *args, **kwargs)

    @defer.inlineCallbacks
    def _create_release_tag(self):
        agent = Agent(reactor)

        json_data = json.dumps(self.release_config)
        producer = StringProducer(json_data)

        response = yield agent.request('POST', self.release_url, self.auth_header, producer)
        response_body = yield readBody(response)
        defer.returnValue((response.code, json.loads(response_body)))

    @defer.inlineCallbacks
    def _upload_file(self, upload_url, filename, file):
        agent = Agent(reactor)
        producer = FileBodyProducer(file)

        url = URITemplate(upload_url).expand(name=filename)

        self.log.addContent("Uploading File %s to %s\n" % (filename, url))

        headers = self.auth_header.copy()
        # This should be configureable. But GitHub itself will detect and overwrite the content-type
        headers.addRawHeader('Content-Type', 'application/octet-stream')

        response = yield agent.request('POST', url, headers, producer)
        response_body = yield readBody(response)
        defer.returnValue((response.code, json.loads(response_body)))

    @defer.inlineCallbacks
    def run(self):
        self.log = yield self.addLog('github_upload', 't')

        if not self.products:
            self.log.addContent("No products to upload.")
            defer.returnValue(SKIPPED)
            return

        self.log.addContent("Creating release tag %s\n" % self.release_config['name'])
        response_code, response = yield self._create_release_tag()
        self.log.addContent("Response from GitHub: %s\n" % response)

        if response_code not in range(200, 300):
            self.log.addContent("Release Creation Failed!\n")
            defer.returnValue(FAILED)
            return

        upload_url = response['upload_url'].encode("utf-8")

        skipped = True

        for product in self.products:
            try:
                filename = posixpath.basename(product)
                local_filename = filename
                filename = ntpath.basename(product)

                with open(posixpath.join(self.product_dir, local_filename), "rb") as f:
                    response_code, response = yield self._upload_file(upload_url, filename, f)
                    self.log.addContent("Response from Github: (%d) %s\n" % (response_code, response))
                    if response_code not in range(200, 300):
                        defer.returnValue(FAILED)
                        return

            except IOError as e:
                if e.errno == errno.EISDIR:
                    self.log.addContent("Skipping directory %s\n" % product)
                else:
                    raise e

        defer.returnValue(SUCCESS)
