# coding=utf-8

import pytz
from collections import namedtuple
import datetime as dt

from celery import schedules


schedstate = namedtuple('schedstate', ('is_due', 'next'))


class TzAwareCrontab(schedules.crontab):

    def __init__(
            self, minute='*', hour='*', day_of_week='*',
            day_of_month='*', month_of_year='*', tz=pytz.utc, app=None
    ):
        self.tz = tz

        nowfun = self.nowfunc

        super(TzAwareCrontab, self).__init__(
            minute=minute, hour=hour, day_of_week=day_of_week,
            day_of_month=day_of_month, month_of_year=month_of_year,
            # tz=tz,
            nowfun=nowfun, app=app
        )

    def nowfunc(self):
        return self.tz.normalize(
            pytz.utc.localize(dt.datetime.utcnow())
        )

    def is_due(self, last_run_at):

        rem_delta = self.remaining_estimate(last_run_at)
        rem = max(rem_delta.total_seconds(), 0)
        due = rem == 0
        if due:
            rem_delta = self.remaining_estimate(self.now())
            rem = max(rem_delta.total_seconds(), 0)
        return schedstate(due, rem)

    def __repr__(self):
        return """<crontab: {0._orig_minute} {0._orig_hour} \
{0._orig_day_of_week} {0._orig_day_of_month} \
{0._orig_month_of_year} (m/h/d/dM/MY), {0.tz}>""".format(self)

    def __reduce__(self):
        return (self.__class__, (self._orig_minute,
                                 self._orig_hour,
                                 self._orig_day_of_week,
                                 self._orig_day_of_month,
                                 self._orig_month_of_year,
                                 self.tz), None)

    def __eq__(self, other):
        if isinstance(other, schedules.crontab):
            return (other.month_of_year == self.month_of_year
                    and other.day_of_month == self.day_of_month
                    and other.day_of_week == self.day_of_week
                    and other.hour == self.hour
                    and other.minute == self.minute
                    and other.tz == self.tz)
        return NotImplemented
