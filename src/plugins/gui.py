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
GUI classes related to plug-in management.

:author: Mateusz Biliński <mateusz@bilinski.it>
:since: 6th June 2008
:copyright: Copyright (2008) Mateusz Biliński <mateusz@bilinski.it>
:license: GPL
'''

__all__ = ['PluginsWindow']

import pango
import gtk, gobject

import gtkgui_helpers
from dialogs import WarningDialog, YesNoDialog, ArchiveChooserDialog
from common import gajim
from plugins.helpers import log_calls, log
from plugins.helpers import GajimPluginActivateException
from common.exceptions import PluginsystemError

class PluginsWindow(object):
    '''Class for Plugins window'''

    @log_calls('PluginsWindow')
    def __init__(self):
        '''Initialize Plugins window'''
        self.xml = gtkgui_helpers.get_gtk_builder('plugins_window.ui')
        self.window = self.xml.get_object('plugins_window')
        self.window.set_transient_for(gajim.interface.roster.window)

        widgets_to_extract = ('plugins_notebook', 'plugin_name_label',
            'plugin_version_label', 'plugin_authors_label',
            'plugin_homepage_linkbutton', 'plugin_description_textview',
            'uninstall_plugin_button', 'configure_plugin_button',
            'installed_plugins_treeview')

        for widget_name in widgets_to_extract:
            setattr(self, widget_name, self.xml.get_object(widget_name))

        attr_list = pango.AttrList()
        attr_list.insert(pango.AttrWeight(pango.WEIGHT_BOLD, 0, -1))
        self.plugin_name_label.set_attributes(attr_list)

        self.installed_plugins_model = gtk.ListStore(gobject.TYPE_PYOBJECT,
            gobject.TYPE_STRING, gobject.TYPE_BOOLEAN)
        self.installed_plugins_treeview.set_model(self.installed_plugins_model)
        self.installed_plugins_treeview.set_rules_hint(True)

        renderer = gtk.CellRendererText()
        col = gtk.TreeViewColumn(_('Plugin'), renderer, text=1)
        self.installed_plugins_treeview.append_column(col)

        renderer = gtk.CellRendererToggle()
        renderer.set_property('activatable', True)
        renderer.connect('toggled', self.installed_plugins_toggled_cb)
        col = gtk.TreeViewColumn(_('Active'), renderer, active=2)
        self.installed_plugins_treeview.append_column(col)

        # connect signal for selection change
        selection = self.installed_plugins_treeview.get_selection()
        selection.connect('changed',
            self.installed_plugins_treeview_selection_changed)
        selection.set_mode(gtk.SELECTION_SINGLE)

        self._clear_installed_plugin_info()

        self.fill_installed_plugins_model()

        self.xml.connect_signals(self)

        self.plugins_notebook.set_current_page(0)

        self.window.show_all()
        gtkgui_helpers.possibly_move_window_in_current_desktop(self.window)

    @log_calls('PluginsWindow')
    def installed_plugins_treeview_selection_changed(self, treeview_selection):
        model, iter = treeview_selection.get_selected()
        if iter:
            plugin = model.get_value(iter, 0)
            plugin_name = model.get_value(iter, 1)
            is_active = model.get_value(iter, 2)

            self._display_installed_plugin_info(plugin)
        else:
            self._clear_installed_plugin_info()

    def _display_installed_plugin_info(self, plugin):
        self.plugin_name_label.set_text(plugin.name)
        self.plugin_version_label.set_text(plugin.version)
        self.plugin_authors_label.set_text(plugin.authors)
        label = self.plugin_homepage_linkbutton.get_children()[0]
        label.set_ellipsize(pango.ELLIPSIZE_END)
        self.plugin_homepage_linkbutton.set_uri(plugin.homepage)
        self.plugin_homepage_linkbutton.set_label(plugin.homepage)
        self.plugin_homepage_linkbutton.set_property('sensitive', True)

        desc_textbuffer = self.plugin_description_textview.get_buffer()
        from plugins.plugins_i18n import _
        desc_textbuffer.set_text(_(plugin.description))
        self.plugin_description_textview.set_property('sensitive', True)
        self.uninstall_plugin_button.set_property('sensitive',
                                    gajim.PLUGINS_DIRS[1] in plugin.__path__)
        if plugin.config_dialog is None:
            self.configure_plugin_button.set_property('sensitive', False)
        else:
            self.configure_plugin_button.set_property('sensitive', True)

    def _clear_installed_plugin_info(self):
        self.plugin_name_label.set_text('')
        self.plugin_version_label.set_text('')
        self.plugin_authors_label.set_text('')
        self.plugin_homepage_linkbutton.set_uri('')
        self.plugin_homepage_linkbutton.set_label('')
        self.plugin_homepage_linkbutton.set_property('sensitive', False)

        desc_textbuffer = self.plugin_description_textview.get_buffer()
        desc_textbuffer.set_text('')
        self.plugin_description_textview.set_property('sensitive', False)
        self.uninstall_plugin_button.set_property('sensitive', False)
        self.configure_plugin_button.set_property('sensitive', False)

    @log_calls('PluginsWindow')
    def fill_installed_plugins_model(self):
        pm = gajim.plugin_manager
        self.installed_plugins_model.clear()
        self.installed_plugins_model.set_sort_column_id(1, gtk.SORT_ASCENDING)

        for plugin in pm.plugins:
            self.installed_plugins_model.append([plugin, plugin.name,
                plugin.active])

    @log_calls('PluginsWindow')
    def installed_plugins_toggled_cb(self, cell, path):
        is_active = self.installed_plugins_model[path][2]
        plugin = self.installed_plugins_model[path][0]

        if is_active:
            gajim.plugin_manager.deactivate_plugin(plugin)
        else:
            try:
                gajim.plugin_manager.activate_plugin(plugin)
            except GajimPluginActivateException, e:
                WarningDialog(_('Plugin failed'), str(e))
                return

        self.installed_plugins_model[path][2] = not is_active

    @log_calls('PluginsWindow')
    def on_plugins_window_destroy(self, widget):
        '''Close window'''
        del gajim.interface.instances['plugins']

    @log_calls('PluginsWindow')
    def on_close_button_clicked(self, widget):
        self.window.destroy()

    @log_calls('PluginsWindow')
    def on_configure_plugin_button_clicked(self, widget):
        #log.debug('widget: %s'%(widget))
        selection = self.installed_plugins_treeview.get_selection()
        model, iter = selection.get_selected()
        if iter:
            plugin = model.get_value(iter, 0)
            plugin_name = model.get_value(iter, 1)
            is_active = model.get_value(iter, 2)


            result = plugin.config_dialog.run(self.window)

        else:
            # No plugin selected. this should never be reached. As configure
            # plugin button should only be clickable when plugin is selected.
            # XXX: maybe throw exception here?
            pass

    @log_calls('PluginsWindow')
    def on_uninstall_plugin_button_clicked(self, widget):
        selection = self.installed_plugins_treeview.get_selection()
        model, iter = selection.get_selected()
        if iter:
            plugin = model.get_value(iter, 0)
            plugin_name = model.get_value(iter, 1).decode('utf-8')
            is_active = model.get_value(iter, 2)
            try:
                gajim.plugin_manager.remove_plugin(plugin)
            except PluginsystemError, e:
                WarningDialog(_('Unable to properly remove the plugin'),
                    str(e), self.window)
                return
            model.remove(iter)

    @log_calls('PluginsWindow')
    def on_install_plugin_button_clicked(self, widget):
        def show_warn_dialog():
            text = _('Archive is malformed')
            dialog = WarningDialog(text, '', transient_for=self.window)
            dialog.set_modal(False)
            dialog.popup()

        def _on_plugin_exists(zip_filename):
            def on_yes(is_checked):
                plugin = gajim.plugin_manager.install_from_zip(zip_filename,
                    True)
                if not plugin:
                    show_warn_dialog()
                    return
                model = self.installed_plugins_model

                for row in xrange(len(model)):
                    if plugin == model[row][0]:
                        model.remove(model.get_iter((row, 0)))
                        break

                iter_ = model.append([plugin, plugin.name, False])
                sel = self.installed_plugins_treeview.get_selection()
                sel.select_iter(iter_)

            YesNoDialog(_('Plugin already exists'), sectext=_('Overwrite?'),
                on_response_yes=on_yes)

        def _try_install(zip_filename):
            try:
                plugin = gajim.plugin_manager.install_from_zip(zip_filename)
            except PluginsystemError, er_type:
                error_text = str(er_type)
                if error_text == _('Plugin already exists'):
                    _on_plugin_exists(zip_filename)
                    return

                WarningDialog(error_text, '"%s"' % zip_filename, self.window)
                return
            if not plugin:
                show_warn_dialog()
                return
            model = self.installed_plugins_model
            iter_ = model.append([plugin, plugin.name, False])
            sel = self.installed_plugins_treeview.get_selection()
            sel.select_iter(iter_)

        self.dialog = ArchiveChooserDialog(on_response_ok=_try_install)


class GajimPluginConfigDialog(gtk.Dialog):

    @log_calls('GajimPluginConfigDialog')
    def __init__(self, plugin, **kwargs):
        gtk.Dialog.__init__(self, '%s %s'%(plugin.name, _('Configuration')),
                                                                    **kwargs)
        self.plugin = plugin
        self.add_button('gtk-close', gtk.RESPONSE_CLOSE)

        self.child.set_spacing(3)

        self.init()

    @log_calls('GajimPluginConfigDialog')
    def run(self, parent=None):
        self.set_transient_for(parent)
        self.on_run()
        self.show_all()
        result =  super(GajimPluginConfigDialog, self).run()
        self.hide()
        return result

    def init(self):
        pass

    def on_run(self):
        pass
