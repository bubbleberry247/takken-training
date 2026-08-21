import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import fs from 'node:fs';
import vm from 'node:vm';

const specSource = fs.readFileSync(new URL('../src/patchR6Takken028Spec.gs', import.meta.url), 'utf8');
const patchSource = fs.readFileSync(new URL('../src/patchR6Takken028.gs', import.meta.url), 'utf8');
const csvText = fs.readFileSync(new URL('../data/takken_questionbank_import.csv', import.meta.url), 'utf8');
const manifest = JSON.parse(fs.readFileSync(new URL('../src/appsscript.json', import.meta.url), 'utf8'));
const QID = 'R6takken-028';

function parseCsv(text) {
  const rows = [];
  let row = [];
  let field = '';
  let quoted = false;
  for (let i = 0; i < text.length; i += 1) {
    const ch = text[i];
    if (quoted) {
      if (ch === '"') {
        if (text[i + 1] === '"') { field += '"'; i += 1; } else quoted = false;
      } else field += ch;
    } else if (ch === '"') quoted = true;
    else if (ch === ',') { row.push(field); field = ''; }
    else if (ch === '\n') { row.push(field); rows.push(row); row = []; field = ''; }
    else if (ch !== '\r') field += ch;
  }
  if (field || row.length) { row.push(field); rows.push(row); }
  const headers = rows.shift().map((value) => value.replace(/^\uFEFF/, ''));
  return { headers, rows: rows.filter((values) => values.length > 1 || values[0]) };
}

class FakeRange {
  constructor(sheet, row, col, numRows = 1, numCols = 1) {
    this.sheet = sheet; this.row = row; this.col = col; this.numRows = numRows; this.numCols = numCols;
  }
  getValues() {
    return Array.from({ length: this.numRows }, (_, r) => Array.from({ length: this.numCols }, (_, c) =>
      (this.sheet.data[this.row - 1 + r] || [])[this.col - 1 + c] ?? ''));
  }
  getDisplayValues() {
    return this.getValues().map((row, rowOffset) => row.map((value, colOffset) => {
      if (this.sheet.displayTransform) return this.sheet.displayTransform(value, this.row - 1 + rowOffset, this.col - 1 + colOffset);
      if (value instanceof Date) return new Date(value.getTime() + 9 * 60 * 60 * 1000).toISOString().slice(0, 10);
      return String(value ?? '');
    }));
  }
  getDisplayValue() { return this.getDisplayValues()[0][0]; }
  setValues(values) {
    const requiredRows = this.row - 1 + values.length;
    const requiredCols = this.col - 1 + Math.max(0, ...values.map((value) => value.length));
    while (this.sheet.data.length < requiredRows) this.sheet.data.push([]);
    for (const source of this.sheet.data) while (source.length < requiredCols) source.push('');
    for (let r = 0; r < values.length; r += 1) for (let c = 0; c < values[r].length; c += 1) {
      this.sheet.data[this.row - 1 + r][this.col - 1 + c] = values[r][c];
    }
  }
  setValue(value) { this.setValues([[value]]); }
  setFrozenRows() {}
}

class FakeSheet {
  constructor(data, sheetId = 501) { this.data = data; this.sheetId = sheetId; this.displayTransform = null; }
  getDataRange() { return new FakeRange(this, 1, 1, this.data.length, this.getLastColumn()); }
  getLastRow() { return this.data.length; }
  getLastColumn() { return this.data[0]?.length || 1; }
  getRange(row, col, numRows = 1, numCols = 1) { return new FakeRange(this, row, col, numRows, numCols); }
  getSheetId() { return this.sheetId; }
  setFrozenRows() {}
}

class FakeDb {
  constructor(questionBank) { this.id = 'fake-r6-db'; this.sheets = new Map([['QuestionBank', new FakeSheet(questionBank)]]); }
  getId() { return this.id; }
  getSheetByName(name) { return this.sheets.get(name) || null; }
  insertSheet(name) { const sheet = new FakeSheet([[]], 777); this.sheets.set(name, sheet); return sheet; }
}

const parsed = parseCsv(csvText);
const headers = parsed.headers;
const targetIndex = parsed.rows.findIndex((row) => row[0] === QID);
assert.notEqual(targetIndex, -1);
assert.equal(parsed.rows.length, 600);

