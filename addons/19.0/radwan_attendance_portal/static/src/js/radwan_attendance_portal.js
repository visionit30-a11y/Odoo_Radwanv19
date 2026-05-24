import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { _t } from "@web/core/l10n/translation";

export class RadwanAttendancePortal extends Interaction {
    static selector = ".radwan_attendance_portal";

    start() {
        this.isSubmitting = false;
        this.messageEl = this.el.querySelector(".radwan-attendance-message");
        this.actionButtons = this.el.querySelectorAll("[data-radwan-attendance-action]");
        this.permissionForm = this.el.querySelector(".radwan-attendance-permission-form");

        for (const button of this.actionButtons) {
            button.addEventListener("click", (ev) => this.onAttendanceAction(ev));
        }
        this.permissionForm?.addEventListener("submit", (ev) => this.onPermissionSubmit(ev));
    }

    setBusy(isBusy) {
        this.isSubmitting = isBusy;
        for (const button of this.el.querySelectorAll("button")) {
            button.disabled = isBusy;
        }
    }

    showMessage(message, type = "success") {
        if (!this.messageEl) {
            return;
        }
        this.messageEl.textContent = message;
        this.messageEl.classList.remove("d-none", "is-success", "is-error");
        this.messageEl.classList.add(type === "success" ? "is-success" : "is-error");
    }

    async getLocation() {
        if (!navigator.geolocation) {
            throw new Error(_t("Geolocation is not supported by this browser."));
        }
        return new Promise((resolve, reject) => {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    resolve({
                        latitude: position.coords.latitude,
                        longitude: position.coords.longitude,
                        accuracy: position.coords.accuracy || 0,
                    });
                },
                () => reject(new Error(_t("You must allow geolocation."))),
                {
                    enableHighAccuracy: true,
                    timeout: 15000,
                    maximumAge: 0,
                }
            );
        });
    }

    async onAttendanceAction(ev) {
        ev.preventDefault();
        if (this.isSubmitting) {
            return;
        }

        const action = ev.currentTarget.dataset.radwanAttendanceAction;
        this.setBusy(true);
        try {
            const location = await this.getLocation();
            const result = await rpc("/my/attendance/action", {
                action,
                ...location,
            });
            this.showMessage(result.message, result.success ? "success" : "error");
            if (result.success && result.reload) {
                window.setTimeout(() => window.location.reload(), 650);
            }
        } catch (error) {
            this.showMessage(error.message || _t("The operation could not be completed."), "error");
        } finally {
            this.setBusy(false);
        }
    }

    timeToFloat(value) {
        if (!value) {
            return 0;
        }
        const [hours, minutes] = value.split(":").map((part) => parseInt(part, 10) || 0);
        return hours + minutes / 60;
    }

    async onPermissionSubmit(ev) {
        ev.preventDefault();
        if (this.isSubmitting) {
            return;
        }

        const formData = new FormData(this.permissionForm);
        this.setBusy(true);
        try {
            const location = await this.getLocation();
            const result = await rpc("/my/attendance/permission", {
                permission_type: formData.get("permission_type"),
                time_from: this.timeToFloat(formData.get("time_from")),
                time_to: this.timeToFloat(formData.get("time_to")),
                reason: formData.get("reason"),
                note: formData.get("note"),
                ...location,
            });
            this.showMessage(result.message, result.success ? "success" : "error");
            if (result.success) {
                const modalEl = this.el.querySelector("#radwanAttendancePermissionModal");
                const modal = window.bootstrap?.Modal.getInstance(modalEl);
                modal?.hide();
                this.permissionForm.reset();
            }
            if (result.success && result.reload) {
                window.setTimeout(() => window.location.reload(), 650);
            }
        } catch (error) {
            this.showMessage(error.message || _t("The operation could not be completed."), "error");
        } finally {
            this.setBusy(false);
        }
    }
}

registry.category("public.interactions").add("radwan_attendance_portal.portal", RadwanAttendancePortal);
