import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import fs from 'node:fs';
import vm from 'node:vm';

const sourceText = fs.readFileSync(new URL('../src/patchR3Q38.gs', import.meta.url), 'utf8');
const csvText = fs.readFileSync(new URL('../data/takken_questionbank_import.csv', import.meta.url), 'utf8');
const manifest = JSON.parse(fs.readFileSync(new URL('../src/appsscript.json', import.meta.url), 'utf8'));

function parseCsv(text) {
  const rows = [];
  let row = [];
  let field = '';
  let quoted = false;
  for (let i = 0; i < text.length; i += 1) {
    const ch = text[i];
    if (quoted) {
      if (ch === '"') {
        if (text[i + 1] === '"') {
          field += '"';
          i += 1;
        } else quoted = false;
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
  constructor(sheet, row, col, numRows = 1, numCols = 1) {
    this.sheet = sheet;
    this.row = row;
    this.col = col;
    this.numRows = numRows;
    this.numCols = numCols;
  }

  getValues() {
    return Array.from({ length: this.numRows }, (_, r) =>
      Array.from({ length: this.numCols }, (_, c) => {
        const source = this.sheet.data[this.row - 1 + r] || [];
        return source[this.col - 1 + c] ?? '';
      }),
    );
  }

  setValues(values) {
    const requiredRows = this.row - 1 + values.length;
    const requiredCols = this.col - 1 + Math.max(0, ...values.map((value) => value.length));
    while (this.sheet.data.length < requiredRows) this.sheet.data.push([]);
    for (const source of this.sheet.data) while (source.length < requiredCols) source.push('');
    for (let r = 0; r < values.length; r += 1) {
      for (let c = 0; c < values[r].length; c += 1) {
        this.sheet.data[this.row - 1 + r][this.col - 1 + c] = values[r][c];
      }
    }
  }

  setValue(value) { this.setValues([[value]]); }
  setFrozenRows() {}
}

class FakeSheet {
  constructor(data, sheetId = 101) { this.data = data; this.sheetId = sheetId; }
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
  insertSheet(name) {
    const sheet = new FakeSheet([[]], 202);
    this.sheets.set(name, sheet);
    return sheet;
  }
}

const parsed = parseCsv(csvText);
const headers = parsed.headers;
const targetIds = new Set(['R3atakken-038', 'R3btakken-038']);
const stemIndex = headers.indexOf('stem');
const correctIndex = headers.indexOf('correct');
const choiceIndices = ['choiceA', 'choiceB', 'choiceC', 'choiceD', 'choiceE'].map((key) => headers.indexOf(key));

function makeOldQuestionBank() {
  const questionBank = [headers, ...parsed.rows.map((values) => headers.map((_, i) => values[i] || ''))];
  for (const row of questionBank.slice(1)) {
    if (!targetIds.has(row[0])) continue;
    row[stemIndex] = row[stemIndex]
      .replace(/\r\n/g, '\n')
      .replace(/\r/g, '\n')
      .replace(/\n\nア\u3000/, '')
      .replace(/\n[イウエ]\u3000/g, '');
  }
  return questionBank;
}

function byQId(questionBank) {
  return new Map(questionBank.slice(1).map((row) => [row[0], row]));
}

function makeHarness() {
  const questionBank = makeOldQuestionBank();
  const db = new FakeDb(questionBank);
  const props = new Map([['DB_SPREADSHEET_ID', 'fake-db-id'], ['TAKKEN_R3Q38_MAINTENANCE_WINDOW', 'OPEN']]);
  let flushHook = null;
  const logger = { logs: [], log(value) { this.logs.push(String(value)); } };
  const fakeSheets = {
    calls: [],
    mode: 'normal',
    beforeBatch: null,
    Spreadsheets: {
      batchUpdate(body, spreadsheetId) {
        fakeSheets.calls.push({ body, spreadsheetId });
        assert.equal(spreadsheetId, 'fake-db-id');
        if (fakeSheets.beforeBatch) {
          const hook = fakeSheets.beforeBatch;
          fakeSheets.beforeBatch = null;
          hook();
        }
        const replies = [];
        for (let i = 0; i < body.requests.length; i += 1) {
          const request = body.requests[i].findReplace;
          assert.equal('allSheets' in request, false, 'range and allSheets are mutually exclusive; range-only is required');
          assert.equal(request.matchCase, true);
          assert.equal(request.matchEntireCell, true);
          assert.equal(request.searchByRegex, false);
          assert.equal(request.includeFormulas, false);
          assert.equal(request.range.sheetId, 101);
          assert.equal(request.range.startColumnIndex, stemIndex);
          assert.equal(request.range.endColumnIndex, stemIndex + 1);
          assert.equal('startRowIndex' in request.range, false, 'QuestionBank writes must not use row indexes');
          let occurrencesChanged = 0;
          if (fakeSheets.mode !== 'zeroReply' && fakeSheets.mode !== 'badReply') {
            for (const row of questionBank.slice(1)) {
              if (row[stemIndex] === request.find) {
                row[stemIndex] = request.replacement;
                occurrencesChanged += 1;
              }
            }
          }
          if (fakeSheets.mode === 'partialThrow' && i === 0) {
            throw new Error('simulated partial/unknown response after first request');
          }
          if (fakeSheets.mode === 'throw') throw new Error('simulated batch failure');
          replies.push({ findReplace: { occurrencesChanged, valuesChanged: occurrencesChanged } });
        }
        if (fakeSheets.mode === 'badReply') return { replies: replies.slice(0, 1) };
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
      getUuid() { uuid += 1; return `test-patch-id-${uuid}`; },
    },
    SpreadsheetApp: { flush() { if (flushHook) { const hook = flushHook; flushHook = null; hook(); } } },
    LockService: {
      waits: 0,
      releases: 0,
      getScriptLock() {
        return {
          waitLock() { context.LockService.waits += 1; },
          releaseLock() { context.LockService.releases += 1; },
        };
      },
    },
    PropertiesService: {},
    Sheets: fakeSheets,
    _questionsCache: [{ qId: 'cached' }],
    _questionsCacheTs: 123,
    normalizeHeader_(value, index) {
      const text = String(value ?? '');
      return index === 0 ? text.replace(/^\uFEFF/, '').trim() : text.trim();
    },
  };
  vm.createContext(context);
  vm.runInContext(sourceText, context, { filename: 'patchR3Q38.gs' });
  context.getDbId_ = () => props.get('DB_SPREADSHEET_ID') || '';
  context.getScriptProps_ = () => ({ getProperty(key) { return props.get(key) || null; } });
  context.getDb_ = () => db;
  context.getSheet_ = (name) => {
    const sheet = db.getSheetByName(name);
    if (!sheet) throw new Error(`missing sheet: ${name}`);
    return sheet;
  };
  let cacheClears = 0;
  context.clearAllCache_ = () => {
    cacheClears += 1;
    context._questionsCache = null;
    context._questionsCacheTs = 0;
    context._questionsCacheVersion = '';
  };
  context.getCache_ = () => ({ remove() {} });
  return {
    context,
    db,
    questionBank,
    beforeSnapshot: JSON.stringify(questionBank),
    targetBefore: new Map([...byQId(questionBank)].filter(([qId]) => targetIds.has(qId)).map(([qId, row]) => [qId, row.slice()])),
    fakeSheets,
    logger,
    props,
    setFlushHook(hook) { flushHook = hook; },
    get cacheClears() { return cacheClears; },
  };
}

function assertAllNonStemCellsUnchanged(harness, beforeById) {
  const current = byQId(harness.questionBank);
  assert.deepEqual([...current.keys()].sort(), [...beforeById.keys()].sort(), 'qId inventory must be unchanged');
  for (const [qId, before] of beforeById) {
    const after = current.get(qId);
    if (!targetIds.has(qId)) {
      assert.deepEqual(after, before, `non-target row changed: ${qId}`);
      continue;
    }
    for (let i = 0; i < before.length; i += 1) {
      if (i !== stemIndex) assert.equal(after[i], before[i], `${qId} non-stem column ${i} changed`);
    }
    assert.equal(after[correctIndex], before[correctIndex], `${qId} correct changed`);
    for (const index of choiceIndices) assert.equal(after[index], before[index], `${qId} choice changed`);
  }
}

// Contract/static checks: the write path is Advanced Sheets only, and GAS
// editor entry points are argument-free.
assert.ok(manifest.dependencies?.enabledAdvancedServices?.some((service) =>
  service.userSymbol === 'Sheets' && service.serviceId === 'sheets' && service.version === 'v4'));
assert.match(sourceText, /function ADMIN_patchTakkenR3Q38DryRun_\(\)/);
assert.match(sourceText, /function ADMIN_applyTakkenR3Q38_\(\)/);
assert.match(sourceText, /function ADMIN_rollbackLatestTakkenR3Q38DryRun_\(\)/);
assert.match(sourceText, /function ADMIN_rollbackLatestTakkenR3Q38_\(\)/);
assert.match(sourceText, /matchEntireCell: true/);
assert.doesNotMatch(sourceText, /getRange\(target\.sheetRow/);
assert.doesNotMatch(sourceText, /function takkenR3Q38RestoreRows_/);
assert.doesNotMatch(sourceText, /sheet\.clear\(/);

// Dry-run is no-argument and must not create a backup or mutate QuestionBank.
const dryHarness = makeHarness();
const dryBefore = new Map([...byQId(dryHarness.questionBank)].map(([qId, row]) => [qId, row.slice()]));
const dry = dryHarness.context.ADMIN_patchTakkenR3Q38DryRun_();
assert.equal(dry.ok, true);
assert.equal(dry.mode, 'dry-run');
assert.equal(dry.matched, 2);
assert.equal(dry.wouldUpdate, 2);
assert.equal(dry.nonTargetCount, 598);
assert.equal(JSON.stringify(dryHarness.questionBank), dryHarness.beforeSnapshot);
assert.equal(dryHarness.db.getSheetByName('_QuestionBankPatchBackup'), null);
assert.equal(dryHarness.logger.logs.length, 1);
assert.doesNotMatch(dryHarness.logger.logs[0], /宅地建物取引業者/);

// Apply with an injected row reorder immediately before the API request.  The
// target cells must still be found by exact stem, while all non-stem content
// remains unchanged and exactly two API requests are issued.
const applyHarness = makeHarness();
const applyBefore = new Map([...byQId(applyHarness.questionBank)].map(([qId, row]) => [qId, row.slice()]));
applyHarness.fakeSheets.beforeBatch = () => {
  const body = applyHarness.questionBank.slice(1).reverse();
  applyHarness.questionBank.splice(1, applyHarness.questionBank.length - 1, ...body);
};
const applied = applyHarness.context.ADMIN_applyTakkenR3Q38_();
assert.equal(applied.ok, true);
assert.equal(applied.mode, 'applied');
assert.equal(applied.matched, 2);
assert.equal(applied.updated, 2);
assert.equal(applyHarness.fakeSheets.calls.length, 1);
assert.equal(applyHarness.fakeSheets.calls[0].body.requests.length, 2);
assert.deepEqual(applyHarness.fakeSheets.calls[0].body.requests.map((request) => request.findReplace.find).length, 2);
for (const request of applyHarness.fakeSheets.calls[0].body.requests) {
  const findReplace = request.findReplace;
  assert.equal('allSheets' in findReplace, false, 'API oneof contract: allSheets must be absent when range is present');
  assert.ok(findReplace.range, 'API oneof contract: range must be present');
  assert.equal(findReplace.range.sheetId, 101);
  assert.equal(findReplace.range.startColumnIndex, stemIndex);
  assert.equal(findReplace.range.endColumnIndex, stemIndex + 1);
  assert.equal(findReplace.matchEntireCell, true);
}
assert.equal(applyHarness.cacheClears, 1);
assert.equal(applyHarness.context._questionsCache, null);
assert.equal(applyHarness.context._questionsCacheTs, 0);
assertAllNonStemCellsUnchanged(applyHarness, applyBefore);
const backup = applyHarness.db.getSheetByName('_QuestionBankPatchBackup');
assert.ok(backup, 'apply must create durable backup sheet');
assert.equal(backup.getLastRow(), 3);
const backupHeaders = backup.data[0];
assert.equal(backupHeaders.includes('targetQId'), true);
assert.equal(backupHeaders.includes('stem'), true);
assert.equal(backupHeaders.includes('patchStatus'), true);
assert.equal(backupHeaders.filter((header) => header === 'status').length, 1, 'backup status header must not be duplicated');
const backupIndex = Object.fromEntries(backupHeaders.map((header, index) => [header, index]));
assert.equal(backup.data.slice(1).every((row) => row[backupIndex.dbSpreadsheetId] === 'fake-db-id'), true);
assert.equal(backup.data.slice(1).every((row) => row[backupIndex.beforeInventorySha256]), true);
assert.equal(backup.data.slice(1).every((row) => row[backupIndex.afterInventorySha256]), true);
assert.equal(backup.data.slice(1).every((row) => row[backupIndex.afterNonTargetInventorySha256]), true);
assert.equal(applyHarness.db.getSheetByName('_QuestionBankPatchBackup').data.slice(1).every((row) => row[2] === 'applied'), true);

// New-already-present / expected-before is a hard stop; no second API write.
assert.throws(() => applyHarness.context.ADMIN_applyTakkenR3Q38_(), /expected-before stem hash mismatch|replacement stem already exists/);
assert.equal(applyHarness.fakeSheets.calls.length, 1);

// Stored post-apply full/non-target inventory hashes block rollback after an
// unrelated QuestionBank edit, even if the target rows still look rollbackable.
const driftHarness = makeHarness();
driftHarness.context.ADMIN_applyTakkenR3Q38_();
const driftRow = driftHarness.questionBank.slice(1).find((row) => !targetIds.has(row[0]));
driftRow[stemIndex] = `${driftRow[stemIndex]} [manual drift]`;
assert.throws(() => driftHarness.context.ADMIN_rollbackLatestTakkenR3Q38DryRun_(), /post-apply inventory drift/);
assert.equal(driftHarness.fakeSheets.calls.length, 1, 'drift must block rollback before API');

// Duplicate old stem in a non-target row is detected before any write.
const duplicateHarness = makeHarness();
const duplicateOld = duplicateHarness.targetBefore.get('R3atakken-038')[stemIndex];
duplicateHarness.questionBank[1][stemIndex] = duplicateOld;
assert.throws(() => duplicateHarness.context.ADMIN_patchTakkenR3Q38DryRun_(), /old stem must occur exactly once/);
assert.equal(duplicateHarness.fakeSheets.calls.length, 0);

// A replacement that is already present is also a hard stop.
const newFirstHarness = makeHarness();
const firstPlan = newFirstHarness.context.takkenR3Q38BuildPlan_();
const nonTargetRow = newFirstHarness.questionBank.slice(1).find((row) => !targetIds.has(row[0]));
nonTargetRow[stemIndex] = firstPlan.targets[0].afterStem;
assert.throws(() => newFirstHarness.context.ADMIN_patchTakkenR3Q38DryRun_(), /replacement stem already exists/);

// A target already in the new state is the separate expected-before stop.
const targetNewHarness = makeHarness();
const targetNewPlan = targetNewHarness.context.takkenR3Q38BuildPlan_();
targetNewHarness.questionBank.find((row) => row[0] === 'R3atakken-038')[stemIndex] = targetNewPlan.targets[0].afterStem;
assert.throws(() => targetNewHarness.context.ADMIN_patchTakkenR3Q38DryRun_(), /expected-before stem hash mismatch/);

// A simulated partial/unknown response must not trigger an unsafe row-based
// rollback. The state is reported partial and left for manual review.
const partialHarness = makeHarness();
partialHarness.fakeSheets.mode = 'partialThrow';
assert.throws(() => partialHarness.context.ADMIN_applyTakkenR3Q38_(), /state is partial/);
const partialRows = byQId(partialHarness.questionBank);
assert.notEqual(partialRows.get('R3atakken-038')[stemIndex], partialHarness.targetBefore.get('R3atakken-038')[stemIndex]);
assert.equal(partialRows.get('R3btakken-038')[stemIndex], partialHarness.targetBefore.get('R3btakken-038')[stemIndex]);
assert.equal(partialHarness.db.getSheetByName('_QuestionBankPatchBackup').data[1][2], 'partial');
assert.equal(partialHarness.cacheClears, 0);

// Rollback is another two-request exact batch, and uses the latest applied
// backup without depending on its original source row numbers.
const rollbackHarness = makeHarness();
const rollbackBefore = new Map([...byQId(rollbackHarness.questionBank)].map(([qId, row]) => [qId, row.slice()]));
const rollbackApplied = rollbackHarness.context.ADMIN_applyTakkenR3Q38_();
const rollbackDry = rollbackHarness.context.ADMIN_rollbackLatestTakkenR3Q38DryRun_();
assert.equal(rollbackDry.mode, 'dry-run');
assert.equal(rollbackDry.wouldRestore, 2);
const rollback = rollbackHarness.context.ADMIN_rollbackLatestTakkenR3Q38_();
assert.equal(rollback.ok, true);
assert.equal(rollback.restored, 2);
assertAllNonStemCellsUnchanged(rollbackHarness, rollbackBefore);
assert.deepEqual(JSON.stringify(rollbackHarness.questionBank), rollbackHarness.beforeSnapshot);
assert.equal(rollbackHarness.fakeSheets.calls.length, 2);
assert.equal(rollbackHarness.cacheClears, 2);
assert.equal(rollbackHarness.db.getSheetByName('_QuestionBankPatchBackup').data.slice(1).every((row) => row[2] === 'rolled_back'), true);
assert.equal(rollbackApplied.patchId, 'takken-r3q38-test-patch-id-1');

// If rollback's Advanced Sheets request fails, the backup is marked and the
// post-patch data is left untouched for manual review.
const rollbackFailureHarness = makeHarness();
rollbackFailureHarness.context.ADMIN_applyTakkenR3Q38_();
rollbackFailureHarness.fakeSheets.mode = 'throw';
assert.throws(() => rollbackFailureHarness.context.ADMIN_rollbackLatestTakkenR3Q38_(), /rollback failed/);
assert.equal(rollbackFailureHarness.db.getSheetByName('_QuestionBankPatchBackup').data[1][2], 'rollback_failed');
assert.equal(rollbackFailureHarness.cacheClears, 1);

// Immediate cache invalidation is part of the patch transaction. A strict
// invalidation failure causes apply to stop and the exact rollback contract to
// run; it is never reported as a successful visible update.
const cacheFailureHarness = makeHarness();
cacheFailureHarness.context.clearAllCache_ = () => { throw new Error('simulated questions_version cache invalidation failed'); };
assert.throws(() => cacheFailureHarness.context.ADMIN_applyTakkenR3Q38_(), /rollback failed/);
assert.equal(cacheFailureHarness.fakeSheets.calls.length, 2);
assert.equal(cacheFailureHarness.db.getSheetByName('_QuestionBankPatchBackup').data[1][2], 'rollback_failed');

// Apply is also fail-closed when the explicit maintenance window is not open.
const closedWindowHarness = makeHarness();
closedWindowHarness.context.getScriptProps_ = () => ({ getProperty() { return 'CLOSED'; } });
assert.throws(() => closedWindowHarness.context.ADMIN_applyTakkenR3Q38_(), /maintenance window is not OPEN/);
assert.equal(closedWindowHarness.db.getSheetByName('_QuestionBankPatchBackup'), null);
assert.deepEqual(JSON.stringify(closedWindowHarness.questionBank), closedWindowHarness.beforeSnapshot);

// Missing Advanced Service is fail-closed; there is no SpreadsheetApp
// fallback. The prepared backup records that no mutation was verified.
const unavailableHarness = makeHarness();
unavailableHarness.context.Sheets = undefined;
assert.throws(() => unavailableHarness.context.ADMIN_applyTakkenR3Q38_(), /Advanced Sheets service unavailable/);
assert.equal(unavailableHarness.fakeSheets.calls.length, 0);
assert.equal(unavailableHarness.db.getSheetByName('_QuestionBankPatchBackup').data[1][2], 'not_applied');
assert.deepEqual(JSON.stringify(unavailableHarness.questionBank), unavailableHarness.beforeSnapshot);

// An API response with zero occurrences or an abnormal reply count is
// fail-closed and cannot fall back to SpreadsheetApp writes.
const zeroOccurrenceHarness = makeHarness();
zeroOccurrenceHarness.fakeSheets.mode = 'zeroReply';
assert.throws(() => zeroOccurrenceHarness.context.ADMIN_applyTakkenR3Q38_(), /occurrencesChanged must equal 1/);
assert.equal(zeroOccurrenceHarness.fakeSheets.calls.length, 1);
assert.equal(zeroOccurrenceHarness.db.getSheetByName('_QuestionBankPatchBackup').data[1][2], 'not_applied');
assert.deepEqual(JSON.stringify(zeroOccurrenceHarness.questionBank), zeroOccurrenceHarness.beforeSnapshot);

const abnormalReplyHarness = makeHarness();
abnormalReplyHarness.fakeSheets.mode = 'badReply';
assert.throws(() => abnormalReplyHarness.context.ADMIN_applyTakkenR3Q38_(), /reply count mismatch/);
assert.equal(abnormalReplyHarness.fakeSheets.calls.length, 1);
assert.equal(abnormalReplyHarness.db.getSheetByName('_QuestionBankPatchBackup').data[1][2], 'not_applied');
assert.deepEqual(JSON.stringify(abnormalReplyHarness.questionBank), abnormalReplyHarness.beforeSnapshot);

// DB_SPREADSHEET_ID is captured in the plan and checked at plan, backup,
// API, and post-read boundaries.
const dbPlanHarness = makeHarness();
dbPlanHarness.props.set('DB_SPREADSHEET_ID', '');
assert.throws(() => dbPlanHarness.context.ADMIN_patchTakkenR3Q38DryRun_(), /DB_SPREADSHEET_ID is missing/);

const dbBackupHarness = makeHarness();
dbBackupHarness.setFlushHook(() => dbBackupHarness.props.set('DB_SPREADSHEET_ID', 'wrong-db'));
assert.throws(() => dbBackupHarness.context.ADMIN_applyTakkenR3Q38_(), /DB_SPREADSHEET_ID changed or is missing at after-backup/);
assert.equal(dbBackupHarness.fakeSheets.calls.length, 0);

const dbApiHarness = makeHarness();
const dbApiBatch = dbApiHarness.context.takkenR3Q38BatchFindReplace_;
dbApiHarness.context.takkenR3Q38BatchFindReplace_ = (plan, replacements) => {
  dbApiHarness.props.set('DB_SPREADSHEET_ID', 'wrong-db');
  return dbApiBatch(plan, replacements);
};
assert.throws(() => dbApiHarness.context.ADMIN_applyTakkenR3Q38_(), /DB_SPREADSHEET_ID changed or is missing at api-batchUpdate/);
assert.equal(dbApiHarness.fakeSheets.calls.length, 0);

// TOCTOU guard: even with the same Script Properties value, replacing the
// loaded Spreadsheet object/ID immediately before the API call must fail
// before any request is sent.
const spreadsheetRaceHarness = makeHarness();
const spreadsheetRaceBatch = spreadsheetRaceHarness.context.takkenR3Q38BatchFindReplace_;
spreadsheetRaceHarness.context.takkenR3Q38BatchFindReplace_ = (plan, replacements) => {
  spreadsheetRaceHarness.db.id = 'different-loaded-spreadsheet';
  return spreadsheetRaceBatch(plan, replacements);
};
assert.throws(() => spreadsheetRaceHarness.context.ADMIN_applyTakkenR3Q38_(), /loaded Spreadsheet\.getId\(\) changed/);
assert.equal(spreadsheetRaceHarness.fakeSheets.calls.length, 0);
assert.equal(spreadsheetRaceHarness.db.getSheetByName('_QuestionBankPatchBackup').data[1][2], 'manual_review');

const dbPostHarness = makeHarness();
const dbPostBatch = dbPostHarness.context.takkenR3Q38BatchFindReplace_;
dbPostHarness.context.takkenR3Q38BatchFindReplace_ = (plan, replacements) => {
  const result = dbPostBatch(plan, replacements);
  dbPostHarness.props.set('DB_SPREADSHEET_ID', 'wrong-db');
  return result;
};
assert.throws(() => dbPostHarness.context.ADMIN_applyTakkenR3Q38_(), /rollback failed|DB_SPREADSHEET_ID changed/);
assert.equal(dbPostHarness.fakeSheets.calls.length, 1);
assert.equal(dbPostHarness.db.getSheetByName('_QuestionBankPatchBackup').data[1][2], 'manual_review');

console.log(JSON.stringify({
  ok: true,
  tests: 77,
  contracts: 10,
  dryRunMatched: dry.matched,
  appliedUpdated: applied.updated,
  rollbackRestored: rollback.restored,
  cacheInvalidations: applyHarness.cacheClears + rollbackHarness.cacheClears,
  batchRequests: applyHarness.fakeSheets.calls[0].body.requests.length,
}));
