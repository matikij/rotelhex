import serial
import time
import threading
import select
import time

from . import commands
from . import charmap
from . import display

DEFAULT_PORT    = '/dev/ttyS0'
DEFAULT_BAUD    = 2400
DEFAULT_TIMEOUT = 5

class Rotel:
  def __init__(self, port=DEFAULT_PORT, baudrate=DEFAULT_BAUD, timeout=DEFAULT_TIMEOUT, display_callbacks=[], debug=False):
    self._serial         = serial.Serial(port, baudrate=baudrate, timeout=timeout)
    self._debug          = debug
    self._serial_lock    = threading.Lock()
    self._display        = display.Display(callbacks=display_callbacks)
    self._run_monitor    = True
    self._monitor_thread = threading.Thread(target=self.__monitor)

    self._monitor_thread.daemon = True
    self._monitor_thread.start()

    # self.update_display()

  def update_display(self):
    self.label_change()
    self.label_change()

  def send(self,command):
    self.write(command.raw)
    time.sleep(0.02)

  def send_and_read(self,command):
    self.send(command)
    return self.read(length=4)

  def write(self,data):
    self._serial.write(data)
    self._serial.flush()

  def read(self,length=1):
    responses=[]
    start_reading=time.time()
    while self._serial.read(1) == b'\xfe':
      if self._debug: print("Waited for: {}".format(time.time() - start_reading))
      count = self._serial.read(1)[0]
      responses.append(commands.Response(self._serial.read(count + 1)))
      if self._debug: print("Got: {}".format(responses[-1].raw))
      start_reading=time.time()
      if len(responses) >= length:
        break
    return responses

  @property
  def display(self):
      return str(self._display)

  def __monitor(self):
    while self._run_monitor:
      if self._serial.is_open:
        ready = select.select([self._serial],[],[])[0]
        if self._debug: print("ready: {}".format(ready))
        responses = self.read()
        if len(responses) > 0:
          self._display.update(responses[-1])
      else:
        print("Serial port not open, trying to fix")
        self._serial.open()

  def monitor_join(self):
    self._monitor_thread.join()

  def set_label(self,function,label):
    if len(label) > 5:
      raise ValueError("label cannot be longer than 5 characters")
    indices = [ charmap.CHARMAP.index(c) for c in label ]
    set_function_code = commands.CODES["source_" + function]
    self.send(commands.Command(set_function_code))
    self.label_change()
    for index in indices:
      for i in range(index):
        self.char_next()
      self.char_enter()
    if len(indices) < 5:
      self.label_change()

def add_command(cls, name, code):
  def command(self):
    return self.send(commands.Command(code))
 
  command.__doc__  = "Execute {} command".format(name)
  command.__name__ = name
  setattr(cls, command.__name__, command)

for name,code in commands.CODES.items():
  add_command(Rotel, name, code)
