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
    APP_IMAGE_FOLDER_NAME_: 'test-images',
    SHEETS: { QuestionBank: 'QuestionBank', Attempts: 'Attempts' },
    HEADERS: { QuestionBank: ['qId', 'explainA'] },
    getUserContext_() { return { role, userKey: role === 'admin' ? 'admin-key' : 'user-key' }; },
    requireAdmin_(userCtx) {
      if (!userCtx || userCtx.role !== 'admin') throw new Error('管理者権限が必要です');
    },
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

console.log('admin import authorization contracts: blank/unknown/user deny and admin success');
