/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { user } from "@web/core/user";
import { PdfOptionsModal } from "@report_pdf_options/js/PdfOptionsModal";

function getWKHTMLTOPDF_MESSAGES(status) {
    const link = '<br><br><a href="http://wkhtmltopdf.org/" target="_blank">wkhtmltopdf.org</a>';
    const messages = {
        broken:
            _t("Your installation of Wkhtmltopdf seems to be broken. The report will be shown in html.") +
            link,
        install:
            _t("Unable to find Wkhtmltopdf on this system. The report will be shown in html.") + link,
        upgrade:
            _t(
                "You should upgrade your version of Wkhtmltopdf to at least 0.12.0 in order to get a correct display of headers and footers as well as support for table-breaking between pages."
            ) + link,
        workers: _t(
            "You need to start Odoo with at least two workers to print a pdf version of the reports."
        ),
    };
    return messages[status];
}

let iframeForReport;

const STANDARD_DOWNLOAD_REPORTS = new Set([
    "om_hr_payroll.report_payslip",
    "om_hr_payroll.report_payslip_details",
    "om_hr_payroll.report_contribution_register",
]);

function printPdf(url, callback) {
    let iframe = iframeForReport;
    if (!iframe) {
        iframe = iframeForReport = document.createElement("iframe");
        iframe.className = "pdfIframe";
        iframe.style.display = "none";
        document.body.appendChild(iframe);
        iframe.onload = function () {
            setTimeout(function () {
                iframe.focus();
                iframe.contentWindow.print();
                callback();
            }, 1);
        };
    }
    iframe.src = url;
}

function getReportUrl(action, type) {
    let url = `/report/${type}/${action.report_name}`;
    const actionContext = action.context || {};
    const userContext = user.context || {};
    const context = encodeURIComponent(JSON.stringify({ ...userContext, ...actionContext }));

    if (action.data && JSON.stringify(action.data) !== "{}") {
        const options = encodeURIComponent(JSON.stringify(action.data));
        url += `?options=${options}&context=${context}`;
    } else {
        if (actionContext.active_ids) {
            url += `/${actionContext.active_ids.join(",")}`;
        }
        url += `?context=${context}`;
    }
    return url;
}

let wkhtmltopdfStateProm;

registry.category("ir.actions.report handlers").add(
    "pdf_report_options_handler",
    async function (action, options, env) {
        let { default_print_option, report_type } = action;
        if (STANDARD_DOWNLOAD_REPORTS.has(action.report_name)) {
            return false;
        }
        if (report_type !== "qweb-pdf" || default_print_option === "download") {
            return false;
        }

        if (!default_print_option) {
            let removeDialog;
            default_print_option = await new Promise((resolve) => {
                removeDialog = env.services.dialog.add(
                    PdfOptionsModal,
                    {
                        onSelectOption: (option) => resolve(option),
                    },
                    {
                        onClose: () => resolve("close"),
                    }
                );
            });
            removeDialog();
            if (default_print_option === "close") {
                return true;
            }
            if (default_print_option === "download") {
                return false;
            }
        }

        wkhtmltopdfStateProm ||= rpc("/report/check_wkhtmltopdf");
        const state = await wkhtmltopdfStateProm;
        const message = getWKHTMLTOPDF_MESSAGES(state);
        if (message) {
            env.services.notification.add(message, {
                sticky: true,
                title: _t("Report"),
            });
        }
        if (!["upgrade", "ok"].includes(state)) {
            return false;
        }

        const url = getReportUrl(action, "pdf");
        if (default_print_option === "print") {
            env.services.ui.block();
            printPdf(url, () => env.services.ui.unblock());
        }
        if (default_print_option === "open") {
            window.open(url);
        }
        return true;
    },
    { force: true }
);
