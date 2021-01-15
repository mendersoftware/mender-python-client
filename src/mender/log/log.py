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
import logging as log
import logging.handlers
import os
import os.path

import mender.settings.settings as settings


class JSONFormatter(logging.Formatter):
    """JSON log formatter

    Logs every log message to a json encoded line in the deployment.log file, in
    the format:

    {
    "message": "foobar",
    "timestamp": "UTC-...",
    "level": "LEVEL"
    }

    """

    def format(self, record) -> str:
        print("Noo")
        level = record.levelname
        message = record.message
        timestamp = self.formatTime(record)
        # print(record.asctime)
        print(self.formatTime(record))
        return json.dumps({"level": level, "timestamp": timestamp, "message": message,})


class DeploymentLogHandler(logging.FileHandler):
    def __init__(self):
        self.enabled = False
        self.log_dir = settings.PATHS.deployment_log
        filename = os.path.join(self.log_dir, "deployment.log")
        self.log_file = filename
        super().__init__(filename=filename)
        print(super(logging.FileHandler))
        super().setFormatter(JSONFormatter())

    def handle(self, record):
        print(f"Handling... {record}")
        if self.enabled:
            print(f"Handling enabled... {record}")
            super(logging.FileHandler, self).handle(record)

    def enable(self):
        print("Enabled..")
        self.enabled = True
        filename = os.path.join(self.log_dir, "deployment.log")
        # Reset the log
        with open(filename, "w") as fh:
            pass

    def disable(self):
        self.enabled = False

    def marshal(self):
        """Marshal the logs to the format required by the deployment endpoint"""
        logs = []
        for line in open(self.log_file):
            try:
                data = json.loads(line)
                logs.append(data)
            except Exception as e:
                # TODO - catch json exception
                log.error(f"Failed to marshal json, {e}")
        return logs



def add_sub_updater_log(log_file):
    try:
        with open(log_file) as fh:
            log_string = fh.read()
            log.info(f"Sub-updater-logs follows:\n{log_string}")
    except FileNotFoundError:
        log.error(
            f"The log_file: {log_file} was not found.\
            No logs from the sub-updater will be reported."
        )
