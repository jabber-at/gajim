# -*- coding:utf-8 -*-
## src/gajim.py
##
## Copyright (C) 2003-2012 Yann Leboulanger <asterix AT lagaule.org>
## Copyright (C) 2004-2005 Vincent Hanquez <tab AT snarc.org>
## Copyright (C) 2005 Alex Podaras <bigpod AT gmail.com>
##                    Norman Rasmussen <norman AT rasmussen.co.za>
##                    Stéphan Kochen <stephan AT kochen.nl>
## Copyright (C) 2005-2006 Dimitur Kirov <dkirov AT gmail.com>
##                         Alex Mauer <hawke AT hawkesnest.net>
## Copyright (C) 2005-2007 Travis Shirk <travis AT pobox.com>
##                         Nikos Kouremenos <kourem AT gmail.com>
## Copyright (C) 2006 Junglecow J <junglecow AT gmail.com>
##                    Stefan Bethge <stefan AT lanpartei.de>
## Copyright (C) 2006-2008 Jean-Marie Traissard <jim AT lapin.org>
## Copyright (C) 2007 Lukas Petrovicky <lukas AT petrovicky.net>
##                    James Newton <redshodan AT gmail.com>
## Copyright (C) 2007-2008 Brendan Taylor <whateley AT gmail.com>
##                         Julien Pivotto <roidelapluie AT gmail.com>
##                         Stephan Erb <steve-e AT h3c.de>
## Copyright (C) 2008 Jonathan Schleifer <js-gajim AT webkeks.org>
##
## This file is part of Gajim.
##
## Gajim is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published
## by the Free Software Foundation; version 3 only.
##
## Gajim is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Gajim. If not, see <http://www.gnu.org/licenses/>.
##

import os
import sys
import warnings

if os.name == 'nt':
    log_path = os.path.join(os.environ['APPDATA'], 'Gajim')
    if not os.path.exists(log_path):
        os.mkdir(log_path, 0700)
    log_file = os.path.join(log_path, 'gajim.log')
    fout = open(log_file, 'a')
    sys.stdout = fout
    sys.stderr = fout

    warnings.filterwarnings(action='ignore')

    if os.path.isdir('gtk'):
        # Used to create windows installer with GTK included
        paths = os.environ['PATH']
        list_ = paths.split(';')
        new_list = []
        for p in list_:
            if p.find('gtk') < 0 and p.find('GTK') < 0:
                new_list.append(p)
        new_list.insert(0, os.path.join(os.getcwd(), 'gtk', 'lib'))
        new_list.insert(0, os.path.join(os.getcwd(), 'gtk', 'bin'))
        os.environ['PATH'] = ';'.join(new_list)

from common import demandimport
demandimport.enable()
demandimport.ignore += ['gobject._gobject', 'libasyncns', 'i18n',
    'logging.NullHandler', 'dbus.glib', 'dbus.service',
    'command_system.implementation.standard',
    'command_system.implementation.execute', 'OpenSSL.SSL', 'OpenSSL.crypto',
    'common.sleepy', 'DLFCN', 'dl', 'xml.sax', 'xml.sax.handler', 'ic',
    'Crypto.PublicKey']

if os.name == 'nt':
    import locale
    import gettext
    APP = 'gajim'
    DIR = '../po'
    lang, enc = locale.getdefaultlocale()
    os.environ['LANG'] = lang
    gettext.bindtextdomain(APP, DIR)
    gettext.textdomain(APP)
    gettext.install(APP, DIR, unicode=True)

    locale.setlocale(locale.LC_ALL, '')
    import ctypes
    import ctypes.util
    libintl_path = ctypes.util.find_library('intl')
    if libintl_path == None:
        local_intl = os.path.join('gtk', 'bin', 'intl.dll')
        if os.path.exists(local_intl):
            libintl_path = local_intl
    if libintl_path == None:
        raise ImportError('intl.dll library not found')
    libintl = ctypes.cdll.LoadLibrary(libintl_path)
    libintl.bindtextdomain(APP, DIR)
    libintl.bind_textdomain_codeset(APP, 'UTF-8')

