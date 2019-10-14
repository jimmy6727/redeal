try:
    from setuptools import setup
except ImportError:
    sys.exit("Please install setuptools by following the instructions at\n"
             "    https://pypi.python.org/pypi/setuptools")

from pathlib import Path
import shutil
import subprocess
import sys

from setuptools import Extension
from setuptools.command.build_ext import build_ext


if sys.platform == "win32":
    PACKAGE_DATA = ["dds-32.dll", "dds-64.dll"]
else:
    # On a POSIX system, libdds.so will be moved to its correct location by
    # make_build.
    PACKAGE_DATA = []


class build_ext(build_ext):
    def finalize_options(self):
        super().finalize_options()
        # Needs to be computed here because setuptools patches out inplace.
        self.__dest_dir = Path(self.get_ext_fullpath("redeal._")).parent

    def build_extensions(self):
        self.distribution.ext_modules[:] = []
        super().build_extensions()
        if sys.platform.startswith("linux") or sys.platform == "darwin":
            dds_src = Path(__file__).resolve().parent / "dds/src"
            if not dds_src.exists():
                sys.exit("""\
DDS sources are missing.

If you are using a git checkout, run
    git submodule init && git submodule update

On a Unix system, do not use the zip archives from github.""")
            if sys.platform.startswith("linux"):
                patched_path = dds_src / "dds.cpp"
                contents = patched_path.read_text()
                try:
                    patched_path.write_text(  # Patch dds issue #91.
                        contents.replace("FreeMemory();", ""))
                    subprocess.check_call(
                        ["make", "-f", "Makefiles/Makefile_linux_shared",
                         "THREADING=", "CC_BOOST_LINK="], cwd=dds_src)
                finally:  # Restore the sources.
                    patched_path.write_text(contents)
            elif sys.platform == "darwin":
                patched_path = dds_src / "Makefiles/Makefile_Mac_clang_static"
                contents = patched_path.read_text()
                try:
                    patched_path.write_text(contents.replace(
                        "ar rcs $(STATIC_LIB) $(O_FILES)\n",
                        "$(CC) "
                        "-dynamiclib -o lib$(DLLBASE).so $(O_FILES) -lc++\n"))
                    subprocess.check_call(
                        ["make", "-f", "Makefiles/Makefile_Mac_clang_static",
                         "CC=gcc"], cwd=dds_src)
                finally:
                    patched_path.write_text(contents)
            shutil.copy2(dds_src / "libdds.so", self.__dest_dir)


setup(
    cmdclass={"build_ext": build_ext},
    name="redeal",
    version="0.2.0",
    author="Antony Lee",
    author_email="anntzer.lee@gmail.com",
    packages=["redeal"],
    package_data={"redeal": PACKAGE_DATA},
    entry_points={
        "console_scripts": ["redeal = redeal.__main__:console_entry"],
        "gui_scripts": ["redeal-gui = redeal.__main__:gui_entry"],
    },
    url="http://github.com/anntzer/redeal",
    license="LICENSE.txt",
    description="A reimplementation of Thomas Andrews' Deal in Python.",
    long_description=Path("README.rst").read_text(encoding="utf-8"),
    python_requires=">=3.6",
    install_requires=["colorama>=0.2.4"],
    ext_modules=[Extension("", [])]
)
