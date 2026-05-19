# Part of Radwan customizations. See LICENSE file for full copyright and licensing details.

import json

import werkzeug.exceptions

from odoo import http
from odoo.http import content_disposition, request
from odoo.tools.safe_eval import safe_eval, time


PAYROLL_REPORT_NAMES = {
    "om_hr_payroll.report_contribution_register",
    "om_hr_payroll.report_payslip",
    "om_hr_payroll.report_payslip_details",
}


class RadwanReportDownloadController(http.Controller):

    @http.route([
        "/radwan_report_speed_fix/report/pdf/<reportname>",
        "/radwan_report_speed_fix/report/pdf/<reportname>/<docids>",
    ], type="http", auth="user", readonly=True)
    def payroll_pdf_download(self, reportname, docids=None, **data):
        if reportname not in PAYROLL_REPORT_NAMES:
            raise werkzeug.exceptions.NotFound()

        context = dict(request.env.context)
        if data.get("context"):
            context.update(json.loads(data.pop("context")))
        if data.get("options"):
            data.update(json.loads(data.pop("options")))

        res_ids = None
        if docids:
            res_ids = [int(docid) for docid in docids.split(",") if docid.isdigit()]

        report_model = request.env["ir.actions.report"]
        pdf = report_model.with_context(context)._render_qweb_pdf(
            reportname,
            res_ids=res_ids,
            data=data,
        )[0]
        report = report_model._get_report_from_name(reportname)
        filename = "%s.pdf" % report.name

        if res_ids:
            records = request.env[report.model].browse(res_ids)
            if report.print_report_name and len(records) == 1:
                filename = "%s.pdf" % safe_eval(
                    report.print_report_name,
                    {"object": records, "time": time},
                )

        return request.make_response(pdf, headers=[
            ("Content-Type", "application/pdf"),
            ("Content-Length", len(pdf)),
            ("Content-Disposition", content_disposition(filename)),
            ("Cache-Control", "no-store"),
        ])
