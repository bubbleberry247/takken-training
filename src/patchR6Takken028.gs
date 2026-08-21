// R6takken-028 approved-source recovery patch.
//
// The companion generated spec is an independently approved, content-addressed,
// stem-only payload. These functions are private GAS-editor maintenance entry
// points; do not expose them through doGet, doPost, or google.script.run.

var TAKKEN_R6_028_TARGET_QID_ = 'R6takken-028';
var TAKKEN_R6_028_TOTAL_COUNT_ = 600;
var TAKKEN_R6_028_NON_TARGET_COUNT_ = 599;
var TAKKEN_R6_028_BACKUP_SHEET_ = '_QuestionBankR6028PatchBackup';
var TAKKEN_R6_028_MAINTENANCE_PROPERTY_ = 'TAKKEN_R6_028_MAINTENANCE_WINDOW';
var TAKKEN_R6_028_ALLOWED_FIELDS_ = {
  stem: true
};

var TAKKEN_R6_028_BACKUP_META_HEADERS_ = [
  'patchId', 'createdAt', 'patchStatus', 'dbSpreadsheetId', 'targetQId',
  'sourceRowNumber', 'afterSourceRowNumber', 'beforeRowSha256', 'afterRowSha256',
  'beforeInventorySha256', 'beforeNonTargetInventorySha256', 'beforeOrderSha256',
  'afterInventorySha256', 'afterNonTargetInventorySha256', 'afterOrderSha256',
  'fieldWhitelistJson', 'replacementValuesJson'
];

function ADMIN_inspectTakkenR6028DryRun_() {
  return takkenR6028EditorRun_('R6takken-028 inspect', function() {
    var inventory = takkenR6028ReadInventory_();
    var target = inventory.byId[TAKKEN_R6_028_TARGET_QID_];
    if (!target || inventory.qIds.length !== TAKKEN_R6_028_TOTAL_COUNT_) {
      throw new Error('fixed target/count contract failed');
    }
    return {
      ok: true,
      mode: 'inspection-only',
      releaseStatus: String(TAKKEN_R6_028_RELEASE_SPEC_.releaseStatus || ''),
      matched: 1,
      wouldUpdate: 0,
      nonTargetCount: TAKKEN_R6_028_NON_TARGET_COUNT_,
      expectedBeforeMatches: target.rowSha256 === TAKKEN_R6_028_RELEASE_SPEC_.expectedBeforeRuntimeRowSha256,
      targetRowSha256: target.rowSha256,
      inventorySha256: inventory.inventorySha256,
      nonTargetInventorySha256: inventory.nonTargetInventorySha256
    };
  });
}

function ADMIN_patchTakkenR6028_(options) {
  options = options || {};
  var apply = options.apply === true;
  if (options.dryRun === false && !apply) {
    throw new Error('dry-run is the default; use {apply:true} for an explicit write');
  }
  takkenR6028ValidateApprovedSpec_();
  if (apply) takkenR6028RequireMaintenanceWindow_();
  var lock = LockService.getScriptLock();
  lock.waitLock(30000);
  try {
    var plan = takkenR6028BuildPlan_();
    takkenR6028AssertSpreadsheet_(plan, 'plan');
    if (!apply) {
      return takkenR6028Receipt_(plan, 'dry-run', 0, 1);
    }
    if (plan.matched !== 1 || plan.nonTargetCount !== TAKKEN_R6_028_NON_TARGET_COUNT_) {
      throw new Error('apply requires matched=1 and nonTargetCount=599');
    }

    var patchId = 'takken-r6-028-' + Utilities.getUuid();
    var backupSheet = takkenR6028EnsureBackupSheet_(plan.spreadsheet, true);
    takkenR6028WriteBackup_(backupSheet, patchId, plan);
    SpreadsheetApp.flush();
    takkenR6028AssertBackupComplete_(backupSheet, patchId, plan);
    takkenR6028AssertSpreadsheet_(plan, 'after-backup');

    try {
      var prewrite = takkenR6028BuildPlan_();
      takkenR6028AssertPlanSnapshot_(plan, prewrite);
      takkenR6028BatchUpdate_(prewrite, 'after');
      takkenR6028ClearQuestionCache_();
      var post = takkenR6028ReadInventory_(prewrite.dbSpreadsheetId);
      takkenR6028ValidateState_(post, prewrite, 'after');
      takkenR6028SetBackupPostState_(backupSheet, patchId, post);
      takkenR6028SetBackupStatus_(backupSheet, patchId, 'applied');
      return takkenR6028Receipt_(prewrite, 'applied', 1, 0, patchId);
    } catch (writeError) {
      throw takkenR6028HandleApplyFailure_(plan, backupSheet, patchId, writeError);
    }
  } finally {
    lock.releaseLock();
  }
}

function ADMIN_patchTakkenR6028DryRun_() {
  return takkenR6028EditorRun_('R6takken-028 patch dry-run', function() {
    return ADMIN_patchTakkenR6028_({ dryRun: true });
  });
}

function ADMIN_applyTakkenR6028_() {
  return takkenR6028EditorRun_('R6takken-028 patch apply', function() {
    return ADMIN_patchTakkenR6028_({ apply: true });
  });
}

