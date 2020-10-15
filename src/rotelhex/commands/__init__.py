MAGIC_PREFIX         = b'\xfe'
ENCODE_PREFIX        = b'\xfd'

DEFAULT_DEVICE_ID    = b'\x04'
DEFAULT_COMMAND_TYPE = b'\x10'

def enc(b):
  val = int.from_bytes(b,'big')
  diff = val - int.from_bytes(ENCODE_PREFIX,'big')
  return ENCODE_PREFIX + diff.to_bytes(1,'big')

def meta_encode(data):
  return data.replace(ENCODE_PREFIX, enc(ENCODE_PREFIX)
            ).replace(MAGIC_PREFIX,  enc(ENCODE_PREFIX))

def meta_decode(data):
  return data.replace(enc(ENCODE_PREFIX), ENCODE_PREFIX
            ).replace(enc(MAGIC_PREFIX),  ENCODE_PREFIX)

class Command:
  def __init__(self, data, device_id=DEFAULT_DEVICE_ID ,command_type=DEFAULT_COMMAND_TYPE):
    self.data         = data
    self.device_id    = device_id
    self.command_type = command_type

    payload = self.device_id + self.command_type + self.data
    self.count = len(payload).to_bytes(1,'big')

    bs = self.count + payload
    self.chksum = sum(bs).to_bytes(1,'big')
    bs += self.chksum
    self.raw = MAGIC_PREFIX + meta_encode(bs)

  def __repr__(self):
    return str(self.__dict__)

class Response:
  def __init__(self, raw):
    self.raw            = raw
    self.payload        = meta_decode(raw)

    chksum              = self.payload[-1]
    self.bad_checksum   = sum(self.payload[:-1]) == chksum
    self.device_id      = self.payload[0]
    self.command_type   = self.payload[1]
    self.data           = self.payload[2:-1]
    self.display_source = self.data[0:5]
    self.display_record = self.data[6:11]
    self.poweroff       = self.data[0] == 255
    if len(self.data) >= 6:
      self.powering_on = not self.poweroff and self.data[5] == 255
    else:
      self.powering_on = None

  def __repr__(self):
    return str(self.__dict__)

