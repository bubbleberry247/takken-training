function getCanonicalMembers_() {
  return [
    { email: 't.hanai.tscg@gmail.com',      role: 'user',  displayName: '花井辰佳' },
    { email: 'y.shinjo.tscg@gmail.com',     role: 'user',  displayName: '新城雄一朗' },
    { email: 'h.kakegawa.tscg@gmail.com',   role: 'user',  displayName: '掛川晴喜' },
    { email: 'r.yokoi.tscg@gmail.com',      role: 'user',  displayName: '横井稜' },
    { email: 's.ishihara.tscg@gmail.com',   role: 'user',  displayName: '石原駿太朗' },
    { email: 'y.isoda.tscg@gmail.com',      role: 'user',  displayName: '磯田百合香' },
    { email: 'k.fukushima.tscg@gmail.com',  role: 'user',  displayName: '福島楓' },
    { email: 'm.terada.tscg@gmail.com',     role: 'user',  displayName: '寺田征弘' },
    { email: 'm.inagaki.tscg@gmail.com',    role: 'user',  displayName: '稲垣誠' },
    { email: 'i.suzuki.tscg@gmail.com',     role: 'user',  displayName: '鈴木勲' },
    { email: 'y.nagasaki.tscg@gmail.com',   role: 'user',  displayName: '長崎豊' },
    { email: 'i.matumura.tscg@gmail.com',   role: 'user',  displayName: '松村巌' },
    { email: 't.masuhara.tscg@gmail.com',   role: 'user',  displayName: '増原卓也' },
    { email: 'e.morikami.tscg@gmail.com',   role: 'user',  displayName: '森上栄介' },
    { email: 'm.yano.tscg@gmail.com',       role: 'user',  displayName: '矢野将也' },
    { email: 'k.anraku.tscg@gmail.com',     role: 'user',  displayName: '安樂洸介' },
    { email: 't.yasui.tscg@gmail.com',      role: 'user',  displayName: '安井智紀' },
    { email: 't.kitamura.tscg@gmail.com',   role: 'admin', displayName: '北村健' },
    { email: 'm.tsuji.tscg@gmail.com',      role: 'admin', displayName: '辻雅幸' },
    { email: 'y.otomori.tscg@gmail.com',    role: 'admin', displayName: '乙守陽介' },
    { email: 'k.fukuoka.tscg@gmail.com',    role: 'admin', displayName: '福岡健治' },
    { email: 'y.minamiwaki.tscg@gmail.com', role: 'admin', displayName: '南脇祐輔' },
    { email: 'h.kondo.tscg@gmail.com',      role: 'user',  displayName: '近藤秀夫' },
    { email: 'a.furukawa.tscg@gmail.com',   role: 'admin', displayName: '古川あかね' },
    { email: 'm.fujita.tscg@gmail.com',     role: 'admin', displayName: '藤田美和' },
    { email: 'kalimistk@gmail.com',         role: 'admin', displayName: '開発者', showInDashboard: false }
  ];
}

function getCanonicalMemberMap_() {
  var map = {};
  getCanonicalMembers_().forEach(function(member) {
    var email = String(member.email || '').trim().toLowerCase();
    if (!email) return;
    map[email] = {
      email: email,
      role: String(member.role || 'user').trim().toLowerCase(),
      displayName: String(member.displayName || '').trim(),
      showInDashboard: normalizeUserAccessBoolean_(member.showInDashboard, true) !== 'false'
    };
  });
  return map;
}

function ensureUserAccessDashboardSchema_(sheet) {
  var headers = HEADERS[SHEETS.UserAccess];
  if (sheet.getMaxColumns() < headers.length) {
    sheet.insertColumnsAfter(sheet.getMaxColumns(), headers.length - sheet.getMaxColumns());
  }
  sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
  sheet.setFrozenRows(1);
}

function syncDashboardRoster() {
  return syncDashboardRosterForCurrentApp_();
}

function syncDashboardRosterForCurrentApp_() {
  var tz = 'Asia/Tokyo';
  try {
    tz = getConfigValue_(getConfigMap_(), 'TIMEZONE', 'Asia/Tokyo');
  } catch (e) {}
  var nowText = formatDateTime_(getNow_(), tz);
  var ss = getDb_();
  var userAccess = syncUserAccessRosterForSpreadsheet_(ss, nowText);
  var users = syncUsersRosterForSpreadsheet_(ss);
  return {
    status: 'ok',
    spreadsheetId: ss.getId(),
    spreadsheetName: ss.getName(),
    userAccess: userAccess,
    users: users
  };
}

