// logic.gs
function getConfigMap_() {
  return getCachedConfig_();
}

function getConfigValue_(map, key, defVal) {
  if (map.hasOwnProperty(key)) return map[key];
  return defVal;
}

function getNow_() {
  return new Date();
}

function formatDateTime_(d, tz) {
  return Utilities.formatDate(d, tz, 'yyyy-MM-dd HH:mm:ss');
}

function formatDate_(d, tz) {
  return Utilities.formatDate(d, tz, 'yyyy-MM-dd');
}

function dateOnlyUtcMs_(value, tz) {
  var ymd = '';
  if (value instanceof Date) {
    ymd = Utilities.formatDate(value, tz || 'Asia/Tokyo', 'yyyy-MM-dd');
  } else {
    var raw = String(value || '').trim();
    var match = raw.match(/^(\d{4})-(\d{1,2})-(\d{1,2})/);
    if (match) {
      ymd = match[1] + '-' + ('0' + match[2]).slice(-2) + '-' + ('0' + match[3]).slice(-2);
    } else {
      var parsed = new Date(raw);
      if (!isNaN(parsed.getTime())) ymd = Utilities.formatDate(parsed, tz || 'Asia/Tokyo', 'yyyy-MM-dd');
    }
  }
  if (!ymd) return NaN;
  var parts = ymd.split('-').map(function(v) { return Number(v); });
  return Date.UTC(parts[0], parts[1] - 1, parts[2]);
}

function parseUnlockWeek_(value) {
  if (value === null || value === undefined) return 0;
  if (typeof value === 'number') return value;
  var s = String(value).trim();
  if (!s) return 0;
  var m = s.match(/-?\d+/);
  if (!m) return NaN;
  return Number(m[0]);
}

function weeksSinceStart_(startDateStr, tz) {
  var zone = tz || 'Asia/Tokyo';
  var startMs = dateOnlyUtcMs_(startDateStr, zone);
  var nowMs = dateOnlyUtcMs_(getNow_(), zone);
  var diff = nowMs - startMs;
  var days = Math.floor(diff / (1000*60*60*24));
  // If before start date, return -1 (no test should be "this week's test")
  if (days < 0) return -1;
  return Math.floor(days / 7);
}

function getTestPlanRows_() {
  return getCachedTestPlan_();
}

function getTestPlanByIndex_(idx) {
  var rows = getTestPlanRows_();
  for (var i = 0; i < rows.length; i++) {
    if (String(rows[i].testIndex) === String(idx)) return rows[i];
  }
  return null;
}

function isTestUnlocked_(planRow, weeksSinceStart) {
  // All tests always unlocked - no week restriction
  return true;
}

function isThisWeeksTest_(planRow, weeksSinceStart) {
  // Check if this test is "this week's test" based on unlockWeek
  // Before program start (weeksSinceStart < 0), only 第1回 (testIndex = 1) is "this week's test"
  if (weeksSinceStart < 0) {
    return Number(planRow.testIndex) === 1;
  }
  // After program start, match by unlockWeek
  var uw = parseUnlockWeek_(planRow.unlockWeek);
  if (isNaN(uw) || uw < 0) return false;
  return uw === weeksSinceStart;
}

function getActiveEmail_() {
  var email = '';
  try {
    email = Session.getActiveUser().getEmail() || '';
  } catch (e) {
    email = '';
  }
  return String(email || '').trim();
}

function normalizeUserAccessBoolean_(value, defaultValue) {
  if (value === true || value === false) return value ? 'true' : 'false';
  var raw = String(value == null ? '' : value).trim().toLowerCase();
  if (!raw) return defaultValue ? 'true' : 'false';
  return (raw === 'false' || raw === '0' || raw === 'no') ? 'false' : 'true';
}

function getDirectoryProfile_(email) {
  if (!email) return { email: '', displayName: '' };
  var displayName = email.split('@')[0];
  try {
    var user = AdminDirectory.Users.get(email, { fields: 'primaryEmail,name/fullName' });
    if (user && user.name && user.name.fullName) displayName = user.name.fullName;
  } catch (e) {
    // Directory API unavailable or insufficient permission; fallback to email prefix
  }
  return { email: email, displayName: displayName };
}

// Global request-scoped variable for client user key (set by each API entry point)
// GAS is single-threaded per execution, so this is safe.
var __clientUserKey = '';

function getUserContext_() {
  // Priority 1: OAuth 確立済みセッション（clientUserKey）
  var cuk = __clientUserKey || '';
  if (cuk) {
    var existing = findUserByKey_(cuk);
    if (existing) {
      return { userKey: existing.userKey, email: existing.email || '', displayName: existing.displayName, authMethod: 'google_local' };
    }
  }
  // Priority 2: Session email（未ログイン時の補助）
  var email = getActiveEmail_();
  if (email) {
    var profile = getDirectoryProfile_(email);
    return { userKey: email, email: profile.email, displayName: profile.displayName, authMethod: 'google' };
  }
  // Priority 3: 未識別
  return { userKey: '', email: '', displayName: '', authMethod: 'none' };
}

function ensureUser_(userKey, email, displayName) {
  var sh = getSheet_(SHEETS.Users);
  var rows = readRecords_(sh);
  for (var i = 0; i < rows.length; i++) {
    if (rows[i].userKey === userKey) return rows[i];
  }
  var name = displayName || (email ? email.split('@')[0] : 'user');
  var now = formatDateTime_(getNow_(), 'Asia/Tokyo');
  appendRows_(sh, [[userKey, email, name, now, '']]);
  return { userKey: userKey, email: email, displayName: name, createdAt: now, recoveryCode: '' };
}

function findUserByKey_(userKey) {
  if (!userKey) return null;
  var rows = readRecords_(getSheet_(SHEETS.Users));
  for (var i = 0; i < rows.length; i++) {
    if (rows[i].userKey === userKey) return rows[i];
  }
  return null;
}

function getUserAccessByEmail_(email) {
  var rows = readRecords_(getUserAccessSheet_());
  var target = String(email || '').toLowerCase();
  for (var i = 0; i < rows.length; i++) {
    var rowEmail = String(rows[i].email || '').toLowerCase();
    if (rowEmail === target) {
      var activeVal = String(rows[i].active || '').toLowerCase();
      var active = !(activeVal === 'false' || activeVal === '0' || activeVal === 'no' || rows[i].active === false);
      return {
        email: email,
        role: String(rows[i].role || 'user').toLowerCase(),
        managerEmail: String(rows[i].managerEmail || ''),
        active: active,
        displayName: String(rows[i].displayName || ''),
        showInDashboard: normalizeUserAccessBoolean_(rows[i].showInDashboard, true) !== 'false'
      };
    }
  }
  return { email: email, role: 'user', managerEmail: '', active: false, displayName: '', showInDashboard: false };
}

