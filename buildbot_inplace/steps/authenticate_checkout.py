""" Buildbot inplace config
(C) Copyright 2015-2017 HicknHack Software GmbH

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
from urlparse import urlparse, urlunparse
from buildbot.steps.source.git import Git
from buildbot.steps.source.svn import SVN
from buildbot.steps.shell import ShellCommand
from .success import ShowStepIfSuccessful


def set_url_auth(git_url, user, password):
    scheme, netloc, url, params, query, fragment = urlparse(git_url)
    if user and password:
        netloc = "%(user)s:%(password)s@%(netloc)s" % locals()
    return urlunparse((scheme, netloc, url, params, query, fragment))


def create_authenticate_checkout_step(project):
    description = 'Authenticate Checkout'
    repo_credentials = project.repo_credentials
    if not repo_credentials:
    	return ShellCommand(command=['echo', 'No Authentication Supplied. Skipping.'])
    
    return ShellCommand(command=['echo', 'TODO: Store Authentication.'])

    # repo_type = project.repo_type
    # if repo_type != "git":
    #     return ShellCommand()
    
    # return ShellCommand()