import sys
from datetime import datetime

class Logger:
    # Source https://stackoverflow.com/a/14906787
    def __init__(self, logPath, printDateTime = False):
        self.terminal = sys.stdout
        self.log = open(logPath, "a", 1)
        self.printDateTime = printDateTime
        self.lineSkip = True
   
    def write(self, message):
        #if self.printDateTime and message != "\n" and message != "\t":
        if self.printDateTime and self.lineSkip:
            # Source https://www.programiz.com/python-programming/datetime/current-datetime
            # Added a bunch of hardcoded checks of my own
            # datetime object containing current date and time
            now = datetime.now()
            # dd/mm/YY H:M:S
            dt_string = now.strftime("%Y-%m-%d %H:%M:%S")
            if not f"[{dt_string}]" in message:
                message = f"[{dt_string}] " + message
        self.lineSkip = (message[-1] == "\n")
        self.terminal.write(message)
        self.log.write(message)  

    def flush(self):
        # this flush method is needed for python 3 compatibility.
        # this handles the flush command by doing nothing.
        # you might want to specify some extra behavior here.
        pass   

    def setPrintDateTime(self, bool):
        self.printDateTime = bool

