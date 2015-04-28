# -*- coding: utf-8 -*-
# Copyright 2015 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for yapf.file_resources."""

import contextlib
import os
import shutil
import sys
import tempfile
import unittest

from yapf.yapflib import file_resources
from yapf.yapflib import py3compat


@contextlib.contextmanager
def stdout_redirector(stream):  # pylint: disable=invalid-name
  old_stdout = sys.stdout
  sys.stdout = stream
  try:
    yield
  finally:
    sys.stdout = old_stdout


class GetDefaultStyleForDirTest(unittest.TestCase):

  def setUp(self):
    self.test_tmpdir = tempfile.mkdtemp()

  def tearDown(self):
    shutil.rmtree(self.test_tmpdir)

  def testNoLocalStyle(self):
    test_file = os.path.join(self.test_tmpdir, 'file.py')
    style_name = file_resources.GetDefaultStyleForDir(test_file)
    self.assertEqual(style_name, 'pep8')

  def testWithLocalStyle(self):
    # Create an empty .style.yapf file in test_tmpdir
    style_file = os.path.join(self.test_tmpdir, '.style.yapf')
    open(style_file, 'w').close()

    test_filename = os.path.join(self.test_tmpdir, 'file.py')
    self.assertEqual(style_file,
                     file_resources.GetDefaultStyleForDir(test_filename))

    test_filename = os.path.join(self.test_tmpdir, 'dir1', 'file.py')
    self.assertEqual(style_file,
                     file_resources.GetDefaultStyleForDir(test_filename))


def _TouchFiles(filenames):
  for name in filenames:
    open(name, 'a').close()


class GetCommandLineFilesTest(unittest.TestCase):

  def setUp(self):
    self.test_tmpdir = tempfile.mkdtemp()

  def tearDown(self):
    shutil.rmtree(self.test_tmpdir)

  def _MakeTestdir(self, name):
    fullpath = os.path.join(self.test_tmpdir, name)
    os.makedirs(fullpath)
    return fullpath

  def test_nonrecursive_find_in_dir(self):
    tdir1 = self._MakeTestdir('test1')
    tdir2 = self._MakeTestdir('test1/foo')
    file1 = os.path.join(tdir1, 'testfile1.py')
    file2 = os.path.join(tdir2, 'testfile2.py')
    _TouchFiles([file1, file2])

    self.assertEqual(file_resources.GetCommandLineFiles([tdir1],
                                                        recursive=False),
                     [file1])

  def test_recursive_find_in_dir(self):
    tdir1 = self._MakeTestdir('test1')
    tdir2 = self._MakeTestdir('test2/testinner/')
    tdir3 = self._MakeTestdir('test3/foo/bar/bas/kkk')
    files = [os.path.join(tdir1, 'testfile1.py'),
             os.path.join(tdir2, 'testfile2.py'),
             os.path.join(tdir3, 'testfile3.py')]
    _TouchFiles(files)

    self.assertEqual(
      sorted(file_resources.GetCommandLineFiles([self.test_tmpdir],
                                                recursive=True)),
      sorted(files))


class BufferedByteStream(object):

  def __init__(self):
    self.stream = py3compat.BytesIO()

  def getvalue(self):  # pylint: disable=invalid-name
    return self.stream.getvalue().decode('utf-8')

  @property
  def buffer(self):
    return self.stream


class WriteReformattedCodeTest(unittest.TestCase):

  @classmethod
  def setUpClass(cls):
    cls.test_tmpdir = tempfile.mkdtemp()

  @classmethod
  def tearDownClass(cls):
    shutil.rmtree(cls.test_tmpdir)

  def testWriteToFile(self):
    s = u'foobar'
    with tempfile.NamedTemporaryFile(dir=self.test_tmpdir) as testfile:
      file_resources.WriteReformattedCode(testfile.name, s,
                                          in_place=True,
                                          encoding='utf-8')
      testfile.flush()

      with open(testfile.name) as f:
        self.assertEqual(f.read(), s)

  def testWriteToStdout(self):
    s = u'foobar'
    stream = BufferedByteStream() if py3compat.PY3 else py3compat.StringIO()
    with stdout_redirector(stream):
      file_resources.WriteReformattedCode(None, s,
                                          in_place=False,
                                          encoding='utf-8')
    self.assertEqual(stream.getvalue(), s)

  def testWriteEncodedToStdout(self):
    s = '\ufeff# -*- coding: utf-8 -*-\nresult = "passed"\n'  # pylint: disable=anomalous-unicode-escape-in-string
    stream = BufferedByteStream() if py3compat.PY3 else py3compat.StringIO()
    with stdout_redirector(stream):
      file_resources.WriteReformattedCode(None, s,
                                          in_place=False,
                                          encoding='utf-8')
    self.assertEqual(stream.getvalue(), s)


if __name__ == '__main__':
  unittest.main()
