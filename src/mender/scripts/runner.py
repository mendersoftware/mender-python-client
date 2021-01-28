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
import subprocess
import logging as log

import mender.settings.settings as settings


def run_sub_updater(deployment_id: str) -> bool:
    """run_sub_updater runs the /usr/share/mender/install script"""
    log.info("Running the sub-updater script at /usr/share/mender/install")
    try:
        # Store the deployment ID in the update lockfile
        with open(settings.PATHS.lockfile_path, "w") as f:
            f.write(deployment_id)
        subprocess.run(
            [
                "/usr/share/mender/install",
                settings.PATHS.artifact_download + "/artifact.mender",
            ],
            check=True,
        )
        return True
    except subprocess.CalledProcessError as e:
        log.error(f"Failed to run the install script '/usr/share/mender/install' {e}")
    return False
