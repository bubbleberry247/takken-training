import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import fs from 'node:fs';
import vm from 'node:vm';

const sourceText = fs.readFileSync(new URL('../src/patchStatementLabels.gs', import.meta.url), 'utf8');
const csvText = fs.readFileSync(new URL('../data/takken_questionbank_import.csv', import.meta.url), 'utf8');
const ledgerText = fs.readFileSync(new URL('../data/statement_label_corrections.csv', import.meta.url), 'utf8');

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
  if (field !== '' || row.length > 0) { row.push(field); rows.push(row); }
  const headers = rows.shift().map((header) => header.replace(/^\uFEFF/, ''));
  return { headers, rows: rows.filter((values) => values.length > 1 || values[0]) };
}

class FakeRange {
  constructor(sheet, row, col, numRows = 1, numCols = 1) { this.sheet = sheet; this.row = row; this.col = col; this.numRows = numRows; this.numCols = numCols; }
  getValues() { return Array.from({ length: this.numRows }, (_, r) => Array.from({ length: this.numCols }, (_, c) => (this.sheet.data[this.row - 1 + r] || [])[this.col - 1 + c] ?? '')); }
  setValues(values) {
    const requiredRows = this.row - 1 + values.length;
    const requiredCols = this.col - 1 + Math.max(0, ...values.map((value) => value.length));
    while (this.sheet.data.length < requiredRows) this.sheet.data.push([]);
    for (const row of this.sheet.data) while (row.length < requiredCols) row.push('');
    for (let r = 0; r < values.length; r += 1) for (let c = 0; c < values[r].length; c += 1) this.sheet.data[this.row - 1 + r][this.col - 1 + c] = values[r][c];
  }
  setValue(value) { this.setValues([[value]]); }
  setFrozenRows() {}
}

class FakeSheet {
  constructor(data, sheetId) { this.data = data; this.sheetId = sheetId; }
  getDataRange() { return new FakeRange(this, 1, 1, this.data.length, this.getLastColumn()); }
  getLastRow() { return this.data.length; }
  getLastColumn() { return this.data[0]?.length || 1; }
  getRange(row, col, numRows = 1, numCols = 1) { return new FakeRange(this, row, col, numRows, numCols); }
  getSheetId() { return this.sheetId; }
  setFrozenRows() {}
}

class FakeDb {
  constructor(questionBank) { this.id = 'fake-db-id'; this.sheets = new Map([['QuestionBank', new FakeSheet(questionBank, 101)]]); }
  getId() { return this.id; }
  getSheetByName(name) { return this.sheets.get(name) || null; }
  insertSheet(name) { const sheet = new FakeSheet([[]], 500 + this.sheets.size); this.sheets.set(name, sheet); return sheet; }
}

const parsed = parseCsv(csvText);
const ledger = parseCsv(ledgerText);
const headers = parsed.headers;
const stemIndex = headers.indexOf('stem');
const correctIndex = headers.indexOf('correct');
const choiceIndices = ['choiceA', 'choiceB', 'choiceC', 'choiceD', 'choiceE'].map((key) => headers.indexOf(key));
const targetIds = new Set(ledger.rows.map((row) => row[0]));
const ledgerById = new Map(ledger.rows.map((row) => [row[0], Object.fromEntries(ledger.headers.map((key, i) => [key, row[i]]))]));
assert.equal(targetIds.size, 51);
assert.equal(targetIds.has('R6takken-028'), false);
assert.equal(targetIds.has('R3atakken-038'), false);
assert.equal(targetIds.has('R3btakken-038'), false);

function sha(value) { return crypto.createHash('sha256').update(String(value), 'utf8').digest('hex'); }
function byQId(questionBank) { return new Map(questionBank.slice(1).map((row) => [row[0], row])); }