function requireActiveUser_(userCtx) {
  if (!userCtx || !userCtx.userKey) {
    throw new Error('ユーザー登録が必要です');
  }
  // Return a compatible access object (role defaults to 'user')
  var role = 'user';
  var managerRef = '';
  var accessName = '';
  var showInDashboard = true;
  // Try email first, then userKey (for non-Workspace users who have no email)
  var lookupKey = userCtx.email || userCtx.userKey;
  if (lookupKey) {
    var access = getUserAccessByEmail_(lookupKey);
    if (!access || !access.active) {
      throw new Error('このユーザーは無効です');
    }
    if (access && access.role) role = access.role;
    if (access && access.managerEmail) managerRef = access.managerEmail;
    if (access && access.displayName) accessName = access.displayName;
    if (access && access.hasOwnProperty('showInDashboard')) showInDashboard = !!access.showInDashboard;
  }
  return { email: userCtx.email || '', role: role, managerEmail: managerRef, active: true, displayName: accessName || userCtx.displayName || '', showInDashboard: showInDashboard };
}

function requireAdmin_(userCtx) {
  var access = requireActiveUser_(userCtx);
  if (access.role !== 'admin') {
    throw new Error('管理者権限が必要です');
  }
  return access;
}

function getDirectReports_(managerEmail) {
  var rows = readRecords_(getUserAccessSheet_());
  var target = String(managerEmail || '').toLowerCase();
  var list = [];
  rows.forEach(function(r){
    if (String(r.managerEmail || '').toLowerCase() === target) {
      var email = String(r.email || '');
      // Handle both boolean false and string 'false'/'FALSE'
      var rawActive = r.active;
      var active = true;
      if (rawActive === false || rawActive === 'false' || rawActive === 'FALSE' || rawActive === '0' || rawActive === 'no' || rawActive === 'No' || rawActive === 'NO') { active = false; }
      if (normalizeUserAccessBoolean_(r.showInDashboard, true) === 'false') active = false;
      if (email && active) list.push(email);
    }
  });
  return list;
}

function ensureUserAccessSheetSchema_(sh) {
  var expected = HEADERS[SHEETS.UserAccess];
  var lastCol = Math.max(1, sh.getLastColumn());
  var header = sh.getRange(1, 1, 1, lastCol).getValues()[0]
    .map(function(h, i) { return normalizeHeader_(h, i); });
  var changed = false;
  expected.forEach(function(name) {
    if (header.indexOf(name) >= 0) return;
    sh.getRange(1, sh.getLastColumn() + 1).setValue(name);
    header.push(name);
    changed = true;
  });
  sh.setFrozenRows(1);
  return { ok: true, changed: changed, headers: header };
}

function getUserAccessSheet_() {
  var ss = getDb_();
  var sh = ss.getSheetByName(SHEETS.UserAccess);
  if (!sh) {
    sh = ss.insertSheet(SHEETS.UserAccess);
    setHeaders_(sh, HEADERS[SHEETS.UserAccess]);
  } else {
    ensureUserAccessSheetSchema_(sh);
  }
  return sh;
}

function getWeekStartKey_(dateObj, tz) {
  var ymd = Utilities.formatDate(dateObj, tz, 'yyyy-MM-dd');
  var parts = ymd.split('-').map(function(v){ return Number(v); });
  var dt = new Date(Date.UTC(parts[0], parts[1] - 1, parts[2]));
  var day = dt.getUTCDay(); // 0=Sun
  var diff = day === 0 ? 6 : day - 1; // Monday start
  dt.setUTCDate(dt.getUTCDate() - diff);
  return Utilities.formatDate(new Date(dt.getTime()), tz, 'yyyy-MM-dd');
}

function buildProgress_(attempts, totalTests, tz, weeksBack) {
  var submittedTests = attempts.filter(function(a){
    return a.status === 'submitted' && a.mode === 'test';
  });
  var submittedMap = {};
  var completedByTest = {};
  submittedTests.forEach(function(a){
    if (a.testIndex !== '' && a.testIndex !== null && a.testIndex !== undefined) {
      var key = String(a.testIndex);
      submittedMap[key] = true;
      var totalQ = Number(a.totalQuestions || 0);
      var scorePct = totalQ > 0 ? Math.round(Number(a.scoreTotal || 0) / totalQ * 1000) / 10 : 0;
      var submittedAt = String(a.submittedAt || a.startedAt || '');
      var rec = completedByTest[key] || { completed: true, lastSubmittedAt: '', latestScorePct: 0, submitCount: 0 };
      rec.submitCount += 1;
      if (!rec.lastSubmittedAt || submittedAt >= String(rec.lastSubmittedAt || '')) {
        rec.lastSubmittedAt = submittedAt;
        rec.latestScorePct = scorePct;
      }
      completedByTest[key] = rec;
    }
  });
  var submittedUniqueCount = Object.keys(submittedMap).length;
  var avgScore = 0;
  if (submittedTests.length > 0) {
    var totalCorrect = 0, totalQCount = 0;
    submittedTests.forEach(function(a) {
      totalCorrect += Number(a.scoreTotal || 0);
      totalQCount  += Number(a.totalQuestions || 0);
    });
    // 正答率 % (0?100) で統一。グラフ・ステータス判定が全て % 基準のため
    avgScore = totalQCount > 0 ? Math.round(totalCorrect / totalQCount * 1000) / 10 : 0;
  }
  var now = getNow_();
  var cutoff = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
  var last7DaysCount = 0;
  attempts.forEach(function(a){
    var ts = a.submittedAt || a.startedAt || '';
    if (!ts) return;
    var d = parseTimestamp_(ts);
    if (d && d >= cutoff) last7DaysCount += 1;
  });

  var weekly = buildWeeklySeries_(attempts, tz, weeksBack || 8);

  // モード別集計（test/mock/field）
  var modeStats = {
    test:  { totalQ: 0, correct: 0, count: 0 },
    mock:  { totalQ: 0, correct: 0, count: 0 },
    field: { totalQ: 0, correct: 0, count: 0 }
  };
  attempts.forEach(function(a) {
    if (a.status !== 'submitted') return;
    var m = String(a.mode || 'test');
    if (modeStats[m]) {
      modeStats[m].totalQ   += Number(a.totalQuestions || 0);
      modeStats[m].correct  += Number(a.scoreTotal || 0);
      modeStats[m].count    += 1;
    }
  });
  var byMode = {};
  ['test', 'mock', 'field'].forEach(function(m) {
    var s = modeStats[m];
    byMode[m] = {
      totalQ:       s.totalQ,
      correctCount: s.correct,
      rate:         s.totalQ > 0 ? Math.round(s.correct / s.totalQ * 100) : 0,
      attempts:     s.count
    };
  });

  return {
    attemptsTotal: attempts.length,
    submittedTests: submittedUniqueCount,
    totalTests: totalTests,
    submittedTestMap: submittedMap,
    completedByTest: completedByTest,
    avgScore: avgScore,
    last7DaysCount: last7DaysCount,
    weekly: weekly,
    byMode: byMode
  };
}

// Parse timestamp: handles both Date objects and string formats
function parseTimestamp_(ts) {
  if (!ts) return null;
  if (ts instanceof Date) return ts;
  var d = new Date(String(ts).replace(' ', 'T'));
  return isNaN(d.getTime()) ? null : d;
}

