// db.gs
var SHEETS = {
  Config: 'Config',
  Users: 'Users',
  QuestionBank: 'QuestionBank',
  UserAccess: 'UserAccess',
  TestPlan14: 'TestPlan14',
  TestSets: 'TestSets',
  Attempts: 'Attempts',
  AttemptAnswers: 'AttemptAnswers',
  TagStats: 'TagStats'
};

var HEADERS = {};
HEADERS[SHEETS.Config] = ['key', 'value'];
HEADERS[SHEETS.Users] = ['userKey', 'email', 'displayName', 'createdAt', 'recoveryCode'];
HEADERS[SHEETS.QuestionBank] = [
  'qId', 'segmentId', 'type', 'difficulty',
  'tag1', 'tag2', 'tag3', 'lawTag',
  'revisionFlag', 'conceptId', 'variantGroupId', 'source_ref',
  'imageUrl', 'choiceImageUrl',
  'stem', 'choiceA', 'choiceB', 'choiceC', 'choiceD', 'choiceE',
  'explainA', 'explainB', 'explainC', 'explainD', 'explainE',
  'correct', 'explainShort', 'explainLong', 'status', 'updatedAt'
];
HEADERS[SHEETS.UserAccess] = ['email', 'role', 'managerEmail', 'active', 'updatedAt', 'displayName'];
HEADERS[SHEETS.TestPlan14] = [
  'testIndex', 'label', 'targetSegments', 'questionsPerTest',
  'abilityCount', 'revisionMinCount', 'unlockWeek', 'notes'
];
HEADERS[SHEETS.TestSets] = ['testIndex', 'generatedAt', 'questionIds'];
HEADERS[SHEETS.Attempts] = [
  'attemptId', 'userKey', 'testIndex', 'mode',
  'startedAt', 'endsAt', 'submittedAt',
  'scoreTotal', 'scoreAbility', 'status', 'totalQuestions'
];
HEADERS[SHEETS.AttemptAnswers] = [
  'attemptId', 'qId', 'chosen', 'isCorrect', 'answeredAt',
  'timeSpentSec', 'tag1', 'tag2', 'tag3'
];
HEADERS[SHEETS.TagStats] = ['userKey', 'tag', 'answeredCount', 'correctCount', 'updatedAt'];

function migrateQuestionBankSchema_() {
  var sh = getSheet_(SHEETS.QuestionBank);
  var expected = HEADERS[SHEETS.QuestionBank];
  var lastCol = Math.max(1, sh.getLastColumn());
  var header = sh.getRange(1, 1, 1, lastCol).getValues()[0]
    .map(function(h, i){ return normalizeHeader_(h, i); });

  function sameArray(a, b) {
    if (a.length !== b.length) return false;
    for (var i = 0; i < a.length; i++) if (a[i] !== b[i]) return false;
    return true;
  }

  if (sameArray(header, expected)) {
    return { status: 'ok', updated: false };
  }

  var prev = [
    'qId', 'segmentId', 'type', 'difficulty',
    'tag1', 'tag2', 'tag3', 'lawTag',
    'revisionFlag', 'conceptId', 'variantGroupId', 'source_ref',
    'stem', 'choiceA', 'choiceB', 'choiceC', 'choiceD', 'choiceE',
    'explainA', 'explainB', 'explainC', 'explainD', 'explainE',
    'correct', 'explainShort', 'explainLong', 'status', 'updatedAt'
  ];

  var old = [
    'qId', 'segmentId', 'type', 'difficulty',
    'tag1', 'tag2', 'tag3', 'lawTag',
    'revisionFlag', 'conceptId', 'variantGroupId', 'source_ref',
    'stem', 'choiceA', 'choiceB', 'choiceC', 'choiceD', 'choiceE',
    'correct', 'explainShort', 'explainLong', 'status', 'updatedAt'
  ];

  if (sameArray(header, prev)) {
    // Insert imageUrl before stem to preserve existing data alignment
    var insertImgAt = prev.indexOf('stem') + 1; // 1-based
    sh.insertColumns(insertImgAt, 1);
    sh.getRange(1, 1, 1, expected.length).setValues([expected]);
    return { status: 'ok', updated: true, insertedColumns: 1 };
  }

  if (sameArray(header, old)) {
    // Insert explainA~E before correct, then imageUrl before stem
    var insertExplainAt = old.indexOf('correct') + 1; // 1-based
    sh.insertColumns(insertExplainAt, 5);
    var insertImageAt = old.indexOf('stem') + 1; // 1-based
    sh.insertColumns(insertImageAt, 1);
    sh.getRange(1, 1, 1, expected.length).setValues([expected]);
    return { status: 'ok', updated: true, insertedColumns: 6 };
  }

  return { status: 'manual', message: 'QuestionBank header mismatch. Manual review required.', header: header };
}

