/**
 * 【2026-04-03】新規メンバー2名を両アプリの UserAccess に追加する。
 * 既存データはクリアせず、重複チェック付きで末尾に追記する。
 *
 * 使い方:
 *   1. GAS エディタでこの関数を選択して「実行」ボタンを押す
 *   2. ログで結果を確認する
 */
function addMembers20260403_() {
  var newMembers = [
    ['m.terada.tscg@gmail.com', 'user', '寺田 征弘'],
    ['t.masuhara.tscg@gmail.com', 'user', '増原 卓也']
  ];

  var now = Utilities.formatDate(new Date(), 'Asia/Tokyo', 'yyyy-MM-dd HH:mm:ss');

  // --- 土木アプリ ---
  var dobokuDb = getDb_();
  var dobokuResult = appendMembersIfNew_(dobokuDb, newMembers, now);
  Logger.log('【土木】追加: ' + dobokuResult.added + '名, スキップ: ' + dobokuResult.skipped + '名');

  // --- 建築アプリ ---
  var archiDbId = '1tesaYYXP7hsZFbq03irX_MNGvb_TZyeG609QNOvU6WU';
  var archiDb = SpreadsheetApp.openById(archiDbId);
  var archiResult = appendMembersIfNew_(archiDb, newMembers, now);
  Logger.log('【建築】追加: ' + archiResult.added + '名, スキップ: ' + archiResult.skipped + '名');

  Logger.log('');
  Logger.log('=== 完了 ===');
}

/**
 * UserAccess シートに重複チェック付きでメンバーを追記する。
 * @param {Spreadsheet} ss - 対象スプレッドシート
 * @param {Array} members - [[email, role, displayName], ...]
 * @param {string} now - フォーマット済みタイムスタンプ
 * @return {{added: number, skipped: number}}
 */
function appendMembersIfNew_(ss, members, now) {
  var sh = ss.getSheetByName('UserAccess');
  if (!sh) throw new Error('UserAccessシートが見つかりません: ' + ss.getName());

  var lastRow = sh.getLastRow();
  var existingEmails = {};
  if (lastRow >= 2) {
    var emailValues = sh.getRange(2, 1, lastRow - 1, 1).getValues();
    for (var i = 0; i < emailValues.length; i++) {
      var email = String(emailValues[i][0]).trim().toLowerCase();
      if (email) {
        existingEmails[email] = true;
      }
    }
  }

  var added = 0;
  var skipped = 0;

  for (var j = 0; j < members.length; j++) {
    var m = members[j];
    var memberEmail = String(m[0]).trim().toLowerCase();

    if (existingEmails[memberEmail]) {
      Logger.log('  スキップ（既存）: ' + m[0]);
      skipped++;
      continue;
    }

    // UserAccess HEADERS: ['email', 'role', 'managerEmail', 'active', 'updatedAt', 'displayName']
    var newRow = [m[0], m[1], '', 'TRUE', now, m[2]];
    var appendRow = sh.getLastRow() + 1;
    sh.getRange(appendRow, 1, 1, newRow.length).setValues([newRow]);
    Logger.log('  追加: ' + m[0] + ' (' + m[2] + ')');
    added++;
  }

  return { added: added, skipped: skipped };
}