if os.name == 'nt':
    # needed for docutils
    sys.path.append('.')

from common import logging_helpers
logging_helpers.init('TERM' in os.environ)

import logging
# gajim.gui or gajim.gtk more appropriate ?
log = logging.getLogger('gajim.gajim')

import getopt
from common import i18n

def parseOpts():
    profile_ = ''
    config_path_ = None

    try:
        shortargs = 'hqvl:p:c:'
        # add gtk/gnome session option as gtk_get_option_group is not wrapped
        longargs = 'help quiet verbose loglevel= profile= config_path='
        longargs += ' class= name= screen= gtk-module= sync g-fatal-warnings'
        longargs += ' sm-client-id= sm-client-state-file= sm-disable'
        opts = getopt.getopt(sys.argv[1:], shortargs, longargs.split())[0]
    except getopt.error, msg1:
        print msg1
        print 'for help use --help'
        sys.exit(2)
    for o, a in opts:
        if o in ('-h', '--help'):
            print 'gajim [--help] [--quiet] [--verbose] ' + \
                '[--loglevel subsystem=level[,subsystem=level[...]]] ' + \
                '[--profile name] [--config-path]'
            sys.exit()
        elif o in ('-q', '--quiet'):
            logging_helpers.set_quiet()
        elif o in ('-v', '--verbose'):
            logging_helpers.set_verbose()
        elif o in ('-p', '--profile'): # gajim --profile name
            profile_ = a
        elif o in ('-l', '--loglevel'):
            logging_helpers.set_loglevels(a)
        elif o in ('-c', '--config-path'):
            config_path_ = a
    return profile_, config_path_

import locale
profile, config_path = parseOpts()
if config_path:
    config_path = unicode(config_path, locale.getpreferredencoding())
del parseOpts

profile = unicode(profile, locale.getpreferredencoding())

import common.configpaths
common.configpaths.gajimpaths.init(config_path)
del config_path
common.configpaths.gajimpaths.init_profile(profile)
del profile

if os.name == 'nt':
    plugins_locale_dir = os.path.join(common.configpaths.gajimpaths[
        'PLUGINS_USER'], 'locale').encode(locale.getpreferredencoding())
    libintl.bindtextdomain('gajim_plugins', plugins_locale_dir)
    libintl.bind_textdomain_codeset('gajim_plugins', 'UTF-8')

    class MyStderr(object):
        _file = None
        _error = None
        def write(self, text):
            fname = os.path.join(common.configpaths.gajimpaths.cache_root,
                os.path.split(sys.executable)[1]+'.log')
            if self._file is None and self._error is None:
                try:
                    self._file = open(fname, 'a')
                except Exception, details:
                    self._error = details
            if self._file is not None:
                self._file.write(text)
                self._file.flush()
        def flush(self):
            if self._file is not None:
                self._file.flush()

    sys.stderr = MyStderr()

# PyGTK2.10+ only throws a warning
warnings.filterwarnings('error', module='gtk')
try:
    import gobject
    gobject.set_prgname('gajim')
    import gtk
except Warning, msg2:
    if str(msg2) == 'could not open display':
        print >> sys.stderr, _('Gajim needs X server to run. Quiting...')
    else:
        print >> sys.stderr, _('importing PyGTK failed: %s') % str(msg2)
    sys.exit()
warnings.resetwarnings()


if os.name == 'nt':
    warnings.filterwarnings(action='ignore')

pritext = ''

from common import exceptions
try:
    from common import gajim
except exceptions.DatabaseMalformed:
    pritext = _('Database Error')
    sectext = _('The database file (%s) cannot be read. Try to repair it (see '
        'http://trac.gajim.org/wiki/DatabaseBackup) or remove it (all history '
        'will be lost).') % common.logger.LOG_DB_PATH
