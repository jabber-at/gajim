# Copyright (C) 2009-2010  Alexander Cherniuk <ts33kr@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Provides a tiny framework with simple, yet powerful and extensible
architecture to implement commands in a streight and flexible,
declarative way.
"""

import re
from types import FunctionType
from inspect import getargspec, getdoc

from dispatcher import Host, Container
from dispatcher import get_command, list_commands
from mapping import parse_arguments, adapt_arguments
from errors import DefinitionError, CommandError, NoCommandError

class CommandHost(object):
    """
    Command host is a hub between numerous command processors and
    command containers. Aimed to participate in a dispatching process in
    order to provide clean and transparent architecture.

    The AUTOMATIC class variable, which must be defined by a command
    host, specifies whether the command host should be automatically
    dispatched and enabled by the dispatcher or not.
    """
    __metaclass__ = Host

class CommandContainer(object):
    """
    Command container is an entity which holds defined commands,
    allowing them to be dispatched and proccessed correctly. Each
    command container may be bound to a one or more command hosts.

    The AUTOMATIC class variable, which must be defined by a command
    processor, specifies whether the command processor should be
    automatically dispatched and enabled by the dispatcher or not.

    Bounding is controlled by the HOSTS class variable, which must be
    defined by the command container. This variable should contain a
    sequence of hosts to bound to, as a tuple or list.
    """
    __metaclass__ = Container

class CommandProcessor(object):
    """
    Command processor is an immediate command emitter. It does not
    participate in the dispatching process directly, but must define a
    host to bound to.

    Bounding is controlled by the COMMAND_HOST variable, which must be
    defined in the body of the command processor. This variable should
    be set to a specific command host.
    """

    # This defines a command prefix (or an initializer), which should
    # preceede a a text in order it to be processed as a command.
    COMMAND_PREFIX = '/'

    def process_as_command(self, text):
        """
        Try to process text as a command. Returns True if it has been
        processed as a command and False otherwise.
        """
        prefix = text.startswith(self.COMMAND_PREFIX)
        length = len(text) > len(self.COMMAND_PREFIX)
        if not (prefix and length):
            return False

        body = text[len(self.COMMAND_PREFIX):]
        body = body.strip()

        parts = body.split(None, 1)
        name, arguments = parts if len(parts) > 1 else (parts[0], None)

        flag = self.looks_like_command(text, body, name, arguments)
        if flag is not None:
            return flag

        self.execute_command(name, arguments)

        return True

    def execute_command(self, name, arguments):
        command = self.get_command(name)

        args, opts = parse_arguments(arguments) if arguments else ([], [])
        args, kwargs = adapt_arguments(command, arguments, args, opts)

        if self.command_preprocessor(command, name, arguments, args, kwargs):
            return
        value = command(self, *args, **kwargs)
        self.command_postprocessor(command, name, arguments, args, kwargs, value)

    def command_preprocessor(self, command, name, arguments, args, kwargs):
        """
        Redefine this method in the subclass to execute custom code
        before command gets executed.

        If returns True then command execution will be interrupted and
        command will not be executed.
        """
        pass

    def command_postprocessor(self, command, name, arguments, args, kwargs, value):
        """
        Redefine this method in the subclass to execute custom code
        after command gets executed.
        """
        pass

    def looks_like_command(self, text, body, name, arguments):
        """
        This hook is being called before any processing, but after it
        was determined that text looks like a command.

        If returns value other then None - then further processing will
        be interrupted and that value will be used to return from
        process_as_command.
        """
        pass

    def get_command(self, name):
        command = get_command(self.COMMAND_HOST, name)
        if not command:
            raise NoCommandError("Command does not exist", name=name)
        return command

    def list_commands(self):
        commands = list_commands(self.COMMAND_HOST)
        commands = dict(commands)
        return sorted(set(commands.itervalues()))

class Command(object):

    def __init__(self, handler, *names, **properties):
        self.handler = handler
        self.names = names

        # Automatically set all the properties passed to a constructor
        # by the command decorator.
        for key, value in properties.iteritems():
            setattr(self, key, value)

    def __call__(self, *args, **kwargs):
        try:
            return self.handler(*args, **kwargs)

        # This allows to use a shortcuted way of raising an exception
        # inside a handler. That is to raise a CommandError without
        # command or name attributes set. They will be set to a
        # corresponding values right here in case if they was not set by
        # the one who raised an exception.
        except CommandError, error:
            if not error.command and not error.name:
                raise CommandError(error.message, self)
            raise

        # This one is a little bit too wide, but as Python does not have
        # anything more constrained - there is no other choice. Take a
        # look here if command complains about invalid arguments while
        # they are ok.
        except TypeError:
            raise CommandError("Command received invalid arguments", self)

    def __repr__(self):
        return "<Command %s>" % ', '.join(self.names)

    def __cmp__(self, other):
        return cmp(self.first_name, other.first_name)

    @property
    def first_name(self):
        return self.names[0]

    @property
    def native_name(self):
        return self.handler.__name__

    def extract_documentation(self):
        """
        Extract handler's documentation which is a doc-string and
        transform it to a usable format.
        """
        return getdoc(self.handler)

    def extract_description(self):
        """
        Extract handler's description (which is a first line of the
        documentation). Try to keep them simple yet meaningful.
        """
        documentation = self.extract_documentation()
        return documentation.split('\n', 1)[0] if documentation else None

    def extract_specification(self):
        """
        Extract handler's arguments specification, as it was defined
        preserving their order.
        """
        names, var_args, var_kwargs, defaults = getargspec(self.handler)

        # Behavior of this code need to be checked. Might yield
        # incorrect results on some rare occasions.
        spec_args = names[:-len(defaults) if defaults else len(names)]
        spec_kwargs = list(zip(names[-len(defaults):], defaults)) if defaults else {}

        # Removing self from arguments specification. Command handler
        # should receive the processors as a first argument, which
        # should be self by the canonical means.
        if spec_args.pop(0) != 'self':
            raise DefinitionError("First argument must be self", self)

        return spec_args, spec_kwargs, var_args, var_kwargs

def command(*names, **properties):
    """
    A decorator for defining commands in a declarative way. Provides
    facilities for setting command's names and properties.

    Names should contain a set of names (aliases) by which the command
    can be reached. If no names are given - the the native name (the one
    extracted from the command handler) will be used.

    If native=True is given (default) and names is non-empty - then the
    native name of the command will be prepended in addition to the
    given names.

    If usage=True is given (default) - then command help will be
    appended with autogenerated usage info, based of the command handler
    arguments introspection.

    If source=True is given - then the first argument of the command
    will receive the source arguments, as a raw, unprocessed string. The
    further mapping of arguments and options will not be affected.

    If raw=True is given - then command considered to be raw and should
    define positional arguments only. If it defines only one positional
    argument - this argument will receive all the raw and unprocessed
    arguments. If the command defines more then one positional argument
    - then all the arguments except the last one will be processed
    normally; the last argument will get what is left after the
    processing as raw and unprocessed string.

    If empty=True is given - this will allow to call a raw command
    without arguments.

    If extra=True is given - then all the extra arguments passed to a
    command will be collected into a sequence and given to the last
    positional argument.

    If overlap=True is given - then all the extra arguments will be
    mapped as if they were values for the keyword arguments.

    If expand=True is given (default) - then short, one-letter options
    will be expanded to a verbose ones, based of the comparison of the
    first letter. If more then one option with the same first letter is
    given - then only first one will be used in the expansion.
    """
    names = list(names)

    native = properties.get('native', True)

    usage = properties.get('usage', True)
    source = properties.get('source', False)
    raw = properties.get('raw', False)
    empty = properties.get('empty', False)
    extra = properties.get('extra', False)
    overlap = properties.get('overlap', False)
    expand = properties.get('expand', True)

    if empty and not raw:
        raise DefinitionError("Empty option can be used only with raw commands")

    if extra and overlap:
        raise DefinitionError("Extra and overlap options can not be used together")

    properties = {
        'usage': usage,
        'source': source,
        'raw': raw,
        'extra': extra,
        'overlap': overlap,
        'empty': empty,
        'expand': expand
    }

    def decorator(handler):
        """
        Decorator which receives handler as a first argument and then
        wraps it in the command which then returns back.
        """
        command = Command(handler, *names, **properties)

        # Extract and inject a native name if either no other names are
        # specified or native property is enabled, while making
        # sure it is going to be the first one in the list.
        if not names or native:
            names.insert(0, command.native_name)
            command.names = tuple(names)

        return command

    # Workaround if we are getting called without parameters. Keep in
    # mind that in that case - first item in the names will be the
    # handler.
    if names and isinstance(names[0], FunctionType):
        return decorator(names.pop(0))

    return decorator

def doc(text):
    """
    This decorator is used to bind a documentation (a help) to a
    command.
    """
    def decorator(target):
        if isinstance(target, Command):
            target.handler.__doc__ = text
        else:
            target.__doc__ = text
        return target

    return decorator
