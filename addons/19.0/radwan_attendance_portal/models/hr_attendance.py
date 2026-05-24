# -*- coding: utf-8 -*-

from odoo import fields, models


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
