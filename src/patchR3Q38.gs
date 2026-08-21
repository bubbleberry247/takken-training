// patchR3Q38.gs
//
// R3（令和3年）問38の設問本文だけを、安全に局所更新するための
// GASエディタ専用メンテナンス関数。
//
// 重要:
// - doGet/doPostから呼び出さない。公開RPC/UIには追加しない。
// - 引数なしのeditor wrapperは必ずdry-run。
// - 本番適用はmaintenance windowを開けたうえで、引数なしwrapperから行う。
// - QuestionBankの書込みはAdvanced Sheets APIのstem列限定batchUpdateだけ。
// - 全量CSV import / QuestionBank全消去は行わない。

var TAKKEN_R3Q38_PATCH_BACKUP_SHEET_ = '_QuestionBankPatchBackup';
var TAKKEN_R3Q38_MAINTENANCE_WINDOW_PROPERTY_ = 'TAKKEN_R3Q38_MAINTENANCE_WINDOW';
// Global initializerのファイル順に依存しないよう、ヘッダーは固定定義する。
var TAKKEN_R3Q38_PATCH_BACKUP_HEADERS_ = [
  'patchId', 'createdAt', 'patchStatus', 'dbSpreadsheetId', 'targetQId', 'sourceRowNumber',
  'beforeRowSha256', 'afterRowSha256', 'beforeInventorySha256', 'beforeNonTargetInventorySha256',
  'afterInventorySha256', 'afterNonTargetInventorySha256',
  'qId', 'segmentId', 'type', 'difficulty',
  'tag1', 'tag2', 'tag3', 'lawTag',
  'revisionFlag', 'conceptId', 'variantGroupId', 'source_ref',
  'imageUrl', 'choiceImageUrl',
  'stem', 'choiceA', 'choiceB', 'choiceC', 'choiceD', 'choiceE',
  'explainA', 'explainB', 'explainC', 'explainD', 'explainE',
  'correct', 'explainShort', 'explainLong', 'status', 'updatedAt'
];

// stemはcanonical CSVの改行（LF）に正規化したものを保持する。
// expectedBeforeStemSha256は、本番シートが今回想定した未修正値であることの停止条件。
var TAKKEN_R3Q38_PATCH_SPECS_ = [
  {
    qId: 'R3atakken-038',
    expectedBeforeStemSha256: '0aa41f73614616282cf45ba4711904e3797bed44c85edf61cdd2411c92c21297',
    replacementStemSha256: '09e45de1f487dc734b364c9f2b81bac3288781df1455c1ef0d0d4e9f25413399',
    expectedBeforeLabelCounts: { 'ア\u3000': 0, 'イ\u3000': 0, 'ウ\u3000': 0, 'エ\u3000': 0 },
    expectedAfterLabelCounts: { 'ア\u3000': 1, 'イ\u3000': 1, 'ウ\u3000': 1, 'エ\u3000': 1 },
    replacementStem: '宅地建物取引業者Aが、宅地建物取引業者BからB所有の建物の売却を依頼され、Bと一般媒介契約（以下この問において「本件契約」という。）を締結した場合に関する次の記述のうち、宅地建物取引業法の規定に違反しないものはいくつあるか。\n\nア\u3000本件契約を締結する際に、Bから有効期間を6か月としたい旨の申出があったが、AとBが協議して、有効期間を3か月とした。\nイ\u3000当該物件に係る買受けの申込みはなかったが、AはBに対し本件契約に係る業務の処理状況の報告を口頭により14日に1回以上の頻度で行った。\nウ\u3000Aは本件契約を締結した後、所定の事項を遅滞なく指定流通機構に登録したが、その登録を証する書面を、登録してから14日後にBに交付した。\nエ\u3000本件契約締結後、1年を経過しても当該物件を売却できなかったため、Bは売却をあきらめ、当該物件を賃貸することにした。そこでBはAと当該物件の貸借に係る一般媒介契約を締結したが、当該契約の有効期間を定めなかった。'
  },
  {
    qId: 'R3btakken-038',
    expectedBeforeStemSha256: '625bd552f0f77387e65de8e08c49e7a2767c08e864f5135a3fb9037e935e5253',
    replacementStemSha256: 'c208d30ca29b7fb1ab2305b7f17f9f1eae379e0b920b320c77ec79c36692a2fa',
    expectedBeforeLabelCounts: { 'ア\u3000': 0, 'イ\u3000': 0, 'ウ\u3000': 0, 'エ\u3000': 0 },
    expectedAfterLabelCounts: { 'ア\u3000': 1, 'イ\u3000': 1, 'ウ\u3000': 1, 'エ\u3000': 1 },
    replacementStem: '次の記述のうち、宅地建物取引業法の規定に違反しないものの組合せとして、正しいものはどれか。なお、この問において「建築確認」とは、建築基準法第6条第1項の確認をいうものとする。\n\nア\u3000宅地建物取引業者Aは、建築確認の済んでいない建築工事完了前の賃貸住宅の貸主Bから当該住宅の貸借の媒介を依頼され、取引態様を媒介と明示して募集広告を行った。\nイ\u3000宅地建物取引業者Cは、建築確認の済んでいない建築工事完了前の賃貸住宅の貸主Dから当該住宅の貸借の代理を依頼され、代理人として借主Eとの間で当該住宅の賃貸借契約を締結した。\nウ\u3000宅地建物取引業者Fは、自己の所有に属しない宅地について、自ら売主として、宅地建物取引業者Gと売買契約の予約を締結した。\nエ\u3000宅地建物取引業者Hは、農地の所有者Iと建物の敷地に供するため農地法第5条の許可を条件とする売買契約を締結したので、自ら売主として宅地建物取引業者ではない個人JとI所有の農地の売買契約を締結した。'
  }
];

