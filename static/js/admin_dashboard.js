(function () {
    function getJson(id) {
        const el = document.getElementById(id);
        if (!el) return null;
        try {
            return JSON.parse(el.textContent);
        } catch (error) {
            console.error(`Failed to parse JSON from ${id}`, error);
            return null;
        }
    }

    function getThemeColors() {
        const styles = getComputedStyle(document.documentElement);
        const text = styles.getPropertyValue("--fallback-bc, oklch(var(--bc)/1)") || "#1f2937";
        return {
            axis: "#94a3b8",
            grid: "rgba(148, 163, 184, 0.25)",
            text: "#334155",
            bars: ["#06b6d4", "#3b82f6", "#f97316"],
            pie: ["#06b6d4", "#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6"],
            billing: ["#ef4444", "#f59e0b", "#10b981"],
            workflow: ["#06b6d4", "#3b82f6", "#f97316", "#ef4444"],
            bg: "#ffffff"
        };
    }

    function prepareCanvas(canvas) {
        if (!canvas) return null;
        const rect = canvas.getBoundingClientRect();
        const dpr = window.devicePixelRatio || 1;
        const width = Math.max(Math.floor(rect.width), 300);
        const height = Math.max(Math.floor(rect.height), 240);
        canvas.width = width * dpr;
        canvas.height = height * dpr;
        const ctx = canvas.getContext("2d");
        ctx.scale(dpr, dpr);
        return { ctx, width, height };
    }

    function formatNumber(value) {
        if (typeof value !== "number") return String(value);
        return value.toLocaleString();
    }

    function drawLegend(ctx, items, startX, startY, maxWidth) {
        const lineHeight = 20;
        const boxSize = 10;
        let x = startX;
        let y = startY;

        ctx.font = "12px sans-serif";
        ctx.textBaseline = "middle";

        items.forEach((item) => {
            const textWidth = ctx.measureText(item.label).width;
            const itemWidth = boxSize + 8 + textWidth + 16;

            if (x + itemWidth > startX + maxWidth) {
                x = startX;
                y += lineHeight;
            }

            ctx.fillStyle = item.color;
            ctx.fillRect(x, y - boxSize / 2, boxSize, boxSize);

            ctx.fillStyle = "#475569";
            ctx.fillText(item.label, x + boxSize + 8, y);

            x += itemWidth;
        });

        return y + lineHeight;
    }

    function drawBarChart(canvasId, labels, datasets) {
        const canvas = document.getElementById(canvasId);
        const prepared = prepareCanvas(canvas);
        if (!prepared) return;

        const { ctx, width, height } = prepared;
        const colors = getThemeColors();

        ctx.clearRect(0, 0, width, height);

        const margin = { top: 20, right: 16, bottom: 60, left: 44 };
        const chartWidth = width - margin.left - margin.right;
        const chartHeight = height - margin.top - margin.bottom;

        const maxValue = Math.max(
            1,
            ...datasets.flatMap((dataset) => dataset.data)
        );

        ctx.strokeStyle = colors.grid;
        ctx.lineWidth = 1;

        const gridLines = 5;
        for (let i = 0; i <= gridLines; i++) {
            const y = margin.top + (chartHeight / gridLines) * i;
            ctx.beginPath();
            ctx.moveTo(margin.left, y);
            ctx.lineTo(width - margin.right, y);
            ctx.stroke();

            const value = Math.round(maxValue - (maxValue / gridLines) * i);
            ctx.fillStyle = colors.text;
            ctx.font = "11px sans-serif";
            ctx.textAlign = "right";
            ctx.fillText(formatNumber(value), margin.left - 6, y + 4);
        }

        const groupCount = labels.length;
        const datasetCount = datasets.length;
        const groupWidth = chartWidth / groupCount;
        const barWidth = Math.min(18, (groupWidth * 0.75) / datasetCount);

        labels.forEach((label, index) => {
            const groupX = margin.left + groupWidth * index;
            const xStart = groupX + (groupWidth - barWidth * datasetCount) / 2;

            datasets.forEach((dataset, datasetIndex) => {
                const value = dataset.data[index] || 0;
                const barHeight = (value / maxValue) * chartHeight;
                const x = xStart + datasetIndex * barWidth;
                const y = margin.top + chartHeight - barHeight;

                ctx.fillStyle = dataset.color;
                ctx.fillRect(x, y, barWidth - 2, barHeight);
            });

            ctx.fillStyle = colors.text;
            ctx.font = "11px sans-serif";
            ctx.textAlign = "center";
            ctx.fillText(label, groupX + groupWidth / 2, height - 16);
        });

        drawLegend(
            ctx,
            datasets.map((dataset) => ({ label: dataset.label, color: dataset.color })),
            margin.left,
            height - 42,
            chartWidth
        );
    }

    function drawPieLikeChart(canvasId, labels, values, colorsList, options = {}) {
        const canvas = document.getElementById(canvasId);
        const prepared = prepareCanvas(canvas);
        if (!prepared) return;

        const { ctx, width, height } = prepared;
        ctx.clearRect(0, 0, width, height);

        const total = values.reduce((sum, value) => sum + value, 0);
        const centerX = width / 2;
        const centerY = Math.max(110, height / 2 - 16);
        const radius = Math.min(width, height) * 0.24;
        const innerRadius = options.doughnut ? radius * 0.55 : 0;

        if (total <= 0) {
            ctx.fillStyle = "#64748b";
            ctx.font = "14px sans-serif";
            ctx.textAlign = "center";
            ctx.fillText("No data available", centerX, centerY);
            return;
        }

        let startAngle = -Math.PI / 2;

        values.forEach((value, index) => {
            const sliceAngle = (value / total) * Math.PI * 2;
            const endAngle = startAngle + sliceAngle;

            ctx.beginPath();
            ctx.moveTo(centerX, centerY);
            ctx.arc(centerX, centerY, radius, startAngle, endAngle);
            ctx.closePath();
            ctx.fillStyle = colorsList[index % colorsList.length];
            ctx.fill();

            startAngle = endAngle;
        });

        if (innerRadius > 0) {
            ctx.beginPath();
            ctx.arc(centerX, centerY, innerRadius, 0, Math.PI * 2);
            ctx.fillStyle = "#ffffff";
            ctx.fill();

            ctx.fillStyle = "#334155";
            ctx.font = "bold 20px sans-serif";
            ctx.textAlign = "center";
            ctx.fillText(String(total), centerX, centerY + 6);
        }

        const legendItems = labels.map((label, index) => ({
            label: `${label} (${formatNumber(values[index])})`,
            color: colorsList[index % colorsList.length]
        }));

        drawLegend(ctx, legendItems, 16, height - 56, width - 32);
    }

    function renderAdminCharts() {
        const labels = getJson("monthly-labels-data") || [];
        const patients = getJson("monthly-patients-data") || [];
        const consultations = getJson("monthly-consultations-data") || [];
        const revenue = getJson("monthly-revenue-data") || [];
        const roleCounts = getJson("role-counts-data") || {};
        const workflow = getJson("workflow-distribution-data") || {};
        const billing = getJson("billing-distribution-data") || {};

        const colors = getThemeColors();

        drawBarChart("activityBarChart", labels, [
            { label: "Patients", data: patients, color: colors.bars[0] },
            { label: "Consultations", data: consultations, color: colors.bars[1] },
            { label: "Revenue", data: revenue, color: colors.bars[2] }
        ]);

        drawPieLikeChart(
            "staffPieChart",
            ["Admins", "Doctors", "Nurses", "Accountants", "Lab Technicians", "Pharmacists"],
            [
                roleCounts.admins || 0,
                roleCounts.doctors || 0,
                roleCounts.nurses || 0,
                roleCounts.accountants || 0,
                roleCounts.lab_technicians || 0,
                roleCounts.pharmacists || 0
            ],
            colors.pie
        );

        drawPieLikeChart(
            "workflowPieChart",
            ["Waiting Room", "Consultations", "Admissions", "Pending Lab"],
            [
                workflow.waiting_room || 0,
                workflow.consultations || 0,
                workflow.admissions || 0,
                workflow.pending_lab || 0
            ],
            colors.workflow,
            { doughnut: true }
        );

        drawPieLikeChart(
            "billingPieChart",
            ["Unpaid", "Part Paid", "Paid Full"],
            [
                billing.unpaid || 0,
                billing.part_paid || 0,
                billing.paid_full || 0
            ],
            colors.billing
        );
    }

    document.addEventListener("DOMContentLoaded", function () {
        if (document.getElementById("activityBarChart")) {
            renderAdminCharts();

            let resizeTimeout = null;
            window.addEventListener("resize", function () {
                clearTimeout(resizeTimeout);
                resizeTimeout = setTimeout(renderAdminCharts, 150);
            });
        }
    });
})();