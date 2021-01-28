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
from datetime import timedelta
from datetime import datetime
import time
import typing


class IsItTime:
    """Objects of this class store a time interval and tell you if it is elapsed"""

    def __init__(self, interval):
        self.interval_seconds = interval
        self.next_trigger_at = datetime.now()

    def get_next(self):
        return datetime.now() + timedelta(0, self.interval_seconds)

    def seconds_till_next(self):
        return self.next_trigger_at.timestamp() - datetime.now().timestamp()

    def is_it_time(self):
        if self.next_trigger_at <= datetime.now():
            self.next_trigger_at = self.get_next()
            return True
        return False


def sleep(is_it_time: IsItTime, is_it_time_parallel: typing.Optional[IsItTime] = None):
    secs_until_next = is_it_time.seconds_till_next()

    if (
        is_it_time_parallel
        and is_it_time_parallel.seconds_till_next() < secs_until_next
    ):
        secs_until_next = is_it_time_parallel.seconds_till_next()

    if secs_until_next <= 0:
        return

    time.sleep(secs_until_next)