function syncUserAccessRosterForSpreadsheet_(ss, nowText) {
  var sh = ss.getSheetByName(SHEETS.UserAccess);
  if (!sh) throw new Error('UserAccessシートが見つかりません: ' + ss.getName());
  ensureUserAccessDashboardSchema_(sh);

  var rows = readRecords_(sh);
  var canonical = getCanonicalMembers_();
  var canonicalMap = getCanonicalMemberMap_();
  var primaryByEmail = {};
  var hiddenRows = [];

  rows.forEach(function(row) {
    var email = String(row.email || '').trim().toLowerCase();
    if (!email) return;
    var normalized = {
      email: email,
      role: String(row.role || '').trim().toLowerCase() || 'user',
      managerEmail: String(row.managerEmail || '').trim(),
      active: normalizeUserAccessBoolean_(row.active, true),
      updatedAt: String(row.updatedAt || '').trim(),
      displayName: String(row.displayName || '').trim(),
      showInDashboard: normalizeUserAccessBoolean_(row.showInDashboard, true)
    };
    if (canonicalMap[email] && !primaryByEmail[email]) {
      primaryByEmail[email] = normalized;
      return;
    }
    hiddenRows.push(normalized);
  });

  var finalRows = [];
  var insertedCanonical = 0;
  canonical.forEach(function(member) {
    var email = String(member.email || '').trim().toLowerCase();
    var existing = primaryByEmail[email];
    if (!existing) insertedCanonical += 1;
    finalRows.push([
      email,
      String(member.role || (existing && existing.role) || 'user').trim().toLowerCase(),
      existing ? String(existing.managerEmail || '').trim() : '',
      existing ? normalizeUserAccessBoolean_(existing.active, true) : 'true',
      nowText,
      String(member.displayName || '').trim(),
      normalizeUserAccessBoolean_(member.showInDashboard, true)
    ]);
  });

  hiddenRows.forEach(function(row) {
    var fallback = canonicalMap[row.email];
    finalRows.push([
      row.email,
      row.role || (fallback ? fallback.role : 'user'),
      row.managerEmail || '',
      normalizeUserAccessBoolean_(row.active, true),
      nowText,
      row.displayName || (fallback ? fallback.displayName : row.email),
      'false'
    ]);
  });

  var clearCols = Math.max(sh.getLastColumn(), HEADERS[SHEETS.UserAccess].length);
  if (sh.getLastRow() > 1) {
    sh.getRange(2, 1, sh.getLastRow() - 1, clearCols).clearContent();
  }
  if (finalRows.length > 0) {
    sh.getRange(2, 1, finalRows.length, HEADERS[SHEETS.UserAccess].length).setValues(finalRows);
  }

  return {
    canonicalCount: canonical.length,
    insertedCanonical: insertedCanonical,
    hiddenCount: hiddenRows.length,
    totalRowsWritten: finalRows.length
  };
}

function syncUsersDisplayNamesForSpreadsheet_(ss) {
  var userSh = ss.getSheetByName(SHEETS.Users);
  if (!userSh) {
    return { updated: 0, totalRows: 0 };
  }
  var uaSh = ss.getSheetByName(SHEETS.UserAccess);
  if (!uaSh) {
    return { updated: 0, totalRows: 0 };
  }

  var canonicalMap = getCanonicalMemberMap_();
  var visibleByEmail = {};
  readRecords_(uaSh).forEach(function(row) {
    var email = String(row.email || '').trim().toLowerCase();
    if (!email || !canonicalMap[email]) return;
    if (normalizeUserAccessBoolean_(row.active, true) === 'false') return;
    visibleByEmail[email] = String(row.displayName || canonicalMap[email].displayName || '').trim();
  });

  var values = userSh.getDataRange().getValues();
  if (values.length <= 1) {
    return { updated: 0, totalRows: 0 };
  }
  var headers = values[0].map(function(h, idx) { return normalizeHeader_(h, idx); });
  var emailIdx = headers.indexOf('email');
  var displayNameIdx = headers.indexOf('displayName');
  if (emailIdx < 0 || displayNameIdx < 0) {
    return { updated: 0, totalRows: values.length - 1 };
  }

  var updated = 0;
  for (var i = 1; i < values.length; i++) {
    var email = String(values[i][emailIdx] || '').trim().toLowerCase();
    var desired = visibleByEmail[email] || '';
    if (!desired) continue;
    if (String(values[i][displayNameIdx] || '') === desired) continue;
    values[i][displayNameIdx] = desired;
    updated += 1;
  }

  if (updated > 0) {
    userSh.getRange(2, 1, values.length - 1, values[0].length).setValues(values.slice(1));
  }

  return { updated: updated, totalRows: values.length - 1 };
}

