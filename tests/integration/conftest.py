# Copyright 2021 Northern.tech AS
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

from os import path
import sys

import logging
import subprocess

logging.getLogger("requests").setLevel(logging.CRITICAL)
logging.getLogger("paramiko").setLevel(logging.CRITICAL)
logging.getLogger("urllib3").setLevel(logging.CRITICAL)
logging.getLogger("filelock").setLevel(logging.INFO)
logger = logging.getLogger()


sys.path += [path.join(path.dirname(__file__), "mender_integration")]

from mender_integration.tests.conftest import pytest_exception_interact


def pytest_runtest_teardown(item, nextitem):
    subprocess.run(["docker", "ps"])
    cmd = "docker ps | grep client | awk '{print $1}'"
    ret = subprocess.check_output(cmd, shell=True).decode("utf-8").strip()
    subprocess.run(["docker", "logs", ret])
