#!/usr/bin/env python
from __future__ import division, print_function
# for distutils compatibility we do not use unicode_literals in this module
import contextlib
from distutils.command.build_py import build_py
import io
import os
import shutil
import subprocess
import sys
if sys.version_info < (3,):
    from cStringIO import StringIO as BytesIO
    from urllib2 import urlopen, URLError
else:
    from io import BytesIO
    from urllib.request import urlopen, URLError
from zipfile import ZipFile


def _abort(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


try:
    from setuptools import setup
except ImportError:
    _abort("Please install setuptools by following the instructions at\n"
           "    https://pypi.python.org/pypi/setuptools")


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if os.name == "posix":
    PACKAGE_DATA = [os.path.join("redeal", "libdds.so")]
elif os.name == "nt":
    PACKAGE_DATA = [os.path.join("redeal", "dds.dll")]
else:
    PACKAGE_DATA = []


class make_build(build_py, object):
    def run(self):
        super(make_build, self).run()
        if os.name == "posix":
            orig_dir = os.getcwd()
            try:
                os.chdir(os.path.join(BASE_DIR, "dds", "src"))
            except OSError as exc:
                if exc.errno == 2: # FileNotFoundError
                    _abort("""\
DDS sources are missing.
If you are using a git checkout, run
    git submodule init && git submodule update
If you downloaded a zip archive from github, get a zip archive from
    https://github.com/dds-bridge/dds/""")
            subprocess.check_call(
                ["make", "-f", "Makefiles/Makefile_linux_shared"])
            os.chdir(orig_dir)
            shutil.move(os.path.join(BASE_DIR, "dds", "src", "libdds.so"),
                        os.path.join(self.build_lib, "redeal", "libdds.so"))


setup(
    cmdclass={"build_py": make_build},
    name="redeal",
    version="0.2.0",
    author="Antony Lee",
    author_email="anntzer.lee@gmail.com",
    packages=["redeal"],
    package_data={"redeal": PACKAGE_DATA},
    entry_points={"console_scripts": ["redeal = redeal.__main__:console_entry"],
                  "gui_scripts": ["redeal-gui = redeal.__main__:gui_entry"]},
    url="http://github.com/anntzer/redeal",
    license="LICENSE.txt",
    description="A reimplementation of Thomas Andrews' Deal in Python.",
    long_description=io.open("README.md", encoding="utf-8").read(),
    install_requires=
        ["colorama>=0.2.4"] +
        (["enum34>=1.0.4"] if sys.version_info < (3, 4) else [])
)
