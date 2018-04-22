#!/usr/bin/env python2.7

import json
import multiprocessing
from multiprocessing.managers import SyncManager
from multiprocessing import Lock
import os
import Queue

import logging
import logging.handlers
import argparse
import sys
import time  # this is only being used as part of the example

import signal

# Deafults
LOG_FILENAME = "/var/log/playbookrunner.log"
LOG_LEVEL = logging.INFO  # Could be e.g. "DEBUG" or "WARNING"

MAX_WORKERS = 3
STATE_FILE = '/opt/playbookrunner/playbookrunner.json'

# Define and parse command line arguments
parser = argparse.ArgumentParser(description="My simple Python service")
parser.add_argument("-l", "--log", help="file to write log to (default '" + LOG_FILENAME + "')")

# If the log file is specified on the command line then override the default
args = parser.parse_args()
if args.log:
	LOG_FILENAME = args.log

# Configure logging to log to a file, making a new file at midnight and keeping the last 3 day's data
# Give the logger a unique name (good practice)
logger = logging.getLogger(__name__)
# Set the log level to LOG_LEVEL
logger.setLevel(LOG_LEVEL)
# Make a handler that writes to a file, making a new file at midnight and keeping 3 backups
handler = logging.handlers.TimedRotatingFileHandler(LOG_FILENAME, when="midnight", backupCount=3)
# Format each log message like this
formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
# Attach the formatter to the handler
handler.setFormatter(formatter)
# Attach the handler to the logger
logger.addHandler(handler)

# Make a class we can use to capture stdout and sterr in the log
class MyLogger(object):
	def __init__(self, logger, level):
		"""Needs a logger and a logger level."""
		self.logger = logger
		self.level = level

	def write(self, message):
		# Only log if there is a message (not just a new line)
		if message.rstrip() != "":
			self.logger.log(self.level, message.rstrip())

	def flush(self):
		for handler in self.logger.handlers:
			handler.flush()

# Replace stdout with logging to file at INFO level
sys.stdout = MyLogger(logger, logging.INFO)
# Replace stderr with logging to file at ERROR level
sys.stderr = MyLogger(logger, logging.ERROR)

def printlock(lock, message):
	lock.acquire()
	print message
	lock.release()

def workerMain(inQ, statQ, lock):
	try:
		printlock(lock, "{} working".format(os.getpid()))
		while True:
			try:
				item = inQ.get(True,1)
				printlock(lock, "{} got item {}".format(os.getpid(), item))
			except Queue.Empty: # Queue here refers to the  module, not a class
				pass
	except KeyboardInterrupt:
		printlock(lock, "{} Keyboard interrupt in process: ".format(os.getpid()))
	finally:
		printlock(lock, "{} cleaning up thread".format(os.getpid()))

def mgr_init():
	signal.signal(signal.SIGINT, signal.SIG_IGN)
	#print 'debug: mgr_init: initialized manager'

def main():
	try:
		lock = Lock()
		#thePool = multiprocessing.Pool(MAX_WORKERS, workerMain,(inputQueue, statusQueue,))
		thePool=[]
		
		printlock(lock, 'debug: creating input/output queues...')
		#manager=multiprocessing.Manager()
		manager = SyncManager()
		# explicitly starting the manager, and telling it to ignore the interrupt signal
		manager.start(mgr_init)

		inputQueue = manager.Queue()
		statusQueue = manager.Queue()
		
		for num in range(MAX_WORKERS):
			proc = multiprocessing.Process(target=workerMain, args=(inputQueue, statusQueue, lock,))
			proc.daemon = True
			proc.start()
			thePool.append(proc)
		
		printlock(lock, 'debug: [%s]' % ', '.join(map(str, thePool)))
		
		stateDict={}
		
		if os.path.isfile(STATE_FILE):
			with open(STATE_FILE) as json_file:  
			    stateDict=json.load(json_file)
		else:
			printlock(lock, 'error: state file {}  does not exist. Start program with --init parameter to create it'.format(STATE_FILE))
			sys.exit(1)
			#json = json.dumps(stateDict)
			#f = open(STATE_FILE,"w")
			#f.write(json)
			#f.close()
	
		printlock(lock, 'debug: seeding input queue...')
		for i in range(5):
			inputQueue.put("hello")
			inputQueue.put("world")
		
		while True:
			time.sleep(1)
			printlock(lock, "main: doing something in a loop ...")
		
		printlock(lock, "main: End of the program. I was killed gracefully :)")
	except KeyboardInterrupt:
		print(lock, "debug: main(): Keyboard interrupt")
		for proc in thePool:
			printlock(lock, 'debug: before killing process ' + proc.name)
			proc.terminate()
			time.sleep(0.5)
			while proc.is_alive():
			    time.sleep(1)
			printlock(lock, "debug: [MAIN]: WORKER is a goner")
			proc.join(timeout=1.0)
			printlock(lock, "debug: [MAIN]: Joined WORKER successfully!")

if __name__ == "__main__":
	main()
