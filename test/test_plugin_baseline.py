# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import pytest
import subprocess
import shutil

from plugin.templates import resource_name
from plugin.utils import casing_utils


TEST_DIR = os.path.join('test', 'testdata')
TEST_OUTPUT_DIR = os.path.join(TEST_DIR, 'test_output')


def read_baseline(baseline):
    filename = os.path.join(TEST_DIR, baseline + '.baseline')
    with open(filename) as f:
        return f.readlines()


def check_output(output_class, output_path, baseline):
    actual_output_file = os.path.join(TEST_OUTPUT_DIR,
                                      output_path,
                                      output_class + '.java')
    with open(actual_output_file) as f:
        actual_output = f.readlines()
    expected_output = read_baseline(baseline)
    assert expected_output == actual_output, "Baseline error.\nExpected: " \
        + str(expected_output) \
        + "\nActual: " \
        + str(actual_output)


def run_protoc_gapic_plugin(output_dir, gapic_yaml, include_dirs, proto,
                            lang_out=None):
    def format_output_arg(name, output_dir, extra_arg=None):
        if extra_arg:
            return '--{}_out={}:{}'.format(name, extra_arg, output_dir)
        else:
            return '--{}_out={}'.format(name, output_dir)

    args = ['protoc']
    if lang_out is not None:
        args.append(format_output_arg(lang_out, output_dir))
    args += [format_output_arg('gapic', output_dir, gapic_yaml),
             '--plugin=protoc-gen-gapic=gapic_plugin.py']
    args += ['-I' + path for path in include_dirs]
    args.append(proto)
    subprocess.check_call(args)


def clean_test_output():
    shutil.rmtree(TEST_OUTPUT_DIR, True)
    os.mkdir(TEST_OUTPUT_DIR)


@pytest.fixture(scope='class')
def run_protoc():
    clean_test_output()
    gapic_yaml = os.path.join(TEST_DIR, 'library_gapic.yaml')
    include_dirs = ['.', '../googleapis']
    run_protoc_gapic_plugin(TEST_OUTPUT_DIR,
                            gapic_yaml,
                            include_dirs,
                            os.path.join(TEST_DIR, 'library_simple.proto'),
                            'java')

RESOURCE_NAMES_TO_GENERATE = ['book_name', 'shelf_name', 'archived_book_name',
                              'deleted_book']
ONEOFS_TO_GENERATE = ['book_name_oneof']
MESSAGE_CLASSES_TO_EXTEND = ['book', 'shelf', 'list_books_response',
                             'book_from_anywhere']

PROTOC_OUTPUT_DIR = os.path.join('com', 'google', 'example', 'library', 'v1')
RESOURCE_OUTPUT_DIR = resource_name.RESOURCE_NAMES_TYPE_PACKAGE_JAVA.replace(
    '.', os.path.sep)


class TestProtocGapicPlugin(object):

    @pytest.mark.parametrize('resource', RESOURCE_NAMES_TO_GENERATE)
    def test_resource_name_generation(self, run_protoc, resource):
        generated_class = casing_utils.lower_underscore_to_upper_camel(
            resource)
        check_output(generated_class, RESOURCE_OUTPUT_DIR, 'java_' + resource)

    @pytest.mark.parametrize('resource', RESOURCE_NAMES_TO_GENERATE)
    def test_resource_name_type_generation(self, run_protoc, resource):
        generated_type = \
            casing_utils.lower_underscore_to_upper_camel(resource) + 'Type'
        check_output(generated_type, RESOURCE_OUTPUT_DIR,
                     'java_' + resource + '_type')

    @pytest.mark.parametrize('oneof', ONEOFS_TO_GENERATE)
    def test_resource_name_oneof_generation(self, run_protoc, oneof):
        generated_oneof = casing_utils.lower_underscore_to_upper_camel(oneof)
        check_output(generated_oneof, PROTOC_OUTPUT_DIR, 'java_' + oneof)

    @pytest.mark.parametrize('message', MESSAGE_CLASSES_TO_EXTEND)
    def test_get_set_insertion(self, run_protoc, message):
        proto_class = casing_utils.lower_underscore_to_upper_camel(message)
        check_output(proto_class, PROTOC_OUTPUT_DIR,
                     'java_' + message + '_insert')