function ADMIN_rollbackTakkenR6028_(options) {
  options = options || {};
  var patchId = String(options.patchId || '').trim();
  if (!patchId) throw new Error('patchId is required');
  var apply = options.apply === true;
  if (options.dryRun === false && !apply) {
    throw new Error('rollback dry-run is the default; use {apply:true, patchId:"..."}');
  }
  if (apply) takkenR6028RequireMaintenanceWindow_();
  var lock = LockService.getScriptLock();
  lock.waitLock(30000);
  try {
    var backupSheet = takkenR6028EnsureBackupSheet_(null, false);
    var backup = takkenR6028ReadBackup_(backupSheet, patchId);
    var plan = takkenR6028BuildRollbackPlan_(backup);
    if (!apply) return takkenR6028Receipt_(plan, 'rollback-dry-run', 0, 0, patchId, 1);
    try {
      takkenR6028BatchUpdate_(plan, 'before');
      takkenR6028ClearQuestionCache_();
      var restored = takkenR6028ReadInventory_(plan.dbSpreadsheetId);
      takkenR6028ValidateState_(restored, plan, 'before');
      takkenR6028SetBackupStatus_(backupSheet, patchId, 'rolled_back');
      return takkenR6028Receipt_(plan, 'rolled-back', 0, 0, patchId, 1);
    } catch (rollbackError) {
      try { takkenR6028SetBackupStatus_(backupSheet, patchId, 'rollback_failed'); } catch (statusError) {}
      throw new Error('rollback failed; manual review required: ' + String(rollbackError.message || rollbackError));
    }
  } finally {
    lock.releaseLock();
  }
}

function ADMIN_rollbackLatestTakkenR6028DryRun_() {
  return takkenR6028EditorRun_('R6takken-028 rollback dry-run', function() {
    return ADMIN_rollbackTakkenR6028_({ patchId: takkenR6028LatestPatchId_(), dryRun: true });
  });
}

function ADMIN_rollbackLatestTakkenR6028_() {
  return takkenR6028EditorRun_('R6takken-028 rollback apply', function() {
    return ADMIN_rollbackTakkenR6028_({ patchId: takkenR6028LatestPatchId_(), apply: true });
  });
}

function takkenR6028ValidateApprovedSpec_() {
  var spec = TAKKEN_R6_028_RELEASE_SPEC_;
  if (!spec || spec.qId !== TAKKEN_R6_028_TARGET_QID_) throw new Error('fixed release spec is missing or has the wrong qId');
  if (String(spec.releaseStatus || '') !== 'approved') {
    throw new Error('official release ledger is not approved; mutation and patch dry-run are blocked');
  }
  var fields = spec.fieldWhitelist;
  if (!fields || fields.length !== 1 || fields[0] !== 'stem') {
    throw new Error('approved field whitelist must be exactly stem');
  }
  if (spec.officialSourceSha256 !== '82a95815f991567ebc4982b05a15a71f6ec942bd6794c3bafe3bcf9c2e985bae' ||
      Number(spec.officialSourcePage) !== 16 || spec.sourceKind !== 'RETIO_official_question_pdf' ||
      spec.expectedLabelSequence !== 'ア・イ・ウ') {
    throw new Error('approved spec official-source identity mismatch');
  }
  if (spec.liveDiagnosticReceiptSha256 !== 'b73cffb1a1e5cf43fc5894edb5107c20d5fbc9bd06a39bd280425d344c810925') {
    throw new Error('approved live diagnostic receipt identity mismatch');
  }
  if (!spec.liveDateOnlyFields || spec.liveDateOnlyFields.length !== 1 || spec.liveDateOnlyFields[0] !== 'updatedAt') {
    throw new Error('approved live date-only contract must be exactly updatedAt');
  }
  var liveOverrideKeys = Object.keys(spec.liveBaselineOverrides || {});
  if (liveOverrideKeys.length !== 1 || liveOverrideKeys[0] !== 'explainLong' || spec.liveBaselineOverrides.explainLong !== '') {
    throw new Error('approved live baseline must preserve blank explainLong');
  }
  var seen = {};
  fields.forEach(function(field) {
    if (!TAKKEN_R6_028_ALLOWED_FIELDS_[field] || seen[field]) throw new Error('invalid or duplicate approved field: ' + field);
    seen[field] = true;
  });
  var beforeKeys = Object.keys(spec.beforeValues || {}).sort().join('\t');
  var afterKeys = Object.keys(spec.replacementValues || {}).sort().join('\t');
  var fieldKeys = fields.slice().sort().join('\t');
  if (beforeKeys !== fieldKeys || afterKeys !== fieldKeys) throw new Error('approved payload keys do not equal field whitelist');
  fields.forEach(function(field) {
    if (typeof spec.beforeValues[field] !== 'string' || typeof spec.replacementValues[field] !== 'string') {
      throw new Error('approved payload values must be strings');
    }
    if (takkenR6028CanonicalText_(spec.beforeValues[field]) === takkenR6028CanonicalText_(spec.replacementValues[field])) {
      throw new Error('field whitelist must contain changed fields only: ' + field);
    }
  });
  [
    spec.officialSourceSha256,
    spec.expectedBeforeRuntimeRowSha256,
    spec.expectedAfterRuntimeRowSha256,
    spec.sourceBeforeRuntimeRowSha256,
    spec.sourceAfterRuntimeRowSha256,
    spec.liveDiagnosticReceiptSha256,
    spec.beforeValuesSha256,
    spec.replacementValuesSha256,
    spec.approvalEvidenceSha256
  ].forEach(function(hash) {
    if (!/^[0-9a-f]{64}$/.test(String(hash || ''))) throw new Error('approved spec contains a missing/invalid SHA-256');
  });
  if (!spec.reviewedAt) throw new Error('approved spec has no review timestamp');
  if (takkenR6028ValuesSha256_(spec.beforeValues, fields) !== spec.beforeValuesSha256) throw new Error('beforeValues hash mismatch');
  if (takkenR6028ValuesSha256_(spec.replacementValues, fields) !== spec.replacementValuesSha256) throw new Error('replacementValues hash mismatch');
}