// Core is intentionally private (trailing underscore). The no-argument editor
// wrappers below are the only documented way to run it from Apps Script.
function ADMIN_patchTakkenR3Q38Stems_(options) {
  options = options || {};
  var apply = options.apply === true;
  if (options.dryRun === false && !apply) {
    throw new Error('dry-run is the default; use {apply:true} for an explicit write');
  }
  if (apply) takkenR3Q38RequireMaintenanceWindow_();

  var lock = LockService.getScriptLock();
  lock.waitLock(30000);
  try {
    var plan = takkenR3Q38BuildPlan_();
    takkenR3Q38AssertDbId_(plan, 'plan');
    if (!apply) {
      plan.mode = 'dry-run';
      plan.wouldUpdate = plan.matched;
      return takkenR3Q38PlanReceipt_(plan);
    }
    if (plan.matched !== 2) throw new Error('matched must equal 2 before apply: ' + plan.matched);

    var patchId = 'takken-r3q38-' + Utilities.getUuid();
    var backupSheet = takkenR3Q38EnsureBackupSheet_();
    var backupRows = plan.targets.map(function(target) {
      return [
        patchId, new Date(), 'prepared', plan.dbSpreadsheetId, target.qId, target.sheetRow,
        target.beforeRowSha256, target.afterRowSha256,
        plan.inventorySha256, plan.nonTargetInventorySha256, '', ''
      ].concat(target.beforeRow);
    });

    // Backup is durable and complete before any QuestionBank mutation.
    backupSheet.getRange(backupSheet.getLastRow() + 1, 1, backupRows.length, backupRows[0].length).setValues(backupRows);
    SpreadsheetApp.flush();
    takkenR3Q38AssertBackupComplete_(backupSheet, patchId, plan);
    takkenR3Q38AssertDbId_(plan, 'after-backup');

    try {
      // Re-read after backup. Row order may change, but qId/content must not.
      var prewritePlan = takkenR3Q38BuildPlan_();
      takkenR3Q38AssertDbId_(prewritePlan, 'prewrite');
      takkenR3Q38AssertPlanSnapshot_(plan, prewritePlan);
      if (prewritePlan.matched !== 2) throw new Error('prewrite matched must equal 2');
      takkenR3Q38AssertDbId_(plan, 'api');
      takkenR3Q38AssertDbId_(prewritePlan, 'api');

      // One atomic Sheets API batchUpdate: exact old stem -> exact new stem,
      // restricted to the stem column. No row number is sent to the API.
      takkenR3Q38BatchFindReplace_(prewritePlan, prewritePlan.targets.map(function(target) {
        return { find: target.beforeStem, replacement: target.afterStem };
      }));

      takkenR3Q38ClearQuestionCache_();
      takkenR3Q38AssertDbId_(prewritePlan, 'post-read');
      var post = takkenR3Q38ReadAndValidatePost_(prewritePlan, backupSheet, patchId);
      if (post.matched !== 2 || post.updated !== 2) {
        throw new Error('post-reread contract failed: matched=' + post.matched + ', updated=' + post.updated);
      }
      if (prewritePlan.afterInventorySha256 !== prewritePlan.expectedAfterInventorySha256 ||
          prewritePlan.afterNonTargetInventorySha256 !== prewritePlan.expectedAfterNonTargetInventorySha256) {
        throw new Error('post inventory hash does not match expected patched inventory');
      }
      takkenR3Q38SetBackupStatus_(backupSheet, patchId, 'applied');
      return {
        ok: true,
        mode: 'applied',
        patchId: patchId,
        matched: prewritePlan.matched,
        updated: post.updated,
        backupSheet: TAKKEN_R3Q38_PATCH_BACKUP_SHEET_,
        targets: post.targets
      };
    } catch (writeError) {
      throw takkenR3Q38HandleApplyFailure_(plan, backupSheet, patchId, writeError);
    }
  } finally {
    lock.releaseLock();
  }
}

// GASエディタのRunボタンから直接実行できる引数なし入口。
function ADMIN_patchTakkenR3Q38DryRun_() {
  return takkenR3Q38EditorRun_('R3Q38 dry-run', function() {
    return ADMIN_patchTakkenR3Q38Stems_({ dryRun: true });
  });
}

function ADMIN_applyTakkenR3Q38_() {
  return takkenR3Q38EditorRun_('R3Q38 apply', function() {
    return ADMIN_patchTakkenR3Q38Stems_({ apply: true });
  });
}

// 明示的なrollback用。既定は検証のみで、{apply:true, patchId:'...'}で復元する。
function ADMIN_rollbackTakkenR3Q38Stems_(options) {
  options = options || {};
  var patchId = String(options.patchId || '').trim();
  if (!patchId) throw new Error('patchId is required');
  var apply = options.apply === true;
  if (options.dryRun === false && !apply) {
    throw new Error('rollback dry-run is the default; use {apply:true, patchId:"..."}');
  }
  if (apply) takkenR3Q38RequireMaintenanceWindow_();

  var lock = LockService.getScriptLock();
  lock.waitLock(30000);
  try {
    var backupSheet = takkenR3Q38EnsureBackupSheet_(false);
    var backup = takkenR3Q38ReadBackup_(backupSheet, patchId);
    if (backup.length !== 2) throw new Error('rollback requires exactly 2 backup rows: ' + backup.length);
    var plan = takkenR3Q38BuildPlanFromBackup_(backup);
    takkenR3Q38AssertDbId_(plan, 'rollback-plan');
    var current = takkenR3Q38ReadInventory_(plan.dbSpreadsheetId);
    takkenR3Q38AssertDbId_(plan, 'rollback-prewrite');
    takkenR3Q38ValidateState_(current, plan, 'after');
    if (!apply) {
      return { ok: true, mode: 'dry-run', patchId: patchId, matched: 2, wouldRestore: 2, targets: plan.targets.map(takkenR3Q38TargetReceipt_) };
    }

    try {
      takkenR3Q38AssertDbId_(plan, 'rollback-api');
      takkenR3Q38BatchFindReplace_(plan, plan.targets.map(function(target) {
        return { find: target.afterStem, replacement: target.beforeStem };
      }));
      takkenR3Q38ClearQuestionCache_();
      takkenR3Q38AssertDbId_(plan, 'rollback-post-read');
      var post = takkenR3Q38ReadInventory_(plan.dbSpreadsheetId);
      takkenR3Q38AssertDbId_(plan, 'rollback-post-read-after');
      takkenR3Q38ValidateState_(post, plan, 'before');
      takkenR3Q38SetBackupStatus_(backupSheet, patchId, 'rolled_back');
      return { ok: true, mode: 'rolled-back', patchId: patchId, matched: 2, restored: 2 };
    } catch (rollbackError) {
      try { takkenR3Q38SetBackupStatus_(backupSheet, patchId, 'rollback_failed'); } catch (statusError) {}
      throw new Error('rollback failed; manual review required: ' + rollbackError.message);
    }
  } finally {
    lock.releaseLock();
  }
}

function ADMIN_rollbackLatestTakkenR3Q38DryRun_() {
  return takkenR3Q38EditorRun_('R3Q38 rollback dry-run', function() {
    return ADMIN_rollbackTakkenR3Q38Stems_({ patchId: takkenR3Q38LatestPatchId_(), dryRun: true });
  });
}

