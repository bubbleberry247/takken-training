// importCsv.gs
// CSVインポート機能

/**
 * QuestionBankシートにCSVデータをインポート
 * @param {string} csvText - CSV文字列（ヘッダー含む）
 * @returns {Object} { ok: boolean, rowsImported: number, error?: string }
 */
function importQuestionBankFromCsv(csvText) {
  try {
    if (!csvText || typeof csvText !== 'string') {
      throw new Error('csvText is required and must be a string');
    }

    // CSVをパース
    var rows = parseCsv_(csvText);
    if (rows.length === 0) {
      throw new Error('CSV contains no data');
    }

    // QuestionBankシートを取得
    var sh = getSheet_(SHEETS.QuestionBank);

    // シートをクリア（ヘッダー含む全データ削除）
    sh.clear();

    // CSVデータを一括書き込み
    var numRows = rows.length;
    var numCols = rows[0].length;

    if (numRows > 10000) {
      throw new Error('CSV contains too many rows (limit: 10000). Current: ' + numRows);
    }

    sh.getRange(1, 1, numRows, numCols).setValues(rows);

    // ヘッダー行を固定
    sh.setFrozenRows(1);

    // キャッシュをクリア
    clearAllCache_();

    Logger.log('importQuestionBankFromCsv: imported ' + (numRows - 1) + ' questions');

    return {
      ok: true,
      rowsImported: numRows - 1,  // ヘッダー除く
      totalRows: numRows,
      columns: numCols
    };

  } catch (err) {
    Logger.log('importQuestionBankFromCsv ERROR: ' + err.message);
    return {
      ok: false,
      error: err.message,
      stack: err.stack
    };
  }
}

/**
 * CSVテキストをパースして2D配列に変換
 * @param {string} csvText - CSV文字列
 * @returns {Array<Array<string>>} 2D配列
 */
function parseCsv_(csvText) {
  var lines = [];
  var current = '';
  var inQuotes = false;

  // BOM削除
  if (csvText.charCodeAt(0) === 0xFEFF) {
    csvText = csvText.substring(1);
  }

  // 行単位に分割（ダブルクォート内の改行を考慮）
  for (var i = 0; i < csvText.length; i++) {
    var c = csvText[i];

    if (c === '"') {
      inQuotes = !inQuotes;
      current += c;
    } else if (c === '\n' && !inQuotes) {
      if (current.trim()) {
        lines.push(current);
      }
      current = '';
    } else if (c === '\r') {
      // スキップ（\r\n対応）
      if (i + 1 < csvText.length && csvText[i + 1] === '\n') {
        continue;
      } else if (!inQuotes) {
        if (current.trim()) {
          lines.push(current);
        }
        current = '';
      } else {
        current += c;
      }
    } else {
      current += c;
    }
  }

  // 最後の行
  if (current.trim()) {
    lines.push(current);
  }

  // 各行をカンマ区切りで分割
  var rows = [];
  for (var j = 0; j < lines.length; j++) {
    var row = parseCsvLine_(lines[j]);
    rows.push(row);
  }

  return rows;
}

/**
 * CSV行をパース（ダブルクォート対応）
 * @param {string} line - CSV行
 * @returns {Array<string>} 列配列
 */
function parseCsvLine_(line) {
  var fields = [];
  var current = '';
  var inQuotes = false;

  for (var i = 0; i < line.length; i++) {
    var c = line[i];
    var next = (i + 1 < line.length) ? line[i + 1] : null;

    if (c === '"') {
      if (inQuotes && next === '"') {
        // エスケープされたダブルクォート
        current += '"';
        i++; // skip next
      } else {
        // クォート開始/終了
        inQuotes = !inQuotes;
      }
    } else if (c === ',' && !inQuotes) {
      // フィールド区切り
      fields.push(current);
      current = '';
    } else {
      current += c;
    }
  }

  // 最後のフィールド
  fields.push(current);

  return fields;
}

/**
 * QuestionBankインポート用のGoogle DriveフォルダURLを返す
 * @returns {Object} { ok: boolean, folderId?: string, folderUrl?: string, message: string }
 */
function getQuestionBankImportUrl() {
  try {
    var folder = getOrCreateImportFolder_();
    return {
      ok: true,
      folderId: folder.getId(),
      folderUrl: folder.getUrl(),
      message: 'このフォルダにCSVファイルをアップロードしてください。ファイル名: questionbank_import.csv'
    };
  } catch (err) {
    return {
      ok: false,
      error: err.message,
      message: '代わりに、CSVテキストを直接 importQuestionBankFromCsv() に渡すこともできます'
    };
  }
}

/**
 * Google DriveからCSVファイルを読み込んでインポート
 * @param {string} fileId - DriveファイルID
 * @returns {Object} インポート結果
 */
