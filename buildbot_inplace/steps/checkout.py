""" Buildbot inplace config
(C) Copyright 2015-2025 HicknHack Software GmbH

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
from urllib.parse import urlparse, urlunparse
from buildbot.steps.source.git import Git
from buildbot.util.git_credential import GitCredentialOptions
from buildbot.steps.source.svn import SVN
from .success import ShowStepIfSuccessful
from ..project import RepoCredential


def set_url_auth(repo_url, user, password):
    scheme, netloc, url, params, query, fragment = urlparse(repo_url)
    if user and password:
        netloc = "%(user)s:%(password)s@%(netloc)s" % locals()
    return urlunparse((scheme, netloc, url, params, query, fragment))


def create_checkout_step(project=None, only_config=False):
    """Generate Checkout steps for the supplied project"""
    description = 'Checkout' if not only_config else 'Checkout Buildbot config'

    repo_type = project.repo_type
    if repo_type == "git":
        repo_credentials = project.repo_credentials
        credentials =  []
        for repo_credential in repo_credentials:
            assert isinstance(repo_credential, RepoCredential)
            if not repo_credential.url and not repo_credential.user and not repo_credential.password:
                continue
            credentials.append(f"url={repo_credential.url}\nusername={repo_credential.user}\npassword={repo_credential.password}\n")

        return Git(repourl=set_url_auth(repo_url=project.repo_url, user=project.repo_user, password=project.repo_password),
                   branch=project.repo_branch,
                   mode=project.repo_mode,
                   submodules=not only_config,
                   shallow=only_config,
                   name=description,
                   git_credentials = GitCredentialOptions(credentials = credentials) if len(credentials) > 0 else None)
    elif repo_type == "svn":
        return SVN(repourl=project.repo_url,
                   mode=project.repo_mode,
                   username=project.repo_user,
                   password=project.repo_password,
                   name=description)

    else:
        raise Exception("Repository type '" + str(repo_type) + "' not supported.")