function getScriptProps_() {
  return PropertiesService.getScriptProperties();
}

// Intentionally empty to avoid accidentally pointing to another app's DB.
// Set via Script Properties (DB_SPREADSHEET_ID) or run setup_().
var FALLBACK_DB_ID_ = '';

function getDbId_() {
  return getScriptProps_().getProperty('DB_SPREADSHEET_ID') || FALLBACK_DB_ID_;
}

function setDbId_(id) {
  getScriptProps_().setProperty('DB_SPREADSHEET_ID', id);
}

var _dbInstance = null;
var _dbId = null;
function getDb_() {
  var id = getDbId_();
  if (!id) {
    throw new Error('DBが未設定です。setup_()を実行してください。');
  }
  if (_dbInstance && _dbId === id) return _dbInstance;
  _dbId = id;
  _dbInstance = SpreadsheetApp.openById(id);
  return _dbInstance;
}

function getSheet_(name) {
  var ss = getDb_();
  var sh = ss.getSheetByName(name);
  if (!sh) {
    throw new Error('シートが見つかりません: ' + name);
  }
  return sh;
}

function ensureSheet_(ss, name) {
  var sh = ss.getSheetByName(name);
  if (!sh) sh = ss.insertSheet(name);
  return sh;
}

function setHeaders_(sheet, headers) {
  sheet.clear();
  sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
  sheet.setFrozenRows(1);
}

function readRecords_(sheet) {
  var values = sheet.getDataRange().getValues();
  if (values.length <= 1) return [];
  // Normalize headers to avoid BOM/whitespace mismatches from CSV imports
  var headers = values[0].map(function(h, i){ return normalizeHeader_(h, i); });
  var rows = [];
  for (var i = 1; i < values.length; i++) {
    var row = values[i];
    var obj = {};
    for (var c = 0; c < headers.length; c++) {
      obj[headers[c]] = row[c];
    }
    rows.push(obj);
  }
  return rows;
}

// Remove sample/template rows from QuestionBank (qId like "Q1" or source_ref starts with "SAMPLE-")
function adminDeleteSampleQuestions_(dryRun) {
  var sh = getSheet_(SHEETS.QuestionBank);
  var values = sh.getDataRange().getValues();
  if (values.length <= 1) return { deleted: 0, rows: [] };
  var headers = values[0].map(function(h, i){ return normalizeHeader_(h, i); });
  var qIdx = headers.indexOf('qId');
  var srcIdx = headers.indexOf('source_ref');
  if (qIdx < 0) throw new Error('qId header not found');
  if (srcIdx < 0) srcIdx = -1;

  var toDelete = [];
  var qIds = [];
  for (var i = 1; i < values.length; i++) {
    var qId = String(values[i][qIdx] || '').trim();
    var src = srcIdx >= 0 ? String(values[i][srcIdx] || '').trim() : '';
    var isSampleId = /^Q\d+$/.test(qId);
    var isSampleSrc = src.toUpperCase().indexOf('SAMPLE-') === 0;
    if (isSampleId || isSampleSrc) {
      toDelete.push(i + 1); // sheet row number
      qIds.push(qId);
    }
  }

  if (!dryRun) {
    for (var j = toDelete.length - 1; j >= 0; j--) {
      sh.deleteRow(toDelete[j]);
    }
  }

  return { deleted: toDelete.length, qIds: qIds, dryRun: !!dryRun };
}

function appendRows_(sheet, rows) {
  if (!rows || rows.length === 0) return;
  sheet.getRange(sheet.getLastRow() + 1, 1, rows.length, rows[0].length).setValues(rows);
}

function setup_(force) {
  if (!force && getDbId_()) {
    return { status: 'exists', id: getDbId_() };
  }
  var today = Utilities.formatDate(new Date(), 'Asia/Tokyo', 'yyyyMMdd');
  var ss = SpreadsheetApp.create(APP_DB_PREFIX_ + today);
  setDbId_(ss.getId());

  // create sheets and headers
  for (var key in SHEETS) {
    var name = SHEETS[key];
    var sh = ensureSheet_(ss, name);
    setHeaders_(sh, HEADERS[name]);
  }

  initConfig_();
  initTestPlan_();
  initSampleData_();

  return { status: 'created', id: ss.getId(), url: ss.getUrl() };
}