function makeOldQuestionBank() {
  const questionBank = [headers, ...parsed.rows.map((values) => headers.map((_, i) => values[i] || ''))];
  for (const row of questionBank.slice(1)) {
    if (!targetIds.has(row[0])) continue;
    const spec = ledgerById.get(row[0]);
    const corrected = row[stemIndex];
    row[stemIndex] = corrected.replace(/\n\n[ア-エ]\u3000/g, '');
    assert.equal(sha(row[stemIndex]), spec.expected_before_stem_sha256, `old fixture hash: ${row[0]}`);
  }
  return questionBank;
}

function makeHarness(options = {}) {
  const questionBank = makeOldQuestionBank();
  const db = new FakeDb(questionBank);
  const props = new Map([['DB_SPREADSHEET_ID', 'fake-db-id'], ['TAKKEN_STATEMENT_LABEL_PATCH_MAINTENANCE_WINDOW', 'OPEN']]);
  let flushHook = null;
  let cacheClears = 0;
  const logger = { logs: [], log(value) { this.logs.push(String(value)); } };
  const fakeSheets = {
    calls: [],
    mode: options.mode || 'normal',
    beforeBatch: null,
    Spreadsheets: {
      batchUpdate(body, spreadsheetId) {
        fakeSheets.calls.push({ body, spreadsheetId });
        assert.equal(spreadsheetId, 'fake-db-id', 'API must use fixed plan DB ID');
        if (fakeSheets.beforeBatch) { const hook = fakeSheets.beforeBatch; fakeSheets.beforeBatch = null; hook(); }
        const replies = [];
        for (let i = 0; i < body.requests.length; i += 1) {
          const request = body.requests[i].findReplace;
          assert.equal('allSheets' in request, false, 'range/allSheets oneof contract');
          assert.equal(request.matchCase, true);
          assert.equal(request.matchEntireCell, true);
          assert.equal(request.searchByRegex, false);
          assert.equal(request.includeFormulas, false);
          assert.equal(request.range.sheetId, 101);
          assert.equal(request.range.startColumnIndex, stemIndex);
          assert.equal(request.range.endColumnIndex, stemIndex + 1);
          assert.equal('startRowIndex' in request.range, false);
          let occurrencesChanged = 0;
          if (fakeSheets.mode !== 'zeroReply' && fakeSheets.mode !== 'badReply') {
            for (const row of questionBank.slice(1)) {
              if (row[stemIndex] === request.find) { row[stemIndex] = request.replacement; occurrencesChanged += 1; }
            }
          }
          if (fakeSheets.mode === 'partialThrow' && i === 0) throw new Error('simulated partial response');
          if (fakeSheets.mode === 'throw') throw new Error('simulated batch failure');
          replies.push({ findReplace: { occurrencesChanged, valuesChanged: occurrencesChanged } });
        }
        if (fakeSheets.mode === 'badReply') return { replies: replies.slice(0, 50) };
        return { replies };
      },
    },
  };
  let uuid = 0;
  const context = {
    console,
    Logger: logger,
    HEADERS: { QuestionBank: headers },
    SHEETS: { QuestionBank: 'QuestionBank' },
    Utilities: {
      DigestAlgorithm: { SHA_256: 'sha256' },
      Charset: { UTF_8: 'utf8' },
      computeDigest(_algorithm, value) { return Array.from(crypto.createHash('sha256').update(String(value), 'utf8').digest()); },
      getUuid() { uuid += 1; return `statement-label-patch-${uuid}`; },
    },
    SpreadsheetApp: { flush() { if (flushHook) { const hook = flushHook; flushHook = null; hook(); } } },
    LockService: { getScriptLock() { return { waitLock() {}, releaseLock() {} }; } },
    Sheets: fakeSheets,
    _questionsCache: [{ qId: 'cached' }],
    _questionsCacheTs: 123,
    normalizeHeader_(value, index) { const text = String(value ?? ''); return index === 0 ? text.replace(/^\uFEFF/, '').trim() : text.trim(); },
  };
  vm.createContext(context);
  vm.runInContext(sourceText, context, { filename: 'patchStatementLabels.gs' });
  context.getDbId_ = () => props.get('DB_SPREADSHEET_ID') || '';
  context.getScriptProps_ = () => ({ getProperty(key) { return props.get(key) || null; } });
  context.getDb_ = () => db;
  context.clearAllCache_ = () => {
    cacheClears += 1;
    if (options.cacheFailure) throw new Error('simulated strict cache invalidation failure');
    context._questionsCache = null;
    context._questionsCacheTs = 0;
    context._questionsCacheVersion = '';
  };
  return {
    context, db, questionBank, fakeSheets, logger, props,
    setFlushHook(hook) { flushHook = hook; },
    get cacheClears() { return cacheClears; },
  };
}

