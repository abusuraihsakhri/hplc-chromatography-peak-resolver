"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const {analyze, parseCsv} = require("../web/peak-analysis.js");

const synthetic = Array.from({length:401}, (_, i) => {
    const time = i * 0.05;
    const peak = (center, width, height) =>
        height * Math.exp(-0.5 * Math.pow((time-center)/width, 2));
    return {time,signal:2+peak(5,0.5,28)+peak(13,0.8,20)};
});

test("two resolved Gaussian peaks have accurate retention times and positive areas", () => {
    const result = analyze(synthetic, {minProminence:0.05,deadTime:1});
    assert.equal(result.peaks.length,2);
    assert.ok(Math.abs(result.peaks[0].retentionTime-5)<0.05);
    assert.ok(Math.abs(result.peaks[1].retentionTime-13)<0.05);
    assert.ok(result.peaks[0].area>0);
    assert.ok(result.peaks[1].area>0);
    assert.ok(result.peaks[1].resolutionFromPrevious>2);
    assert.ok(Math.abs(result.peaks[0].retentionFactor-4)<0.05);
    const total=result.peaks.reduce((s,p)=>s+p.areaPercent,0);
    assert.ok(Math.abs(total-100)<1e-8);
});

test("CSV accepts quoted headers, BOM, tabs, and rejects unordered time", () => {
    assert.equal(parseCsv("\uFEFFtime,signal\n0,1\n1,4\n2,3\n3,5\n4,1").length,5);
    assert.equal(parseCsv("time\tsignal\n0\t1\n1\t4\n2\t3\n3\t5\n4\t1").length,5);
    assert.throws(()=>parseCsv("time,signal\n0,1\n1,2\n1,3\n3,2\n4,1"),/increasing/);
});

test("bad numeric data and limits produce explicit errors", () => {
    assert.throws(()=>parseCsv("time,signal\n0,1\n1,2\n2,abc\n3,2\n4,1"),/numeric/);
    assert.throws(()=>analyze(synthetic,{deadTime:0}),/positive/);
    assert.throws(()=>analyze(synthetic,{minProminence:1.5}),/prominence/);
    assert.throws(()=>analyze([{time:0,signal:1}]),/samples/);
});

test("flat traces generate no invented peaks", () => {
    assert.equal(analyze(Array.from({length:10},(_,i)=>({time:i,signal:4}))).peaks.length,0);
});