function ADMIN_rollbackLatestTakkenR3Q38_() {
  return takkenR3Q38EditorRun_('R3Q38 rollback apply', function() {
    return ADMIN_rollbackTakkenR3Q38Stems_({ patchId: takkenR3Q38LatestPatchId_(), apply: true });
  });
}

// Read the complete QuestionBank as an identity-keyed inventory.  sheetRow is
// retained only as evidence; no QuestionBank write in this patch is allowed
// to depend on it because a row can move between the pre-write read and the
// Sheets API request.
function takkenR3Q38ReadInventory_() {
  var expectedDbId = arguments.length ? String(arguments[0] || '').trim() : '';
  var configuredDbId = String(getDbId_() || '').trim();
  if (!configuredDbId) throw new Error('DB_SPREADSHEET_ID is missing; no mutation allowed');
  var spreadsheet = getDb_();
  var loadedDbId = String(spreadsheet.getId() || '').trim();
  if (!loadedDbId || loadedDbId !== configuredDbId) {
    throw new Error('loaded Spreadsheet.getId() does not match DB_SPREADSHEET_ID');
  }
  if (expectedDbId && loadedDbId !== expectedDbId) {
    throw new Error('loaded Spreadsheet object does not match expected plan DB');
  }
  var sheet = spreadsheet.getSheetByName(SHEETS.QuestionBank);
  if (!sheet) throw new Error('QuestionBank sheet not found');
  var values = sheet.getDataRange().getValues();
  if (values.length <= 1) throw new Error('QuestionBank has no data rows');
  var headers = values[0].map(function(h, i) { return normalizeHeader_(h, i); });
  var expectedHeaders = HEADERS[SHEETS.QuestionBank];
  if (headers.join('\t') !== expectedHeaders.join('\t')) {
    throw new Error('QuestionBank header mismatch; no mutation allowed');
  }
  var headerIndex = {};
  headers.forEach(function(h, i) { headerIndex[h] = i; });
  var byId = {};
  var rowFingerprints = {};
  for (var r = 1; r < values.length; r++) {
    if (values[r].length !== headers.length) {
      throw new Error('QuestionBank row width mismatch at sheet row ' + (r + 1));
    }
    var qId = String(values[r][headerIndex.qId] || '').trim();
    if (!qId) throw new Error('blank qId at sheet row ' + (r + 1));
    if (Object.prototype.hasOwnProperty.call(byId, qId)) {
      throw new Error('duplicate qId: ' + qId);
    }
    var row = values[r].slice();
    byId[qId] = { row: row, sheetRow: r + 1 };
    rowFingerprints[qId] = {
      sheetRow: r + 1,
      rowSha256: takkenR3Q38RowSha256_(row)
    };
  }
  return {
    spreadsheet: spreadsheet,
    spreadsheetId: loadedDbId,
    sheet: sheet,
    sheetId: sheet.getSheetId(),
    values: values,
    headers: headers,
    headerIndex: headerIndex,
    byId: byId,
    rowFingerprints: rowFingerprints,
    qIds: Object.keys(byId).sort(),
    stemColumnIndex: headerIndex.stem,
    inventorySha256: takkenR3Q38InventorySha256_(rowFingerprints),
    nonTargetInventorySha256: takkenR3Q38InventorySha256_(rowFingerprints, takkenR3Q38FixedTargetIdMap_())
  };
}

function takkenR3Q38FixedTargetIdMap_() {
  var map = {};
  TAKKEN_R3Q38_PATCH_SPECS_.forEach(function(spec) { map[spec.qId] = true; });
  return map;
}

function takkenR3Q38InventorySha256_(rowFingerprints, excludedQIds) {
  excludedQIds = excludedQIds || {};
  var entries = Object.keys(rowFingerprints).filter(function(qId) {
    return !excludedQIds[qId];
  }).sort().map(function(qId) {
    return qId + '\u001f' + rowFingerprints[qId].rowSha256;
  });
  return takkenR3Q38Sha256_(entries.join('\u001e'));
}

function takkenR3Q38AssertDbId_(plan, phase) {
  takkenR3Q38AssertSpreadsheet_(plan, phase);
}

function takkenR3Q38AssertSpreadsheet_(plan, phase) {
  var current = String(getDbId_() || '').trim();
  if (!plan || !plan.dbSpreadsheetId || current !== plan.dbSpreadsheetId) {
    throw new Error('DB_SPREADSHEET_ID changed or is missing at ' + phase);
  }
  var spreadsheet = getDb_();
  var loaded = String(spreadsheet.getId() || '').trim();
  if (loaded !== plan.dbSpreadsheetId) {
    throw new Error('loaded Spreadsheet.getId() changed at ' + phase);
  }
  if (plan.spreadsheet && spreadsheet !== plan.spreadsheet) {
    throw new Error('loaded Spreadsheet object changed at ' + phase);
  }
  return spreadsheet;
}

function takkenR3Q38CountStemOccurrences_(inventory, needle) {
  var exact = 0;
  var substring = 0;
  Object.keys(inventory.byId).forEach(function(qId) {
    var stem = takkenR3Q38CanonicalText_(inventory.byId[qId].row[inventory.stemColumnIndex]);
    if (stem === needle) exact++;
    var from = 0;
    while (true) {
      var at = stem.indexOf(needle, from);
      if (at < 0) break;
      substring++;
      from = at + Math.max(1, needle.length);
    }
  });
  return { exact: exact, substring: substring };
}

