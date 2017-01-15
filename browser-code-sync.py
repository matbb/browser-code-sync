#!/usr/bin/env python3

import time
import os
import argparse
import sys
import json
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
from queue import Empty, LifoQueue
import threading

import logging

parser = argparse.ArgumentParser(
        description="""Synchronization of CodeMirror derived code editors
        inside browser with local disk files or stdin/stdout streams.

        Uses : chromium debug bridge through chromote package in python3""",
        )

parser.add_argument('action', metavar='action', type=str,
        choices=["push","pull","syncfolder","execjs"],
        help='What to do')
parser.add_argument('files', metavar='files', type=str, nargs='+',
                    help="""
                    For push / pull : <filename or - for stdin / stdout> <index of codemirror editor, defaults to 0>\n
                    For syncfolder  : <foldername> <file1> <file2> ...\n
                    For execjs      : <javascript to execute>\n
                    """,)
parser.add_argument( 
        "--chromium-port",
        type=int,
        default=9222,
        help="""Chromium debug port, i.e. : chromium-browser --remote-debugging-port=9222""",
        )
parser.add_argument( 
        "--debug",
        action="store_true",
        help="""Print more debug output""",
        )

args = parser.parse_args()

logger = logging.getLogger()

logger = logging.getLogger()
if args.debug : 
    logger.setLevel(logging.DEBUG)
else :
    logger.setLevel(logging.INFO)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

from chromote import Chromote 
logging.getLogger("requests").setLevel(logging.ERROR)
logging.getLogger("urllib3.connectionpool").setLevel(logging.ERROR)

# Chrome must be listening on localhost port 9222 
c = Chromote()
# Presuming only one tab is opened and it has what we need
tab = c.tabs[0]
# Prevent pushing and pulling the code at the same time with a lock 
lock = threading.Lock()

escapechars = [ 
        ( "\\", "\\\\" ),
        ( "\n", "\\n" ), ( "\r", "\\r" ), ( "\f", "\\f" ), ( "\t", "\\t" ),
        ( "\v", "\\v" ), ( "\b", "\\b" ),
        ( "'", "\\'" ), ( '"', '\\"' ),  ] 

def push_code( idx, code ) :
    """
    Push code to browser
    --------------------
    idx  : CodeMirror editor index 
    code : code to push
    """
    logger.debug("Pushing code, idx = " + str(idx) + " | " + code )
    for ch, replacement in escapechars : 
        code = code.replace( ch, replacement )
    lock.acquire()
    try :
        tab = c.tabs[0]
        tab.evaluate( """var tmpeditor{:d} = $('.CodeMirror')[{:d}].CodeMirror;""".format( idx, idx ) )
        val = tab.evaluate( """tmpeditor{:d}.setValue('{:s}')""".format( idx, code ) )
        logger.debug("Return value of push : " + str(val) )
    finally : 
        lock.release()
    return None

def pull_code( idx ) :
    """
    Pull code from the browser 
    --------------------------
    idx  : CodeMirror editor index 
    """
    logger.debug("Pulling code, idx = " + str(idx) )
    lock.acquire()
    try :
        tab = c.tabs[0]
        tab.evaluate("""var tmpeditor{:d} = $('.CodeMirror')[{:d}].CodeMirror;""".format( idx, idx ))
        data = json.loads( tab.evaluate("""tmpeditor{:d}.getValue()""".format(idx)) )
    finally : 
        lock.release()
    try : 
        code = data["result"]["result"]["value"]
        logger.debug("Pulling code, idx = " + str(idx) + ", code = " + code ) 
        return code
    except KeyError as e : 
        return ""

def exec_js( js ) :
    lock.acquire()
    try :
        tab = c.tabs[0]
        print( tab.evaluate( js ) )
    finally : 
        lock.release()


