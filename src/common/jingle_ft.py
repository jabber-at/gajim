# -*- coding:utf-8 -*-
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


"""
Handles  Jingle File Transfer (XEP 0234)
"""

import os
import hashlib
import gajim
import nbxmpp
import configpaths
import jingle_xtls
from common.jingle_ftstates import StateCandReceived, \
    StateCandSent, StateCandSentAndRecv, StateInitialized, StateTransfering,\
    StateTransportReplace
from common.jingle_transport import TransportType, JingleTransportSocks5
from jingle_content import contents, JingleContent
from common import helpers
from common.connection_handlers_events import FileRequestReceivedEvent, \
    JingleSessionInitiateSendingEvent
import threading
import logging

log = logging.getLogger('gajim.c.jingle_ft')

STATE_NOT_STARTED = 0
STATE_INITIALIZED = 1
# We send the candidates and we are waiting for a reply
STATE_CAND_SENT = 2
# We received the candidates and we are waiting to reply
STATE_CAND_RECEIVED = 3
# We have sent and received the candidates
# This also includes any candidate-error received or sent
STATE_CAND_SENT_AND_RECEIVED = 4
STATE_TRANSPORT_REPLACE = 5
# We are transfering the file
STATE_TRANSFERING = 6


class JingleFileTransfer(JingleContent):

    def __init__(self, session, transport=None, file_props=None,
    use_security=False):
        JingleContent.__init__(self, session, transport)
        log.info("transport value: %s" % transport)
        # events we might be interested in
        self.callbacks['session-initiate'] += [self.__on_session_initiate]
        self.callbacks['session-initiate-sent'] += [
            self.__on_session_initiate_sent]
        self.callbacks['content-add'] += [self.__on_session_initiate]
        self.callbacks['session-accept'] += [self.__on_session_accept]
        self.callbacks['session-terminate'] += [self.__on_session_terminate]
        self.callbacks['session-info'] += [self.__on_session_info]
        self.callbacks['transport-accept'] += [self.__on_transport_accept]
        self.callbacks['transport-replace'] += [self.__on_transport_replace]
        self.callbacks['session-accept-sent'] += [self.__transport_setup]
        # fallback transport method
        self.callbacks['transport-reject'] += [self.__on_transport_reject]
        self.callbacks['transport-info'] += [self.__on_transport_info]
        self.callbacks['iq-result'] += [self.__on_iq_result]
        self.use_security = use_security
        self.x509_fingerprint = None
        self.file_props = file_props
        self.weinitiate = self.session.weinitiate
        self.werequest = self.session.werequest
        if self.file_props is not None:
            if self.session.werequest:
                self.file_props.sender = self.session.peerjid
                self.file_props.receiver = self.session.ourjid
            else:
                self.file_props.sender = self.session.ourjid
                self.file_props.receiver = self.session.peerjid
            self.file_props.session_type = 'jingle'
            self.file_props.sid = session.sid
            self.file_props.transfered_size = []
            self.file_props.transport_sid = self.transport.sid
        log.info("FT request: %s" % file_props)
        if transport is None:
            self.transport = JingleTransportSocks5()
        self.transport.set_connection(session.connection)
        self.transport.set_file_props(self.file_props)
        self.transport.set_our_jid(session.ourjid)
        log.info('ourjid: %s' % session.ourjid)
        self.session = session
        self.media = 'file'
        self.nominated_cand = {}
        if gajim.contacts.is_gc_contact(session.connection.name,
        session.peerjid):
            roomjid = session.peerjid.split('/')[0]
            dstaddr = hashlib.sha1('%s%s%s' % (self.file_props.sid,
                session.ourjid, roomjid)).hexdigest()
            self.file_props.dstaddr = dstaddr
        self.state = STATE_NOT_STARTED
        self.states = {STATE_INITIALIZED   : StateInitialized(self),
                       STATE_CAND_SENT     : StateCandSent(self),
                       STATE_CAND_RECEIVED : StateCandReceived(self),
                       STATE_TRANSFERING   : StateTransfering(self),
                   STATE_TRANSPORT_REPLACE : StateTransportReplace(self),
              STATE_CAND_SENT_AND_RECEIVED : StateCandSentAndRecv(self)
        }

        if jingle_xtls.PYOPENSSL_PRESENT:
            cert_name = os.path.join(configpaths.gajimpaths['MY_CERT'],
                                     jingle_xtls.SELF_SIGNED_CERTIFICATE)
            if not (os.path.exists(cert_name + '.cert')
                    and os.path.exists(cert_name + '.pkey')):
                jingle_xtls.make_certs(cert_name, 'gajim')

    def __state_changed(self, nextstate, args=None):
        # Executes the next state action and sets the next state
        current_state = self.state
        st = self.states[nextstate]
        st.action(args)
        # state can have been changed during the action. Don't go back.
        if self.state == current_state:
            self.state = nextstate

    def __on_session_initiate(self, stanza, content, error, action):
        log.debug("Jingle FT request received")
        gajim.nec.push_incoming_event(FileRequestReceivedEvent(None,
            conn=self.session.connection, stanza=stanza, jingle_content=content,
            FT_content=self))
        if self.session.request:
            # accept the request
            self.session.approve_content(self.media, self.name)
            self.session.accept_session()

    def __on_session_initiate_sent(self, stanza, content, error, action):
        log.debug("Jingle FT session initiate sending")
        gajim.nec.push_outgoing_event(JingleSessionInitiateSendingEvent(None,
            conn=self.session.connection, stanza=stanza, jingle_content=content,
            FT_content=self))

    def __send_hash(self):
        # Send hash in a session info
        checksum = nbxmpp.Node(tag='checksum', payload=[nbxmpp.Node(tag='file',
            payload=[self._calcHash()])])
        checksum.setNamespace(nbxmpp.NS_JINGLE_FILE_TRANSFER)
        self.session.__session_info(checksum )
        pjid = gajim.get_jid_without_resource(self.session.peerjid)
        file_info = {'name' : self.file_props.name,
                     'file-name' : self.file_props.file_name,
                     'hash' : self.file_props.hash_,
                     'size' : self.file_props.size,
                     'date' : self.file_props.date,
                     'peerjid' : pjid
                    }
        self.session.connection.set_file_info(file_info)

    def _calcHash(self):
        # Caculates the hash and returns a xep-300 hash stanza
        if self.file_props.algo == None:
            return
        try:
            file_ = open(self.file_props.file_name, 'rb')
        except:
            # can't open file
            return
        h = nbxmpp.Hashes()
        hash_ = h.calculateHash(self.file_props.algo, file_)
        file_.close()
        # DEBUG
        #hash_ = '1294809248109223'
        if not hash_:
            # Hash alogrithm not supported
            return
        self.file_props.hash_ = hash_
        h.addHash(hash_, self.file_props.algo)
        return h

    def on_cert_received(self):
        self.session.approve_session()
        self.session.approve_content('file', name=self.name)

    def __on_session_accept(self, stanza, content, error, action):
        log.info("__on_session_accept")
        con = self.session.connection
        security = content.getTag('security')
        if not security: # responder can not verify our fingerprint
            self.use_security = False
        else:
            fingerprint = security.getTag('fingerprint')
            if fingerprint:
                fingerprint = fingerprint.getData()
                self.x509_fingerprint = fingerprint
                if not jingle_xtls.check_cert(gajim.get_jid_without_resource(
                self.session.responder), fingerprint):
                    id_ = jingle_xtls.send_cert_request(con,
                        self.session.responder)
                    jingle_xtls.key_exchange_pend(id_,
                        self.continue_session_accept, [stanza])
                    raise nbxmpp.NodeProcessed
        self.continue_session_accept(stanza)

    def continue_session_accept(self, stanza):
        con = self.session.connection
        if self.state == STATE_TRANSPORT_REPLACE:
            # If we are requesting we don't have the file
            if self.session.werequest:
                raise nbxmpp.NodeProcessed
            # We send the file
            self.__state_changed(STATE_TRANSFERING)
            raise nbxmpp.NodeProcessed
        self.file_props.streamhosts = self.transport.remote_candidates
        # Calculate file hash in a new thread
        # if we haven't sent the hash already.
        if self.file_props.hash_ is None and self.file_props.algo and \
        not self.werequest:
            self.hashThread = threading.Thread(target=self.__send_hash)
            self.hashThread.start()
        for host in self.file_props.streamhosts:
            host['initiator'] = self.session.initiator
            host['target'] = self.session.responder
            host['sid'] = self.file_props.sid
        fingerprint = None
        if self.use_security:
            fingerprint = 'client'
        if self.transport.type_ == TransportType.SOCKS5:
            gajim.socks5queue.connect_to_hosts(self.session.connection.name,
                self.file_props.sid, self.on_connect,
                self._on_connect_error, fingerprint=fingerprint,
                receiving=False)
            raise nbxmpp.NodeProcessed
        self.__state_changed(STATE_TRANSFERING)
        raise nbxmpp.NodeProcessed

    def __on_session_terminate(self, stanza, content, error, action):
        log.info("__on_session_terminate")

    def __on_session_info(self, stanza, content, error, action):
        pass

    def __on_transport_accept(self, stanza, content, error, action):
        log.info("__on_transport_accept")

    def __on_transport_replace(self, stanza, content, error, action):
        log.info("__on_transport_replace")

    def __on_transport_reject(self, stanza, content, error, action):
        log.info("__on_transport_reject")

    def __on_transport_info(self, stanza, content, error, action):
        log.info("__on_transport_info")
        candError = content.getTag('transport').getTag('candidate-error')
        candUsed  = content.getTag('transport').getTag('candidate-used')
        if (candError or candUsed) and \
                self.state >= STATE_CAND_SENT_AND_RECEIVED:
            raise nbxmpp.NodeProcessed
        if candError:
            if not gajim.socks5queue.listener.connections:
                gajim.socks5queue.listener.disconnect()
            self.nominated_cand['peer-cand'] = False
            if self.state == STATE_CAND_SENT:
                if not self.nominated_cand['our-cand'] and \
                   not self.nominated_cand['peer-cand']:
                    if not self.weinitiate:
                        return
                    self.__state_changed(STATE_TRANSPORT_REPLACE)
                else:
                    response = stanza.buildReply('result')
                    response.delChild(response.getQuery())
                    self.session.connection.connection.send(response)
                    self.__state_changed(STATE_TRANSFERING)
                    raise nbxmpp.NodeProcessed
            else:
                args = {'candError' : True}
                self.__state_changed(STATE_CAND_RECEIVED, args)
            return
        if candUsed:
            streamhost_cid = candUsed.getAttr('cid')
            streamhost_used = None
            for cand in self.transport.candidates:
                if cand['candidate_id'] == streamhost_cid:
                    streamhost_used = cand
                    break
            if streamhost_used == None or streamhost_used['type'] == 'proxy':
                if gajim.socks5queue.listener and \
                not gajim.socks5queue.listener.connections:
                    gajim.socks5queue.listener.disconnect()
        if content.getTag('transport').getTag('activated'):
            self.state = STATE_TRANSFERING
            jid = gajim.get_jid_without_resource(self.session.ourjid)
            gajim.socks5queue.send_file(self.file_props,
                self.session.connection.name, 'client')
            return
        args = {'content' : content,
                'sendCand' : False}
        if self.state == STATE_CAND_SENT:
            self.__state_changed(STATE_CAND_SENT_AND_RECEIVED, args)
            self.__state_changed(STATE_TRANSFERING)
            raise nbxmpp.NodeProcessed
        else:
            self.__state_changed(STATE_CAND_RECEIVED, args)

    def __on_iq_result(self, stanza, content, error, action):
        log.info("__on_iq_result")

        if self.state == STATE_NOT_STARTED:
            self.__state_changed(STATE_INITIALIZED)
        elif self.state == STATE_CAND_SENT_AND_RECEIVED:
            if not self.nominated_cand['our-cand'] and \
            not self.nominated_cand['peer-cand']:
                if not self.weinitiate:
                    return
                self.__state_changed(STATE_TRANSPORT_REPLACE)
                return
            # initiate transfer
            self.__state_changed(STATE_TRANSFERING)

    def __transport_setup(self, stanza=None, content=None, error=None,
    action=None):
        # Sets up a few transport specific things for the file transfer
        if self.transport.type_ == TransportType.IBB:
            # No action required, just set the state to transfering
            self.state = STATE_TRANSFERING
        else:
            self._listen_host()

    def on_connect(self, streamhost):
        """
        send candidate-used stanza
        """
        log.info('send_candidate_used')
        if streamhost is None:
            return
        args = {'streamhost' : streamhost,
                'sendCand'   : True}
        self.nominated_cand['our-cand'] = streamhost
        self.__sendCand(args)

    def _on_connect_error(self, sid):
        log.info('connect error, sid=' + sid)
        args = {'candError' : True,
                'sendCand'  : True}
        self.__sendCand(args)

    def __sendCand(self, args):
        if self.state == STATE_CAND_RECEIVED:
            self.__state_changed(STATE_CAND_SENT_AND_RECEIVED, args)
        else:
            self.__state_changed(STATE_CAND_SENT, args)

    def _store_socks5_sid(self, sid, hash_id):
        # callback from socsk5queue.start_listener
        self.file_props.hash_ = hash_id

    def _listen_host(self):
        receiver = self.file_props.receiver
        sender = self.file_props.sender
        sha_str = helpers.get_auth_sha(self.file_props.sid, sender,
            receiver)
        self.file_props.sha_str = sha_str
        port = gajim.config.get('file_transfers_port')
        fingerprint = None
        if self.use_security:
            fingerprint = 'server'
        if self.weinitiate:
            listener = gajim.socks5queue.start_listener(port, sha_str,
                self._store_socks5_sid, self.file_props,
                fingerprint=fingerprint, typ='sender')
        else:
            listener = gajim.socks5queue.start_listener(port, sha_str,
                self._store_socks5_sid, self.file_props,
                fingerprint=fingerprint, typ='receiver')
        if not listener:
            # send error message, notify the user
            return

    def isOurCandUsed(self):
        '''
        If this method returns true then the candidate we nominated will be
        used, if false, the candidate nominated by peer will be used
        '''

        if self.nominated_cand['peer-cand'] == False:
            return True
        if self.nominated_cand['our-cand'] == False:
            return False
        peer_pr = int(self.nominated_cand['peer-cand']['priority'])
        our_pr = int(self.nominated_cand['our-cand']['priority'])
        if peer_pr != our_pr:
            return our_pr > peer_pr
        else:
            return self.weinitiate

    def start_IBB_transfer(self):
        if self.file_props.type_ == 's':
            self.__state_changed(STATE_TRANSFERING)


def get_content(desc):
    return JingleFileTransfer

contents[nbxmpp.NS_JINGLE_FILE_TRANSFER] = get_content
