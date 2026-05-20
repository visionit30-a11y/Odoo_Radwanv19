from odoo import Command, fields, models


class HrJob(models.Model):
    _inherit = "hr.job"

    radwan_job_description_line_ids = fields.One2many(
        "radwan.job.description.line",
        "job_id",
        string="Structured Job Description",
        copy=True,
    )

    def action_radwan_load_job_description_sections(self):
        Section = self.env["radwan.job.description.section"]
        sections = Section.search([("active", "=", True)], order="sequence, id")
        for job in self:
            existing_sections = job.radwan_job_description_line_ids.filtered(
                lambda line: line.display_type == "line_section"
            ).section_id
            sequence = max(job.radwan_job_description_line_ids.mapped("sequence") or [0])
            commands = []
            for section in sections - existing_sections:
                sequence += 10
                commands.append(Command.create({
                    "display_type": "line_section",
                    "section_id": section.id,
                    "name": section.name,
                    "sequence": sequence,
                }))
            if commands:
                job.write({"radwan_job_description_line_ids": commands})
        return True
