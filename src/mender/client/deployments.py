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
import logging as log
from typing import Optional
from typing import Dict
import os.path
import time
import re

import requests

import mender.settings.settings as settings
import mender.log.log as menderlog
from mender.client import HTTPUnathorized

STATUS_SUCCESS = "success"
STATUS_FAILURE = "failure"
STATUS_DOWNLOADING = "downloading"

DOWNLOAD_RESUME_MIN_INTERVAL = 60
DOWNLOAD_RESUME_MAX_INTERVAL = 10 * 60


class DeploymentDownloadFailed(Exception):
    pass


class DeploymentInfo:
    """Class which holds all the information related to a deployment.

    The information is extracted from the json response from the server, and is
    thus afterwards considered safe to access all the keys in the data.

    """

    def __init__(self, deployment_json: dict) -> None:
        try:
            self.ID = deployment_json["id"]
            self.artifact_name = deployment_json["artifact"]["artifact_name"]
            self.artifact_uri = deployment_json["artifact"]["source"]["uri"]
        except KeyError as e:
            log.error(
                f"The key '{e}' is missing from the deployments/next response JSON"
            )


def request(
    server_url: str,
    JWT: str,
    device_type: Optional[dict],
    artifact_name: Optional[dict],
    server_certificate: str,
) -> Optional[DeploymentInfo]:
    if not server_url:
        log.error("ServerURL not provided. Update cannot proceed")
        return None
    if not device_type:
        log.error("No device_type found. Update cannot proceed")
        return None
    if not artifact_name:
        log.error("No artifact_Name found. Update cannot proceed")
        return None
    headers = {"Content-Type": "application/json", "Authorization": "Bearer " + JWT}
    parameters = {**device_type, **artifact_name}
    try:
        r = requests.get(
            server_url + "/api/devices/v1/deployments/device/deployments/next",
            headers=headers,
            params=parameters,
            verify=server_certificate if server_certificate else True,
        )
        log.debug(f"update: request: {r}")
        deployment_info = None
        if r.status_code == 200:
            log.info(f"New update available: {r.text}")
            update_json = r.json()
            deployment_info = DeploymentInfo(update_json)
        elif r.status_code == 204:
            log.info("No new update available")
        elif r.status_code == 401:
            log.info(f"The client seems to have been unathorized {r}")
            raise HTTPUnathorized()
        else:
            log.error(f"Error {r.reason}. code: {r.status_code}")
            log.debug(f"{r.json()}")
            log.error("Error while fetching update")
        return deployment_info
    except (
        requests.RequestException,
        requests.ConnectionError,
        requests.URLRequired,
        requests.TooManyRedirects,
        requests.Timeout,
    ) as e:
        log.error(e)
        return None


def get_exponential_backoff_time(tried: int, max_interval: int) -> int:
    per_internal_attempts = 3
    smallest_unit = DOWNLOAD_RESUME_MIN_INTERVAL

    interval = smallest_unit
    next_interval = interval
    for count in range(0, tried + 1, per_internal_attempts):
        interval = next_interval
        next_interval *= 2
        if interval >= max_interval:
            if tried - count >= per_internal_attempts:
                raise DeploymentDownloadFailed(
                    f"Max tries exceeded: tries {tried} max_interval {max_interval}"
                )
            if max_interval < smallest_unit:
                return smallest_unit
            return max_interval

    return interval


header_range_regex = re.compile(r"^bytes ([0-9]+)-([0-9]+)/(:?[0-9]+)?")


def parse_range_response(response: requests.Response, offset: int) -> bool:
    if response.status_code != requests.status_codes.codes["partial_content"]:
        return False

    h_range_str = str(response.headers.get("Content-Range"))
    log.debug(f"Content-Range received from server: '{h_range_str}'")

    match = header_range_regex.match(h_range_str)
    if not match:
        raise DeploymentDownloadFailed(
            f"Cannot match Content-Range header: '{h_range_str}'"
        )

    new_offset = int(match.group(1))
    log.debug(
        f"Successfully parsed '{h_range_str}', new_offset {new_offset}, offset {offset},"
    )

    if new_offset > offset:
        raise DeploymentDownloadFailed(
            f"Missing data. Got Content-Range header: '{h_range_str}'"
        )

    if new_offset < offset:
        log.debug(f"Discarding {offset-new_offset} bytes")
        size_to_discard = offset - new_offset
        while size_to_discard > 0:
            chunk_size = 1024 * 1024
            if size_to_discard < chunk_size:
                chunk_size = size_to_discard
            log.debug(f"Discarding chunk of  {chunk_size    } bytes")
            for _ in response.iter_content(chunk_size=chunk_size):
                size_to_discard -= chunk_size
                break

    return True


