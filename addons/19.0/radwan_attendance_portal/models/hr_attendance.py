# -*- coding: utf-8 -*-

from odoo import _, fields, models
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
