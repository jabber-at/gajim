##
## Copyright (C) 2006 Gajim Team
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published
## by the Free Software Foundation; version 2 only.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##

"""
Handles Jingle RTP sessions (XEP 0167)
"""

from collections import deque

import gobject
import socket

import xmpp
import farstream, gst
from glib import GError

import gajim

from jingle_transport import JingleTransportICEUDP
from jingle_content import contents, JingleContent, JingleContentSetupException
from connection_handlers_events import InformationEvent


import logging
log = logging.getLogger('gajim.c.jingle_rtp')


class JingleRTPContent(JingleContent):
    def __init__(self, session, media, transport=None):
        if transport is None:
            transport = JingleTransportICEUDP()
        JingleContent.__init__(self, session, transport)
        self.media = media
        self._dtmf_running = False
        self.farstream_media = {'audio': farstream.MEDIA_TYPE_AUDIO,
                                                        'video': farstream.MEDIA_TYPE_VIDEO}[media]

        self.pipeline = None
        self.src_bin = None
        self.stream_failed_once = False

        self.candidates_ready = False # True when local candidates are prepared

        self.callbacks['session-initiate'] += [self.__on_remote_codecs]
        self.callbacks['content-add'] += [self.__on_remote_codecs]
        self.callbacks['description-info'] += [self.__on_remote_codecs]
        self.callbacks['content-accept'] += [self.__on_remote_codecs]
        self.callbacks['session-accept'] += [self.__on_remote_codecs]
        self.callbacks['session-terminate'] += [self.__stop]
        self.callbacks['session-terminate-sent'] += [self.__stop]

    def setup_stream(self, on_src_pad_added):
        # pipeline and bus
        self.pipeline = gst.Pipeline()
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect('message', self._on_gst_message)

        # conference
        self.conference = gst.element_factory_make('fsrtpconference')
        self.pipeline.add(self.conference)
        self.funnel = None

        self.p2psession = self.conference.new_session(self.farstream_media)

        participant = self.conference.new_participant()
        # FIXME: Consider a workaround, here...
        # pidgin and telepathy-gabble don't follow the XEP, and it won't work
        # due to bad controlling-mode
        params = {'controlling-mode': self.session.weinitiate, 'debug': False}
        if gajim.config.get('use_stun_server'):
            stun_server = gajim.config.get('stun_server')
            if not stun_server and self.session.connection._stun_servers:
                stun_server = self.session.connection._stun_servers[0]['host']
            if stun_server:
                try:
                    ip = socket.getaddrinfo(stun_server, 0, socket.AF_UNSPEC,
                            socket.SOCK_STREAM)[0][4][0]
                except socket.gaierror, (errnum, errstr):
                    log.warn('Lookup of stun ip failed: %s' % errstr)
                else:
                    params['stun-ip'] = ip

        self.p2pstream = self.p2psession.new_stream(participant,
                farstream.DIRECTION_RECV)
        self.p2pstream.connect('src-pad-added', on_src_pad_added)
        self.p2pstream.set_transmitter('nice', params)

    def is_ready(self):
        return (JingleContent.is_ready(self) and self.candidates_ready)

    def make_bin_from_config(self, config_key, pipeline, text):
        pipeline = pipeline % gajim.config.get(config_key)
        try:
            bin = gst.parse_bin_from_description(pipeline, True)
            return bin
        except GError, error_str:
            gajim.nec.push_incoming_event(InformationEvent(None,
                conn=self.session.connection, level='error',
                pri_txt=_('%s configuration error') % text.capitalize(),
                sec_txt=_("Couldn't setup %s. Check your configuration.\n\n"
                "Pipeline was:\n%s\n\nError was:\n%s") % (text, pipeline,
                error_str)))
            raise JingleContentSetupException

    def add_remote_candidates(self, candidates):
        JingleContent.add_remote_candidates(self, candidates)
        # FIXME: connectivity should not be etablished yet
        # Instead, it should be etablished after session-accept!
        if self.sent:
            self.p2pstream.add_remote_candidates(candidates)

    def batch_dtmf(self, events):
        """
        Send several DTMF tones
        """
        if self._dtmf_running:
            raise Exception("There is a DTMF batch already running")
        events = deque(events)
        self._dtmf_running = True
        self._start_dtmf(events.popleft())
        gobject.timeout_add(500, self._next_dtmf, events)

    def _next_dtmf(self, events):
        self._stop_dtmf()
        if events:
            self._start_dtmf(events.popleft())
            gobject.timeout_add(500, self._next_dtmf, events)
        else:
            self._dtmf_running = False

    def _start_dtmf(self, event):
        if event in ('*', '#'):
            event = {'*': farstream.DTMF_EVENT_STAR,
                    '#': farstream.DTMF_EVENT_POUND}[event]
        else:
            event = int(event)
        self.p2psession.start_telephony_event(event, 2)

    def _stop_dtmf(self):
        self.p2psession.stop_telephony_event()

    def _fill_content(self, content):
        content.addChild(xmpp.NS_JINGLE_RTP + ' description',
                attrs={'media': self.media}, payload=self.iter_codecs())

    def _setup_funnel(self):
        self.funnel = gst.element_factory_make('fsfunnel')
        self.pipeline.add(self.funnel)
        self.funnel.set_state(gst.STATE_PLAYING)
        self.sink.set_state(gst.STATE_PLAYING)
        self.funnel.link(self.sink)

    def _on_src_pad_added(self, stream, pad, codec):
        if not self.funnel:
            self._setup_funnel()
        pad.link(self.funnel.get_pad('sink%d'))

    def _on_gst_message(self, bus, message):
        if message.type == gst.MESSAGE_ELEMENT:
            name = message.structure.get_name()
            log.debug('gst element message: %s: %s' % (name, message))
            if name == 'farstream-new-active-candidate-pair':
                pass
            elif name == 'farstream-recv-codecs-changed':
                pass
            elif name == 'farstream-codecs-changed':
                if self.sent and self.p2psession.get_property('codecs'):
                    self.send_description_info()
                    if self.transport.remote_candidates:
                        # those lines MUST be done after we get info on our
                        # codecs
                        self.p2pstream.add_remote_candidates(
                            self.transport.remote_candidates)
                        self.transport.remote_candidates = []
                        self.p2pstream.set_property('direction',
                            farstream.DIRECTION_BOTH)

            elif name == 'farstream-local-candidates-prepared':
                self.candidates_ready = True
                if self.is_ready():
                    self.session.on_session_state_changed(self)
            elif name == 'farstream-new-local-candidate':
                candidate = message.structure['candidate']
                self.transport.candidates.append(candidate)
                if self.sent:
                    # FIXME: Is this case even possible?
                    self.send_candidate(candidate)
            elif name == 'farstream-component-state-changed':
                state = message.structure['state']
                if state == farstream.STREAM_STATE_FAILED:
                    reason = xmpp.Node('reason')
                    reason.setTag('failed-transport')
                    self.session.remove_content(self.creator, self.name, reason)
            elif name == 'farstream-error':
                log.error('Farstream error #%d!\nMessage: %s' % (
                    message.structure['error-no'],
                    message.structure['error-msg']))
        elif message.type == gst.MESSAGE_ERROR:
            # TODO: Fix it to fallback to videotestsrc anytime an error occur,
            # or raise an error, Jingle way
            # or maybe one-sided stream?
            if not self.stream_failed_once:
                gajim.nec.push_incoming_event(InformationEvent(None,
                    conn=self.session.connection, level='error',
                    pri_txt=_('GStreamer error'), sec_txt=_('Error: %s\nDebug: '
                    '%s' % (message.structure['gerror'],
                    message.structure['debug']))))

            sink_pad = self.p2psession.get_property('sink-pad')

            # Remove old source
            self.src_bin.get_pad('src').unlink(sink_pad)
            self.src_bin.set_state(gst.STATE_NULL)
            self.pipeline.remove(self.src_bin)

            if not self.stream_failed_once:
                # Add fallback source
                self.src_bin = self.get_fallback_src()
                self.pipeline.add(self.src_bin)
                self.src_bin.get_pad('src').link(sink_pad)
                self.stream_failed_once = True
            else:
                reason = xmpp.Node('reason')
                reason.setTag('failed-application')
                self.session.remove_content(self.creator, self.name, reason)

            # Start playing again
            self.pipeline.set_state(gst.STATE_PLAYING)

    def get_fallback_src(self):
        return gst.element_factory_make('fakesrc')

    def on_negotiated(self):
        if self.accepted:
            if self.p2psession.get_property('codecs'):
                # those lines MUST be done after we get info on our codecs
                if self.transport.remote_candidates:
                    self.p2pstream.add_remote_candidates(
                        self.transport.remote_candidates)
                    self.transport.remote_candidates = []
                # TODO: farstream.DIRECTION_BOTH only if senders='both'
                self.p2pstream.set_property('direction',
                    farstream.DIRECTION_BOTH)
        JingleContent.on_negotiated(self)

    def __on_remote_codecs(self, stanza, content, error, action):
        """
        Get peer codecs from what we get from peer
        """

        codecs = []
        for codec in content.getTag('description').iterTags('payload-type'):
            if not codec['id'] or not codec['name'] or not codec['clockrate']:
                # ignore invalid payload-types
                continue
            c = farstream.Codec(int(codec['id']), codec['name'],
                    self.farstream_media, int(codec['clockrate']))
            if 'channels' in codec:
                c.channels = int(codec['channels'])
            else:
                c.channels = 1
            c.optional_params = [(str(p['name']), str(p['value'])) for p in \
                    codec.iterTags('parameter')]
            codecs.append(c)

        if codecs:
            # FIXME: Handle this case:
            # glib.GError: There was no intersection between the remote codecs and
            # the local ones
            self.p2pstream.set_remote_codecs(codecs)

    def iter_codecs(self):
        codecs = self.p2psession.get_property('codecs')
        for codec in codecs:
            attrs = {'name': codec.encoding_name,
                    'id': codec.id,
                    'channels': codec.channels}
            if codec.clock_rate:
                attrs['clockrate'] = codec.clock_rate
            if codec.optional_params:
                payload = (xmpp.Node('parameter', {'name': name, 'value': value})
                        for name, value in codec.optional_params)
            else:
                payload = ()
            yield xmpp.Node('payload-type', attrs, payload)

    def __stop(self, *things):
        self.pipeline.set_state(gst.STATE_NULL)

    def __del__(self):
        self.__stop()

    def destroy(self):
        JingleContent.destroy(self)
        self.p2pstream.disconnect_by_func(self._on_src_pad_added)
        self.pipeline.get_bus().disconnect_by_func(self._on_gst_message)