function buildWeeklySeries_(attempts, tz, weeksBack) {
  var map = {};
  attempts.forEach(function(a){
    if (a.status !== 'submitted') return;
    var ts = a.submittedAt || a.startedAt || '';
    if (!ts) return;
    var d = parseTimestamp_(ts);
    if (!d) return;
    var key = getWeekStartKey_(d, tz);
    if (!map[key]) map[key] = { weekStart: key, count: 0, avgScore: 0, _sum: 0 };
    map[key].count += 1;
    map[key]._sum += Number(a.scoreTotal || 0);
  });

  var keys = Object.keys(map).sort();
  var list = keys.map(function(k){
    var item = map[k];
    item.avgScore = item.count > 0 ? item._sum / item.count : 0;
    delete item._sum;
    return item;
  });

  if (!weeksBack) return list;

  var now = getNow_();
  var result = [];
  for (var i = weeksBack - 1; i >= 0; i--) {
    var d = new Date(now.getTime() - i * 7 * 24 * 60 * 60 * 1000);
    var key = getWeekStartKey_(d, tz);
    var found = map[key] || { weekStart: key, count: 0, avgScore: 0 };
    result.push(found);
  }
  return result;
}

function readQuestionBank_() {
  return getCachedQuestions_();
}

function isValidChoiceQuestion_(q) {
  var correct = String(q.correct || '').trim().toUpperCase();
  var choiceE = String(q.choiceE || '').trim();
  var choices = [q.choiceA, q.choiceB, q.choiceC, q.choiceD];
  for (var i = 0; i < choices.length; i++) {
    if (isBlank_(choices[i])) return false;
  }
  var hasE = !isBlank_(choiceE);
  var parts = correct.split(',').map(function(s){ return s.trim(); }).filter(Boolean);
  if (parts.length === 0) return false;
  for (var p = 0; p < parts.length; p++) {
    var c = parts[p];
    if (hasE) {
      if (!/^[A-E]$/.test(c)) return false;
    } else {
      if (!/^[A-D]$/.test(c)) return false;
    }
  }
  var map = {
    A: String(q.choiceA || '').trim(),
    B: String(q.choiceB || '').trim(),
    C: String(q.choiceC || '').trim(),
    D: String(q.choiceD || '').trim(),
    E: String(q.choiceE || '').trim()
  };
  for (var p2 = 0; p2 < parts.length; p2++) {
    if (isBlank_(map[parts[p2]])) return false;
  }
  return true;
}

function getQuestionsByIds_(ids) {
  return getQuestionsByIdsFromBank_(ids, readQuestionBank_());
}

// Optimized: accepts pre-read QuestionBank
function getQuestionsByIdsFromBank_(ids, questionBank) {
  var map = {};
  questionBank.forEach(function(q){ map[q.qId] = q; });
  var list = [];
  ids.forEach(function(id){ if (map[id]) list.push(map[id]); });
  return list;
}

function shuffle_(arr) {
  for (var i = arr.length - 1; i > 0; i--) {
    var j = Math.floor(Math.random() * (i + 1));
    var t = arr[i]; arr[i] = arr[j]; arr[j] = t;
  }
  return arr;
}

function pickQuestions_(pool, count, usedVariant) {
  var picked = [];
  shuffle_(pool);
  for (var i = 0; i < pool.length && picked.length < count; i++) {
    var q = pool[i];
    var vg = q.variantGroupId || q.qId;
    if (usedVariant[vg]) continue;
    usedVariant[vg] = true;
    picked.push(q);
  }
  return picked;
}

function parseExamRangeTarget_(token) {
  var m = String(token || '').trim().match(/^range:((?:H|R)\d+[A-Z]?)(takken|sekisan)?:(\d+)-(\d+)$/);
  if (!m) return null;
  var from = Number(m[3]);
  var to = Number(m[4]);
  if (from > to) {
    var tmp = from;
    from = to;
    to = tmp;
  }
  return { year: m[1].toUpperCase(), exam: String(m[2] || '').toLowerCase(), from: from, to: to };
}

function questionMatchesExamRangeTarget_(q, token) {
  var target = parseExamRangeTarget_(token);
  if (!target) return false;
  var meta = parseExamQId_(q.qId);
  if (!meta) return false;
  return meta.year === target.year && meta.no >= target.from && meta.no <= target.to;
}

function questionMatchesTargetSegments_(q, segs) {
  if (!segs || segs.length === 0) return true;
  for (var i = 0; i < segs.length; i++) {
    var token = String(segs[i] || '').trim();
    if (!token) continue;
    if (questionMatchesExamRangeTarget_(q, token)) return true;
    if (String(q.segmentId || '').trim() === token) return true;
  }
  return false;
}

function generateTestSet_(planRow, config) {
  var qb = readQuestionBank_().filter(function(q){
    return q.status === 'published' && isValidChoiceQuestion_(q);
  });
  var segs = String(planRow.targetSegments || '').split(',').map(function(s){ return s.trim(); }).filter(Boolean);
  var qPer = Number(planRow.questionsPerTest || config.QUESTIONS_PER_TEST);
  var abilityCount = Number(planRow.abilityCount || config.ABILITY_PER_TEST);
  var knowledgeCount = Math.max(0, qPer - abilityCount);
  var revisionMin = Number(planRow.revisionMinCount || 0);

  var usedVariant = {};

  var abilityPool = qb.filter(function(q){ return q.type === 'ability'; });
  var abilityPicked = pickQuestions_(abilityPool, abilityCount, usedVariant);

  // Redistribute unfilled ability slots to knowledge
  var actualKnowledgeCount = knowledgeCount + (abilityCount - abilityPicked.length);

  var knowledgePool = qb.filter(function(q){ return q.type === 'knowledge' && questionMatchesTargetSegments_(q, segs); });
  var revisionPool = knowledgePool.filter(function(q){ return String(q.revisionFlag) === '1'; });

  var picked = [];
  var revPicked = pickQuestions_(revisionPool, Math.min(revisionMin, actualKnowledgeCount), usedVariant);
  picked = picked.concat(revPicked);

  var remaining = actualKnowledgeCount - picked.length;
  var restPool = knowledgePool.filter(function(q){ return picked.indexOf(q) === -1; });
  var restPicked = pickQuestions_(restPool, remaining, usedVariant);
  picked = picked.concat(restPicked);

  if (picked.length < actualKnowledgeCount) {
    // fallback: use any knowledge to fill
    var fallback = qb.filter(function(q){ return q.type === 'knowledge'; });
    var need = actualKnowledgeCount - picked.length;
    picked = picked.concat(pickQuestions_(fallback, need, usedVariant));
  }

  var all = abilityPicked.concat(picked);
  return all.map(function(q){ return q.qId; });
}

function getAllSegmentIds_(qb) {
  var map = {};
  qb.forEach(function(q){
    var seg = String(q.segmentId || '').trim();
    if (seg) map[seg] = true;
  });
  return Object.keys(map);
}

function computeRevisionMin_(knowledgeCount, config) {
  var ratio = Number(getConfigValue_(config, 'REVISION_RATIO', 0));
  if (isNaN(ratio) || ratio <= 0) return 0;
  return Math.max(0, Math.floor(knowledgeCount * ratio));
}

