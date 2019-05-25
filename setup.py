#!/usr/bin/python3

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="python-telnet-vlc",
    version="1.0.4",
    author="stephenmac7, rodripf",
    author_email="rodripf@gmail.com",
    description="A library to control or get information about VLC using Telnet",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/rodripf/python-telnet-vlc",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Topic :: Multimedia"
    ],
)