function assertOnlyStemChanges(harness, beforeById) {
  const current = byQId(harness.questionBank);
  assert.deepEqual([...current.keys()].sort(), [...beforeById.keys()].sort());
  for (const [qId, before] of beforeById) {
    const after = current.get(qId);
    if (!targetIds.has(qId)) { assert.deepEqual(after, before, `non-target changed: ${qId}`); continue; }
    for (let i = 0; i < before.length; i += 1) if (i !== stemIndex) assert.equal(after[i], before[i], `${qId} non-stem changed`);
    assert.equal(after[correctIndex], before[correctIndex], `${qId} correct changed`);
    for (const index of choiceIndices) assert.equal(after[index], before[index], `${qId} choice changed`);
  }
}

// Static allowlist and dry-run contract.
const dryHarness = makeHarness();
const q38Before = new Map([...byQId(dryHarness.questionBank)].filter(([qId]) => ['R3atakken-038', 'R3btakken-038'].includes(qId)).map(([qId, row]) => [qId, row[stemIndex]]));
const beforeDry = new Map([...byQId(dryHarness.questionBank)].map(([qId, row]) => [qId, row.slice()]));
const dry = dryHarness.context.ADMIN_patchTakkenStatementLabelsDryRun_();
assert.equal(dry.ok, true);
assert.equal(dry.mode, 'dry-run');
assert.equal(dry.matched, 51);
assert.equal(dry.wouldUpdate, 51);
assert.equal(dry.nonTargetCount, 549);
assert.equal(dryHarness.fakeSheets.calls.length, 0);
assert.equal(dryHarness.db.getSheetByName('_QuestionBankStatementLabelPatchBackup'), null);
assert.deepEqual([...byQId(dryHarness.questionBank)].map(([, row]) => row), [...beforeDry.values()]);

// Successful apply: one 51-request atomic batch, 51 updates, all protected
// columns/non-target rows unchanged, Q38 untouched, and durable backup.
const applyHarness = makeHarness();
const beforeApply = new Map([...byQId(applyHarness.questionBank)].map(([qId, row]) => [qId, row.slice()]));
const applied = applyHarness.context.ADMIN_applyTakkenStatementLabels_();
assert.equal(applied.ok, true);
assert.equal(applied.matched, 51);
assert.equal(applied.updated, 51);
assert.equal(applied.nonTargetCount, 549);
assert.equal(applyHarness.fakeSheets.calls.length, 1);
assert.equal(applyHarness.fakeSheets.calls[0].body.requests.length, 51);
assert.equal(applyHarness.cacheClears, 1);
assert.equal(applyHarness.context._questionsCache, null);
assertOnlyStemChanges(applyHarness, beforeApply);
const appliedRows = byQId(applyHarness.questionBank);
for (const [qId, spec] of ledgerById) assert.equal(sha(appliedRows.get(qId)[stemIndex]), spec.replacement_stem_sha256, `replacement state: ${qId}`);
for (const [qId, stem] of q38Before) assert.equal(appliedRows.get(qId)[stemIndex], stem, `Q38 must remain untouched: ${qId}`);
const backup = applyHarness.db.getSheetByName('_QuestionBankStatementLabelPatchBackup');
assert.ok(backup);
assert.equal(backup.getLastRow(), 52);
assert.equal(backup.data[0].includes('patchStatus'), true);
assert.equal(backup.data[0].filter((header) => header === 'status').length, 1);