function makeHarness({ specMode = 'fixture' } = {}) {
  const questionBank = [headers.slice(), ...parsed.rows.map((row) => headers.map((_, index) => row[index] ?? ''))];
  const liveTarget = questionBank[targetIndex + 1];
  liveTarget[headers.indexOf('explainLong')] = '';
  liveTarget[headers.indexOf('updatedAt')] = new Date('2026-04-09T15:00:00.000Z');
  const db = new FakeDb(questionBank);
  const props = new Map([
    ['DB_SPREADSHEET_ID', db.id],
    ['TAKKEN_R6_028_MAINTENANCE_WINDOW', 'OPEN'],
  ]);
  const logger = { logs: [], log(value) { this.logs.push(String(value)); } };
  let flushHook = null;
  let uuid = 0;
  let cacheClears = 0;
  const fakeSheets = {
    calls: [], mode: 'normal', beforeBatch: null, afterBatch: null,
    Spreadsheets: {
      batchUpdate(body, spreadsheetId) {
        fakeSheets.calls.push({ body, spreadsheetId });
        assert.equal(spreadsheetId, 'fake-r6-db');
        if (fakeSheets.beforeBatch) { const hook = fakeSheets.beforeBatch; fakeSheets.beforeBatch = null; hook(); }
        if (fakeSheets.mode === 'throw') throw new Error('simulated atomic API rejection');
        const replies = [];
        for (let requestIndex = 0; requestIndex < body.requests.length; requestIndex += 1) {
          const update = body.requests[requestIndex].updateCells;
          assert.ok(update, 'only updateCells requests are allowed');
          assert.equal(update.fields, 'userEnteredValue');
          assert.equal(update.range.sheetId, 501);
          assert.equal(update.range.endRowIndex, update.range.startRowIndex + 1);
          const targetRow = questionBank[update.range.startRowIndex];
          for (let offset = 0; offset < update.rows[0].values.length; offset += 1) {
            targetRow[update.range.startColumnIndex + offset] = update.rows[0].values[offset].userEnteredValue.stringValue;
          }
          if (fakeSheets.mode === 'partialThrow' && requestIndex === 0) throw new Error('simulated unknown partial response');
          replies.push({ updateCells: {} });
        }
        if (fakeSheets.afterBatch) { const hook = fakeSheets.afterBatch; fakeSheets.afterBatch = null; hook(); }
        if (fakeSheets.mode === 'badReply') {
          fakeSheets.mode = 'normal';
          return { replies: replies.slice(0, Math.max(0, replies.length - 1)) };
        }
        return { replies };
      },
    },
  };
  const context = {
    console,
    Logger: logger,
    HEADERS: { QuestionBank: headers },
    SHEETS: { QuestionBank: 'QuestionBank' },
    Utilities: {
      DigestAlgorithm: { SHA_256: 'sha256' }, Charset: { UTF_8: 'utf8' },
      computeDigest(_algorithm, value) { return Array.from(crypto.createHash('sha256').update(String(value), 'utf8').digest()); },
      formatDate(value, _timezone, pattern) {
        const local = new Date(value.getTime() + 9 * 60 * 60 * 1000);
        const date = local.toISOString().slice(0, 10);
        const time = local.toISOString().slice(11, 19);
        return pattern === 'yyyy-MM-dd' ? date : `${date} ${time}`;
      },
      getUuid() { uuid += 1; return `fixture-${uuid}`; },
    },
    SpreadsheetApp: { flush() { if (flushHook) { const hook = flushHook; flushHook = null; hook(); } } },
    LockService: {
      waits: 0, releases: 0,
      getScriptLock() { return { waitLock() { context.LockService.waits += 1; }, releaseLock() { context.LockService.releases += 1; } }; },
    },
    Sheets: fakeSheets,
    normalizeHeader_(value, index) { const text = String(value ?? '').trim(); return index === 0 ? text.replace(/^\uFEFF/, '') : text; },
  };
  vm.createContext(context);
  vm.runInContext(`${specSource}\n${patchSource}`, context, { filename: 'R6Takken028Patch.gs' });
  context.getDbId_ = () => props.get('DB_SPREADSHEET_ID') || '';
  context.getDb_ = () => db;
  context.getScriptProps_ = () => ({ getProperty(key) { return props.get(key) || null; } });
  context.clearAllCache_ = ({ strict }) => { assert.equal(strict, true); cacheClears += 1; };

  if (specMode === 'checked-in') {
    const target = questionBank[targetIndex + 1];
    target[headers.indexOf('stem')] = context.TAKKEN_R6_028_RELEASE_SPEC_.beforeValues.stem;
  } else if (specMode === 'blocked') {
    const target = questionBank[targetIndex + 1];
    context.TAKKEN_R6_028_RELEASE_SPEC_ = {
      qId: QID,
      releaseStatus: 'blocked',
      expectedBeforeRuntimeRowSha256: context.takkenR6028FullRowSha256_(target, headers),
      fieldWhitelist: [], beforeValues: {}, replacementValues: {},
    };
  } else if (specMode === 'fixture') {
    const target = questionBank[targetIndex + 1];
    const fieldWhitelist = ['stem'];
    const beforeValues = Object.fromEntries(fieldWhitelist.map((field) => [field, target[headers.indexOf(field)]]));
    const replacementValues = { stem: `${beforeValues.stem}\n\nTEST-APPROVED-STATEMENTS` };
    const afterRow = target.slice();
    for (const field of fieldWhitelist) afterRow[headers.indexOf(field)] = replacementValues[field];
    context.TAKKEN_R6_028_RELEASE_SPEC_ = {
      qId: QID,
      releaseStatus: 'approved',
      officialSourceSha256: '82a95815f991567ebc4982b05a15a71f6ec942bd6794c3bafe3bcf9c2e985bae',
      officialSourcePage: 16,
      sourceKind: 'RETIO_official_question_pdf',
      expectedLabelSequence: 'ア・イ・ウ',
      sourceBeforeRuntimeRowSha256: 'a'.repeat(64),
      sourceAfterRuntimeRowSha256: 'b'.repeat(64),
      liveBaselineOverrides: { explainLong: '' },
      liveDateOnlyFields: ['updatedAt'],
      liveDiagnosticReceiptSha256: 'b73cffb1a1e5cf43fc5894edb5107c20d5fbc9bd06a39bd280425d344c810925',
      expectedBeforeRuntimeRowSha256: context.takkenR6028FullRowSha256_(target, headers),
      expectedAfterRuntimeRowSha256: context.takkenR6028FullRowSha256_(afterRow, headers),
      fieldWhitelist,
      beforeValues,
      replacementValues,
      beforeValuesSha256: context.takkenR6028ValuesSha256_(beforeValues, fieldWhitelist),
      replacementValuesSha256: context.takkenR6028ValuesSha256_(replacementValues, fieldWhitelist),
      approvalEvidenceSha256: 'b'.repeat(64),
      reviewedAt: '2099-01-01T00:00:00+09:00',
    };
  } else throw new Error(`unknown specMode: ${specMode}`);
  const initial = new Map(questionBank.slice(1).map((row) => [row[0], row.slice()]));
  return {
    context, questionBank, db, props, logger, fakeSheets, initial,
    setFlushHook(hook) { flushHook = hook; },
    get cacheClears() { return cacheClears; },
  };
}

