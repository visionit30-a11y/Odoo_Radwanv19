from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError


class RadwanApprovalRequest(models.Model):
    _name = "radwan.approval.request"
    _description = "Approval Request"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc, id desc"

    name = fields.Char(
        string="Approval Subject",
        required=True,
        copy=False,
        default=lambda self: _("New"),
        tracking=True,
    )
    request_owner_id = fields.Many2one(
        "res.users",
        string="Request Owner",
        default=lambda self: self.env.user,
        required=True,
        tracking=True,
    )
    category_id = fields.Many2one(
        "radwan.approval.category",
        string="Category",
        required=True,
        tracking=True,
    )
    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
        required=True,
        index=True,
    )
    date = fields.Datetime(default=fields.Datetime.now, tracking=True)
    period_start = fields.Date(string="Period Start")
    period_end = fields.Date(string="Period End")
    location = fields.Char()
    contact_id = fields.Many2one("res.partner", string="Contact")
    amount = fields.Monetary(currency_field="currency_id", tracking=True)
    currency_id = fields.Many2one(
        "res.currency",
        default=lambda self: self.env.company.currency_id,
        required=True,
    )
    reference = fields.Char()
    description = fields.Html()
    state = fields.Selection(
        [
            ("new", "To Submit"),
            ("pending", "Submitted"),
            ("approved", "Approved"),
            ("refused", "Refused"),
            ("cancel", "Cancel"),
        ],
        default="new",
        required=True,
        copy=False,
        tracking=True,
    )

    approver_ids = fields.One2many(
        "radwan.approver",
        "request_id",
        string="Approver(s)",
        copy=True,
    )
    product_line_ids = fields.One2many(
        "radwan.approval.product.line",
        "request_id",
        string="Products",
        copy=True,
    )

    category_image_128 = fields.Image(related="category_id.image_128")
    has_amount = fields.Boolean(related="category_id.has_amount")
    has_reference = fields.Boolean(related="category_id.has_reference")
    has_date = fields.Boolean(related="category_id.has_date")
    has_location = fields.Boolean(related="category_id.has_location")
    has_contact = fields.Boolean(related="category_id.has_contact")
    has_product = fields.Boolean(related="category_id.has_product")
    has_period = fields.Boolean(related="category_id.has_period")
    has_document = fields.Boolean(related="category_id.has_document")
    amount_mode = fields.Selection(
        string="Amount Requirement",
        related="category_id.amount_mode",
    )
    reference_mode = fields.Selection(
        string="Reference Requirement",
        related="category_id.reference_mode",
    )
    date_mode = fields.Selection(
        string="Date Requirement",
        related="category_id.date_mode",
    )
    location_mode = fields.Selection(
        string="Location Requirement",
        related="category_id.location_mode",
    )
    contact_mode = fields.Selection(
        string="Contact Requirement",
        related="category_id.contact_mode",
    )
    product_mode = fields.Selection(
        string="Product Requirement",
        related="category_id.product_mode",
    )
    quantity_mode = fields.Selection(
        string="Quantity Requirement",
        related="category_id.quantity_mode",
    )
    period_mode = fields.Selection(
        string="Period Requirement",
        related="category_id.period_mode",
    )
    document_mode = fields.Selection(
        string="Document Requirement",
        related="category_id.document_mode",
    )
    automated_sequence = fields.Boolean(related="category_id.automated_sequence")
    manager_approval = fields.Boolean(related="category_id.manager_approval")
    approver_sequence = fields.Boolean(related="category_id.approver_sequence")
    minimum_approval = fields.Integer(related="category_id.minimum_approval")

    attachment_count = fields.Integer(
        string="Documents Count",
        compute="_compute_attachment_count",
    )
    can_approve = fields.Boolean(compute="_compute_can_approve")

    @api.depends("approver_ids.user_id", "approver_ids.status", "state")
    def _compute_can_approve(self):
        is_manager = self.env.user.has_group(
            "radwan_approvals.radwan_approvals_group_manager"
        )
        for request in self:
            approval_lines = request.approver_ids.filtered(lambda line: line.status == "new")
            if request.approver_sequence and approval_lines:
                approval_lines = approval_lines.sorted(lambda line: (line.sequence, line.id))[:1]
            request.can_approve = (
                request.state == "pending"
                and (
                    is_manager
                    or any(
                        line.user_id == self.env.user and line.status == "new"
                        for line in approval_lines
                    )
                )
            )

    def _compute_attachment_count(self):
        Attachment = self.env["ir.attachment"].sudo()
        for request in self:
            request.attachment_count = Attachment.search_count([
                ("res_model", "=", request._name),
                ("res_id", "=", request.id),
            ])

    @api.onchange("category_id")
    def _onchange_category_id(self):
        for request in self:
            if request.state == "new":
                request.approver_ids = request._category_approver_commands()

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        category_id = values.get("category_id") or self.env.context.get("default_category_id")
        if category_id and "approver_ids" in fields_list:
            category = self.env["radwan.approval.category"].browse(category_id)
            values["approver_ids"] = [
                Command.create({
                    "user_id": approver.user_id.id,
                    "sequence": approver.sequence,
                    "required": approver.required,
                })
                for approver in category.approver_ids
            ]
        return values

    def _category_approver_commands(self):
        self.ensure_one()
        commands = [Command.clear()]
        for approver in self.category_id.approver_ids:
            commands.append(Command.create({
                "user_id": approver.user_id.id,
                "sequence": approver.sequence,
                "required": approver.required,
            }))
        return commands

    @api.model_create_multi
    def create(self, vals_list):
        sequence = self.env["ir.sequence"]
        for vals in vals_list:
            category = self.env["radwan.approval.category"].browse(
                vals.get("category_id") or self.env.context.get("default_category_id")
            )
            if vals.get("name", _("New")) == _("New"):
                if category and category.automated_sequence:
                    vals["name"] = sequence.next_by_code("radwan.approval.request") or _("New")
                elif category:
                    vals["name"] = category.name
        requests = super().create(vals_list)
        for request in requests.filtered(lambda rec: rec.category_id and not rec.approver_ids):
            request.approver_ids = request._category_approver_commands()
        return requests

    def write(self, vals):
        result = super().write(vals)
        if "category_id" in vals:
            for request in self.filtered(lambda rec: rec.state == "new"):
                request.approver_ids = request._category_approver_commands()
        return result

    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {})
        default.update({
            "name": _("New"),
            "state": "new",
        })
        return super().copy(default)

    def action_submit(self):
        for request in self:
            request._refresh_manager_approver()
            request._check_required_values()
            if not request.approver_ids:
                raise UserError(_("Please configure at least one approver."))
            request.approver_ids.write({"status": "new", "date": False})
            request.state = "pending"
            request._clear_approval_activities()
            request._schedule_approval_activities()
            request.message_post(body=_("Approval request submitted."))

    def action_approve(self):
        for request in self:
            if request.state != "pending":
                continue
            lines = request._get_current_user_approval_lines()
            if not lines and not self.env.user.has_group(
                "radwan_approvals.radwan_approvals_group_manager"
            ):
                raise UserError(_("Only assigned approvers can approve this request."))
            (lines or request.approver_ids.filtered(lambda line: line.status == "new")[:1]).write({
                "status": "approved",
                "date": fields.Datetime.now(),
            })
            if request.approver_sequence:
                request._clear_approval_activities()
            else:
                request.activity_feedback(
                    ["mail.mail_activity_data_todo"],
                    user_id=self.env.user.id,
                    feedback=_("Approved"),
                )
            if request._is_approval_complete():
                request.state = "approved"
                request._clear_approval_activities()
                request.message_post(body=_("Approval request approved."))
            elif request.approver_sequence:
                request._schedule_approval_activities()

    def action_refuse(self):
        for request in self:
            if request.state != "pending":
                continue
            lines = request._get_current_user_approval_lines()
            if not lines and not self.env.user.has_group(
                "radwan_approvals.radwan_approvals_group_manager"
            ):
                raise UserError(_("Only assigned approvers can refuse this request."))
            (lines or request.approver_ids.filtered(lambda line: line.status == "new")[:1]).write({
                "status": "refused",
                "date": fields.Datetime.now(),
            })
            request.state = "refused"
            request._clear_approval_activities()
            request.message_post(body=_("Approval request refused."))

    def action_cancel(self):
        self.write({"state": "cancel"})
        self._clear_approval_activities()

    def action_reset_to_draft(self):
        self.write({"state": "new"})
        self.approver_ids.write({"status": "new", "date": False})
        self._clear_approval_activities()

    def action_open_attachments(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Documents"),
            "res_model": "ir.attachment",
            "view_mode": "list,form",
            "domain": [("res_model", "=", self._name), ("res_id", "=", self.id)],
            "context": {
                "default_res_model": self._name,
                "default_res_id": self.id,
            },
        }

    def action_attach_document(self):
        return self.action_open_attachments()

    def _get_current_user_approval_lines(self):
        self.ensure_one()
        lines = self.approver_ids.filtered(
            lambda line: line.user_id == self.env.user and line.status == "new"
        )
        if self.approver_sequence and lines:
            first_line = self.approver_ids.filtered(
                lambda line: line.status == "new"
            ).sorted(lambda line: (line.sequence, line.id))[:1]
            return lines & first_line
        return lines

    def _schedule_approval_activities(self):
        for request in self:
            approvers = request.approver_ids.filtered(lambda line: line.status == "new")
            if request.approver_sequence and approvers:
                approvers = approvers.sorted(lambda line: (line.sequence, line.id))[:1]
            for approver in approvers:
                request.activity_schedule(
                    "mail.mail_activity_data_todo",
                    date_deadline=fields.Date.context_today(request),
                    summary=_("Approval required"),
                    note=_("Please review approval request %s.", request.display_name),
                    user_id=approver.user_id.id,
                )

    def _clear_approval_activities(self):
        for request in self:
            request.activity_unlink(["mail.mail_activity_data_todo"])

    def _refresh_manager_approver(self):
        for request in self:
            if not request.manager_approval:
                continue
            employee = self.env["hr.employee"].search([
                ("user_id", "=", request.request_owner_id.id),
                "|",
                ("company_id", "=", request.company_id.id),
                ("company_id", "=", False),
            ], limit=1)
            manager_user = employee.parent_id.user_id
            if manager_user and manager_user not in request.approver_ids.mapped("user_id"):
                request.approver_ids = [
                    Command.create({
                        "sequence": 0,
                        "user_id": manager_user.id,
                        "required": True,
                    })
                ]

    def _check_required_values(self):
        for request in self:
            missing = []
            if request.document_mode == "required" and not request.attachment_count:
                missing.append(_("Document"))
            if request.contact_mode == "required" and not request.contact_id:
                missing.append(_("Contact"))
            if request.date_mode == "required" and not request.date:
                missing.append(_("Date"))
            if request.period_mode == "required" and (
                not request.period_start or not request.period_end
            ):
                missing.append(_("Period"))
            if request.product_mode == "required" and not request.product_line_ids:
                missing.append(_("Product"))
            if request.quantity_mode == "required" and any(
                line.quantity <= 0 for line in request.product_line_ids
            ):
                missing.append(_("Quantity"))
            if request.amount_mode == "required" and not request.amount:
                missing.append(_("Amount"))
            if request.reference_mode == "required" and not request.reference:
                missing.append(_("Reference"))
            if request.location_mode == "required" and not request.location:
                missing.append(_("Location"))
            if missing:
                raise UserError(
                    _("Please fill the required approval fields: %s", ", ".join(missing))
                )

    def _is_approval_complete(self):
        self.ensure_one()
        minimum_approval = max(self.minimum_approval or 1, 1)
        approved_lines = self.approver_ids.filtered(lambda line: line.status == "approved")
        required_lines = self.approver_ids.filtered("required")
        if required_lines and required_lines.filtered(lambda line: line.status != "approved"):
            return False
        return len(approved_lines) >= minimum_approval
