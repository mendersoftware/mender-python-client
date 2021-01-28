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
import json
import logging as testlogger
import os.path
import pytest

import mender.log.log as mlog
import mender.settings.settings as settings


class TestDeploymentLogger:
    @pytest.fixture(autouse=True)
    def set_log_level_info(self, caplog):
        """Set the log-level capture to info for all tests"""
        caplog.set_level(testlogger.INFO)

    @pytest.fixture()
    def deployment_logger(self, tmpdir):
        d = tmpdir.mkdir("test_logger")
        log_file = os.path.join(d, "deployment.log")
        settings.PATHS.deployment_log = d
        logger = mlog.DeploymentLogHandler()
        rootlogger = testlogger.getLogger("")
        rootlogger.addHandler(logger)
        return logger, log_file

    def test_logger(self, caplog, deployment_logger):
        logger, log_file = deployment_logger
        testlogger.info("Foobar")
        # Should not show up in log, as the logger is not enabled
        assert os.path.getsize(log_file) == 0
        logger.enable()
        testlogger.info("BarBaz")
        assert os.path.getsize(log_file) != 0
        with open(log_file) as fh:
            data = json.loads(fh.read().strip())
            assert data["message"] == "BarBaz"
            assert data["level"] == "INFO"
        assert "Foobar" in caplog.text
        assert "BarBaz" in caplog.text

    def test_log_marshalling(self, caplog, deployment_logger):
        logger, _ = deployment_logger
        logger.enable()
        rootlogger = testlogger.getLogger("")
        rootlogger.addHandler(logger)
        testlogger.info("foo")
        testlogger.error("bar")
        data = logger.marshal()
        assert data[0]["message"] == "foo"
        assert data[0]["level"] == "INFO"
        assert data[1]["message"] == "bar"
        assert data[1]["level"] == "ERROR"
        # stream log
        assert "foo" in caplog.text
        assert "bar" in caplog.text
