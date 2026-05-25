# -*- coding: utf-8 -*-

import pytz

from datetime import datetime, time
from math import asin, cos, radians, sin, sqrt

from odoo import _, fields, http
from odoo.http import request
from odoo.tools import format_date, format_time


class RadwanAttendancePortal(http.Controller):
    def _config_bool(self, key, default=False):
        value = request.env["ir.config_parameter"].sudo().get_param(key)
        if value is None:
            return default
        return value in ("1", "True", "true")

    def _config_float(self, key, default=0.0):
        value = request.env["ir.config_parameter"].sudo().get_param(key)
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def _config_text(self, key, default=""):
        return request.env["ir.config_parameter"].sudo().get_param(key) or default

    def _bool_param(self, value):
        return value in (True, 1, "1", "True", "true", "yes", "on")

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

    def _latest_attendance_today(self, employee):
        today, domain = self._attendance_domain_today(employee)
        return request.env["hr.attendance"].sudo().search(domain, order="check_in desc, id desc", limit=1)

    def _duplicate_attendance_for_action(self, employee, action):
        latest_today = self._latest_attendance_today(employee)
        if action == "check_in":
            return latest_today
        if action == "check_out":
            open_attendance = self._open_attendance(employee)
            if open_attendance:
                return False
            return latest_today if latest_today and latest_today.check_out else False
        return False

    def _duplicate_attendance_message(self, attendance, action):
        field_name = "check_in" if action == "check_in" else "check_out"
        action_label = _("Check in") if action == "check_in" else _("Check out")
        action_time = format_time(
            request.env,
            attendance[field_name],
            tz=self._employee_timezone(attendance.employee_id),
        )
        return _(
            "%(action)s is already recorded for this date at %(time)s. Do you want to update it?",
            action=action_label,
            time=action_time,
        )

    def _duplicate_attendance_response(self, attendance, action):
        return {
            "success": False,
            "needs_confirmation": True,
            "message": self._duplicate_attendance_message(attendance, action),
            "confirm_label": _("Yes, update"),
            "cancel_label": _("No, keep current record"),
            "cancel_message": _("No changes were made."),
        }

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
            "approval_status": _(
                dict(attendance._fields["radwan_approval_state"].selection).get(attendance.radwan_approval_state)
            )
            if attendance.radwan_approval_state
            else "",
        }

    def _permission_state_label(self, state):
        return {
            "draft": _("Draft"),
            "submitted": _("Submitted"),
            "approved": _("Approved"),
            "refused": _("Refused"),
        }.get(state, state or "")

    def _permission_state_class(self, state):
        return {
            "draft": "muted",
            "submitted": "warning",
            "approved": "success",
            "refused": "danger",
        }.get(state, "muted")

    def _permission_row(self, permission):
        return {
            "id": permission.id,
            "request_date": format_date(request.env, permission.request_date) if permission.request_date else "",
            "permission_type": dict(permission._fields["permission_type"].selection).get(permission.permission_type),
            "time_from": self._format_float_time(permission.time_from),
            "time_to": self._format_float_time(permission.time_to),
            "reason": permission.reason or "",
            "state": permission.state,
            "state_label": self._permission_state_label(permission.state),
            "state_class": self._permission_state_class(permission.state),
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
        permissions = request.env["radwan.attendance.permission"].sudo().search(
            [("employee_id", "=", employee.id), ("request_date", "=", today)],
            order="request_date desc, id desc",
        )
        return {
            "employee": self._employee_values(employee),
            "today": format_date(request.env, today),
            "attendance_rows": [self._attendance_row(attendance) for attendance in attendances],
            "permission_rows": [self._permission_row(permission) for permission in permissions],
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

    def _clean_photo_data(self, photo_data=None):
        if not photo_data:
            return False
        if "," in photo_data:
            return photo_data.split(",", 1)[1]
        return photo_data

    def _attendance_photo_required(self, employee, check_result):
        if self._config_bool("radwan_attendance_portal.photo_required", False):
            return True
        accepted_location = check_result["accepted_location"]
        if accepted_location and accepted_location.radwan_require_attendance_photo:
            return True
        assigned_locations = employee.radwan_attendance_location_ids.filtered(
            lambda location: location.active and location.radwan_require_attendance_photo
        )
        return bool(assigned_locations)

    def _distance_meters(self, lat1, lon1, lat2, lon2):
        earth_radius = 6371000.0
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        return earth_radius * 2 * asin(sqrt(a))

    def _location_check(self, employee, location):
        geo_required = self._config_bool("radwan_attendance_portal.geo_required", True)
        max_accuracy = self._config_float("radwan_attendance_portal.max_accuracy", 150.0)
        show_distance = self._config_bool("radwan_attendance_portal.show_distance_details", True)
        outside_message = self._config_text(
            "radwan_attendance_portal.outside_range_message",
            _("You are outside your allowed attendance locations. The operation cannot be recorded from this location."),
        )
        weak_accuracy_message = self._config_text(
            "radwan_attendance_portal.weak_accuracy_message",
            _("Location accuracy is weak. Please try again from a clearer location."),
        )

        result = {
            "status": "inside",
            "accepted_location": False,
            "nearest_location": False,
            "distance": 0.0,
            "allowed_radius": 0.0,
            "warning": "",
            "validity_status": False,
            "validity_warning": "",
            "reject": False,
            "reason": False,
        }

        if not location["latitude"] or not location["longitude"]:
            result.update(
                {
                    "status": "unavailable",
                    "warning": _("You must allow geolocation."),
                    "reject": geo_required,
                    "reason": "location_unavailable",
                }
            )
            return result

        if location["accuracy"] and max_accuracy and location["accuracy"] > max_accuracy:
            result.update(
                {
                    "status": "weak_accuracy",
                    "warning": weak_accuracy_message,
                    "reject": True,
                    "reason": "weak_accuracy",
                }
            )
            return result

        locations = employee.radwan_attendance_location_ids.filtered(lambda loc: loc.active and loc.latitude and loc.longitude)
        if not locations:
            result.update(
                {
                    "status": "unavailable",
                    "warning": _("No attendance locations are configured for this employee."),
                    "reject": self._config_bool("radwan_attendance_portal.reject_outside_range", True),
                    "reason": "location_unavailable",
                }
            )
            return result

        nearest = False
        nearest_distance = 0.0
        accepted = False
        for allowed_location in locations:
            distance = self._distance_meters(
                location["latitude"],
                location["longitude"],
                allowed_location.latitude,
                allowed_location.longitude,
            )
            if not nearest or distance < nearest_distance:
                nearest = allowed_location
                nearest_distance = distance
            if distance <= allowed_location.allowed_radius:
                accepted = allowed_location
                break

        if accepted:
            validity_review = accepted.radwan_get_validity_review(fields.Date.context_today(request.env.user))
            result.update(
                {
                    "status": "inside",
                    "accepted_location": accepted,
                    "nearest_location": accepted,
                    "distance": nearest_distance if nearest else 0.0,
                    "allowed_radius": accepted.allowed_radius,
                    "validity_status": validity_review["status"],
                    "validity_warning": validity_review["warning"],
                }
            )
            return result

        allowed_radius = nearest.allowed_radius if nearest else 0.0
        validity_review = (
            nearest.radwan_get_validity_review(fields.Date.context_today(request.env.user))
            if nearest
            else {"status": False, "warning": ""}
        )
        warning = outside_message
        if show_distance and nearest:
            warning = _(
                "You are outside your allowed attendance locations. Nearest location: %(location)s, current distance: %(distance).0f m, allowed range: %(radius).0f m, current accuracy: %(accuracy).0f m.",
                location=nearest.name,
                distance=nearest_distance,
                radius=allowed_radius,
                accuracy=location["accuracy"] or 0.0,
            )
        result.update(
            {
                "status": "outside",
                "nearest_location": nearest,
                "distance": nearest_distance,
                "allowed_radius": allowed_radius,
                "warning": warning,
                "validity_status": validity_review["status"],
                "validity_warning": validity_review["warning"],
                "reject": self._config_bool("radwan_attendance_portal.reject_outside_range", True),
                "reason": "outside_range",
            }
        )
        return result

    def _location_payload(self, location, check_result, prefix, photo_data=None):
        photo = self._clean_photo_data(photo_data)
        values = {
            "radwan_location_status": check_result["status"],
            "radwan_location_warning_message": check_result["warning"],
            "radwan_location_validity_status": check_result["validity_status"],
            "radwan_location_validity_warning": check_result["validity_warning"],
            "radwan_nearest_attendance_location_id": check_result["nearest_location"].id
            if check_result["nearest_location"]
            else False,
            "radwan_distance_to_nearest_location": check_result["distance"],
            "radwan_allowed_radius": check_result["allowed_radius"],
        }
        if prefix == "in":
            values.update(
                {
                    "in_latitude": location["latitude"],
                    "in_longitude": location["longitude"],
                    "radwan_in_accuracy": location["accuracy"],
                    "radwan_checkin_latitude": location["latitude"],
                    "radwan_checkin_longitude": location["longitude"],
                    "radwan_checkin_accuracy": location["accuracy"],
                    "radwan_checkin_location_id": check_result["accepted_location"].id
                    if check_result["accepted_location"]
                    else False,
                    "radwan_checkin_photo": photo,
                }
            )
        else:
            values.update(
                {
                    "out_latitude": location["latitude"],
                    "out_longitude": location["longitude"],
                    "radwan_out_accuracy": location["accuracy"],
                    "radwan_checkout_latitude": location["latitude"],
                    "radwan_checkout_longitude": location["longitude"],
                    "radwan_checkout_accuracy": location["accuracy"],
                    "radwan_checkout_location_id": check_result["accepted_location"].id
                    if check_result["accepted_location"]
                    else False,
                    "radwan_checkout_photo": photo,
                }
            )
        return values

    def _log_rejected_attempt(self, employee, action, location, check_result):
        if not self._config_bool("radwan_attendance_portal.log_rejected_attempts", True):
            return
        request.env["radwan.attendance.attempt.log"].sudo().create(
            {
                "employee_id": employee.id,
                "user_id": request.env.user.id,
                "action_type": action,
                "latitude": location["latitude"],
                "longitude": location["longitude"],
                "accuracy": location["accuracy"],
                "nearest_attendance_location_id": check_result["nearest_location"].id
                if check_result["nearest_location"]
                else False,
                "distance_to_nearest_location": check_result["distance"],
                "allowed_radius": check_result["allowed_radius"],
                "rejection_reason": check_result["reason"] or "outside_range",
                "warning_message": check_result["warning"],
                "user_agent": request.httprequest.headers.get("User-Agent"),
                "ip_address": request.httprequest.remote_addr,
            }
        )

    @http.route(["/my/attendance"], type="http", auth="user", website=True, sitemap=False)
    def attendance_portal(self, **kwargs):
        employee = self._get_employee()
        if not employee:
            return request.render("radwan_attendance_portal.radwan_attendance_no_employee")
        return request.render(
            "radwan_attendance_portal.radwan_attendance_portal_page",
            self._page_values(employee),
        )

    @http.route(
        ["/radwan/attendance/location/<int:location_id>/map-picker"],
        type="http",
        auth="user",
        website=True,
        sitemap=False,
    )
    def attendance_location_map_picker(self, location_id, **kwargs):
        if not request.env.user.has_group("hr_attendance.group_hr_attendance_user"):
            return request.not_found()
        location = request.env["radwan.attendance.location"].sudo().browse(location_id).exists()
        if not location:
            return request.not_found()
        return request.render(
            "radwan_attendance_portal.radwan_attendance_location_map_picker",
            {"location": location},
        )

    @http.route(
        "/radwan/attendance/location/<int:location_id>/save-map",
        type="jsonrpc",
        auth="user",
        website=True,
        methods=["POST"],
    )
    def attendance_location_save_map(self, location_id, latitude, longitude, allowed_radius):
        if not request.env.user.has_group("hr_attendance.group_hr_attendance_user"):
            return {"success": False, "message": _("You do not have access to update attendance locations.")}
        location = request.env["radwan.attendance.location"].sudo().browse(location_id).exists()
        if not location:
            return {"success": False, "message": _("Attendance location was not found.")}
        location.write(
            {
                "latitude": float(latitude or 0.0),
                "longitude": float(longitude or 0.0),
                "allowed_radius": float(allowed_radius or 100.0),
            }
        )
        return {"success": True, "message": _("Attendance location saved successfully.")}

    @http.route("/my/attendance/photo-policy", type="jsonrpc", auth="user", website=True, methods=["POST"])
    def attendance_photo_policy(self, action, latitude=None, longitude=None, accuracy=None, update_existing=False):
        employee = self._get_employee()
        if not employee:
            return {"success": False, "message": _("No employee is linked to your user.")}

        update_existing = self._bool_param(update_existing)
        duplicate_attendance = self._duplicate_attendance_for_action(employee, action)
        if duplicate_attendance and not update_existing:
            return self._duplicate_attendance_response(duplicate_attendance, action)

        if action == "check_out" and not self._open_attendance(employee):
            duplicate_attendance = self._duplicate_attendance_for_action(employee, action)
            if not duplicate_attendance:
                return {"success": False, "message": _("You cannot check out without check in.")}

        location = self._location_values(latitude, longitude, accuracy)
        check_result = self._location_check(employee, location)
        if check_result["reject"]:
            self._log_rejected_attempt(employee, action, location, check_result)
            return {"success": False, "message": check_result["warning"]}

        return {
            "success": True,
            "require_photo": self._attendance_photo_required(employee, check_result),
            "message": _("Please capture an attendance photo before continuing."),
        }

    @http.route("/my/attendance/action", type="jsonrpc", auth="user", website=True, methods=["POST"])
    def attendance_action(self, action, latitude=None, longitude=None, accuracy=None, photo_data=None, update_existing=False):
        employee = self._get_employee()
        if not employee:
            return {"success": False, "message": _("No employee is linked to your user.")}

        update_existing = self._bool_param(update_existing)
        duplicate_attendance = self._duplicate_attendance_for_action(employee, action)
        if duplicate_attendance and not update_existing:
            return self._duplicate_attendance_response(duplicate_attendance, action)

        if action == "check_out" and not self._open_attendance(employee):
            duplicate_attendance = self._duplicate_attendance_for_action(employee, action)
            if not duplicate_attendance:
                return {"success": False, "message": _("You cannot check out without check in.")}

        location = self._location_values(latitude, longitude, accuracy)
        check_result = self._location_check(employee, location)
        if check_result["reject"]:
            self._log_rejected_attempt(employee, action, location, check_result)
            return {"success": False, "message": check_result["warning"]}

        if self._attendance_photo_required(employee, check_result) and not photo_data:
            return {"success": False, "message": _("Please capture an attendance photo before continuing.")}

        Attendance = request.env["hr.attendance"].sudo()
        now = fields.Datetime.now()

        if action == "check_in":
            if update_existing and duplicate_attendance:
                duplicate_attendance.write(
                    {
                        "check_in": now,
                        "radwan_check_in_user_id": request.env.user.id,
                        "radwan_check_in_source": "portal",
                        "in_mode": "manual",
                        "radwan_approval_state": "to_review",
                        "radwan_approved_by_id": False,
                        "radwan_approved_date": False,
                        "radwan_rejected_by_id": False,
                        "radwan_rejected_date": False,
                        "radwan_rejection_reason": False,
                        **self._location_payload(location, check_result, "in", photo_data),
                    }
                )
                return {"success": True, "message": _("Check in updated successfully."), "reload": True}
            Attendance.create(
                {
                    "employee_id": employee.id,
                    "check_in": now,
                    "radwan_check_in_user_id": request.env.user.id,
                    "radwan_check_in_source": "portal",
                    "in_mode": "manual",
                    **self._location_payload(location, check_result, "in", photo_data),
                }
            )
            return {"success": True, "message": _("Check in recorded successfully."), "reload": True}

        if action == "check_out":
            attendance = duplicate_attendance if update_existing and duplicate_attendance else self._open_attendance(employee)
            if not attendance:
                return {"success": False, "message": _("You cannot check out without check in.")}
            attendance.write(
                {
                    "check_out": now,
                    "radwan_check_out_user_id": request.env.user.id,
                    "radwan_check_out_source": "portal",
                    "out_mode": "manual",
                    "radwan_approval_state": "to_review",
                    "radwan_approved_by_id": False,
                    "radwan_approved_date": False,
                    "radwan_rejected_by_id": False,
                    "radwan_rejected_date": False,
                    "radwan_rejection_reason": False,
                    **self._location_payload(location, check_result, "out", photo_data),
                }
            )
            message = _("Check out updated successfully.") if update_existing and duplicate_attendance else _("Check out recorded successfully.")
            return {"success": True, "message": message, "reload": True}

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
        check_result = self._location_check(employee, location)
        if check_result["reject"]:
            self._log_rejected_attempt(employee, "permission", location, check_result)
            return {"success": False, "message": check_result["warning"]}

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
