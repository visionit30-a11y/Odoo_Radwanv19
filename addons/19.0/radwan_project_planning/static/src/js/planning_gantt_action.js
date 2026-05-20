/** @odoo-module **/

import { registry } from "@web/core/registry";
import { standardActionServiceProps } from "@web/webclient/actions/action_service";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { Component, onWillStart, useState } from "@odoo/owl";

const DAY_WIDTH = 56;
const MODEL = "radwan.planning.slot";

function formatServerDate(date) {
    return date.toISOString().slice(0, 19).replace("T", " ");
}

function parseServerDate(value) {
    if (!value) {
        return false;
    }
    return new Date(`${value.replace(" ", "T")}Z`);
}

function startOfWeek(date) {
    const result = new Date(date);
    result.setHours(0, 0, 0, 0);
    result.setDate(result.getDate() - result.getDay());
    return result;
}

function endOfDay(date) {
    const result = new Date(date);
    result.setHours(23, 59, 59, 999);
    return result;
}

function addDays(date, days) {
    const result = new Date(date);
    result.setDate(result.getDate() + days);
    return result;
}

function addMonths(date, months) {
    const result = new Date(date);
    result.setMonth(result.getMonth() + months);
    return result;
}

function getMany2OneName(value) {
    return Array.isArray(value) ? value[1] : "";
}

function getMany2OneId(value) {
    return Array.isArray(value) ? value[0] : false;
}

