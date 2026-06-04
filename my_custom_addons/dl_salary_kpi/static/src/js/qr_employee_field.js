/** @odoo-module **/

import { ImageField } from "@web/views/fields/image/image_field";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { deserializeDate } from "@web/core/l10n/dates";

export class QrEmployeeImageField extends ImageField {
    setup() {
        super.setup();
        this.notification = useService("notification");
        this.orm = useService("orm");
    }

    async onFileUploaded(info) {
        try {
            const result = await this.processQRAndCrop(info.data, info.type);
            if (result && result.qrData) {
                // Dùng ảnh QR đã cắt thay cho ảnh avatar gốc
                info.data = result.croppedData;
                await this.parseCCCDQR(result.qrData);
            } else {
                this.notification.add(
                    _t("Không tìm thấy mã QR nào trong ảnh. Avatar sẽ được tải lên như ảnh thông thường."),
                    { type: "info", title: _t("Thông báo") }
                );
            }
        } catch (err) {
            console.error("Error processing QR Code", err);
            this.notification.add(
                _t("Lỗi khi xử lý ảnh QR CCCD: ") + err.message,
                { type: "danger", title: _t("Lỗi quét QR CCCD") }
            );
        }

        // Tiếp tục quá trình upload ảnh của Odoo
        await super.onFileUploaded(info);
    }

    processQRAndCrop(base64Data, mimeType) {
        return new Promise((resolve, reject) => {
            const img = new Image();
            img.onload = () => {
                try {
                    const canvas = document.createElement("canvas");
                    canvas.width = img.width;
                    canvas.height = img.height;
                    const ctx = canvas.getContext("2d");
                    ctx.drawImage(img, 0, 0);

                    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
                    
                    // Kiểm tra thư viện jsQR có được tải hay chưa
                    if (typeof window.jsQR === "undefined") {
                        reject(new Error("Thư viện jsQR chưa được nạp. Vui lòng refresh lại trang."));
                        return;
                    }
                    
                    const code = window.jsQR(imageData.data, imageData.width, imageData.height, {
                        inversionAttempts: "dontInvert",
                    });
                    
                    if (code && code.location) {
                        const loc = code.location;
                        const xs = [loc.topLeftCorner.x, loc.topRightCorner.x, loc.bottomLeftCorner.x, loc.bottomRightCorner.x];
                        const ys = [loc.topLeftCorner.y, loc.topRightCorner.y, loc.bottomLeftCorner.y, loc.bottomRightCorner.y];
                        
                        const minX = Math.min(...xs);
                        const maxX = Math.max(...xs);
                        const minY = Math.min(...ys);
                        const maxY = Math.max(...ys);
                        
                        const qrWidth = maxX - minX;
                        const qrHeight = maxY - minY;
                        
                        // Thêm padding 20%
                        const padding = Math.max(Math.max(qrWidth, qrHeight) * 0.2, 40);
                        
                        const cropX = Math.max(0, Math.floor(minX - padding));
                        const cropY = Math.max(0, Math.floor(minY - padding));
                        const cropWidth = Math.min(img.width - cropX, Math.ceil(qrWidth + padding * 2));
                        const cropHeight = Math.min(img.height - cropY, Math.ceil(qrHeight + padding * 2));
                        
                        const cropCanvas = document.createElement("canvas");
                        cropCanvas.width = cropWidth;
                        cropCanvas.height = cropHeight;
                        const cropCtx = cropCanvas.getContext("2d");
                        
                        cropCtx.drawImage(
                            img,
                            cropX, cropY, cropWidth, cropHeight,
                            0, 0, cropWidth, cropHeight
                        );
                        
                        const croppedDataUrl = cropCanvas.toDataURL(mimeType);
                        const croppedBase64 = croppedDataUrl.split(',')[1];
                        
                        resolve({
                            qrData: code.data,
                            croppedData: croppedBase64
                        });
                    } else {
                        resolve(null);
                    }
                } catch (e) {
                    reject(e);
                }
            };
            img.onerror = () => reject(new Error("Không thể nạp file ảnh."));
            img.src = `data:${mimeType};base64,${base64Data}`;
        });
    }

