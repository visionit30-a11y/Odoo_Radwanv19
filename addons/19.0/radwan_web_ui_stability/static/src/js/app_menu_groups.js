/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { NavBar } from "@web/webclient/navbar/navbar";

const RADWAN_DEFAULT_OPEN_APP_GROUPS = new Set(["finance", "human_resources"]);

const RADWAN_APP_DISPLAY_NAMES = {
    documents: "\u0627\u0644\u0645\u0633\u062a\u0646\u062f\u0627\u062a",
    knowledge: "\u0627\u0644\u0645\u0639\u0631\u0641\u0629",
    "radwan helpdesk": "\u0645\u0631\u0643\u0632 \u0627\u0644\u0645\u0633\u0627\u0639\u062f\u0629",
    helpdesk: "\u0645\u0631\u0643\u0632 \u0627\u0644\u0645\u0633\u0627\u0639\u062f\u0629",
    "link tracker": "\u0645\u062a\u062a\u0628\u0639 \u0627\u0644\u0631\u0648\u0627\u0628\u0637",
    "performance appraisals": "\u062a\u0642\u064a\u064a\u0645\u0627\u062a \u0627\u0644\u0623\u062f\u0627\u0621",
    orientations: "\u0627\u0644\u062a\u0648\u062c\u064a\u0647",
    "training program": "\u0628\u0631\u0646\u0627\u0645\u062c \u0627\u0644\u062a\u062f\u0631\u064a\u0628",
    loans: "\u0627\u0644\u0633\u0644\u0641",
};

const RADWAN_APP_GROUPS = [
    {
        key: "productivity",
        name: _t("Productivity & Communication"),
        names: ["Discuss", "Calendar", "To-do", "To Do", "Knowledge", "Documents", "Contacts"],
        fragments: ["mail", "calendar", "project_todo", "knowledge", "documents", "contacts"],
    },
    {
        key: "sales_service",
        name: _t("Sales & Customer Service"),
        names: ["CRM", "Sales", "Radwan Helpdesk", "Helpdesk", "Link Tracker"],
        fragments: ["crm", "sale", "support_helpdesk_ticket", "helpdesk", "link_tracker"],
    },
    {
        key: "finance",
        name: _t("Finance & Accounting"),
        names: ["Accounting", "Expenses"],
        fragments: ["account", "account_accountant", "expense"],
    },
    {
        key: "projects",
        name: _t("Projects & Services"),
        names: ["Project", "Timesheets", "Planning"],
        fragments: ["project", "timesheet", "planning"],
    },
    {
        key: "development",
        name: _t("Development"),
        names: [
            "Orientations",
            "Orintations",
            "Training Program",
            "Performance Appraisals",
            "Performane Appraisals",
        ],
        fragments: [
            "employee_orientation",
            "orientation",
            "training",
            "mj_appraisal",
            "appraisal",
            "performance_appraisal",
        ],
    },
    {
        key: "human_resources",
        name: _t("Human Resources"),
        names: ["Employees", "Payroll", "Attendances", "Recruitment", "Time Off", "Fleet"],
        fragments: ["hr", "payroll", "attendance", "recruitment", "holidays", "fleet"],
    },
    {
        key: "operations",
        name: _t("Purchasing, Inventory & Operations"),
        names: ["Purchase", "Inventory", "Maintenance"],
        fragments: ["purchase", "stock", "inventory", "maintenance"],
    },
    {
        key: "website_learning",
        name: _t("Website, Learning & Surveys"),
        names: ["Website", "eLearning", "Elearning", "Surveys"],
        fragments: ["website", "website_slides", "survey"],
    },
    {
        key: "analytics",
        name: _t("Analytics & Reporting"),
        names: ["Dashboards", "BI Connector", "User Audit"],
        fragments: ["board", "dashboard", "bi_connector", "user_audit"],
    },
    {
        key: "admin",
        name: _t("Administration & Settings"),
        names: ["Apps", "Settings"],
        fragments: ["base.menu_apps", "base.menu_administration", "settings"],
    },
];

function normalize(value) {
    return (value || "")
        .toString()
        .toLowerCase()
        .replace(/&/g, " and ")
        .replace(/[^a-z0-9]+/g, " ")
        .trim();
}

function appMatchesGroup(app, group) {
    const appName = normalize(app.name);
    const technicalName = normalize([app.xmlid, app.actionPath].filter(Boolean).join(" "));
    const names = group.names.map(normalize);
    const fragments = group.fragments.map(normalize);

    return (
        names.some((name) => appName === name || appName === `radwan ${name}`) ||
        fragments.some((fragment) => technicalName.includes(fragment))
    );
}

patch(NavBar.prototype, {
    setup() {
        super.setup(...arguments);
        this.state.radwanCollapsedAppGroups = this.state.radwanCollapsedAppGroups || {};
    },

    radwanGetGroupedApps(apps = []) {
        const usedAppIds = new Set();
        const groupedApps = [];

        for (const group of RADWAN_APP_GROUPS) {
            const groupApps = apps.filter((app) => {
                if (usedAppIds.has(app.id) || !appMatchesGroup(app, group)) {
                    return false;
                }
                usedAppIds.add(app.id);
                return true;
            });

            if (groupApps.length) {
                groupedApps.push({
                    key: group.key,
                    name: group.name,
                    apps: groupApps,
                });
            }
        }

        const otherApps = apps.filter((app) => !usedAppIds.has(app.id));
        if (otherApps.length) {
            groupedApps.push({
                key: "other",
                name: _t("Other Apps"),
                apps: otherApps,
            });
        }

        return groupedApps;
    },

    radwanGetAppDisplayName(app) {
        return RADWAN_APP_DISPLAY_NAMES[normalize(app.name)] || app.name;
    },

    radwanIsAppGroupOpen(groupKey) {
        if (Object.prototype.hasOwnProperty.call(this.state.radwanCollapsedAppGroups, groupKey)) {
            return this.state.radwanCollapsedAppGroups[groupKey] !== true;
        }
        return RADWAN_DEFAULT_OPEN_APP_GROUPS.has(groupKey);
    },

    radwanToggleAppGroup(groupKey, ev) {
        ev?.preventDefault();
        ev?.stopPropagation();
        ev?.stopImmediatePropagation?.();
        this.state.radwanCollapsedAppGroups = {
            ...this.state.radwanCollapsedAppGroups,
            [groupKey]: this.radwanIsAppGroupOpen(groupKey),
        };
    },
});
