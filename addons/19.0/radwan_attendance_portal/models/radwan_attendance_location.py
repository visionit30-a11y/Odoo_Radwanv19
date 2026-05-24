# -*- coding: utf-8 -*-

from odoo import fields, models


class RadwanAttendanceLocation(models.Model):
    _name = "radwan.attendance.location"
    _description = "Attendance Work Location"
    _order = "sequence, name"

    name = fields.Char(string="Location Name", required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    latitude = fields.Float(string="Latitude", digits=(10, 7), aggregator=None)
    longitude = fields.Float(string="Longitude", digits=(10, 7), aggregator=None)
    allowed_radius = fields.Float(string="Allowed Radius (m)", default=100.0, required=True, aggregator=None)
    radwan_require_attendance_photo = fields.Boolean(string="Require Attendance Photo")
    note = fields.Text(string="Notes")
    employee_ids = fields.Many2many(
        "hr.employee",
        "radwan_employee_attendance_location_rel",
        "location_id",
        "employee_id",
        string="Employees",
    )
    google_maps_url = fields.Char(string="Google Maps URL", compute="_compute_map_urls")
    map_picker_url = fields.Char(string="Map Picker URL", compute="_compute_map_urls")

    def _compute_map_urls(self):
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url", "")
        for location in self:
            if location.latitude and location.longitude:
                location.google_maps_url = "https://maps.google.com?q=%s,%s" % (
                    location.latitude,
                    location.longitude,
                )
            else:
                location.google_maps_url = False
            location.map_picker_url = "%s/radwan/attendance/location/%s/map-picker" % (base_url, location.id)

    def action_open_google_maps(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_url",
            "url": self.google_maps_url or "https://maps.google.com",
            "target": "new",
        }

    def action_open_map_picker(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_url",
            "url": self.map_picker_url,
            "target": "new",
        }
