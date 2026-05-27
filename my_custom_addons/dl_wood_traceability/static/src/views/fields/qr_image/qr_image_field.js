import { ImageField } from "@web/views/fields/image/image_field";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { deserializeDate } from "@web/core/l10n/dates";
import { Dialog } from "@web/core/dialog/dialog";
import { Component } from "@odoo/owl";

export class ImagePreviewDialog extends Component {
    static template = "dl_wood_traceability.ImagePreviewDialog";
    static components = { Dialog };
    static props = {
        imageSrc: String,
        title: { type: String, optional: true },
        size: { type: String, optional: true },
        close: Function,
    };
}

export class DuplicatePartnerDialog extends Component {
    static template = "dl_wood_traceability.DuplicatePartnerDialog";
    static components = { Dialog };
    static props = {
        partner: Object,
        exploitationAddress: { type: String, optional: true },
        title: { type: String, optional: true },
        onRedirect: Function,
        close: Function,
    };

    get cccdNumber() {
        const p = this.props.partner;
        return p.x_cccd || p.x_identity_code || "";
    }

    get phone() {
        return this.props.partner.phone || "";
    }

    get partnerAddress() {
        const parts = [];
        const p = this.props.partner;
        if (p.street) parts.push(p.street);
        if (p.city) parts.push(p.city);
        if (p.state_id && p.state_id[1]) parts.push(p.state_id[1]);
        return parts.join(", ");
    }

    onRedirectClick() {
        this.props.onRedirect();
        this.props.close();
    }
}


export class QrImageField extends ImageField {
    static template = "dl_wood_traceability.QrImageField";

    setup() {
        super.setup();
        this.notification = useService("notification");
        this.dialogService = useService("dialog");
        this.actionService = useService("action");
    }

    onImageClick() {
        if (!this.props.record.data[this.props.name]) {
            return;
        }
        const imageSrc = this.getUrl(this.props.previewImage || this.props.name);
        this.dialogService.add(ImagePreviewDialog, {
            imageSrc: imageSrc,
            title: _t("Xem ảnh QR CCCD"),
            size: "md",
        });
    }

