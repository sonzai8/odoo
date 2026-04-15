/** @odoo-module **/

import { Component, useState, onMounted } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class MissingAttendanceView extends Component {
    static template = "dl_wood_payroll.MissingAttendanceView";
    static props = {};

    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");

        this.state = useState({
            date: this._getYesterday(),
            groupId: false,
            groups: [],
            employees: [],
            loading: false,
        });

        onMounted(async () => {
            await this._loadGroups();
            await this._loadMissingEmployees();
        });
    }

    // ─── Helpers ngày tháng ──────────────────────────────────────────────────

    _formatDate(date) {
        const y = date.getFullYear();
        const m = String(date.getMonth() + 1).padStart(2, "0");
        const d = String(date.getDate()).padStart(2, "0");
        return `${y}-${m}-${d}`;
    }

    _getYesterday() {
        const d = new Date();
        d.setDate(d.getDate() - 1);
        return this._formatDate(d);
    }

    _parseDate(dateStr) {
        const [y, m, d] = dateStr.split("-").map(Number);
        return new Date(y, m - 1, d);
    }

    get formattedDate() {
        const [y, m, d] = this.state.date.split("-");
        return `${d}/${m}/${y}`;
    }

    get isToday() {
        return this.state.date === this._formatDate(new Date());
    }

    get isFuture() {
        return this.state.date > this._formatDate(new Date());
    }

    // ─── Tải dữ liệu ─────────────────────────────────────────────────────────

    async _loadGroups() {
        const groups = await this.orm.searchRead(
            "dl.production.group",
            [["active", "=", true]],
            ["id", "name", "department_id"],
            { order: "department_id asc, name asc" }
        );
        this.state.groups = groups;
    }

    async _loadMissingEmployees() {
        this.state.loading = true;
        try {
            // Bước 1: Lấy IDs nhân viên đã chấm công trong ngày đã chọn
            const attendedLines = await this.orm.searchRead(
                "dl.daily.attendance.line",
                [["date", "=", this.state.date]],
                ["employee_id"]
            );
            const attendedIds = attendedLines
                .map((l) => l.employee_id && l.employee_id[0])
                .filter(Boolean);

            // Bước 2: Domain lọc nhân viên thiếu công
            const domain = [
                ["id", "not in", attendedIds],
                ["active", "=", true],
                ["x_source_group_id", "!=", false], // Chỉ NV sản xuất có tổ biên chế
            ];

            if (this.state.groupId) {
                domain.push(["x_source_group_id", "=", this.state.groupId]);
            }

            const employees = await this.orm.searchRead(
                "hr.employee",
                domain,
                ["id", "name", "department_id", "x_source_group_id", "job_id"],
                { order: "x_source_group_id asc, name asc" }
            );

            this.state.employees = employees;
        } finally {
            this.state.loading = false;
        }
    }

    // ─── Handlers ─────────────────────────────────────────────────────────────

    async prevDay() {
        const d = this._parseDate(this.state.date);
        d.setDate(d.getDate() - 1);
        this.state.date = this._formatDate(d);
        await this._loadMissingEmployees();
    }

    async nextDay() {
        const d = this._parseDate(this.state.date);
        d.setDate(d.getDate() + 1);
        this.state.date = this._formatDate(d);
        await this._loadMissingEmployees();
    }

    async onDateChange(ev) {
        if (!ev.target.value) return;
        this.state.date = ev.target.value;
        await this._loadMissingEmployees();
    }

    async onGroupChange(ev) {
        this.state.groupId = ev.target.value ? parseInt(ev.target.value) : false;
        await this._loadMissingEmployees();
    }

    openEmployee(employeeId) {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            res_model: "hr.employee",
            res_id: employeeId,
            views: [[false, "form"]],
            target: "current",
        });
    }

    // ─── Export ───────────────────────────────────────────────────────────────

    exportToExcel() {
        if (this.state.employees.length === 0) return;

        // Chuẩn bị header và dữ liệu
        const headers = ["STT", "Tên nhân viên", "Tổ sản xuất", "Công đoạn", "Chức vụ"];
        const rows = this.state.employees.map((emp, index) => [
            index + 1,
            emp.name,
            emp.x_source_group_id ? emp.x_source_group_id[1] : "",
            emp.department_id ? emp.department_id[1] : "",
            emp.job_id ? emp.job_id[1] : "",
        ]);

        // Tạo nội dung CSV (có BOM để hỗ trợ tiếng Việt Excel)
        const csvContent = "\uFEFF" + [
            headers.join(","),
            ...rows.map(row => row.map(cell => `"${cell}"`).join(","))
        ].join("\n");

        // Tạo link download
        const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        const fileName = `Nhan_vien_thieu_cong_${this.state.date}.csv`;

        link.setAttribute("href", url);
        link.setAttribute("download", fileName);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
}

registry.category("actions").add("dl_missing_attendance_view", MissingAttendanceView);
