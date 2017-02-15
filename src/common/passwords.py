# -*- coding:utf-8 -*-
## src/common/passwords.py
##
## Copyright (C) 2006 Gustavo J. A. M. Carneiro <gjcarneiro AT gmail.com>
##                    Nikos Kouremenos <kourem AT gmail.com>
## Copyright (C) 2006-2017 Yann Leboulanger <asterix AT lagaule.org>
## Copyright (C) 2007 Jean-Marie Traissard <jim AT lapin.org>
##                    Julien Pivotto <roidelapluie AT gmail.com>
## Copyright (C) 2008 Stephan Erb <steve-e AT h3c.de>
## Copyright (c) 2009 Thorsten Glaser <t.glaser AT tarent.de>
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

__all__ = ['get_password', 'save_password']

import os
import logging
import warnings
from common import gajim
from common import kwalletbinding

log = logging.getLogger('gajim.password')

if os.name == 'nt':
    try:
        import keyring
    except ImportError:
        log.exception(
            'python-keyring missing, falling back to plaintext storage')

USER_HAS_GNOMEKEYRING = False
USER_USES_GNOMEKEYRING = False
USER_HAS_KWALLETCLI = False
gnomekeyring = None

class PasswordStorage(object):
    def get_password(self, account_name):
        raise NotImplementedError
    def save_password(self, account_name, password):
        raise NotImplementedError


class SimplePasswordStorage(PasswordStorage):
    def get_password(self, account_name):
        passwd = gajim.config.get_per('accounts', account_name, 'password')
        if passwd and (passwd.startswith('gnomekeyring:') or passwd.startswith('libsecret:') or \
        passwd == '<kwallet>' or passwd.startswith('winvault:')):
            # this is not a real password
            return None
        else:
            return passwd

    def save_password(self, account_name, password):
        gajim.config.set_per('accounts', account_name, 'password', password)
        if account_name in gajim.connections:
            gajim.connections[account_name].password = password


class GnomePasswordStorage(PasswordStorage):
    def __init__(self):
        self.keyring = gnomekeyring.get_default_keyring_sync()
        if self.keyring is None:
            self.keyring = 'login'
        try:
            gnomekeyring.create_sync(self.keyring, None)
        except gnomekeyring.AlreadyExistsError:
            pass

    def get_password(self, account_name):
        conf = gajim.config.get_per('accounts', account_name, 'password')
        if conf is None or conf == '<kwallet>':
            return None
        if not (conf.startswith('gnomekeyring:') or conf.startswith('libsecret')):
            password = conf
            ## migrate the password over to keyring
            try:
                self.save_password(account_name, password)
            except gnomekeyring.NoKeyringDaemonError:
                ## no keyring daemon: in the future, stop using it
                set_storage(SimplePasswordStorage())
            return password
        try:
            server = gajim.config.get_per('accounts', account_name, 'hostname')
            user = gajim.config.get_per('accounts', account_name, 'name')
            attributes1 = dict(server=str(server), user=str(user), protocol='xmpp')
            attributes2 = dict(account_name=str(account_name), gajim=1)
            try:
                items = gnomekeyring.find_items_sync(
                        gnomekeyring.ITEM_NETWORK_PASSWORD, attributes1)
            except gnomekeyring.Error:
                try:
                    items = gnomekeyring.find_items_sync(
                            gnomekeyring.ITEM_GENERIC_SECRET, attributes2)
                    if items:
                        # We found an old item, move it to new way of storing
                        password = items[0].secret
                        self.save_password(account_name, password)
                        gnomekeyring.item_delete_sync(items[0].keyring,
                                int(items[0].item_id))
                except gnomekeyring.Error:
                    items = []
            if len(items) > 1:
                warnings.warn("multiple gnome keyring items found for account %s;"
                              " trying to use the first one..."
                              % account_name)
            if items:
                return items[0].secret
            else:
                return None
        except gnomekeyring.DeniedError:
            return None
        except gnomekeyring.NoKeyringDaemonError:
            ## no keyring daemon: in the future, stop using it
            set_storage(SimplePasswordStorage())
            return None

    def save_password(self, account_name, password, update=True):
        server = gajim.config.get_per('accounts', account_name, 'hostname')
        user = gajim.config.get_per('accounts', account_name, 'name')
        display_name = _('XMPP account %s@%s') % (user, server)
        attributes1 = dict(server=str(server), user=str(user), protocol='xmpp')
        if password is None:
            password = str()
        try:
            auth_token = gnomekeyring.item_create_sync(
                self.keyring, gnomekeyring.ITEM_NETWORK_PASSWORD, display_name,
                attributes1, password, update)
        except (gnomekeyring.DeniedError, gnomekeyring.CancelledError):
            set_storage(SimplePasswordStorage())
            storage.save_password(account_name, password)
            return
        gajim.config.set_per('accounts', account_name, 'password',
            'gnomekeyring:')
        if account_name in gajim.connections:
            gajim.connections[account_name].password = password