function takkenR3Q38BuildPlan_() {
  var dbSpreadsheetId = String(getDbId_() || '').trim();
  if (!dbSpreadsheetId) throw new Error('DB_SPREADSHEET_ID is missing; no mutation allowed');
  var inventory = takkenR3Q38ReadInventory_(dbSpreadsheetId);
  if (inventory.spreadsheetId !== dbSpreadsheetId) {
    throw new Error('plan Spreadsheet object ID mismatch');
  }
  var specs = TAKKEN_R3Q38_PATCH_SPECS_;
  if (specs.length !== 2) throw new Error('fixed patch spec must contain exactly 2 targets');
  var seenBefore = {};
  var seenAfter = {};
  var targets = specs.map(function(spec) {
    if (!Object.prototype.hasOwnProperty.call(inventory.byId, spec.qId)) {
      throw new Error('target qId not found: ' + spec.qId);
    }
    var rowInfo = inventory.byId[spec.qId];
    var beforeStem = takkenR3Q38CanonicalText_(rowInfo.row[inventory.stemColumnIndex]);
    var afterStem = takkenR3Q38CanonicalText_(spec.replacementStem);
    takkenR3Q38ValidateSpec_(spec, beforeStem, afterStem);
    if (Object.prototype.hasOwnProperty.call(seenBefore, beforeStem)) {
      throw new Error('duplicate old stem in fixed targets: ' + spec.qId);
    }
    if (Object.prototype.hasOwnProperty.call(seenAfter, afterStem)) {
      throw new Error('duplicate replacement stem in fixed targets: ' + spec.qId);
    }
    seenBefore[beforeStem] = spec.qId;
    seenAfter[afterStem] = spec.qId;
    var oldOccurrences = takkenR3Q38CountStemOccurrences_(inventory, beforeStem);
    var newOccurrences = takkenR3Q38CountStemOccurrences_(inventory, afterStem);
    if (oldOccurrences.exact !== 1 || oldOccurrences.substring !== 1) {
      throw new Error('old stem must occur exactly once in stem column: ' + spec.qId +
        ' exact=' + oldOccurrences.exact + ' substring=' + oldOccurrences.substring);
    }
    if (newOccurrences.exact !== 0 || newOccurrences.substring !== 0) {
      throw new Error('replacement stem already exists or is embedded in QuestionBank: ' + spec.qId +
        ' exact=' + newOccurrences.exact + ' substring=' + newOccurrences.substring);
    }
    var beforeRow = rowInfo.row.slice();
    var afterRow = rowInfo.row.slice();
    afterRow[inventory.stemColumnIndex] = afterStem;
    return {
      qId: spec.qId,
      sheetRow: rowInfo.sheetRow,
      beforeStem: beforeStem,
      afterStem: afterStem,
      beforeRow: beforeRow,
      afterRow: afterRow,
      beforeRowSha256: takkenR3Q38RowSha256_(beforeRow),
      afterRowSha256: takkenR3Q38RowSha256_(afterRow),
      beforeLabelCounts: takkenR3Q38LabelCounts_(beforeStem),
      afterLabelCounts: takkenR3Q38LabelCounts_(afterStem)
    };
  });
  if (targets.length !== 2) throw new Error('matched must equal 2: ' + targets.length);
  var expectedAfterFingerprints = {};
  Object.keys(inventory.rowFingerprints).forEach(function(qId) {
    expectedAfterFingerprints[qId] = { rowSha256: inventory.rowFingerprints[qId].rowSha256 };
  });
  targets.forEach(function(target) {
    expectedAfterFingerprints[target.qId].rowSha256 = target.afterRowSha256;
  });
  return {
    ok: true,
    mode: 'plan',
    matched: targets.length,
    updated: 0,
    dbSpreadsheetId: dbSpreadsheetId,
    spreadsheet: inventory.spreadsheet,
    sheetId: inventory.sheetId,
    stemColumnIndex: inventory.stemColumnIndex,
    inventorySha256: inventory.inventorySha256,
    nonTargetInventorySha256: inventory.nonTargetInventorySha256,
    expectedAfterInventorySha256: takkenR3Q38InventorySha256_(expectedAfterFingerprints),
    expectedAfterNonTargetInventorySha256: takkenR3Q38InventorySha256_(expectedAfterFingerprints, takkenR3Q38FixedTargetIdMap_()),
    headerIndex: inventory.headerIndex,
    qIds: inventory.qIds,
    targets: targets,
    rowFingerprints: inventory.rowFingerprints
  };
}

function takkenR3Q38ValidateSpec_(spec, beforeStem, afterStem) {
  if (takkenR3Q38Sha256_(beforeStem) !== spec.expectedBeforeStemSha256) {
    throw new Error('expected-before stem hash mismatch: ' + spec.qId);
  }
  if (takkenR3Q38Sha256_(afterStem) !== spec.replacementStemSha256) {
    throw new Error('replacement stem hash mismatch in patch source: ' + spec.qId);
  }
  var beforeCounts = takkenR3Q38LabelCounts_(beforeStem);
  var afterCounts = takkenR3Q38LabelCounts_(afterStem);
  Object.keys(spec.expectedBeforeLabelCounts).forEach(function(marker) {
    if (beforeCounts[marker] !== spec.expectedBeforeLabelCounts[marker]) {
      throw new Error('unexpected old label occurrence count: ' + spec.qId + ' ' + marker);
    }
  });
  Object.keys(spec.expectedAfterLabelCounts).forEach(function(marker) {
    if (afterCounts[marker] !== spec.expectedAfterLabelCounts[marker]) {
      throw new Error('unexpected new label occurrence count: ' + spec.qId + ' ' + marker);
    }
  });
}

function takkenR3Q38AssertPlanSnapshot_(before, after) {
  if (before.dbSpreadsheetId !== after.dbSpreadsheetId) throw new Error('DB_SPREADSHEET_ID changed between reads');
  takkenR3Q38AssertDbId_(before, 'plan-snapshot');
  if (before.spreadsheet !== after.spreadsheet || before.spreadsheetId !== after.spreadsheetId) {
    throw new Error('Spreadsheet object or ID changed between reads');
  }
  if (before.sheetId !== after.sheetId) throw new Error('QuestionBank sheet identity changed');
  var beforeIds = (before.qIds || Object.keys(before.rowFingerprints)).slice().sort();
  var afterIds = (after.qIds || Object.keys(after.rowFingerprints)).slice().sort();
  if (beforeIds.join('\t') !== afterIds.join('\t')) {
    throw new Error('QuestionBank qId inventory changed between backup and write');
  }
  beforeIds.forEach(function(qId) {
    if (!after.rowFingerprints[qId] ||
        after.rowFingerprints[qId].rowSha256 !== before.rowFingerprints[qId].rowSha256) {
      throw new Error('QuestionBank content changed between backup and write: ' + qId);
    }
  });
  if (before.stemColumnIndex !== after.stemColumnIndex) throw new Error('stem column changed');
  before.targets.forEach(function(target) {
    var current = after.targets.find(function(candidate) { return candidate.qId === target.qId; });
    if (!current || current.beforeRowSha256 !== target.beforeRowSha256 ||
        current.beforeStem !== target.beforeStem) {
      throw new Error('target changed between backup and write: ' + target.qId);
    }
  });
}

