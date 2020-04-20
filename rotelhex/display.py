import threading

BASIC_FUNTIONS=[
  b"PHONO",
  b" CD  ",
  b"TUNER",
  b"VIDEO",
  b" AUX1",
  b" AUX2",
  b"TAPE1",
  b"TAPE2",
  b" OFF "
]

class Display:
  def __init__(self, callbacks=[]):
    self._callbacks        = callbacks
    self._lock             = threading.Lock()
    self._source           = b"     "
    self._basic_source     = b"     "
    self._record           = b"     "
    self._basic_record     = b"     "
    self._label_change     = False
    self._current_char_idx = None
    self._current_char     = None

  def update(self, response):
    prev_source = ""
    prev_basic_source = ""
    prev_record = ""
    prev_basic_record = ""
    with self._lock:
      update = DisplayUpdate(self, response)
      self._source = response.display_source
      self._record = response.display_record
      self._basic_source = update.curr_basic_source
      self._basic_record = update.curr_basic_record
    for callback in self._callbacks:
      callback(update)
    if self._label_change:
      source_diff = [i for i in range(len(update.prev_source)) if update.prev_source[i] != response.display_source[i] ]
      if len(source_diff) == 1:
        self._current_char_idx = source_diff[0]
        if update.prev_source[self._current_char_idx] == b' '[0]: # what I want is 32
          self._current_char = bytes([response.display_source[self._current_char_idx]])

  @property
  def source(self):
    with self._lock:
      return self._source

  @property
  def record(self):
    with self._lock:
      return self._record

  @property
  def label_change(self):
    return self._label_change

  @label_change.setter
  def label_change(self,val):
    self._label_change = val
    if not val:
      self._current_char_idx = None
      self._current_char     = None

  def __str__(self):
    ret = "{} {}".format(self.source.decode("cp850"),self.record.decode("cp850"))
    if self._label_change:
      ret += " current_char: {}, idx: {}".format(self._current_char, self._current_char_idx)
    return ret

class DisplayUpdate:
  def __init__(self, display, response):
    self._prev_source = display._source
    self._prev_record = display._record
    self._prev_basic_source = display._basic_source
    self._prev_basic_record = display._basic_record
    self._curr_source = response.display_source
    self._curr_record = response.display_record
    if self._curr_source in BASIC_FUNTIONS:
      self._curr_basic_source = self._curr_source
    else:
      self._curr_basic_source = self._prev_basic_source
    if self._curr_record in BASIC_FUNTIONS:
      self._curr_basic_record = self._curr_record
    else:
      self._curr_basic_record = self._prev_basic_record
  
  @property
  def prev_source(self):
    return self._prev_source

  @property
  def prev_record(self):
    return self._prev_record

  @property
  def prev_basic_source(self):
    return self._prev_basic_source

  @property
  def prev_basic_record(self):
    return self._prev_basic_record
  
  @property
  def curr_source(self):
    return self._curr_source

  @property
  def curr_record(self):
    return self._curr_record

  @property
  def curr_basic_source(self):
    return self._curr_basic_source

  @property
  def curr_basic_record(self):
    return self._curr_basic_record
