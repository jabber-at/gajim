##      common/zeroconf/client_zeroconf.py
##
## Copyright (C) 2006 Stefan Bethge <stefan@lanpartei.de>
##                              2006 Dimitur Kirov <dkirov@gmail.com>
##
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
from common import gajim
import nbxmpp
from nbxmpp.idlequeue import IdleObject
from nbxmpp import dispatcher_nb, simplexml
from nbxmpp.plugin import *
from nbxmpp.simplexml import ustr
from nbxmpp.transports_nb import DATA_RECEIVED, DATA_SENT, DATA_ERROR
from common.zeroconf import zeroconf

from nbxmpp.protocol import *
import socket
import errno
import sys
import os
import string
from random import Random

import logging
log = logging.getLogger('gajim.c.z.client_zeroconf')

from common.zeroconf import roster_zeroconf

MAX_BUFF_LEN = 65536
TYPE_SERVER, TYPE_CLIENT = range(2)

# wait XX sec to establish a connection
CONNECT_TIMEOUT_SECONDS = 10

# after XX sec with no activity, close the stream
ACTIVITY_TIMEOUT_SECONDS = 30

class ZeroconfListener(IdleObject):
    def __init__(self, port, conn_holder):
        """
        Handle all incomming connections on ('0.0.0.0', port)
        """
        self.port = port
        self.queue_idx = -1
        #~ self.queue = None
        self.started = False
        self._sock = None
        self.fd = -1
        self.caller = conn_holder.caller
        self.conn_holder = conn_holder

    def bind(self):
        flags = socket.AI_PASSIVE
        if hasattr(socket, 'AI_ADDRCONFIG'):
            flags |= socket.AI_ADDRCONFIG
        ai = socket.getaddrinfo(None, self.port, socket.AF_UNSPEC,
            socket.SOCK_STREAM, 0, flags)[0]
        self._serv = socket.socket(ai[0], ai[1])
        self._serv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._serv.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        self._serv.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        if os.name == 'nt':
            ver = os.sys.getwindowsversion()
            if (ver[3], ver[0]) == (2, 6): # Win Vista +
                # 47 is socket.IPPROTO_IPV6
                # 27 is socket.IPV6_V6ONLY under windows, but not defined ...
                self._serv.setsockopt(41, 27, 0)
        # will fail when port is busy, or we don't have rights to bind
        try:
            self._serv.bind((ai[4][0], self.port))
        except Exception:
            # unable to bind, show error dialog
            return None
        self._serv.listen(socket.SOMAXCONN)
        self._serv.setblocking(False)
        self.fd = self._serv.fileno()
        gajim.idlequeue.plug_idle(self, False, True)
        self.started = True

    def pollend(self):
        """
        Called when we stop listening on (host, port)
        """
        self.disconnect()

    def pollin(self):
        """
        Accept a new incomming connection and notify queue
        """
        sock = self.accept_conn()
        # loop through roster to find who has connected to us
        from_jid = None
        ipaddr = sock[1][0]
        for jid in self.conn_holder.getRoster().keys():
            entry = self.conn_holder.getRoster().getItem(jid)
            for address in entry['addresses']:
                if (address['address'] == ipaddr):
                    from_jid = jid
                    break
        P2PClient(sock[0], [{'host': ipaddr, 'address': ipaddr, 'port': sock[1][1]}], self.conn_holder, [], from_jid)

    def disconnect(self, message=''):
        """
        Free all resources, we are not listening anymore
        """
        log.info('Disconnecting ZeroconfListener: %s' % message)
        gajim.idlequeue.remove_timeout(self.fd)
        gajim.idlequeue.unplug_idle(self.fd)
        self.fd = -1
        self.started = False
        try:
            self._serv.close()
        except socket.error:
            pass
        self.conn_holder.kill_all_connections()

    def accept_conn(self):
        """
        Accept a new incoming connection
        """
        _sock = self._serv.accept()
        _sock[0].setblocking(False)
        return _sock

