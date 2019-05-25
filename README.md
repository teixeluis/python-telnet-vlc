python-telnet-vlc
==========
A simple python library to interface with a VLC player using the telnet interface.

Installation
```
pip install python-telnet-vlc
```

Usage:

```python
from python_telnet_vlc import VLCTelnet
v = VLCTelnet("192.168.1.44", "password", 4212)
v.add("http://radios-mp3-uy.cdn.nedmedia.io/uy-futura.mp3")
v.play()

```

More Info: <https://wiki.videolan.org/Documentation:Modules/telnet/>

Original author: @stephenmac7