# Copyright 2016-2021 The Meson development team

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import subprocess
import json
import os
import unittest
from distutils.dir_util import copy_tree

from .baseplatformtests import BasePlatformTests

class RewriterTests(BasePlatformTests):
    def setUp(self):
        super().setUp()
        self.maxDiff = None

    def prime(self, dirname):
        copy_tree(os.path.join(self.rewrite_test_dir, dirname), self.builddir)

    def rewrite_raw(self, directory, args):
        if isinstance(args, str):
            args = [args]
        command = self.rewrite_command + ['--verbose', '--skip', '--sourcedir', directory] + args
        p = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           universal_newlines=True, timeout=60)
        print('STDOUT:')
        print(p.stdout)
        print('STDERR:')
        print(p.stderr)
        if p.returncode != 0:
            if 'MESON_SKIP_TEST' in p.stdout:
                raise unittest.SkipTest('Project requested skipping.')
            raise subprocess.CalledProcessError(p.returncode, command, output=p.stdout)
        if not p.stderr:
            return {}
        return json.loads(p.stderr)

    def rewrite(self, directory, args):
        if isinstance(args, str):
            args = [args]
        return self.rewrite_raw(directory, ['command'] + args)

    def test_target_source_list(self):
        self.prime('1 basic')
        out = self.rewrite(self.builddir, os.path.join(self.builddir, 'info.json'))
        expected = {
            'target': {
                'trivialprog0@exe': {'name': 'trivialprog0', 'sources': ['main.cpp', 'fileA.cpp', 'fileB.cpp', 'fileC.cpp']},
                'trivialprog1@exe': {'name': 'trivialprog1', 'sources': ['main.cpp', 'fileA.cpp']},
                'trivialprog2@exe': {'name': 'trivialprog2', 'sources': ['fileB.cpp', 'fileC.cpp']},
                'trivialprog3@exe': {'name': 'trivialprog3', 'sources': ['main.cpp', 'fileA.cpp']},
                'trivialprog4@exe': {'name': 'trivialprog4', 'sources': ['main.cpp', 'fileA.cpp']},
                'trivialprog5@exe': {'name': 'trivialprog5', 'sources': ['main.cpp', 'fileB.cpp', 'fileC.cpp']},
                'trivialprog6@exe': {'name': 'trivialprog6', 'sources': ['main.cpp', 'fileA.cpp']},
                'trivialprog7@exe': {'name': 'trivialprog7', 'sources': ['fileB.cpp', 'fileC.cpp', 'main.cpp', 'fileA.cpp']},
                'trivialprog8@exe': {'name': 'trivialprog8', 'sources': ['main.cpp', 'fileA.cpp']},
                'trivialprog9@exe': {'name': 'trivialprog9', 'sources': ['main.cpp', 'fileA.cpp']},
            }
        }
        self.assertDictEqual(out, expected)

    def test_target_add_sources(self):
        self.prime('1 basic')
        out = self.rewrite(self.builddir, os.path.join(self.builddir, 'addSrc.json'))
        expected = {
            'target': {
                'trivialprog0@exe': {'name': 'trivialprog0', 'sources': ['a1.cpp', 'a2.cpp', 'a6.cpp', 'fileA.cpp', 'main.cpp', 'a7.cpp', 'fileB.cpp', 'fileC.cpp']},
                'trivialprog1@exe': {'name': 'trivialprog1', 'sources': ['a1.cpp', 'a2.cpp', 'a6.cpp', 'fileA.cpp', 'main.cpp']},
                'trivialprog2@exe': {'name': 'trivialprog2', 'sources': ['a7.cpp', 'fileB.cpp', 'fileC.cpp']},
                'trivialprog3@exe': {'name': 'trivialprog3', 'sources': ['a5.cpp', 'fileA.cpp', 'main.cpp']},
                'trivialprog4@exe': {'name': 'trivialprog4', 'sources': ['a5.cpp', 'main.cpp', 'fileA.cpp']},
                'trivialprog5@exe': {'name': 'trivialprog5', 'sources': ['a3.cpp', 'main.cpp', 'a7.cpp', 'fileB.cpp', 'fileC.cpp']},
                'trivialprog6@exe': {'name': 'trivialprog6', 'sources': ['main.cpp', 'fileA.cpp', 'a4.cpp']},
                'trivialprog7@exe': {'name': 'trivialprog7', 'sources': ['fileB.cpp', 'fileC.cpp', 'a1.cpp', 'a2.cpp', 'a6.cpp', 'fileA.cpp', 'main.cpp']},
                'trivialprog8@exe': {'name': 'trivialprog8', 'sources': ['a1.cpp', 'a2.cpp', 'a6.cpp', 'fileA.cpp', 'main.cpp']},
                'trivialprog9@exe': {'name': 'trivialprog9', 'sources': ['a1.cpp', 'a2.cpp', 'a6.cpp', 'fileA.cpp', 'main.cpp']},
            }
        }
        self.assertDictEqual(out, expected)

        # Check the written file
        out = self.rewrite(self.builddir, os.path.join(self.builddir, 'info.json'))
        self.assertDictEqual(out, expected)

    def test_target_add_sources_abs(self):
        self.prime('1 basic')
        abs_src = [os.path.join(self.builddir, x) for x in ['a1.cpp', 'a2.cpp', 'a6.cpp']]
        add = json.dumps([{"type": "target", "target": "trivialprog1", "operation": "src_add", "sources": abs_src}])
        inf = json.dumps([{"type": "target", "target": "trivialprog1", "operation": "info"}])
        self.rewrite(self.builddir, add)
        out = self.rewrite(self.builddir, inf)
        expected = {'target': {'trivialprog1@exe': {'name': 'trivialprog1', 'sources': ['a1.cpp', 'a2.cpp', 'a6.cpp', 'fileA.cpp', 'main.cpp']}}}
        self.assertDictEqual(out, expected)

    def test_target_remove_sources(self):
        self.prime('1 basic')
        out = self.rewrite(self.builddir, os.path.join(self.builddir, 'rmSrc.json'))
        expected = {
            'target': {
                'trivialprog0@exe': {'name': 'trivialprog0', 'sources': ['main.cpp', 'fileC.cpp']},
                'trivialprog1@exe': {'name': 'trivialprog1', 'sources': ['main.cpp']},
                'trivialprog2@exe': {'name': 'trivialprog2', 'sources': ['fileC.cpp']},
                'trivialprog3@exe': {'name': 'trivialprog3', 'sources': ['main.cpp']},
                'trivialprog4@exe': {'name': 'trivialprog4', 'sources': ['main.cpp']},
                'trivialprog5@exe': {'name': 'trivialprog5', 'sources': ['main.cpp', 'fileC.cpp']},
                'trivialprog6@exe': {'name': 'trivialprog6', 'sources': ['main.cpp']},
                'trivialprog7@exe': {'name': 'trivialprog7', 'sources': ['fileC.cpp', 'main.cpp']},
                'trivialprog8@exe': {'name': 'trivialprog8', 'sources': ['main.cpp']},
                'trivialprog9@exe': {'name': 'trivialprog9', 'sources': ['main.cpp']},
            }
        }
        self.assertDictEqual(out, expected)

        # Check the written file
        out = self.rewrite(self.builddir, os.path.join(self.builddir, 'info.json'))
        self.assertDictEqual(out, expected)

    def test_target_subdir(self):
        self.prime('2 subdirs')
        out = self.rewrite(self.builddir, os.path.join(self.builddir, 'addSrc.json'))
        expected = {'name': 'something', 'sources': ['first.c', 'second.c', 'third.c']}
        self.assertDictEqual(list(out['target'].values())[0], expected)

        # Check the written file
        out = self.rewrite(self.builddir, os.path.join(self.builddir, 'info.json'))
        self.assertDictEqual(list(out['target'].values())[0], expected)

    def test_target_remove(self):
        self.prime('1 basic')
        self.rewrite(self.builddir, os.path.join(self.builddir, 'rmTgt.json'))
        out = self.rewrite(self.builddir, os.path.join(self.builddir, 'info.json'))

        expected = {
            'target': {
                'trivialprog2@exe': {'name': 'trivialprog2', 'sources': ['fileB.cpp', 'fileC.cpp']},
                'trivialprog3@exe': {'name': 'trivialprog3', 'sources': ['main.cpp', 'fileA.cpp']},
                'trivialprog4@exe': {'name': 'trivialprog4', 'sources': ['main.cpp', 'fileA.cpp']},
                'trivialprog5@exe': {'name': 'trivialprog5', 'sources': ['main.cpp', 'fileB.cpp', 'fileC.cpp']},
                'trivialprog6@exe': {'name': 'trivialprog6', 'sources': ['main.cpp', 'fileA.cpp']},
                'trivialprog7@exe': {'name': 'trivialprog7', 'sources': ['fileB.cpp', 'fileC.cpp', 'main.cpp', 'fileA.cpp']},
                'trivialprog8@exe': {'name': 'trivialprog8', 'sources': ['main.cpp', 'fileA.cpp']},
            }
        }
        self.assertDictEqual(out, expected)

    def test_tatrget_add(self):
        self.prime('1 basic')
        self.rewrite(self.builddir, os.path.join(self.builddir, 'addTgt.json'))
        out = self.rewrite(self.builddir, os.path.join(self.builddir, 'info.json'))

        expected = {
            'target': {
                'trivialprog0@exe': {'name': 'trivialprog0', 'sources': ['main.cpp', 'fileA.cpp', 'fileB.cpp', 'fileC.cpp']},
                'trivialprog1@exe': {'name': 'trivialprog1', 'sources': ['main.cpp', 'fileA.cpp']},
                'trivialprog2@exe': {'name': 'trivialprog2', 'sources': ['fileB.cpp', 'fileC.cpp']},
                'trivialprog3@exe': {'name': 'trivialprog3', 'sources': ['main.cpp', 'fileA.cpp']},
                'trivialprog4@exe': {'name': 'trivialprog4', 'sources': ['main.cpp', 'fileA.cpp']},
                'trivialprog5@exe': {'name': 'trivialprog5', 'sources': ['main.cpp', 'fileB.cpp', 'fileC.cpp']},
                'trivialprog6@exe': {'name': 'trivialprog6', 'sources': ['main.cpp', 'fileA.cpp']},
                'trivialprog7@exe': {'name': 'trivialprog7', 'sources': ['fileB.cpp', 'fileC.cpp', 'main.cpp', 'fileA.cpp']},
                'trivialprog8@exe': {'name': 'trivialprog8', 'sources': ['main.cpp', 'fileA.cpp']},
                'trivialprog9@exe': {'name': 'trivialprog9', 'sources': ['main.cpp', 'fileA.cpp']},
                'trivialprog10@sha': {'name': 'trivialprog10', 'sources': ['new1.cpp', 'new2.cpp']},
            }
        }
        self.assertDictEqual(out, expected)

    def test_target_remove_subdir(self):
        self.prime('2 subdirs')
        self.rewrite(self.builddir, os.path.join(self.builddir, 'rmTgt.json'))
        out = self.rewrite(self.builddir, os.path.join(self.builddir, 'info.json'))
        self.assertDictEqual(out, {})

    def test_target_add_subdir(self):
        self.prime('2 subdirs')
        self.rewrite(self.builddir, os.path.join(self.builddir, 'addTgt.json'))
        out = self.rewrite(self.builddir, os.path.join(self.builddir, 'info.json'))
        expected = {'name': 'something', 'sources': ['first.c', 'second.c']}
        self.assertDictEqual(out['target']['94b671c@@something@exe'], expected)

    def test_target_source_sorting(self):
        self.prime('5 sorting')
        add_json = json.dumps([{'type': 'target', 'target': 'exe1', 'operation': 'src_add', 'sources': ['a666.c']}])
        inf_json = json.dumps([{'type': 'target', 'target': 'exe1', 'operation': 'info'}])
        out = self.rewrite(self.builddir, add_json)
        out = self.rewrite(self.builddir, inf_json)
        expected = {
            'target': {
                'exe1@exe': {
                    'name': 'exe1',
                    'sources': [
                        'aaa/a/a1.c',
                        'aaa/b/b1.c',
                        'aaa/b/b2.c',
                        'aaa/f1.c',
                        'aaa/f2.c',
                        'aaa/f3.c',
                        'bbb/a/b1.c',
                        'bbb/b/b2.c',
                        'bbb/c1/b5.c',
                        'bbb/c2/b7.c',
                        'bbb/c10/b6.c',
                        'bbb/a4.c',
                        'bbb/b3.c',
                        'bbb/b4.c',
                        'bbb/b5.c',
                        'a1.c',
                        'a2.c',
                        'a3.c',
                        'a10.c',
                        'a20.c',
                        'a30.c',
                        'a100.c',
                        'a101.c',
                        'a110.c',
                        'a210.c',
                        'a666.c',
                        'b1.c',
                        'c2.c'
                    ]
                }
            }
        }
        self.assertDictEqual(out, expected)

    def test_target_same_name_skip(self):
        self.prime('4 same name targets')
        out = self.rewrite(self.builddir, os.path.join(self.builddir, 'addSrc.json'))
        out = self.rewrite(self.builddir, os.path.join(self.builddir, 'info.json'))
        expected = {'name': 'myExe', 'sources': ['main.cpp']}
        self.assertEqual(len(out['target']), 2)
        for val in out['target'].values():
            self.assertDictEqual(expected, val)

    def test_kwargs_info(self):
        self.prime('3 kwargs')
        out = self.rewrite(self.builddir, os.path.join(self.builddir, 'info.json'))
        expected = {
            'kwargs': {
                'project#/': {'version': '0.0.1'},
                'target#tgt1': {'build_by_default': True},
                'dependency#dep1': {'required': False}
            }
        }
        self.assertDictEqual(out, expected)

    def test_kwargs_set(self):
        self.prime('3 kwargs')
        self.rewrite(self.builddir, os.path.join(self.builddir, 'set.json'))
        out = self.rewrite(self.builddir, os.path.join(self.builddir, 'info.json'))
        expected = {
            'kwargs': {
                'project#/': {'version': '0.0.2', 'meson_version': '0.50.0', 'license': ['GPL', 'MIT']},
                'target#tgt1': {'build_by_default': False, 'build_rpath': '/usr/local', 'dependencies': 'dep1'},
                'dependency#dep1': {'required': True, 'method': 'cmake'}
            }
        }
        self.assertDictEqual(out, expected)

    def test_kwargs_add(self):
        self.prime('3 kwargs')
        self.rewrite(self.builddir, os.path.join(self.builddir, 'add.json'))
        out = self.rewrite(self.builddir, os.path.join(self.builddir, 'info.json'))
        expected = {
            'kwargs': {
                'project#/': {'version': '0.0.1', 'license': ['GPL', 'MIT', 'BSD', 'Boost']},
                'target#tgt1': {'build_by_default': True},
                'dependency#dep1': {'required': False}
            }
        }
        self.assertDictEqual(out, expected)

    def test_kwargs_remove(self):
        self.prime('3 kwargs')
        self.rewrite(self.builddir, os.path.join(self.builddir, 'remove.json'))
        out = self.rewrite(self.builddir, os.path.join(self.builddir, 'info.json'))
        expected = {
            'kwargs': {
                'project#/': {'version': '0.0.1', 'license': 'GPL'},
                'target#tgt1': {'build_by_default': True},
                'dependency#dep1': {'required': False}
            }
        }
        self.assertDictEqual(out, expected)

    def test_kwargs_remove_regex(self):
        self.prime('3 kwargs')
        self.rewrite(self.builddir, os.path.join(self.builddir, 'remove_regex.json'))
        out = self.rewrite(self.builddir, os.path.join(self.builddir, 'info.json'))
        expected = {
            'kwargs': {
                'project#/': {'version': '0.0.1', 'default_options': 'debug=true'},
                'target#tgt1': {'build_by_default': True},
                'dependency#dep1': {'required': False}
            }
        }
        self.assertDictEqual(out, expected)

    def test_kwargs_delete(self):
        self.prime('3 kwargs')
        self.rewrite(self.builddir, os.path.join(self.builddir, 'delete.json'))
        out = self.rewrite(self.builddir, os.path.join(self.builddir, 'info.json'))
        expected = {
            'kwargs': {
                'project#/': {},
                'target#tgt1': {},
                'dependency#dep1': {'required': False}
            }
        }
        self.assertDictEqual(out, expected)

    def test_default_options_set(self):
        self.prime('3 kwargs')
        self.rewrite(self.builddir, os.path.join(self.builddir, 'defopts_set.json'))
        out = self.rewrite(self.builddir, os.path.join(self.builddir, 'info.json'))
        expected = {
            'kwargs': {
                'project#/': {'version': '0.0.1', 'default_options': ['buildtype=release', 'debug=True', 'cpp_std=c++11']},
                'target#tgt1': {'build_by_default': True},
                'dependency#dep1': {'required': False}
            }
        }
        self.assertDictEqual(out, expected)

    def test_default_options_delete(self):
        self.prime('3 kwargs')
        self.rewrite(self.builddir, os.path.join(self.builddir, 'defopts_delete.json'))
        out = self.rewrite(self.builddir, os.path.join(self.builddir, 'info.json'))
        expected = {
            'kwargs': {
                'project#/': {'version': '0.0.1', 'default_options': ['cpp_std=c++14', 'debug=true']},
                'target#tgt1': {'build_by_default': True},
                'dependency#dep1': {'required': False}
            }
        }
        self.assertDictEqual(out, expected)