function takkenR3Q38ValidateState_(inventory, plan, state) {
  if (state !== 'before' && state !== 'after') throw new Error('invalid patch state: ' + state);
  var expectedIds = Object.keys(plan.rowFingerprints || {}).sort();
  var actualIds = inventory.qIds.slice().sort();
  if (expectedIds.join('\t') !== actualIds.join('\t')) throw new Error('QuestionBank qId inventory changed');
  var expectedInventorySha256 = state === 'after'
    ? (plan.expectedAfterInventorySha256 || plan.afterInventorySha256)
    : plan.inventorySha256;
  var expectedNonTargetInventorySha256 = state === 'after'
    ? (plan.expectedAfterNonTargetInventorySha256 || plan.afterNonTargetInventorySha256)
    : plan.nonTargetInventorySha256;
  if (expectedInventorySha256 && inventory.inventorySha256 !== expectedInventorySha256) {
    throw new Error(state + ' full inventory hash mismatch');
  }
  if (expectedNonTargetInventorySha256 && inventory.nonTargetInventorySha256 !== expectedNonTargetInventorySha256) {
    throw new Error(state + ' non-target inventory hash mismatch');
  }
  var targetIds = {};
  var updated = 0;
  var receipts = plan.targets.map(function(target) {
    targetIds[target.qId] = true;
    var current = inventory.byId[target.qId];
    if (!current) throw new Error('target qId missing: ' + target.qId);
    var expectedStem = state === 'after' ? target.afterStem : target.beforeStem;
    var forbiddenStem = state === 'after' ? target.beforeStem : target.afterStem;
    var currentStem = takkenR3Q38CanonicalText_(current.row[inventory.stemColumnIndex]);
    var expectedCount = takkenR3Q38CountStemOccurrences_(inventory, expectedStem);
    var forbiddenCount = takkenR3Q38CountStemOccurrences_(inventory, forbiddenStem);
    if (expectedCount.exact !== 1 || expectedCount.substring !== 1) {
      throw new Error(state + ' expected stem occurrence must be exactly 1: ' + target.qId +
        ' exact=' + expectedCount.exact + ' substring=' + expectedCount.substring);
    }
    if (forbiddenCount.exact !== 0 || forbiddenCount.substring !== 0) {
      throw new Error(state + ' forbidden stem still present: ' + target.qId +
        ' exact=' + forbiddenCount.exact + ' substring=' + forbiddenCount.substring);
    }
    if (takkenR3Q38Sha256_(currentStem) !== takkenR3Q38Sha256_(expectedStem)) {
      throw new Error(state + ' stem hash mismatch: ' + target.qId);
    }
    var expectedRowHash = state === 'after' ? target.afterRowSha256 : target.beforeRowSha256;
    if (takkenR3Q38RowSha256_(current.row) !== expectedRowHash) {
      throw new Error(state + ' target row hash mismatch: ' + target.qId);
    }
    if (state === 'after') {
      takkenR3Q38AssertOnlyStemChanged_(target.beforeRow, current.row, inventory.stemColumnIndex, target.qId);
      updated++;
    }
    return {
      qId: target.qId,
      sheetRow: current.sheetRow,
      stemSha256: takkenR3Q38Sha256_(currentStem),
      labelCounts: takkenR3Q38LabelCounts_(currentStem)
    };
  });
  Object.keys(inventory.byId).forEach(function(qId) {
    if (!targetIds[qId] &&
        (!plan.rowFingerprints[qId] ||
         takkenR3Q38RowSha256_(inventory.byId[qId].row) !== plan.rowFingerprints[qId].rowSha256)) {
      throw new Error('non-target row changed: ' + qId);
    }
  });
  return { matched: receipts.length, updated: updated, targets: receipts };
}

function takkenR3Q38ReadAndValidatePost_(plan, backupSheet, patchId) {
  takkenR3Q38AssertDbId_(plan, 'post-read-before');
  var inventory = takkenR3Q38ReadInventory_(plan.dbSpreadsheetId);
  takkenR3Q38AssertDbId_(plan, 'post-read-after');
  plan.afterInventorySha256 = inventory.inventorySha256;
  plan.afterNonTargetInventorySha256 = inventory.nonTargetInventorySha256;
  if (backupSheet && patchId) takkenR3Q38SetBackupInventoryHashes_(backupSheet, patchId, inventory);
  return takkenR3Q38ValidateState_(inventory, plan, 'after');
}

function takkenR3Q38AssertOnlyStemChanged_(beforeRow, currentRow, stemIndex, qId) {
  if (beforeRow.length !== currentRow.length) throw new Error('row width changed: ' + qId);
  for (var i = 0; i < beforeRow.length; i++) {
    if (i === stemIndex) continue;
    if (takkenR3Q38CellKey_(beforeRow[i]) !== takkenR3Q38CellKey_(currentRow[i])) {
      throw new Error('non-stem cell changed: ' + qId + ' column ' + i);
    }
  }
}

function takkenR3Q38EnsureBackupSheet_(allowCreate) {
  allowCreate = allowCreate !== false;
  var ss = getDb_();
  var sheet = ss.getSheetByName(TAKKEN_R3Q38_PATCH_BACKUP_SHEET_);
  if (!sheet) {
    if (!allowCreate) throw new Error('backup sheet not found: ' + TAKKEN_R3Q38_PATCH_BACKUP_SHEET_);
    sheet = ss.insertSheet(TAKKEN_R3Q38_PATCH_BACKUP_SHEET_);
    sheet.getRange(1, 1, 1, TAKKEN_R3Q38_PATCH_BACKUP_HEADERS_.length).setValues([TAKKEN_R3Q38_PATCH_BACKUP_HEADERS_]);
    sheet.setFrozenRows(1);
    return sheet;
  }
  var lastCol = Math.max(1, sheet.getLastColumn());
  var headers = sheet.getRange(1, 1, 1, lastCol).getValues()[0].map(function(h, i) { return normalizeHeader_(h, i); });
  if (headers.join('\t') !== TAKKEN_R3Q38_PATCH_BACKUP_HEADERS_.join('\t')) {
    throw new Error('backup sheet header mismatch');
  }
  return sheet;
}

function takkenR3Q38SetBackupStatus_(sheet, patchId, status) {
  var data = sheet.getDataRange().getValues();
  var patchCol = TAKKEN_R3Q38_PATCH_BACKUP_HEADERS_.indexOf('patchId');
  var statusCol = TAKKEN_R3Q38_PATCH_BACKUP_HEADERS_.indexOf('patchStatus');
  for (var r = 1; r < data.length; r++) {
    if (String(data[r][patchCol]) === patchId) sheet.getRange(r + 1, statusCol + 1).setValue(status);
  }
}

