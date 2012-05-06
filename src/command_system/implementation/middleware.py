# Copyright (c) 2009-2010, Alexander Cherniuk (ts33kr@gmail.com)
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
Provides a glue to tie command system framework and the actual code
where it would be dropped in. Defines a little bit of scaffolding to
support interaction between the two and a few utility methods so you
don't need to dig up the code itself to write basic commands.
"""

from types import StringTypes
from traceback import print_exc

from pango import FontDescription
from common import gajim

from ..framework import CommandProcessor
from ..errors import CommandError, NoCommandError
from ..tools import gconf

class ChatCommandProcessor(CommandProcessor):
    """
    A basic scaffolding to provide convenient interaction between the
    command system and chat controls. It will be merged directly into
    the controls, by ChatCommandProcessor being among superclasses of
    the controls.
    """

    def process_as_command(self, text):
        self.command_succeeded = False
        parents = super(ChatCommandProcessor, self)
        flag = parents.process_as_command(text)
        if flag and self.command_succeeded:
            self.add_history(text)
            self.clear_input()
        return flag

    def execute_command(self, name, arguments):
        try:
            parents = super(ChatCommandProcessor, self)
            parents.execute_command(name, arguments)
        except NoCommandError, error:
            details = dict(name=error.name, message=error.message)
            message = "%(name)s: %(message)s\n" % details
            message += "Try using the //%(name)s or /say /%(name)s " % details
            message += "construct if you intended to send it as a text."
            self.echo_error(message)
        except CommandError, error:
            self.echo_error("%s: %s" % (error.name, error.message))
        except Exception:
            self.echo_error("Error during command execution!")
            print_exc()
        else:
            self.command_succeeded = True

    def looks_like_command(self, text, body, name, arguments):
        # Command escape stuff ggoes here. If text was prepended by the
        # command prefix twice, like //not_a_command (if prefix is set
        # to /) then it will be escaped, that is sent just as a regular
        # message with one (only one) prefix removed, so message will be
        # /not_a_command.
        if body.startswith(self.COMMAND_PREFIX):
            self.send(body)
            return True

    def command_preprocessor(self, command, name, arguments, args, kwargs):
        # If command argument contain h or help option - forward it to
        # the /help command. Dont forget to pass self, as all commands
        # are unbound. And also don't forget to print output.
        if 'h' in kwargs or 'help' in kwargs:
            help = self.get_command('help')
            self.echo(help(self, name))
            return True

    def command_postprocessor(self, command, name, arguments, args, kwargs, value):
        # If command returns a string - print it to a user. A convenient
        # and sufficient in most simple cases shortcut to a using echo.
        if value and isinstance(value, StringTypes):
            self.echo(value)

class CommandTools:
    """
    Contains a set of basic tools and shortcuts you can use in your
    commands to perform some simple operations. These will be merged
    directly into the controls, by CommandTools being among superclasses
    of the controls.
    """

    def __init__(self):
        self.install_tags()

    def install_tags(self):
        buffer = self.conv_textview.tv.get_buffer()

        name = gconf("/desktop/gnome/interface/monospace_font_name")
        name = name if name else "Monospace"
        font = FontDescription(name)

        command_ok_tag = buffer.create_tag("command_ok")
        command_ok_tag.set_property("font-desc", font)
        command_ok_tag.set_property("foreground", "#3465A4")

        command_error_tag = buffer.create_tag("command_error")
        command_error_tag.set_property("font-desc", font)
        command_error_tag.set_property("foreground", "#F57900")

    def shift_line(self):
        buffer = self.conv_textview.tv.get_buffer()
        iter = buffer.get_end_iter()
        if iter.ends_line() and not iter.is_start():
            buffer.insert_with_tags_by_name(iter, "\n", "eol")

    def append_with_tags(self, text, *tags):
        buffer = self.conv_textview.tv.get_buffer()
        iter = buffer.get_end_iter()
        buffer.insert_with_tags_by_name(iter, text, *tags)

    def echo(self, text, tag="command_ok"):
        """
        Print given text to the user, as a regular command output.
        """
        self.shift_line()
        self.append_with_tags(text, tag)

    def echo_error(self, text):
        """
        Print given text to the user, as an error command output.
        """
        self.echo(text, "command_error")

    def send(self, text):
        """
        Send a message to the contact.
        """
        self.send_message(text, process_commands=False)

    def set_input(self, text):
        """
        Set given text into the input.
        """
        buffer = self.msg_textview.get_buffer()
        buffer.set_text(text)

    def clear_input(self):
        """
        Clear input.
        """
        self.set_input(str())

    def add_history(self, text):
        """
        Add given text to the input history, so user can scroll through
        it using ctrl + up/down arrow keys.
        """
        self.save_message(text, 'sent')

    @property
    def connection(self):
        """
        Get the current connection object.
        """
        return gajim.connections[self.account]

    @property
    def full_jid(self):
        """
        Get a full JID of the contact.
        """
        return self.contact.get_full_jid()
