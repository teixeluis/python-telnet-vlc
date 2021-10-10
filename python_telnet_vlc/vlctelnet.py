# Library for contacting VLC through telnet.

# Imports
import logging
import telnetlib
import re

# Error Imports
from socket import error as sockerr

_LOGGER = logging.getLogger(__package__)

# Exceptions
class VLCProcessError(Exception):
    """Something is wrong with VLC itself."""
    pass


class CommandError(Exception):
    """Something is wrong with the command."""
    pass


class ParseError(Exception):
    """Could not parse the information provided by VLC."""
    pass


class LuaError(Exception):
    """Problem with the VLC lua telnet."""
    pass


class ConnectionError(Exception):
    """Something is wrong with the connection to VLC."""
    pass


class AuthError(Exception):
    """Failed to login with provided password."""
    pass


# VLC Telnet Class
class VLCTelnet(object):
    """Conection to VLC using Telnet."""

    # Non commands
    def __init__(self, host="localhost", password="admin", port=4212, connect=True, login=True, retries=5):
        self.tn = telnetlib.Telnet()
        self.host = host
        self.port = port
        self.password = password
        self.retries = retries

        if connect:
            self.connect()
        # Login to VLC using password provided in the arguments
        if connect and login:
            self.login()

    def connect(self):
        """Connect to VLC."""
        # Connect to telnet.
        try:
            self.tn.open(self.host, port=self.port, timeout=10)
        except sockerr:
            raise ConnectionError("Could not connect to VLC. Make sure the Telnet interface is enabled and accessible.")

    def disconnect(self):
        """Disconnect from VLC."""
        self.tn.close()
        # reset the instance
        self.tn = telnetlib.Telnet()

    def login(self):
        """Login with password."""
        self.tn.read_until(b"Password: ")
        full_command = self.password.encode('utf-8') + b'\n'
        self.tn.write(full_command)
        for _ in range(2):
            command_output = self.tn.read_until(b'\n', timeout=10).decode('utf-8').strip('\r\n')
            if command_output:  # discard empty line once.
                break
        _LOGGER.debug("Password response: %s", command_output)
        parsed_output = command_output.lower()
        if "wrong password" in parsed_output:
            raise AuthError("Failed to login to VLC.")
        if "welcome" not in parsed_output:
            raise CommandError("Unexpected password response: {}".format(command_output))
        if "> " in command_output:
            return
        # Read until prompt
        self.tn.read_until(b'> ')

    def is_connected(self):
        try:
            self.tn.write(b'\n')
            answer = self.tn.read_until(b'> ')
            if answer:
                _LOGGER.debug("is_connected: answer obtained. Value: %s", answer)
                return True
            else:
                _LOGGER.debug("is_connected: failed to obtain answer.")
                return False
        except sockerr:
            return False

    def run_command(self, command):
        return self.do_run_command(command, self.retries)

    def do_send_string(self, string):
        """Run a command and return a list with the output lines."""
        # Put the command in a nice byte-encoded variable
        full_command = string.encode('utf-8') + b'\n'
        _LOGGER.debug("Sending command: %s", string)
        # Write out the command to telnet
        self.tn.write(full_command)
        # Get the command output, decode it, and split out the junk
        command_output = self.tn.read_until(b'> ').decode('utf-8').split('\r\n')[:-1]
        # Raise command error if VLC does not recognize the command.
        _LOGGER.debug("Command output: %s", command_output)
        if command_output:
            command_error = re.match(r"Error in.*", command_output[0])
            if re.match(r"Unknown command `.*'\. Type `help' for help\.", command_output[0]):
                raise CommandError("Unknown Command")
            elif command_error:
                raise LuaError(command_error.group())
        # Return the split output of the command
        return command_output

    def do_run_command(self, command, retries):
        _LOGGER.debug("do_run_command: retries: %s", retries)

        if self.is_connected():
            return self.do_send_string(command)
        else:
            if retries > 0:
                self.connect()
                return self.do_run_command(command, retries - 1)
            else:
                raise ConnectionError("Could not connect to VLC. Make sure the Telnet interface is enabled and accessible.")
    # Commands
    # Block 1
    def add(self, xyz):
        """Add XYZ to playlist."""
        command = 'add ' + xyz
        self.run_command(command)

    def enqueue(self, xyz):
        """Queue XYZ to playlist."""
        command = 'enqueue ' + xyz
        self.run_command(command)

    # Todo: Must figure out the playlist, search, and key commands.

    def sd(self, service='show'):
        """Show services discovery or toggle.
           Returns True for enabled and False for Disabled."""
        if service == 'show':
            return self.run_command('sd')
        else:
            command = 'sd ' + service
            output = self.run_command(command)[0]
            if 'enabled.' in output:
                return True
            elif 'disabled.' in output:
                return False
            else:
                raise ParseError("Could not parse the output of sd.")

    def play(self):
        """Play stream."""
        self.run_command('play')

    def stop(self):
        """Stop stream."""
        self.run_command('stop')

    def next(self):
        """Next playlist item."""
        self.run_command('next')

    def prev(self):
        """Previous playlist item."""
        self.run_command('prev')

    def goto(self, item):
        """Goto item at index."""
        command = 'goto {}'.format(item)
        self.run_command(command)

    def repeat(self, switch=True, setting='on'):
        """Toggle playlist repeat."""
        if switch:
            self.run_command('repeat')
        else:
            command = 'repeat ' + setting
            self.run_command(command)

    def loop(self, switch=True, setting='on'):
        """Toggle playlist loop."""
        if switch:
            self.run_command('loop')
        else:
            command = 'loop ' + setting
            self.run_command(command)

    def random(self, switch=True, setting='on'):
        """Toggle playlist random."""
        if switch:
            self.run_command('random')
        else:
            command = 'random ' + setting
            self.run_command(command)

    def clear(self):
        """Clear the playlist."""
        self.run_command('clear')

    def status(self):
        """Current playlist status."""
        status_output = self.run_command('status')
        _LOGGER.debug("status: status output: %s", status_output)
        if status_output is None:
            raise ParseError("Could not get status.")
        if len(status_output) == 3:
            inputloc = '%20'.join(status_output[0].split(' ')[3:-1])
            volume = int(status_output[1].split(' ')[3])
            state = status_output[2].split(' ')[2]
            returndict = {'input': inputloc, 'volume': volume, 'state': state}
        elif len(status_output) == 2:
            volume = int(status_output[0].split(' ')[3])
            state = status_output[1].split(' ')[2]
            returndict = {'volume': volume, 'state': state}
        else:
            raise ParseError("Could not get status.")
        return returndict

    def set_title(self, setto):
        """Set title in current item."""
        command = 'title ' + setto
        self.run_command(command)

    def title(self):
        """Get title in current item."""
        return self.run_command('title')[0]

    def title_n(self):
        """Next title in current item."""
        self.run_command('title_n')

    def title_p(self):
        """Previous title in current item."""
        self.run_command('title_p')

    def set_chapter(self, setto):
        """Set chapter in current item."""
        command = 'chapter ' + setto
        self.run_command(command)

    def chapter(self):
        """Get chapter in current item."""
        return self.run_command('chapter')[0]

    def chapter_n(self):
        """Next chapter in current item."""
        self.run_command('chapter_n')

    def chapter_p(self):
        """Previous chapter in current item."""
        self.run_command('chapter_p')

    # Block 2
    def seek(self, time):
        """Seek in seconds, for instance 'seek 12'."""
        command = 'seek ' + str(time)
        self.run_command(command)

    def pause(self):
        """Toggle pause."""
        self.run_command('pause')

    def fastforward(self):
        """Set to maximum rate."""
        self.run_command('fastforward')

    def rewind(self):
        """Set to minimum rate."""
        self.run_command('rewind')

    def faster(self):
        """Faster playing of stream."""
        self.run_command('faster')

    def slower(self):
        """Slower playing of stream."""
        self.run_command('slower')

    def normal(self):
        """Normal playing of stream."""
        self.run_command('normal')

    def rate(self, newrate):
        """Set playback rate to value."""
        command = 'rate ' + newrate
        self.run_command(command)

    def frame(self):
        """Play frame by frame."""
        self.run_command('frame')

    def fullscreen(self, switch=True, setting='on'):
        """Toggle fullscreen."""
        if switch:
            self.run_command('f')
        else:
            command = 'f ' + setting
            self.run_command(command)

    def info(self):
        """Information about the current stream."""
        section = None
        data = {}
        for l in self.run_command('info'):
            if l[0] == '+':
                # Example: "+----[ Stream 5 ]" or "+----[ Meta data ]"
                if 'end of stream info' in l: continue
                section = l.split('[')[1].replace(']','').strip().split(' ')[1]
                try:
                    section = int(section)
                except ValueError:
                    pass
                data[section] = {}
            elif l[0] == '|':
                # Example: "| Description: Closed captions 4"
                if len(l[2:]) == 0: continue
                key, value = l[2:].split(':',1)
                try:
                    value = int(value)
                except ValueError:
                    try:
                        value = float(value)
                    except ValueError:
                        value = value.strip()
                data[section][key.strip()] = value
            else:
                raise ParseError("Unexpected line in info output")
        return data

    # Skipping stats
    def get_time(self):
        """Seconds elapsed since stream's beginning."""
        stream_time = self.run_command('get_time')[0]
        return int(stream_time) if stream_time else 0

    def is_playing(self):
        """True if a stream plays, False otherwise."""
        command_output = self.run_command('is_playing')[0]
        return True if command_output == '1' else False

    def get_title(self):
        """The title of the current stream."""
        return self.run_command('get_title')[0]

    def get_length(self):
        """The length of the current stream."""
        stream_length = self.run_command('get_length')[0]
        return int(stream_length) if stream_length else 0

    # Block 3
    def set_volume(self, setto):
        """Set audio volume."""
        command = 'volume {}'.format(int(setto))
        self.run_command(command)

    def volume(self):
        """Get audio volume (0 to 500)."""
        return int(self.run_command('volume')[0])

    def volup(self, raiseby):
        """Raise audio volume X steps."""
        command = 'volup {}'.format(int(raiseby))
        self.run_command(command)

    def voldown(self, raiseby):
        """Lower audio volume X steps."""
        command = 'voldown {}'.format(int(raiseby))
        self.run_command(command)

    # The following 'get' commands ARE NOT PARSED! Must do later :D
    def set_adev(self, setto):
        """Set audio device."""
        command = 'adev ' + setto
        self.run_command(command)

    def adev(self):
        """Get audio device."""
        return self.run_command('adev')[0]

    def set_achan(self, setto):
        """Set audio channels."""
        command = 'achan ' + setto
        self.run_command(command)

    def achan(self):
        """Get audio channels."""
        return self.run_command('achan')[0]

    def set_atrack(self, setto):
        """Set audio track."""
        command = 'atrack ' + str(setto)
        self.run_command(command)

    def atrack(self):
        """Get audio track."""
        return self.run_command('atrack')[0]

    def set_vtrack(self, setto):
        """Set video track."""
        command = 'vtrack ' + str(setto)
        self.run_command(command)

    def vtrack(self):
        """Get video track."""
        return self.run_command('vtrack')[0]

    def set_vratio(self, setto):
        """Set video aspect ratio."""
        command = 'vratio ' + setto
        self.run_command(command)

    def vratio(self):
        """Get video aspect ratio."""
        return self.run_command('vratio')[0]

    def set_crop(self, setto):
        """Set video crop."""
        command = 'crop ' + setto
        self.run_command(command)

    def crop(self):
        """Get video crop."""
        return self.run_command('crop')[0]

    def set_zoom(self, setto):
        """Set video zoom."""
        command = 'zoom ' + setto
        self.run_command(command)

    def zoom(self):
        """Get video zoom."""
        return self.run_command('zoom')[0]

    def set_vdeinterlace(self, setto):
        """Set video deintelace."""
        command = 'vdeinterlace ' + setto
        self.run_command(command)

    def vdeinterlace(self):
        """Get video deintelace."""
        return self.run_command('vdeinterlace')[0]

    def set_vdeinterlace_mode(self, setto):
        """Set video deintelace mode."""
        command = 'vdeinterlace_mode ' + setto
        self.run_command(command)

    def vdeinterlace_mode(self):
        """Get video deintelace mode."""
        return self.run_command('vdeinterlace_mode')[0]

    def snapshot(self):
        """Take video snapshot."""
        self.run_command('snapshot')

    def set_strack(self, setto):
        """Set subtitles track."""
        command = 'strack ' + setto
        self.run_command(command)

    def strack(self):
        """Get subtitles track."""
        return self.run_command('strack')[0]

    # Block 4 - Skipping a few useless ones when using a library
    def vlm(self):
        """Load the VLM."""
        self.run_command('vlm')

    def logout(self):
        """Exit."""
        self.run_command('logout')

    def shutdown(self):
        """Shutdown VLC."""
        self.run_command('shutdown')
