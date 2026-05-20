# -*- coding: utf-8 -*-

from odoo import Command, api, fields, models


class HrVersion(models.Model):
    _inherit = "hr.version"

    _RADWAN_PAYROLL_FIELD_MAP = {
        "radwan_housing": "hra",
        "radwan_transportation": "travel_allowance",
        "radwan_other_allowances": "other_allowance",
    }
    _RADWAN_SALARY_AMOUNT_FIELDS = (
        "radwan_basic",
        "wage",
    ) + tuple(_RADWAN_PAYROLL_FIELD_MAP) + (
        "radwan_fuel_car_allowance",
        "radwan_mobile_communications_allowance",
    )

    radwan_non_renewal = fields.Boolean(
        string="Non-Renewal",
        tracking=True,
        groups="hr.group_hr_manager",
    )
    radwan_work_entry_source = fields.Selection(
        selection=[
            ("working_schedule", "Working Schedule"),
            ("attendances", "Attendances"),
            ("planning", "Planning"),
        ],
        string="Work Entry Source",
        default="working_schedule",
        tracking=True,
        groups="hr.group_hr_manager",
    )
    radwan_working_hours = fields.Float(
        string="Working Hours",
        tracking=True,
        groups="hr.group_hr_manager",
    )
    radwan_notice_period = fields.Char(
        string="Notice Period",
        tracking=True,
        groups="hr.group_hr_manager",
    )
    radwan_employer_termination_penalty = fields.Monetary(
        string="Employer Termination Penalty",
        currency_field="currency_id",
        tracking=True,
        groups="hr.group_hr_manager",
    )
    radwan_employee_termination_penalty = fields.Monetary(
        string="Employee Termination Penalty",
        currency_field="currency_id",
        tracking=True,
        groups="hr.group_hr_manager",
    )
    radwan_contract_other_notes = fields.Text(
        string="Other Notes",
        tracking=True,
        groups="hr.group_hr_manager",
    )
    radwan_basic = fields.Monetary(
        string="Basic",
        currency_field="currency_id",
        tracking=True,
        groups="hr.group_hr_manager",
    )
    radwan_housing = fields.Monetary(
        string="Housing",
        currency_field="currency_id",
        tracking=True,
        groups="hr.group_hr_manager",
    )
    radwan_transportation = fields.Monetary(
        string="Transportation",
        currency_field="currency_id",
        tracking=True,
        groups="hr.group_hr_manager",
    )
    radwan_fuel_car_allowance = fields.Monetary(
        string="Fuel and Car Allowance",
        currency_field="currency_id",
        tracking=True,
        groups="hr.group_hr_manager",
    )
    radwan_mobile_communications_allowance = fields.Monetary(
        string="Mobile & Communications Allowance",
        currency_field="currency_id",
        tracking=True,
        groups="hr.group_hr_manager",
    )
    radwan_other_allowances = fields.Monetary(
        string="Other Allowances",
        currency_field="currency_id",
        tracking=True,
        groups="hr.group_hr_manager",
    )
    radwan_total_salary = fields.Monetary(
        string="Total Salary",
        currency_field="currency_id",
        compute="_compute_radwan_total_salary",
        store=True,
        groups="hr.group_hr_manager",
    )
    radwan_salary_structure_type_id = fields.Many2one(
        "hr.payroll.structure.type",
        string="Radwan Legacy Salary Structure Type",
        tracking=True,
        groups="hr.group_hr_manager",
        help="Compatibility field kept in sync with the standard Pay Category.",
    )
    radwan_gosi_not_appear_in_payslip = fields.Boolean(
        string="Hide GOSI on Payslip",
        tracking=True,
        groups="hr.group_hr_manager",
    )
    radwan_trial_start_date = fields.Date(
        string="Trial Start Date",
        tracking=True,
        groups="hr.group_hr_manager",
    )
    radwan_extended_trial_start_date = fields.Date(
        string="Extended Trial Start Date",
        tracking=True,
        groups="hr.group_hr_manager",
    )
    radwan_extended_trial_end_date = fields.Date(
        string="Extended Trial End Date",
        tracking=True,
        groups="hr.group_hr_manager",
    )
    radwan_allow_overtime = fields.Boolean(
        string="Allow Overtime",
        tracking=True,
        groups="hr.group_hr_manager",
    )

    def _radwan_create_company_structure(self, structure_type, company):
        template = self.env.ref(
            "radwan_contract_payroll_custom.radwan_salary_structure",
            raise_if_not_found=False,
        )
        if not template or not structure_type or not company:
            return self.env["hr.payroll.structure"]

        return self.env["hr.payroll.structure"].sudo().create({
            "name": "%s - %s" % (template.name, company.display_name),
            "code": "%s_%s" % (template.code, company.id),
            "company_id": company.id,
            "parent_id": False,
            "radwan_structure_type_id": structure_type.id,
            "rule_ids": [Command.set(template.rule_ids.ids)],
        })

    def _radwan_get_structure_for_type(
        self,
        structure_type,
        company=False,
        create_missing=False,
    ):
        if not structure_type:
            return self.env["hr.payroll.structure"]
        company = company or self.env.company
        structure = self.env["hr.payroll.structure"].search(
            [
                ("radwan_structure_type_id", "=", structure_type.id),
                ("company_id", "=", company.id),
            ],
            limit=1,
        )
        if structure or not create_missing:
            return structure
        return self._radwan_create_company_structure(structure_type, company)

    def _radwan_default_structure(self, company=False, create_missing=False):
        company = company or self.env.company
        structure = self.env.ref(
            "radwan_contract_payroll_custom.radwan_salary_structure",
            raise_if_not_found=False,
        )
        if structure and structure.company_id == company:
            return structure
        structure_type = self.env.ref(
            "radwan_contract_payroll_custom.radwan_salary_structure_type",
            raise_if_not_found=False,
        )
        return self._radwan_get_structure_for_type(
            structure_type,
            company,
            create_missing=create_missing,
        )

    @staticmethod
    def _radwan_amount_changed(old_amount, new_amount):
        return float(old_amount or 0.0) != float(new_amount or 0.0)

    def _radwan_sync_basic_wage_vals(self, vals):
        basic_in_vals = "radwan_basic" in vals
        wage_in_vals = "wage" in vals
        if not basic_in_vals and not wage_in_vals:
            return vals

        if basic_in_vals and not wage_in_vals:
            vals["wage"] = vals["radwan_basic"]
            return vals

        if wage_in_vals and not basic_in_vals:
            vals["radwan_basic"] = vals["wage"]
            return vals

        if len(self) == 1:
            basic_changed = self._radwan_amount_changed(
                self.radwan_basic,
                vals["radwan_basic"],
            )
            wage_changed = self._radwan_amount_changed(self.wage, vals["wage"])
            if basic_changed and not wage_changed:
                vals["wage"] = vals["radwan_basic"]
            elif wage_changed and not basic_changed:
                vals["radwan_basic"] = vals["wage"]
            elif vals["radwan_basic"] != vals["wage"]:
                vals["radwan_basic"] = vals["wage"]
        elif vals["radwan_basic"] != vals["wage"]:
            vals["radwan_basic"] = vals["wage"]

        return vals

    def _radwan_prepare_payroll_sync_vals(self, vals):
        vals = dict(vals)
        vals = self._radwan_sync_basic_wage_vals(vals)

        for custom_field, payroll_field in self._RADWAN_PAYROLL_FIELD_MAP.items():
            if custom_field in vals and payroll_field not in vals:
                vals[payroll_field] = vals[custom_field]
            elif payroll_field in vals and custom_field not in vals:
                vals[custom_field] = vals[payroll_field]

        if "radwan_salary_structure_type_id" in vals and "structure_type_id" not in vals:
            vals["structure_type_id"] = vals["radwan_salary_structure_type_id"]
        elif "structure_type_id" in vals and "radwan_salary_structure_type_id" not in vals:
            vals["radwan_salary_structure_type_id"] = vals["structure_type_id"]

        company = self.env["res.company"].browse(vals["company_id"]) if vals.get("company_id") else self.env.company
        structure = self.env["hr.payroll.structure"]
        if vals.get("struct_id"):
            structure = self.env["hr.payroll.structure"].browse(vals["struct_id"])
        elif vals.get("radwan_salary_structure_type_id"):
            structure_type = self.env["hr.payroll.structure.type"].browse(vals["radwan_salary_structure_type_id"])
            structure = self._radwan_get_structure_for_type(
                structure_type,
                company,
                create_missing=True,
            )
        elif any(field in vals for field in self._RADWAN_SALARY_AMOUNT_FIELDS):
            structure = self._radwan_default_structure(
                company,
                create_missing=True,
            )

        if structure and "struct_id" not in vals:
            vals["struct_id"] = structure.id
        if structure and structure.radwan_structure_type_id:
            vals.setdefault("structure_type_id", structure.radwan_structure_type_id.id)
            vals.setdefault("radwan_salary_structure_type_id", structure.radwan_structure_type_id.id)

        return vals

    @api.model_create_multi
    def create(self, vals_list):
        return super().create([
            self._radwan_prepare_payroll_sync_vals(vals)
            for vals in vals_list
        ])

    def write(self, vals):
        if len(self) > 1 and {"radwan_basic", "wage"} & vals.keys():
            for version in self:
                super(HrVersion, version).write(
                    version._radwan_prepare_payroll_sync_vals(vals)
                )
            return True
        return super().write(self._radwan_prepare_payroll_sync_vals(vals))

    @api.onchange("radwan_basic")
    def _onchange_radwan_basic(self):
        for version in self:
            version.wage = version.radwan_basic

    @api.onchange("wage")
    def _onchange_wage(self):
        for version in self:
            version.radwan_basic = version.wage

    @api.onchange("radwan_housing")
    def _onchange_radwan_housing(self):
        for version in self:
            version.hra = version.radwan_housing

    @api.onchange("hra")
    def _onchange_hra(self):
        for version in self:
            version.radwan_housing = version.hra

    @api.onchange("radwan_transportation")
    def _onchange_radwan_transportation(self):
        for version in self:
            version.travel_allowance = version.radwan_transportation

    @api.onchange("travel_allowance")
    def _onchange_travel_allowance(self):
        for version in self:
            version.radwan_transportation = version.travel_allowance

    @api.onchange("radwan_other_allowances")
    def _onchange_radwan_other_allowances(self):
        for version in self:
            version.other_allowance = version.radwan_other_allowances

    @api.onchange("other_allowance")
    def _onchange_other_allowance(self):
        for version in self:
            version.radwan_other_allowances = version.other_allowance

    @api.onchange("struct_id")
    def _onchange_radwan_struct_id(self):
        for version in self:
            if version.struct_id.radwan_structure_type_id:
                version.structure_type_id = version.struct_id.radwan_structure_type_id
                version.radwan_salary_structure_type_id = version.struct_id.radwan_structure_type_id

    @api.onchange("structure_type_id", "radwan_salary_structure_type_id")
    def _onchange_radwan_structure_type_id(self):
        for version in self:
            structure_type = version.structure_type_id or version.radwan_salary_structure_type_id
            if version.radwan_salary_structure_type_id != structure_type:
                version.radwan_salary_structure_type_id = structure_type
            if version.structure_type_id != structure_type:
                version.structure_type_id = structure_type
            if structure_type and not version.struct_id:
                version.struct_id = version._radwan_get_structure_for_type(
                    structure_type,
                    version.company_id,
                )

    @api.depends(
        "radwan_basic",
        "radwan_housing",
        "radwan_transportation",
        "radwan_fuel_car_allowance",
        "radwan_mobile_communications_allowance",
        "radwan_other_allowances",
    )
    def _compute_radwan_total_salary(self):
        for version in self:
            version.radwan_total_salary = sum([
                version.radwan_basic,
                version.radwan_housing,
                version.radwan_transportation,
                version.radwan_fuel_car_allowance,
                version.radwan_mobile_communications_allowance,
                version.radwan_other_allowances,
            ])

    @api.model
    def _get_whitelist_fields_from_template(self):
        return super()._get_whitelist_fields_from_template() + [
            "contract_date_start",
            "contract_date_end",
            "radwan_notice_period",
            "radwan_employer_termination_penalty",
            "radwan_employee_termination_penalty",
            "radwan_contract_other_notes",
            "employee_type",
            "radwan_non_renewal",
            "radwan_work_entry_source",
            "radwan_working_hours",
            "radwan_basic",
            "radwan_housing",
            "radwan_transportation",
            "radwan_fuel_car_allowance",
            "radwan_mobile_communications_allowance",
            "radwan_other_allowances",
            "radwan_salary_structure_type_id",
            "structure_type_id",
            "struct_id",
            "hra",
            "travel_allowance",
            "other_allowance",
            "schedule_pay",
            "type_id",
            "radwan_gosi_not_appear_in_payslip",
            "radwan_trial_start_date",
            "trial_date_end",
            "radwan_extended_trial_start_date",
            "radwan_extended_trial_end_date",
            "radwan_allow_overtime",
        ]
