"use strict";
(function () {
    const $ = id => document.getElementById(id);
    const ns = "http://www.w3.org/2000/svg";
    let points = [];
    let lastPeaks = [];

    function status(message, isError) {
        const node = $("status");
        node.textContent = message;
        node.dataset.error = isError ? "true" : "false";
    }

    function example() {
        return Array.from({length: 401}, (_, i) => {
            const t = i * 0.05;
            const gauss = (center, width, amplitude) =>
                amplitude * Math.exp(-0.5 * Math.pow((t - center) / width, 2));
            return {time: t, signal: 2 + 0.025 * t + gauss(5.2, 0.52, 38)
                + gauss(11.8, 0.83, 28) + gauss(14.6, 0.47, 13)};
        });
    }

    function format(value, digits) {
        return value === null || !Number.isFinite(value) ? "—" : value.toFixed(digits);
    }

    function svgNode(name, attrs, parent, content) {
        const el = document.createElementNS(ns, name);
        Object.entries(attrs || {}).forEach(([key, value]) => el.setAttribute(key, String(value)));
        if (content !== undefined) el.textContent = content;
        parent.appendChild(el);
        return el;
    }

    function plot(input, peaks) {
        const svg = $("chart");
        svg.replaceChildren();
        const width = 980, height = 340, l = 64, r = 20, t = 20, b = 46;
        const left = input[0].time, right = input[input.length - 1].time;
        const yValues = input.map(p => p.signal);
        let low = Infinity, high = -Infinity;
        for (const v of yValues) { if (v < low) low = v; if (v > high) high = v; }
        const pad = Math.max((high - low) * 0.07, 1e-9);
        const yMin = low - pad, yMax = high + pad;
        const x = val => l + (val - left) * (width - l - r) / (right - left);
        const y = val => height - b - (val - yMin) * (height - t - b) / (yMax - yMin);
        svgNode("line", {x1:l,y1:height-b,x2:width-r,y2:height-b,class:"axis"}, svg);
        svgNode("line", {x1:l,y1:t,x2:l,y2:height-b,class:"axis"}, svg);
        for (let i = 0; i <= 4; i++) {
            const xv = left + (right-left)*i/4;
            const yv = yMin + (yMax-yMin)*i/4;
            svgNode("text", {x:x(xv),y:height-18,"text-anchor":"middle",class:"tick"},svg,format(xv,1));
            svgNode("text", {x:l-9,y:y(yv)+4,"text-anchor":"end",class:"tick"},svg,format(yv,1));
        }
        svgNode("text",{x:width/2,y:height-2,"text-anchor":"middle",class:"axis-label"},svg,"Retention time (min)");
        svgNode("text",{x:15,y:height/2,transform:"rotate(-90 15 "+height/2+")","text-anchor":"middle",class:"axis-label"},svg,"Detector response");
        const stride = Math.max(1, Math.ceil(input.length / 1800));
        const sampled = input.filter((_, i) => i % stride === 0 || i === input.length - 1);
        const coords = sampled.map(p => x(p.time).toFixed(2)+","+y(p.signal).toFixed(2)).join(" ");
        svgNode("polyline",{points:coords,fill:"none",class:"trace"},svg);
        peaks.forEach(p => {
            const nearest = input.find(q => q.time === p.retentionTime);
            if (!nearest) return;
            svgNode("circle",{cx:x(p.retentionTime),cy:y(nearest.signal),r:5,class:"peak-dot"},svg);
            svgNode("text",{x:x(p.retentionTime),y:y(nearest.signal)-12,
                "text-anchor":"middle",class:"peak-label"},svg,"P"+p.index);
        });
    }

    function renderTable(peaks) {
        const tbody = $("peak-rows");
        tbody.replaceChildren();
        if (!peaks.length) {
            const tr = document.createElement("tr"), cell = document.createElement("td");
            cell.colSpan = 8; cell.textContent = "No peaks detected at this prominence threshold.";
            tr.appendChild(cell); tbody.appendChild(tr); return;
        }
        peaks.forEach(p => {
            const tr = document.createElement("tr");
            const values = [p.index, format(p.retentionTime,3), format(p.height,3),
                format(p.area,3), format(p.areaPercent,1), format(p.fwhm,3),
                format(p.resolutionFromPrevious,2), format(p.retentionFactor,2)];
            values.forEach(value => {
                const td = document.createElement("td");
                td.textContent = String(value);
                tr.appendChild(td);
            });
            tbody.appendChild(tr);
        });
    }

    function run() {
        try {
            if (!points.length) throw new Error("Load a CSV file or the example first.");
            const minProminence = Number($("prominence").value) / 100;
            const deadTime = $("dead-time").value.trim();
            const result = PeakAnalysis.analyze(points, {minProminence,deadTime});
            lastPeaks = result.peaks;
            plot(points, lastPeaks);
            renderTable(lastPeaks);
            $("total-points").textContent = result.points.toLocaleString();
            $("total-peaks").textContent = String(lastPeaks.length);
            $("export").disabled = lastPeaks.length === 0;
            status("Analysis complete. Peak areas use valley splitting and a local linear baseline.", false);
        } catch (err) {
            lastPeaks = [];
            $("export").disabled = true;
            status(err instanceof Error ? err.message : "Analysis failed.", true);
        }
    }

    function downloadCsv() {
        if (!lastPeaks.length) return;
        const headers = ["peak","retention_time_min","height","area","area_percent",
            "fwhm_min","resolution_from_previous","retention_factor"];
        const rows = lastPeaks.map(p => [p.index,p.retentionTime,p.height,p.area,
            p.areaPercent,p.fwhm,p.resolutionFromPrevious,p.retentionFactor]
            .map(v => v === null ? "" : String(v)).join(","));
        const csv = [headers.join(","),...rows].join("\r\n")+"\r\n";
        const url = URL.createObjectURL(new Blob([csv],{type:"text/csv;charset=utf-8"}));
        const a = document.createElement("a"); a.href = url; a.download = "hplc-peaks.csv";
        document.body.appendChild(a); a.click(); a.remove();
        URL.revokeObjectURL(url);
    }

    $("demo").addEventListener("click", () => {
        points = example(); $("source-name").textContent = "Synthetic example (3 Gaussian peaks)";
        run();
    });
    $("file").addEventListener("change", async event => {
        const file = event.target.files && event.target.files[0];
        if (!file) return;
        if (file.size > 3 * 1024 * 1024) {
            status("The selected file exceeds the 3 MB limit.", true); return;
        }
        try {
            const parsed = PeakAnalysis.parseCsv(await file.text());
            points = parsed;
            $("source-name").textContent = file.name;
            run();
        } catch (err) {
            points = []; lastPeaks = []; $("export").disabled = true;
            status(err instanceof Error ? err.message : "Could not read file.", true);
        }
    });
    $("analyze").addEventListener("click", run);
    $("export").addEventListener("click", downloadCsv);
    points = example();
    run();
})();
