# -*- coding: utf-8 -*-

from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    radwan_non_renewal = fields.Boolean(
        related="version_id.radwan_non_renewal",
        readonly=False,
        inherited=True,
        groups="hr.group_hr_manager",
    )
    radwan_work_entry_source = fields.Selection(
        related="version_id.radwan_work_entry_source",
        readonly=False,
        inherited=True,
        groups="hr.group_hr_manager",
    )
    radwan_working_hours = fields.Float(
        related="version_id.radwan_working_hours",
        readonly=False,
        inherited=True,
        groups="hr.group_hr_manager",
    )
    radwan_notice_period = fields.Char(
        related="version_id.radwan_notice_period",
        readonly=False,
        inherited=True,
        groups="hr.group_hr_manager",
    )
    radwan_employer_termination_penalty = fields.Monetary(
        related="version_id.radwan_employer_termination_penalty",
        readonly=False,
        inherited=True,
        currency_field="currency_id",
        groups="hr.group_hr_manager",
    )
    radwan_employee_termination_penalty = fields.Monetary(
        related="version_id.radwan_employee_termination_penalty",
        readonly=False,
        inherited=True,
        currency_field="currency_id",
        groups="hr.group_hr_manager",
    )
    radwan_contract_other_notes = fields.Text(
        related="version_id.radwan_contract_other_notes",
        readonly=False,
        inherited=True,
        groups="hr.group_hr_manager",
    )
    radwan_basic = fields.Monetary(
        related="version_id.radwan_basic",
        readonly=False,
        inherited=True,
        currency_field="currency_id",
        groups="hr.group_hr_manager",
    )
    radwan_housing = fields.Monetary(
        related="version_id.radwan_housing",
        readonly=False,
        inherited=True,
        currency_field="currency_id",
        groups="hr.group_hr_manager",
    )
    radwan_transportation = fields.Monetary(
        related="version_id.radwan_transportation",
        readonly=False,
        inherited=True,
        currency_field="currency_id",
        groups="hr.group_hr_manager",
    )
    radwan_fuel_car_allowance = fields.Monetary(
        related="version_id.radwan_fuel_car_allowance",
        readonly=False,
        inherited=True,
        currency_field="currency_id",
        groups="hr.group_hr_manager",
    )
    radwan_mobile_communications_allowance = fields.Monetary(
        related="version_id.radwan_mobile_communications_allowance",
        readonly=False,
        inherited=True,
        currency_field="currency_id",
        groups="hr.group_hr_manager",
    )
    radwan_other_allowances = fields.Monetary(
        related="version_id.radwan_other_allowances",
        readonly=False,
        inherited=True,
        currency_field="currency_id",
        groups="hr.group_hr_manager",
    )
    radwan_total_salary = fields.Monetary(
        related="version_id.radwan_total_salary",
        inherited=True,
        currency_field="currency_id",
        groups="hr.group_hr_manager",
    )
    radwan_salary_structure_type_id = fields.Many2one(
        related="version_id.radwan_salary_structure_type_id",
        readonly=False,
        inherited=True,
        groups="hr.group_hr_manager",
    )
    radwan_gosi_not_appear_in_payslip = fields.Boolean(
        related="version_id.radwan_gosi_not_appear_in_payslip",
        readonly=False,
        inherited=True,
        groups="hr.group_hr_manager",
    )
    radwan_trial_start_date = fields.Date(
        related="version_id.radwan_trial_start_date",
        readonly=False,
        inherited=True,
        groups="hr.group_hr_manager",
    )
    radwan_extended_trial_start_date = fields.Date(
        related="version_id.radwan_extended_trial_start_date",
        readonly=False,
        inherited=True,
        groups="hr.group_hr_manager",
    )
    radwan_extended_trial_end_date = fields.Date(
        related="version_id.radwan_extended_trial_end_date",
        readonly=False,
        inherited=True,
        groups="hr.group_hr_manager",
    )
    radwan_allow_overtime = fields.Boolean(
        related="version_id.radwan_allow_overtime",
        readonly=False,
        inherited=True,
        groups="hr.group_hr_manager",
    )
