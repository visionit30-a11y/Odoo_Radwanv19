# -*- coding: utf-8 -*-

from datetime import datetime, time, timedelta

import pytz

from odoo import api, models


class HrLeave(models.Model):
    _inherit = "hr.leave"

    @api.depends(
        "date_from",
        "date_to",
        "resource_calendar_id",
        "holiday_status_id.request_unit",
        "holiday_status_id.include_weekly_off_at_start",
        "holiday_status_id.include_weekly_off_inside",
        "holiday_status_id.include_weekly_off_at_end",
    )
    def _compute_duration(self):
        return super()._compute_duration()

    def _get_durations(self, check_leave_type=True, resource_calendar=None):
        durations = super()._get_durations(check_leave_type=check_leave_type, resource_calendar=resource_calendar)
        if not check_leave_type:
            return durations
        for leave in self:
            extra_days = leave._radwan_get_counted_weekly_off_days(resource_calendar=resource_calendar)
            if not extra_days:
                continue
            days, hours = durations.get(leave.id, (0, 0))
            calendar = resource_calendar or leave.resource_calendar_id
            hours_per_day = calendar.hours_per_day or 8.0
            durations[leave.id] = (days + extra_days, hours + (extra_days * hours_per_day))
        return durations

    def _radwan_get_counted_weekly_off_days(self, resource_calendar=None):
        self.ensure_one()
        leave_type = self.holiday_status_id
        if not leave_type or not (
            leave_type.include_weekly_off_at_start
            or leave_type.include_weekly_off_inside
            or leave_type.include_weekly_off_at_end
        ):
            return 0
        if not self.employee_id or not self.request_date_from or not self.request_date_to:
            return 0
        if self.leave_type_request_unit != "day":
            return 0

        calendar = resource_calendar or self.resource_calendar_id or self.employee_id.resource_calendar_id
        if not calendar:
            return 0

        days = self._radwan_leave_dates()
        if not days:
            return 0

        working_days = [day for day in days if self._radwan_is_working_day(day, calendar)]
        weekly_off_days = [day for day in days if day not in working_days]
        if not weekly_off_days:
            return 0

        counted = 0
        first_working_day = working_days[0] if working_days else False
        last_working_day = working_days[-1] if working_days else False
        for day in weekly_off_days:
            position = self._radwan_weekly_off_position(day, days, first_working_day, last_working_day)
            if position == "start" and leave_type.include_weekly_off_at_start:
                counted += 1
            elif position == "inside" and leave_type.include_weekly_off_inside:
                counted += 1
            elif position == "end" and leave_type.include_weekly_off_at_end:
                counted += 1
        return counted

    def _radwan_leave_dates(self):
        start_date = self.request_date_from
        end_date = self.request_date_to
        if start_date > end_date:
            return []
        days = []
        current = start_date
        while current <= end_date:
            days.append(current)
            current += timedelta(days=1)
        return days

    def _radwan_is_working_day(self, day, calendar):
        tz = pytz.timezone(calendar.tz or self.employee_id.tz or self.env.user.tz or "UTC")
        day_start = tz.localize(datetime.combine(day, time.min))
        day_end = tz.localize(datetime.combine(day, time.max))
        resource = self.employee_id.resource_id
        intervals = calendar._attendance_intervals_batch(day_start, day_end, resource)[resource.id]
        return bool(intervals)

    def _radwan_weekly_off_position(self, day, days, first_working_day=False, last_working_day=False):
        if first_working_day and day < first_working_day:
            return "start"
        if last_working_day and day > last_working_day:
            return "end"
        if first_working_day and last_working_day:
            return "inside"
        if day == days[0]:
            return "start"
        if day == days[-1]:
            return "end"
        return "inside"
