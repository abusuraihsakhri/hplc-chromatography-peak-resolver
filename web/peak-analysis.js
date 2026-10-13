/* Standalone, dependency-free chromatogram analysis (browser and Node). */
(function (root, factory) {
    const api = factory();
    if (typeof module === "object" && module.exports) module.exports = api;
    else root.PeakAnalysis = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
    "use strict";
    const MAX_POINTS = 100000;

    function parseCsv(source) {
        if (typeof source !== "string" || !source.trim()) throw new Error("CSV input is empty.");
        const text = source.replace(/^\uFEFF/, "");
        const firstLine = text.split(/\r?\n/, 1)[0];
        const delimiter = ["\t", ";", ","].sort((a, b) =>
            firstLine.split(b).length - firstLine.split(a).length)[0];
        const records = [];
        let record = [], cell = "", quoted = false;
        for (let i = 0; i < text.length; i++) {
            const ch = text[i];
            if (ch === '"') {
                if (quoted && text[i + 1] === '"') { cell += '"'; i++; }
                else quoted = !quoted;
            } else if (ch === delimiter && !quoted) {
                record.push(cell.trim()); cell = "";
            } else if ((ch === "\r" || ch === "\n") && !quoted) {
                if (ch === "\r" && text[i + 1] === "\n") i++;
                record.push(cell.trim());
                if (record.some(value => value !== "")) records.push(record);
                record = []; cell = "";
            } else cell += ch;
        }
        if (quoted) throw new Error("CSV contains an unterminated quoted field.");
        record.push(cell.trim());
        if (record.some(value => value !== "")) records.push(record);
        if (records.length < 6) throw new Error("At least five numeric samples are required.");
        if (records.length > MAX_POINTS + 1) throw new Error("CSV exceeds the 100,000-point limit.");

        const numeric = value => value !== "" && Number.isFinite(Number(value));
        const hasHeader = !numeric(records[0][0]) || !numeric(records[0][1]);
        const header = hasHeader ? records.shift().map(s => s.toLowerCase().trim()) : [];
        const findCol = (pattern, fallback) => {
            const i = header.findIndex(name => pattern.test(name));
            return i < 0 ? fallback : i;
        };
        const timeCol = findCol(/^(time|retention.?time|rt|minutes|min)(\b|_)/, 0);
        const signalCol = findCol(/^(signal|response|intensity|absorbance|area|uv|mau)(\b|_)/, timeCol === 0 ? 1 : 0);
        if (timeCol === signalCol) throw new Error("Select distinct time and signal columns.");
        const points = records.map((r, i) => {
            const t = Number(r[timeCol]), y = Number(r[signalCol]);
            if (!numeric(r[timeCol]) || !numeric(r[signalCol])) {
                throw new Error("Invalid numeric value at data row " + (i + 1) + ".");
            }
            if (i > 0 && t <= Number(records[i - 1][timeCol])) {
                throw new Error("Retention times must be strictly increasing (row " + (i + 1) + ").");
            }
            return {time: t, signal: y};
        });
        if (points.length < 5) throw new Error("At least five numeric samples are required.");
        return points;
    }

    function analyze(points, options) {
        options = options || {};
        const threshold = options.minProminence == null ? 0.06 : Number(options.minProminence);
        const deadTime = options.deadTime == null || options.deadTime === "" ? null : Number(options.deadTime);
        if (!Number.isFinite(threshold) || threshold <= 0 || threshold >= 1) {
            throw new Error("Minimum prominence must be between 0 and 1.");
        }
        if (deadTime !== null && (!Number.isFinite(deadTime) || deadTime <= 0)) {
            throw new Error("Dead time must be positive.");
        }
        if (!Array.isArray(points) || points.length < 5 || points.length > MAX_POINTS) {
            throw new Error("Provide 5 to 100,000 samples.");
        }
        const y = points.map((p, i) => {
            if (!p || !Number.isFinite(p.time) || !Number.isFinite(p.signal) ||
                (i > 0 && p.time <= points[i - 1].time)) {
                throw new Error("Non-finite value or non-increasing time at sample " + (i + 1) + ".");
            }
            return p.signal;
        });
        const n = y.length, smooth = y.map((v, i) => i === 0 || i === n - 1
            ? v : (y[i - 1] + 2 * v + y[i + 1]) / 4);
        let low = Infinity, high = -Infinity;
        for (const v of smooth) { if (v < low) low = v; if (v > high) high = v; }
        const span = high - low;
        if (span <= 0) return {peaks: [], points: points.length, minSignal: low, maxSignal: high};
        const minimaLeft = [], minimaRight = [];
        let floor = Infinity;
        for (let i = 0; i < n; i++) { floor = Math.min(floor, smooth[i]); minimaLeft.push(floor); }
        floor = Infinity;
        for (let i = n - 1; i >= 0; i--) { floor = Math.min(floor, smooth[i]); minimaRight[i] = floor; }
        const maxima = [];
        for (let i = 1; i < n - 1; i++) {
            const prominence = smooth[i] - Math.max(minimaLeft[i], minimaRight[i]);
            if (smooth[i] > smooth[i - 1] && smooth[i] >= smooth[i + 1] &&
                prominence >= threshold * span) maxima.push(i);
        }
        const valleys = [];
        for (let i = 0; i < maxima.length - 1; i++) {
            let best = maxima[i];
            for (let k = maxima[i] + 1; k < maxima[i + 1]; k++) {
                if (smooth[k] < smooth[best]) best = k;
            }
            valleys.push(best);
        }
        function crossing(center, edge, half, direction) {
            let i = center;
            while (i !== edge) {
                const next = i + direction;
                if (smooth[next] <= half) {
                    const dy = smooth[next] - smooth[i];
                    const ratio = dy === 0 ? 0 : (half - smooth[i]) / dy;
                    return points[i].time + ratio * (points[next].time - points[i].time);
                }
                i = next;
            }
            return null;
        }
        const peaks = maxima.map((index, ordinal) => {
            const left = ordinal === 0 ? 0 : valleys[ordinal - 1];
            const right = ordinal === maxima.length - 1 ? n - 1 : valleys[ordinal];
            const base = Math.max(smooth[left], smooth[right]);
            const height = smooth[index] - base;
            const half = base + height / 2;
            const cLeft = height > 0 ? crossing(index, left, half, -1) : null;
            const cRight = height > 0 ? crossing(index, right, half, 1) : null;
            let area = 0;
            for (let k = left; k < right; k++) {
                const b1 = y[left] + (y[right] - y[left]) *
                    (points[k].time - points[left].time) / (points[right].time - points[left].time);
                const b2 = y[left] + (y[right] - y[left]) *
                    (points[k + 1].time - points[left].time) / (points[right].time - points[left].time);
                area += (points[k + 1].time - points[k].time) *
                    (Math.max(0, y[k] - b1) + Math.max(0, y[k + 1] - b2)) / 2;
            }
            return {
                index: ordinal + 1,
                retentionTime: points[index].time,
                height: Math.max(0, height),
                area: area,
                areaPercent: 0,
                fwhm: cLeft === null || cRight === null ? null : cRight - cLeft,
                resolutionFromPrevious: null,
                retentionFactor: deadTime === null ? null : (points[index].time - deadTime) / deadTime,
                startTime: points[left].time,
                endTime: points[right].time
            };
        });
        const totalArea = peaks.reduce((sum, p) => sum + p.area, 0);
        peaks.forEach((p, i) => {
            p.areaPercent = totalArea > 0 ? 100 * p.area / totalArea : 0;
            if (i > 0 && p.fwhm !== null && peaks[i - 1].fwhm !== null) {
                const denom = p.fwhm + peaks[i - 1].fwhm;
                if (denom > 0) p.resolutionFromPrevious =
                    1.18 * (p.retentionTime - peaks[i - 1].retentionTime) / denom;
            }
        });
        let ymin = Infinity, ymax = -Infinity;
        for (const v of y) { if (v < ymin) ymin = v; if (v > ymax) ymax = v; }
        return {peaks, points: n, minSignal: ymin, maxSignal: ymax};
    }
    return {parseCsv, analyze};
});
