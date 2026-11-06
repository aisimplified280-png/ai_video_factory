import test from "node:test";
import assert from "node:assert/strict";
import { buildContactSheetFilter } from "../pipeline/contact-sheet.mjs";

test("contact sheet includes all five scene frames in a 3 by 2 grid", () => {
  const result = buildContactSheetFilter(5);
  assert.equal(result.columns, 3);
  assert.equal(result.rows, 2);
  assert.equal(result.outputWidth, 1080);
  assert.equal(result.outputHeight, 1280);
  assert.match(result.filterComplex, /\[4:v\]/);
  assert.match(result.filterComplex, /hstack=inputs=2,pad=1080:640/);
  assert.match(result.filterComplex, /vstack=inputs=2/);
});

test("pads a one-frame final row without creating a one-input stack", () => {
  const result = buildContactSheetFilter(4);
  assert.equal(result.rows, 2);
  assert.match(result.filterComplex, /\\[3:v\\]pad=1080:640:0:0:black\\[r1\\]/);
  assert.doesNotMatch(result.filterComplex, /hstack=inputs=1/);
});

test("motion contact sheet supports five rows of entrance, action and payoff", () => {
  const result = buildContactSheetFilter(15, { columns: 3 });
  assert.equal(result.columns, 3);
  assert.equal(result.rows, 5);
  assert.equal(result.outputWidth, 1080);
  assert.equal(result.outputHeight, 3200);
  assert.match(result.filterComplex, /\[14:v\]/);
  assert.match(result.filterComplex, /vstack=inputs=5/);
});

test("rejects invalid grid dimensions and input counts", () => {
  assert.throws(() => buildContactSheetFilter(0), /positive integer/);
  assert.throws(() => buildContactSheetFilter(4, { columns: 0 }), /positive integer/);
  assert.throws(() => buildContactSheetFilter(4, { cellWidth: 8 }), />= 16/);
});
