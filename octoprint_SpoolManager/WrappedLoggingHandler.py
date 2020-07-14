

from logging import StreamHandler

class WrappedLoggingHandler(StreamHandler):

    def __init__(self, wrappedLogger):
        StreamHandler.__init__(self)
        self.wrappedLogger = wrappedLogger


    def emit(self, record):
		msg = self.format(record)
		self.wrappedLogger.debug(msg) # this is it!!!!
		# self.wrappedLogger.handle(record)
