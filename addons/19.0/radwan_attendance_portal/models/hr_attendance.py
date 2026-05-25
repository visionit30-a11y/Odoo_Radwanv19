# -*- coding: utf-8 -*-

from markupsafe import escape

from odoo import api, _, fields, models
from odoo.exceptions import UserError


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    radwan_in_accuracy = fields.Float(string="Check In Accuracy", readonly=True, aggregator=None)
    radwan_out_accuracy = fields.Float(string="Check Out Accuracy", readonly=True, aggregator=None)
    radwan_check_in_user_id = fields.Many2one("res.users", string="Check In User", readonly=True)
    radwan_check_out_user_id = fields.Many2one("res.users", string="Check Out User", readonly=True)
    radwan_check_in_source = fields.Selection(
        selection=[
            ("portal", "Employee Portal"),
            ("backend", "Backend"),
        ],
        string="Check In Source",
        readonly=True,
    )
    radwan_check_out_source = fields.Selection(
        selection=[
            ("portal", "Employee Portal"),
            ("backend", "Backend"),
        ],
        string="Check Out Source",
        readonly=True,
    )
    radwan_location_status = fields.Selection(
        selection=[
            ("inside", "Inside Range"),
            ("outside", "Outside Range"),
            ("weak_accuracy", "Weak Location Accuracy"),
            ("unavailable", "Location Unavailable"),
        ],
        string="Location Status",
        readonly=True,
    )
    radwan_location_warning_message = fields.Text(string="Location Warning Message", readonly=True)
    radwan_location_warning_display = fields.Html(
        string="Location Warning Message",
        compute="_compute_radwan_location_review_display",
        sanitize=False,
    )
    radwan_location_validity_status = fields.Selection(
        selection=[
            ("valid", "Valid"),
            ("not_started", "Not Started"),
            ("expired", "Expired"),
            ("no_dates", "No Validity Dates"),
        ],
        string="Location Validity Status",
        readonly=True,
    )
    radwan_location_validity_review_status = fields.Selection(
        selection=[
            ("valid", "Valid"),
            ("not_started", "Not Started"),
            ("expired", "Expired"),
            ("no_dates", "No Validity Dates"),
        ],
        string="Location Validity Status",
        compute="_compute_radwan_location_review_display",
    )
    radwan_location_validity_warning = fields.Text(string="Location Validity Warning", readonly=True)
    radwan_location_validity_warning_display = fields.Html(
        string="Location Validity Warning",
        compute="_compute_radwan_location_review_display",
        sanitize=False,
    )
    radwan_nearest_attendance_location_id = fields.Many2one(
        "radwan.attendance.location",
        string="Nearest Attendance Location",
        readonly=True,
    )
    radwan_distance_to_nearest_location = fields.Float(
        string="Distance to Nearest Location (m)",
        readonly=True,
        aggregator=None,
    )
    radwan_allowed_radius = fields.Float(string="Allowed Radius (m)", readonly=True, aggregator=None)
    radwan_checkin_location_id = fields.Many2one(
        "radwan.attendance.location",
        string="Accepted Check In Location",
        readonly=True,
    )
    radwan_checkout_location_id = fields.Many2one(
        "radwan.attendance.location",
        string="Accepted Check Out Location",
        readonly=True,
    )
    radwan_checkin_latitude = fields.Float(string="Check In Latitude", digits=(10, 7), readonly=True, aggregator=None)
    radwan_checkin_longitude = fields.Float(string="Check In Longitude", digits=(10, 7), readonly=True, aggregator=None)
    radwan_checkin_accuracy = fields.Float(string="Check In Accuracy", readonly=True, aggregator=None)
    radwan_checkout_latitude = fields.Float(string="Check Out Latitude", digits=(10, 7), readonly=True, aggregator=None)
    radwan_checkout_longitude = fields.Float(string="Check Out Longitude", digits=(10, 7), readonly=True, aggregator=None)
    radwan_checkout_accuracy = fields.Float(string="Check Out Accuracy", readonly=True, aggregator=None)
    radwan_checkin_actual_location = fields.Char(
        string="Actual Check In Location",
        compute="_compute_radwan_actual_location_display",
    )
    radwan_checkout_actual_location = fields.Char(
        string="Actual Check Out Location",
        compute="_compute_radwan_actual_location_display",
    )
    radwan_checkin_maps_url = fields.Char(
        string="Actual Check In Map URL",
        compute="_compute_radwan_actual_location_display",
    )
    radwan_checkout_maps_url = fields.Char(
        string="Actual Check Out Map URL",
        compute="_compute_radwan_actual_location_display",
    )
    radwan_checkin_photo = fields.Image(string="Check In Photo", readonly=True, max_width=1280, max_height=1280)
    radwan_checkout_photo = fields.Image(string="Check Out Photo", readonly=True, max_width=1280, max_height=1280)
    radwan_approval_state = fields.Selection(
        selection=[
            ("to_review", "To Review"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ],
        string="Approval Status",
        default="to_review",
        readonly=True,
        copy=False,
    )
    radwan_approved_by_id = fields.Many2one("res.users", string="Approved By", readonly=True, copy=False)
    radwan_approved_date = fields.Datetime(string="Approved Date", readonly=True, copy=False)
    radwan_rejected_by_id = fields.Many2one("res.users", string="Rejected By", readonly=True, copy=False)
    radwan_rejected_date = fields.Datetime(string="Rejected Date", readonly=True, copy=False)
    radwan_rejection_reason = fields.Text(string="Rejection Reason", readonly=True, copy=False)
    radwan_permission_count = fields.Integer(
        string="Permissions",
        compute="_compute_radwan_permission_count",
    )

    @api.depends(
        "check_in",
        "check_out",
        "radwan_approval_state",
        "radwan_location_warning_message",
        "radwan_location_validity_status",
        "radwan_location_validity_warning",
        "radwan_nearest_attendance_location_id",
        "radwan_nearest_attendance_location_id.radwan_valid_from",
        "radwan_nearest_attendance_location_id.radwan_valid_to",
    )
    def _compute_radwan_location_review_display(self):
        for attendance in self:
            color = "#198754" if attendance.radwan_approval_state == "approved" else "#dc3545"
            validity_status, validity_warning = attendance._radwan_location_validity_review_values()
            attendance.radwan_location_validity_review_status = validity_status
            if attendance.radwan_location_warning_message:
                attendance.radwan_location_warning_display = (
                    '<span style="color:%s;font-weight:600;">%s</span>'
                    % (color, escape(attendance.radwan_location_warning_message))
                )
            else:
                attendance.radwan_location_warning_display = False
            if validity_warning:
                attendance.radwan_location_validity_warning_display = (
                    '<span style="color:%s;font-weight:600;">%s</span>'
                    % (color, escape(validity_warning))
                )
            else:
                attendance.radwan_location_validity_warning_display = False

    def _radwan_attendance_review_date(self):
        self.ensure_one()
        datetime_value = self.check_in or self.check_out
        if datetime_value:
            return fields.Datetime.context_timestamp(self, datetime_value).date()
        return fields.Date.context_today(self)

    def _radwan_location_validity_review_values(self):
        self.ensure_one()
        status = self.radwan_location_validity_status
        warning = self.radwan_location_validity_warning
        if (not status or (status == "no_dates" and not warning)) and self.radwan_nearest_attendance_location_id:
            review = self.radwan_nearest_attendance_location_id.radwan_get_validity_review(
                self._radwan_attendance_review_date()
            )
            status = review["status"]
            warning = review["warning"]
        return status, warning

    def _radwan_attendance_permission_dates(self):
        self.ensure_one()
        dates = set()
        for datetime_value in (self.check_in, self.check_out):
            if datetime_value:
                dates.add(fields.Datetime.context_timestamp(self, datetime_value).date())
        return dates

    def _radwan_attendance_permission_domain(self):
        self.ensure_one()
        domain = [("employee_id", "=", self.employee_id.id)]
        dates = list(self._radwan_attendance_permission_dates())
        if self.id and dates:
            domain += ["|", ("attendance_id", "=", self.id), ("request_date", "in", dates)]
        elif self.id:
            domain.append(("attendance_id", "=", self.id))
        elif dates:
            domain.append(("request_date", "in", dates))
        return domain

    def _compute_radwan_permission_count(self):
        Permission = self.env["radwan.attendance.permission"]
        for attendance in self:
            attendance.radwan_permission_count = Permission.search_count(
                attendance._radwan_attendance_permission_domain()
            )

    @api.depends(
        "radwan_checkin_latitude",
        "radwan_checkin_longitude",
        "radwan_checkin_accuracy",
        "radwan_checkout_latitude",
        "radwan_checkout_longitude",
        "radwan_checkout_accuracy",
        "in_latitude",
        "in_longitude",
        "out_latitude",
        "out_longitude",
    )
    def _compute_radwan_actual_location_display(self):
        for attendance in self:
            checkin_latitude = attendance.radwan_checkin_latitude or attendance.in_latitude
            checkin_longitude = attendance.radwan_checkin_longitude or attendance.in_longitude
            checkout_latitude = attendance.radwan_checkout_latitude or attendance.out_latitude
            checkout_longitude = attendance.radwan_checkout_longitude or attendance.out_longitude

            attendance.radwan_checkin_actual_location = attendance._radwan_format_actual_location(
                checkin_latitude,
                checkin_longitude,
                attendance.radwan_checkin_accuracy or attendance.radwan_in_accuracy,
            )
            attendance.radwan_checkout_actual_location = attendance._radwan_format_actual_location(
                checkout_latitude,
                checkout_longitude,
                attendance.radwan_checkout_accuracy or attendance.radwan_out_accuracy,
            )
            attendance.radwan_checkin_maps_url = attendance._radwan_actual_maps_url(
                checkin_latitude,
                checkin_longitude,
            )
            attendance.radwan_checkout_maps_url = attendance._radwan_actual_maps_url(
                checkout_latitude,
                checkout_longitude,
            )

    def _radwan_format_actual_location(self, latitude, longitude, accuracy=0.0):
        if not latitude or not longitude:
            return False
        if accuracy:
            return "%.7f, %.7f (%.0f m accuracy)" % (latitude, longitude, accuracy)
        return "%.7f, %.7f" % (latitude, longitude)

    def _radwan_actual_maps_url(self, latitude, longitude):
        if not latitude or not longitude:
            return False
        return "https://maps.google.com?q=%s,%s" % (latitude, longitude)

    def _radwan_action_open_actual_location(self, url):
        self.ensure_one()
        if not url:
            raise UserError(_("No actual attendance location is available."))
        return {
            "type": "ir.actions.act_url",
            "url": url,
            "target": "new",
        }

    def action_radwan_open_actual_checkin_location(self):
        self.ensure_one()
        return self._radwan_action_open_actual_location(self.radwan_checkin_maps_url)

    def action_radwan_open_actual_checkout_location(self):
        self.ensure_one()
        return self._radwan_action_open_actual_location(self.radwan_checkout_maps_url)

    def action_radwan_open_nearest_location(self):
        self.ensure_one()
        return self.radwan_nearest_attendance_location_id.action_open_google_maps()

    def action_radwan_open_same_day_permissions(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "radwan_attendance_portal.radwan_attendance_permission_action"
        )
        action["name"] = _("Attendance Permissions")
        action["domain"] = self._radwan_attendance_permission_domain()
        action["context"] = {
            "default_employee_id": self.employee_id.id,
            "default_attendance_id": self.id,
        }
        return action

    def _radwan_open_photo_preview(self, photo_field, photo_type, title):
        self.ensure_one()
        photo = self[photo_field]
        if not photo:
            raise UserError(_("No attendance photo is available for preview."))
        wizard = self.env["radwan.attendance.photo.preview"].create(
            {
                "name": title,
                "attendance_id": self.id,
                "photo_type": photo_type,
                "photo": photo,
            }
        )
        return {
            "type": "ir.actions.act_window",
            "name": title,
            "res_model": "radwan.attendance.photo.preview",
            "view_mode": "form",
            "res_id": wizard.id,
            "target": "new",
        }

    def action_radwan_preview_checkin_photo(self):
        return self._radwan_open_photo_preview(
            "radwan_checkin_photo",
            "check_in",
            _("Check In Photo Preview"),
        )

    def action_radwan_preview_checkout_photo(self):
        return self._radwan_open_photo_preview(
            "radwan_checkout_photo",
            "check_out",
            _("Check Out Photo Preview"),
        )

    def action_radwan_approve_attendance(self):
        self.write(
            {
                "radwan_approval_state": "approved",
                "radwan_approved_by_id": self.env.user.id,
                "radwan_approved_date": fields.Datetime.now(),
                "radwan_rejected_by_id": False,
                "radwan_rejected_date": False,
                "radwan_rejection_reason": False,
            }
        )

    def action_radwan_reject_attendance(self):
        self.write(
            {
                "radwan_approval_state": "rejected",
                "radwan_rejected_by_id": self.env.user.id,
                "radwan_rejected_date": fields.Datetime.now(),
                "radwan_rejection_reason": _("Rejected from Odoo attendance review."),
            }
        )