    async onFileUploaded(info) {
        try {
            // Giải mã mã QR và tự động cắt ảnh trực tiếp trên client
            const result = await this.processQRAndCrop(info.data, info.type);
            if (result && result.qrData) {
                // Thay thế dữ liệu ảnh upload bằng ảnh đã cắt
                info.data = result.croppedData;
                // Điền dữ liệu CCCD lên form
                await this.parseCCCDQR(result.qrData);
            } else {
                this.notification.add(
                    _t("Không tìm thấy mã QR nào trong ảnh. Vui lòng chọn ảnh chụp mã QR CCCD rõ nét hơn!"),
                    { type: "danger", title: _t("Lỗi quét QR CCCD") }
                );
            }
        } catch (err) {
            console.error("Error processing and cropping QR Code", err);
            this.notification.add(
                _t("Lỗi khi xử lý ảnh QR CCCD: ") + err.message,
                { type: "danger", title: _t("Lỗi quét QR CCCD") }
            );
        }

        // Gọi xử lý tải ảnh lên hệ thống (Nếu có QR thì upload ảnh đã crop, ngược lại upload ảnh gốc)
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
                        reject(new Error("Thư viện jsQR chưa được nạp."));
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
                        
                        // Thêm khoảng đệm (padding) 20% kích thước QR (tối thiểu 40px)
                        const padding = Math.max(Math.max(qrWidth, qrHeight) * 0.2, 40);
                        
                        const cropX = Math.max(0, Math.floor(minX - padding));
                        const cropY = Math.max(0, Math.floor(minY - padding));
                        const cropWidth = Math.min(img.width - cropX, Math.ceil(qrWidth + padding * 2));
                        const cropHeight = Math.min(img.height - cropY, Math.ceil(qrHeight + padding * 2));
                        
                        // Thực hiện cắt ảnh trên canvas mới
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
        // Định dạng CCCD: Số CCCD|Số CMND cũ|Họ và tên|Ngày sinh|Giới tính|Địa chỉ thường trú|Ngày cấp
        console.log("[CCCD] parseCCCDQR gọi với qrString:", qrString);
        const parts = qrString.split('|');
        console.log("[CCCD] parts sau khi split('|'):", parts, "=> length:", parts.length);
        if (parts.length < 7) {
            this.notification.add(
                _t("Nội dung mã QR không đúng định dạng CCCD Việt Nam hợp lệ (thiếu thông tin). Vui lòng thử lại!"),
                { type: "danger", title: _t("Lỗi định dạng QR") }
            );
            return;
        }

        const identityCode = parts[0].trim();
        const name = parts[2].trim();
        const birthDateStr = parts[3].trim();
        const gender = parts[4].trim();
        const address = parts[5].trim();
        const issueDateStr = parts[6].trim();
        console.log("[CCCD] Dữ liệu bóc tách: identityCode=", identityCode, "| name=", name, "| address=", address);

        // Kiểm tra hợp lệ Số CCCD (12 chữ số)
        if (!/^\d{12}$/.test(identityCode)) {
            this.notification.add(
                _t("Mã QR không đúng định dạng CCCD Việt Nam hợp lệ (Số CCCD phải có 12 chữ số)."),
                { type: "danger", title: _t("Lỗi dữ liệu CCCD") }
            );
            return;
        }

        // Parse ngày sinh và ngày cấp (định dạng DDMMYYYY sang YYYY-MM-DD)
        const parseDate = (dateStr) => {
            if (dateStr.length !== 8) return null;
            const day = dateStr.substring(0, 2);
            const month = dateStr.substring(2, 4);
            const year = dateStr.substring(4, 8);
            return `${year}-${month}-${day}`;
        };

        const birthDate = parseDate(birthDateStr);
        const issueDate = parseDate(issueDateStr);

        if (!birthDate || !issueDate) {
            this.notification.add(
                _t("Ngày tháng trong CCCD không đúng định dạng (DDMMYYYY)."),
                { type: "danger", title: _t("Lỗi định dạng Ngày") }
            );
            return;
        }

        // Gọi RPC lên Backend để phân tách và ánh xạ địa giới hành chính cũ sang mới
        let parsedAddress = { street: address, city: "", state_id: false };
        try {
            console.log("[CCCD] Gọi RPC action_parse_cccd_address với address:", address);
            const result = await this.orm.call(
                "res.partner",
                "action_parse_cccd_address",
                [address]
            );
            console.log("[CCCD] Kết quả RPC trả về:", result);
            if (result) {
                parsedAddress = result;
            }
        } catch (rpcErr) {
            console.error("[CCCD] Lỗi RPC khi phân tích địa chỉ: ", rpcErr);
        }

        // Cập nhật các trường trên form thông qua Odoo OWL record update API
        const stateValue = (parsedAddress.state_id && parsedAddress.state_name)
            ? { id: parsedAddress.state_id, display_name: parsedAddress.state_name }
            : false;
            
        const wardValue = (parsedAddress.ward_id && parsedAddress.ward_name)
            ? { id: parsedAddress.ward_id, display_name: parsedAddress.ward_name }
            : false;

        const changes = {
            x_identity_code: identityCode,
            x_cccd: identityCode,
            name: name,
            x_birth_date: deserializeDate(birthDate),
            street: parsedAddress.street || "",
            city: parsedAddress.city || "",
            state_id: stateValue,
            ward_id: wardValue,
            x_issue_date: deserializeDate(issueDate),
            x_cccd_date: deserializeDate(issueDate),
            x_cccd_place: "Cục Cảnh sát QLHC về TTXH",
        };
        console.log("[CCCD] parsedAddress dùng để ghi vào form:", parsedAddress);
        console.log("[CCCD] stateValue (Many2one format):", stateValue);
        console.log("[CCCD] changes ghi vào record:", JSON.stringify(changes, null, 2));

        if (gender === 'Nam' || gender === 'Nữ') {
            changes.x_gender = gender;
        }

        // Kiểm tra trùng lặp CCCD trong cơ sở dữ liệu trước khi điền form
        try {
            const domain = [
                "|",
                ["x_cccd", "=", identityCode],
                ["x_identity_code", "=", identityCode],
                ["id", "!=", this.props.record.resId || 0]
            ];
            // Đối với Chủ rừng, có thể cần thêm điều kiện x_is_wood_supplier = 'owner'
            // nhưng để an toàn, quét trùng trên toàn partner
            console.log("[CCCD] Kiểm tra trùng lặp CCCD với domain:", domain);
            const duplicates = await this.orm.searchRead(
                "res.partner",
                domain,
                ["id", "name", "phone", "x_cccd", "x_identity_code", "street", "city", "state_id"]
            );
            console.log("[CCCD] Kết quả kiểm tra trùng lặp:", duplicates);
            
            if (duplicates.length > 0) {
                const duplicatePartner = duplicates[0];
                this.notification.add(
                    _t("Phát hiện CCCD đã tồn tại! Hệ thống sẽ không điền dữ liệu để tránh tạo trùng."),
                    { type: "warning", title: _t("Cảnh báo trùng lặp") }
                );

                // Lấy thông tin địa chỉ khai thác, ưu tiên địa điểm chính (is_main = true)
                let exploitationAddress = "";
                try {
                    const locations = await this.orm.searchRead(
                        "dl.wood.exploitation.location",
                        [["partner_id", "=", duplicatePartner.id]],
                        ["name", "full_address", "is_main"]
                    );
                    if (locations.length > 0) {
                        let mainLoc = locations.find(loc => loc.is_main) || locations[0];
                        exploitationAddress = mainLoc.name;
                        if (mainLoc.full_address) {
                            exploitationAddress += " - " + mainLoc.full_address;
                        }
                    }
                } catch (locErr) {
                    console.error("[CCCD] Lỗi khi tìm địa chỉ khai thác:", locErr);
                }

                this.dialogService.add(DuplicatePartnerDialog, {
                    partner: duplicatePartner,
                    exploitationAddress: exploitationAddress,
                    title: _t("Cảnh báo: Chủ rừng đã tồn tại"),
                    onRedirect: () => {
                        this.actionService.doAction({
                            type: "ir.actions.act_window",
                            res_model: "res.partner",
                            res_id: duplicatePartner.id,
                            views: [[false, "form"]],
                            target: "current",
                        });
                    }
                });
                
                // Trả về ngay, không update thông tin vào form để ngăn user lưu trùng
                return;
            }
        } catch (dbErr) {
            console.error("[CCCD] Lỗi khi kiểm tra trùng lặp CCCD trong DB:", dbErr);
        }

        try {
            console.log("[CCCD] Bắt đầu gọi record.update...");
            this.props.record.update(changes);
            console.log("[CCCD] record.update gọi thành công!");
            
            // Hiển thị thông báo thành công
            this.notification.add(
                _t("Đã quét và điền thông tin CCCD thành công cho: ") + name,
                { type: "success", title: _t("Thành công") }
            );
        } catch (updateErr) {
            console.error("[CCCD] Lỗi khi update record:", updateErr);
            this.notification.add(
                _t("Lỗi khi điền thông tin lên form: ") + updateErr.message,
                { type: "danger", title: _t("Lỗi điền thông tin") }
            );
        }
    }
}

