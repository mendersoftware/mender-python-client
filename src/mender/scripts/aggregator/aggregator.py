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
import logging
import subprocess
from typing import Dict, List

log = logging.getLogger(__name__)


class ScriptKeyValueAggregator:
    """Handles the parsing of the output from any Mender identity of inventory scripts.

    These scripts support key=value pairs, with one output per line maximum.
    Multiple lines with a matching key are aggregated into an array."""

    def __init__(self, script_path: str):
        self.script_path = script_path
        self.vals: Dict[str, List[str]] = {}

    def run(self) -> dict:
        try:
            output = subprocess.run(
                self.script_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=100,
                check=True,
            )
            data = output.stdout.decode()
            return self.parse(data)
        except subprocess.CalledProcessError as e:
            errout = ", stderr: " + e.stderr.decode() if e.stderr else ""
            log.error(
                f"Failed to aggregate key-value pairs from {self.script_path}.\
                Script returned: {e.returncode}{errout}"
            )
            return {}

    def collect(self, unique_keys: bool = False) -> Dict[str, List[str]]:
        with open(self.script_path) as fh:
            data = fh.read()
            return self.parse(data, unique_keys)

    def parse(self, data: str, unique_keys: bool = False) -> Dict[str, List[str]]:
        for line in data.split("\n"):
            if line == "":
                continue
            arr = line.strip().split("=", 1)
            if len(arr) < 2:
                log.debug("Skipping line without output")
                continue
            key, val = arr[0], arr[1]
            if unique_keys:
                self.vals[key] = [val]
            else:
                self.vals.setdefault(key, []).append(val)
        return self.vals
