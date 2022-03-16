# -*- coding: utf-8 -*-
"""
    proxy.py
    ~~~~~~~~
    ⚡⚡⚡ Fast, Lightweight, Pluggable, TLS interception capable proxy server focused on
    Network monitoring, controls & Application development, testing, debugging.

    :copyright: (c) 2013-present by Abhinav Singh and contributors.
    :license: BSD, see LICENSE for more details.
"""
import argparse
from typing import TYPE_CHECKING
import socket
import logging
import select
import threading

logger = logging.getLogger(__name__)

if TYPE_CHECKING:   # pragma: no cover
    from ...common.types import HostPort
    try:
        from paramiko.channel import Channel
    except ImportError:
        pass


class SshHttpProtocolHandler:
    """Handles incoming connections over forwarded SSH transport."""

    def __init__(self, flags: argparse.Namespace) -> None:
        self.flags = flags

    def tunnel_forward_worker(self, chan):
        host, port = '127.0.0.1', self.flags.port
        sock = socket.socket()
        try:
            sock.connect((host, port))
        except Exception as e:
            logger.info("Forwarding request to %s:%d failed: %r" % (host, port, e))
            return
        logger.info(
            "Connected!  Tunnel open %r -> %r -> %r"
            % (chan.origin_addr, chan.getpeername(), (host, port))
        )
        while True:
            r, w, x = select.select([sock, chan], [], [])
            if sock in r:
                data = sock.recv(1024)
                if len(data) == 0:
                    break
                chan.send(data)
            if chan in r:
                data = chan.recv(1024)
                if len(data) == 0:
                    break
                sock.send(data)
        chan.close()
        sock.close()
        logger.info("Tunnel closed from %r" % (chan.origin_addr,))


    def on_connection(
        self,
        chan: 'Channel',
        origin: 'HostPort',
        server: 'HostPort',
    ) -> None:
        thr = threading.Thread(
            target=self.tunnel_forward_worker, args=(chan,)
        )
        thr.setDaemon(True)
        thr.start()