class JingleAudio(JingleRTPContent):
    """
    Jingle VoIP sessions consist of audio content transported over an ICE UDP
    protocol
    """

    def __init__(self, session, transport=None):
        JingleRTPContent.__init__(self, session, 'audio', transport)
        self.setup_stream()

    def set_mic_volume(self, vol):
        """
        vol must be between 0 ans 1
        """
        self.mic_volume.set_property('volume', vol)

    def set_out_volume(self, vol):
        """
        vol must be between 0 ans 1
        """
        self.out_volume.set_property('volume', vol)

    def setup_stream(self):
        JingleRTPContent.setup_stream(self, self._on_src_pad_added)

        # Configure SPEEX
        # Workaround for psi (not needed since rev
        # 147aedcea39b43402fe64c533d1866a25449888a):
        #  place 16kHz before 8kHz, as buggy psi versions will take in
        #  account only the first codec

        codecs = [farstream.Codec(farstream.CODEC_ID_ANY, 'SPEEX',
                farstream.MEDIA_TYPE_AUDIO, 16000),
                farstream.Codec(farstream.CODEC_ID_ANY, 'SPEEX',
                farstream.MEDIA_TYPE_AUDIO, 8000)]
        self.p2psession.set_codec_preferences(codecs)

        # the local parts
        # TODO: Add queues?
        self.src_bin = self.make_bin_from_config('audio_input_device',
                '%s ! audioconvert', _("audio input"))

        self.sink = self.make_bin_from_config('audio_output_device',
                'audioconvert ! volume name=gajim_out_vol ! %s', _("audio output"))

        self.mic_volume = self.src_bin.get_by_name('gajim_vol')
        self.out_volume = self.sink.get_by_name('gajim_out_vol')

        # link gst elements
        self.pipeline.add(self.sink, self.src_bin)

        self.src_bin.get_pad('src').link(self.p2psession.get_property(
                'sink-pad'))

        # The following is needed for farstream to process ICE requests:
        self.pipeline.set_state(gst.STATE_PLAYING)