function takkenR6028ReadInventory_() {
  var expectedDbId = arguments.length ? String(arguments[0] || '').trim() : '';
  var configuredDbId = String(getDbId_() || '').trim();
  if (!configuredDbId) throw new Error('DB_SPREADSHEET_ID is missing; no mutation allowed');
  var spreadsheet = getDb_();
  var loadedDbId = String(spreadsheet.getId() || '').trim();
  if (!loadedDbId || loadedDbId !== configuredDbId) throw new Error('loaded Spreadsheet.getId does not match DB_SPREADSHEET_ID');
  if (expectedDbId && loadedDbId !== expectedDbId) throw new Error('loaded Spreadsheet object does not match planned DB');
  var sheet = spreadsheet.getSheetByName(SHEETS.QuestionBank);
  if (!sheet) throw new Error('QuestionBank sheet not found');
  var dataRange = sheet.getDataRange();
  var values = dataRange.getValues();
  var displayValues = dataRange.getDisplayValues();
  if (values.length !== TAKKEN_R6_028_TOTAL_COUNT_ + 1) throw new Error('QuestionBank must contain exactly 600 data rows');
  if (displayValues.length !== values.length) throw new Error('QuestionBank display/value row count mismatch');
  var headers = values[0].map(function(value, index) { return normalizeHeader_(value, index); });
  var expectedHeaders = HEADERS[SHEETS.QuestionBank];
  if (headers.join('\t') !== expectedHeaders.join('\t')) throw new Error('QuestionBank header mismatch');
  var index = {};
  headers.forEach(function(header, column) { index[header] = column; });
  var byId = {};
  var rowFingerprints = {};
  var orderedQIds = [];
  for (var rowIndex = 1; rowIndex < values.length; rowIndex++) {
    var row = values[rowIndex];
    if (row.length !== headers.length) throw new Error('QuestionBank row width mismatch at ' + (rowIndex + 1));
    var qId = String(row[index.qId] || '').trim();
    if (!qId || Object.prototype.hasOwnProperty.call(byId, qId)) throw new Error('blank or duplicate qId: ' + qId);
    if (!displayValues[rowIndex] || displayValues[rowIndex].length !== headers.length) throw new Error('QuestionBank display row width mismatch at ' + (rowIndex + 1));
    var rowSha256 = takkenR6028FullRowSha256_(row, headers);
    byId[qId] = { row: row.slice(), displayRow: displayValues[rowIndex].slice(), sheetRow: rowIndex + 1, rowSha256: rowSha256 };
    rowFingerprints[qId] = { rowSha256: rowSha256, sheetRow: rowIndex + 1 };
    orderedQIds.push(qId);
  }
  var qIds = Object.keys(byId).sort();
  if (qIds.length !== TAKKEN_R6_028_TOTAL_COUNT_) throw new Error('QuestionBank unique qId count is not 600');
  if (!byId[TAKKEN_R6_028_TARGET_QID_]) throw new Error('fixed target qId is missing');
  return {
    spreadsheet: spreadsheet,
    spreadsheetId: loadedDbId,
    sheet: sheet,
    sheetId: sheet.getSheetId(),
    headers: headers,
    headerIndex: index,
    byId: byId,
    rowFingerprints: rowFingerprints,
    qIds: qIds,
    orderedQIds: orderedQIds,
    inventorySha256: takkenR6028InventorySha256_(rowFingerprints),
    nonTargetInventorySha256: takkenR6028InventorySha256_(rowFingerprints, TAKKEN_R6_028_TARGET_QID_),
    orderSha256: takkenR6028Sha256_(orderedQIds.join('\u001f'))
  };
}

function takkenR6028BuildPlan_() {
  takkenR6028ValidateApprovedSpec_();
  var dbId = String(getDbId_() || '').trim();
  var inventory = takkenR6028ReadInventory_(dbId);
  var spec = TAKKEN_R6_028_RELEASE_SPEC_;
  var target = inventory.byId[TAKKEN_R6_028_TARGET_QID_];
  if (target.rowSha256 !== spec.expectedBeforeRuntimeRowSha256) throw new Error('expected-before full-row hash mismatch');
  if (!takkenR6028IsDateCell_(target.row[inventory.headerIndex.updatedAt])) throw new Error('updatedAt live type mismatch; Date cell required');
  if (target.displayRow[inventory.headerIndex.updatedAt] !== '2026-04-10') throw new Error('updatedAt display baseline mismatch');
  spec.fieldWhitelist.forEach(function(field) {
    var index = inventory.headerIndex[field];
    if (index === undefined) throw new Error('approved field missing from QuestionBank: ' + field);
    if (takkenR6028CanonicalCell_(target.row[index], field) !== takkenR6028CanonicalText_(spec.beforeValues[field])) {
      throw new Error('expected-before field mismatch: ' + field);
    }
  });
  Object.keys(spec.liveBaselineOverrides).forEach(function(field) {
    var protectedIndex = inventory.headerIndex[field];
    if (protectedIndex === undefined || takkenR6028CanonicalCell_(target.row[protectedIndex], field) !== spec.liveBaselineOverrides[field]) {
      throw new Error('approved protected live baseline mismatch: ' + field);
    }
  });
  var beforeRow = target.row.slice();
  var afterRow = beforeRow.slice();
  spec.fieldWhitelist.forEach(function(field) { afterRow[inventory.headerIndex[field]] = spec.replacementValues[field]; });
  var afterRowSha256 = takkenR6028FullRowSha256_(afterRow, inventory.headers);
  if (afterRowSha256 !== spec.expectedAfterRuntimeRowSha256) throw new Error('expected-after full-row hash mismatch');
  takkenR6028AssertOnlyWhitelistedChanged_(beforeRow, afterRow, inventory.headers, spec.fieldWhitelist);
  var expectedAfterFingerprints = takkenR6028CopyFingerprints_(inventory.rowFingerprints);
  expectedAfterFingerprints[TAKKEN_R6_028_TARGET_QID_].rowSha256 = afterRowSha256;
  return {
    ok: true,
    matched: 1,
    nonTargetCount: TAKKEN_R6_028_NON_TARGET_COUNT_,
    dbSpreadsheetId: dbId,
    spreadsheet: inventory.spreadsheet,
    sheetId: inventory.sheetId,
    headers: inventory.headers,
    headerIndex: inventory.headerIndex,
    qIds: inventory.qIds,
    orderedQIds: inventory.orderedQIds,
    rowFingerprints: inventory.rowFingerprints,
    inventorySha256: inventory.inventorySha256,
    nonTargetInventorySha256: inventory.nonTargetInventorySha256,
    orderSha256: inventory.orderSha256,
    expectedAfterInventorySha256: takkenR6028InventorySha256_(expectedAfterFingerprints),
    expectedAfterNonTargetInventorySha256: inventory.nonTargetInventorySha256,
    expectedAfterOrderSha256: inventory.orderSha256,
    target: {
      qId: TAKKEN_R6_028_TARGET_QID_,
      sheetRow: target.sheetRow,
      beforeRow: beforeRow,
      afterRow: afterRow,
      beforeRowSha256: target.rowSha256,
      afterRowSha256: afterRowSha256,
      fieldWhitelist: spec.fieldWhitelist.slice(),
      beforeValues: takkenR6028CopyObject_(spec.beforeValues),
      replacementValues: takkenR6028CopyObject_(spec.replacementValues)
    }
  };
}

