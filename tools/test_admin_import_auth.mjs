import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const apiSource = fs.readFileSync(new URL('../src/api.gs', import.meta.url), 'utf8');
const htmlSource = fs.readFileSync(new URL('../src/index.html', import.meta.url), 'utf8');

function makeContext(role) {
  const counters = { lock: 0, append: 0, setValues: 0, validate: 0 };
  const sheet = {
    getDataRange() {
      return { getValues() { return [['qId', 'explainA'], ['Q1', 'old']]; } };
    },
    getRange() {
      return { setValues() { counters.setValues += 1; } };
    },
  };
  const ctx = {
    console,
    Logger: { log() {} },
    APP_IMAGE_FOLDER_NAME_: 'test-images',
    SHEETS: { QuestionBank: 'QuestionBank', Attempts: 'Attempts' },
    HEADERS: { QuestionBank: ['qId', 'explainA'] },
    getUserContext_() { return { role, userKey: role === 'admin' ? 'admin-key' : 'user-key' }; },
    requireAdmin_(userCtx) {
      if (!userCtx || userCtx.role !== 'admin') throw new Error('管理者権限が必要です');
    },
    requireActiveUser_(userCtx) {
      if (!userCtx || !['user', 'manager', 'admin'].includes(userCtx.role)) throw new Error('ログインが必要です');
    },
    findAttemptById_() {
      return { index: 2, row: { userKey: 'other-user', status: 'started' } };
    },
    getConfigMap_() { return {}; },
    getConfigValue_(_map, _key, fallback) { return fallback; },
    getNow_() { return new Date('2026-08-21T00:00:00Z'); },
    formatDateTime_(value) { return value.toISOString(); },
    isAttemptExpired_() { return false; },
    getQuestionsByIds_() { return []; },
    updateAttempt_() { ctx.__submitUpdateCount += 1; },
    updateTagStats_() {},
    computeTopWeakTags_() { return []; },
    getRecentScores_() { return []; },
    getWrongAnswerRanking_() { return []; },
    computeFieldStats_() { return []; },
    generateStudyAdvice_() { return { text: '' }; },
    __submitUpdateCount: 0,
    LockService: {
      getScriptLock() {
        counters.lock += 1;
        return { waitLock() {}, releaseLock() {} };
      },
    },
    getSheet_() { return sheet; },
    validateCsvForSheet_() {
      counters.validate += 1;
      return { ok: true, rows: [['row']] };
    },
    appendRows_() { counters.append += 1; },
    migrateQuestionBankSchema_() { return { status: 'ok' }; },
  };
  vm.createContext(ctx);
  vm.runInContext(apiSource, ctx, { filename: 'src/api.gs' });
  return { ctx, counters };
}

for (const denied of [
  { role: '', key: '' },
  { role: 'unknown', key: 'unknown-key' },
  { role: 'user', key: 'user-key' },
]) {
  for (const [name, args] of [
    ['apiAdminDryRunCsv', ['Attempts', 'x', denied.key]],
    ['apiAdminImportCsv', ['Attempts', 'x', denied.key]],
    ['apiImportExplanations', ['qId,explainA\nQ1,new', denied.key]],
  ]) {
    const { ctx, counters } = makeContext(denied.role);
    assert.throws(() => ctx[name](...args), /管理者権限/);
    assert.deepEqual(counters, { lock: 0, append: 0, setValues: 0, validate: 0 }, name + ' must deny before reads/writes');
  }
}

{
  const { ctx, counters } = makeContext('admin');
  const dry = ctx.apiAdminDryRunCsv('Attempts', 'x', 'admin-key');
  assert.equal(dry.ok, true);
  assert.equal(counters.validate, 1);

  const imported = ctx.apiAdminImportCsv('Attempts', 'x', 'admin-key');
  assert.equal(imported.ok, true);
  assert.equal(imported.inserted, 1);
  assert.equal(counters.append, 1);

  const explained = ctx.apiImportExplanations('qId,explainA\nQ1,new', 'admin-key');
  assert.equal(explained.ok, true);
  assert.equal(explained.updated, 1);
  assert.equal(counters.setValues, 1);
}