class JingleVideo(JingleRTPContent):
    def __init__(self, session, transport=None):
        JingleRTPContent.__init__(self, session, 'video', transport)
        self.setup_stream()

    def setup_stream(self):
        # TODO: Everything is not working properly:
        # sometimes, one window won't show up,
        # sometimes it'll freeze...
        JingleRTPContent.setup_stream(self, self._on_src_pad_added)

        # the local parts
        if gajim.config.get('video_framerate'):
            framerate = 'videorate ! video/x-raw-yuv,framerate=%s ! ' % \
                gajim.config.get('video_framerate')
        else:
            framerate = ''
        try:
            w, h = gajim.config.get('video_size').split('x')
        except:
            w = h = None
        if w and h:
            video_size = 'video/x-raw-yuv,width=%s,height=%s ! ' % (w, h)
        else:
            video_size = ''
        self.src_bin = self.make_bin_from_config('video_input_device',
            '%%s ! %svideoscale ! %sffmpegcolorspace' % (framerate, video_size),
            _("video input"))
        #caps = gst.element_factory_make('capsfilter')
        #caps.set_property('caps', gst.caps_from_string('video/x-raw-yuv, width=320, height=240'))

        self.pipeline.add(self.src_bin)#, caps)
        #src_bin.link(caps)

        self.sink = self.make_bin_from_config('video_output_device',
            'videoscale ! ffmpegcolorspace ! %s force-aspect-ratio=True',
            _("video output"))
        self.pipeline.add(self.sink)

        self.src_bin.get_pad('src').link(self.p2psession.get_property(
            'sink-pad'))

        # The following is needed for farstream to process ICE requests:
        self.pipeline.set_state(gst.STATE_PLAYING)

    def get_fallback_src(self):
        # TODO: Use avatar?
        pipeline = 'videotestsrc is-live=true ! video/x-raw-yuv,framerate=10/1 ! ffmpegcolorspace'
        return gst.parse_bin_from_description(pipeline, True)

def get_content(desc):
    if desc['media'] == 'audio':
        return JingleAudio
    elif desc['media'] == 'video':
        return JingleVideo

contents[xmpp.NS_JINGLE_RTP] = get_content