function takkenR6028AssertPlanSnapshot_(before, after) {
  takkenR6028AssertSpreadsheet_(before, 'prewrite-before');
  takkenR6028AssertSpreadsheet_(after, 'prewrite-after');
  if (before.dbSpreadsheetId !== after.dbSpreadsheetId || before.spreadsheet !== after.spreadsheet) throw new Error('DB/Spreadsheet changed between plan and prewrite');
  if (before.inventorySha256 !== after.inventorySha256 || before.nonTargetInventorySha256 !== after.nonTargetInventorySha256) throw new Error('QuestionBank content changed between plan and prewrite');
  if (before.orderSha256 !== after.orderSha256 || before.orderedQIds.join('\t') !== after.orderedQIds.join('\t')) throw new Error('QuestionBank row order changed between plan and prewrite');
  if (before.target.beforeRowSha256 !== after.target.beforeRowSha256 || before.target.sheetRow !== after.target.sheetRow) throw new Error('target row changed or moved between plan and prewrite');
}

function takkenR6028AssertSpreadsheet_(plan, phase) {
  var currentId = String(getDbId_() || '').trim();
  if (!plan || !plan.dbSpreadsheetId || currentId !== plan.dbSpreadsheetId) throw new Error('DB_SPREADSHEET_ID changed or is missing at ' + phase);
  var spreadsheet = getDb_();
  var loadedId = String(spreadsheet.getId() || '').trim();
  if (loadedId !== plan.dbSpreadsheetId) throw new Error('loaded Spreadsheet.getId changed at ' + phase);
  if (plan.spreadsheet && spreadsheet !== plan.spreadsheet) throw new Error('loaded Spreadsheet object changed at ' + phase);
  return spreadsheet;
}

function takkenR6028BatchUpdate_(plan, desiredState) {
  if (desiredState !== 'before' && desiredState !== 'after') throw new Error('invalid desired state');
  takkenR6028AssertSpreadsheet_(plan, 'api-preflight');
  if (typeof Sheets === 'undefined' || !Sheets.Spreadsheets || typeof Sheets.Spreadsheets.batchUpdate !== 'function') {
    throw new Error('Advanced Sheets service unavailable; no fallback is permitted');
  }
  // Final read/rebind occurs inside the only QuestionBank write primitive.
  // A maintenance window is still mandatory because manual Sheet edits are not
  // covered by ScriptLock during the final network-call interval.
  var fresh = takkenR6028ReadInventory_(plan.dbSpreadsheetId);
  takkenR6028ValidateState_(fresh, plan, desiredState === 'after' ? 'before' : 'after');
  takkenR6028AssertSpreadsheet_(plan, 'api-immediate');
  var target = fresh.byId[TAKKEN_R6_028_TARGET_QID_];
  var fromRow = desiredState === 'after' ? plan.target.beforeRow : plan.target.afterRow;
  var toRow = desiredState === 'after' ? plan.target.afterRow : plan.target.beforeRow;
  var requests = takkenR6028BuildUpdateRequests_(fresh, target.sheetRow, fromRow, toRow, plan.target.fieldWhitelist);
  var response = Sheets.Spreadsheets.batchUpdate({ requests: requests, includeSpreadsheetInResponse: false }, plan.dbSpreadsheetId);
  var replies = response && response.replies;
  if (!replies || replies.length !== requests.length) throw new Error('Sheets batchUpdate reply count mismatch');
  return { requests: requests.length, targetRows: 1 };
}

