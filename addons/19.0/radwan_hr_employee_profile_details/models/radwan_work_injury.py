from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class RadwanWorkInjuryType(models.Model):
    _name = "radwan.work.injury.type"
    _description = "Work Injury Type"
    _order = "sequence, name"

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)


class RadwanWorkInjury(models.Model):
    _name = "radwan.work.injury"
    _description = "Work Injury"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "injury_date desc, id desc"

    name = fields.Char(
        string="Injury Reference",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: self.env._("New"),
        tracking=True,
    )
    employee_id = fields.Many2one(
        comodel_name="hr.employee",
        string="Employee",
        required=True,
        index=True,
        tracking=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
        tracking=True,
    )
    department_id = fields.Many2one(
        comodel_name="hr.department",
        string="Department",
        tracking=True,
    )
    job_id = fields.Many2one(
        comodel_name="hr.job",
        string="Job Position",
        tracking=True,
    )
    manager_id = fields.Many2one(
        comodel_name="hr.employee",
        string="Manager",
        tracking=True,
    )
    responsible_person_id = fields.Many2one(
        comodel_name="hr.employee",
        string="Responsible Person",
        tracking=True,
    )

    injury_date = fields.Date(
        string="Injury Date",
        required=True,
        default=fields.Date.context_today,
        tracking=True,
    )
    injury_time = fields.Float(
        string="Injury Time",
        tracking=True,
    )
    location = fields.Char(
        string="Workplace / Location",
        tracking=True,
    )
    injury_type_id = fields.Many2one(
        comodel_name="radwan.work.injury.type",
        string="Injury Type",
        tracking=True,
    )
    severity = fields.Selection(
        selection=[
            ("minor", "Minor"),
            ("moderate", "Moderate"),
            ("severe", "Severe"),
            ("critical", "Critical"),
            ("fatal", "Fatal"),
        ],
        string="Injury Severity",
        default="minor",
        required=True,
        tracking=True,
    )
    injury_description = fields.Text(string="Injury Description")
    accident_cause = fields.Text(string="Accident Cause")
    witness_ids = fields.Many2many(
        comodel_name="hr.employee",
        relation="radwan_work_injury_witness_rel",
        column1="injury_id",
        column2="employee_id",
        string="Witnesses",
    )
    witness_notes = fields.Text(string="External Witnesses / Notes")
    corrective_action = fields.Text(string="Corrective Action")
    investigation_date = fields.Date(string="Investigation Date")

    first_aid_provided = fields.Boolean(
        string="First Aid Provided",
        tracking=True,
    )
    medical_facility = fields.Char(string="Medical Facility")
    medical_report_date = fields.Date(
        string="Medical Report Date",
        tracking=True,
    )
    sick_leave_days = fields.Integer(
        string="Sick Leave Days",
        tracking=True,
    )
    work_interruption_days = fields.Integer(
        string="Work Interruption Days",
        tracking=True,
    )

    gosi_report_no = fields.Char(
        string="GOSI Report No.",
        tracking=True,
    )
    insurance_claim_no = fields.Char(
        string="Insurance Claim No.",
        tracking=True,
    )
    claim_status = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("submitted", "Submitted"),
            ("under_review", "Under Review"),
            ("approved", "Approved"),
            ("paid", "Paid"),
            ("rejected", "Rejected"),
            ("no_claim", "No Claim"),
        ],
        string="Claim Status",
        default="draft",
        required=True,
        tracking=True,
    )
    compensation_amount = fields.Monetary(
        string="Compensation Amount",
        currency_field="currency_id",
        tracking=True,
    )
    payment_date = fields.Date(string="Payment Date")
    currency_id = fields.Many2one(
        related="company_id.currency_id",
        store=True,
        readonly=True,
    )

    medical_report_attachment = fields.Binary(string="Medical Report Attachment")
    medical_report_filename = fields.Char(string="Medical Report Filename")
    accident_photos = fields.Binary(string="Accident Photos")
    accident_photos_filename = fields.Char(string="Accident Photos Filename")
    gosi_report_attachment = fields.Binary(string="GOSI Report Attachment")
    gosi_report_filename = fields.Char(string="GOSI Report Filename")
    notes = fields.Text(string="Notes")

    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("under_review", "Under Review"),
            ("reported_gosi", "Reported to GOSI"),
            ("medical_report_received", "Medical Report Received"),
            ("compensation_process", "Compensation Under Process"),
            ("closed", "Closed"),
            ("rejected", "Rejected / Not Work Related"),
        ],
        string="Status",
        default="draft",
        required=True,
        tracking=True,
    )
    active = fields.Boolean(default=True)

    @api.onchange("employee_id")
    def _onchange_employee_id(self):
        for injury in self:
            employee = injury.employee_id
            if not employee:
                continue
            injury.company_id = employee.company_id or self.env.company
            injury.department_id = employee.department_id
            injury.job_id = employee.job_id
            injury.manager_id = employee.parent_id

    @api.model_create_multi
    def create(self, vals_list):
        sequence = self.env["ir.sequence"]
        for vals in vals_list:
            if vals.get("name", self.env._("New")) == self.env._("New"):
                vals["name"] = sequence.next_by_code("radwan.work.injury") or self.env._("New")
            employee = self.env["hr.employee"].browse(vals.get("employee_id"))
            if employee:
                vals.setdefault("company_id", employee.company_id.id or self.env.company.id)
                vals.setdefault("department_id", employee.department_id.id)
                vals.setdefault("job_id", employee.job_id.id)
                vals.setdefault("manager_id", employee.parent_id.id)
        return super().create(vals_list)

    def write(self, vals):
        if "employee_id" in vals:
            employee = self.env["hr.employee"].browse(vals["employee_id"])
            if employee:
                vals = dict(
                    vals,
                    company_id=employee.company_id.id or self.env.company.id,
                    department_id=employee.department_id.id,
                    job_id=employee.job_id.id,
                    manager_id=employee.parent_id.id,
                )
        return super().write(vals)

    @api.constrains("sick_leave_days", "work_interruption_days", "compensation_amount")
    def _check_positive_amounts(self):
        for injury in self:
            if injury.sick_leave_days < 0:
                raise ValidationError(self.env._("Sick Leave Days cannot be negative."))
            if injury.work_interruption_days < 0:
                raise ValidationError(self.env._("Work Interruption Days cannot be negative."))
            if injury.compensation_amount < 0:
                raise ValidationError(self.env._("Compensation Amount cannot be negative."))

    def action_submit_review(self):
        for injury in self:
            injury.state = "under_review"
            injury._schedule_followup_activity(
                self.env._("Review work injury case"),
                injury.injury_date or fields.Date.context_today(injury),
            )

    def action_report_gosi(self):
        for injury in self:
            injury.state = "reported_gosi"
            if injury.claim_status == "draft":
                injury.claim_status = "submitted"

    def action_receive_medical_report(self):
        for injury in self:
            injury.state = "medical_report_received"
            if not injury.medical_report_date:
                injury.medical_report_date = fields.Date.context_today(injury)

    def action_start_compensation(self):
        for injury in self:
            injury.state = "compensation_process"
            if injury.claim_status in ("draft", "submitted"):
                injury.claim_status = "under_review"

    def action_close(self):
        for injury in self:
            injury.state = "closed"
            injury.activity_unlink(["mail.mail_activity_data_todo"])

    def action_reject(self):
        for injury in self:
            injury.state = "rejected"
            injury.claim_status = "no_claim"
            injury.activity_unlink(["mail.mail_activity_data_todo"])

    def _get_followup_users(self):
        self.ensure_one()
        users = self.env["res.users"]
        if self.manager_id.user_id:
            users |= self.manager_id.user_id
        if self.responsible_person_id.user_id:
            users |= self.responsible_person_id.user_id
        hr_manager_group = self.env.ref("hr.group_hr_manager", raise_if_not_found=False)
        if hr_manager_group:
            users |= hr_manager_group.users
        return users.filtered(lambda user: user.active)

    def _schedule_followup_activity(self, summary, date_deadline):
        activity_type = self.env.ref("mail.mail_activity_data_todo", raise_if_not_found=False)
        if not activity_type:
            return
        Activity = self.env["mail.activity"]
        for injury in self:
            for user in injury._get_followup_users():
                domain = [
                    ("res_model", "=", injury._name),
                    ("res_id", "=", injury.id),
                    ("activity_type_id", "=", activity_type.id),
                    ("user_id", "=", user.id),
                    ("summary", "=", summary),
                ]
                if not Activity.search_count(domain):
                    injury.activity_schedule(
                        "mail.mail_activity_data_todo",
                        user_id=user.id,
                        summary=summary,
                        date_deadline=date_deadline,
                    )

    @api.model
    def _cron_schedule_followup_activities(self):
        today = fields.Date.context_today(self)
        open_injuries = self.search([("state", "not in", ["closed", "rejected"])])
        for injury in open_injuries:
            injury._schedule_periodic_followups(today)

    def _schedule_periodic_followups(self, today):
        self.ensure_one()
        if self.injury_date and self.injury_date <= today - timedelta(days=7):
            self._schedule_followup_activity(
                self.env._("Work injury case is still open"),
                today,
            )
        if self.injury_date and not self.medical_report_date and self.injury_date <= today - timedelta(days=2):
            self._schedule_followup_activity(
                self.env._("Medical report is still missing"),
                today,
            )
        if self.injury_date and self.sick_leave_days:
            sick_leave_end = self.injury_date + timedelta(days=self.sick_leave_days - 1)
            if today <= sick_leave_end <= today + timedelta(days=1):
                self._schedule_followup_activity(
                    self.env._("Sick leave is ending soon"),
                    sick_leave_end,
                )
        if (
            self.state == "compensation_process"
            and self.claim_status in ("draft", "submitted", "under_review")
            and self.injury_date
            and self.injury_date <= today - timedelta(days=14)
        ):
            self._schedule_followup_activity(
                self.env._("Insurance claim follow-up is overdue"),
                today,
            )