function generateMiniTestSet_(config) {
  var qb = readQuestionBank_().filter(function(q){
    return q.status === 'published' && isValidChoiceQuestion_(q);
  });
  var segs = getAllSegmentIds_(qb);
  var qPer = Number(getConfigValue_(config, 'MINI_QUESTIONS_PER_TEST', 10));
  var abilityCount = Number(getConfigValue_(config, 'MINI_ABILITY_PER_TEST', 0));
  var knowledgeCount = Math.max(0, qPer - abilityCount);
  var planRow = {
    targetSegments: segs.join(','),
    questionsPerTest: qPer,
    abilityCount: abilityCount,
    revisionMinCount: computeRevisionMin_(knowledgeCount, config)
  };
  return generateTestSet_(planRow, config);
}

function generateTrainingTestSet_(userKey, config) {
  var qb = readQuestionBank_().filter(function(q){
    return q.status === 'published' && isValidChoiceQuestion_(q);
  });
  var qPer = Number(getConfigValue_(config, 'TRAIN_QUESTIONS_PER_TEST', 10));
  var abilityCount = Number(getConfigValue_(config, 'TRAIN_ABILITY_PER_TEST', 0));
  var usedVariant = {};
  var picked = [];

  if (abilityCount > 0) {
    var abilityPool = qb.filter(function(q){ return q.type === 'ability'; });
    picked = picked.concat(pickQuestions_(abilityPool, abilityCount, usedVariant));
  }

  var weakTags = computeTopWeakTags_(userKey, 3).map(function(t){ return t.tag; });
  var focusPool = [];
  if (weakTags.length > 0) {
    focusPool = qb.filter(function(q){
      return q.type === 'knowledge' && (weakTags.indexOf(q.tag1) >= 0 || weakTags.indexOf(q.tag2) >= 0 || weakTags.indexOf(q.tag3) >= 0);
    });
  }

  var remaining = qPer - picked.length;
  if (remaining > 0 && focusPool.length > 0) {
    picked = picked.concat(pickQuestions_(focusPool, remaining, usedVariant));
  }

  remaining = qPer - picked.length;
  if (remaining > 0) {
    var restPool = qb.filter(function(q){ return q.type === 'knowledge' && picked.indexOf(q) === -1; });
    picked = picked.concat(pickQuestions_(restPool, remaining, usedVariant));
  }

  if (picked.length < qPer) {
    var anyPool = qb.filter(function(q){ return picked.indexOf(q) === -1; });
    picked = picked.concat(pickQuestions_(anyPool, qPer - picked.length, usedVariant));
  }

  return picked.map(function(q){ return q.qId; });
}

function getMockExamQuestions_(year, part) {
  var y = String(year).toUpperCase();
  var p = String(part || 'FULL').toUpperCase();

  var qb = readQuestionBank_().filter(function(q) {
    var meta = parseExamQId_(q.qId);
    return q.status === 'published' &&
           isValidChoiceQuestion_(q) &&
           meta &&
           meta.year === y;
  });
  if (p !== 'FULL') {
    qb = qb.filter(function(q) {
      var meta = parseExamQId_(q.qId);
      return meta && meta.section === p;
    });
  }
  qb.sort(function(a, b) {
    var metaA = parseExamQId_(a.qId);
    var metaB = parseExamQId_(b.qId);
    if (!metaA || !metaB) return 0;
    return metaA.no - metaB.no;
  });
  return qb.map(function(q) { return q.qId; });
}

function findActiveMockAttempt_(userKey, year, part) {
  var testIndex = buildSekisanTestIndex_(year, part);

  var rows = readRecords_(getSheet_(SHEETS.Attempts));
  for (var i = rows.length - 1; i >= 0; i--) {
    var r = rows[i];
    if (r.userKey === userKey &&
        String(r.testIndex) === testIndex &&
        r.mode === 'mock' &&
        r.status === 'started') {
      return { row: r, index: i + 2 };
    }
  }
  return null;
}

function toQuestionForClient_(q) {
  return toQuestionForClient_full_(q);
}

// 全フィールド版（1問取得、復習用）
function toQuestionForClient_full_(q) {
  var choices = buildChoices_(q);
  return {
    qId: q.qId,
    segmentId: q.segmentId || '',
    stem: q.stem,
    choices: choices,
    imageUrl: q.imageUrl || '',
    choiceImageUrl: q.choiceImageUrl || '',
    correct: q.correct || '',
    explainShort: q.explainShort || '',
    explainLong: q.explainLong || '',
    explainA: q.explainA || '',
    explainB: q.explainB || '',
    explainC: q.explainC || '',
    explainD: q.explainD || '',
    explainE: q.explainE || '',
    tag1: q.tag1 || '',
    tag2: q.tag2 || '',
    tag3: q.tag3 || '',
    source_ref: q.source_ref || '',
    choiceCount: choices.length,
    answerCount: getAnswerCount_(q)
  };
}

// 軽量版（模試配信用 — explain省略でサイズ削減）
function toQuestionForClient_lite_(q) {
  var choices = buildChoices_(q);
  return {
    qId: q.qId,
    segmentId: q.segmentId || '',
    stem: q.stem,
    choices: choices,
    imageUrl: q.imageUrl || '',
    choiceImageUrl: q.choiceImageUrl || '',
    correct: q.correct || '',
    tag1: q.tag1 || '',
    choiceCount: choices.length,
    answerCount: getAnswerCount_(q)
  };
}

function buildChoices_(q) {
  var choices = [
    { key: 'A', text: q.choiceA },
    { key: 'B', text: q.choiceB },
    { key: 'C', text: q.choiceC },
    { key: 'D', text: q.choiceD }
  ];
  if (!isBlank_(q.choiceE)) {
    choices.push({ key: 'E', text: q.choiceE });
  }
  return choices;
}

function getAnswerCount_(q) {
  var raw = String(q.correct || '').trim();
  if (!raw) return 1;
  var parts = raw.split(',').map(function(s){ return String(s || '').trim(); }).filter(Boolean);
  return parts.length > 0 ? parts.length : 1;
}

function parseExamQId_(qId) {
  var m = String(qId || '').match(/^((?:H|R)\d+[A-Z]?)(?:takken|sekisan)-(\d+)$/i);
  if (!m) return null;
  var year = m[1].toUpperCase();
  var no = Number(m[2]);
  var section = sekisanSectionFromNo_(no);
  return { year: year, part: 'FULL', section: section, no: no };
}

function getExamSectionRules_(year, part) {
  var y = String(year || '').toUpperCase();
  var p = String(part || 'FULL').toUpperCase();
  if (!y) return [];
  var rules = [
    { label: '権利関係', noFrom: 1, noTo: 14, mode: 'ALL', required: 14 },
    { label: '法令上の制限', noFrom: 15, noTo: 22, mode: 'ALL', required: 8 },
    { label: '税・その他', noFrom: 23, noTo: 25, mode: 'ALL', required: 3 },
    { label: '宅地建物取引業法等', noFrom: 26, noTo: 45, mode: 'ALL', required: 20 },
    { label: '免除科目・その他', noFrom: 46, noTo: 50, mode: 'ALL', required: 5 }
  ];
  if (p === 'RIGHTS') return [rules[0]];
  if (p === 'LAW') return [rules[1]];
  if (p === 'BUSINESS') return [rules[3]];
  if (p === 'OTHER') return [rules[2], rules[4]];
  return rules;
}