function setup() {
  return setup_(false);
}

function setupForce() {
  return setup_(true);
}

function initConfig_() {
  var sh = getSheet_(SHEETS.Config);
  var rows = [
    ['PROGRAM_START_DATE', '2026-04-11'],
    ['EXAM_DATE', ''],
    ['TIME_LIMIT_MINUTES', '30'],
    ['QUESTIONS_PER_TEST', '20'],
    ['ABILITY_PER_TEST', '0'],
    ['MINI_TIME_LIMIT_MINUTES', '15'],
    ['MINI_QUESTIONS_PER_TEST', '10'],
    ['MINI_ABILITY_PER_TEST', '0'],
    ['TRAIN_TIME_LIMIT_MINUTES', '10'],
    ['TRAIN_QUESTIONS_PER_TEST', '10'],
    ['TRAIN_ABILITY_PER_TEST', '0'],
    ['MOCK_TIME_LIMIT_MINUTES', '120'],
    ['REVISION_RATIO', '0.2'],
    ['SHARED_TESTSET_MODE', 'ON'],
    ['TIMEZONE', 'Asia/Tokyo']
  ];
  appendRows_(sh, rows);
}

// 設定値を更新する関数
function updateConfigValue_(key, newValue) {
  var sh = getSheet_(SHEETS.Config);
  var data = sh.getDataRange().getValues();

  // ヘッダー行をスキップして検索
  for (var i = 1; i < data.length; i++) {
    if (data[i][0] === key) {
      sh.getRange(i + 1, 2).setValue(newValue);
      Logger.log('Updated ' + key + ' to ' + newValue);
      return true;
    }
  }

  // 見つからなければ新規追加
  sh.appendRow([key, newValue]);
  Logger.log('Added new config: ' + key + ' = ' + newValue);
  return true;
}

// 試験日を修正する一時関数
function fixExamDate_() {
  updateConfigValue_('EXAM_DATE', '');
  Logger.log('試験日を空欄に更新しました');
}

function initTestPlan_() {
  var sh = getSheet_(SHEETS.TestPlan14);
  var plan = [
    [1, '第1回 Ⅰ建築一般 ウォームアップ', 'sekisan_I', 20, 0, 2, 0, '基礎用語と出題形式に慣れる回'],
    [2, '第2回 Ⅰ建築一般 実践1', 'sekisan_I', 20, 0, 2, 1, '建築一般の頻出テーマを反復'],
    [3, '第3回 Ⅰ建築一般 実践2', 'sekisan_I', 20, 0, 2, 2, '苦手論点の洗い出し'],
    [4, '第4回 Ⅰ建築一般 仕上げ', 'sekisan_I', 20, 0, 2, 3, 'Ⅰ分野の総合確認'],
    [5, '第5回 Ⅱ数量積算 ウォームアップ', 'sekisan_II', 20, 0, 2, 4, '積算の基本ルールを整理'],
    [6, '第6回 Ⅱ数量積算 実践1', 'sekisan_II', 20, 0, 2, 5, '数量積算の頻出論点を反復'],
    [7, '第7回 Ⅱ数量積算 実践2', 'sekisan_II', 20, 0, 2, 6, '計算と判断の精度を上げる'],
    [8, '第8回 Ⅱ数量積算 仕上げ', 'sekisan_II', 20, 0, 2, 7, 'Ⅱ分野の総合確認'],
    [9, '第9回 総合演習 1', 'sekisan_I,sekisan_II', 25, 0, 3, 8, '全範囲の横断演習'],
    [10, '第10回 総合演習 2', 'sekisan_I,sekisan_II', 25, 0, 3, 9, '本試験ペースの確認'],
    [11, '第11回 総合演習 3', 'sekisan_I,sekisan_II', 25, 0, 3, 10, '頻出分野の取りこぼし防止'],
    [12, '第12回 総合演習 4', 'sekisan_I,sekisan_II', 25, 0, 3, 11, '直前総仕上げ']
  ];
  appendRows_(sh, plan);
}

