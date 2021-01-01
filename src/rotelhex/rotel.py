import asyncio
import serial_asyncio
import time

from importlib import import_module

from . import commands
from . import charmap
from . import display

DEFAULT_PORT    = '/dev/ttyS0'
DEFAULT_BAUD    = 2400
DEFAULT_TIMEOUT = 5

class Rotel:
  def __init__(self, model, debug=False):
    self._model = import_module("..commands.{}".format(model),__name__)
    self._debug = debug
    for name,code in self._model.CODES.items():
      add_command(Rotel, name, code)

  async def connect(self, port=DEFAULT_PORT, baudrate=DEFAULT_BAUD, timeout=DEFAULT_TIMEOUT, display_callbacks=[], restart_on_connect=True):
    self._reader, self._writer = await serial_asyncio.open_serial_connection(url=port, baudrate=baudrate, timeout=timeout)
    self._monitor_task         = asyncio.create_task(self.__monitor())
    self._display              = display.Display(callbacks=display_callbacks)
    if restart_on_connect:
      if self._debug: print("Restarting on initialization")
      await self.restart()

  async def restart(self):
    await self.power_toggle()
    await asyncio.sleep(4)
    await self.power_toggle()
    await asyncio.sleep(4)

  async def send(self,command):
    await self.write(command.raw)
    await asyncio.sleep(0.02)

  async def write(self,data):
    self._writer.write(data)
    await asyncio.sleep(0.02)

  async def read(self,length=1):
    responses=[]
    start_reading=time.time()
    try:
      while await self._reader.readexactly(1) == b'\xfe':
        if self._debug: print("Waited for: {}".format(time.time() - start_reading))
        count = (await self._reader.readexactly(1))[0]
        if self._debug: print("Reading {} chars".format(count))
        payload = await self._reader.readexactly(count + 1)
        if self._debug: print("Got payload: {}".format(payload))
        responses.append(commands.Response(payload))
        if self._debug: print("Got: {}".format(responses[-1].raw))
        start_reading=time.time()
        if len(responses) >= length:
          break
    except IncompleteReadError as e:
      print(e)
      print("Got {}".format(e.partial))
    return responses

  @property
  def display(self):
    return str(self._display)

  @property
  def basic_source(self):
    return self._display.basic_source

  @property
  def source(self):
    return self._display.source

  @property
  def basic_record(self):
    return self._display.basic_record

  @property
  def record(self):
    return self._display.record

  @property
  def valid_commands(self):
    return [ k for k in self._model.CODES.keys() ]

  @property
  def basic_sources(self):
    return [ s[len("source_"):] for s in self.valid_commands if s.startswith("source_")]

  async def __monitor(self):
    while True:
      responses = await self.read()
      if len(responses) > 0:
        await self._display.update(responses[-1])

  async def set_label(self,function,label):
    if len(label) > 5:
      raise ValueError("label cannot be longer than 5 characters")
    indices = [ charmap.CHARMAP.index(c) for c in label ]
    await self.set_source(function)
    await self.label_change()
    for index in indices:
      for i in range(index):
        await self.char_next()
      await self.char_enter()
    if len(indices) < 5:
      await self.label_change()

  async def set_source(self, function):
    await self.send_command("source_" + function)
  async def set_record(self, function):
    await self.send_command("record_" + function)
  async def send_command(self, name):
    code = self._model.CODES[name]
    await self.send(commands.Command(code))

def add_command(cls, name, code):
  async def command(self):
    return await self.send(commands.Command(code))
 
  command.__doc__  = "Execute {} command".format(name)
  command.__name__ = name
  setattr(cls, command.__name__, command)