function takkenR6028BuildUpdateRequests_(inventory, sheetRow, fromRow, toRow, whitelist) {
  var indexes = whitelist.map(function(field) { return inventory.headerIndex[field]; }).sort(function(a, b) { return a - b; });
  var groups = [];
  indexes.forEach(function(index) {
    var last = groups.length ? groups[groups.length - 1] : null;
    if (last && last.end === index) last.end = index + 1;
    else groups.push({ start: index, end: index + 1 });
  });
  if (!groups.length) throw new Error('no approved update groups');
  return groups.map(function(group) {
    var cells = [];
    for (var index = group.start; index < group.end; index++) {
      if (takkenR6028CanonicalText_(fromRow[index]) === takkenR6028CanonicalText_(toRow[index])) throw new Error('update request contains an unchanged field');
      cells.push({ userEnteredValue: { stringValue: takkenR6028CanonicalText_(toRow[index]) } });
    }
    return {
      updateCells: {
        rows: [{ values: cells }],
        fields: 'userEnteredValue',
        range: {
          sheetId: inventory.sheetId,
          startRowIndex: sheetRow - 1,
          endRowIndex: sheetRow,
          startColumnIndex: group.start,
          endColumnIndex: group.end
        }
      }
    };
  });
}

function takkenR6028ValidateState_(inventory, plan, state) {
  if (state !== 'before' && state !== 'after') throw new Error('invalid validation state');
  if (inventory.spreadsheetId !== plan.dbSpreadsheetId) throw new Error(state + ' DB mismatch');
  if (inventory.qIds.join('\t') !== plan.qIds.join('\t')) throw new Error(state + ' qId inventory changed');
  var expectedInventory = state === 'before' ? plan.inventorySha256 : plan.expectedAfterInventorySha256;
  var expectedNonTarget = state === 'before' ? plan.nonTargetInventorySha256 : plan.expectedAfterNonTargetInventorySha256;
  var expectedOrder = state === 'before' ? plan.orderSha256 : plan.expectedAfterOrderSha256;
  if (inventory.inventorySha256 !== expectedInventory) throw new Error(state + ' full inventory hash mismatch');
  if (inventory.nonTargetInventorySha256 !== expectedNonTarget) throw new Error(state + ' non-target inventory hash mismatch');
  if (inventory.orderSha256 !== expectedOrder || inventory.orderedQIds.join('\t') !== plan.orderedQIds.join('\t')) throw new Error(state + ' row order changed');
  var current = inventory.byId[TAKKEN_R6_028_TARGET_QID_];
  var expectedRow = state === 'before' ? plan.target.beforeRow : plan.target.afterRow;
  var expectedHash = state === 'before' ? plan.target.beforeRowSha256 : plan.target.afterRowSha256;
  if (!current || current.sheetRow !== plan.target.sheetRow || current.rowSha256 !== expectedHash) throw new Error(state + ' target row/hash mismatch');
  if (!takkenR6028IsDateCell_(current.row[inventory.headerIndex.updatedAt])) throw new Error(state + ' updatedAt live type mismatch; Date cell required');
  if (current.displayRow[inventory.headerIndex.updatedAt] !== '2026-04-10') throw new Error(state + ' updatedAt display baseline mismatch');
  if (state === 'after') {
    takkenR6028AssertOnlyWhitelistedChanged_(plan.target.beforeRow, expectedRow, inventory.headers, plan.target.fieldWhitelist);
    takkenR6028AssertOnlyWhitelistedChanged_(plan.target.beforeRow, current.row, inventory.headers, plan.target.fieldWhitelist);
  }
  return { matched: 1, updated: state === 'after' ? 1 : 0 };
}

function takkenR6028ClassifyState_(inventory, plan) {
  try { takkenR6028ValidateState_(inventory, plan, 'before'); return 'before'; } catch (beforeError) {}
  try { takkenR6028ValidateState_(inventory, plan, 'after'); return 'after'; } catch (afterError) {}
  return 'unknown';
}

function takkenR6028HandleApplyFailure_(plan, backupSheet, patchId, writeError) {
  var message = String(writeError && writeError.message || writeError || 'unknown write error');
  var current;
  try { current = takkenR6028ReadInventory_(plan.dbSpreadsheetId); }
  catch (readError) {
    try { takkenR6028SetBackupStatus_(backupSheet, patchId, 'manual_review'); } catch (statusError) {}
    return new Error('apply response/state unknown; manual review required: ' + message + '; reread failed');
  }
  var state = takkenR6028ClassifyState_(current, plan);
  if (state === 'before') {
    try { takkenR6028SetBackupStatus_(backupSheet, patchId, 'not_applied'); } catch (statusError1) {}
    return new Error('apply failed; no QuestionBank mutation verified: ' + message);
  }
  if (state === 'after') {
    try {
      takkenR6028BatchUpdate_(plan, 'before');
      takkenR6028ClearQuestionCache_();
      var restored = takkenR6028ReadInventory_(plan.dbSpreadsheetId);
      takkenR6028ValidateState_(restored, plan, 'before');
      takkenR6028SetBackupStatus_(backupSheet, patchId, 'rolled_back');
      return new Error('apply failed; exact automatic rollback verified: ' + message);
    } catch (rollbackError) {
      try { takkenR6028SetBackupStatus_(backupSheet, patchId, 'rollback_failed'); } catch (statusError2) {}
      return new Error('apply failed; rollback failed; manual review required: ' + message + '; ' + String(rollbackError.message || rollbackError));
    }
  }
  try { takkenR6028SetBackupStatus_(backupSheet, patchId, 'manual_review'); } catch (statusError3) {}
  return new Error('apply state is unknown/partial; manual review required: ' + message);
}

function takkenR6028BackupHeaders_() {
  return TAKKEN_R6_028_BACKUP_META_HEADERS_.concat(HEADERS[SHEETS.QuestionBank].map(function(header) { return 'before_' + header; }));
}

