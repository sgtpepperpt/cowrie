# -*- test-case-name: Cowrie Proxy Test Cases -*-

# Copyright (c) 2019 Guilherme Borges
# See LICENSE for details.

from __future__ import absolute_import, division

import os

from twisted.cred import portal
from twisted.internet import defer, reactor
from twisted.trial import unittest

from cowrie.core.checkers import HoneypotPasswordChecker, HoneypotPublicKeyChecker
from cowrie.core.realm import HoneyPotRealm
from cowrie.ssh.factory import CowrieSSHFactory
from cowrie.test.proxy_compare import ProxyCommandCompare

# os.environ['HONEYPOT_LOG_PATH'] = '../../../../var/log/cowrie'
# os.environ['HONEYPOT_DOWNLOAD_PATH'] = '../../../../var/lib/cowrie/downloads'
# os.environ['HONEYPOT_SHARE_PATH'] = '../../../../share/cowrie'
# os.environ['HONEYPOT_STATE_PATH'] = '../../../../var/lib/cowrie'
# os.environ['HONEYPOT_ETC_PATH'] = '../../../../etc'
# os.environ['HONEYPOT_CONTENTS_PATH'] = '../../../../honeyfs'
# os.environ['HONEYPOT_TXTCMDS_PATH'] = '../../../../txtcmds'
#
# os.environ['SHELL_FILESYSTEM'] = '../../../../share/cowrie/fs.pickle'
# os.environ['SHELL_PROCESSES'] = '../../../../share/cowrie/cmdoutput.json'

# os.environ['SSH_RSA_PUBLIC_KEY'] = '../../../../var/lib/cowrie/ssh_host_rsa_key.pub'
# os.environ['SSH_RSA_PRIVATE_KEY'] = '../../../../var/lib/cowrie/ssh_host_rsa_key'
# os.environ['SSH_DSA_PUBLIC_KEY'] = '../../../../var/lib/cowrie/ssh_host_dsa_key.pub'
# os.environ['SSH_DSA_PRIVATE_KEY'] = '../../../../var/lib/cowrie/ssh_host_dsa_key'

os.environ['HONEYPOT_TTYLOG'] = 'false'
os.environ['OUTPUT_JSONLOG_ENABLED'] = 'false'


def create_ssh_factory(backend):
    factory = CowrieSSHFactory(None, backend)
    factory.portal = portal.Portal(HoneyPotRealm())
    factory.portal.registerChecker(HoneypotPublicKeyChecker())
    factory.portal.registerChecker(HoneypotPasswordChecker())
    # factory.portal.registerChecker(HoneypotNoneChecker())

    return factory


class ProxyTests(unittest.TestCase):
    """
    How to test the proxy:
        - setUp runs a 'shell' backend on 4444; then set up a 'proxy' on port 5555 connected to the 'shell' backend
        - test_ssh_proxy runs an exec command via a client against both proxy and shell; returns a deferred
        - the deferred resolves if the output from both is the same
    """
    def setUp(self):
        os.chdir('../../../../')

        self.factory_shell = create_ssh_factory('shell')
        self.shell_server = reactor.listenTCP(4444, self.factory_shell)

        # Proxy
        os.environ['PROXY_BACKEND'] = 'simple'

        os.environ['PROXY_BACKEND_SSH_HOST'] = 'localhost'
        os.environ['PROXY_BACKEND_SSH_PORT'] = '4444'
        os.environ['PROXY_BACKEND_TELNET_HOST'] = 'localhost'
        os.environ['PROXY_BACKEND_TELNET_PORT'] = '4445'

        self.factory_proxy = create_ssh_factory('proxy')
        self.proxy_server = reactor.listenTCP(5555, self.factory_proxy)

    def test_ls(self):
        self.ssh_deferred = defer.Deferred()
        ProxyCommandCompare().execute('ls -halt', self.ssh_deferred)
        return self.ssh_deferred

    def tearDown(self):
        for x in self.factory_proxy.running:
            x.loseConnection()

        self.proxy_server.stopListening()
        self.shell_server.stopListening()

        self.factory_shell.stopFactory()
        self.factory_proxy.stopFactory()
