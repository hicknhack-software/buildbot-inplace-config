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
from buildbot.steps.shell import ShellCommand
from ..project import RepoCredential


def set_url_auth(git_url, user, password):
    scheme, netloc, url, params, query, fragment = urlparse(git_url)
    if user and password:
        netloc = "%(user)s:%(password)s@%(netloc)s" % locals()
    return urlunparse((scheme, netloc, url, params, query, fragment))


def create_authenticate_checkout_steps(project):
    repo_credentials = project.repo_credentials
    if not repo_credentials:
        return [ShellCommand(command=['echo', 'Incomplete Authentication Supplied. Skipping.'])]
    auth_commands = [ShellCommand(command=['rm', '~/.git-credentials'])]
    for repo_credential in repo_credentials:
    	assert isinstance(repo_credentials, RepoCredential)
    	if not repo_credential.url and not repo_credential.user and not repo_credential.password
    		continue
    	configure_git_command = ["git", "config", "--global", "credential.helper", "store"]
    	auth_url = set_url_auth(git_url=repo_credentials.url, user=repo_credentials.user, password=repo_credentials.password)
    	update_store_command = ["echo", auth_url, ">>", "~/.git-credentials"]
    	auth_commands.extend([ShellCommand(command=configure_git_command), ShellCommand(command=update_store_command)])
    return auth_commands