function getExamRuleForQId_(qId) {
  var meta = parseExamQId_(qId);
  if (!meta) return null;
  var rules = getExamSectionRules_(meta.year, meta.part);
  for (var i = 0; i < rules.length; i++) {
    if (meta.no >= rules[i].noFrom && meta.no <= rules[i].noTo) return rules[i];
  }
  return null;
}

function buildExamSectionScores_(questions, answersMap) {
  var baseMeta = null;
  for (var i = 0; i < questions.length; i++) {
    var meta = parseExamQId_(questions[i].qId);
    if (meta) { baseMeta = meta; break; }
  }
  if (!baseMeta) return { sectionScores: [], penaltyTotal: 0 };
  var rules = getExamSectionRules_(baseMeta.year, baseMeta.part);
  if (!rules || rules.length === 0) return { sectionScores: [], penaltyTotal: 0 };

  var sectionScores = [];
  var penaltyTotal = 0;

  rules.forEach(function(rule){
    var sectionQs = questions.filter(function(q){
      var meta = parseExamQId_(q.qId);
      if (!meta) return false;
      return meta.year === baseMeta.year && meta.part === baseMeta.part && meta.no >= rule.noFrom && meta.no <= rule.noTo;
    });
    var totalCount = sectionQs.length;
    if (totalCount === 0) return;
    var answeredCount = 0;
    var correctCount = 0;
    sectionQs.forEach(function(q){
      var entry = answersMap[q.qId];
      if (!entry || !entry.chosenList || entry.chosenList.length === 0) return;
      answeredCount += 1;
      if (entry.isCorrect) correctCount += 1;
    });
    var required = rule.mode === 'PICK' ? rule.required : totalCount;
    var penalty = 0;
    if (rule.mode === 'PICK' && answeredCount > required) penalty = answeredCount - required;
    var score = correctCount - penalty;
    if (score < 0) score = 0;
    penaltyTotal += penalty;
    sectionScores.push({
      label: rule.label,
      mode: rule.mode,
      required: required,
      answered: answeredCount,
      correct: correctCount,
      penalty: penalty,
      score: score,
      total: totalCount
    });
  });

  return { sectionScores: sectionScores, penaltyTotal: penaltyTotal };
}

function computeTopWeakTags_(userKey, topN) {
  var tagRows = readRecords_(getSheet_(SHEETS.TagStats)).filter(function(r){ return r.userKey === userKey; });
  return computeTopWeakTagsFromRows_(tagRows, topN);
}

// Optimized: accepts pre-read and pre-filtered TagStats rows for user
function computeTopWeakTagsFromRows_(userTagRows, topN) {
  var WEAK_ERROR_THRESHOLD = 0.30;   // accuracy < 70% = weak
  var MIN_ANSWERED = 5;              // ignore tags with fewer answers

  var rows = userTagRows.slice();
  rows.forEach(function(r){
    r.answeredCount = Number(r.answeredCount || 0);
    r.correctCount = Number(r.correctCount || 0);
    r.errorRate = r.answeredCount > 0 ? (1 - r.correctCount / r.answeredCount) : 0;
  });

  var weak = rows.filter(function(r){
    return r.answeredCount >= MIN_ANSWERED && r.errorRate > WEAK_ERROR_THRESHOLD;
  });

  weak.sort(function(a,b){
    if (b.errorRate !== a.errorRate) return b.errorRate - a.errorRate;
    return b.answeredCount - a.answeredCount;
  });
  return weak.slice(0, topN).map(function(r){ return { tag: r.tag, errorRate: r.errorRate, answeredCount: r.answeredCount }; });
}

function computeFieldStats_(userKey) {
  var qb = readQuestionBank_();
  var tagStats = [];
  try {
    var tagSh = getDb_().getSheetByName(SHEETS.TagStats);
    if (tagSh) { tagStats = readRecords_(tagSh).filter(function(r) { return r.userKey === userKey; }); }
  } catch (e) {}
  return computeFieldStatsFromRows_(tagStats, qb);
}

// Optimized: accepts pre-read QuestionBank and user's TagStats rows
function computeFieldStatsFromRows_(userTagRows, questionBank) {
  var FIELD_ORDER = [
    { tag: '権利関係', label: '権利関係' },
    { tag: '法令上の制限', label: '法令上の制限' },
    { tag: '宅地建物取引業法等', label: '宅地建物取引業法等' },
    { tag: '税・その他', label: '税・その他' }
  ];

  var qb = questionBank.filter(function(q) {
    return q.status === 'published' && isValidChoiceQuestion_(q);
  });
  var qCount = {};
  qb.forEach(function(q) {
    var t = String(q.tag1 || '');
    qCount[t] = (qCount[t] || 0) + 1;
  });

  var tagMap = {};
  userTagRows.forEach(function(r) { tagMap[r.tag] = r; });

  return FIELD_ORDER.map(function(f) {
    var stat = tagMap[f.tag] || {};
    var answered = Number(stat.answeredCount || 0);
    var correct = Number(stat.correctCount || 0);
    return {
      tag: f.tag,
      label: f.label,
      totalQuestions: qCount[f.tag] || 0,
      answered: answered,
      accuracy: answered > 0 ? Math.round(correct / answered * 100) : null
    };
  });
}

function getRecentScores_(userKey, limit) {
  var rows = readRecords_(getSheet_(SHEETS.Attempts)).filter(function(r){ return r.userKey === userKey; });
  return getRecentScoresFromRows_(rows, limit);
}

// Optimized: accepts pre-read attempts rows
function getRecentScoresFromRows_(userAttempts, limit) {
  var rows = userAttempts.filter(function(r){ return r.status === 'submitted' || r.status === 'expired'; });
  rows.sort(function(a, b){
    return String(b.submittedAt || b.startedAt).localeCompare(String(a.submittedAt || a.startedAt));
  });
  return rows.slice(0, limit || 5).map(function(r){
    var score = r.scoreTotal;
    if (score === '' || score === null || score === undefined) score = 0;
    var tq = r.totalQuestions;
    var totalQ = (tq !== '' && tq !== null && tq !== undefined) ? Number(tq) : 0;
    var pct = totalQ > 0 ? Math.round(Number(score || 0) / totalQ * 100) : null;
    return {
      scoreTotal: Number(score || 0),
      totalQuestions: totalQ,
      pct: pct,
      mode: r.mode || '',
      submittedAt: r.submittedAt || ''
    };
  });
}

