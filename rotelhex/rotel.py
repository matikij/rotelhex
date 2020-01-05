import serial
import time

from . import commands

DEFAULT_PORT    = '/dev/ttyS0'
DEFAULT_BAUD    = 2400
DEFAULT_TIMEOUT = 5

class Rotel:
  def __init__(self, port=DEFAULT_PORT, baudrate=DEFAULT_BAUD, timeout=DEFAULT_TIMEOUT):
    self.serial = serial.Serial(port, baudrate=baudrate, timeout=timeout)
  def send_and_read(self,command):
    self.write(command.raw)
    return self.read_all()
  def write(self,data):
    self.serial.write(data)
    self.serial.flush()
  def read_all(self):
    responses=[]
    start_reading=time.time()
    while self.serial.read(1) == b'\xfe' and len(responses) <= 4:
      print("Waited for: {}".format(time.time() - start_reading))
      count    = self.serial.read(1)[0]
      responses.append(commands.Response(self.serial.read(count + 1)))
      start_reading=time.time()
    return responses

def add_command(cls, name, code):
  def command(self):
    return self.send_and_read(commands.Command(code))
 
  command.__doc__  = "Execute {} command".format(name)
  command.__name__ = name
  setattr(cls,command.__name__, command)

for name,code in commands.CODES.items():
  add_command(Rotel, name, code)