function takkenR6028EnsureBackupSheet_(spreadsheet, allowCreate) {
  allowCreate = allowCreate !== false;
  var ss = spreadsheet || getDb_();
  var sheet = ss.getSheetByName(TAKKEN_R6_028_BACKUP_SHEET_);
  var expectedHeaders = takkenR6028BackupHeaders_();
  if (!sheet) {
    if (!allowCreate) throw new Error('backup sheet not found: ' + TAKKEN_R6_028_BACKUP_SHEET_);
    sheet = ss.insertSheet(TAKKEN_R6_028_BACKUP_SHEET_);
    sheet.getRange(1, 1, 1, expectedHeaders.length).setValues([expectedHeaders]);
    sheet.setFrozenRows(1);
    return sheet;
  }
  var headers = sheet.getRange(1, 1, 1, Math.max(1, sheet.getLastColumn())).getValues()[0].map(function(value, index) { return normalizeHeader_(value, index); });
  if (headers.join('\t') !== expectedHeaders.join('\t')) throw new Error('R6-028 backup sheet header mismatch');
  return sheet;
}

function takkenR6028WriteBackup_(sheet, patchId, plan) {
  var target = plan.target;
  var row = [
    patchId, new Date(), 'prepared', plan.dbSpreadsheetId, target.qId,
    target.sheetRow, '', target.beforeRowSha256, target.afterRowSha256,
    plan.inventorySha256, plan.nonTargetInventorySha256, plan.orderSha256,
    '', '', '', JSON.stringify(target.fieldWhitelist), JSON.stringify(target.replacementValues)
  ].concat(target.beforeRow);
  sheet.getRange(sheet.getLastRow() + 1, 1, 1, row.length).setValues([row]);
}

function takkenR6028ReadBackup_(sheet, patchId) {
  var data = sheet.getDataRange().getValues();
  if (data.length < 2) throw new Error('backup sheet is empty');
  var headers = data[0].map(function(value, index) { return normalizeHeader_(value, index); });
  var index = {};
  headers.forEach(function(header, column) { index[header] = column; });
  var rows = data.slice(1).filter(function(row) { return String(row[index.patchId] || '') === patchId; });
  if (rows.length !== 1) throw new Error('rollback requires exactly one backup row: ' + rows.length);
  var row = rows[0];
  return {
    patchId: patchId,
    patchStatus: String(row[index.patchStatus] || ''),
    dbSpreadsheetId: String(row[index.dbSpreadsheetId] || '').trim(),
    targetQId: String(row[index.targetQId] || '').trim(),
    sourceRowNumber: Number(row[index.sourceRowNumber]),
    afterSourceRowNumber: Number(row[index.afterSourceRowNumber]),
    beforeRowSha256: String(row[index.beforeRowSha256] || ''),
    afterRowSha256: String(row[index.afterRowSha256] || ''),
    beforeInventorySha256: String(row[index.beforeInventorySha256] || ''),
    beforeNonTargetInventorySha256: String(row[index.beforeNonTargetInventorySha256] || ''),
    beforeOrderSha256: String(row[index.beforeOrderSha256] || ''),
    afterInventorySha256: String(row[index.afterInventorySha256] || ''),
    afterNonTargetInventorySha256: String(row[index.afterNonTargetInventorySha256] || ''),
    afterOrderSha256: String(row[index.afterOrderSha256] || ''),
    fieldWhitelist: JSON.parse(String(row[index.fieldWhitelistJson] || '[]')),
    replacementValues: JSON.parse(String(row[index.replacementValuesJson] || '{}')),
    beforeRow: HEADERS[SHEETS.QuestionBank].map(function(header) { return row[index['before_' + header]]; })
  };
}

function takkenR6028AssertBackupComplete_(sheet, patchId, plan) {
  var backup = takkenR6028ReadBackup_(sheet, patchId);
  if (backup.dbSpreadsheetId !== plan.dbSpreadsheetId || backup.targetQId !== TAKKEN_R6_028_TARGET_QID_ ||
      backup.sourceRowNumber !== plan.target.sheetRow || backup.beforeRowSha256 !== plan.target.beforeRowSha256 ||
      backup.afterRowSha256 !== plan.target.afterRowSha256 || backup.beforeInventorySha256 !== plan.inventorySha256 ||
      backup.beforeNonTargetInventorySha256 !== plan.nonTargetInventorySha256 || backup.beforeOrderSha256 !== plan.orderSha256 ||
      backup.afterInventorySha256 || backup.afterNonTargetInventorySha256 || backup.afterOrderSha256 ||
      takkenR6028FullRowSha256_(backup.beforeRow, plan.headers) !== plan.target.beforeRowSha256) {
    throw new Error('durable backup verification failed');
  }
  if (JSON.stringify(backup.fieldWhitelist) !== JSON.stringify(plan.target.fieldWhitelist) ||
      JSON.stringify(backup.replacementValues) !== JSON.stringify(plan.target.replacementValues)) {
    throw new Error('backup approved payload verification failed');
  }
}

function takkenR6028SetBackupStatus_(sheet, patchId, status) {
  var data = sheet.getDataRange().getValues();
  var headers = data[0].map(function(value, index) { return normalizeHeader_(value, index); });
  var patchColumn = headers.indexOf('patchId');
  var statusColumn = headers.indexOf('patchStatus');
  for (var row = 1; row < data.length; row++) if (String(data[row][patchColumn]) === patchId) sheet.getRange(row + 1, statusColumn + 1).setValue(status);
}

