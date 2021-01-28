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
import time

from mender.util import timeutil


class TestUtil:
    INTERVAL = 8
    DT = 0.9

    def test_is_it_time(self):
        timer = timeutil.IsItTime(self.INTERVAL)
        assert timer.is_it_time()
        assert not timer.is_it_time()
        time.sleep(self.INTERVAL + 1)
        assert timer.is_it_time()

    def test_is_it_time_zero_timeout(self):
        timer = timeutil.IsItTime(0)
        start_time = time.time()
        assert timer.is_it_time()
        assert timer.is_it_time()
        end_time = time.time()
        assert (end_time - start_time) <= self.DT

    def test_is_it_time_sleep_full(self):
        timer = timeutil.IsItTime(self.INTERVAL)
        timer.is_it_time()
        start_time = time.time()
        timeutil.sleep(timer)
        end_time = time.time()
        assert (end_time - start_time - self.INTERVAL) <= self.DT

    def test_is_it_time_sleep_full_shortest(self):
        timer = timeutil.IsItTime(self.INTERVAL)
        longer_timer = timeutil.IsItTime(self.INTERVAL * 2)
        timer.is_it_time()
        longer_timer.is_it_time()
        start_time = time.time()
        timeutil.sleep(longer_timer, timer)
        end_time = time.time()
        assert (end_time - start_time - self.INTERVAL) <= self.DT

    def test_is_it_time_sleep_partial(self):
        timer = timeutil.IsItTime(self.INTERVAL)
        timer.is_it_time()
        start_time = time.time()
        time.sleep(timer.seconds_till_next() * 0.5)
        timeutil.sleep(timer)
        end_time = time.time()
        assert (end_time - start_time - self.INTERVAL) <= self.DT

    def test_is_it_time_sleep_partial_shortest(self):
        timer = timeutil.IsItTime(self.INTERVAL)
        longer_timer = timeutil.IsItTime(self.INTERVAL * 2)
        timer.is_it_time()
        longer_timer.is_it_time()
        start_time = time.time()
        time.sleep(timer.seconds_till_next() * 0.5)
        timeutil.sleep(longer_timer, timer)
        end_time = time.time()
        assert (end_time - start_time - self.INTERVAL) <= self.DT
