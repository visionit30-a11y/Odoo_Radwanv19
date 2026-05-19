import logging

from odoo import api, models
from odoo.addons.base.models import ir_actions_report as base_ir_actions_report
from odoo.http import request

_logger = logging.getLogger(__name__)


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    @api.model
    def _run_wkhtmltopdf(self, *args, **kwargs):
        params = self.env["ir.config_parameter"].sudo()
        if params.get_param("radwan_report_speed_fix.skip_cookie_jar", "1") != "1":
            return super()._run_wkhtmltopdf(*args, **kwargs)

        original_request = base_ir_actions_report.request
        base_ir_actions_report.request = None
        try:
            return super()._run_wkhtmltopdf(*args, **kwargs)
        finally:
            base_ir_actions_report.request = original_request

    @api.model
    def _build_wkhtmltopdf_args(
        self,
        paperformat_id,
        landscape,
        specific_paperformat_args=None,
        set_viewport_size=False,
    ):
        args = super()._build_wkhtmltopdf_args(
            paperformat_id,
            landscape,
            specific_paperformat_args=specific_paperformat_args,
            set_viewport_size=set_viewport_size,
        )

        params = self.env["ir.config_parameter"].sudo()
        if params.get_param("radwan_report_speed_fix.disable_javascript", "1") == "1":
            if "--disable-javascript" not in args:
                args.append("--disable-javascript")
            if "--enable-javascript" in args:
                idx = args.index("--enable-javascript")
                del args[idx]

        if params.get_param("radwan_report_speed_fix.ignore_load_errors", "1") == "1":
            args.extend(["--load-error-handling", "ignore"])
            args.extend(["--load-media-error-handling", "ignore"])

        if params.get_param("radwan_report_speed_fix.no_proxy", "1") == "1":
            args.extend(["--proxy", "None"])

        delay = params.get_param("radwan_report_speed_fix.javascript_delay")
        if delay:
            try:
                idx = args.index("--javascript-delay")
            except ValueError:
                args.extend(["--javascript-delay", delay])
            else:
                args[idx + 1] = delay

        _logger.debug("Radwan report speed fix wkhtmltopdf args: %s", " ".join(args))
        return args


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    @classmethod
    def _post_dispatch(cls, response):
        super()._post_dispatch(response)
        try:
            user_agent = request.httprequest.headers.get("User-Agent", "").lower()
        except RuntimeError:
            return

        if "wkhtmltopdf" in user_agent or "wkhtmltoimage" in user_agent:
            response.headers["Connection"] = "close"
            response.headers["Keep-Alive"] = "timeout=0, max=0"
