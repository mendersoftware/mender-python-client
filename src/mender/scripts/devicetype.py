# Copyright 2020 Northern.tech AS
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
import logging as log
from typing import Optional

from mender.scripts.aggregator.aggregator import ScriptKeyValueAggregator


def get(path: str) -> Optional[dict]:
    try:
        device_type = ScriptKeyValueAggregator(path).collect(unique_keys=True)
        if len(device_type.keys()) > 1:
            log.error(
                "Multiple key=value pairs found in the device_type file. Only one is allowed"
            )
            return None
        return device_type
    except FileNotFoundError:
        log.error(f"No device_type file found in {path}")
        return None
