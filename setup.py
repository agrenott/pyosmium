# SPDX-License-Identifier: BSD-2-Clause
#
# This file is part of pyosmium. (https://osmcode.org/pyosmium/)
#
# Copyright (C) 2024 Sarah Hoffmann <lonvia@denofr.de> and others.
# For a full list of authors see the git log.
import os
import re
import sys
import platform
import subprocess

from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext
from packaging.version import Version

BASEDIR = os.path.split(os.path.abspath(__file__))[0]


def get_versions():
    """ Read the version file.

        The file cannot be directly imported because it is not installed
        yet.
    """
    version_py = os.path.join(BASEDIR, "src/npyosmium/version.py")
    v = {}
    with open(version_py) as version_file:
        # Execute the code in version.py.
        exec(compile(version_file.read(), version_py, 'exec'), v)

    return v

class CMakeExtension(Extension):
    def __init__(self, name, sourcedir=''):
        Extension.__init__(self, name, sources=[])
        self.sourcedir = os.path.abspath(sourcedir)


class CMakeBuild(build_ext):
    def run(self):
        try:
            out = subprocess.check_output(['cmake', '--version'])
        except OSError:
            raise RuntimeError("CMake must be installed to build the following extensions: " +
                               ", ".join(e.name for e in self.extensions))

        if platform.system() == "Windows":
            cmake_version = Version(re.search(r'version\s*([\d.]+)', out.decode()).group(1))
            if cmake_version < Version('3.1.0'):
                raise RuntimeError("CMake >= 3.1.0 is required on Windows")

        for ext in self.extensions:
            self.build_extension(ext)

    def build_extension(self, ext):
        extdir = os.path.abspath(os.path.dirname(self.get_ext_fullpath(ext.name)))
        cmake_args = ['-DCMAKE_LIBRARY_OUTPUT_DIRECTORY=' + extdir,
                      '-DPYTHON_EXECUTABLE=' + sys.executable]

        cfg = 'Debug' if self.debug else 'Release'
        build_args = ['--config', cfg]

        if platform.system() == "Windows":
            cmake_args += ['-DCMAKE_LIBRARY_OUTPUT_DIRECTORY_{}={}'.format(cfg.upper(), extdir)]
            if sys.maxsize > 2**32:
                cmake_args += ['-A', 'x64']
            build_args += ['--', '/m']
        else:
            cmake_args += ['-DCMAKE_BUILD_TYPE=' + cfg]
            build_args += ['--', '-j2']

        env = os.environ.copy()
        env['CXXFLAGS'] = '{} -DVERSION_INFO=\\"{}\\"'.format(env.get('CXXFLAGS', ''),
                                                              self.distribution.get_version())

        if 'LIBOSMIUM_PREFIX' in env:
            cmake_args += ['-DOSMIUM_INCLUDE_DIR={}/include'.format(env['LIBOSMIUM_PREFIX'])]
        elif os.path.exists(os.path.join(BASEDIR, 'contrib', 'libosmium', 'include', 'osmium', 'version.hpp')):
            cmake_args += ['-DOSMIUM_INCLUDE_DIR={}/contrib/libosmium/include'.format(BASEDIR)]

        if 'PROTOZERO_PREFIX' in env:
            cmake_args += ['-DPROTOZERO_INCLUDE_DIR={}/include'.format(env['PROTOZERO_PREFIX'])]
        elif os.path.exists(os.path.join(BASEDIR, 'contrib', 'protozero', 'include', 'protozero', 'version.hpp')):
            cmake_args += ['-DPROTOZERO_INCLUDE_DIR={}/contrib/protozero/include'.format(BASEDIR)]

        if 'PYBIND11_PREFIX' in env:
            cmake_args += ['-DPYBIND11_PREFIX={}'.format(env['PYBIND11_PREFIX'])]
        elif os.path.exists(os.path.join(BASEDIR, 'contrib', 'pybind11')):
            cmake_args += ['-DPYBIND11_PREFIX={}/contrib/pybind11'.format(BASEDIR)]

        if 'BOOST_PREFIX' in env:
            cmake_args += ['-DBOOST_ROOT={}'.format(env['BOOST_PREFIX'])]

        if 'CMAKE_CXX_STANDARD' in env:
            cmake_args += ['-DCMAKE_CXX_STANDARD={}'.format(env['CMAKE_CXX_STANDARD'])]

        if not os.path.exists(self.build_temp):
            os.makedirs(self.build_temp)
        subprocess.check_call(['cmake', ext.sourcedir] + cmake_args, cwd=self.build_temp, env=env)
        subprocess.check_call(['cmake', '--build', '.'] + build_args, cwd=self.build_temp)

versions = get_versions()

if sys.version_info < (3,8):
    raise RuntimeError("Python 3.8 or larger required.")

with open('README.md', 'r') as descfile:
    long_description = descfile.read()

setup(
    name='npyosmium',
    version=versions['npyosmium_release'],
    description='Python bindings for libosmium, the data processing library for OSM data, with numpy interface',
    long_description=long_description,
    author='Sarah Hoffmann',
    author_email='lonvia@denofr.de',
    maintainer='Aurélien Grenotton',
    maintainer_email='agrenott@gmail.com',
    download_url='https://github.com/agrenott/npyosmium',
    url='https://github.com/agrenott/npyosmium',
    keywords=["OSM", "OpenStreetMap", "Osmium"],
    license='BSD',
    scripts=['tools/npyosmium-get-changes', 'tools/npyosmium-up-to-date'],
    classifiers = [
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: C++",
        ],

    ext_modules=[CMakeExtension('cmake_example')],
    packages = ['npyosmium', 'npyosmium/osm', 'npyosmium/replication'],
    package_dir = {'' : 'src'},
    package_data = { 'npyosmium': ['py.typed', '*.pyi',
                                'replication/_replication.pyi',
                                'osm/_osm.pyi']},
    python_requires = ">=3.8",
    install_requires = ['requests'],
    extras_require = {
        'tests': ['pytest', 'pytest-httpserver', 'werkzeug'],
    },
    cmdclass=dict(build_ext=CMakeBuild),
    zip_safe=False,
)