function initSampleData_() {
  var qb = getSheet_(SHEETS.QuestionBank);

  var tags = [
    'Ⅰ建築一般', 'Ⅱ数量積算'
  ];

  var now = Utilities.formatDate(new Date(), 'Asia/Tokyo', 'yyyy-MM-dd HH:mm:ss');

  // QuestionBank (sample)
  var segments = [
    'sekisan_I', 'sekisan_II'
  ];
  var qRows = [];
  var qId = 1;
  for (var s = 0; s < segments.length; s++) {
    for (var k = 0; k < 4; k++) {
      var t1 = tags[(s + k) % tags.length];
      var t2 = tags[(s + k + 1) % tags.length];
      var t3 = tags[(s + k + 2) % tags.length];
      qRows.push([
        'Q' + (qId++),
        segments[s],
        'knowledge',
        2,
        segments[s] === 'sekisan_I' ? 'Ⅰ建築一般' : 'Ⅱ数量積算',
        'H25',
        '',
        '',
        (k % 3 === 0) ? 1 : 0,
        '',
        'VG-' + segments[s] + '-' + k,
        'SAMPLE-' + segments[s] + '-' + k,
        '',
        '次のうち正しい記述はどれか（' + (segments[s] === 'sekisan_I' ? 'Ⅰ建築一般' : 'Ⅱ数量積算') + '）',
        '選択肢A', '選択肢B', '選択肢C', '選択肢D', '選択肢E',
        '', '', '', '', '',
        'A',
        '解説（要点）',
        '解説（詳細）',
        'published',
        now
      ]);
    }
  }

  appendRows_(qb, qRows);
}

// === CacheService Helpers ===
var CACHE_TTL_CONFIG = 300;      // 5 minutes
var CACHE_TTL_TESTPLAN = 300;    // 5 minutes
var CACHE_TTL_QUESTIONS = 3600;  // 1 hour (was 10min)   // 10 minutes

function getCache_() {
  return CacheService.getScriptCache();
}

function getCachedConfig_() {
  var cache = getCache_();
  var cached = cache.get('config_map');
  if (cached) {
    try { return JSON.parse(cached); } catch(e) {}
  }
  var sh = getSheet_(SHEETS.Config);
  var values = sh.getDataRange().getValues();
  var map = {};
  if (values.length > 1) {
    for (var i = 1; i < values.length; i++) {
      var key = normalizeHeader_(values[i][0], 0);
      if (key) map[key] = values[i][1];
    }
  }
  cache.put('config_map', JSON.stringify(map), CACHE_TTL_CONFIG);
  return map;
}

function getCachedTestPlan_() {
  var cache = getCache_();
  var cached = cache.get('testplan_rows');
  if (cached) {
    try { return JSON.parse(cached); } catch(e) {}
  }
  var sh = getSheet_(SHEETS.TestPlan14);
  var values = sh.getDataRange().getValues();
  var headers = HEADERS[SHEETS.TestPlan14];
  var rows = [];
  if (values.length > 1) {
    for (var i = 1; i < values.length; i++) {
      var rowVals = values[i];
      if (String(rowVals[0] || '').trim() === '') continue;
      var obj = {};
      for (var c = 0; c < headers.length; c++) obj[headers[c]] = rowVals[c];
      rows.push(obj);
    }
  }
  cache.put('testplan_rows', JSON.stringify(rows), CACHE_TTL_TESTPLAN);
  return rows;
}

// Script-scope cache for full QuestionBank (avoids 100KB CacheService limit)
var _questionsCache = null;
var _questionsCacheTs = 0;

function getCachedQuestions_() {
  // 1. Script-scope cache (instant, same execution)
  var now = Date.now();
  if (_questionsCache && (now - _questionsCacheTs) < CACHE_TTL_QUESTIONS * 1000) {
    return _questionsCache;
  }

  // 2. CacheService flag check (cross-execution, lightweight)
  var cache = getCache_();
  var cacheVersion = cache.get('questions_version');

  // 3. Read from sheet
  var sh = getSheet_(SHEETS.QuestionBank);
  var values = sh.getDataRange().getValues();
  if (values.length <= 1) {
    _questionsCache = [];
    _questionsCacheTs = now;
    return [];
  }
  var headers = values[0].map(function(h, i){ return normalizeHeader_(h, i); });
  var rows = [];
  for (var i = 1; i < values.length; i++) {
    var row = values[i];
    var obj = {};
    for (var c = 0; c < headers.length; c++) obj[headers[c]] = row[c];
    if (obj.status !== 'published') continue;
    rows.push(obj);
  }

  // Store in script-scope (no size limit)
  _questionsCache = rows;
  _questionsCacheTs = now;

  // Store lightweight version marker in CacheService
  try { cache.put('questions_version', String(now), CACHE_TTL_QUESTIONS); } catch(e) {}
  return rows;
}

function clearAllCache_() {
  var cache = getCache_();
  cache.removeAll(['config_map', 'testplan_rows', 'questions_list']);
}