    async parseCCCDQR(qrString) {
        console.log("[CCCD] parseCCCDQR gọi với qrString:", qrString);
        const parts = qrString.split('|');
        if (parts.length < 7) {
            this.notification.add(
                _t("Nội dung mã QR không đúng định dạng CCCD Việt Nam hợp lệ."),
                { type: "danger", title: _t("Lỗi định dạng QR") }
            );
            return;
        }

        const identityCode = parts[0].trim();
        const name = parts[2].trim();
        const birthDateStr = parts[3].trim();
        const gender = parts[4].trim();
        const address = parts[5] ? parts[5].trim() : '';

        // Kiểm tra CCCD
        if (!/^\d{12}$/.test(identityCode)) {
            this.notification.add(
                _t("Mã QR không hợp lệ (Số CCCD phải có 12 chữ số)."),
                { type: "danger", title: _t("Lỗi dữ liệu CCCD") }
            );
            return;
        }

        const parseDate = (dateStr) => {
            if (dateStr.length !== 8) return null;
            const day = dateStr.substring(0, 2);
            const month = dateStr.substring(2, 4);
            const year = dateStr.substring(4, 8);
            return `${year}-${month}-${day}`;
        };

        const birthDate = parseDate(birthDateStr);
        if (!birthDate) {
            this.notification.add(
                _t("Ngày tháng trong CCCD không đúng định dạng."),
                { type: "danger", title: _t("Lỗi Ngày sinh") }
            );
            return;
        }

        let parsedAddress = {};
        try {
            console.log("[CCCD] Gọi RPC action_parse_cccd_address với address:", address);
            const result = await this.orm.call(
                "res.partner",
                "action_parse_cccd_address",
                [address]
            );
            if (result) {
                parsedAddress = result;
            }
        } catch (rpcErr) {
            console.error("[CCCD] Lỗi RPC khi phân tích địa chỉ: ", rpcErr);
        }

        const stateValue = (parsedAddress.state_id && parsedAddress.state_name)
            ? { id: parsedAddress.state_id, display_name: parsedAddress.state_name }
            : false;

        const changes = {
            identification_id: identityCode,
            name: name,
            birthday: deserializeDate(birthDate),
            private_street: parsedAddress.street || address,
            private_city: parsedAddress.city || "",
        };

        if (stateValue) {
            changes.private_state_id = stateValue;
        }

        const nameParts = name.split(' ');
        const firstName = nameParts.length > 0 ? nameParts[nameParts.length - 1] : name;
        changes.dl_first_name = firstName;

        if (gender === 'Nam') {
            changes.sex = 'male';
        } else if (gender === 'Nữ') {
            changes.sex = 'female';
        }

        try {
            const domain = [
                ["identification_id", "=", identityCode],
                ["id", "!=", this.props.record.resId || 0]
            ];
            const duplicates = await this.orm.searchRead("hr.employee", domain, ["id", "name"]);
            
            if (duplicates.length > 0) {
                this.notification.add(
                    _t("Phát hiện Nhân viên có cùng số CCCD này đã tồn tại! Cập nhật dữ liệu tự động bị hủy."),
                    { type: "warning", title: _t("Cảnh báo trùng lặp") }
                );
                return;
            }
        } catch (dbErr) {
            console.error("[CCCD] Lỗi khi kiểm tra trùng lặp CCCD trong DB:", dbErr);
        }

        try {
            console.log("[CCCD] Đang cập nhật record với dữ liệu:", changes);
            await this.props.record.update(changes);
            this.notification.add(
                _t("Đã bóc tách và điền thông tin CCCD thành công cho: ") + name,
                { type: "success", title: _t("Thành công") }
            );
        } catch (updateErr) {
            console.error("[CCCD] Lỗi khi update record:", updateErr);
            this.notification.add(
                _t("Lỗi khi điền thông tin lên form: ") + updateErr.message,
                { type: "danger", title: _t("Lỗi") }
            );
        }
    }
}

export const qrEmployeeImageField = {
    supportedAttributes: [
        { label: _t("Alternative text"), name: "alt", type: "string" },
    ],
    supportedOptions: [
        { label: _t("Reload"), name: "reload", type: "boolean", default: true },
        { label: _t("Enable zoom"), name: "zoom", type: "boolean" },
        { label: _t("Preview image"), name: "preview_image", type: "field", availableTypes: ["binary"] },
        { label: _t("Size"), name: "size", type: "selection", choices: [
            { label: _t("Small"), value: "[0,90]" },
            { label: _t("Medium"), value: "[0,180]" },
            { label: _t("Large"), value: "[0,270]" },
        ] },
    ],
    supportedTypes: ["binary"],
    fieldDependencies: [{ name: "write_date", type: "datetime" }],
    isEmpty: () => false,
    extractProps: ({ attrs, options }) => ({
        alt: attrs.alt,
        enableZoom: options.zoom,
        imgClass: options.img_class,
        previewImage: options.preview_image,
        width: options.size && Boolean(options.size[0]) ? options.size[0] : undefined,
        height: options.size && Boolean(options.size[1]) ? options.size[1] : undefined,
        reload: "reload" in options ? Boolean(options.reload) : true,
    }),
    component: QrEmployeeImageField,
    displayName: _t("QR Employee Avatar"),
};

registry.category("fields").add("qr_employee_image", qrEmployeeImageField);