// Rollback dry-run/apply uses the stored post-state and the same atomic
// reverse requests, then restores the exact old state.
const rollbackDry = applyHarness.context.ADMIN_rollbackLatestTakkenStatementLabelsDryRun_();
assert.equal(rollbackDry.ok, true);
assert.equal(rollbackDry.wouldRestore, 51);
const rolledBack = applyHarness.context.ADMIN_rollbackLatestTakkenStatementLabels_();
assert.equal(rolledBack.ok, true);
assert.equal(rolledBack.restored, 51);
assert.equal(applyHarness.fakeSheets.calls.length, 2);
assert.equal(applyHarness.cacheClears, 2);
assert.deepEqual([...byQId(applyHarness.questionBank)].map(([, row]) => row), [...beforeApply.values()]);

// Fail-closed guards: duplicate old, replacement already present, row reorder
// before API, zero occurrences, partial/unknown response, and strict cache
// failure must never be reported as a successful 51-row update.
const duplicateHarness = makeHarness();
duplicateHarness.questionBank[1][stemIndex] = [...ledgerById.values()][0].expected_before_stem_sha256;
// Replace with the real old stem from the target, without exposing text in output.
duplicateHarness.questionBank[1][stemIndex] = byQId(makeOldQuestionBank()).get([...targetIds][0])[stemIndex];
assert.throws(() => duplicateHarness.context.ADMIN_patchTakkenStatementLabelsDryRun_(), /occur exactly once/);
assert.equal(duplicateHarness.fakeSheets.calls.length, 0);

const existingNewHarness = makeHarness();
const firstTarget = [...targetIds][0];
const correctedFirst = parsed.rows.find((row) => row[0] === firstTarget)[stemIndex];
existingNewHarness.questionBank[1][stemIndex] = correctedFirst;
assert.throws(() => existingNewHarness.context.ADMIN_patchTakkenStatementLabelsDryRun_(), /already exists/);
assert.equal(existingNewHarness.fakeSheets.calls.length, 0);

const reorderHarness = makeHarness();
reorderHarness.setFlushHook(() => reorderHarness.questionBank.splice(1, reorderHarness.questionBank.length - 1, ...reorderHarness.questionBank.slice(1).reverse()));
assert.throws(() => reorderHarness.context.ADMIN_applyTakkenStatementLabels_(), /manual review|changed between backup/);
assert.equal(reorderHarness.fakeSheets.calls.length, 0, 'row reorder before API must fail closed');

const zeroHarness = makeHarness({ mode: 'zeroReply' });
assert.throws(() => zeroHarness.context.ADMIN_applyTakkenStatementLabels_(), /no QuestionBank mutation verified/);
assert.equal(zeroHarness.fakeSheets.calls.length, 1);

const partialHarness = makeHarness({ mode: 'partialThrow' });
assert.throws(() => partialHarness.context.ADMIN_applyTakkenStatementLabels_(), /partial|manual review/);
assert.equal(partialHarness.fakeSheets.calls.length, 1);

const cacheFailureHarness = makeHarness({ cacheFailure: true });
assert.throws(() => cacheFailureHarness.context.ADMIN_applyTakkenStatementLabels_(), /rollback failed|manual review/);
assert.equal(cacheFailureHarness.fakeSheets.calls.length, 2, 'strict cache failure must trigger exact reverse batch attempt');

console.log(JSON.stringify({
  ok: true,
  tests: 51 + 51 + 51 + 8,
  dryRun: { matched: dry.matched, wouldUpdate: dry.wouldUpdate, nonTargetCount: dry.nonTargetCount },
  applied: { matched: applied.matched, updated: applied.updated },
  rollback: { restored: rolledBack.restored },
  failureModes: ['duplicate-old', 'new-already-present', 'row-reorder', 'zero-occurrences', 'partial-response', 'strict-cache-failure'],
}));