function takkenR6028SetBackupPostState_(sheet, patchId, inventory) {
  var data = sheet.getDataRange().getValues();
  var headers = data[0].map(function(value, index) { return normalizeHeader_(value, index); });
  var patchColumn = headers.indexOf('patchId');
  var rowIndex = data.slice(1).findIndex(function(row) { return String(row[patchColumn]) === patchId; });
  if (rowIndex < 0) throw new Error('backup row missing during post-state write');
  var sheetRow = rowIndex + 2;
  sheet.getRange(sheetRow, headers.indexOf('afterSourceRowNumber') + 1).setValue(inventory.byId[TAKKEN_R6_028_TARGET_QID_].sheetRow);
  sheet.getRange(sheetRow, headers.indexOf('afterInventorySha256') + 1).setValue(inventory.inventorySha256);
  sheet.getRange(sheetRow, headers.indexOf('afterNonTargetInventorySha256') + 1).setValue(inventory.nonTargetInventorySha256);
  sheet.getRange(sheetRow, headers.indexOf('afterOrderSha256') + 1).setValue(inventory.orderSha256);
}

function takkenR6028BuildRollbackPlan_(backup) {
  if (!backup || backup.targetQId !== TAKKEN_R6_028_TARGET_QID_) throw new Error('backup target qId mismatch');
  if (!backup.dbSpreadsheetId || String(getDbId_() || '').trim() !== backup.dbSpreadsheetId) throw new Error('DB_SPREADSHEET_ID does not match backup');
  if (!backup.afterInventorySha256 || !backup.afterNonTargetInventorySha256 || !backup.afterOrderSha256) throw new Error('backup has no verified post-apply baseline');
  var spreadsheet = getDb_();
  if (String(spreadsheet.getId() || '').trim() !== backup.dbSpreadsheetId) throw new Error('loaded Spreadsheet does not match backup DB');
  var inventory = takkenR6028ReadInventory_(backup.dbSpreadsheetId);
  if (inventory.inventorySha256 !== backup.afterInventorySha256 || inventory.nonTargetInventorySha256 !== backup.afterNonTargetInventorySha256 || inventory.orderSha256 !== backup.afterOrderSha256) throw new Error('post-apply inventory/non-target/order drift blocks rollback');
  var beforeRow = backup.beforeRow.slice();
  var afterRow = beforeRow.slice();
  if (!backup.fieldWhitelist.length || backup.beforeRow[inventory.headerIndex.qId] !== TAKKEN_R6_028_TARGET_QID_) throw new Error('backup target/whitelist is invalid');
  var seenFields = {};
  if (Object.keys(backup.replacementValues).sort().join('\t') !== backup.fieldWhitelist.slice().sort().join('\t')) throw new Error('backup whitelist/payload keys mismatch');
  backup.fieldWhitelist.forEach(function(field) {
    if (!TAKKEN_R6_028_ALLOWED_FIELDS_[field] || seenFields[field] || typeof backup.replacementValues[field] !== 'string') throw new Error('backup whitelist/payload is invalid');
    seenFields[field] = true;
    afterRow[inventory.headerIndex[field]] = backup.replacementValues[field];
  });
  if (takkenR6028FullRowSha256_(beforeRow, inventory.headers) !== backup.beforeRowSha256 || takkenR6028FullRowSha256_(afterRow, inventory.headers) !== backup.afterRowSha256) throw new Error('backup row hash mismatch');
  var target = inventory.byId[TAKKEN_R6_028_TARGET_QID_];
  if (!target || target.sheetRow !== backup.afterSourceRowNumber || target.rowSha256 !== backup.afterRowSha256) throw new Error('target row/order drift blocks rollback');
  if (!takkenR6028IsDateCell_(target.row[inventory.headerIndex.updatedAt]) ||
      !takkenR6028IsDateCell_(backup.beforeRow[inventory.headerIndex.updatedAt])) {
    throw new Error('updatedAt live type mismatch blocks rollback; Date cell required');
  }
  var beforeFingerprints = takkenR6028CopyFingerprints_(inventory.rowFingerprints);
  beforeFingerprints[TAKKEN_R6_028_TARGET_QID_].rowSha256 = backup.beforeRowSha256;
  return {
    ok: true,
    matched: 1,
    nonTargetCount: TAKKEN_R6_028_NON_TARGET_COUNT_,
    dbSpreadsheetId: backup.dbSpreadsheetId,
    spreadsheet: spreadsheet,
    sheetId: inventory.sheetId,
    headers: inventory.headers,
    headerIndex: inventory.headerIndex,
    qIds: inventory.qIds,
    orderedQIds: inventory.orderedQIds,
    rowFingerprints: beforeFingerprints,
    inventorySha256: backup.beforeInventorySha256,
    nonTargetInventorySha256: backup.beforeNonTargetInventorySha256,
    orderSha256: backup.beforeOrderSha256,
    expectedAfterInventorySha256: backup.afterInventorySha256,
    expectedAfterNonTargetInventorySha256: backup.afterNonTargetInventorySha256,
    expectedAfterOrderSha256: backup.afterOrderSha256,
    target: {
      qId: TAKKEN_R6_028_TARGET_QID_,
      sheetRow: target.sheetRow,
      beforeRow: beforeRow,
      afterRow: afterRow,
      beforeRowSha256: backup.beforeRowSha256,
      afterRowSha256: backup.afterRowSha256,
      fieldWhitelist: backup.fieldWhitelist.slice(),
      beforeValues: {},
      replacementValues: takkenR6028CopyObject_(backup.replacementValues)
    }
  };
}

