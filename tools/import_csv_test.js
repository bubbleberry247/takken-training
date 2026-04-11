/**
 * CSVインポートのテストスクリプト
 *
 * 使用方法:
 * 1. ローカルCSVをGoogle Driveにアップロード
 * 2. importQuestionBankFromDriveFile(fileId) を実行
 *
 * または:
 * 1. Apps Scriptエディタで testImportFromLocalCsv() を実行
 * 2. CSVテキストを直接貼り付け
 */

// Deploy URL
const DEPLOY_URL = 'https://script.google.com/macros/s/AKfycbx9f7KnJ5WMuH3T3AWrewGaU14V5k8xn4uelGlxB9YFZyOL-So2IcF_D7J5jmggk-vYdg/exec';

/**
 * POSTリクエストでCSVテキストをインポート
 */
async function importCsvViaPost(csvText) {
  const response = await fetch(DEPLOY_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      action: 'importCsvText',
      csvText: csvText
    })
  });

  const result = await response.json();
  console.log('Import result:', result);
  return result;
}

/**
 * GETリクエストでフォルダURLを取得
 */
async function getImportFolderUrl() {
  const response = await fetch(`${DEPLOY_URL}?action=getImportFolderUrl`);
  const result = await response.json();
  console.log('Folder URL:', result);
  return result;
}

/**
 * GETリクエストでフォルダからCSVをインポート
 */
async function importCsvFromFolder() {
  const response = await fetch(`${DEPLOY_URL}?action=importCsvFromFolder`);
  const result = await response.json();
  console.log('Import from folder result:', result);
  return result;
}

// Node.js環境でテスト実行
if (typeof require !== 'undefined' && require.main === module) {
  const fs = require('fs');
  const path = require('path');

  const csvPath = path.join(__dirname, 'questionbank_drive_import.csv');
  const csvText = fs.readFileSync(csvPath, 'utf-8');

  console.log(`CSV file loaded: ${csvPath}`);
  console.log(`CSV size: ${csvText.length} bytes`);
  console.log(`CSV lines: ${csvText.split('\n').length}`);

  // ブラウザでコピペ用のテキストを出力
  console.log('\n--- Copy the following CSV text to test in Apps Script Editor ---\n');
  console.log(csvText.substring(0, 500) + '...');
  console.log('\n--- End of sample ---\n');

  // POSTリクエストでインポート（コメントアウト：実際に実行する場合は有効化）
  // importCsvViaPost(csvText);
}

module.exports = {
  importCsvViaPost,
  getImportFolderUrl,
  importCsvFromFolder
};
