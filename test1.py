#!/usr/local/bin/python3.9

import sys
import peer
import threading


maxpeers = int(sys.argv[1])
serverport = int(sys.argv[2])
firstpeer = sys.argv[3]


def peerstart(maxpeers, serverport, firstpeer):

    node = peer.Peer(maxpeers, serverport)
    host, port = firstpeer.split(":")

    t = threading.Thread(target=node.mainloop, args=[])
    t.start()


peerstart(maxpeers, serverport, firstpeer)
