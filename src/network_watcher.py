# -*- coding: utf-8 -*-
## src/network_watcher.py
##
## Copyright (C) 2006 Jeffrey C. Ollie <jeff AT ocjtech.us>
##                    Nikos Kouremenos <kourem AT gmail.com>
##                    Stefan Bethge <stefan AT lanpartei.de>
## Copyright (C) 2006-2017 Yann Leboulanger <asterix AT lagaule.org>
## Copyright (C) 2017 Jörg Sommer <joerg@alea.gnuu.de>
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

from common import gajim

def update_accounts(connection_is_up):
    if connection_is_up:
        for connection in gajim.connections.itervalues():
            if gajim.config.get_per('accounts', connection.name,
            'listen_to_network_manager') and connection.time_to_reconnect:
                connection._reconnect()
    else:
        for connection in gajim.connections.itervalues():
            if gajim.config.get_per('accounts', connection.name,
            'listen_to_network_manager') and connection.connected > 1:
                connection._disconnectedReconnCB()

supported = False

from common import dbus_support

if dbus_support.supported:
    import dbus

    from common.dbus_support import system_bus

    bus = system_bus.bus()

    if 'org.freedesktop.NetworkManager' in bus.list_names():
        try:
            """
            For Network Manager 0.7 - 0.9
            """
            nm_object = bus.get_object('org.freedesktop.NetworkManager',
                                       '/org/freedesktop/NetworkManager')
            props = dbus.Interface(nm_object, "org.freedesktop.DBus.Properties")

            bus.add_signal_receiver(lambda state: update_accounts(connection_is_up = state == 70),
                    'StateChanged',
                    'org.freedesktop.NetworkManager',
                    'org.freedesktop.NetworkManager',
                    '/org/freedesktop/NetworkManager')
            supported = True

        except dbus.DBusException:
            try:
                """
                For Network Manager 0.6
                """
                supported = True

                bus.add_signal_receiver(lambda *args: update_accounts(connection_is_up = False),
                        'DeviceNoLongerActive',
                        'org.freedesktop.NetworkManager',
                        'org.freedesktop.NetworkManager',
                        '/org/freedesktop/NetworkManager')

                bus.add_signal_receiver(lambda *args: update_accounts(connection_is_up = True),
                        'DeviceNowActive',
                        'org.freedesktop.NetworkManager',
                        'org.freedesktop.NetworkManager',
                        '/org/freedesktop/NetworkManager')
            except Exception:
                pass
    elif 'org.freedesktop.network1' in bus.list_names():
        """
        For systemd-networkd
        """
        def state_changed(sender, data, junk):
            if 'OperationalState' in data:
                update_accounts(connection_is_up = data['OperationalState'] == 'routable')

        bus.add_signal_receiver(state_changed, 'PropertiesChanged',
                path = '/org/freedesktop/network1')
        supported = True
