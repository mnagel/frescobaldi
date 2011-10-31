#! python

"""
This package provides the functionality of the PortMIDI library to Python.

It tries various ways to import the PyRex-based interface by John Harrison,
by trying 'pypm', 'pyportmidi._pyportmidi', 'pygame.pypm' (without importing the
rest or PyGame) or the plain portmidi library via a ctypes-based interface.

The module provides one simple API to control the most important parts of
PortMIDI, very much like the pygame.midi api.

To affect the order in which PortMIDI is tried, alter the global try_order list.
The first name in the list if tried first. This only works before init() is
called for the first time.

The module can always be imported, but only init() and available() can be used
if PortMIDI itself is not available.

This module itself is in the public domain.

"""

import atexit
import collections


__all__ = [
    'available', 'init', 'quit',
    'get_count', 'get_device_info',
    'get_default_input_id', 'get_default_output_id',
    'time',
    'Input', 'Output',
]

pypm = None
_initalized = None



# you can change this before calling init() for the first time
try_order = ['pypm', 'pyportmidi', 'pygame', 'ctypes']


def available():
    """Returns True if PortMIDI is available."""
    return _setup()

def init():
    """Initializes the PortMIDI library for use.
    
    It is safe to call this more than once.
    
    """
    global _initalized
    if _setup() and not _initalized:
        pypm.Initialize()
        _initalized = True

def quit():
    """Terminates the PortMIDI library.
    
    It is safe to call this more than once.
    On application exit this is also called.
    
    """
    global _initalized
    if pypm and _initalized:
        pypm.Terminate()
        _initalized = False

def get_count():
    """Returns the number if available MIDI devices."""
    _check_initialized()
    return pypm.CountDevices()

def get_default_input_id():
    """Returns the default input device number."""
    _check_initialized()
    return pypm.GetDefaultInputDeviceID()

def get_default_output_id():
    """Returns the default output device number."""
    _check_initialized()
    return pypm.GetDefaultOutputDeviceID()

def get_device_info(device_id):
    """Returns information about a midi device.
    
    A file-tuple is returned:
    (api, device name, input, output, open),
    where:
        api: 
    """
    _check_initialized()
    return device_info(*pypm.GetDeviceInfo(device_id))

def time():
    """Returns the current time in ms of the PortMidi timer."""
    return pypm.Time()


class Input(object):
    """Reads MIDI input from a device."""
    def __init__(self, device_id, buffer_size=4096):
        self._input = None
        _check_initialized()
        _check_device_id(device_id)
        info = get_device_info(device_id)
        if not info.isinput:
            raise MidiException("not an input device")
        
        self._input = pypm.Input(device_id, buffer_size)

    def close(self):
        """Closes the input stream."""
        if self._input:
            self._input.Close()
        self._input = None

    def read(self, num_events):
        """reads num_events midi events from the buffer."""
        return self._input.Read(num_events)

    def poll(self):
        """Returns True if there's data, otherwise False."""
        r = self._input.Poll()
        if r == pypm.TRUE:
            return True
        elif r == pypm.FALSE:
            return False
        else:
            raise MidiException(pypm.GetErrorText(r))


class Output(object):
    """Writes MIDI output to a device."""

    def __init__(self, device_id, latency = 0, buffer_size = 4096):
        self._output = None
        _check_initialized()
        _check_device_id(device_id)
        info = get_device_info(device_id)
        if not info.isoutput:
            raise MidiException("not an output device")
        
        self._output = pypm.Output(device_id, latency)

    def close(self):
        """Closes the output stream."""
        if self._output:
            self._output.Close()
        self._output = None

    def write(self, data):
        """Writes a list of MIDI data to the output."""
        self._output.Write(data)

    def write_short(self, status, data1 = 0, data2 = 0):
        """Output MIDI information of 3 bytes or less."""
        self._output.WriteShort(status, data1, data2)

    def write_sys_ex(self, timestamp, message):
        """Writes a timestamped System-Exclusive MIDI message."""
        self._output.WriteSysEx(timestamp, message)

    def note_on(self, note, velocity=80, channel = 0):
        """turns a midi note on.  Note must be off."""
        _check_channel(channel)
        self.write_short(0x90 + channel, note, velocity)

    def note_off(self, note, velocity=0, channel = 0):
        """turns a midi note off.  Note must be on."""
        _check_channel(channel)
        self.write_short(0x80 + channel, note, velocity)

    def set_instrument(self, instrument_id, channel = 0):
        """select an instrument, with a value between 0 and 127"""
        if not 0 <= instrument_id <= 127:
            raise ValueError("invalid instrument id")
        _check_channel(channel)
        self.write_short(0xC0 + channel, instrument_id)




# helper functions

device_info = collections.namedtuple('device_info',
    'api name isinput isoutput isopen')

def _check_device_id(device_id):
    if not 0 <= device_id < get_count():
        raise ValueError("invalid device id")

def _check_channel(channel):
    if not 0 <= channel <= 15:
        raise ValueError("invalid channel number (must be 0..15)")

def _check_initialized():
    if not _initalized:
        raise RuntimeError("PortMIDI not initialized.")

def _setup():
    global pypm
    if pypm is None:
        for name in try_order:
            try:
                pypm = globals()['_do_import_' + name]()
                break
            except ImportError:
                continue
        else:
            pypm = False
    return bool(pypm)

def _do_import_pypm():
    return __import__('pypm')

def _do_import_pyportmidi():
    return __import__('pyportmidi._pyportmidi')

def _do_import_pygame():
    import imp
    # raises ImportError when not found
    pygame_path = imp.find_module('pygame')[1]
    file_handle, path, description = imp.find_module('pypm', [pygame_path])
    return imp.load_module('pypm', file_handle, path, description)

def _do_import_ctypes():
    raise ImportError() # TODO


class MidiException(Exception):
    """Raised on MIDI-specific errors."""
    pass