class KWalletPasswordStorage(PasswordStorage):
    def get_password(self, account_name):
        pw = gajim.config.get_per('accounts', account_name, 'password')
        if not pw or pw.startswith('gnomekeyring:'):
            # unset, empty or not ours
            return None
        if pw != '<kwallet>':
            # migrate the password
            if kwalletbinding.kwallet_put('gajim', account_name, pw):
                gajim.config.set_per('accounts', account_name, 'password',
                 '<kwallet>')
            else:
                # stop using the KDE Wallet
                set_storage(SimplePasswordStorage())
            return pw
        pw = kwalletbinding.kwallet_get('gajim', account_name)
        if pw is None:
            # stop using the KDE Wallet
            set_storage(SimplePasswordStorage())
        if not pw:
            # False, None, or the empty string
            return None
        return pw

    def save_password(self, account_name, password):
        if not kwalletbinding.kwallet_put('gajim', account_name, password):
            # stop using the KDE Wallet
            set_storage(SimplePasswordStorage())
            storage.save_password(account_name, password)
            return
        pwtoken = '<kwallet>'
        if not password:
            # no sense in looking up the empty string in the KWallet
            pwtoken = ''
        gajim.config.set_per('accounts', account_name, 'password', pwtoken)
        if account_name in gajim.connections:
            gajim.connections[account_name].password = password


class SecretWindowsPasswordStorage(PasswordStorage):
    """ Windows Keyring """

    def __init__(self):
        self.win_keyring = keyring.get_keyring()

    def save_password(self, account_name, password):
        try:
            self.win_keyring.set_password('gajim', account_name, password)
            gajim.config.set_per(
                'accounts', account_name, 'password', 'winvault:')
        except:
            log.exception('error:')
            set_storage(SimplePasswordStorage())
            storage.save_password(account_name, password)

    def get_password(self, account_name):
        conf = gajim.config.get_per('accounts', account_name, 'password')
        if conf is None:
            return None
        if not conf.startswith('winvault:'):
            password = conf
            # migrate the password over to keyring
            self.save_password(account_name, password)
            return password
        return self.win_keyring.get_password('gajim', account_name)


storage = None
def get_storage():
    global storage
    if storage is None: # None is only in first time get_storage is called
        if gajim.config.get('use_gnomekeyring'):
            global gnomekeyring
            try:
                gnomekeyring = __import__('gnomekeyring')
            except ImportError:
                pass
            else:
                global USER_HAS_GNOMEKEYRING
                global USER_USES_GNOMEKEYRING
                USER_HAS_GNOMEKEYRING = True
                if gnomekeyring.is_available():
                    USER_USES_GNOMEKEYRING = True
                else:
                    USER_USES_GNOMEKEYRING = False
        if USER_USES_GNOMEKEYRING:
            try:
                storage = GnomePasswordStorage()
            except (gnomekeyring.NoKeyringDaemonError, gnomekeyring.DeniedError,
            gnomekeyring.CancelledError):
                storage = None
        if storage is None:
            if gajim.config.get('use_kwalletcli'):
                global USER_HAS_KWALLETCLI
                if kwalletbinding.kwallet_available():
                    USER_HAS_KWALLETCLI = True
                if USER_HAS_KWALLETCLI:
                    storage = KWalletPasswordStorage()
        if storage is None and os.name == 'nt':
            if gajim.config.get('use_winvault'):
                try:
                    storage = SecretWindowsPasswordStorage()
                except:
                    log.exception('error:')
                    storage = None
        if storage is None:
            storage = SimplePasswordStorage()
    return storage

def set_storage(storage_):
    global storage
    storage = storage_


def get_password(account_name):
    return get_storage().get_password(account_name)

def save_password(account_name, password):
    return get_storage().save_password(account_name, password)