function takkenR3Q38SetBackupInventoryHashes_(sheet, patchId, inventory) {
  var data = sheet.getDataRange().getValues();
  var patchCol = TAKKEN_R3Q38_PATCH_BACKUP_HEADERS_.indexOf('patchId');
  var fullCol = TAKKEN_R3Q38_PATCH_BACKUP_HEADERS_.indexOf('afterInventorySha256');
  var nonTargetCol = TAKKEN_R3Q38_PATCH_BACKUP_HEADERS_.indexOf('afterNonTargetInventorySha256');
  if (fullCol < 0 || nonTargetCol < 0) throw new Error('backup inventory hash columns are missing');
  for (var r = 1; r < data.length; r++) {
    if (String(data[r][patchCol]) !== patchId) continue;
    sheet.getRange(r + 1, fullCol + 1).setValue(inventory.inventorySha256);
    sheet.getRange(r + 1, nonTargetCol + 1).setValue(inventory.nonTargetInventorySha256);
  }
}

function takkenR3Q38ReadBackup_(sheet, patchId) {
  var data = sheet.getDataRange().getValues();
  var headers = data[0].map(function(h, i) { return normalizeHeader_(h, i); });
  var index = {};
  headers.forEach(function(h, i) { index[h] = i; });
  return data.slice(1).filter(function(row) { return String(row[index.patchId] || '') === patchId; }).map(function(row) {
    var beforeRow = HEADERS[SHEETS.QuestionBank].map(function(h) { return row[index[h]]; });
    return {
      qId: String(row[index.targetQId] || '').trim(),
      dbSpreadsheetId: String(row[index.dbSpreadsheetId] || '').trim(),
      sourceRowNumber: Number(row[index.sourceRowNumber]),
      beforeRow: beforeRow,
      beforeRowSha256: String(row[index.beforeRowSha256] || ''),
      afterRowSha256: String(row[index.afterRowSha256] || ''),
      beforeInventorySha256: String(row[index.beforeInventorySha256] || ''),
      beforeNonTargetInventorySha256: String(row[index.beforeNonTargetInventorySha256] || ''),
      afterInventorySha256: String(row[index.afterInventorySha256] || ''),
      afterNonTargetInventorySha256: String(row[index.afterNonTargetInventorySha256] || '')
    };
  });
}

function takkenR3Q38AssertBackupComplete_(sheet, patchId, plan) {
  var saved = takkenR3Q38ReadBackup_(sheet, patchId);
  if (saved.length !== 2) throw new Error('backup verification requires exactly 2 rows: ' + saved.length);
  var byId = {};
  saved.forEach(function(row) {
    if (byId[row.qId]) throw new Error('backup duplicate qId: ' + row.qId);
    byId[row.qId] = row;
  });
  plan.targets.forEach(function(target) {
    var savedTarget = byId[target.qId];
    if (!savedTarget || savedTarget.dbSpreadsheetId !== plan.dbSpreadsheetId ||
        savedTarget.beforeRowSha256 !== target.beforeRowSha256 ||
        savedTarget.afterRowSha256 !== target.afterRowSha256 ||
        savedTarget.beforeInventorySha256 !== plan.inventorySha256 ||
        savedTarget.beforeNonTargetInventorySha256 !== plan.nonTargetInventorySha256 ||
        savedTarget.afterInventorySha256 !== '' ||
        savedTarget.afterNonTargetInventorySha256 !== '' ||
        takkenR3Q38RowSha256_(savedTarget.beforeRow) !== target.beforeRowSha256) {
      throw new Error('backup row/hash verification failed: ' + target.qId);
    }
  });
}

function takkenR3Q38BuildPlanFromBackup_(backup) {
  if (!backup || backup.length !== 2) throw new Error('backup must contain exactly 2 targets');
  var headerIndex = {};
  HEADERS[SHEETS.QuestionBank].forEach(function(h, i) { headerIndex[h] = i; });
  var seen = {};
  var targets = backup.map(function(row) {
    var beforeRow = row.beforeRow.slice();
    if (Object.prototype.hasOwnProperty.call(seen, row.qId)) throw new Error('duplicate backup qId: ' + row.qId);
    seen[row.qId] = true;
    var spec = TAKKEN_R3Q38_PATCH_SPECS_.find(function(s) { return s.qId === row.qId; });
    if (!spec) throw new Error('backup qId is outside fixed allowlist: ' + row.qId);
    if (beforeRow.length !== HEADERS[SHEETS.QuestionBank].length) {
      throw new Error('backup row width mismatch: ' + row.qId);
    }
    if (takkenR3Q38RowSha256_(beforeRow) !== row.beforeRowSha256) {
      throw new Error('backup before-row hash mismatch: ' + row.qId);
    }
    var beforeStem = takkenR3Q38CanonicalText_(beforeRow[headerIndex.stem]);
    var afterStem = takkenR3Q38CanonicalText_(spec.replacementStem);
    takkenR3Q38ValidateSpec_(spec, beforeStem, afterStem);
    var afterRow = beforeRow.slice();
    afterRow[headerIndex.stem] = afterStem;
    var computedAfterHash = takkenR3Q38RowSha256_(afterRow);
    if (computedAfterHash !== row.afterRowSha256) {
      throw new Error('backup after-row hash mismatch: ' + row.qId);
    }
    return {
      qId: row.qId,
      beforeRow: beforeRow,
      afterRow: afterRow,
      beforeRowSha256: row.beforeRowSha256,
      afterRowSha256: computedAfterHash,
      beforeStem: beforeStem,
      afterStem: afterStem,
      beforeLabelCounts: takkenR3Q38LabelCounts_(beforeStem),
      afterLabelCounts: takkenR3Q38LabelCounts_(afterStem),
      sheetRow: Number(row.sourceRowNumber) || 0
    };
  });
  if (Object.keys(seen).length !== 2) throw new Error('backup target qId inventory must equal 2');
  var dbSpreadsheetId = String(backup[0].dbSpreadsheetId || '').trim();
  if (!dbSpreadsheetId) throw new Error('backup has no DB_SPREADSHEET_ID; rollback is blocked');
  backup.forEach(function(row) {
    if (row.dbSpreadsheetId !== dbSpreadsheetId) throw new Error('backup DB_SPREADSHEET_ID mismatch');
    if (row.beforeInventorySha256 !== backup[0].beforeInventorySha256 ||
        row.beforeNonTargetInventorySha256 !== backup[0].beforeNonTargetInventorySha256 ||
        row.afterInventorySha256 !== backup[0].afterInventorySha256 ||
        row.afterNonTargetInventorySha256 !== backup[0].afterNonTargetInventorySha256) {
      throw new Error('backup inventory hash mismatch between target rows');
    }
  });
  if (!backup[0].afterInventorySha256 || !backup[0].afterNonTargetInventorySha256) {
    throw new Error('backup has no post-apply inventory hash; rollback is blocked');
  }
  if (String(getDbId_() || '').trim() !== dbSpreadsheetId) {
    throw new Error('DB_SPREADSHEET_ID does not match backup; rollback is blocked');
  }
  var inventory = takkenR3Q38ReadInventory_(dbSpreadsheetId);
  if (inventory.inventorySha256 !== backup[0].afterInventorySha256 ||
      inventory.nonTargetInventorySha256 !== backup[0].afterNonTargetInventorySha256) {
    throw new Error('post-apply inventory drift detected before rollback');
  }
  return {
    ok: true,
    mode: 'rollback-plan',
    matched: targets.length,
    updated: 0,
    dbSpreadsheetId: dbSpreadsheetId,
    spreadsheet: inventory.spreadsheet,
    sheetId: inventory.sheetId,
    stemColumnIndex: inventory.stemColumnIndex,
    inventorySha256: backup[0].beforeInventorySha256,
    nonTargetInventorySha256: backup[0].beforeNonTargetInventorySha256,
    expectedAfterInventorySha256: backup[0].afterInventorySha256,
    expectedAfterNonTargetInventorySha256: backup[0].afterNonTargetInventorySha256,
    afterInventorySha256: backup[0].afterInventorySha256,
    afterNonTargetInventorySha256: backup[0].afterNonTargetInventorySha256,
    headerIndex: inventory.headerIndex,
    qIds: inventory.qIds,
    targets: targets,
    // For rollback, this is the observed post-patch baseline. It protects
    // every non-target row without relying on the old source row numbers.
    rowFingerprints: inventory.rowFingerprints
  };
}

