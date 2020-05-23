import select
import serial
import threading
import time

from importlib import import_module

from . import commands
from . import charmap
from . import display

DEFAULT_PORT    = '/dev/ttyS0'
DEFAULT_BAUD    = 2400
DEFAULT_TIMEOUT = 5

class Rotel:
  def __init__(self, model, port=DEFAULT_PORT, baudrate=DEFAULT_BAUD, timeout=DEFAULT_TIMEOUT, display_callbacks=[], restart_on_init=True, debug=False):

    self._model=import_module("..commands.{}".format(model),__name__)
    for name,code in self._model.CODES.items():
      add_command(Rotel, name, code)

    self._serial         = serial.Serial(port, baudrate=baudrate, timeout=timeout)
    self._debug          = debug
    self._serial_lock    = threading.Lock()
    self._display        = display.Display(callbacks=display_callbacks)
    self._run_monitor    = True
    self._monitor_thread = threading.Thread(target=self.__monitor)

    self._monitor_thread.daemon = True
    self._monitor_thread.start()

    if restart_on_init:
        if self._debug: print("Restarting on initialization")
        self.restart()

  def restart(self):
    self.power_toggle()
    time.sleep(5)
    self.power_toggle()

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
    self.set_source(function)
    self.label_change()
    for index in indices:
      for i in range(index):
        self.char_next()
      self.char_enter()
    if len(indices) < 5:
      self.label_change()

  def set_source(self, function):
    set_function_code = self._model.CODES["source_" + function]
    self.send(commands.Command(set_function_code))
  def set_record(self, function):
    set_function_code = self._model.CODES["record_" + function]
    self.send(commands.Command(set_function_code))

def add_command(cls, name, code):
  def command(self):
    return self.send(commands.Command(code))
 
  command.__doc__  = "Execute {} command".format(name)
  command.__name__ = name
  setattr(cls, command.__name__, command)