function rowsById(questionBank) { return new Map(questionBank.slice(1).map((row) => [row[0], row])); }

function assertOnlyFieldsChanged(harness, state, fields = ['stem']) {
  const current = rowsById(harness.questionBank);
  const allowed = new Set(fields.map((field) => headers.indexOf(field)));
  for (const [qId, before] of harness.initial) {
    const after = current.get(qId);
    assert.ok(after, `${qId} is missing`);
    if (qId !== QID || state === 'before') assert.deepEqual(after, before, `${qId} unexpectedly changed`);
    else for (let index = 0; index < headers.length; index += 1) {
      if (allowed.has(index)) assert.notEqual(after[index], before[index], `${headers[index]} did not change`);
      else assert.equal(after[index], before[index], `${headers[index]} is protected`);
    }
  }
}

function assertOnlyApprovedFieldsChanged(harness, state) {
  assertOnlyFieldsChanged(harness, state);
}

// Static publication-safety contracts.
assert.ok(manifest.dependencies?.enabledAdvancedServices?.some((service) =>
  service.userSymbol === 'Sheets' && service.serviceId === 'sheets' && service.version === 'v4'));
assert.match(patchSource, /function ADMIN_inspectTakkenR6028DryRun_\(\)/);
assert.match(patchSource, /function ADMIN_patchTakkenR6028DryRun_\(\)/);
assert.match(patchSource, /function ADMIN_applyTakkenR6028_\(\)/);
assert.match(patchSource, /function ADMIN_rollbackLatestTakkenR6028DryRun_\(\)/);
assert.match(patchSource, /function ADMIN_rollbackLatestTakkenR6028_\(\)/);
assert.doesNotMatch(patchSource, /\.clear\s*\(/);
assert.doesNotMatch(patchSource, /findReplace/);
assert.match(patchSource, /updateCells/);
assert.doesNotMatch(specSource, /TEST-APPROVED/);

// A blocked release record permits redacted inspection but no patch dry-run.
const blockedHarness = makeHarness({ specMode: 'blocked' });
const inspection = blockedHarness.context.ADMIN_inspectTakkenR6028DryRun_();
assert.equal(inspection.releaseStatus, 'blocked');
assert.equal(inspection.matched, 1);
assert.equal(inspection.nonTargetCount, 599);
assert.equal(inspection.wouldUpdate, 0);
assert.equal(inspection.expectedBeforeMatches, true);
assert.throws(() => blockedHarness.context.ADMIN_patchTakkenR6028DryRun_(), /not approved/);
assert.equal(blockedHarness.fakeSheets.calls.length, 0);
assert.equal(blockedHarness.db.getSheetByName('_QuestionBankR6028PatchBackup'), null);

// This release is permanently stem-only; even a formerly generic allowed
// field such as choiceA is rejected before a plan or write is attempted.
const protectedFieldHarness = makeHarness();
protectedFieldHarness.context.TAKKEN_R6_028_RELEASE_SPEC_.fieldWhitelist = ['choiceA'];
assert.throws(() => protectedFieldHarness.context.ADMIN_patchTakkenR6028DryRun_(), /exactly stem/);
assert.equal(protectedFieldHarness.fakeSheets.calls.length, 0);

const receiptIdentityHarness = makeHarness();
receiptIdentityHarness.context.TAKKEN_R6_028_RELEASE_SPEC_.liveDiagnosticReceiptSha256 = '0'.repeat(64);
assert.throws(() => receiptIdentityHarness.context.ADMIN_patchTakkenR6028DryRun_(), /receipt identity mismatch/);
assert.equal(receiptIdentityHarness.fakeSheets.calls.length, 0);

// The checked-in official release spec contains one approved stem payload and
// validates against the preserved pre-production row fixture.
const checkedInHarness = makeHarness({ specMode: 'checked-in' });
const checkedInDry = checkedInHarness.context.ADMIN_patchTakkenR6028DryRun_();
assert.equal(checkedInHarness.context.TAKKEN_R6_028_RELEASE_SPEC_.releaseStatus, 'approved');
assert.deepEqual(Array.from(checkedInHarness.context.TAKKEN_R6_028_RELEASE_SPEC_.fieldWhitelist), ['stem']);
assert.equal(checkedInDry.matched, 1);
assert.equal(checkedInDry.wouldUpdate, 1);
assert.equal(checkedInDry.nonTargetCount, 599);
assert.equal(checkedInDry.fieldCount, 1);
assert.equal(checkedInHarness.fakeSheets.calls.length, 0);
assert.equal(checkedInHarness.context.takkenR6028CanonicalCell_(
  new Date('2026-04-09T15:00:00.000Z'), 'updatedAt'), '2026-04-10');
assert.equal(checkedInHarness.context.takkenR6028CanonicalCell_(
  new Date('2026-04-09T14:59:59.000Z'), 'updatedAt'), '2026-04-09');

// A date-only string and the diagnosed live Date object have the same semantic
// hash, but the patch requires the live Sheet value to remain a Date object.
const dateStringHarness = makeHarness({ specMode: 'checked-in' });
dateStringHarness.questionBank[targetIndex + 1][headers.indexOf('updatedAt')] = '2026-04-10';
assert.equal(
  dateStringHarness.context.takkenR6028FullRowSha256_(dateStringHarness.questionBank[targetIndex + 1], headers),
  dateStringHarness.context.TAKKEN_R6_028_RELEASE_SPEC_.expectedBeforeRuntimeRowSha256,
);
assert.throws(() => dateStringHarness.context.ADMIN_patchTakkenR6028DryRun_(), /updatedAt live type mismatch/);
const dateBoundaryHarness = makeHarness({ specMode: 'checked-in' });
dateBoundaryHarness.questionBank[targetIndex + 1][headers.indexOf('updatedAt')] = new Date('2026-04-09T14:59:59.000Z');
assert.throws(() => dateBoundaryHarness.context.ADMIN_patchTakkenR6028DryRun_(), /expected-before full-row hash mismatch/);
const displayMismatchHarness = makeHarness({ specMode: 'checked-in' });
displayMismatchHarness.db.getSheetByName('QuestionBank').displayTransform = (value, rowIndex, colIndex) => {
  if (rowIndex === targetIndex + 1 && colIndex === headers.indexOf('updatedAt')) return '2026/04/10';
  if (value instanceof Date) return new Date(value.getTime() + 9 * 60 * 60 * 1000).toISOString().slice(0, 10);
  return String(value ?? '');
};
assert.throws(() => displayMismatchHarness.context.ADMIN_patchTakkenR6028DryRun_(), /updatedAt display baseline mismatch/);

const explainLongHarness = makeHarness({ specMode: 'checked-in' });
explainLongHarness.questionBank[targetIndex + 1][headers.indexOf('explainLong')] = 'unexpected protected value';
assert.throws(() => explainLongHarness.context.ADMIN_patchTakkenR6028DryRun_(), /expected-before full-row hash mismatch/);

// The actual checked-in spec writes one stem cell in one atomic request; its
// choices, official-correct key, explanations, images, provenance, and status
// remain byte-for-byte unchanged. Its rollback restores the exact old row.
const checkedInApplyHarness = makeHarness({ specMode: 'checked-in' });
const checkedInApplied = checkedInApplyHarness.context.ADMIN_applyTakkenR6028_();
assert.equal(checkedInApplied.updated, 1);
assert.equal(checkedInApplied.fieldCount, 1);
assert.equal(checkedInApplyHarness.fakeSheets.calls.length, 1);
assert.equal(checkedInApplyHarness.fakeSheets.calls[0].body.requests.length, 1);
assert.equal(checkedInApplyHarness.fakeSheets.calls[0].body.requests[0].updateCells.range.startColumnIndex, headers.indexOf('stem'));
assertOnlyFieldsChanged(checkedInApplyHarness, 'after', ['stem']);
assert.equal(
  checkedInApplyHarness.context.takkenR6028Sha256_(rowsById(checkedInApplyHarness.questionBank).get(QID)[headers.indexOf('stem')]),
  '9f9907be1958fc9c649703194535907f5aea38f46cfc436766dc5c7dba470f76',
);
const checkedInRolledBack = checkedInApplyHarness.context.ADMIN_rollbackLatestTakkenR6028_();
assert.equal(checkedInRolledBack.restored, 1);
assertOnlyFieldsChanged(checkedInApplyHarness, 'before', ['stem']);
assert.equal(checkedInApplyHarness.fakeSheets.calls.length, 2);

// A Date-to-string mutation after the atomic stem write is not accepted as an
// equivalent post-state. No success receipt or second write is permitted.
const postDateTypeHarness = makeHarness({ specMode: 'checked-in' });
postDateTypeHarness.fakeSheets.afterBatch = () => {
  postDateTypeHarness.questionBank[targetIndex + 1][headers.indexOf('updatedAt')] = '2026-04-10';
};
assert.throws(() => postDateTypeHarness.context.ADMIN_applyTakkenR6028_(), /manual review|required|unknown\/partial/);
assert.equal(postDateTypeHarness.fakeSheets.calls.length, 1);

// Approved-fixture dry-run must be one target, 599 non-targets, no mutation.
const dryHarness = makeHarness();
const dry = dryHarness.context.ADMIN_patchTakkenR6028DryRun_();
assert.equal(dry.ok, true);
assert.equal(dry.matched, 1);
assert.equal(dry.wouldUpdate, 1);
assert.equal(dry.nonTargetCount, 599);
assertOnlyApprovedFieldsChanged(dryHarness, 'before');
assert.equal(dryHarness.fakeSheets.calls.length, 0);
assert.equal(dryHarness.db.getSheetByName('_QuestionBankR6028PatchBackup'), null);

// Apply changes only the synthetic stem field in one atomic call.
const applyHarness = makeHarness();
const applied = applyHarness.context.ADMIN_applyTakkenR6028_();
assert.equal(applied.mode, 'applied');
assert.equal(applied.updated, 1);
assert.equal(applied.fieldCount, 1);
assert.equal(applyHarness.fakeSheets.calls.length, 1);
assert.equal(applyHarness.fakeSheets.calls[0].body.requests.length, 1);
assertOnlyApprovedFieldsChanged(applyHarness, 'after');
for (const request of applyHarness.fakeSheets.calls[0].body.requests) {
  assert.ok(request.updateCells.range.startRowIndex >= 1);
  assert.equal('allSheets' in request.updateCells, false);
}
assert.equal(applyHarness.cacheClears, 1);
const backup = applyHarness.db.getSheetByName('_QuestionBankR6028PatchBackup');
assert.ok(backup);
assert.equal(backup.getLastRow(), 2);
assert.equal(backup.data[0].filter((header) => header === 'patchStatus').length, 1);
assert.equal(backup.data[1][2], 'applied');

// A second apply is stale/new-already-present and stops before API.
assert.throws(() => applyHarness.context.ADMIN_applyTakkenR6028_(), /expected-before full-row hash mismatch/);
assert.equal(applyHarness.fakeSheets.calls.length, 1);

// Duplicate qId and total-count mismatch are hard stops.
const duplicateHarness = makeHarness();
duplicateHarness.questionBank[1][0] = QID;
assert.throws(() => duplicateHarness.context.ADMIN_patchTakkenR6028DryRun_(), /duplicate qId/);
assert.equal(duplicateHarness.fakeSheets.calls.length, 0);
const countHarness = makeHarness();
countHarness.questionBank.pop();
assert.throws(() => countHarness.context.ADMIN_patchTakkenR6028DryRun_(), /exactly 600/);

// Full-row expected-before protects choices/correct and every other column.
const staleHarness = makeHarness();
staleHarness.questionBank[targetIndex + 1][headers.indexOf('explainShort')] += ' drift';
assert.throws(() => staleHarness.context.ADMIN_patchTakkenR6028DryRun_(), /expected-before full-row hash mismatch/);

// Reorder between initial plan and prewrite reread is fail-closed.
const reorderHarness = makeHarness();
reorderHarness.setFlushHook(() => {
  const rows = reorderHarness.questionBank.slice(1).reverse();
  reorderHarness.questionBank.splice(1, rows.length, ...rows);
});
assert.throws(() => reorderHarness.context.ADMIN_applyTakkenR6028_(), /row order changed|target row changed/);
assert.equal(reorderHarness.fakeSheets.calls.length, 0);
assert.equal(reorderHarness.db.getSheetByName('_QuestionBankR6028PatchBackup').data[1][2], 'manual_review');

// API rejection means no write; partial/unknown state is never reported as success.
const rejectHarness = makeHarness();
rejectHarness.fakeSheets.mode = 'throw';
assert.throws(() => rejectHarness.context.ADMIN_applyTakkenR6028_(), /no QuestionBank mutation verified/);
assertOnlyApprovedFieldsChanged(rejectHarness, 'before');
assert.equal(rejectHarness.db.getSheetByName('_QuestionBankR6028PatchBackup').data[1][2], 'not_applied');

const partialHarness = makeHarness();
partialHarness.fakeSheets.mode = 'partialThrow';
assert.throws(() => partialHarness.context.ADMIN_applyTakkenR6028_(), /unknown partial response/);
assert.equal(partialHarness.db.getSheetByName('_QuestionBankR6028PatchBackup').data[1][2], 'rollback_failed');

// Bad API response after a complete write triggers exact automatic rollback.
const replyHarness = makeHarness();
replyHarness.fakeSheets.mode = 'badReply';
assert.throws(() => replyHarness.context.ADMIN_applyTakkenR6028_(), /automatic rollback verified/);
assertOnlyApprovedFieldsChanged(replyHarness, 'before');
assert.equal(replyHarness.fakeSheets.calls.length, 2);
assert.equal(replyHarness.db.getSheetByName('_QuestionBankR6028PatchBackup').data[1][2], 'rolled_back');

// Manual rollback verifies the saved post-apply full/non-target/order baseline.
const rollbackHarness = makeHarness();
rollbackHarness.context.ADMIN_applyTakkenR6028_();
const rollbackDry = rollbackHarness.context.ADMIN_rollbackLatestTakkenR6028DryRun_();
assert.equal(rollbackDry.mode, 'rollback-dry-run');
assert.equal(rollbackDry.restored, 1);
const rolledBack = rollbackHarness.context.ADMIN_rollbackLatestTakkenR6028_();
assert.equal(rolledBack.mode, 'rolled-back');
assert.equal(rolledBack.restored, 1);
assertOnlyApprovedFieldsChanged(rollbackHarness, 'before');
assert.equal(rollbackHarness.fakeSheets.calls.length, 2);
assert.equal(rollbackHarness.cacheClears, 2);

// Manual rollback rejects protected Date-to-string drift before another API
// call, although date-only semantic hashing intentionally yields the same hash.
const rollbackDateTypeHarness = makeHarness({ specMode: 'checked-in' });
rollbackDateTypeHarness.context.ADMIN_applyTakkenR6028_();
rollbackDateTypeHarness.questionBank[targetIndex + 1][headers.indexOf('updatedAt')] = '2026-04-10';
assert.throws(() => rollbackDateTypeHarness.context.ADMIN_rollbackLatestTakkenR6028DryRun_(), /updatedAt live type mismatch|drift blocks rollback/);
assert.equal(rollbackDateTypeHarness.fakeSheets.calls.length, 1);

// Non-target drift blocks rollback before any second API call.
const driftHarness = makeHarness();
driftHarness.context.ADMIN_applyTakkenR6028_();
driftHarness.questionBank[1][headers.indexOf('stem')] += ' non-target drift';
assert.throws(() => driftHarness.context.ADMIN_rollbackLatestTakkenR6028DryRun_(), /drift blocks rollback/);
assert.equal(driftHarness.fakeSheets.calls.length, 1);

// Maintenance, DB identity, Advanced Service, and strict cache are fail-closed.
const windowHarness = makeHarness();
windowHarness.props.set('TAKKEN_R6_028_MAINTENANCE_WINDOW', 'CLOSED');
assert.throws(() => windowHarness.context.ADMIN_applyTakkenR6028_(), /maintenance window is not OPEN/);
assert.equal(windowHarness.fakeSheets.calls.length, 0);

const dbHarness = makeHarness();
dbHarness.setFlushHook(() => dbHarness.props.set('DB_SPREADSHEET_ID', 'changed-db'));
assert.throws(() => dbHarness.context.ADMIN_applyTakkenR6028_(), /DB_SPREADSHEET_ID changed/);
assert.equal(dbHarness.fakeSheets.calls.length, 0);

const serviceHarness = makeHarness();
serviceHarness.context.Sheets = undefined;
assert.throws(() => serviceHarness.context.ADMIN_applyTakkenR6028_(), /Advanced Sheets service unavailable/);
assertOnlyApprovedFieldsChanged(serviceHarness, 'before');

const cacheHarness = makeHarness();
cacheHarness.context.clearAllCache_ = () => { throw new Error('strict cache failure'); };
assert.throws(() => cacheHarness.context.ADMIN_applyTakkenR6028_(), /rollback failed/);
assertOnlyApprovedFieldsChanged(cacheHarness, 'before');
assert.equal(cacheHarness.fakeSheets.calls.length, 2);

console.log(JSON.stringify({
  ok: true,
  tests: 93,
  checkedInReleaseStatus: checkedInHarness.context.TAKKEN_R6_028_RELEASE_SPEC_.releaseStatus,
  checkedInPayloadFields: checkedInDry.fieldCount,
  dryRunMatched: dry.matched,
  dryRunNonTarget: dry.nonTargetCount,
  approvedFixtureUpdated: applied.updated,
  rollbackRestored: rolledBack.restored,
  mutationApi: 'Sheets.Spreadsheets.batchUpdate/updateCells',
}));