// The only QuestionBank write primitive in this file.  It intentionally uses
// the Advanced Sheets service and an identity-free column range: no row index
// is sent, and both exact replacements are submitted in one batchUpdate.
// There is deliberately no setValue/setValues fallback when the service is
// unavailable; a missing dependency is a hard stop.
function takkenR3Q38BatchFindReplace_(plan, replacements) {
  takkenR3Q38AssertSpreadsheet_(plan, 'api-batchUpdate');
  if (typeof Sheets === 'undefined' || !Sheets.Spreadsheets ||
      typeof Sheets.Spreadsheets.batchUpdate !== 'function') {
    throw new Error('Advanced Sheets service unavailable; no fallback is permitted');
  }
  if (!plan || plan.matched !== 2 || !plan.sheetId && plan.sheetId !== 0) {
    throw new Error('invalid fixed patch plan for Sheets batchUpdate');
  }
  if (!replacements || replacements.length !== 2) {
    throw new Error('exactly 2 findReplace requests are required');
  }
  var seenFind = {};
  var seenReplacement = {};
  var requests = replacements.map(function(replacement) {
    var find = takkenR3Q38CanonicalText_(replacement.find);
    var replaceWith = takkenR3Q38CanonicalText_(replacement.replacement);
    if (!find || !replaceWith || find === replaceWith) {
      throw new Error('invalid exact stem replacement');
    }
    if (Object.prototype.hasOwnProperty.call(seenFind, find)) throw new Error('duplicate find stem');
    if (Object.prototype.hasOwnProperty.call(seenReplacement, replaceWith)) throw new Error('duplicate replacement stem');
    seenFind[find] = true;
    seenReplacement[replaceWith] = true;
    return {
      findReplace: {
        find: find,
        replacement: replaceWith,
        allSheets: false,
        matchCase: true,
        matchEntireCell: true,
        searchByRegex: false,
        includeFormulas: false,
        range: {
          sheetId: plan.sheetId,
          startColumnIndex: plan.stemColumnIndex,
          endColumnIndex: plan.stemColumnIndex + 1
        }
      }
    };
  });
  var response = Sheets.Spreadsheets.batchUpdate(
    { requests: requests, includeSpreadsheetInResponse: false },
    plan.dbSpreadsheetId
  );
  var replies = response && response.replies;
  if (!replies || replies.length !== 2) throw new Error('Sheets batchUpdate reply count mismatch');
  var occurrences = replies.map(function(reply, i) {
    var count = reply && reply.findReplace && Number(reply.findReplace.occurrencesChanged);
    if (count !== 1) throw new Error('occurrencesChanged must equal 1 for request ' + (i + 1) + ': ' + count);
    return count;
  });
  return { requests: 2, occurrencesChanged: occurrences };
}

function takkenR3Q38ClassifyState_(inventory, plan) {
  try {
    var before = true;
    var after = true;
    plan.targets.forEach(function(target) {
      var current = inventory.byId[target.qId];
      if (!current) { before = false; after = false; return; }
      var stem = takkenR3Q38CanonicalText_(current.row[inventory.stemColumnIndex]);
      if (stem !== target.beforeStem) before = false;
      if (stem !== target.afterStem) after = false;
    });
    if (before) return 'before';
    if (after) return 'after';
    var anyBefore = false;
    var anyAfter = false;
    plan.targets.forEach(function(target) {
      var current = inventory.byId[target.qId];
      if (!current) return;
      var stem = takkenR3Q38CanonicalText_(current.row[inventory.stemColumnIndex]);
      anyBefore = anyBefore || stem === target.beforeStem;
      anyAfter = anyAfter || stem === target.afterStem;
    });
    if (anyBefore && anyAfter) return 'partial';
    return 'unknown';
  } catch (e) {
    return 'unknown';
  }
}

function takkenR3Q38HandleApplyFailure_(plan, backupSheet, patchId, writeError) {
  var message = String(writeError && writeError.message || writeError || 'unknown write error');
  var current;
  try {
    current = takkenR3Q38ReadInventory_(plan.dbSpreadsheetId);
  } catch (readError) {
    try { takkenR3Q38SetBackupStatus_(backupSheet, patchId, 'manual_review'); } catch (statusError) {}
    return new Error('apply response/state is unknown; manual review required: ' + message +
      '; reread failed: ' + String(readError.message || readError));
  }
  var state = takkenR3Q38ClassifyState_(current, plan);
  if (state === 'before') {
    try { takkenR3Q38ValidateState_(current, plan, 'before'); } catch (beforeError) {
      try { takkenR3Q38SetBackupStatus_(backupSheet, patchId, 'manual_review'); } catch (statusError1) {}
      return new Error('apply failed and pre-write state could not be verified; manual review required: ' +
        message + '; ' + beforeError.message);
    }
    try { takkenR3Q38SetBackupStatus_(backupSheet, patchId, 'not_applied'); } catch (statusError2) {}
    return new Error('apply failed; no QuestionBank mutation verified: ' + message);
  }
  if (state === 'after') {
    try {
      // Only an exact, fully validated post-state can be rolled back.  This
      // rollback is also a two-request exact batch, never row restoration.
      takkenR3Q38ValidateState_(current, plan, 'after');
      takkenR3Q38BatchFindReplace_(plan, plan.targets.map(function(target) {
        return { find: target.afterStem, replacement: target.beforeStem };
      }));
      takkenR3Q38ClearQuestionCache_();
      var restored = takkenR3Q38ReadInventory_(plan.dbSpreadsheetId);
      takkenR3Q38ValidateState_(restored, plan, 'before');
      takkenR3Q38SetBackupStatus_(backupSheet, patchId, 'rolled_back');
      return new Error('apply failed; exact automatic rollback verified: ' + message);
    } catch (rollbackError) {
      try { takkenR3Q38SetBackupStatus_(backupSheet, patchId, 'rollback_failed'); } catch (statusError3) {}
      return new Error('apply failed; rollback failed; manual review required: ' + message +
        '; ' + String(rollbackError.message || rollbackError));
    }
  }
  try { takkenR3Q38SetBackupStatus_(backupSheet, patchId, state === 'partial' ? 'partial' : 'manual_review'); } catch (statusError4) {}
  return new Error('apply state is ' + state + '; no automatic rollback attempted; manual review required: ' + message);
}