class P2PClient(IdleObject):
    def __init__(self, _sock, addresses, conn_holder, stanzaqueue, to=None,
    on_ok=None, on_not_ok=None):
        self._owner = self
        self.Namespace = 'jabber:client'
        self.protocol_type = 'XMPP'
        self.defaultNamespace = self.Namespace
        self._component = 0
        self._registered_name = None
        self._caller = conn_holder.caller
        self.conn_holder = conn_holder
        self.stanzaqueue = stanzaqueue
        self.to = to
        #self.Server = addresses[0]['host']
        self.on_ok = on_ok
        self.on_not_ok = on_not_ok
        self.Connection = None
        self.sock_hash = None
        if _sock:
            self.sock_type = TYPE_SERVER
        else:
            self.sock_type = TYPE_CLIENT
        self.fd = -1
        conn = P2PConnection('', _sock, addresses, self._caller,
            self.on_connect, self)
        self.Server = conn.host  # set Server to the last host name / address tried
        if not self.conn_holder:
            # An error occured, disconnect() has been called
            if on_not_ok:
                on_not_ok('Connection to host could not be established.')
            return
        self.sock_hash = conn._sock.__hash__
        self.fd = conn.fd
        self.conn_holder.add_connection(self, self.Server, conn.port, self.to)
        # count messages in queue
        for val in self.stanzaqueue:
            stanza, is_message = val
            if is_message:
                if self.fd == -1:
                    if on_not_ok:
                        on_not_ok(
                            'Connection to host could not be established.')
                    return
                thread_id = stanza.getThread()
                id_ = stanza.getID()
                if not id_:
                    id_ = self.Dispatcher.getAnID()
                if self.conn_holder.ids_of_awaiting_messages.has_key(self.fd):
                    self.conn_holder.ids_of_awaiting_messages[self.fd].append((
                        id_, thread_id))
                else:
                    self.conn_holder.ids_of_awaiting_messages[self.fd] = [(id_,
                        thread_id)]

        self.on_responses = {}

    def add_stanza(self, stanza, is_message=False):
        if self.Connection:
            if self.Connection.state == -1:
                return False
            self.send(stanza, is_message)
        else:
            self.stanzaqueue.append((stanza, is_message))

        if is_message:
            thread_id = stanza.getThread()
            id_ = stanza.getID()
            if not id_:
                id_ = self.Dispatcher.getAnID()
            if self.conn_holder.ids_of_awaiting_messages.has_key(self.fd):
                self.conn_holder.ids_of_awaiting_messages[self.fd].append((id_,
                    thread_id))
            else:
                self.conn_holder.ids_of_awaiting_messages[self.fd] = [(id_,
                    thread_id)]

        return True

    def on_message_sent(self, connection_id):
        id_, thread_id = \
            self.conn_holder.ids_of_awaiting_messages[connection_id].pop(0)
        if self.on_ok:
            self.on_ok(id_)
            # use on_ok only on first message. For others it's called in
            # ClientZeroconf
            self.on_ok = None

    def on_connect(self, conn):
        self.Connection = conn
        self.Connection.PlugIn(self)
        dispatcher_nb.Dispatcher().PlugIn(self)
        self._register_handlers()

    def StreamInit(self):
        """
        Send an initial stream header
        """
        self.Dispatcher.Stream = simplexml.NodeBuilder()
        self.Dispatcher.Stream._dispatch_depth = 2
        self.Dispatcher.Stream.dispatch = self.Dispatcher.dispatch
        self.Dispatcher.Stream.stream_header_received = self._check_stream_start
        self.Dispatcher.Stream.features = None
        if self.sock_type == TYPE_CLIENT:
            self.send_stream_header()

    def send_stream_header(self):
        self.Dispatcher._metastream = Node('stream:stream')
        self.Dispatcher._metastream.setNamespace(self.Namespace)
        self.Dispatcher._metastream.setAttr('version', '1.0')
        self.Dispatcher._metastream.setAttr('xmlns:stream', NS_STREAMS)
        self.Dispatcher._metastream.setAttr('from',
            self.conn_holder.zeroconf.name)
        if self.to:
            self.Dispatcher._metastream.setAttr('to', self.to)
        self.Dispatcher.send("<?xml version='1.0'?>%s>" % str(
                self.Dispatcher._metastream)[:-2])

    def _check_stream_start(self, ns, tag, attrs):
        if ns != NS_STREAMS or tag != 'stream':
            log.error('Incorrect stream start: (%s,%s).Terminating!' % (tag,
                ns), 'error')
            self.Connection.disconnect()
            if self.on_not_ok:
                self.on_not_ok('Connection to host could not be established: '
                    'Incorrect answer from server.')
            return
        if self.sock_type == TYPE_SERVER:
            if attrs.has_key('from'):
                self.to = attrs['from']
            self.send_stream_header()
            if attrs.has_key('version') and attrs['version'] == '1.0':
                # other part supports stream features
                features = Node('stream:features')
                self.Dispatcher.send(features)
            while self.stanzaqueue:
                stanza, is_message = self.stanzaqueue.pop(0)
                self.send(stanza, is_message)
        elif self.sock_type == TYPE_CLIENT:
            while self.stanzaqueue:
                stanza, is_message = self.stanzaqueue.pop(0)
                self.send(stanza, is_message)

    def on_disconnect(self):
        if self.conn_holder:
            if self.conn_holder.ids_of_awaiting_messages.has_key(self.fd):
                del self.conn_holder.ids_of_awaiting_messages[self.fd]
            self.conn_holder.remove_connection(self.sock_hash)
        if self.__dict__.has_key('Dispatcher'):
            self.Dispatcher.PlugOut()
        if self.__dict__.has_key('P2PConnection'):
            self.P2PConnection.PlugOut()
        self.Connection = None
        self._caller = None
        self.conn_holder = None

    def force_disconnect(self):
        if self.Connection:
            self.disconnect()
        else:
            self.on_disconnect()

    def _on_receive_document_attrs(self, data):
        if data:
            self.Dispatcher.ProcessNonBlocking(data)
        if not hasattr(self, 'Dispatcher') or \
                self.Dispatcher.Stream._document_attrs is None:
            return
        self.onreceive(None)
        if self.Dispatcher.Stream._document_attrs.has_key('version') and \
        self.Dispatcher.Stream._document_attrs['version'] == '1.0':
                #~ self.onreceive(self._on_receive_stream_features)
                #XXX continue with TLS
            return
        self.onreceive(None)
        return True

    def remove_timeout(self):
        pass

    def _register_handlers(self):
        self._caller.peerhost = self.Connection._sock.getsockname()
        self.RegisterHandler('message', lambda conn,
            data:self._caller._messageCB(self.Server, conn, data))
        self.RegisterHandler('iq', self._caller._siSetCB, 'set', nbxmpp.NS_SI)
        self.RegisterHandler('iq', self._caller._siErrorCB, 'error',
            nbxmpp.NS_SI)
        self.RegisterHandler('iq', self._caller._siResultCB, 'result',
            nbxmpp.NS_SI)
        self.RegisterHandler('iq', self._caller._bytestreamSetCB, 'set',
            nbxmpp.NS_BYTESTREAM)
        self.RegisterHandler('iq', self._caller._bytestreamResultCB, 'result',
            nbxmpp.NS_BYTESTREAM)
        self.RegisterHandler('iq', self._caller._bytestreamErrorCB, 'error',
            nbxmpp.NS_BYTESTREAM)
        self.RegisterHandler('iq', self._caller._DiscoverItemsGetCB, 'get',
            nbxmpp.NS_DISCO_ITEMS)
        self.RegisterHandler('iq', self._caller._JingleCB, 'result')
        self.RegisterHandler('iq', self._caller._JingleCB, 'error')
        self.RegisterHandler('iq', self._caller._JingleCB, 'set',
            nbxmpp.NS_JINGLE)