function generateRosterRecoveryCode_() {
  return String(Utilities.getUuid()).replace(/-/g, '').slice(0, 12);
}

function syncUsersRosterForSpreadsheet_(ss) {
  var userSh = ss.getSheetByName(SHEETS.Users);
  var uaSh = ss.getSheetByName(SHEETS.UserAccess);
  if (!uaSh) return { inserted: 0, updated: 0, totalRows: 0 };
  if (!userSh) {
    userSh = ss.insertSheet(SHEETS.Users);
    userSh.getRange(1, 1, 1, HEADERS[SHEETS.Users].length).setValues([HEADERS[SHEETS.Users]]);
    userSh.setFrozenRows(1);
  }

  var canonicalMap = getCanonicalMemberMap_();
  var desiredByEmail = {};
  readRecords_(uaSh).forEach(function(row) {
    var email = String(row.email || '').trim().toLowerCase();
    if (!email || !canonicalMap[email]) return;
    if (normalizeUserAccessBoolean_(row.active, true) === 'false') return;
    desiredByEmail[email] = {
      email: email,
      displayName: String(row.displayName || canonicalMap[email].displayName || '').trim()
    };
  });

  var values = userSh.getDataRange().getValues();
  var headers = values.length ? values[0].map(function(h, idx) { return normalizeHeader_(h, idx); }) : [];
  if (!headers.length || headers.indexOf('email') < 0) {
    headers = HEADERS[SHEETS.Users].slice();
    userSh.clear();
    userSh.getRange(1, 1, 1, headers.length).setValues([headers]);
    userSh.setFrozenRows(1);
    values = [headers];
  }

  var userKeyIdx = headers.indexOf('userKey');
  var emailIdx = headers.indexOf('email');
  var displayNameIdx = headers.indexOf('displayName');
  var createdAtIdx = headers.indexOf('createdAt');

  var updated = 0;
  var seen = {};
  for (var i = 1; i < values.length; i++) {
    var email = String(values[i][emailIdx] || '').trim().toLowerCase();
    if (!email) continue;
    seen[email] = true;
    var desired = desiredByEmail[email];
    if (desired && displayNameIdx >= 0 && desired.displayName && String(values[i][displayNameIdx] || '') !== desired.displayName) {
      values[i][displayNameIdx] = desired.displayName;
      updated += 1;
    }
    if (desired && userKeyIdx >= 0 && !String(values[i][userKeyIdx] || '').trim()) {
      values[i][userKeyIdx] = email;
      updated += 1;
    }
    if (desired && createdAtIdx >= 0 && !String(values[i][createdAtIdx] || '').trim()) {
      values[i][createdAtIdx] = new Date().toISOString();
      updated += 1;
    }
  }

  if (updated > 0) {
    userSh.getRange(2, 1, values.length - 1, values[0].length).setValues(values.slice(1));
  }

  var nowIso = new Date().toISOString();
  var insertedRows = [];
  Object.keys(desiredByEmail).forEach(function(email) {
    if (seen[email]) return;
    var desired = desiredByEmail[email];
    insertedRows.push(headers.map(function(h) {
      if (h === 'userKey') return email;
      if (h === 'email') return email;
      if (h === 'displayName') return desired.displayName;
      if (h === 'createdAt') return nowIso;
      if (h === 'recoveryCode') return generateRosterRecoveryCode_();
      return '';
    }));
  });

  if (insertedRows.length > 0) {
    userSh.getRange(userSh.getLastRow() + 1, 1, insertedRows.length, headers.length).setValues(insertedRows);
  }

  return { inserted: insertedRows.length, updated: updated, totalRows: Math.max(0, userSh.getLastRow() - 1) };
}
