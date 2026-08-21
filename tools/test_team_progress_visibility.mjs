import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const apiSource = fs.readFileSync(new URL('../src/api.gs', import.meta.url), 'utf8');

function extractFunction(name) {
  const start = apiSource.indexOf(`function ${name}(`);
  assert.notEqual(start, -1, `${name} must remain defined in api.gs`);
  const open = apiSource.indexOf('{', start);
  let depth = 0;
  for (let i = open; i < apiSource.length; i += 1) {
    if (apiSource[i] === '{') depth += 1;
    if (apiSource[i] === '}') {
      depth -= 1;
      if (depth === 0) return apiSource.slice(start, i + 1);
    }
  }
  throw new Error(`Could not extract ${name}`);
}

const context = {
  normalizeUserAccessBoolean_(value, defaultValue) {
    if (value === true || value === false) return value ? 'true' : 'false';
    const raw = String(value ?? '').trim().toLowerCase();
    if (!raw) return defaultValue ? 'true' : 'false';
    return ['false', '0', 'no'].includes(raw) ? 'false' : 'true';
  },
  buildProgress_(attempts, totalTests) {
    return { submitted: attempts.length, totalTests };
  },
  Logger: { log() {} },
};
vm.createContext(context);
vm.runInContext(extractFunction('buildTeamProgressSummary_'), context);

function summary(viewer, accessRows, userRows = [], allAttempts = []) {
  return JSON.parse(JSON.stringify(
    context.buildTeamProgressSummary_(accessRows, userRows, allAttempts, 16, 'Asia/Tokyo', viewer),
  ));
}

const adminRows = [
  { email: '  ADMIN@EXAMPLE.COM ', active: false, showInDashboard: 'false', managerEmail: 'someone@example.com', displayName: '' },
  { email: 'admin@example.com', active: true, showInDashboard: true, managerEmail: '', displayName: '管理者本人' },
  { email: 'duplicate@example.com', active: true, showInDashboard: false, managerEmail: '', displayName: '重複非表示' },
  { email: ' ACTIVE@EXAMPLE.COM ', active: true, showInDashboard: true, managerEmail: 'other@example.com', displayName: '表示対象' },
  { email: ' DUPLICATE@EXAMPLE.COM ', active: true, showInDashboard: true, managerEmail: '', displayName: '重複表示対象' },
  { email: 'duplicate@example.com', active: true, showInDashboard: true, managerEmail: '', displayName: '重複後続' },
  { email: 'hidden@example.com', active: true, showInDashboard: 'false', managerEmail: '', displayName: '非表示' },
  { email: 'inactive@example.com', active: 'false', showInDashboard: true, managerEmail: '', displayName: '無効' },
  { email: '', active: true, showInDashboard: true, managerEmail: '', displayName: '空メール' },
];
const adminResult = summary(
  { role: ' ADMIN ', email: ' admin@example.com ' },
  adminRows,
  [
    { email: ' ADMIN@EXAMPLE.COM ', userKey: '', displayName: '' },
    { email: 'admin@example.com', userKey: 'admin-key', displayName: 'ユーザー名簿の管理者名' },
    { email: 'active@example.com', userKey: 'active-key', displayName: '表示対象' },
  ],
  [{ userKey: 'admin-key', scoreTotal: 10 }],
);
assert.deepEqual(
  adminResult.team.map((row) => row.email),
  ['admin@example.com', 'active@example.com', 'duplicate@example.com'],
  'admin rows keep the order of the first eligible normalized email',
);
assert.equal(adminResult.team.filter((row) => row.email === 'admin@example.com').length, 1, 'mixed-case self duplicates render once');
assert.equal(adminResult.team.filter((row) => row.email === 'duplicate@example.com').length, 1, 'other duplicates render once');
assert.equal(adminResult.team[0].displayName, '管理者本人', 'self name is merged from the complete duplicate set');
assert.equal(adminResult.team[0].progress.submitted, 1, 'self user lookup is merged from normalized duplicate rows');
assert.equal(adminResult.team[2].displayName, '重複表示対象', 'first eligible duplicate row supplies the other member name');
assert.deepEqual(Object.keys(adminResult.team[0]).sort(), ['displayName', 'email', 'progress'], 'team rows do not expose answer details');