else:
    from common import dbus_support
    if dbus_support.supported:
        from music_track_listener import MusicTrackListener

    from ctypes import CDLL
    from ctypes.util import find_library
    import platform

    sysname = platform.system()
    if sysname in ('Linux', 'FreeBSD', 'OpenBSD', 'NetBSD'):
        libc = CDLL(find_library('c'))

        # The constant defined in <linux/prctl.h> which is used to set the name
        # of the process.
        PR_SET_NAME = 15

        if sysname == 'Linux':
            libc.prctl(PR_SET_NAME, 'gajim')
        elif sysname in ('FreeBSD', 'OpenBSD', 'NetBSD'):
            libc.setproctitle('gajim')

    if gtk.pygtk_version < (2, 16, 0):
        pritext = _('Gajim needs PyGTK 2.16 or above')
        sectext = _('Gajim needs PyGTK 2.16 or above to run. Quiting...')
    elif gtk.gtk_version < (2, 16, 0):
        pritext = _('Gajim needs GTK 2.16 or above')
        sectext = _('Gajim needs GTK 2.16 or above to run. Quiting...')

    from common import check_paths

    if os.name == 'nt':
        try:
            import winsound # windows-only built-in module for playing wav
            import win32api # do NOT remove. we req this module
        except Exception:
            pritext = _('Gajim needs pywin32 to run')
            sectext = _('Please make sure that Pywin32 is installed on your '
                'system. You can get it at %s') % \
                'http://sourceforge.net/project/showfiles.php?group_id=78018'

if pritext:
    dlg = gtk.MessageDialog(None,
            gtk.DIALOG_DESTROY_WITH_PARENT | gtk.DIALOG_MODAL,
            gtk.MESSAGE_ERROR, gtk.BUTTONS_OK, message_format = pritext)

    dlg.format_secondary_text(sectext)
    dlg.run()
    dlg.destroy()
    sys.exit()

del pritext

import gtkexcepthook

import signal
import gtkgui_helpers

gajimpaths = common.configpaths.gajimpaths

pid_filename = gajimpaths['PID_FILE']
config_filename = gajimpaths['CONFIG_FILE']

import traceback
import errno
import dialogs

def pid_alive():
    try:
        pf = open(pid_filename)
    except IOError:
        # probably file not found
        return False

    try:
        pid = int(pf.read().strip())
        pf.close()
    except Exception:
        traceback.print_exc()
        # PID file exists, but something happened trying to read PID
        # Could be 0.10 style empty PID file, so assume Gajim is running
        return True

    if os.name == 'nt':
        try:
            from ctypes import (windll, c_ulong, c_int, Structure, c_char)
            from ctypes import (POINTER, pointer, sizeof)
        except Exception:
            return True

        class PROCESSENTRY32(Structure):
            _fields_ = [
                    ('dwSize', c_ulong, ),
                    ('cntUsage', c_ulong, ),
                    ('th32ProcessID', c_ulong, ),
                    ('th32DefaultHeapID', c_ulong, ),
                    ('th32ModuleID', c_ulong, ),
                    ('cntThreads', c_ulong, ),
                    ('th32ParentProcessID', c_ulong, ),
                    ('pcPriClassBase', c_ulong, ),
                    ('dwFlags', c_ulong, ),
                    ('szExeFile', c_char*512, ),
                    ]

        kernel = windll.kernel32
        kernel.CreateToolhelp32Snapshot.argtypes = c_ulong, c_ulong,
        kernel.CreateToolhelp32Snapshot.restype = c_int
        kernel.Process32First.argtypes = c_int, POINTER(PROCESSENTRY32),
        kernel.Process32First.restype = c_int
        kernel.Process32Next.argtypes = c_int, POINTER(PROCESSENTRY32),
        kernel.Process32Next.restype = c_int

        def get_p(pid_):
            TH32CS_SNAPPROCESS = 2
            CreateToolhelp32Snapshot = kernel.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
            assert CreateToolhelp32Snapshot > 0, 'CreateToolhelp32Snapshot failed'
            pe32 = PROCESSENTRY32()
            pe32.dwSize = sizeof( PROCESSENTRY32 )
            f3 = kernel.Process32First(CreateToolhelp32Snapshot, pointer(pe32))
            while f3:
                if pe32.th32ProcessID == pid_:
                    return pe32.szExeFile
                f3 = kernel.Process32Next(CreateToolhelp32Snapshot, pointer(pe32))

        if get_p(pid) in ('python.exe', 'gajim.exe'):
            return True
        return False
    try:
        if not os.path.exists('/proc'):
            return True # no /proc, assume Gajim is running

        try:
            f1 = open('/proc/%d/cmdline'% pid)
        except IOError, e1:
            if e1.errno == errno.ENOENT:
                return False # file/pid does not exist
            raise

        n = f1.read().lower()
        f1.close()
        if n.find('gajim') < 0:
            return False
        return True # Running Gajim found at pid
    except Exception:
        traceback.print_exc()

    # If we are here, pidfile exists, but some unexpected error occured.
    # Assume Gajim is running.
    return True