class P2PConnection(IdleObject, PlugIn):
    def __init__(self, sock_hash, _sock, addresses=None, caller=None,
    on_connect=None, client=None):
        IdleObject.__init__(self)
        self._owner = client
        PlugIn.__init__(self)
        self.sendqueue = []
        self.sendbuff = None
        self.buff_is_message = False
        self._sock = _sock
        self.sock_hash = None
        self.addresses = addresses
        self.on_connect = on_connect
        self.client = client
        self.writable = False
        self.readable = False
        self._exported_methods = [self.send, self.disconnect, self.onreceive]
        self.on_receive = None
        if _sock:
            self.host = addresses[0]['host']
            self.port = addresses[0]['port']
            self._sock = _sock
            self.state = 1
            self._sock.setblocking(False)
            self.fd = self._sock.fileno()
            self.on_connect(self)
        else:
            self.state = 0
            self.addresses_ = self.addresses
            self.get_next_addrinfo()

    def get_next_addrinfo(self):
        address = self.addresses_.pop(0)
        self.host = address['host']
        self.port = address['port']
        try:
            self.ais = socket.getaddrinfo(address['host'], address['port'], socket.AF_UNSPEC,
                    socket.SOCK_STREAM)
        except socket.gaierror, e:
            log.info('Lookup failure for %s: %s[%s]', host, e[1],
                repr(e[0]), exc_info=True)
            if len(self.addresses_) > 0: return self.get_next_addrinfo()
        else:
            self.connect_to_next_ip()

    def connect_to_next_ip(self):
        if len(self.ais) == 0:
            log.error('Connection failure to %s', str(self.host), exc_info=True)
            if len(self.addresses_) > 0: return self.get_next_addrinfo()
            self.disconnect()
            return
        ai = self.ais.pop(0)
        log.info('Trying to connect to %s through %s:%s', str(self.host),
            ai[4][0], ai[4][1], exc_info=True)
        try:
            self._sock = socket.socket(*ai[:3])
            self._sock.setblocking(False)
            self._server = ai[4]
        except socket.error:
            if sys.exc_value[0] != errno.EINPROGRESS:
                # for all errors, we try other addresses
                self.connect_to_next_ip()
                return
        self.fd = self._sock.fileno()
        gajim.idlequeue.plug_idle(self, True, False)
        self.set_timeout(CONNECT_TIMEOUT_SECONDS)
        self.do_connect()

    def set_timeout(self, timeout):
        gajim.idlequeue.remove_timeout(self.fd)
        if self.state >= 0:
            gajim.idlequeue.set_read_timeout(self.fd, timeout)

    def plugin(self, owner):
        self.onreceive(owner._on_receive_document_attrs)
        self._plug_idle()
        return True

    def plugout(self):
        """
        Disconnect from the remote server and unregister self.disconnected
        method from the owner's dispatcher
        """
        self.disconnect()
        self._owner = None

    def onreceive(self, recv_handler):
        if not recv_handler:
            if hasattr(self._owner, 'Dispatcher'):
                self.on_receive = self._owner.Dispatcher.ProcessNonBlocking
            else:
                self.on_receive = None
            return
        _tmp = self.on_receive
        # make sure this cb is not overriden by recursive calls
        if not recv_handler(None) and _tmp == self.on_receive:
            self.on_receive = recv_handler

    def send(self, packet, is_message=False, now=False):
        """
        Append stanza to the queue of messages to be send if now is False, else
        send it instantly

        If supplied data is unicode string, encode it to UTF-8.
        """
        if self.state <= 0:
            return

        r = packet

        if isinstance(r, unicode):
            r = r.encode('utf-8')
        elif not isinstance(r, str):
            r = ustr(r).encode('utf-8')

        if now:
            self.sendqueue.insert(0, (r, is_message))
            self._do_send()
        else:
            self.sendqueue.append((r, is_message))
        self._plug_idle()

    def read_timeout(self):
        ids = self.client.conn_holder.ids_of_awaiting_messages
        if self.fd in ids and len(ids[self.fd]) > 0:
            for (id_, thread_id) in ids[self.fd]:
                if hasattr(self._owner, 'Dispatcher'):
                    self._owner.Dispatcher.Event('', DATA_ERROR, (
                        self.client.to, thread_id))
                else:
                    self._owner.on_not_ok('connection timeout')
            ids[self.fd] = []
        self.pollend()

    def do_connect(self):
        errnum = 0
        try:
            self._sock.connect(self._server[:2])
            self._sock.setblocking(False)
        except Exception, ee:
            (errnum, errstr) = ee
        errors = (errno.EINPROGRESS, errno.EALREADY, errno.EWOULDBLOCK)
        if 'WSAEINVAL' in errno.__dict__:
            errors += (errno.WSAEINVAL,)
        if errnum in errors:
            return
        # win32 needs this
        elif errnum not in (0, 10056, errno.EISCONN) or self.state != 0:
            log.error('Could not connect to %s: %s [%s]', str(self.host),
                errnum, errstr)
            self.connect_to_next_ip()
            return
        else: # socket is already connected
            self._sock.setblocking(False)
        self.state = 1 # connected
        # we are connected
        self.on_connect(self)

    def pollout(self):
        if self.state == 0:
            self.do_connect()
            return
        gajim.idlequeue.remove_timeout(self.fd)
        self._do_send()

    def pollend(self):
        if self.state == 0:  # error in connect()?
            #self.disconnect()
            self.connect_to_next_ip()
        else:
            self.state = -1
            self.disconnect()

    def pollin(self):
        """
        Reads all pending incoming data. Call owner's disconnected() method if
        appropriate
        """
        received = ''
        errnum = 0
        try:
            # get as many bites, as possible, but not more than RECV_BUFSIZE
            received = self._sock.recv(MAX_BUFF_LEN)
        except Exception, e:
            if len(e.args) > 0 and isinstance(e.args[0], int):
                errnum = e[0]
            # "received" will be empty anyhow
        if errnum == socket.SSL_ERROR_WANT_READ:
            pass
        elif errnum in [errno.ECONNRESET, errno.ENOTCONN, errno.ESHUTDOWN]:
            self.pollend()
            # don't proccess result, cas it will raise error
            return
        elif not received :
            if errnum != socket.SSL_ERROR_EOF:
                # 8 EOF occurred in violation of protocol
                self.pollend()
            if self.state >= 0:
                self.disconnect()
            return

        if self.state < 0:
            return
        if self.on_receive:
            if self._owner.sock_type == TYPE_CLIENT:
                self.set_timeout(ACTIVITY_TIMEOUT_SECONDS)
            if received.strip():
                log.debug('received: %s', received)
            if hasattr(self._owner, 'Dispatcher'):
                self._owner.Dispatcher.Event('', DATA_RECEIVED, received)
            self.on_receive(received)
        else:
            # This should never happed, so we need the debug
            log.error('Unhandled data received: %s' % received)
            self.disconnect()
        return True

    def disconnect(self, message=''):
        """
        Close the socket
        """
        gajim.idlequeue.remove_timeout(self.fd)
        gajim.idlequeue.unplug_idle(self.fd)
        try:
            self._sock.shutdown(socket.SHUT_RDWR)
            self._sock.close()
        except socket.error:
            # socket is already closed
            pass
        self.fd = -1
        self.state = -1
        if self._owner:
            self._owner.on_disconnect()

    def _do_send(self):
        if not self.sendbuff:
            if not self.sendqueue:
                return None # nothing to send
            self.sendbuff, self.buff_is_message = self.sendqueue.pop(0)
            self.sent_data = self.sendbuff
        try:
            send_count = self._sock.send(self.sendbuff)
            if send_count:
                self.sendbuff = self.sendbuff[send_count:]
                if not self.sendbuff and not self.sendqueue:
                    if self.state < 0:
                        gajim.idlequeue.unplug_idle(self.fd)
                        self._on_send()
                        self.disconnect()
                        return
                    # we are not waiting for write
                    self._plug_idle()
                self._on_send()

        except socket.error, e:
            if e[0] == socket.SSL_ERROR_WANT_WRITE:
                return True
            if self.state < 0:
                self.disconnect()
                return
            self._on_send_failure()
            return
        if self._owner.sock_type == TYPE_CLIENT:
            self.set_timeout(ACTIVITY_TIMEOUT_SECONDS)
        return True

    def _plug_idle(self):
        readable = self.state != 0
        if self.sendqueue or self.sendbuff:
            writable = True
        else:
            writable = False
        if self.writable != writable or self.readable != readable:
            gajim.idlequeue.plug_idle(self, writable, readable)


    def _on_send(self):
        if self.sent_data and self.sent_data.strip():
            log.debug('sent: %s' % self.sent_data)
            if hasattr(self._owner, 'Dispatcher'):
                self._owner.Dispatcher.Event('', DATA_SENT, self.sent_data)
        self.sent_data = None
        if self.buff_is_message:
            self._owner.on_message_sent(self.fd)
            self.buff_is_message = False

    def _on_send_failure(self):
        log.error('Socket error while sending data')
        self._owner.on_disconnect()
        self.sent_data = None

