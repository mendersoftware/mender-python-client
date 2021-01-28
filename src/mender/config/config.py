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
import json
import logging as log
from typing import Optional


class NoConfigurationFileError(Exception):
    pass


class Config:
    """A dictionary for storing Mender configuration values"""

    ServerURL = ""
    RootfsPartA = ""
    RootfsPartB = ""
    TenantToken = ""
    InventoryPollIntervalSeconds = ""
    UpdatePollIntervalSeconds = ""
    RetryPollIntervalSeconds = ""
    ServerCertificate = ""

    def __init__(self, global_conf: dict, local_conf: dict):
        vals = {**global_conf, **local_conf}
        log.debug("Mender configuration values:")
        for k, v in vals.items():
            if k == "ServerURL":
                log.debug(f"ServerURL: {v}")
                self.ServerURL = v
            elif k == "RootfsPartA":
                log.debug(f"RootfsPartA: {v}")
                self.RootfsPartA = v
            elif k == "RootfsPartB":
                log.debug(f"RootfsPartB: {v}")
                self.RootfsPartB = v
            elif k == "TenantToken":
                log.debug(f"TenantToken: {v}")
                self.TenantToken = v
            elif k == "InventoryPollIntervalSeconds":
                log.debug(f"InventoryPollInvervalSeconds: {v}")
                self.InventoryPollIntervalSeconds = v
            elif k == "UpdatePollIntervalSeconds":
                log.debug(f"UpdatePollIntervalSeconds: {v}")
                self.UpdatePollIntervalSeconds = v
            elif k == "RetryPollIntervalSeconds":
                log.debug(f"RetryPollIntervalSeconds: {v}")
                self.RetryPollIntervalSeconds = v
            elif k == "ServerCertificate":
                log.debug(f"ServerCertificate: {v}")
                self.ServerCertificate = v
            else:
                log.error(f"The key {k} is not recognized by the Python client")


def load(local_path: str, global_path: str) -> Optional[Config]:
    """Read and return the merged configuration from the local and global config files"""
    log.info("Loading the configuration files...")
    global_conf = local_conf = None
    try:
        with open(global_path, "r") as fh:
            global_conf = json.load(fh)
    except FileNotFoundError:
        log.info("Global configuration file not found")
    try:
        with open(local_path, "r") as fh:
            local_conf = json.load(fh)
    except FileNotFoundError as e:
        log.info(f"Local configuration file not found: {e}")
    if not global_conf and not local_conf:
        raise NoConfigurationFileError
    return Config(global_conf=global_conf or {}, local_conf=local_conf or {})