function importQuestionBankFromDriveFile(fileId) {
  try {
    var file = DriveApp.getFileById(fileId);
    var csvText = file.getBlob().getDataAsString('UTF-8');
    return importQuestionBankFromCsv(csvText);
  } catch (err) {
    Logger.log('importQuestionBankFromDriveFile ERROR: ' + err.message);
    return {
      ok: false,
      error: err.message
    };
  }
}

/**
 * Google Driveフォルダから最新のquestionbank_import.csvを自動インポート
 * @returns {Object} インポート結果
 */
function importQuestionBankFromFolder() {
  try {
    var folder = getOrCreateImportFolder_();
    var files = folder.getFilesByName('questionbank_import.csv');

    if (!files.hasNext()) {
      return {
        ok: false,
        error: 'questionbank_import.csv not found in folder',
        folderUrl: folder.getUrl()
      };
    }

    var file = files.next();
    Logger.log('Found CSV file: ' + file.getName() + ' (ID: ' + file.getId() + ')');

    return importQuestionBankFromDriveFile(file.getId());

  } catch (err) {
    Logger.log('importQuestionBankFromFolder ERROR: ' + err.message);
    return {
      ok: false,
      error: err.message
    };
  }
}

function getOrCreateImportFolder_() {
  var props = PropertiesService.getScriptProperties();
  var folderId = props.getProperty('IMPORT_FOLDER_ID');
  if (folderId) {
    try {
      return DriveApp.getFolderById(folderId);
    } catch (e) {
      props.deleteProperty('IMPORT_FOLDER_ID');
    }
  }

  var folders = DriveApp.getFoldersByName(APP_IMPORT_FOLDER_NAME_);
  if (folders.hasNext()) {
    var existing = folders.next();
    props.setProperty('IMPORT_FOLDER_ID', existing.getId());
    return existing;
  }

  var created = DriveApp.createFolder(APP_IMPORT_FOLDER_NAME_);
  props.setProperty('IMPORT_FOLDER_ID', created.getId());
  return created;
}

/**
 * テスト用: ローカルCSVファイルの内容を直接貼り付けて実行
 * Apps Scriptエディタで実行可能
 */
function testImportQuestionBankFromCsv() {
  // サンプルCSV（最初の3行のみ）
  var sampleCsv = '﻿qId,segmentId,type,difficulty,tag1,tag2,tag3,lawTag,revisionFlag,conceptId,variantGroupId,source_ref,imageUrl,choiceImageUrl,stem,choiceA,choiceB,choiceC,choiceD,choiceE,explainA,explainB,explainC,explainD,explainE,correct,explainShort,explainLong,status,updatedAt\n' +
    'H28takken-001,takken_rights,knowledge,3,権利関係,H28,,,0,,H28takken-001,TAKKEN-SAMPLE,,,"宅建試験の権利関係に関する次の記述のうち最も適切なものはどれか。","民法などの条文と判例を根拠に判断する。","宅建業法だけを見ればよい。","年度別演習は不要である。","権利関係は出題されない。",,,,,,,A,"権利関係は民法や判例を根拠に判断する。","権利関係では条文と判例をセットで確認する。",published,2026-04-11T00:00:00\n' +
    'H28takken-026,takken_business,knowledge,3,宅地建物取引業法等,H28,,,0,,H28takken-026,TAKKEN-SAMPLE,,,"宅地建物取引業法に関する次の記述のうち最も適切なものはどれか。","重要事項説明や37条書面を区別して整理する。","宅建業法は出題数が少ない。","広告規制は対象外である。","免許制度は学習不要である。",,,,,,,A,"宅建業法は手続と書面を区別する。","宅建業法は得点源になりやすいため手続ごとに整理する。",published,2026-04-11T00:00:00';

  Logger.log('Testing CSV import with sample data...');
  var result = importQuestionBankFromCsv(sampleCsv);
  Logger.log('Result: ' + JSON.stringify(result));

  return result;
}

/**
 * 実際のCSVファイル全量をインポートする場合は、この関数を使用
 * CSVテキストを引数として渡す（Apps Scriptエディタでは実行しにくいため、Webエンドポイント経由推奨）
 */
function importFullQuestionBank(csvText) {
  if (!csvText) {
    throw new Error('csvText is required. Use testImportQuestionBankFromCsv() for sample test.');
  }

  Logger.log('Importing full QuestionBank CSV...');
  var result = importQuestionBankFromCsv(csvText);
  Logger.log('Result: ' + JSON.stringify(result));

  return result;
}

/**
 * ファイルIDを指定してインポート
 */
function importByFileId() {
  var fileId = '13tgR5ynk6_s3BcAQY5oUJcoMA9qMBXy6';
  var result = importQuestionBankFromDriveFile(fileId);
  Logger.log('Result: ' + JSON.stringify(result));
  return result;
}
