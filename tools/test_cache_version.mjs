import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import fs from 'node:fs';
import vm from 'node:vm';

const dbText = fs.readFileSync(new URL('../src/db.gs', import.meta.url), 'utf8');
const start = dbText.indexOf('// Script-scope cache for full QuestionBank');
assert.ok(start >= 0, 'QuestionBank cache section must exist');
const cacheSource = dbText.slice(start);

const sharedStore = new Map();
let uuidCounter = 0;
let failPut = false;
let cacheWriteMode = 'normal';
const sheet = {
  rows: [
    ['qId', 'status', 'stem'],
    ['Q-1', 'published', 'old'],
  ],
  getDataRange() {
    return { getValues: () => this.rows.map((row) => row.slice()) };
  },
};

function makeContext() {
  const context = {
    Date,
    Utilities: {
      getUuid() { uuidCounter += 1; return `uuid-${uuidCounter}`; },
    },
    CACHE_TTL_QUESTIONS: 3600,
    getCache_() {
      return {
        get(key) { return sharedStore.get(key) ?? null; },
        put(key, value) {
          if (failPut) throw new Error('simulated CacheService put failure');
          if (key === 'questions_version') {
            if (cacheWriteMode === 'no-reflection') return;
            if (cacheWriteMode === 'old-value') {
              sharedStore.set(key, 'old-cache-token');
              return;
            }
            if (cacheWriteMode === 'empty') {
              sharedStore.delete(key);
              return;
            }
          }
          sharedStore.set(key, String(value));
        },
        removeAll(keys) { for (const key of keys) sharedStore.delete(key); },
      };
    },
    SHEETS: { QuestionBank: 'QuestionBank' },
    getSheet_() { return sheet; },
    HEADERS: { QuestionBank: ['qId', 'status', 'stem'] },
    normalizeHeader_(value) { return String(value ?? '').trim(); },
  };
  vm.createContext(context);
  vm.runInContext(cacheSource, context, { filename: 'db-cache-section.gs' });
  return context;
}

// Instance A holds an in-process value. Instance B represents another Web
// App execution and invalidates the shared version after a QuestionBank edit.
const instanceA = makeContext();
const instanceB = makeContext();
const first = instanceA.getCachedQuestions_();
assert.equal(first[0].stem, 'old');
assert.ok(sharedStore.get('questions_version'));

sheet.rows[1][2] = 'new';
instanceB.clearAllCache_();
const second = instanceA.getCachedQuestions_();
assert.equal(second[0].stem, 'new', 'another instance invalidation must bypass local TTL cache');
assert.notEqual(instanceA._questionsCacheVersion, '', 'instance must track the shared version');

// Same-process invalidation also discards the script-scope cache immediately.
sheet.rows[1][2] = 'newer';
instanceA.clearAllCache_();
assert.equal(instanceA._questionsCache, null);
assert.equal(instanceA._questionsCacheTs, 0);
assert.equal(instanceA.getCachedQuestions_()[0].stem, 'newer');

// Normal reads remain available during a transient questions_version put
// failure, but the strict invalidator used by the patch must fail closed.
sheet.rows[1][2] = 'degraded';
sharedStore.delete('questions_version');
failPut = true;
const degradedInstance = makeContext();
assert.doesNotThrow(() => degradedInstance.getCachedQuestions_());
assert.equal(degradedInstance.getCachedQuestions_()[0].stem, 'degraded');
assert.throws(() => degradedInstance.clearAllCache_({ strict: true }), /questions_version cache invalidation failed/);
failPut = false;

// A put() that reports success but is not visible to the next read must also
// fail closed. Cover no reflection, an old token remaining, and an empty
// marker; all three would otherwise keep another execution's stale cache.
const readAfterWriteModes = ['no-reflection', 'old-value', 'empty'];
for (const mode of readAfterWriteModes) {
  sharedStore.set('questions_version', 'old-cache-token');
  cacheWriteMode = mode;
  const strictInstance = makeContext();
  assert.throws(
    () => strictInstance.clearAllCache_({ strict: true }),
    /questions_version (?:read-after-write mismatch|cache invalidation failed)/,
    `strict invalidation must reject ${mode}`,
  );
}
cacheWriteMode = 'normal';

console.log(JSON.stringify({
  ok: true,
  tests: 12,
  crossInstanceRefresh: true,
  sameProcessRefresh: true,
  strictFailureDetected: true,
  readAfterWriteMismatchModes: readAfterWriteModes,
}));
