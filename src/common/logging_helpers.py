# -*- coding:utf-8 -*-
## src/common/logging_helpers.py
##
## Copyright (C) 2009 Bruno Tarquini <btarquini AT gmail.com>
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

import logging
import i18n

def parseLogLevel(arg):
    """
    Eiter numeric value or level name from logging module
    """
    if arg.isdigit():
        return int(arg)
    elif arg.isupper() and hasattr(logging, arg):
        return getattr(logging, arg)
    else:
        print _('%s is not a valid loglevel') % repr(arg)
        return 0

def parseLogTarget(arg):
    """
    [gajim.]c.x.y  ->  gajim.c.x.y
    .other_logger  ->  other_logger
    <None>         ->  gajim
    """
    arg = arg.lower()
    if not arg:
        return 'gajim'
    elif arg.startswith('.'):
        return arg[1:]
    elif arg.startswith('gajim'):
        return arg
    else:
        return 'gajim.' + arg

def parseAndSetLogLevels(arg):
    """
    [=]LOGLEVEL     ->  gajim=LOGLEVEL
    gajim=LOGLEVEL  ->  gajim=LOGLEVEL
    .other=10       ->  other=10
    .=10            ->  <nothing>
    c.x.y=c.z=20    ->  gajim.c.x.y=20
                        gajim.c.z=20
    gajim=10,c.x=20 ->  gajim=10
                        gajim.c.x=20
    """
    for directive in arg.split(','):
        directive = directive.strip()
        if not directive:
            continue
        if '=' not in directive:
            directive = '=' + directive
        targets, level = directive.rsplit('=', 1)
        level = parseLogLevel(level.strip())
        for target in targets.split('='):
            target = parseLogTarget(target.strip())
            if target:
                logging.getLogger(target).setLevel(level)
                print "Logger %s level set to %d" % (target, level)


class colors:
    NONE         = chr(27) + "[0m"
    BLACk        = chr(27) + "[30m"
    RED          = chr(27) + "[31m"
    GREEN        = chr(27) + "[32m"
    BROWN        = chr(27) + "[33m"
    BLUE         = chr(27) + "[34m"
    MAGENTA      = chr(27) + "[35m"
    CYAN         = chr(27) + "[36m"
    LIGHT_GRAY   = chr(27) + "[37m"
    DARK_GRAY    = chr(27) + "[30;1m"
    BRIGHT_RED   = chr(27) + "[31;1m"
    BRIGHT_GREEN = chr(27) + "[32;1m"
    YELLOW       = chr(27) + "[33;1m"
    BRIGHT_BLUE  = chr(27) + "[34;1m"
    PURPLE       = chr(27) + "[35;1m"
    BRIGHT_CYAN  = chr(27) + "[36;1m"
    WHITE        = chr(27) + "[37;1m"

def colorize(text, color):
    return color + text + colors.NONE

class FancyFormatter(logging.Formatter):
    """
    An eye-candy formatter with colors
    """
    colors_mapping = {
            'DEBUG':                colors.BLUE,
            'INFO':                colors.GREEN,
            'WARNING':      colors.BROWN,
            'ERROR':                colors.RED,
            'CRITICAL':     colors.BRIGHT_RED,
    }

    def __init__(self, fmt, datefmt=None, use_color=False):
        logging.Formatter.__init__(self, fmt, datefmt)
        self.use_color = use_color

    def formatTime(self, record, datefmt=None):
        f = logging.Formatter.formatTime(self, record, datefmt)
        if self.use_color:
            f = colorize(f, colors.DARK_GRAY)
        return f

    def format(self, record):
        level = record.levelname
        record.levelname = '(%s)' % level[0]

        if self.use_color:
            c = FancyFormatter.colors_mapping.get(level, '')
            record.levelname = colorize(record.levelname, c)
            record.name = colorize(record.name, colors.CYAN)
        else:
            record.name += ':'

        return logging.Formatter.format(self, record)


def init(use_color=False):
    """
    Iinitialize the logging system
    """
    consoleloghandler = logging.StreamHandler()
    consoleloghandler.setFormatter(
            FancyFormatter(
                    '%(asctime)s %(levelname)s %(name)s %(message)s',
                    '%H:%M:%S',
                    use_color
            )
    )

    # fake the root logger so we have 'gajim' root name instead of 'root'
    root_log = logging.getLogger('gajim')
    root_log.setLevel(logging.WARNING)
    root_log.addHandler(consoleloghandler)
    root_log.propagate = False

def set_loglevels(loglevels_string):
    parseAndSetLogLevels(loglevels_string)

def set_verbose():
    parseAndSetLogLevels('gajim=1')

def set_quiet():
    parseAndSetLogLevels('gajim=CRITICAL')


# tests
if __name__ == '__main__':
    init(use_color=True)

    set_loglevels('gajim.c=DEBUG,INFO')

    log = logging.getLogger('gajim')
    log.debug('debug')
    log.info('info')
    log.warn('warn')
    log.error('error')
    log.critical('critical')

    log = logging.getLogger('gajim.c.x.dispatcher')
    log.debug('debug')
    log.info('info')
    log.warn('warn')
    log.error('error')
    log.critical('critical')
