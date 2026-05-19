/** @odoo-module **/

import { registry } from "@web/core/registry";
import { patch } from "@web/core/utils/patch";
import { ReportAction } from "@web/webclient/actions/reports/report_action";

const FORCE_PDF_CONTEXT_KEY = "radwan_force_pdf_download";
const FAST_DOWNLOAD_REPORTS = new Set([
    "om_hr_payroll.report_payslip",
    "om_hr_payroll.report_payslip_details",
    "om_hr_payroll.report_contribution_register",
]);

let fastDownloadIframe;

function getReportUrl(action) {
    const actionContext = action.context || {};
    const params = new URLSearchParams();
    let url = `/report/pdf/${action.report_name}`;

    if (action.data && JSON.stringify(action.data) !== "{}") {
        params.set("options", JSON.stringify(action.data));
    } else if (actionContext.active_ids?.length) {
        url += `/${actionContext.active_ids.join(",")}`;
    }
    params.set("context", JSON.stringify(actionContext));

    return `${url}?${params.toString()}`;
}

function downloadFastPdf(action) {
    if (!fastDownloadIframe) {
        fastDownloadIframe = document.createElement("iframe");
        fastDownloadIframe.name = "radwan_fast_report_download_frame";
        fastDownloadIframe.style.display = "none";
        document.body.appendChild(fastDownloadIframe);
    }

    const form = document.createElement("form");
    form.action = "/report/download";
    form.method = "POST";
    form.target = fastDownloadIframe.name;
    form.style.display = "none";

    const values = {
        data: JSON.stringify([getReportUrl(action), action.report_type]),
        context: JSON.stringify(action.context || {}),
        token: "dummy-because-api-expects-one",
    };
    if (odoo.csrf_token) {
        values.csrf_token = odoo.csrf_token;
    }

    for (const [name, value] of Object.entries(values)) {
        const input = document.createElement("input");
        input.type = "hidden";
        input.name = name;
        input.value = value;
        form.appendChild(input);
    }

    document.body.appendChild(form);
    form.submit();
    form.remove();
}

registry.category("ir.actions.report handlers").add("radwan_report_preview_first", (action) => {
    if (action.report_type !== "qweb-pdf" || action.context?.[FORCE_PDF_CONTEXT_KEY]) {
        return false;
    }

    action.report_type = "qweb-html";
    action.close_on_report_download = false;
    return false;
}, { sequence: 1 });

registry.category("ir.actions.report handlers").add("radwan_payroll_fast_pdf_download", (action) => {
    if (action.report_type !== "qweb-pdf" || !FAST_DOWNLOAD_REPORTS.has(action.report_name)) {
        return false;
    }

    downloadFastPdf(action);
    return true;
}, { sequence: 0 });

patch(ReportAction.prototype, {
    print() {
        this.action.doAction({
            type: "ir.actions.report",
            report_type: "qweb-pdf",
            report_name: this.props.report_name,
            report_file: this.props.report_file,
            data: this.props.data || {},
            default_print_option: "download",
            close_on_report_download: false,
            context: {
                ...(this.props.context || {}),
                [FORCE_PDF_CONTEXT_KEY]: true,
            },
            display_name: this.title,
        });
    },
});