assert.match(htmlSource, /\.apiAdminDryRunCsv\(sheet, csv, getClientUserKey\(\)\)/);
assert.match(htmlSource, /\.apiAdminImportCsv\(sheet, csv, getClientUserKey\(\)\)/);
assert.match(htmlSource, /\.apiImportExplanations\(csv, getClientUserKey\(\)\)/);
assert.match(htmlSource, /\.apiLogClientAuthIssue\(payload, getClientUserKey\(\)\)/);
assert.match(htmlSource, /\.apiSubmitTest\([^]*getClientUserKey\(\)\)/);
assert.match(htmlSource, /\.apiSubmitPractice\([^]*getClientUserKey\(\)\)/);

{
  const { ctx, counters } = makeContext('');
  assert.throws(() => ctx.apiSubmitTest({ attemptId: 'x', answers: [] }, ''), /ログイン/);
  assert.equal(counters.lock, 0, 'unauthenticated submit must stop before lock/write');
  const logResult = ctx.apiLogClientAuthIssue({ issueType: 'test' }, '');
  assert.equal(logResult.persisted, false, 'unauthenticated telemetry must not write to Sheets');
}

{
  const { ctx, counters } = makeContext('user');
  const result = ctx.apiSubmitTest({ attemptId: 'other-attempt', answers: [] }, 'user-key');
  assert.equal(result._error, true, 'another user attempt must be rejected');
  assert.equal(counters.append, 0);
  assert.equal(counters.setValues, 0);
}

{
  const { ctx } = makeContext('user');
  ctx.findAttemptById_ = () => ({
    index: 2,
    row: { userKey: 'user-key', status: 'started', mode: 'practice', testIndex: '' },
  });
  ctx.updateAttempt_ = () => { ctx.__submitUpdateCount += 1; };
  const result = ctx.apiSubmitTest({ attemptId: 'own-attempt', answers: [] }, 'user-key');
  assert.equal(result.status, 'submitted', 'owner must still be able to submit');
  assert.equal(ctx.__submitUpdateCount, 1);
}

const maintenanceSources = [
  fs.readFileSync(new URL('../src/importCsv.gs', import.meta.url), 'utf8'),
  fs.readFileSync(new URL('../src/adminImport.gs', import.meta.url), 'utf8'),
  fs.readFileSync(new URL('../src/db.gs', import.meta.url), 'utf8'),
  fs.readFileSync(new URL('../src/memberRoster.gs', import.meta.url), 'utf8'),
  fs.readFileSync(new URL('../src/auth.gs', import.meta.url), 'utf8'),
];
const publicMaintenanceNames = [];
for (const source of maintenanceSources) {
  for (const match of source.matchAll(/^function ([A-Za-z0-9_]+)\(/gm)) {
    const name = match[1];
    if (
      ['importQuestionBankFromCsv', 'importQuestionBankFromDriveFile', 'importQuestionBankFromFolder',
       'getQuestionBankImportUrl', 'importFullQuestionBank', 'importByFileId',
       'testImportQuestionBankFromCsv', 'setup', 'setupForce', 'syncDashboardRoster'].includes(name) ||
      (name.startsWith('ADMIN_') && !name.endsWith('_'))
    ) publicMaintenanceNames.push(name);
  }
}
assert.deepEqual(publicMaintenanceNames, [], 'legacy maintenance entry points must be private');

const codeSource = fs.readFileSync(new URL('../src/Code.gs', import.meta.url), 'utf8');
assert.match(codeSource, /importQuestionBankFromFolder_\(\)/);
assert.match(codeSource, /getQuestionBankImportUrl_\(\)/);
assert.match(codeSource, /importQuestionBankFromCsv_\(csvText\)/);
assert.match(codeSource, /importCsvText:\s*true/);
assert.match(codeSource, /importCsvFromFolder[^]*maintenanceActions\[action\]/);


console.log('admin import authorization contracts: blank/unknown/user deny and admin success');
