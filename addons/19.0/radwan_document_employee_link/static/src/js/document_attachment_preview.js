/** @odoo-module **/

function isPreviewableAttachment(url) {
    return Boolean(url) && (url.includes("/web/content") || url.includes("/web/image"));
}

function getPreviewUrl(href) {
    const previewUrl = new URL(href, window.location.origin);
    previewUrl.searchParams.delete("download");
    return previewUrl.toString();
}

document.addEventListener(
    "click",
    (event) => {
        if (!(event.target instanceof Element)) {
            return;
        }
        const link = event.target.closest(".o_form_document .o_field_html a[href]");
        if (!link || !isPreviewableAttachment(link.getAttribute("href"))) {
            return;
        }
        event.preventDefault();
        window.open(getPreviewUrl(link.getAttribute("href")), "_blank", "noopener");
    },
    true
);
