import math
import socket, errno

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    s.bind(("127.0.0.1", 5000))
except socket.error as e:
    if e.errno == errno.EADDRINUSE:
        print("Port is already in use")
    else:
        # something else raised the socket.error exception
        print(e)

s.close()


import subprocess

proc1 = subprocess.Popen(['ps', 'aux'], stdout=subprocess.PIPE)
proc2 = subprocess.Popen(['grep', 'serve --debug'], stdin=proc1.stdout,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)

proc1.stdout.close() # Allow proc1 to receive a SIGPIPE if proc2 exits.
out, err = proc2.communicate()

procesList = str(out)
processCount = len(procesList.split("\n"))

if (processCount >= 3):
	pass

print('out: {0}'.format(out))
print('err: {0}'.format(err))


length = 150
diameter = 1.0
density = 1.0
radius = diameter / 2.0;
volume = length * math.pi * (radius * radius) / 1000
result = volume * density

print(result)