const managerRows = [
  { email: ' manager@example.com ', active: false, showInDashboard: false, managerEmail: 'someone@example.com', displayName: '上司本人' },
  { email: 'direct@example.com', active: true, showInDashboard: true, managerEmail: ' MANAGER@EXAMPLE.COM ', displayName: '直属' },
  { email: 'direct-hidden@example.com', active: true, showInDashboard: false, managerEmail: 'manager@example.com', displayName: '直属非表示' },
  { email: 'direct-inactive@example.com', active: false, showInDashboard: true, managerEmail: 'manager@example.com', displayName: '直属無効' },
  { email: 'conflict@example.com', active: true, showInDashboard: true, managerEmail: 'other-manager@example.com', displayName: '非直属重複' },
  { email: 'other@example.com', active: true, showInDashboard: true, managerEmail: 'other-manager@example.com', displayName: '非直属' },
  { email: ' CONFLICT@EXAMPLE.COM ', active: true, showInDashboard: true, managerEmail: ' MANAGER@EXAMPLE.COM ', displayName: '直属重複' },
  { email: 'conflict@example.com', active: true, showInDashboard: true, managerEmail: 'manager@example.com', displayName: '直属重複後続' },
  { email: 'unassigned@example.com', active: true, showInDashboard: true, managerEmail: ' ', displayName: '担当なし' },
];
const managerResult = summary(
  { role: 'manager', email: ' MANAGER@EXAMPLE.COM ' },
  managerRows,
  [
    { email: 'manager@example.com', userKey: 'manager-key', displayName: '上司本人' },
    { email: 'direct@example.com', userKey: 'direct-key', displayName: '直属' },
  ],
  [{ userKey: 'direct-key', scoreTotal: 10 }],
);
assert.deepEqual(
  managerResult.team.map((row) => row.email),
  ['manager@example.com', 'direct@example.com', 'conflict@example.com'],
  'manager keeps self and the first eligible direct-report row in source order',
);
assert.equal(managerResult.team[0].progress.submitted, 0, 'manager self is shown even with zero progress');
assert.equal(managerResult.team[1].progress.submitted, 1, 'direct report progress remains available');
assert.equal(managerResult.team.filter((row) => row.email === 'conflict@example.com').length, 1, 'non-direct duplicate cannot create or suppress duplicate rows');
assert.equal(managerResult.team[2].displayName, '直属重複', 'first eligible direct-report duplicate is retained');

const userResult = summary(
  { role: 'user', email: 'user@example.com' },
  [...managerRows, { email: 'user@example.com', active: true, showInDashboard: true, managerEmail: '' }],
);
assert.deepEqual(userResult.team.map((row) => row.email), ['user@example.com'], 'regular users receive only their own row');
assert.equal(userResult.team[0].progress.submitted, 0, 'regular users receive their own progress');
assert.deepEqual(
  summary({ role: 'user', email: '   ' }, managerRows).team,
  [],
  'blank regular-user identity never receives another user row',
);

const emptyViewerResult = summary(
  { role: 'admin', email: '   ' },
  [
    { email: 'active@example.com', active: true, showInDashboard: true, managerEmail: '' },
    { email: 'inactive@example.com', active: false, showInDashboard: true, managerEmail: '' },
    { email: '', active: true, showInDashboard: true, managerEmail: '' },
  ],
);
assert.deepEqual(emptyViewerResult.team.map((row) => row.email), ['active@example.com'], 'blank viewer email never becomes a self-match');

console.log('team progress visibility: duplicate and role regressions passed');