function takkenR6028LatestPatchId_() {
  var sheet = takkenR6028EnsureBackupSheet_(null, false);
  var data = sheet.getDataRange().getValues();
  if (data.length < 2) throw new Error('no R6-028 backup exists');
  var headers = data[0].map(function(value, index) { return normalizeHeader_(value, index); });
  var patchColumn = headers.indexOf('patchId');
  for (var row = data.length - 1; row >= 1; row--) {
    var patchId = String(data[row][patchColumn] || '').trim();
    if (patchId) return patchId;
  }
  throw new Error('no R6-028 patchId exists');
}

function takkenR6028RequireMaintenanceWindow_() {
  var value = String(getScriptProps_().getProperty(TAKKEN_R6_028_MAINTENANCE_PROPERTY_) || '').trim().toUpperCase();
  if (value !== 'OPEN') throw new Error('R6-028 maintenance window is not OPEN');
}

function takkenR6028ClearQuestionCache_() {
  clearAllCache_({ strict: true });
}

function takkenR6028FullRowSha256_(row, headers) {
  if (!row || !headers || row.length !== headers.length) throw new Error('full-row hash width mismatch');
  var parts = [];
  for (var index = 0; index < headers.length; index++) parts.push(headers[index] + '\u001e' + takkenR6028CanonicalCell_(row[index], headers[index]));
  return takkenR6028Sha256_(parts.join('\u001f'));
}

function takkenR6028CanonicalCell_(value, header) {
  if (Object.prototype.toString.call(value) === '[object Date]') {
    if (header === 'updatedAt') return Utilities.formatDate(value, 'Asia/Tokyo', 'yyyy-MM-dd');
    var hasTime = value.getHours() || value.getMinutes() || value.getSeconds() || value.getMilliseconds();
    return Utilities.formatDate(value, 'Asia/Tokyo', hasTime ? 'yyyy-MM-dd HH:mm:ss' : 'yyyy-MM-dd');
  }
  return takkenR6028CanonicalText_(value);
}

function takkenR6028IsDateCell_(value) {
  return Object.prototype.toString.call(value) === '[object Date]' && !isNaN(value.getTime());
}

function takkenR6028CanonicalText_(value) {
  return String(value == null ? '' : value).replace(/\r\n/g, '\n').replace(/\r/g, '\n');
}

function takkenR6028ValuesSha256_(values, fields) {
  return takkenR6028Sha256_(fields.map(function(field) { return field + '\u001e' + takkenR6028CanonicalText_(values[field]); }).join('\u001f'));
}

function takkenR6028InventorySha256_(fingerprints, excludedQId) {
  return takkenR6028Sha256_(Object.keys(fingerprints).filter(function(qId) { return qId !== excludedQId; }).sort().map(function(qId) { return qId + '\u001f' + fingerprints[qId].rowSha256; }).join('\u001e'));
}

function takkenR6028Sha256_(value) {
  var bytes = Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, String(value), Utilities.Charset.UTF_8);
  return bytes.map(function(byte) { var n = byte < 0 ? byte + 256 : byte; return (n < 16 ? '0' : '') + n.toString(16); }).join('');
}

function takkenR6028AssertOnlyWhitelistedChanged_(beforeRow, afterRow, headers, whitelist) {
  if (beforeRow.length !== afterRow.length || beforeRow.length !== headers.length) throw new Error('row width changed');
  var allowed = {};
  whitelist.forEach(function(field) { allowed[field] = true; });
  for (var index = 0; index < headers.length; index++) {
    var same = takkenR6028CanonicalCell_(beforeRow[index]) === takkenR6028CanonicalCell_(afterRow[index]);
    if (allowed[headers[index]] && same) throw new Error('whitelisted field did not change: ' + headers[index]);
    if (!allowed[headers[index]] && !same) throw new Error('protected field changed: ' + headers[index]);
  }
}

function takkenR6028CopyFingerprints_(source) {
  var copy = {};
  Object.keys(source).forEach(function(qId) { copy[qId] = { rowSha256: source[qId].rowSha256, sheetRow: source[qId].sheetRow }; });
  return copy;
}

function takkenR6028CopyObject_(source) {
  var copy = {};
  Object.keys(source || {}).forEach(function(key) { copy[key] = source[key]; });
  return copy;
}

function takkenR6028Receipt_(plan, mode, updated, wouldUpdate, patchId, restored) {
  var receipt = {
    ok: true,
    mode: mode,
    matched: 1,
    updated: updated || 0,
    wouldUpdate: wouldUpdate || 0,
    nonTargetCount: TAKKEN_R6_028_NON_TARGET_COUNT_,
    qId: TAKKEN_R6_028_TARGET_QID_,
    beforeRowSha256: plan.target.beforeRowSha256,
    afterRowSha256: plan.target.afterRowSha256,
    fieldCount: plan.target.fieldWhitelist.length
  };
  if (patchId) receipt.patchId = patchId;
  if (restored) receipt.restored = restored;
  return receipt;
}

function takkenR6028EditorRun_(label, fn) {
  try {
    var result = fn();
    Logger.log(JSON.stringify({
      operation: label,
      ok: result.ok === true,
      mode: result.mode,
      releaseStatus: result.releaseStatus,
      matched: result.matched,
      updated: result.updated,
      wouldUpdate: result.wouldUpdate,
      nonTargetCount: result.nonTargetCount,
      qId: result.qId,
      fieldCount: result.fieldCount,
      patchId: result.patchId,
      beforeRowSha256: result.beforeRowSha256 || result.targetRowSha256,
      afterRowSha256: result.afterRowSha256
    }));
    return result;
  } catch (error) {
    Logger.log(JSON.stringify({ operation: label, ok: false, errorClass: 'R6_028_PATCH_BLOCKED_OR_FAILED' }));
    throw error;
  }
}