function getWrongAnswerRanking_(userKey, limit) {
  var sh = getSheet_(SHEETS.AttemptAnswers);
  var rows = readRecords_(sh);
  var attSh = getSheet_(SHEETS.Attempts);
  var attempts = readRecords_(attSh);
  var userAttemptIds = {};
  attempts.forEach(function(a) {
    if (a.userKey === userKey) userAttemptIds[a.attemptId] = true;
  });
  var wrongCounts = {};
  var totalCounts = {};
  rows.forEach(function(r) {
    if (!userAttemptIds[r.attemptId]) return;
    var qId = r.qId;
    totalCounts[qId] = (totalCounts[qId] || 0) + 1;
    if (String(r.isCorrect) === 'false' || r.isCorrect === false) {
      wrongCounts[qId] = (wrongCounts[qId] || 0) + 1;
    }
  });
  var ranking = [];
  Object.keys(wrongCounts).forEach(function(qId) {
    ranking.push({ qId: qId, wrongCount: wrongCounts[qId], totalCount: totalCounts[qId] || 0 });
  });
  ranking.sort(function(a, b) { return b.wrongCount - a.wrongCount || a.qId.localeCompare(b.qId); });
  var qb = getCachedQuestions_();
  var qMap = {};
  qb.forEach(function(q) { qMap[q.qId] = q; });
  return ranking.slice(0, limit || 10).map(function(r) {
    var q = qMap[r.qId] || {};
    return { qId: r.qId, stem: String(q.stem || '').substring(0, 60), wrongCount: r.wrongCount, totalCount: r.totalCount };
  });
}

function updateTagStats_(userKey, answerRows) {
  var sh = getSheet_(SHEETS.TagStats);
  var rows = readRecords_(sh);
  var map = {};
  rows.forEach(function(r){ map[r.userKey + '::' + r.tag] = r; });

  var now = formatDateTime_(getNow_(), 'Asia/Tokyo');

  answerRows.forEach(function(a){
    ['tag1','tag2','tag3'].forEach(function(tk){
      var tag = a[tk];
      if (!tag) return;
      var key = userKey + '::' + tag;
      var row = map[key];
      if (!row) {
        row = { userKey: userKey, tag: tag, answeredCount: 0, correctCount: 0, updatedAt: now };
        map[key] = row;
        rows.push(row);
      }
      row.answeredCount = Number(row.answeredCount || 0) + 1;
      row.correctCount = Number(row.correctCount || 0) + (a.isCorrect ? 1 : 0);
      row.updatedAt = now;
    });
  });

  // write back
  setHeaders_(sh, HEADERS[SHEETS.TagStats]);
  var out = rows.map(function(r){
    return [r.userKey, r.tag, r.answeredCount, r.correctCount, r.updatedAt];
  });
  appendRows_(sh, out);
}

function findAttemptById_(attemptId) {
  var rows = readRecords_(getSheet_(SHEETS.Attempts));
  for (var i = 0; i < rows.length; i++) {
    if (rows[i].attemptId === attemptId) return { row: rows[i], index: i + 2 };
  }
  return null;
}

function findActiveAttempt_(userKey, testIndex) {
  var rows = readRecords_(getSheet_(SHEETS.Attempts));
  for (var i = rows.length - 1; i >= 0; i--) {
    var r = rows[i];
    if (r.userKey === userKey && String(r.testIndex) === String(testIndex) && r.status === 'started') {
      return { row: r, index: i + 2 };
    }
  }
  return null;
}

function setConfigValue_(key, value) {
  var sh = getSheet_(SHEETS.Config);
  var values = sh.getDataRange().getValues();
  for (var i = 1; i < values.length; i++) {
    if (normalizeHeader_(values[i][0], 0) === String(key)) {
      values[i][1] = String(value);
      sh.getRange(i + 1, 1, 1, 2).setValues([[values[i][0], values[i][1]]]);
      return;
    }
  }
  appendRows_(sh, [[String(key), String(value)]]);
}

function updateTestPlanRow_(testIndex, fields) {
  var sh = getSheet_(SHEETS.TestPlan14);
  var headers = HEADERS[SHEETS.TestPlan14];
  var values = sh.getDataRange().getValues();
  for (var i = 1; i < values.length; i++) {
    if (String(values[i][0]) === String(testIndex)) {
      for (var k in fields) {
        var idx = headers.indexOf(k);
        if (idx >= 0) values[i][idx] = fields[k];
      }
      sh.getRange(i + 1, 1, 1, headers.length).setValues([values[i]]);
      return true;
    }
  }
  return false;
}

function adminFixTestPlanLabels_() {
  var labels = [
    [1, '第1回 権利関係 ウォームアップ'],
    [2, '第2回 権利関係 実践'],
    [3, '第3回 法令上の制限'],
    [4, '第4回 宅建業法 ウォームアップ'],
    [5, '第5回 宅建業法 実践1'],
    [6, '第6回 宅建業法 実践2'],
    [7, '第7回 税・その他'],
    [8, '第8回 権利・法令 横断'],
    [9, '第9回 宅建業法・その他 横断'],
    [10, '第10回 総合演習 1'],
    [11, '第11回 総合演習 2'],
    [12, '第12回 総合演習 3']
  ];

  var updated = 0;
  var missing = [];
  labels.forEach(function(pair){
    var ok = updateTestPlanRow_(pair[0], { label: pair[1] });
    if (ok) updated++;
    else missing.push(pair[0]);
  });

  return { updated: updated, total: labels.length, missing: missing };
}

function upsertByKey_(sheetName, keyField, rowObj) {
  var sh = getSheet_(sheetName);
  var headers = HEADERS[sheetName];
  var keyIdx = headers.indexOf(keyField);
  if (keyIdx < 0) throw new Error('Key field not found: ' + keyField);

  var values = sh.getDataRange().getValues();
  var keyVal = String(rowObj[keyField]);
  for (var i = 1; i < values.length; i++) {
    if (String(values[i][keyIdx]) === keyVal) {
      for (var c = 0; c < headers.length; c++) {
        var h = headers[c];
        if (rowObj.hasOwnProperty(h)) values[i][c] = rowObj[h];
      }
      sh.getRange(i + 1, 1, 1, headers.length).setValues([values[i]]);
      return 'updated';
    }
  }
  var newRow = headers.map(function(h){ return rowObj.hasOwnProperty(h) ? rowObj[h] : ''; });
  appendRows_(sh, [newRow]);
  return 'inserted';
}

function normalizeHeader_(h, idx) {
  var s = String(h || '');
  if (idx === 0) s = s.replace(/^\uFEFF/, '');
  return s.trim();
}

function normalizeValue_(v) {
  return String(v == null ? '' : v);
}

function isBlank_(v) {
  return normalizeValue_(v).trim() === '';
}