if pid_alive():
    pix = gtkgui_helpers.get_icon_pixmap('gajim', 48)
    gtk.window_set_default_icon(pix) # set the icon to all newly opened wind
    pritext = _('Gajim is already running')
    sectext = _('Another instance of Gajim seems to be running\nRun anyway?')
    dialog = dialogs.YesNoDialog(pritext, sectext)
    dialog.popup()
    if dialog.run() != gtk.RESPONSE_YES:
        sys.exit(3)
    dialog.destroy()
    # run anyway, delete pid and useless global vars
    if os.path.exists(pid_filename):
        os.remove(pid_filename)
    del pix
    del pritext
    del sectext
    dialog.destroy()

# Create .gajim dir
pid_dir =  os.path.dirname(pid_filename)
if not os.path.exists(pid_dir):
    check_paths.create_path(pid_dir)
# Create pid file
try:
    f2 = open(pid_filename, 'w')
    f2.write(str(os.getpid()))
    f2.close()
except IOError, e2:
    dlg = dialogs.ErrorDialog(_('Disk Write Error'), str(e2))
    dlg.run()
    dlg.destroy()
    sys.exit()
del pid_dir

def on_exit():
    # delete pid file on normal exit
    if os.path.exists(pid_filename):
        os.remove(pid_filename)
    # Shutdown GUI and save config
    if hasattr(gajim.interface, 'roster') and gajim.interface.roster:
        gajim.interface.roster.prepare_quit()

import atexit
atexit.register(on_exit)

from gui_interface import Interface

if __name__ == '__main__':
    def sigint_cb(num, stack):
        sys.exit(5)
    # ^C exits the application normally to delete pid file
    signal.signal(signal.SIGINT, sigint_cb)

    log.info("Encodings: d:%s, fs:%s, p:%s", sys.getdefaultencoding(), \
            sys.getfilesystemencoding(), locale.getpreferredencoding())

    if os.name != 'nt':
        # Session Management support
        try:
            import gnome.ui
            raise ImportError
        except ImportError:
            pass
        else:
            def die_cb(dummy):
                gajim.interface.roster.quit_gtkgui_interface()
            gnome.program_init('gajim', gajim.version)
            cli = gnome.ui.master_client()
            cli.connect('die', die_cb)

            path_to_gajim_script = gtkgui_helpers.get_abspath_for_script(
                'gajim')

            if path_to_gajim_script:
                argv = [path_to_gajim_script]
                try:
                    cli.set_restart_command(argv)
                except TypeError:
                    # Fedora systems have a broken gnome-python wrapper for this
                    # function.
                    cli.set_restart_command(len(argv), argv)

    check_paths.check_and_possibly_create_paths()

    interface = Interface()
    interface.run()

    try:
        if os.name != 'nt':
            # This makes Gajim unusable under windows, and threads are used only
            # for GPG, so not under windows
            gtk.gdk.threads_init()
        gtk.main()
    except KeyboardInterrupt:
        print >> sys.stderr, 'KeyboardInterrupt'
