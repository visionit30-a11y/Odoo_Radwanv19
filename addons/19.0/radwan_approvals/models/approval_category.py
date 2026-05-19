from odoo import _, api, fields, models


APPROVAL_FIELD_MODES = [
    ("none", "None"),
    ("optional", "Optional"),
    ("required", "Required"),
]


class RadwanApprovalCategory(models.Model):
    _name = "radwan.approval.category"
    _description = "Approval Type"
    _order = "sequence, name"

    name = fields.Char(required=True, translate=True)
    description = fields.Text(translate=True)
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    color = fields.Integer()
    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
        index=True,
    )
    image_1920 = fields.Image(max_width=1920, max_height=1920)
    image_128 = fields.Image(
        string="Image 128",
        related="image_1920",
        max_width=128,
        max_height=128,
        store=True,
    )

    automated_sequence = fields.Boolean(string="Automated Sequence")
    document_mode = fields.Selection(
        APPROVAL_FIELD_MODES,
        string="Document",
        default="optional",
        required=True,
    )
    contact_mode = fields.Selection(
        APPROVAL_FIELD_MODES,
        string="Contact",
        default="none",
        required=True,
    )
    date_mode = fields.Selection(
        APPROVAL_FIELD_MODES,
        string="Date",
        default="none",
        required=True,
    )
    period_mode = fields.Selection(
        APPROVAL_FIELD_MODES,
        string="Period",
        default="none",
        required=True,
    )
    product_mode = fields.Selection(
        APPROVAL_FIELD_MODES,
        string="Product",
        default="none",
        required=True,
    )
    quantity_mode = fields.Selection(
        APPROVAL_FIELD_MODES,
        string="Quantity",
        default="none",
        required=True,
    )
    amount_mode = fields.Selection(
        APPROVAL_FIELD_MODES,
        string="Amount",
        default="none",
        required=True,
    )
    reference_mode = fields.Selection(
        APPROVAL_FIELD_MODES,
        string="Reference",
        default="none",
        required=True,
    )
    location_mode = fields.Selection(
        APPROVAL_FIELD_MODES,
        string="Location",
        default="none",
        required=True,
    )

    has_amount = fields.Boolean(string="Show Amount", compute="_compute_visible_fields")
    has_reference = fields.Boolean(string="Show Reference", compute="_compute_visible_fields")
    has_date = fields.Boolean(string="Show Date", compute="_compute_visible_fields")
    has_location = fields.Boolean(string="Show Location", compute="_compute_visible_fields")
    has_contact = fields.Boolean(string="Show Contact", compute="_compute_visible_fields")
    has_product = fields.Boolean(string="Show Products", compute="_compute_visible_fields")
    has_period = fields.Boolean(string="Show Period", compute="_compute_visible_fields")
    has_document = fields.Boolean(string="Show Document", compute="_compute_visible_fields")

    manager_approval = fields.Boolean(string="Employee's Manager Is Approver")
    approver_sequence = fields.Boolean(string="Approvers Sequence")
    minimum_approval = fields.Integer(default=1)
    _minimum_approval_positive = models.Constraint(
        "CHECK (minimum_approval >= 1)",
        "Minimum Approval must be greater than or equal to 1.",
    )

    approver_ids = fields.One2many(
        "radwan.approval.category.approver",
        "category_id",
        string="Approvers",
        copy=True,
    )
    request_count = fields.Integer(compute="_compute_request_counts")
    to_review_count = fields.Integer(compute="_compute_request_counts")

    def _compute_visible_fields(self):
        for category in self:
            category.has_amount = category.amount_mode != "none"
            category.has_reference = category.reference_mode != "none"
            category.has_date = category.date_mode != "none"
            category.has_location = category.location_mode != "none"
            category.has_contact = category.contact_mode != "none"
            category.has_product = category.product_mode != "none"
            category.has_period = category.period_mode != "none"
            category.has_document = category.document_mode != "none"

    def _compute_request_counts(self):
        Request = self.env["radwan.approval.request"]
        Approver = self.env["radwan.approver"]
        for category in self:
            category.request_count = Request.search_count([
                ("category_id", "=", category.id),
            ])
            category.to_review_count = Approver.search_count([
                ("request_id.category_id", "=", category.id),
                ("request_id.state", "=", "pending"),
                ("user_id", "=", self.env.user.id),
                ("status", "=", "new"),
            ])

    def action_new_request(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("New Approval Request"),
            "res_model": "radwan.approval.request",
            "view_mode": "form",
            "target": "current",
            "context": {
                "default_category_id": self.id,
                "default_request_owner_id": self.env.user.id,
            },
        }

    def action_open_to_review(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Approvals to Review"),
            "res_model": "radwan.approval.request",
            "view_mode": "list,form,kanban",
            "domain": [
                ("category_id", "=", self.id),
                ("state", "=", "pending"),
                ("approver_ids.user_id", "=", self.env.user.id),
                ("approver_ids.status", "=", "new"),
            ],
            "context": {"search_default_to_review": 1},
        }

    def _get_default_category_values(self):
        return (
            {
                "name": "Business Trip",
                "sequence": 10,
                "description": "Approve business travel and related arrangements.",
                "document_mode": "optional",
                "period_mode": "required",
                "location_mode": "required",
                "manager_approval": True,
                "minimum_approval": 1,
            },
            {
                "name": "Borrow Items",
                "sequence": 20,
                "description": "Approve borrowing company assets or equipment.",
                "document_mode": "optional",
                "date_mode": "optional",
                "product_mode": "required",
                "quantity_mode": "required",
                "manager_approval": True,
                "minimum_approval": 1,
            },
            {
                "name": "General Approval",
                "sequence": 30,
                "description": "Use this type for general internal approvals.",
                "document_mode": "optional",
                "date_mode": "optional",
                "reference_mode": "optional",
                "minimum_approval": 1,
            },
            {
                "name": "Overtime",
                "sequence": 35,
                "description": "Approve overtime work requests.",
                "date_mode": "required",
                "amount_mode": "optional",
                "manager_approval": True,
                "minimum_approval": 1,
            },
            {
                "name": "Contract Approval",
                "sequence": 40,
                "description": "Approve contracts before signature or execution.",
                "document_mode": "required",
                "reference_mode": "required",
                "manager_approval": True,
                "minimum_approval": 1,
            },
            {
                "name": "Payment Application",
                "sequence": 50,
                "description": "Approve payment requests and supplier disbursements.",
                "document_mode": "optional",
                "amount_mode": "required",
                "reference_mode": "required",
                "minimum_approval": 1,
            },
            {
                "name": "Car Rental Application",
                "sequence": 60,
                "description": "Approve temporary car rental requests.",
                "document_mode": "optional",
                "period_mode": "required",
                "location_mode": "required",
                "amount_mode": "optional",
                "manager_approval": True,
                "minimum_approval": 1,
            },
            {
                "name": "Job Referral Award",
                "sequence": 70,
                "description": "Approve employee referral rewards.",
                "document_mode": "optional",
                "contact_mode": "required",
                "amount_mode": "optional",
                "manager_approval": True,
                "minimum_approval": 1,
            },
            {
                "name": "Procurement",
                "sequence": 80,
                "description": "Approve purchase or material requests.",
                "document_mode": "optional",
                "product_mode": "required",
                "quantity_mode": "required",
                "amount_mode": "optional",
                "reference_mode": "optional",
                "minimum_approval": 1,
            },
        )

    @api.model
    def action_sync_default_categories(self):
        base_values = {
            "document_mode": "none",
            "contact_mode": "none",
            "date_mode": "none",
            "period_mode": "none",
            "product_mode": "none",
            "quantity_mode": "none",
            "amount_mode": "none",
            "reference_mode": "none",
            "location_mode": "none",
            "manager_approval": False,
            "approver_sequence": False,
            "minimum_approval": 1,
        }
        for values in self._get_default_category_values():
            values = dict(base_values, **values)
            category = self.search([("name", "=", values["name"])], limit=1)
            if category:
                category.write(values)
            else:
                self.create(values)


class RadwanApprovalCategoryApprover(models.Model):
    _name = "radwan.approval.category.approver"
    _description = "Approval Type Approver"
    _order = "sequence, id"

    sequence = fields.Integer(default=10)
    category_id = fields.Many2one(
        "radwan.approval.category",
        required=True,
        ondelete="cascade",
    )
    user_id = fields.Many2one(
        "res.users",
        required=True,
        string="Approver",
        domain="[('share', '=', False)]",
    )
    required = fields.Boolean(default=True)
    company_id = fields.Many2one(related="category_id.company_id", store=True)

    _category_user_unique = models.Constraint(
        "UNIQUE (category_id, user_id)",
        "Each approver can be configured once per approval type.",
    )
