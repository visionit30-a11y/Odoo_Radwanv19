/** @odoo-module **/

const DIALOG_CLASS = "o_radwan_skill_select_dialog";
const SELECTED_CLASS = "o_radwan_skill_option_selected";

function cleanText(element) {
    return (element?.textContent || "").replace(/\s+/g, " ").trim();
}

function isSkillDialog(dialog) {
    const title = cleanText(
        dialog.querySelector(".modal-title, .o_dialog_title, header h4")
    );
    if (title.includes("Select Skills")) {
        return true;
    }

    const bodyText = cleanText(dialog.querySelector(".modal-body, .o_content"));
    return (
        bodyText.includes("Category") &&
        bodyText.includes("Skill") &&
        bodyText.includes("Skill Level")
    );
}

function findButtonGroup(button) {
    const explicitGroup = button.closest(".o_field_widget, .btn-group");
    if (explicitGroup) {
        return explicitGroup;
    }

    let group = button.parentElement;
    while (group?.parentElement && group.parentElement.querySelectorAll(".btn").length) {
        const groupButtonCount = group.querySelectorAll(".btn").length;
        const parentButtonCount = group.parentElement.querySelectorAll(".btn").length;
        if (groupButtonCount > 1 || parentButtonCount > 12) {
            break;
        }
        group = group.parentElement;
    }
    return group || button.parentElement;
}

function markButton(button) {
    const group = findButtonGroup(button);
    if (!group) {
        return;
    }

    for (const option of group.querySelectorAll(`.${SELECTED_CLASS}`)) {
        option.classList.remove(SELECTED_CLASS);
    }
    button.classList.add(SELECTED_CLASS);
}

function decorateDialogs(root = document) {
    for (const dialog of root.querySelectorAll?.(".modal, .o_dialog") || []) {
        if (isSkillDialog(dialog)) {
            dialog.classList.add(DIALOG_CLASS);
        }
    }
}

function onDocumentClick(ev) {
    const button = ev.target.closest(".modal .modal-body .btn, .o_dialog .btn");
    if (!button || button.closest(".modal-footer")) {
        return;
    }

    const dialog = button.closest(".modal, .o_dialog");
    if (!dialog || !isSkillDialog(dialog)) {
        return;
    }

    dialog.classList.add(DIALOG_CLASS);
    const label = cleanText(button);
    markButton(button);

    requestAnimationFrame(() => {
        decorateDialogs(document);
        const currentDialog = dialog.isConnected
            ? dialog
            : document.querySelector(`.${DIALOG_CLASS}`);
        const currentButton = [...(currentDialog?.querySelectorAll(".modal-body .btn") || [])]
            .find((candidate) => cleanText(candidate) === label);
        if (currentButton) {
            markButton(currentButton);
        }
    });
}

function start() {
    document.addEventListener("click", onDocumentClick, true);
    decorateDialogs(document);

    const observer = new MutationObserver((mutations) => {
        for (const mutation of mutations) {
            for (const node of mutation.addedNodes) {
                if (node.nodeType === Node.ELEMENT_NODE) {
                    decorateDialogs(node);
                }
            }
        }
    });
    observer.observe(document.body, { childList: true, subtree: true });
}

if (document.body) {
    start();
} else {
    document.addEventListener("DOMContentLoaded", start, { once: true });
}
