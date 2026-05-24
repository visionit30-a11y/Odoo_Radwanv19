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
        this.cameraModalEl = this.el.querySelector("#radwanAttendanceCameraModal");
        this.cameraVideo = this.el.querySelector(".radwan-attendance-camera-video");
        this.cameraCanvas = this.el.querySelector(".radwan-attendance-camera-canvas");
        this.cameraCaptureButton = this.el.querySelector("[data-radwan-camera-capture]");
        this.cameraCancelButton = this.el.querySelector("[data-radwan-camera-cancel]");
        this.cameraStream = null;

        for (const button of this.actionButtons) {
            button.addEventListener("click", (ev) => this.onAttendanceAction(ev));
        }
        this.permissionForm?.addEventListener("submit", (ev) => this.onPermissionSubmit(ev));
    }

    setBusy(isBusy) {
        this.isSubmitting = isBusy;
        for (const button of this.el.querySelectorAll("[data-radwan-attendance-action], .radwan-attendance-permission-form button")) {
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

    stopCamera() {
        if (this.cameraStream) {
            for (const track of this.cameraStream.getTracks()) {
                track.stop();
            }
            this.cameraStream = null;
        }
        if (this.cameraVideo) {
            this.cameraVideo.srcObject = null;
        }
    }

    async captureAttendancePhoto(message) {
        if (!navigator.mediaDevices?.getUserMedia) {
            throw new Error(_t("Camera is not supported by this browser."));
        }
        if (!this.cameraModalEl || !this.cameraVideo || !this.cameraCanvas) {
            throw new Error(_t("Camera capture is not available."));
        }

        const messageEl = this.cameraModalEl.querySelector(".radwan-attendance-camera-message");
        if (messageEl) {
            messageEl.textContent = message || _t("Please capture an attendance photo before continuing.");
        }

        this.stopCamera();
        this.cameraStream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: "user" },
            audio: false,
        });
        this.cameraVideo.srcObject = this.cameraStream;
        await this.cameraVideo.play();

        const modal = window.bootstrap?.Modal.getOrCreateInstance(this.cameraModalEl);
        modal?.show();

        return new Promise((resolve, reject) => {
            const cleanup = () => {
                this.cameraCaptureButton?.removeEventListener("click", onCapture);
                this.cameraCancelButton?.removeEventListener("click", onCancel);
                this.cameraModalEl.removeEventListener("hidden.bs.modal", onCancel);
                this.stopCamera();
            };
            const onCapture = () => {
                const width = this.cameraVideo.videoWidth || 640;
                const height = this.cameraVideo.videoHeight || 480;
                this.cameraCanvas.width = width;
                this.cameraCanvas.height = height;
                this.cameraCanvas.getContext("2d").drawImage(this.cameraVideo, 0, 0, width, height);
                const photo = this.cameraCanvas.toDataURL("image/jpeg", 0.82);
                cleanup();
                modal?.hide();
                resolve(photo);
            };
            const onCancel = () => {
                cleanup();
                reject(new Error(_t("Attendance photo capture was cancelled.")));
            };
            this.cameraCaptureButton?.addEventListener("click", onCapture);
            this.cameraCancelButton?.addEventListener("click", onCancel);
            this.cameraModalEl.addEventListener("hidden.bs.modal", onCancel);
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
            const policy = await rpc("/my/attendance/photo-policy", {
                action,
                ...location,
            });
            if (!policy.success) {
                this.showMessage(policy.message, "error");
                return;
            }
            const photoData = policy.require_photo ? await this.captureAttendancePhoto(policy.message) : false;
            const result = await rpc("/my/attendance/action", {
                action,
                photo_data: photoData,
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

export class RadwanAttendanceLocationMapPicker extends Interaction {
    static selector = ".radwan_attendance_location_picker";

    start() {
        this.locationId = parseInt(this.el.dataset.locationId, 10);
        this.latInput = this.el.querySelector("[name='latitude']");
        this.lngInput = this.el.querySelector("[name='longitude']");
        this.radiusInput = this.el.querySelector("[name='allowed_radius']");
        this.messageEl = this.el.querySelector(".radwan-map-picker-message");
        this.mapEl = this.el.querySelector(".radwan-location-map");
        this.marker = null;
        this.circle = null;

        this.el.querySelector("[data-radwan-map-current]")?.addEventListener("click", () => this.useCurrentLocation());
        this.el.querySelector("[data-radwan-map-save]")?.addEventListener("click", () => this.saveLocation());

        this.initMapWhenReady();
    }

    initMapWhenReady() {
        if (window.L) {
            this.initMap();
            return;
        }
        window.setTimeout(() => this.initMapWhenReady(), 150);
    }

    initMap() {
        const latitude = parseFloat(this.latInput.value) || 24.7136;
        const longitude = parseFloat(this.lngInput.value) || 46.6753;
        this.map = window.L.map(this.mapEl).setView([latitude, longitude], 15);
        window.L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
            maxZoom: 19,
            attribution: "&copy; OpenStreetMap",
        }).addTo(this.map);
        this.setMarker(latitude, longitude);
        this.map.on("click", (ev) => this.setMarker(ev.latlng.lat, ev.latlng.lng));
        this.radiusInput.addEventListener("input", () => this.drawCircle());
    }

    setMarker(latitude, longitude) {
        const lat = Number(latitude).toFixed(7);
        const lng = Number(longitude).toFixed(7);
        this.latInput.value = lat;
        this.lngInput.value = lng;
        if (!this.marker) {
            this.marker = window.L.marker([latitude, longitude], { draggable: true }).addTo(this.map);
            this.marker.on("dragend", () => {
                const position = this.marker.getLatLng();
                this.setMarker(position.lat, position.lng);
            });
        } else {
            this.marker.setLatLng([latitude, longitude]);
        }
        this.drawCircle();
    }

    drawCircle() {
        const latitude = parseFloat(this.latInput.value);
        const longitude = parseFloat(this.lngInput.value);
        const radius = parseFloat(this.radiusInput.value) || 100;
        if (this.circle) {
            this.circle.remove();
        }
        this.circle = window.L.circle([latitude, longitude], {
            radius,
            color: "#6f5aa7",
            fillColor: "#6f5aa7",
            fillOpacity: 0.12,
            weight: 2,
        }).addTo(this.map);
    }

    showMessage(message, type = "success") {
        this.messageEl.textContent = message;
        this.messageEl.classList.remove("d-none", "is-success", "is-error");
        this.messageEl.classList.add(type === "success" ? "is-success" : "is-error");
    }

    async useCurrentLocation() {
        try {
            const position = await new Promise((resolve, reject) => {
                navigator.geolocation.getCurrentPosition(resolve, reject, {
                    enableHighAccuracy: true,
                    timeout: 15000,
                    maximumAge: 0,
                });
            });
            const { latitude, longitude } = position.coords;
            this.setMarker(latitude, longitude);
            this.map.setView([latitude, longitude], 17);
        } catch {
            this.showMessage(_t("You must allow geolocation."), "error");
        }
    }

    async saveLocation() {
        const result = await rpc(`/radwan/attendance/location/${this.locationId}/save-map`, {
            latitude: this.latInput.value,
            longitude: this.lngInput.value,
            allowed_radius: this.radiusInput.value,
        });
        this.showMessage(result.message, result.success ? "success" : "error");
    }
}

registry
    .category("public.interactions")
    .add("radwan_attendance_portal.location_map_picker", RadwanAttendanceLocationMapPicker);
