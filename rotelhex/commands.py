CODES = {
 "power_toggle"  : b"\x00",
 "power_off"     : b"\x01",
 "power_on"      : b"\x02",
 "volume_up"     : b"\x13",
 "volume_down"   : b"\x14",
 "mute_toggle"   : b"\x15",
 "source_phono"  : b"\x03",
 "source_cd"     : b"\x04",
 "source_tuner"  : b"\x05",
 "source_video"  : b"\x06",
 "source_aux1"   : b"\x07",
 "source_aux2"   : b"\x08",
 "source_tape1"  : b"\x09",
 "source_tape2"  : b"\x0a",
 "record_phono"  : b"\x0b",
 "record_cd"     : b"\x0c",
 "record_tuner"  : b"\x0d",
 "record_video"  : b"\x0e",
 "record_aux1"   : b"\x0f",
 "record_aux2"   : b"\x10",
 "record_tape1"  : b"\x11",
 "record_tape2"  : b"\x12",
 "record_select" : b"\x1a",
 "char_enter"    : b"\x16",
 "char_next"     : b"\x17",
 "char_prev"     : b"\x18",
 "label_change"  : b"\x19",
 "display_toggle": b"\x1b",
}

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
    bs = self.device_id + self.command_type + self.data
    self.count = len(bs).to_bytes(1,'big')
    bs = self.count + bs
    self.chksum = sum(bs).to_bytes(1,'big')
    bs += self.chksum
    self.raw = MAGIC_PREFIX + meta_encode(bs)

  def __repr__(self):
    return str(self.__dict__)

class Response:
  def __init__(self, raw):
    self.raw = raw
    self.payload = meta_decode(raw)
    chksum = self.payload[-1]
    self.bad_checksum = sum(self.payload[:-1]) == chksum
    self.device_id = self.payload[0]
    self.command_type = self.payload[1]
    self.data = self.payload[2:-1]
    self.poweroff    = self.data[0] == 255
    self.powering_on = not self.poweroff and self.data[5] == 255

  def __repr__(self):
    return str(self.__dict__)