def download(
    deployment_data: DeploymentInfo, artifact_path: str, server_certificate: str
) -> bool:
    """Download the update artifact to the artifact_path"""
    if not artifact_path:
        log.error("No path provided in which to store the Artifact")
        return False
    try:
        return download_and_resume(deployment_data, artifact_path, server_certificate)
    except DeploymentDownloadFailed as e:
        log.error(e)
        return False


def download_and_resume(
    deployment_data: DeploymentInfo, artifact_path: str, server_certificate: str
) -> bool:
    """Download the update artifact to the artifact_path"""
    if not artifact_path:
        log.error("No path provided in which to store the Artifact")
        return False

    update_url = deployment_data.artifact_uri
    log.info(f"Downloading Artifact: {artifact_path}")
    with open(artifact_path, "wb") as fh:
        # Truncate file, if exists
        pass

    # Loop  will try/except until download is complete or exhaust the retries
    offset = 0
    content_length = None
    tried = 0
    while True:
        try:
            req_headers: Dict[str, str] = {}
            if content_length:
                req_headers["Range"] = f"bytes={offset}-"
                log.debug(f"Request with headers {req_headers}")
            with requests.get(
                update_url,
                headers=req_headers,
                stream=True,
                verify=server_certificate if server_certificate else True,
            ) as response:
                if not content_length:
                    content_length = int(str(response.headers.get("Content-Length")))
                    log.debug(f"content_length: {content_length}")
                if "Range" in req_headers:
                    if not parse_range_response(response, offset):
                        log.debug("Server ignored our range request, resetting offset")
                        offset = 0
                log.debug(f"Opening file to write at offset {offset}")
                with open(artifact_path, "rb+") as fh:
                    fh.seek(offset)
                    for data in response.iter_content(
                        chunk_size=1024 * 1024
                    ):  # 1MiB at a time
                        if not data:
                            break
                        fh.write(data)
                        offset += len(data)
                        fh.flush()
                # Download completed in one go, return
                log.debug(f"Got EOF. Wrote {offset} bytes. Total is {content_length}.")
                if offset >= content_length:
                    return True
        except (
            requests.RequestException,
            requests.ConnectionError,
            requests.URLRequired,
            requests.TooManyRedirects,
            requests.Timeout,
        ) as e:
            log.error(e)
            log.debug(f"Got Error. Wrote {offset} bytes. Total is {content_length}.")

        # Prepare for next attempt
        next_attempt_in = get_exponential_backoff_time(
            tried, DOWNLOAD_RESUME_MAX_INTERVAL
        )
        tried += 1
        log.debug(f"Next attempt in {next_attempt_in} seconds, sleeping...")
        time.sleep(next_attempt_in)
        log.debug("Resuming!")


def report(
    server_url: str,
    status: str,
    deployment_id: str,
    server_certificate: str,
    JWT: str,
    deployment_logger: Optional[menderlog.DeploymentLogHandler] = None,
) -> bool:
    """Report update :param status to the Mender server"""
    if not status:
        log.error("No status given to report")
        return False
    try:
        headers = {"Content-Type": "application/json", "Authorization": "Bearer " + JWT}
        response = requests.put(
            server_url
            + "/api/devices/v1/deployments/device/deployments/"
            + deployment_id
            + "/status",
            headers=headers,
            verify=server_certificate if server_certificate else True,
            json={"status": status},
        )
        if response.status_code != 204:
            log.error(
                f"Failed to upload the deployment status '{status}',\
                error: {response.status_code}: {response.reason}"
            )
            return False
        if status == STATUS_FAILURE:
            menderlog.add_sub_updater_log(
                os.path.join(settings.PATHS.data_store, "sub-updater.log")
            )
            if deployment_logger:
                logdata = deployment_logger.marshal()
            else:
                log.error("No deployment log handler given")
                return True

            response = requests.put(
                server_url
                + "/api/devices/v1/deployments/device/deployments/"
                + deployment_id
                + "/log",
                headers=headers,
                verify=server_certificate if server_certificate else True,
                json={"messages": logdata,},
            )
            if response.status_code != 204:
                log.error(
                    f"Failed to upload the deployment log,\
                    error: {response.status_code}: {response.reason} {response.text}"
                )
                return False
    except (
        requests.RequestException,
        requests.ConnectionError,
        requests.URLRequired,
        requests.TooManyRedirects,
        requests.Timeout,
    ) as e:
        log.error(e)
        return False
    return True