class ClientZeroconf:
    def __init__(self, caller):
        self.caller = caller
        self.zeroconf = None
        self.roster = None
        self.last_msg = ''
        self.connections = {}
        self.recipient_to_hash = {}
        self.ip_to_hash = {}
        self.hash_to_port = {}
        self.listener = None
        self.ids_of_awaiting_messages = {}
        self.disconnect_handlers = []
        self.disconnecting = False

    def connect(self, show, msg):
        self.port = self.start_listener(self.caller.port)
        if not self.port:
            return False
        self.zeroconf_init(show, msg)
        if not self.zeroconf.connect():
            self.disconnect()
            return None
        self.roster = roster_zeroconf.Roster(self.zeroconf)
        return True

    def remove_announce(self):
        if self.zeroconf:
            return self.zeroconf.remove_announce()

    def announce(self):
        if self.zeroconf:
            return self.zeroconf.announce()

    def set_show_msg(self, show, msg):
        if self.zeroconf:
            self.zeroconf.txt['msg'] = msg
            self.last_msg = msg
            return self.zeroconf.update_txt(show)

    def resolve_all(self):
        if self.zeroconf:
            self.zeroconf.resolve_all()

    def reannounce(self, txt):
        self.remove_announce()
        self.zeroconf.txt = txt
        self.zeroconf.port = self.port
        self.zeroconf.username = self.caller.username
        return self.announce()

    def zeroconf_init(self, show, msg):
        self.zeroconf = zeroconf.Zeroconf(self.caller._on_new_service,
            self.caller._on_remove_service, self.caller._on_name_conflictCB,
            self.caller._on_disconnected, self.caller._on_error,
            self.caller.username, self.caller.host, self.port)
        self.zeroconf.txt['msg'] = msg
        self.zeroconf.txt['status'] = show
        self.zeroconf.txt['1st'] = self.caller.first
        self.zeroconf.txt['last'] = self.caller.last
        self.zeroconf.txt['jid'] = self.caller.jabber_id
        self.zeroconf.txt['email'] = self.caller.email
        self.zeroconf.username = self.caller.username
        self.zeroconf.host = self.caller.host
        self.zeroconf.port = self.port
        self.last_msg = msg

    def disconnect(self):
        # to avoid recursive calls
        if self.disconnecting:
            return
        if self.listener:
            self.listener.disconnect()
            self.listener = None
        if self.zeroconf:
            self.zeroconf.disconnect()
            self.zeroconf = None
        if self.roster:
            self.roster.zeroconf = None
            self.roster._data = None
            self.roster = None
        self.disconnecting = True
        for i in reversed(self.disconnect_handlers):
            log.debug('Calling disconnect handler %s' % i)
            i()
        self.disconnecting = False

    def start_disconnect(self):
        self.disconnect()

    def kill_all_connections(self):
        for connection in self.connections.values():
            connection.force_disconnect()

    def add_connection(self, connection, ip, port, recipient):
        sock_hash=connection.sock_hash
        if sock_hash not in self.connections:
            self.connections[sock_hash] = connection
        self.ip_to_hash[ip] = sock_hash
        self.hash_to_port[sock_hash] = port
        if recipient:
            self.recipient_to_hash[recipient] = sock_hash

    def remove_connection(self, sock_hash):
        if sock_hash in self.connections:
            del self.connections[sock_hash]
        for i in self.recipient_to_hash:
            if self.recipient_to_hash[i] == sock_hash:
                del self.recipient_to_hash[i]
                break
        for i in self.ip_to_hash:
            if self.ip_to_hash[i] == sock_hash:
                del self.ip_to_hash[i]
                break
        if self.hash_to_port.has_key(sock_hash):
            del self.hash_to_port[sock_hash]

    def start_listener(self, port):
        for p in range(port, port + 5):
            self.listener = ZeroconfListener(p, self)
            self.listener.bind()
            if self.listener.started:
                return p
        self.listener = None
        return False

    def getRoster(self):
        if self.roster:
            return self.roster.getRoster()
        return {}

    def send(self, stanza, is_message=False, now=False, on_ok=None,
    on_not_ok=None):
        stanza.setFrom(self.roster.zeroconf.name)
        to = unicode(stanza.getTo())
        to = gajim.get_jid_without_resource(to)

        try:
            item = self.roster[to]
        except KeyError:
            # Contact offline
            return -1

        # look for hashed connections
        if to in self.recipient_to_hash:
            conn = self.connections[self.recipient_to_hash[to]]
            id_ = stanza.getID() or ''
            if conn.add_stanza(stanza, is_message):
                if on_ok:
                    on_ok(id_)
                return

        the_address = None
        for address in item['addresses']:
            if address['address'] in self.ip_to_hash:
                the_address = address
        if the_address and the_address['address'] in self.ip_to_hash:
            hash_ = self.ip_to_hash[the_address['address']]
            if self.hash_to_port[hash_] == the_address['port']:
                conn = self.connections[hash_]
                id_ = stanza.getID() or ''
                if conn.add_stanza(stanza, is_message):
                    if on_ok:
                        on_ok(id_)
                    return

        # otherwise open new connection
        if not stanza.getID():
            stanza.setID('zero')
        addresses_ = []
        for address in item['addresses']:
            addresses_ += [{'host': address['address'], 'address': address['address'], 'port': address['port']}]
        P2PClient(None, addresses_, self,
            [(stanza, is_message)], to, on_ok=on_ok, on_not_ok=on_not_ok)

    def getAnID(self):
        """
        Generate a random id
        """
        return ''.join(Random().sample(string.letters + string.digits, 6))

    def RegisterDisconnectHandler(self, handler):
        """
        Register handler that will be called on disconnect
        """
        self.disconnect_handlers.append(handler)

    def UnregisterDisconnectHandler(self, handler):
        """
        Unregister handler that is called on disconnect
        """
        self.disconnect_handlers.remove(handler)

    def SendAndWaitForResponse(self, stanza, timeout=None, func=None,
    args=None):
        """
        Send stanza and wait for recipient's response to it. Will call
        transports on_timeout callback if response is not retrieved in time

        Be aware: Only timeout of latest call of SendAndWait is active.
        """