export class RadwanPlanningGanttAction extends Component {
    static template = "radwan_project_planning.GanttAction";
    static props = { ...standardActionServiceProps };

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");
        const context = this.props.action.context || {};
        this.state = useState({
            anchorDate: new Date(),
            groupBy: context.radwan_gantt_group_by || "resource",
            scale: "month",
            search: "",
            isLoading: true,
            slots: [],
        });
        onWillStart(() => this.load());
    }

    get range() {
        const anchor = new Date(this.state.anchorDate);
        if (this.state.scale === "week") {
            const start = startOfWeek(anchor);
            return { start, stop: endOfDay(addDays(start, 6)) };
        }
        const start = new Date(anchor.getFullYear(), anchor.getMonth(), 1);
        const stop = endOfDay(new Date(anchor.getFullYear(), anchor.getMonth() + 1, 0));
        return { start, stop };
    }

    get days() {
        const { start, stop } = this.range;
        const days = [];
        let cursor = new Date(start);
        while (cursor <= stop) {
            days.push({
                key: cursor.toISOString().slice(0, 10),
                number: String(cursor.getDate()).padStart(2, "0"),
                weekday: cursor.toLocaleDateString(undefined, { weekday: "short" }),
                isToday: cursor.toDateString() === new Date().toDateString(),
            });
            cursor = addDays(cursor, 1);
        }
        return days;
    }

    get rangeLabel() {
        const { start, stop } = this.range;
        const options = { month: "short", day: "numeric", year: "numeric" };
        return `${start.toLocaleDateString(undefined, options)} - ${stop.toLocaleDateString(
            undefined,
            options
        )}`;
    }

    get groupLabel() {
        const labels = {
            resource: _t("Resource"),
            role: _t("Role"),
            project: _t("Project"),
        };
        return labels[this.state.groupBy] || labels.resource;
    }

    get title() {
        return _t("Schedule by %s", this.groupLabel);
    }

    get filteredSlots() {
        const term = this.state.search.trim().toLowerCase();
        if (!term) {
            return this.state.slots;
        }
        return this.state.slots.filter((slot) =>
            [
                slot.name,
                slot.description,
                getMany2OneName(slot.employee_id),
                getMany2OneName(slot.material_id),
                getMany2OneName(slot.role_id),
                getMany2OneName(slot.project_id),
                getMany2OneName(slot.task_id),
            ]
                .filter(Boolean)
                .some((value) => value.toLowerCase().includes(term))
        );
    }

    get rows() {
        const rows = new Map();
        for (const slot of this.filteredSlots) {
            const key = this.getRowKey(slot);
            if (!rows.has(key)) {
                rows.set(key, {
                    key,
                    label: this.getRowLabel(slot),
                    avatarUrl: this.getAvatarUrl(slot),
                    slots: [],
                    totalHours: 0,
                });
            }
            const row = rows.get(key);
            row.slots.push(this.prepareSlot(slot));
            row.totalHours += slot.allocated_hours || 0;
        }
        return [...rows.values()].sort((a, b) => a.label.localeCompare(b.label));
    }

    get totalSlots() {
        return this.filteredSlots.length;
    }

    async load() {
        this.state.isLoading = true;
        const { start, stop } = this.range;
        const domain = [
            ["active", "=", true],
            ["start_datetime", "<", formatServerDate(stop)],
            ["end_datetime", ">", formatServerDate(start)],
        ];
        this.state.slots = await this.orm.searchRead(
            MODEL,
            domain,
            [
                "name",
                "description",
                "resource_type",
                "employee_id",
                "material_id",
                "role_id",
                "project_id",
                "task_id",
                "start_datetime",
                "end_datetime",
                "allocated_hours",
                "state",
                "color",
            ],
            { order: "start_datetime, employee_id, material_id, id", limit: 500 }
        );
        this.state.isLoading = false;
    }

    getRowKey(slot) {
        if (this.state.groupBy === "role") {
            return `role-${getMany2OneId(slot.role_id) || "none"}`;
        }
        if (this.state.groupBy === "project") {
            return `project-${getMany2OneId(slot.project_id) || "none"}`;
        }
        if (slot.resource_type === "open") {
            return "open";
        }
        if (slot.resource_type === "material") {
            return `material-${getMany2OneId(slot.material_id) || "none"}`;
        }
        return `employee-${getMany2OneId(slot.employee_id) || "none"}`;
    }

    getRowLabel(slot) {
        if (this.state.groupBy === "role") {
            return getMany2OneName(slot.role_id) || _t("No Role");
        }
        if (this.state.groupBy === "project") {
            return getMany2OneName(slot.project_id) || _t("No Project");
        }
        if (slot.resource_type === "open") {
            return _t("Open Shifts");
        }
        if (slot.resource_type === "material") {
            return getMany2OneName(slot.material_id) || _t("No Material");
        }
        return getMany2OneName(slot.employee_id) || _t("No Employee");
    }

    getAvatarUrl(slot) {
        if (this.state.groupBy !== "resource" || slot.resource_type !== "employee") {
            return false;
        }
        const employeeId = getMany2OneId(slot.employee_id);
        return employeeId ? `/web/image/hr.employee/${employeeId}/avatar_128` : false;
    }

    prepareSlot(slot) {
        const { start, stop } = this.range;
        const slotStart = parseServerDate(slot.start_datetime);
        const slotStop = parseServerDate(slot.end_datetime);
        const boundedStart = slotStart < start ? start : slotStart;
        const boundedStop = slotStop > stop ? stop : slotStop;
        const totalMs = stop - start || 1;
        const left = ((boundedStart - start) / totalMs) * this.days.length * DAY_WIDTH;
        const width = Math.max(((boundedStop - boundedStart) / totalMs) * this.days.length * DAY_WIDTH, 28);
        return {
            ...slot,
            displayName: this.getSlotName(slot),
            style: `left:${left}px;width:${width}px;`,
            className: `o_radwan_gantt_bar_${slot.state}`,
        };
    }

    getSlotName(slot) {
        return (
            slot.description ||
            getMany2OneName(slot.task_id) ||
            getMany2OneName(slot.project_id) ||
            getMany2OneName(slot.role_id) ||
            slot.name
        );
    }

    async previous() {
        this.state.anchorDate =
            this.state.scale === "week"
                ? addDays(this.state.anchorDate, -7)
                : addMonths(this.state.anchorDate, -1);
        await this.load();
    }

    async next() {
        this.state.anchorDate =
            this.state.scale === "week"
                ? addDays(this.state.anchorDate, 7)
                : addMonths(this.state.anchorDate, 1);
        await this.load();
    }

    async today() {
        this.state.anchorDate = new Date();
        await this.load();
    }

    async setScale(scale) {
        this.state.scale = scale;
        await this.load();
    }

    async setGroupBy(groupBy) {
        this.state.groupBy = groupBy;
    }

    onSearch(ev) {
        this.state.search = ev.target.value;
    }

    openSlot(slot) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: _t("Planning Shift"),
            res_model: MODEL,
            res_id: slot.id,
            views: [[false, "form"]],
            target: "current",
        });
    }

    createSlot() {
        const { start } = this.range;
        this.action.doAction({
            type: "ir.actions.act_window",
            name: _t("Planning Shift"),
            res_model: MODEL,
            views: [[false, "form"]],
            target: "current",
            context: {
                default_start_datetime: formatServerDate(start),
                default_end_datetime: formatServerDate(addDays(start, 1)),
            },
        });
    }

    async publishVisibleDrafts() {
        const ids = this.filteredSlots
            .filter((slot) => slot.state === "draft")
            .map((slot) => slot.id);
        if (!ids.length) {
            this.notification.add(_t("There are no draft shifts to publish."), {
                type: "info",
            });
            return;
        }
        await this.orm.call(MODEL, "action_publish", [ids]);
        this.notification.add(_t("Draft shifts were published."), { type: "success" });
        await this.load();
    }

    openWindowView(viewType) {
        const viewModes = {
            calendar: "calendar,list,form",
            list: "list,form",
            kanban: "kanban,list,form",
            pivot: "pivot,graph,list",
            graph: "graph,pivot,list",
        };
        const contexts = {
            resource: { search_default_group_employee: 1 },
            role: { search_default_group_role: 1 },
            project: { search_default_group_project: 1 },
        };
        this.action.doAction({
            type: "ir.actions.act_window",
            name: this.title,
            res_model: MODEL,
            views: [[false, viewType]],
            view_mode: viewModes[viewType] || "list,form",
            target: "current",
            context: contexts[this.state.groupBy] || {},
        });
    }
}

registry.category("actions").add("radwan_planning_gantt", RadwanPlanningGanttAction);