function takkenR3Q38RequireMaintenanceWindow_() {
  var props = getScriptProps_();
  var value = props && props.getProperty(TAKKEN_R3Q38_MAINTENANCE_WINDOW_PROPERTY_);
  if (String(value || '').toUpperCase() !== 'OPEN') {
    throw new Error('maintenance window is not OPEN; set ' + TAKKEN_R3Q38_MAINTENANCE_WINDOW_PROPERTY_ + '=OPEN only during the approved window');
  }
}

function takkenR3Q38RedactedReceipt_(result) {
  if (!result || typeof result !== 'object') return result;
  var safe = {};
  ['ok', 'mode', 'patchId', 'matched', 'updated', 'wouldUpdate', 'restored', 'wouldRestore',
    'nonTargetCount', 'backupSheet'].forEach(function(key) {
    if (result[key] !== undefined) safe[key] = result[key];
  });
  if (result.targets) safe.targets = result.targets.map(function(target) {
    return {
      qId: target.qId,
      sheetRow: target.sheetRow,
      beforeStemSha256: target.beforeStemSha256,
      afterStemSha256: target.afterStemSha256,
      beforeRowSha256: target.beforeRowSha256,
      afterRowSha256: target.afterRowSha256,
      beforeLabelCounts: target.beforeLabelCounts,
      afterLabelCounts: target.afterLabelCounts
    };
  });
  return safe;
}

function takkenR3Q38EditorRun_(label, callback) {
  try {
    var result = callback();
    if (typeof Logger !== 'undefined' && Logger.log) Logger.log(label + ': ' + JSON.stringify(takkenR3Q38RedactedReceipt_(result)));
    return result;
  } catch (e) {
    if (typeof Logger !== 'undefined' && Logger.log) Logger.log(label + ' ERROR: ' + String(e.message || e));
    throw e;
  }
}

function takkenR3Q38LatestPatchId_() {
  var sheet = takkenR3Q38EnsureBackupSheet_(false);
  var data = sheet.getDataRange().getValues();
  if (data.length <= 1) throw new Error('no patch backup exists');
  var patchCol = TAKKEN_R3Q38_PATCH_BACKUP_HEADERS_.indexOf('patchId');
  var statusCol = TAKKEN_R3Q38_PATCH_BACKUP_HEADERS_.indexOf('patchStatus');
  var seen = {};
  for (var r = data.length - 1; r >= 1; r--) {
    var patchId = String(data[r][patchCol] || '');
    var status = String(data[r][statusCol] || '');
    if (patchId && status === 'applied' && !seen[patchId]) return patchId;
    seen[patchId] = true;
  }
  throw new Error('no applied patch backup is available for rollback');
}

function takkenR3Q38ClearQuestionCache_() {
  // Patch application requires a durable shared version bump. If CacheService
  // cannot persist it, the caller treats the mutation as failed and attempts
  // the exact rollback path rather than claiming immediate visibility.
  clearAllCache_({ strict: true });
}

function takkenR3Q38CanonicalText_(value) {
  return String(value == null ? '' : value).replace(/\r\n/g, '\n').replace(/\r/g, '\n');
}

function takkenR3Q38CellKey_(value) {
  if (Object.prototype.toString.call(value) === '[object Date]') return 'date:' + value.toISOString();
  return typeof value + ':' + String(value == null ? '' : value);
}

function takkenR3Q38RowSha256_(row) {
  return takkenR3Q38Sha256_(row.map(takkenR3Q38CellKey_).join('\u001f'));
}

function takkenR3Q38Sha256_(value) {
  var bytes = Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, String(value), Utilities.Charset.UTF_8);
  return bytes.map(function(b) {
    var n = b < 0 ? b + 256 : b;
    return (n < 16 ? '0' : '') + n.toString(16);
  }).join('');
}

function takkenR3Q38LabelCounts_(stem) {
  var labels = ['ア\u3000', 'イ\u3000', 'ウ\u3000', 'エ\u3000'];
  var result = {};
  labels.forEach(function(label) { result[label] = takkenR3Q38Count_(stem, label); });
  return result;
}

function takkenR3Q38Count_(text, needle) {
  var count = 0;
  var from = 0;
  while (true) {
    var at = text.indexOf(needle, from);
    if (at < 0) return count;
    count++;
    from = at + needle.length;
  }
}

function takkenR3Q38TargetReceipt_(target) {
  return {
    qId: target.qId,
    sheetRow: target.sheetRow,
    beforeStemSha256: takkenR3Q38Sha256_(target.beforeStem),
    afterStemSha256: takkenR3Q38Sha256_(target.afterStem),
    beforeLabelCounts: target.beforeLabelCounts || takkenR3Q38LabelCounts_(target.beforeStem),
    afterLabelCounts: target.afterLabelCounts || takkenR3Q38LabelCounts_(target.afterStem),
    beforeRowSha256: target.beforeRowSha256,
    afterRowSha256: target.afterRowSha256
  };
}

function takkenR3Q38PlanReceipt_(plan) {
  return {
    ok: plan.ok,
    mode: plan.mode,
    matched: plan.matched,
    updated: plan.updated,
    wouldUpdate: plan.wouldUpdate,
    nonTargetCount: Math.max(0, Object.keys(plan.rowFingerprints || {}).length - plan.matched),
    targets: plan.targets.map(takkenR3Q38TargetReceipt_)
  };
}