// Đăng ký field widget mới vào registry của Odoo 19
export const qrImageField = {
    supportedAttributes: [
        {
            label: _t("Alternative text"),
            name: "alt",
            type: "string",
        },
    ],
    supportedOptions: [
        {
            label: _t("Reload"),
            name: "reload",
            type: "boolean",
            default: true,
        },
        {
            label: _t("Enable zoom"),
            name: "zoom",
            type: "boolean",
        },
        {
            label: _t("Convert to webp"),
            name: "convert_to_webp",
            type: "boolean",
        },
        {
            label: _t("Zoom delay"),
            name: "zoom_delay",
            type: "number",
        },
        {
            label: _t("Accepted file extensions"),
            name: "accepted_file_extensions",
            type: "string",
        },
        {
            label: _t("Size"),
            name: "size",
            type: "selection",
            choices: [
                { label: _t("Small"), value: "[0,90]" },
                { label: _t("Medium"), value: "[0,180]" },
                { label: _t("Large"), value: "[0,270]" },
            ],
        },
        {
            label: _t("Preview image"),
            name: "preview_image",
            type: "field",
            availableTypes: ["binary"],
        },
    ],
    supportedTypes: ["binary"],
    fieldDependencies: [{ name: "write_date", type: "datetime" }],
    isEmpty: () => false,
    extractProps: ({ attrs, options }) => ({
        alt: attrs.alt,
        enableZoom: options.zoom,
        convertToWebp: options.convert_to_webp,
        imgClass: options.img_class,
        zoomDelay: options.zoom_delay,
        previewImage: options.preview_image,
        acceptedFileExtensions: options.accepted_file_extensions,
        width: options.size && Boolean(options.size[0]) ? options.size[0] : undefined,
        height: options.size && Boolean(options.size[1]) ? options.size[1] : undefined,
        reload: "reload" in options ? Boolean(options.reload) : true,
    }),
    component: QrImageField,
    displayName: _t("QR Image"),
};

registry.category("fields").add("qr_image", qrImageField);
