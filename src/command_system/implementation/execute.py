# Copyright (c) 2010, Alexander Cherniuk (ts33kr@gmail.com)
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# * Redistributions of source code must retain the above copyright
#   notice, this list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in the
#   documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""
Provides facilities to safely execute expressions inside a shell process
and capture the resulting output, in an asynchronous fashion, avoiding
deadlocks. If the process execution time reaches the threshold - it is
forced to terminate. Consists of a tiny framework and a couple of
commands as a frontend.
"""

from subprocess import Popen, PIPE
from os.path import expanduser

from glib import timeout_add

from ..framework import CommandContainer, command, doc
from hosts import ChatCommands, PrivateChatCommands, GroupChatCommands

class Execute(CommandContainer):
    AUTOMATIC = True
    HOSTS = ChatCommands, PrivateChatCommands, GroupChatCommands

    DIRECTORY = "~"

    POLL_INTERVAL = 100
    POLL_COUNT = 5

    @command("exec", raw=True)
    @doc(_("Execute expression inside a shell, show output"))
    def execute(self, expression):
        Execute.spawn(self, expression)

    @classmethod
    def spawn(cls, processor, expression):
        pipes = dict(stdout=PIPE, stderr=PIPE)
        directory = expanduser(cls.DIRECTORY)
        popen = Popen(expression, shell=True, cwd=directory, **pipes)
        cls.monitor(processor, popen)

    @classmethod
    def monitor(cls, processor, popen):
        poller = cls.poller(processor, popen)
        timeout_add(cls.POLL_INTERVAL, poller.next)

    @classmethod
    def poller(cls, processor, popen):
        for x in xrange(cls.POLL_COUNT):
            yield cls.brush(processor, popen)
        cls.overdue(processor, popen)
        yield False

    @classmethod
    def brush(cls, processor, popen):
        if popen.poll() is not None:
            cls.terminated(processor, popen)
            return False
        return True

    @classmethod
    def terminated(cls, processor, popen):
        stdout, stderr = cls.fetch(popen)
        success = popen.returncode == 0
        if success and stdout:
            processor.echo(stdout)
        elif not success and stderr:
            processor.echo_error(stderr)

    @classmethod
    def overdue(cls, processor, popen):
        popen.terminate()

    @classmethod
    def fetch(cls, popen):
        data = popen.communicate()
        return map(cls.clean, data)

    @staticmethod
    def clean(text):
        strip = chr(10) + chr(32)
        return text.strip(strip)

class Show(Execute):

    @command("sh", raw=True)
    @doc(_("Execute expression inside a shell, send output"))
    def show(self, expression):
        Show.spawn(self, expression)

    @classmethod
    def terminated(cls, processor, popen):
        stdout, stderr = cls.fetch(popen)
        success = popen.returncode == 0
        if success and stdout:
            processor.send(stdout.decode('utf8'))
        elif not success and stderr:
            processor.echo_error(stderr)