#        if timeout is None:
#            timeout = DEFAULT_TIMEOUT_SECONDS
        def on_ok(_waitid):
#            if timeout:
#                self._owner.set_timeout(timeout)
            to = unicode(stanza.getTo())
            to = gajim.get_jid_without_resource(to)

            try:
                item = self.roster[to]
            except KeyError:
                # Contact offline
                item = None

            conn = None
            if to in self.recipient_to_hash:
                conn = self.connections[self.recipient_to_hash[to]]
            elif item:
                the_address = None
                for address in item['addresses']:
                    if address['address'] in self.ip_to_hash:
                        the_address = address
                if the_address and the_address['address'] in self.ip_to_hash:
                    hash_ = self.ip_to_hash[the_address['address']]
                    if self.hash_to_port[hash_] == the_address['port']:
                        conn = self.connections[hash_]
            if func:
                conn.Dispatcher.on_responses[_waitid] = (func, args)
            conn.onreceive(conn.Dispatcher._WaitForData)
            conn.Dispatcher._expected[_waitid] = None
        self.send(stanza, on_ok=on_ok)

    def SendAndCallForResponse(self, stanza, func=None, args=None):
        """
        Put stanza on the wire and call back when recipient replies. Additional
        callback arguments can be specified in args.
        """
        self.SendAndWaitForResponse(stanza, 0, func, args)
