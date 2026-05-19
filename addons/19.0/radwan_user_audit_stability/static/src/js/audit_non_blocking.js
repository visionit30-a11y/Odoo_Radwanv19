/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import {
    deleteConfirmationMessage,
    ConfirmationDialog,
} from "@web/core/confirmation_dialog/confirmation_dialog";
import { useService } from "@web/core/utils/hooks";
import { patch } from "@web/core/utils/patch";
import { DynamicList } from "@web/model/relational_model/dynamic_list";
import { DynamicRecordList } from "@web/model/relational_model/dynamic_record_list";
import { executeButtonCallback } from "@web/views/view_button/view_button_hook";
import { FormController } from "@web/views/form/form_controller";
import { KanbanController } from "@web/views/kanban/kanban_controller";
import { ListController } from "@web/views/list/list_controller";

function auditAsync(controller, resModel, resId, operationType) {
    if (!controller.orm || !resModel) {
        return;
    }
    controller.orm
        .call("user.audit", "create_audit_log", [resModel, resId, operationType])
        .catch(() => {});
}

patch(FormController.prototype, {
    setup() {
        super.setup(...arguments);
        this.orm = useService("orm");
    },

    saveButtonClicked(params = {}) {
        const result = executeButtonCallback(this.ui.activeElement, () => this.save(params));
        Promise.resolve(result).then((saved) => {
            if (saved !== false) {
                auditAsync(this, this.model.root.resModel, this.model.root.resId, "write");
            }
        });
        return result;
    },

    async create() {
        const dirty = await this.model.root.isDirty();
        const onError = (error, options) => this.onSaveError(error, options, true);
        const canProceed = !dirty || (await this.model.root.save({ onError }));
        if (canProceed) {
            await executeButtonCallback(this.ui.activeElement, () =>
                this.model.load({ resId: false })
            );
            auditAsync(this, this.model.root.resModel, this.model.root.resId, "create");
        }
    },

    get deleteConfirmationDialogProps() {
        return {
            confirm: async () => {
                const resId = this.model.root.resId;
                auditAsync(this, this.model.root.resModel, [resId], "delete");
                await this.model.root.delete();
                if (!this.model.root.resId) {
                    this.env.config.historyBack();
                }
            },
        };
    },

    async deleteRecord() {
        this.deleteRecordsWithConfirmation(this.deleteConfirmationDialogProps, [this.model.root]);
    },
});

patch(ListController.prototype, {
    setup() {
        super.setup(...arguments);
        this.orm = useService("orm");
    },

    async createRecord({ group } = {}) {
        if (!this.model.isReady && !this.model.config.groupBy.length && this.editable) {
            await this.model.whenReady;
        }
        const list = (group && group.list) || this.model.root;
        const resModel = this.model.root.resModel;
        if (this.editable && !list.isGrouped) {
            if (!(list instanceof DynamicRecordList)) {
                throw new Error("List should be a DynamicRecordList");
            }
            await list.leaveEditMode();
            if (!list.editedRecord) {
                await (group || list).addNewRecord(this.editable === "top");
            }
            this.render();
        } else {
            await this.props.createRecord();
            auditAsync(this, resModel, false, "create");
        }
    },

    async openRecord(record, { force, newWindow } = { force: false }) {
        const dirty = await record.isDirty();
        if (dirty) {
            await record.save();
        }
        if (this.props.allowOpenAction && this.archInfo.openAction) {
            this.actionService.doActionButton(
                {
                    name: this.archInfo.openAction.action,
                    type: this.archInfo.openAction.type,
                    resModel: record.resModel,
                    resId: record.resId,
                    resIds: record.resIds,
                    context: record.context,
                    onClose: async () => {
                        await record.model.root.load();
                    },
                },
                {
                    newWindow,
                }
            );
        } else {
            const activeIds = this.model.root.records.map((datapoint) => datapoint.resId);
            this.props.selectRecord(record.resId, { activeIds, force, newWindow });
        }
        auditAsync(this, record.resModel, record.resId, "read");
    },

    get deleteConfirmationDialogProps() {
        const root = this.model.root;
        let body = deleteConfirmationMessage;
        if (root.isDomainSelected || root.selection.length > 1) {
            body = _t("Are you sure you want to delete these records?");
        }
        return {
            title: _t("Bye-bye, record!"),
            body,
            confirmLabel: _t("Delete"),
            confirm: async () => {
                const records = this.model.root.selection.map((record) => record.resId);
                await this.model.root.deleteRecords();
                auditAsync(this, this.model.root.resModel, records, "delete");
            },
            cancel: () => {},
            cancelLabel: _t("No, keep it"),
        };
    },

    async onDeleteSelectedRecords() {
        this.dialogService.add(ConfirmationDialog, this.deleteConfirmationDialogProps);
    },
});

patch(KanbanController.prototype, {
    setup() {
        super.setup(...arguments);
        this.orm = useService("orm");
    },

    deleteRecord(record) {
        this.deleteRecordsWithConfirmation(
            {
                confirm: async () => {
                    const isDynamicList = this.model.root instanceof DynamicList;
                    auditAsync(this, this.model.root.resModel, [record.resId], "delete");
                    if (isDynamicList) {
                        await this.model.root.deleteRecords([record]);
                    } else {
                        record.forEach((item) => item.delete());
                    }
                },
            },
            [record]
        );
    },

    async createRecord() {
        const { onCreate } = this.props.archInfo;
        const { root } = this.model;
        if (this.canQuickCreate && onCreate === "quick_create") {
            const firstGroup = root.groups.find((group) => !group.isFolded) || root.groups[0];
            if (firstGroup.isFolded) {
                await firstGroup.toggle();
            }
            this.quickCreateState.groupId = firstGroup.id;
        } else if (onCreate && onCreate !== "quick_create") {
            const options = {
                additionalContext: root.context,
                onClose: async ({ noReload } = {}) => {
                    if (!noReload) {
                        await root.load();
                        this.model.useSampleModel = false;
                        this.render(true);
                    }
                },
            };
            await this.actionService.doAction(onCreate, options);
        } else {
            await this.props.createRecord();
        }
        auditAsync(this, this.model.root.resModel, this.model.root.resId, "create");
    },

    async openRecord(record, { newWindow } = {}) {
        const activeIds = this.model.root.records.map((datapoint) => datapoint.resId);
        this.props.selectRecord(record.resId, { activeIds, newWindow });
        auditAsync(this, record.resModel, record.resId, "read");
    },

    async onDeleteSelectedRecords() {
        this.deleteRecordsWithConfirmation(this.deleteConfirmationDialogProps);
    },
});