if args.action == "push" : 
    fn = args.files[0]
    inf = open(fn,"rt") if sys.argv[2] != "-" else sys.stdin
    try : 
        idx = int( args.files[1] ) 
    except :
        idx = 0
    logger.debug( "Pushing to file " + fn )
    code = inf.read()
    if fn != "-" : 
        inf.close()
    logger.debug( "Pushing contents : " + code )
    push_code( idx, code )

elif args.action == "pull" : 
    fn = args.files[0]
    inf = open(fn,"wt") if fn != "-" else sys.stdout
    try : 
        idx = int( args.files[1] ) 
    except :
        idx = 0
    logger.debug( "Pulling to file " + fn )
    code = pull_code( idx )
    logger.debug( "Pulled contents : " + code )
    inf.write( code )
    if fn != "-" : 
        inf.close()
elif args.action == "execjs" : 
    exec_js( args.files[0] )

elif args.action == "syncfolder" : 
    class folder_change_handler( FileSystemEventHandler ) : 
        """
        Watches a folder for file changes
        """
        def __init__( self, ev_queue, files ) : 
            self.ev_queue = ev_queue
            self.files = files
        def on_any_event( self, event ) :
            path = os.path.normpath( event.src_path )
            if path not in self.files : 
                return
            event.time = time.time()
            self.ev_queue.put( ( "folderchange", time.time(), self.files.index( path ) ) )
            logger.debug( "Event detected : path = " + event.src_path + " | " + str( event ) )

    class folder_change_watcher : 
        def __init__( self, ev_queue, foldername, files ) : 
            self.fch = folder_change_handler( ev_queue, files ) 
            self.observer = Observer()
            self.observer.schedule( self.fch, foldername ) 
            self.observer.start()

    class browser_change_watcher( threading.Thread ) : 
        def __init__( self, ev_queue, files, period=1 ) : 
            threading.Thread.__init__( self ) 
            self.n = len(files)
            self.ev_queue = ev_queue
            self.period = period
            self.code = [ "" for i in range(self.n) ]
        def set_code( self, code, idx ) : 
            self.code[idx] = code 
        def run( self ) :
            while True : 
                for idx in range( self.n ) : 
                    code = pull_code( idx )
                    if code != self.code[idx] : 
                        self.ev_queue.put( ( "browserchange", time.time(), idx ) )
                time.sleep( self.period )

    class code_synchronizer( threading.Thread ) : 
        def __init__( self, ev_queue, files, bcw, timeout=1 ) :
            threading.Thread.__init__( self ) 
            self.ev_queue = ev_queue
            self.files = files
            self.timeout = timeout
            self.bcw = bcw
            self.last_change = [ 0 for i in range(len(files)) ]
        def run( self ) : 
            while True : 
                what, when, idx = self.ev_queue.get()
                if self.last_change[idx] + self.timeout > when : 
                    continue
                if what == "browserchange" : 
                    code = pull_code( idx )
                    self.bcw.set_code( code, idx )
                    with open( self.files[idx], "wt" ) as f : 
                        f.write( code )
                    logger.info("SYNC : Pulling code : idx = " + str(idx) + " | \n" + code )
                else : 
                    with open( self.files[idx], "rt" ) as f : 
                        code = f.read()
                    push_code( idx, code )
                    time.sleep( self.timeout ) 
                    code = pull_code( idx )
                    self.bcw.set_code( code, idx )
                    logger.info("SYNC : Pushing code : idx = " + str(idx) + " | \n" + code )
                t = time.time()
                self.last_change[idx] = t

    foldername = args.files[0] 
    filenames = [ os.path.normpath( f ) for f in args.files[1:] ]
    print("Synchronizing files ", filenames, " in folder ", foldername )
    ev_queue = LifoQueue()
    fc = folder_change_watcher( ev_queue, foldername, filenames )
    bc = browser_change_watcher( ev_queue, filenames )
    bc.start()
    cs = code_synchronizer( ev_queue, filenames, bc )
    cs.start()
    cs.join()

