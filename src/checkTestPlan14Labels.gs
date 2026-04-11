// TestPlan14のlabelフィールドを確認するスクリプト

function checkTestPlan14Labels_() {
  Logger.log('=== TestPlan14 Label確誁E===');

  var sh = getSheet_(SHEETS.TestPlan14);
  var data = sh.getDataRange().getValues();
  var headers = data[0];

  var testIndexCol = headers.indexOf('testIndex');
  var labelCol = headers.indexOf('label');

  Logger.log('総エントリー数: ' + (data.length - 1));
  Logger.log('');

  for (var i = 1; i < data.length; i++) {
    var testIndex = String(data[i][testIndexCol] || '');
    var label = String(data[i][labelCol] || '');

    Logger.log((i) + '. testIndex=' + testIndex + ', label="' + label + '"');
  }

  Logger.log('');
  Logger.log('=== 確認完亁E===');
}

