#!/usr/bin/env python

import os
import random
import string
import threading
import sys
import time 

from select import select

BUFFER_SIZE = 1024

msg_list = []

rlock = True
wlock = True

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def reset_term():
    print(chr(27) + "[2J")

def draw():
    for line in msg_list:
        print(line)
    print("> "),
    sys.stdout.flush()

class ReadThread(threading.Thread):

    def __init__(self,fifo=None):
        threading.Thread.__init__(self)

        self.fifo = fifo
        self.running = True

        self._stop = threading.Event()
        return

    def run(self):
        global rlock

        fd = os.open(self.fifo, os.O_RDONLY|os.O_NONBLOCK)

        while self.running:
            try:
                line = os.read(fd, BUFFER_SIZE)
            except:
                if not os.path.exists(self.fifo):
                    self.running = False
                continue

            if not line:
                continue

            if line == "q":
                self.running = False
                continue

            msg_list.append(bcolors.WARNING + "Them: " + line + bcolors.ENDC)
            reset_term()
            draw()

        #print("Writing thread closed")

        os.close(fd)

        #print("FIFO closed")
        rlock = False
        return       

    def stop(self):
        self.running = False
        self._stop.set()

    def stopped(self):
       self._stop.isSet()  

class WriteThread(threading.Thread):

    def __init__(self, fifo=None):
        threading.Thread.__init__(self)

        self.fifo = fifo
        self.running = True
        self._stop = threading.Event()

        return

    def run(self):
        global wlock
        self.fd = open(self.fifo, "w")

        reset_term()
        draw()
    
        line = ""

        timeout = 1

        while self.running:
            rlist, _, _ = select([sys.stdin], [], [], timeout)
            if rlist:
                line = sys.stdin.readline()
            else:
                continue
            if not line:
                reset_term()
                draw()
                continue

            if "q" == line.strip():
                self.running = False
                self.fd.write("q")
                self.fd.flush()
                continue

            msg_list.append(bcolors.OKBLUE + "Me: " + line + bcolors.ENDC)
            reset_term()
            draw()

            self.fd.write(line)
            self.fd.flush()
        
        #print("Closing down thread")
        self.fd.close()

        #print("FIFO closed")

        wlock = False
        return        

    def stop(self):
        self.running = False
        self._stop.set()

    def stopped(self):
       self._stop.isSet()  

def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.SystemRandom().choice(chars) for _ in range(size))

def main():

    print("RDVZ Online\n\n")

    key = raw_input("<Enter> for a new session or enter key: ")

    if not key:
        key = id_generator()
        print("Session key: %s" % key)

    fifo = "/tmp/"+key

    #print("Opening fifo %s" % fifo)

    if os.path.exists(fifo):
        # we're not first

        #print("Not first, open fifo")

        fd = open(fifo,"w")

        os.mkfifo(fifo+"2")

        # Send message
        fd.write("1")
        fd.close()

        readerThread = ReadThread(fifo=fifo+"2")
        writerThread = WriteThread(fifo=fifo)

    else:
        # we're first

        #print("First, create fifo")

        os.mkfifo(fifo)

        fd = os.open(fifo,os.O_RDONLY|os.O_NONBLOCK)

        print("waiting for connection...")

        # Wait for message
        while True:
            try:
                data = os.read(fd,1)
                if data:
                    break
            except:
                continue

        # Got it, we're good to go
        os.close(fd)

        readerThread = ReadThread(fifo=fifo)
        writerThread = WriteThread(fifo=fifo+"2")

        
    #print("Session ready")
    
    readerThread.start()
    writerThread.start()     

    global rlock
    global wlock

    while rlock and wlock:
        time.sleep(1)

    readerThread.stop()
    writerThread.stop()

    readerThread.join()
    writerThread.join()

    if os.path.exists(fifo):
        os.remove(fifo)
    if os.path.exists(fifo+"2"):
        os.remove(fifo+"2")

if __name__=="__main__":
    main()
