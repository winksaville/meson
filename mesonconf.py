#!/usr/bin/env python3

# Copyright 2014-2015 The Meson development team

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys, os
import pickle
import argparse
import coredata, mesonlib
from meson import build_types, layouts, warning_levels

parser = argparse.ArgumentParser()

parser.add_argument('-D', action='append', default=[], dest='sets',
                    help='Set an option to the given value.')
parser.add_argument('directory', nargs='*')

class ConfException(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class Conf:
    def __init__(self, build_dir):
        self.build_dir = build_dir
        self.coredata_file = os.path.join(build_dir, 'meson-private/coredata.dat')
        self.build_file = os.path.join(build_dir, 'meson-private/build.dat')
        if not os.path.isfile(self.coredata_file) or not os.path.isfile(self.build_file):
            raise ConfException('Directory %s does not seem to be a Meson build directory.' % build_dir)
        self.coredata = pickle.load(open(self.coredata_file, 'rb'))
        self.build = pickle.load(open(self.build_file, 'rb'))
        if self.coredata.version != coredata.version:
            raise ConfException('Version mismatch (%s vs %s)' %
                                (coredata.version, self.coredata.version))

    def save(self):
        # Only called if something has changed so overwrite unconditionally.
        pickle.dump(self.coredata, open(self.coredata_file, 'wb'))
        # We don't write the build file because any changes to it
        # are erased when Meson is executed the nex time, i.e. the next
        # time Ninja is run.

    def print_aligned(self, arr):
        if len(arr) == 0:
            return
        titles = ['Option', 'Description', 'Current Value', '']
        longest_name = len(titles[0])
        longest_descr = len(titles[1])
        longest_value = len(titles[2])
        longest_possible_value = len(titles[3])
        for x in arr:
          longest_name = max(longest_name, len(x[0]))
          longest_descr = max(longest_descr, len(x[1]))
          longest_value = max(longest_value, len(str(x[2])))
          longest_possible_value = max(longest_possible_value, len(x[3]))

        if longest_possible_value > 0:
          titles[3] = 'Possible Values'
        print('  %s%s %s%s %s%s %s' % (titles[0], ' '*(longest_name - len(titles[0])), titles[1], ' '*(longest_descr - len(titles[1])), titles[2], ' '*(longest_value - len(titles[2])), titles[3]))
        print('  %s%s %s%s %s%s %s' % ('-'*len(titles[0]), ' '*(longest_name - len(titles[0])), '-'*len(titles[1]), ' '*(longest_descr - len(titles[1])), '-'*len(titles[2]), ' '*(longest_value - len(titles[2])), '-'*len(titles[3])))
        for i in arr:
            name = i[0]
            descr = i[1]
            value = i[2]
            if str(value) == 'True':
                value = 'true'
            else:
                value = 'false'
            possible_values = i[3]
            namepad = ' '*(longest_name - len(name))
            descrpad = ' '*(longest_descr - len(descr))
            valuepad = ' '*(longest_value - len(str(value)))
            f = '  %s%s %s%s %s%s %s' % (name, namepad, descr, descrpad, value, valuepad, possible_values)
            print(f)

    def set_options(self, options):
        for o in options:
            if '=' not in o:
                raise ConfException('Value "%s" not of type "a=b".' % o)
            (k, v) = o.split('=', 1)
            if k == 'buildtype':
                if v not in build_types:
                    raise ConfException('Invalid build type %s.' % v)
                self.coredata.buildtype = v
            elif k == 'layout':
                if v not in layouts:
                    raise ConfException('Invalid layout type %s.' % v)
                self.coredata.layout = v
            elif k == 'warnlevel':
                if not v in warning_levels:
                    raise ConfException('Invalid warning level %s.' % v)
                self.coredata.warning_level = v
            elif k == 'strip':
                self.coredata.strip = self.tobool(v)
            elif k == 'coverage':
                v = self.tobool(v)
                self.coredata.coverage = self.tobool(v)
            elif k == 'pch':
                self.coredata.use_pch = self.tobool(v)
            elif k == 'unity':
                self.coredata.unity = self.tobool(v)
            elif k == 'prefix':
                if not os.path.isabs(v):
                    raise ConfException('Install prefix %s is not an absolute path.' % v)
                self.coredata.prefix = v
            elif k == 'libdir':
                if os.path.isabs(v):
                    raise ConfException('Library dir %s must not be an absolute path.' % v)
                self.coredata.libdir = v
            elif k == 'bindir':
                if os.path.isabs(v):
                    raise ConfException('Binary dir %s must not be an absolute path.' % v)
                self.coredata.bindir = v
            elif k == 'includedir':
                if os.path.isabs(v):
                    raise ConfException('Include dir %s must not be an absolute path.' % v)
                self.coredata.includedir = v
            elif k == 'datadir':
                if os.path.isabs(v):
                    raise ConfException('Data dir %s must not be an absolute path.' % v)
                self.coredata.datadir = v
            elif k == 'mandir':
                if os.path.isabs(v):
                    raise ConfException('Man dir %s must not be an absolute path.' % v)
                self.coredata.mandir = v
            elif k == 'localedir':
                if os.path.isabs(v):
                    raise ConfException('Locale dir %s must not be an absolute path.' % v)
                self.coredata.localedir = v
            elif k in self.coredata.user_options:
                tgt = self.coredata.user_options[k]
                tgt.set_value(v)
            elif k in self.coredata.compiler_options:
                tgt = self.coredata.compiler_options[k]
                tgt.set_value(v)
            elif k.endswith('linkargs'):
                lang = k[:-8]
                if not lang in self.coredata.external_link_args:
                    raise ConfException('Unknown language %s in linkargs.' % lang)
                # TODO, currently split on spaces, make it so that user
                # can pass in an array string.
                newvalue = v.split()
                self.coredata.external_link_args[lang] = newvalue
            elif k.endswith('args'):
                lang = k[:-4]
                if not lang in self.coredata.external_args:
                    raise ConfException('Unknown language %s in compile args' % lang)
                # TODO same fix as above
                newvalue = v.split()
                self.coredata.external_args[lang] = newvalue
            else:
                raise ConfException('Unknown option %s.' % k)


    def print_conf(self):
        print('Core properties:')
        print('  Source dir', self.build.environment.source_dir)
        print('  Build dir ', self.build.environment.build_dir)
        print('')
        print('Core options:')
        carr = []
        booleans = '[true, false]'
        carr.append(['buildtype', 'Build type', self.coredata.buildtype, build_types])
        carr.append(['warnlevel', 'Warning level', self.coredata.warning_level, warning_levels])
        carr.append(['strip', 'Strip on install', self.coredata.strip, booleans])
        carr.append(['coverage', 'Coverage report', self.coredata.coverage, booleans])
        carr.append(['pch', 'Precompiled headers', self.coredata.use_pch, booleans])
        carr.append(['unity', 'Unity build', self.coredata.unity, booleans])
        self.print_aligned(carr)
        print('')
        print('Compiler arguments:')
        for (lang, args) in self.coredata.external_args.items():
            print('  ' + lang + 'args', str(args))
        print('')
        print('Linker args:')
        for (lang, args) in self.coredata.external_link_args.items():
            print('  ' + lang + 'linkargs', str(args))
        print('')
        print('Directories:')
        parr = []
        parr.append(['prefix', 'Install prefix', self.coredata.prefix, ''])
        parr.append(['libdir', 'Library directory', self.coredata.libdir, ''])
        parr.append(['bindir', 'Binary directory', self.coredata.bindir, ''])
        parr.append(['includedir', 'Header directory', self.coredata.includedir, ''])
        parr.append(['datadir', 'Data directory', self.coredata.datadir, ''])
        parr.append(['mandir', 'Man page directory', self.coredata.mandir, ''])
        parr.append(['localedir', 'Locale file directory', self.coredata.localedir, ''])
        self.print_aligned(parr)
        print('')
        print('Project options:')
        if len(self.coredata.user_options) == 0:
            print('  This project does not have any options')
        else:
            options = self.coredata.user_options
            keys = list(options.keys())
            keys.sort()
            optarr = []
            for key in keys:
                opt = options[key]
                if (opt.choices is None) or (len(opt.choices) == 0):
                  # Zero length list or string
                  choices = '';
                else:
                  # A non zero length list or string, convert to string
                  choices = str(opt.choices);
                optarr.append([key, opt.description, opt.value, choices])
            self.print_aligned(optarr)

if __name__ == '__main__':
    options = parser.parse_args()
    if len(options.directory) > 1:
        print('%s <build directory>' % sys.argv[0])
        print('If you omit the build directory, the current directory is substituted.')
        sys.exit(1)
    if len(options.directory) == 0:
        builddir = os.getcwd()
    else:
        builddir = options.directory[0]
    try:
        c = Conf(builddir)
        if len(options.sets) > 0:
            c.set_options(options.sets)
            c.save()
        else:
            c.print_conf()
    except ConfException as e:
        print('Meson configurator encountered an error:\n')
        print(e)