function validateCsvForSheet_(sheetName, csvText) {
  var result = {
    ok: true,
    rowCount: 0,
    validCount: 0,
    errorCount: 0,
    warningCount: 0,
    errors: [],
    warnings: [],
    rows: [],
    _rowErrors: {}
  };

  if (!HEADERS[sheetName]) {
    addError_(result, 1, 'sheet', 'Unknown sheet: ' + sheetName);
    result.ok = false;
    return result;
  }

  var data = Utilities.parseCsv(csvText || '');
  if (data.length === 0) {
    addError_(result, 1, 'csv', 'CSV is empty');
    result.ok = false;
    return result;
  }

  var header = data[0].map(function(h, i){ return normalizeHeader_(h, i); });
  var expected = HEADERS[sheetName];

  if (header.length !== expected.length) {
    addError_(result, 1, 'header', 'Header length mismatch. expected=' + expected.length + ', actual=' + header.length);
    result.ok = false;
    return result;
  }

  for (var c = 0; c < expected.length; c++) {
    if (header[c] !== expected[c]) {
      addError_(result, 1, 'header', 'Header mismatch at col ' + (c + 1) + '. expected=' + expected[c] + ', actual=' + header[c]);
    }
  }

  if (result.errorCount > 0) {
    result.ok = false;
    return result;
  }

  var rows = [];
  var rowCount = 0;

  var existingIds = {};
  if (sheetName === SHEETS.QuestionBank) {
    readQuestionBank_().forEach(function(r){
      if (r.qId) existingIds[String(r.qId)] = true;
    });
  }

  for (var i = 1; i < data.length; i++) {
    var rowNum = i + 1;
    var row = data[i] || [];
    var allEmpty = true;
    for (var k = 0; k < row.length; k++) {
      if (!isBlank_(row[k])) { allEmpty = false; break; }
    }
    if (allEmpty) continue;
    rowCount += 1;

    if (row.length !== expected.length) {
      addError_(result, rowNum, 'row', 'Column count mismatch. expected=' + expected.length + ', actual=' + row.length);
      continue;
    }

    var values = row.map(function(v){ return normalizeValue_(v); });
    var obj = {};
    for (var j = 0; j < expected.length; j++) {
      obj[expected[j]] = values[j];
    }

    if (sheetName === SHEETS.QuestionBank) {
      validateQuestionRow_(result, rowNum, obj, existingIds);
    }

    rows.push(values);
  }

  result.rows = rows;
  result.rowCount = rowCount;
  var errorRows = Object.keys(result._rowErrors).filter(function(r){ return Number(r) > 1; }).length;
  result.validCount = Math.max(0, result.rowCount - errorRows);
  result.ok = result.errorCount === 0;

  return result;
}

function validateQuestionRow_(result, rowNum, obj, existingIds) {
  var required = ['qId','segmentId','type','difficulty','tag1','stem','choiceA','choiceB','choiceC','choiceD','correct','explainShort','status'];
  required.forEach(function(f){
    if (isBlank_(obj[f])) addError_(result, rowNum, f, 'Required');
  });

  var rawId = obj.qId || '';
  if (!isBlank_(rawId) && rawId.trim() !== rawId) {
    addError_(result, rowNum, 'qId', 'Leading/trailing spaces');
  }

  var qId = rawId.trim();
  if (qId) {
    if (existingIds[qId]) addError_(result, rowNum, 'qId', 'Duplicate qId (existing or in CSV): ' + qId);
    existingIds[qId] = true;
  }

  var type = String(obj.type || '').trim().toLowerCase();
  if (type && type !== 'knowledge' && type !== 'ability') {
    addError_(result, rowNum, 'type', 'Invalid type: ' + obj.type);
  }

  var diff = String(obj.difficulty || '').trim();
  if (diff && !/^[1-5]$/.test(diff)) {
    addError_(result, rowNum, 'difficulty', 'Difficulty must be 1-5');
  }

  var rev = String(obj.revisionFlag || '').trim();
  if (rev && rev !== '0' && rev !== '1') {
    addError_(result, rowNum, 'revisionFlag', 'revisionFlag must be 0 or 1');
  }

  var status = String(obj.status || '').trim().toLowerCase();
  if (status && status !== 'draft' && status !== 'published') {
    addError_(result, rowNum, 'status', 'Invalid status: ' + obj.status);
  }

  var choiceE = String(obj.choiceE || '').trim();
  var hasE = !isBlank_(choiceE);

  var correct = String(obj.correct || '').trim().toUpperCase();
  var parts = correct.split(',').map(function(s){ return s.trim(); }).filter(Boolean);
  if (parts.length > 1) {
    addWarning_(result, rowNum, 'correct', 'Multiple answers detected');
  }
  if (parts.length === 0) {
    addError_(result, rowNum, 'correct', 'Correct is empty');
  } else {
    for (var p = 0; p < parts.length; p++) {
      var c = parts[p];
      if (hasE) {
        if (!/^[A-E]$/.test(c)) addError_(result, rowNum, 'correct', 'Correct must be A-E');
      } else {
        if (!/^[A-D]$/.test(c)) addError_(result, rowNum, 'correct', 'Correct must be A-D');
      }
    }
  }
  if (parts.length > 0) {
    var map = {
      A: String(obj.choiceA || '').trim(),
      B: String(obj.choiceB || '').trim(),
      C: String(obj.choiceC || '').trim(),
      D: String(obj.choiceD || '').trim(),
      E: String(obj.choiceE || '').trim()
    };
    for (var p2 = 0; p2 < parts.length; p2++) {
      if (isBlank_(map[parts[p2]])) {
        addError_(result, rowNum, 'correct', 'Correct points to empty choice');
      }
    }
  }
}

function addError_(result, rowNum, field, message) {
  result.errors.push({ row: rowNum, field: field, message: message });
  result.errorCount += 1;
  if (result._rowErrors) result._rowErrors[rowNum] = true;
}

function addWarning_(result, rowNum, field, message) {
  result.warnings.push({ row: rowNum, field: field, message: message });
  result.warningCount += 1;
}


// 「今日の一手」判定ロジック
function computeNextAction_(unlocked, submittedMap, weakTags, next) {
  // 1. 今週のテスト（recommended: true）- 提出済みでも表示
  var thisWeekTests = [];
  for (var i = 0; i < unlocked.length; i++) {
    var t = unlocked[i];
    if (t.recommended) {
      thisWeekTests.push(t);
    }
  }
  thisWeekTests.sort(function(a, b) {
    return Number(a.testIndex || 0) - Number(b.testIndex || 0);
  });

  if (thisWeekTests.length > 0) {
    var first = thisWeekTests[0];
    return {
      type: 'test',
      label: first.label,
      testIndex: first.testIndex,
      unlockWeek: first.unlockWeek,
      targetSegments: first.targetSegments || '',
      questionsPerTest: first.questionsPerTest || 30,
      reason: '今週のテストです'
    };
  }
  
  // 2. 弱点復習
  if (weakTags && weakTags.length > 0) {
    var tagNames = weakTags.map(function(w){ return w.tag; });
    return {
      type: 'practice',
      label: '弱点復習',
      tags: tagNames,
      reason: '弱点タグ: ' + tagNames.slice(0, 3).join(', ')
    };
  }
  
  // 3. 次回テスト
  if (next) {
    return {
      type: 'upcoming',
      label: next.label,
      testIndex: next.testIndex,
      unlockWeek: next.unlockWeek,
      reason: '次回解放: 第' + next.unlockWeek + '週'
    };
  }
  
  // 4. 全て完了
  return {
    type: 'complete',
    label: '全テスト完了',
    reason: 'お疲れ様でした'
  };
}

// ============================================================
// Gemini AI Study Advice
// ============================================================

