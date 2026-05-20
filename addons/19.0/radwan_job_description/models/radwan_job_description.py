from odoo import api, fields, models


class RadwanJobDescriptionSection(models.Model):
    _name = "radwan.job.description.section"
    _description = "Job Description Heading"
    _order = "sequence, id"

    name = fields.Char(required=True)
    code = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    _code_unique = models.Constraint(
        "unique(code)",
        "The heading code must be unique.",
    )


class RadwanJobDescriptionLine(models.Model):
    _name = "radwan.job.description.line"
    _description = "Job Description Line"
    _order = "job_id, sequence, id"

    sequence = fields.Integer(default=10)
    job_id = fields.Many2one(
        "hr.job",
        string="Job Position",
        required=True,
        ondelete="cascade",
        index=True,
    )
    display_type = fields.Selection([
        ("line_section", "Section"),
        ("line_note", "Note"),
    ], default=False)
    section_id = fields.Many2one(
        "radwan.job.description.section",
        string="Main Heading",
        ondelete="restrict",
    )
    name = fields.Text(string="Description", required=True)

    @api.onchange("display_type", "section_id")
    def _onchange_section_id(self):
        for line in self:
            if line.display_type == "line_section" and line.section_id:
                line.name = line.section_id.name

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("display_type") == "line_section" and vals.get("section_id") and not vals.get("name"):
                vals["name"] = self.env["radwan.job.description.section"].browse(vals["section_id"]).name
        return super().create(vals_list)

    def write(self, vals):
        if vals.get("display_type") == "line_section" and vals.get("section_id") and not vals.get("name"):
            vals = dict(vals)
            vals["name"] = self.env["radwan.job.description.section"].browse(vals["section_id"]).name
        return super().write(vals)
