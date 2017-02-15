# -*- coding:utf-8 -*-
## src/atom_window.py
##
## Copyright (C) 2006 Tomasz Melcer <liori AT exroot.org>
## Copyright (C) 2006-2017 Yann Leboulanger <asterix AT lagaule.org>
## Copyright (C) 2007 Nikos Kouremenos <kourem AT gmail.com>
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


import gtk
import gobject

import gtkgui_helpers
from common import helpers
from common import i18n

class AtomWindow:
    window = None
    entries = []

    @classmethod
    def newAtomEntry(cls, entry):
        """
        Queue new entry, open window if there's no one opened
        """
        cls.entries.append(entry)

        if cls.window is None:
            cls.window = AtomWindow()
        else:
            cls.window.updateCounter()

    @classmethod
    def windowClosed(cls):
        cls.window = None

    def __init__(self):
        """
        Create new window... only if we have anything to show
        """
        assert len(self.__class__.entries)

        self.entry = None # the entry actually displayed

        self.xml = gtkgui_helpers.get_gtk_builder('atom_entry_window.ui')
        self.window = self.xml.get_object('atom_entry_window')
        for name in ('new_entry_label', 'feed_title_label',
        'feed_title_eventbox', 'feed_tagline_label', 'entry_title_label',
        'entry_title_eventbox', 'last_modified_label', 'close_button',
        'next_button'):
            self.__dict__[name] = self.xml.get_object(name)

        self.displayNextEntry()

        self.xml.connect_signals(self)
        self.window.show_all()

        self.entry_title_eventbox.add_events(gtk.gdk.BUTTON_PRESS_MASK)
        self.feed_title_eventbox.add_events(gtk.gdk.BUTTON_PRESS_MASK)

    def displayNextEntry(self):
        """
        Get next entry from the queue and display it in the window
        """
        assert len(self.__class__.entries)>0

        newentry = self.__class__.entries.pop(0)

        # fill the fields
        if newentry.feed_link is not None:
            self.feed_title_label.set_markup(
                u'<span foreground="blue" underline="single">%s</span>' % \
                gobject.markup_escape_text(newentry.feed_title))
        else:
            self.feed_title_label.set_markup(
                gobject.markup_escape_text(newentry.feed_title))

        self.feed_tagline_label.set_markup(
            u'<small>%s</small>' % \
            gobject.markup_escape_text(newentry.feed_tagline))

        if newentry.title:
            if newentry.uri is not None:
                self.entry_title_label.set_markup(
                    u'<span foreground="blue" underline="single">%s</span>' % \
                    gobject.markup_escape_text(newentry.title))
            else:
                self.entry_title_label.set_markup(
                    gobject.markup_escape_text(newentry.title))
        else:
            self.entry_title_label.set_markup('')

        self.last_modified_label.set_text(newentry.updated)

        # update the counters
        self.updateCounter()

        self.entry = newentry

    def updateCounter(self):
        """
        Display number of events on the top of window, sometimes it needs to be
        changed
        """
        count = len(self.__class__.entries)
        if count:
            self.new_entry_label.set_text(i18n.ngettext(
                'You have received new entries (and %d not displayed):',
                'You have received new entries (and %d not displayed):', count,
                count, count))
            self.next_button.set_sensitive(True)
        else:
            self.new_entry_label.set_text(_('You have received new entry:'))
            self.next_button.set_sensitive(False)

    def on_close_button_clicked(self, widget):
        self.window.destroy()
        self.windowClosed()

    def on_next_button_clicked(self, widget):
        self.displayNextEntry()

    def on_entry_title_eventbox_button_press_event(self, widget, event):
        #FIXME: make it using special gtk2.10 widget
        if event.button == 1:   # left click
            uri = self.entry.uri
            if uri is not None:
                helpers.launch_browser_mailer('url', uri)
        return True

    def on_feed_title_eventbox_button_press_event(self, widget, event):
        #FIXME: make it using special gtk2.10 widget
        if event.button == 1:   # left click
            uri = self.entry.feed_uri
            if uri is not None:
                helpers.launch_browser_mailer('url', uri)
        return True
