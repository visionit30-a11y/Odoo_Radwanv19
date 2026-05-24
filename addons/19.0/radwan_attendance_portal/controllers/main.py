# -*- coding: utf-8 -*-

import pytz

from datetime import datetime, time

from odoo import _, fields, http
from odoo.http import request
from odoo.tools import format_date, format_time


class RadwanAttendancePortal(http.Controller):
    def _get_employee(self):
        user = request.env.user
        employee = request.env["hr.employee"].sudo().search([("user_id", "=", user.id)], limit=1)
        return employee or user.sudo().employee_id

    def _employee_timezone(self, employee):
        return employee._get_tz() or request.env.user.tz or "UTC"

    def _today_utc_range(self, employee):
        tz = pytz.timezone(self._employee_timezone(employee))
        today = datetime.now(pytz.utc).astimezone(tz).date()
        start = tz.localize(datetime.combine(today, time.min)).astimezone(pytz.utc).replace(tzinfo=None)
        end = tz.localize(datetime.combine(today, time.max)).astimezone(pytz.utc).replace(tzinfo=None)
        return today, start, end

    def _attendance_domain_today(self, employee):
        today, start, end = self._today_utc_range(employee)
        return today, [
            ("employee_id", "=", employee.id),
            ("check_in", ">=", start),
            ("check_in", "<=", end),
        ]

    def _open_attendance(self, employee):
        return request.env["hr.attendance"].sudo().search(
            [("employee_id", "=", employee.id), ("check_out", "=", False)],
            order="check_in desc",
            limit=1,
        )

    def _attendance_status(self, employee):
        open_attendance = self._open_attendance(employee)
        if open_attendance:
            permission = request.env["radwan.attendance.permission"].sudo().search(
                [
                    ("employee_id", "=", employee.id),
                    ("attendance_id", "=", open_attendance.id),
                    ("state", "in", ("submitted", "approved")),
                ],
                limit=1,
            )
            return "permission" if permission else "present"

        today, domain = self._attendance_domain_today(employee)
        latest_today = request.env["hr.attendance"].sudo().search(domain, order="check_in desc", limit=1)
        return "checked_out" if latest_today and latest_today.check_out else "not_checked_in"

    def _status_label(self, status):
        return {
            "present": _("Present"),
            "checked_out": _("Checked Out"),
            "permission": _("Permission"),
            "not_checked_in": _("Not Checked In"),
        }.get(status, _("Not Checked In"))

    def _format_float_time(self, value):
        if value is None:
            return ""
        hours = int(value)
        minutes = int(round((value - hours) * 60))
        return "%02d:%02d" % (hours, minutes)

    def _attendance_row(self, attendance):
        env = request.env
        tz_name = self._employee_timezone(attendance.employee_id)
        tz = pytz.timezone(tz_name)
        check_in = pytz.utc.localize(attendance.check_in).astimezone(tz) if attendance.check_in else False
        check_out = pytz.utc.localize(attendance.check_out).astimezone(tz) if attendance.check_out else False
        in_maps = (
            "https://maps.google.com?q=%s,%s" % (attendance.in_latitude, attendance.in_longitude)
            if attendance.in_latitude and attendance.in_longitude
            else False
        )
        out_maps = (
            "https://maps.google.com?q=%s,%s" % (attendance.out_latitude, attendance.out_longitude)
            if attendance.out_latitude and attendance.out_longitude
            else False
        )
        return {
            "id": attendance.id,
            "check_in_date": format_date(env, check_in.date()) if check_in else "",
            "check_in_time": format_time(env, attendance.check_in, tz=tz_name) if attendance.check_in else "",
            "check_out_date": format_date(env, check_out.date()) if check_out else "",
            "check_out_time": format_time(env, attendance.check_out, tz=tz_name) if attendance.check_out else "",
            "in_coordinates": "%s, %s" % (attendance.in_latitude, attendance.in_longitude)
            if attendance.in_latitude and attendance.in_longitude
            else "",
            "out_coordinates": "%s, %s" % (attendance.out_latitude, attendance.out_longitude)
            if attendance.out_latitude and attendance.out_longitude
            else "",
            "in_maps": in_maps,
            "out_maps": out_maps,
            "worked_hours": "%.2f" % attendance.worked_hours if attendance.worked_hours else "0.00",
            "status": _("Open") if not attendance.check_out else _("Done"),
        }

    def _employee_values(self, employee):
        status = self._attendance_status(employee)
        return {
            "id": employee.id,
            "name": employee.name or "",
            "department": employee.department_id.name or "",
            "manager": employee.parent_id.name or "",
            "job_title": employee.job_title or "",
            "job": employee.job_id.name or "",
            "nationality": employee.country_id.name or "",
            "status": status,
            "status_label": self._status_label(status),
            "image_url": "/web/image/hr.employee/%s/image_128" % employee.id,
        }

    def _page_values(self, employee):
        today, domain = self._attendance_domain_today(employee)
        attendances = request.env["hr.attendance"].sudo().search(domain, order="check_in asc")
        return {
            "employee": self._employee_values(employee),
            "today": format_date(request.env, today),
            "attendance_rows": [self._attendance_row(attendance) for attendance in attendances],
            "permission_types": [
                ("personal", _("Personal Permission")),
                ("work", _("Work Permission")),
                ("medical", _("Medical Permission")),
                ("other", _("Other")),
            ],
        }

    def _location_values(self, latitude=None, longitude=None, accuracy=None):
        return {
            "latitude": float(latitude or 0.0),
            "longitude": float(longitude or 0.0),
            "accuracy": float(accuracy or 0.0),
        }

    @http.route(["/my/attendance"], type="http", auth="user", website=True, sitemap=False)
    def attendance_portal(self, **kwargs):
        employee = self._get_employee()
        if not employee:
            return request.render("radwan_attendance_portal.radwan_attendance_no_employee")
        return request.render(
            "radwan_attendance_portal.radwan_attendance_portal_page",
            self._page_values(employee),
        )

    @http.route("/my/attendance/action", type="jsonrpc", auth="user", website=True, methods=["POST"])
    def attendance_action(self, action, latitude=None, longitude=None, accuracy=None):
        employee = self._get_employee()
        if not employee:
            return {"success": False, "message": _("No employee is linked to your user.")}

        location = self._location_values(latitude, longitude, accuracy)
        if not location["latitude"] or not location["longitude"]:
            return {"success": False, "message": _("You must allow geolocation.")}

        Attendance = request.env["hr.attendance"].sudo()
        now = fields.Datetime.now()

        if action == "check_in":
            if self._open_attendance(employee):
                return {"success": False, "message": _("Check in is already recorded.")}
            Attendance.create(
                {
                    "employee_id": employee.id,
                    "check_in": now,
                    "in_latitude": location["latitude"],
                    "in_longitude": location["longitude"],
                    "radwan_in_accuracy": location["accuracy"],
                    "radwan_check_in_user_id": request.env.user.id,
                    "radwan_check_in_source": "portal",
                    "in_mode": "manual",
                }
            )
            return {"success": True, "message": _("Check in recorded successfully."), "reload": True}

        if action == "check_out":
            attendance = self._open_attendance(employee)
            if not attendance:
                return {"success": False, "message": _("You cannot check out without check in.")}
            attendance.write(
                {
                    "check_out": now,
                    "out_latitude": location["latitude"],
                    "out_longitude": location["longitude"],
                    "radwan_out_accuracy": location["accuracy"],
                    "radwan_check_out_user_id": request.env.user.id,
                    "radwan_check_out_source": "portal",
                    "out_mode": "manual",
                }
            )
            return {"success": True, "message": _("Check out recorded successfully."), "reload": True}

        return {"success": False, "message": _("Unsupported attendance action.")}

    @http.route("/my/attendance/permission", type="jsonrpc", auth="user", website=True, methods=["POST"])
    def attendance_permission(self, permission_type, time_from, time_to, reason, note="", latitude=None, longitude=None, accuracy=None):
        employee = self._get_employee()
        if not employee:
            return {"success": False, "message": _("No employee is linked to your user.")}

        attendance = self._open_attendance(employee)
        if not attendance:
            return {"success": False, "message": _("You cannot request permission without check in.")}

        location = self._location_values(latitude, longitude, accuracy)
        if not location["latitude"] or not location["longitude"]:
            return {"success": False, "message": _("You must allow geolocation.")}

        request.env["radwan.attendance.permission"].sudo().create(
            {
                "employee_id": employee.id,
                "user_id": request.env.user.id,
                "attendance_id": attendance.id,
                "permission_type": permission_type,
                "time_from": float(time_from or 0.0),
                "time_to": float(time_to or 0.0),
                "reason": reason,
                "note": note,
                "latitude": location["latitude"],
                "longitude": location["longitude"],
                "accuracy": location["accuracy"],
            }
        )
        return {"success": True, "message": _("Permission request submitted."), "reload": True}
