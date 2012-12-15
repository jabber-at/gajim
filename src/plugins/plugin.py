# -*- coding: utf-8 -*-

## This file is part of Gajim.
##
## Gajim is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published
## by the Free Software Foundation; version 3 only.
##
## Gajim is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Gajim.  If not, see <http://www.gnu.org/licenses/>.
##

'''
Base class for implementing plugin.

:author: Mateusz Biliński <mateusz@bilinski.it>
:since: 1st June 2008
:copyright: Copyright (2008) Mateusz Biliński <mateusz@bilinski.it>
:license: GPL
'''

import os
import locale

from common import gajim

from plugins.helpers import log_calls, log
from plugins.gui import GajimPluginConfigDialog

import logging
log = logging.getLogger('gajim.p.plugin')


class GajimPlugin(object):
    '''
    Base class for implementing Gajim plugins.
    '''
    name = u''
    '''
    Name of plugin.

    Will be shown in plugins management GUI.

    :type: unicode
    '''
    short_name = u''
    '''
    Short name of plugin.

    Used for quick indentification of plugin.

    :type: unicode

    :todo: decide whether we really need this one, because class name (with
            module name) can act as such short name
    '''
    version = u''
    '''
    Version of plugin.

    :type: unicode

    :todo: decide how to compare version between each other (which one
            is higher). Also rethink: do we really need to compare versions
            of plugins between each other? This would be only useful if we detect
            same plugin class but with different version and we want only the newest
            one to be active - is such policy good?
    '''
    description = u''
    '''
    Plugin description.

    :type: unicode

    :todo: should be allow rich text here (like HTML or reStructuredText)?
    '''
    authors = []
    '''
    Plugin authors.

    :type: [] of unicode

    :todo: should we decide on any particular format of author strings?
            Especially: should we force format of giving author's e-mail?
    '''
    homepage = u''
    '''
    URL to plug-in's homepage.

    :type: unicode

    :todo: should we check whether provided string is valid URI? (Maybe
    using 'property')
    '''
    gui_extension_points = {}
    '''
    Extension points that plugin wants to connect with and handlers to be used.

    Keys of this string should be strings with name of GUI extension point
    to handles. Values should be 2-element tuples with references to handling
    functions. First function will be used to connect plugin with extpoint,
    the second one to successfuly disconnect from it. Connecting takes places
    when plugin is activated and extpoint already exists, or when plugin is
    already activated but extpoint is being created (eg. chat window opens).
    Disconnecting takes place when plugin is deactivated and extpoint exists
    or when extpoint is destroyed and plugin is activate (eg. chat window
    closed).
    '''
    config_default_values = {}
    '''
    Default values for keys that should be stored in plug-in config.

    This dict is used when when someone calls for config option but it has not
    been set yet.

    Values are tuples: (default_value, option_description). The first one can
    be anything (this is the advantage of using shelve/pickle instead of
    custom-made     config I/O handling); the second one should be unicode (gettext
    can be used if need and/or translation is planned).

    :type: {} of 2-element tuples
    '''
    events_handlers = {}
    '''
    Dictionary with events handlers.

    Keys are event names. Values should be 2-element tuples with handler
    priority as first element and reference to handler function as second
    element. Priority is integer. See `ged` module for predefined priorities
    like `ged.PRECORE`, `ged.CORE` or `ged.POSTCORE`.

    :type: {} with 2-element tuples
    '''
    events = []
    '''
    New network event classes to be registered in Network Events Controller.

    :type: [] of `nec.NetworkIncomingEvent` or `nec.NetworkOutgoingEvent`
    subclasses.
    '''

    @log_calls('GajimPlugin')
    def __init__(self):
        self.config = GajimPluginConfig(self)
        '''
        Plug-in configuration dictionary.

        Automatically saved and loaded and plug-in (un)load.

        :type: `plugins.plugin.GajimPluginConfig`
        '''
        self.activatable = True
        self.available_text = ''
        self.load_config()
        self.config_dialog = GajimPluginConfigDialog(self)
        self.init()

    @log_calls('GajimPlugin')
    def save_config(self):
        self.config.save()

    @log_calls('GajimPlugin')
    def load_config(self):
        self.config.load()

    def __eq__(self, plugin):
        if self.short_name == plugin.short_name:
            return True

        return False

    def __ne__(self, plugin):
        if self.short_name != plugin.short_name:
            return True

        return False

    @log_calls('GajimPlugin')
    def local_file_path(self, file_name):
        return os.path.join(self.__path__, file_name)

    @log_calls('GajimPlugin')
    def init(self):
        pass

    @log_calls('GajimPlugin')
    def activate(self):
        pass

    @log_calls('GajimPlugin')
    def deactivate(self):
        pass

import cPickle

class GajimPluginConfig():
    @log_calls('GajimPluginConfig')
    def __init__(self, plugin):
        self.plugin = plugin
        self.FILE_PATH = os.path.join(gajim.PLUGINS_CONFIG_DIR,
            self.plugin.short_name).decode('utf-8').encode(
            locale.getpreferredencoding())
        self.data = {}

    @log_calls('GajimPluginConfig')
    def __getitem__(self, key):
        if not key in self.data:
            self.data[key] = self.plugin.config_default_values[key][0]
            self.save()

        return self.data[key]

    @log_calls('GajimPluginConfig')
    def __setitem__(self, key, value):
        self.data[key] = value
        self.save()

    @log_calls('GajimPluginConfig')
    def __delitem__(self, key):
        del self.data[key]
        self.save()

    @log_calls('GajimPluginConfig')
    def __contains__(self, key):
        return key in self.data

    def __iter__(self):
        for k in self.data.keys():
            yield k

    def keys(self):
        return self.data.keys()

    def items(self):
        return self.data.items()

    @log_calls('GajimPluginConfig')
    def save(self):
        fd = open(self.FILE_PATH, 'wb')
        cPickle.dump(self.data, fd)
        fd.close()

    @log_calls('GajimPluginConfig')
    def load(self):
        if os.path.isfile(self.FILE_PATH):
            fd = open(self.FILE_PATH, 'rb')
            try:
                self.data = cPickle.load(fd)
                fd.close()
            except:
                fd.close()
                try:
                    import shelve
                    s = shelve.open(self.FILE_PATH)
                    for (k, v) in s.iteritems():
                        self.data[k] = v
                    if not isinstance(self.data, dict):
                        raise GajimPluginException
                    s.close()
                    self.save()
                except:
                    log.warn('%s plugin config file not readable. Saving it as '
                        '%s and creating a new one' % (self.plugin.short_name,
                        self.FILE_PATH + '.bak'))
                    if os.path.exists(self.FILE_PATH + '.bak'):
                        os.remove(self.FILE_PATH + '.bak')
                    os.rename(self.FILE_PATH, self.FILE_PATH + '.bak')
                    self.data = {}
                    self.save()
        else:
            self.data = {}
            self.save()


class GajimPluginException(Exception):
    pass

class GajimPluginInitError(GajimPluginException):
    pass