function generateStudyAdvice_(scoreData) {
  var config = getConfigMap_();
  var apiKey = getConfigValue_(config, 'GEMINI_API_KEY', '');
  if (!apiKey) return { text: '', debug: 'no_api_key' };

  var prompt = buildAdvicePrompt_(scoreData);
  var url = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=' + apiKey;
  var payload = {
    contents: [{ parts: [{ text: prompt }] }],
    generationConfig: { maxOutputTokens: 600, temperature: 0.7 }
  };
  var options = {
    method: 'post',
    contentType: 'application/json',
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  };

  try {
    var response = UrlFetchApp.fetch(url, options);
    var code = response.getResponseCode();
    if (code !== 200) {
      return { text: '', debug: 'http_' + code + ':' + response.getContentText().substring(0, 150) };
    }
    var json = JSON.parse(response.getContentText());
    if (json.candidates && json.candidates[0] && json.candidates[0].content && json.candidates[0].content.parts) {
      var text = json.candidates[0].content.parts[0].text || '';
      return { text: text, debug: 'ok(' + text.length + ')' };
    }
    return { text: '', debug: 'no_candidates:' + JSON.stringify(json).substring(0, 150) };
  } catch (e) {
    return { text: '', debug: 'exception:' + String(e.message || e).substring(0, 150) };
  }
}

function buildAdvicePrompt_(data) {
  var lines = [];
  lines.push('あなたは宅地建物取引士（宅建）試験の学習支援に詳しいコーチです。');
  lines.push('以下の試験結果と過去の学習履歴を分析し、受験者への具体的な学習アドバイスを日本語で4?6行で書いてください。');
  lines.push('');
  lines.push('【重要な指示】');
  lines.push('1. 必ず最初に「良かった点・成長した点」を1?2点具体的に褒めてください（例：正答率の向上、特定分野の強さ、継続的な学習姿勢、解答ルール理解による減点なしなど）');
  lines.push('2. 改善点は「?するとさらに良くなります」というポジティブな表現で伝えてください');
  lines.push('3. 【必須】毎回、資格試験勉強のコツを1つ具体的に紹介してください。以下から選んで詳しく説明:');
  lines.push('   - 過去問の活用法（解説をしっかり読む、間違えた問題だけノートにまとめる、時間を計って解く）');
  lines.push('   - 暗記術（語呂合わせ、図解・イラスト化、音読、繰り返しの間隔を空ける分散学習）');
  lines.push('   - 短時間で効率を上げる勉強法（スキマ時間活用、ポモドーロテクニック、朝型学習）');
  lines.push('   - 理解を深める方法（人に説明するつもりで学ぶ、なぜ？を繰り返す、実務と結びつける）');
  lines.push('   - モチベーション維持（小さな目標設定、学習記録をつける、合格後のイメージ）');
  lines.push('   - 試験本番の戦略（時間配分、わからない問題は後回し、見直しの仕方）');
  lines.push('4. 上記に加え、弱点分野やスコア推移に基づく個別アドバイスも含めてください');
  lines.push('5. 点数が低くても批判せず、「伸びしろがある」「ここを押さえれば一気に伸びる」等の前向きな表現を使ってください');
  lines.push('6. 最後に励ましの言葉を1文含めてください');
  lines.push('');
  lines.push('【今回の試験結果】');
  lines.push('総合得点: ' + (data.scoreTotal || 0) + '点 / ' + (data.totalQuestions || 0) + '問');
  lines.push('誤答数: ' + (data.wrongCount || 0) + '問');

  if (data.weakTags && data.weakTags.length > 0) {
    lines.push('');
    lines.push('【弱点分野（累積）】');
    data.weakTags.forEach(function(w) {
      lines.push('- ' + w.tag + ' (正答率: ' + Math.round((1 - w.errorRate) * 100) + '%, 回答数: ' + w.answeredCount + ')');
    });
  }

  if (data.sectionScores && data.sectionScores.length > 0) {
    lines.push('');
    lines.push('【セクション別成績】');
    data.sectionScores.forEach(function(s) {
      lines.push('- ' + s.label + ': ' + s.correct + '/' + s.answered + '正解' + (s.penalty > 0 ? ' (減点' + s.penalty + ')' : ''));
    });
  }

  if (data.scoreHistory && data.scoreHistory.length > 0) {
    lines.push('');
    lines.push('【過去のスコア推移（直近' + data.scoreHistory.length + '回）】');
    var modeLabels = { mini: 'ミニテスト', field: '分野別', practice: '弱点演習', mock: '模試', test: '全問テスト' };
    data.scoreHistory.forEach(function(h, i) {
      var pctStr = h.pct !== null && h.pct !== undefined ? h.pct + '%' : '-';
      var modeLabel = modeLabels[h.mode] || h.mode || '';
      lines.push('- ' + (i + 1) + '回前: ' + h.scoreTotal + '/' + (h.totalQuestions || '?') + '問 (' + pctStr + ') [' + modeLabel + ']');
    });
    // モード別平均正答率
    var modeStats = {};
    data.scoreHistory.forEach(function(h) {
      var m = h.mode || 'other';
      if (!modeStats[m]) modeStats[m] = { sum: 0, count: 0 };
      if (h.pct !== null && h.pct !== undefined) {
        modeStats[m].sum += h.pct;
        modeStats[m].count++;
      }
    });
    var modeAvgs = [];
    Object.keys(modeStats).forEach(function(m) {
      if (modeStats[m].count > 0) {
        var avg = Math.round(modeStats[m].sum / modeStats[m].count);
        var label = modeLabels[m] || m;
        modeAvgs.push(label + ': 平均' + avg + '% (' + modeStats[m].count + '回)');
      }
    });
    if (modeAvgs.length > 0) {
      lines.push('');
      lines.push('【テスト種別ごとの平均正答率】');
      modeAvgs.forEach(function(s) { lines.push('- ' + s); });
    }
  }

  if (data.wrongRanking && data.wrongRanking.length > 0) {
    lines.push('');
    lines.push('【繰り返し間違える問題TOP' + data.wrongRanking.length + '】');
    data.wrongRanking.forEach(function(r) {
      lines.push('- ' + r.stem + '... (' + r.wrongCount + '/' + r.totalCount + '回不正解)');
    });
  }

  if (data.fieldStats && data.fieldStats.length > 0) {
    var hasData = data.fieldStats.some(function(f) { return f.answered > 0; });
    if (hasData) {
      lines.push('');
      lines.push('【分野別正答率】');
      data.fieldStats.forEach(function(f) {
        if (f.answered > 0) {
          lines.push('- ' + f.label + ': ' + f.accuracy + '% (' + f.answered + '問回答済み / 全' + f.totalQuestions + '問)');
        }
      });
    }
  }

  lines.push('');
  lines.push('上記を踏まえ、以下の3点を必ず含めてください:');
  lines.push('(1) どの分野を優先して勉強すべきか（弱点分野の重点練習には「分野別テスト」機能を推奨）');
  lines.push('(2) 今日からすぐに実践できる具体的な勉強法のコツ（上記の【重要な指示】3.から1つ選んで詳しく）');
  lines.push('(3) 次のテストに向けた目標設定（例：正答率○%を目指す、○○分野を集中的に等）');
  return lines.join('\n');
}

