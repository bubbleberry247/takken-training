/**
 * QuestionBankシートにCSVをインポート（管理者用・一時関数）
 * GASエディタから▶実行するだけでOK
 */

/** 土木: GASエディタで▶実行 */
function ADMIN_importDoboku() {
  var fileId = '1mPp0JpnSV21G-9cKHsXFOKDp4WzrkLp1';
  var url = 'https://www.googleapis.com/drive/v3/files/' + fileId + '?alt=media';
  var token = ScriptApp.getOAuthToken();
  var response = UrlFetchApp.fetch(url, {
    headers: { 'Authorization': 'Bearer ' + token },
    muteHttpExceptions: true
  });

  Logger.log('HTTP status: ' + response.getResponseCode());
  if (response.getResponseCode() !== 200) {
    Logger.log('Error: ' + response.getContentText().substring(0, 500));
    return { ok: false, error: response.getContentText().substring(0, 200) };
  }

  var csvText = response.getContentText('UTF-8');
  Logger.log('CSV size: ' + csvText.length + ' chars');
  return adminImportCsvText_(csvText);
}

function adminImportCsvText_(csvText) {
  if (csvText.charCodeAt(0) === 0xFEFF) csvText = csvText.substring(1);

  var lines = Utilities.parseCsv(csvText);
  if (lines.length < 2) {
    Logger.log('ERROR: No data parsed');
    return { ok: false, error: 'No data' };
  }

  var headers = lines[0];
  Logger.log('Parsed: ' + lines.length + ' lines, ' + headers.length + ' columns');

  var sheet = getSheet_(SHEETS.QuestionBank);
  var oldCount = sheet.getLastRow();
  Logger.log('Before: ' + oldCount + ' rows');

  sheet.clear();
  SpreadsheetApp.flush();

  sheet.getRange(1, 1, 1, headers.length).setValues([headers]);

  var dataLines = lines.slice(1);
  var batchSize = 200;
  for (var i = 0; i < dataLines.length; i += batchSize) {
    var batch = dataLines.slice(i, Math.min(i + batchSize, dataLines.length));
    sheet.getRange(i + 2, 1, batch.length, headers.length).setValues(batch);
  }

  SpreadsheetApp.flush();
  Logger.log('Done: ' + dataLines.length + ' questions imported');
  return { ok: true, imported: dataLines.length, columns: headers.length };
}

/** 全中断中mock attemptをexpiredにする（クリーンアップ） */
function ADMIN_expireAllMockAttempts() {
  var attempts = readRecords_(getSheet_(SHEETS.Attempts));
  var fixed = 0;
  for (var i = 0; i < attempts.length; i++) {
    var r = attempts[i];
    if (r.mode === 'mock' && r.status === 'started') {
      updateAttempt_(i + 2, { status: 'expired' });
      Logger.log('Expired: ' + r.attemptId + ' (' + r.testIndex + ' ' + r.userKey + ')');
      fixed++;
    }
  }
  Logger.log('Total expired: ' + fixed);
  return { expired: fixed };
}

/** デバッグ: R5AM resume処理を完全再現 */
function ADMIN_debugMockR5AM() {
  // dancing.keita のattemptでresume処理をシミュレート
  var userKey = 'dancing.keita@gmail.com';
  var year = 'R5';
  var part = 'AM';
  try {
    Logger.log('=== Step 1: findActiveMockAttempt_ ===');
    var existing = findActiveMockAttempt_(userKey, year, part);
    Logger.log('existing: ' + (existing ? JSON.stringify({attemptId: existing.row.attemptId, endsAt: existing.row.endsAt}) : 'null'));

    if (existing) {
      var endsAt = existing.row.endsAt ? new Date(existing.row.endsAt) : null;
      Logger.log('endsAt parsed: ' + (endsAt ? endsAt.toISOString() : 'null'));
      Logger.log('expired: ' + (endsAt ? (getNow_() > endsAt) : 'N/A'));

      Logger.log('=== Step 2: getMockExamQuestions_ ===');
      var qIds = getMockExamQuestions_(year, part);
      Logger.log('qIds count: ' + qIds.length);

      Logger.log('=== Step 3: getQuestionsByIds_ ===');
      var questions = getQuestionsByIds_(qIds);
      Logger.log('questions fetched: ' + questions.length);

      Logger.log('=== Step 4: toQuestionForClient_ ===');
      var clientQs = questions.map(toQuestionForClient_);
      Logger.log('client questions: ' + clientQs.length);

      Logger.log('=== Step 5: getExamSectionRules_ ===');
      var rules = getExamSectionRules_(year, part);
      Logger.log('rules: ' + JSON.stringify(rules));

      Logger.log('=== Step 6: Build response ===');
      var config = getConfigMap_();
      var tz = getConfigValue_(config, 'TIMEZONE', 'Asia/Tokyo');
      var resp = {
        attemptId: existing.row.attemptId,
        year: year,
        part: part,
        endsAt: existing.row.endsAt,
        serverNow: formatDateTime_(getNow_(), tz),
        questions: clientQs,
        sectionRules: rules
      };
      Logger.log('Response attemptId: ' + resp.attemptId);
      Logger.log('Response questions: ' + resp.questions.length);
      Logger.log('=== SUCCESS ===');
      return resp;
    } else {
      Logger.log('No active attempt found for ' + userKey);
    }
  } catch(e) {
    Logger.log('=== ERROR at step ===');
    Logger.log('Message: ' + e.message);
    Logger.log('Stack: ' + (e.stack || 'N/A'));
    return { error: e.message };
  }
  return null;
}

function ADMIN_debugMockR5AM_OLD() {
  try {
    var attempts = readRecords_(getSheet_(SHEETS.Attempts));
    var active = [];
    for (var i = attempts.length - 1; i >= 0; i--) {
      var r = attempts[i];
      if (r.mode === 'mock' && r.status === 'started') {
        active.push({
          row: i+2,
          attemptId: r.attemptId,
          userKey: r.userKey,
          testIndex: r.testIndex,
          endsAt: r.endsAt,
          startedAt: r.startedAt,
          status: r.status
        });
      }
    }
    Logger.log('ALL active mock attempts: ' + active.length);
    for (var j = 0; j < active.length; j++) {
      Logger.log('  ' + JSON.stringify(active[j]));
    }

    // endsAtのパースチェック
    if (active.length > 0) {
      var a = active[0];
      var parsed = a.endsAt ? new Date(a.endsAt) : null;
      var now = getNow_();
      Logger.log('endsAt raw: ' + a.endsAt);
      Logger.log('endsAt parsed: ' + (parsed ? parsed.toISOString() : 'null'));
      Logger.log('now: ' + now.toISOString());
      Logger.log('expired: ' + (parsed ? (now > parsed) : 'N/A'));
    }

    return { count: active.length, attempts: active };
  } catch(e) {
    Logger.log('ERROR: ' + e.message + '\n' + e.stack);
    return { error: e.message, stack: e.stack };
  }
}
