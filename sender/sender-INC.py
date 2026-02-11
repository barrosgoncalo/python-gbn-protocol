"""
Reliable Data Transport Protocol (UDP)
Authors: Gonçalo Barros & João Horta
Description: Implementation of a reliable transport layer over UDP
             using Go-Back-N Sliding Window and Multithreading.
Developed as part of the Computer Networks course at FCT NOVA.
"""

import sys
import os
from socket import *
import threading
import pickle
import random
import select
import math

blocksInWindow = 0
window = []
is_endfile = False


currentState = 1

def sendDatagram(blockNo, contents, sock, end):
    rand = random.randint(0, 9)
    if rand > 1:
        toSend = (blockNo, contents)
        msg = pickle.dumps(toSend)
        sock.sendto(msg, end)


def waitForAck(s, seg):
    rx, tx, er = select.select([s], [], [], seg)
    return rx != []


# AUXILIARY METHODS

# resend window blocks in case of corrupted ack
def retransmission(s, receiver):
    for pck in window:
        # s.sendto(pickle.dumps(pck), receiver)
        sendDatagram(*pck, s, receiver)


# calculates the blocks to pop from window
def to_pop(ackNo, expectedNo):
    diff = ackNo - expectedNo
    return min(diff, blocksInWindow)


# slides the leftmost part of the window,
# in other words pops the acked blocks
def slide_window(ackNo, expectedAck):
    global blocksInWindow, window
    for _ in range(to_pop(ackNo, expectedAck)):
        # pop the acked element
        window.pop(0)
        blocksInWindow -= 1

# calculates the number of blocks the file represents
def file2blocks():
    return math.ceil(fileSize / blockSize)


# checks if it is the end of the file
def updt_endfile(seqNo, num_blocks):
    global is_endfile
    if seqNo == num_blocks: is_endfile = True


# gets block number from a packet
def get_number(packet):
    buff, addr = packet
    (ackNo,) = pickle.loads(buff)
    return ackNo


def tx_thread(s, receiver, windowSize, cond, timeout):
    global blocksInWindow, is_endfile, currentState

    while True:
        # ENDFILE handle
        if is_endfile and not blocksInWindow: break

        # S1
        is_timeout = not waitForAck(s, timeout)

        # TIMEOUT handle
        if is_timeout:
            cond.acquire()
            retransmission(s, receiver)
            cond.notify()
            cond.release()
            continue

        # ack receipt
        ack = s.recvfrom(256)
        # block number fetch
        ackNo = get_number(ack)


        # empty window verification
        if not blocksInWindow:
            continue
        # expected ack fetch
        expectedAck, _ = window[0]

        # REPEATED ACK
        # S1 -> S2
        if ackNo == (expectedAck - 1):
            if currentState == 1:
                currentState = 2
            else:
                cond.acquire()
                retransmission(s, receiver)
                currentState = 1
                cond.notify()
                cond.release()

        # NORMAL ACK
        elif ackNo >= expectedAck:
            # permission to read/update window request
            cond.acquire()
            # window sliding
            slide_window(ackNo, expectedAck)
            currentState = 1
            cond.notify()
            cond.release()


def sendBlock(seqNo, fileBytes, s, receiver, windowSize, cond):  # producer

    global blocksInWindow
    cond.acquire()
    updt_endfile(seqNo, file2blocks())
    block = (seqNo, fileBytes)
    while blocksInWindow >= windowSize:
        cond.wait()
    window.append(block)
    blocksInWindow += 1
    sendDatagram(seqNo, fileBytes, s, receiver)
    cond.notify()
    cond.release()



def main(hostname, senderPort, windowSize, timeOutInSec):
    s = socket( AF_INET, SOCK_DGRAM)
    s.bind((hostname, senderPort))
    # interaction with receiver; no datagram loss
    buf, rem = s.recvfrom( 256 )
    req = pickle.loads( buf)
    fileName = req[0]
    global blockSize
    blockSize = req[1]
    result = os.path.exists(fileName)
    if not result:
        print(f'file {fileName} does not exist in server')
        reply = ( -1, 0 )
        rep=pickle.dumps(reply)
        s.sendto( rep, rem )
        sys.exit(1)
    global fileSize
    fileSize = os.path.getsize(fileName)
    reply = ( 0, fileSize)
    rep=pickle.dumps(reply)
    s.sendto( rep, rem )
    # file transfer; datagram loss possible
    windowCond = threading.Condition()
    tid = threading.Thread( target=tx_thread,
                            args=(s,rem,windowSize, windowCond,timeOutInSec))
    tid.start()
    f = open( fileName, 'rb')
    blockNo = 1

    while True:
        b = f.read( blockSize  )
        sizeOfBlockRead = len(b)
        if sizeOfBlockRead > 0:
            sendBlock( blockNo, b, s, rem, windowSize, windowCond)
        if sizeOfBlockRead == blockSize:
            blockNo=blockNo+1
        else:
            break
    f.close()
    tid.join()


if __name__ == "__main__":
    # python sender.py senderPort windowSize timeOutInSec


    if len(sys.argv) != 4:
        print("Usage: python sender.py senderPort windowSize timeOutInSec")
    else:
        senderPort = int(sys.argv[1])
        windowSize = int(sys.argv[2])
        timeOutInSec = int(sys.argv[3])
        hostname = gethostbyname(gethostname())
        random.seed( 5 )
        main( hostname, senderPort, windowSize, timeOutInSec)
