// TestPlan14にdisplayOrderカラムを追加し、1-14の番号を振るスクリプト

function addDisplayOrderToTestPlan14_() {
  Logger.log('=== TestPlan14にdisplayOrderを追加 ===');

  var sh = getSheet_(SHEETS.TestPlan14);
  var data = sh.getDataRange().getValues();
  var headers = data[0];

  // displayOrderカラムが既に存在するかチェック
  var displayOrderCol = headers.indexOf('displayOrder');

  if (displayOrderCol === -1) {
    // displayOrderカラムを追加（testIndexの次）
    var testIndexCol = headers.indexOf('testIndex');
    sh.insertColumnAfter(testIndexCol + 1);
    sh.getRange(1, testIndexCol + 2).setValue('displayOrder');
    Logger.log('displayOrderカラムを追加しました');
    displayOrderCol = testIndexCol + 1;

    // データを再取得
    data = sh.getDataRange().getValues();
    headers = data[0];
  } else {
    Logger.log('displayOrderカラムは既に存在します');
  }

  var testIndexCol = headers.indexOf('testIndex');

  // 順番にdisplayOrderを設定
  // R7gakkaA→1, R7gakkaB→2, R6gakkaA→3...の順番
  var yearOrder = ['R7', 'R6', 'R5', 'R4', 'R3', 'R2', 'R1'];
  var gakkaOrder = ['gakkaA', 'gakkaB'];

  var displayOrder = 1;
  for (var y = 0; y < yearOrder.length; y++) {
    for (var g = 0; g < gakkaOrder.length; g++) {
      var targetTestIndex = yearOrder[y] + gakkaOrder[g];

      // data内で該当するtestIndexを探す
      for (var i = 1; i < data.length; i++) {
        if (String(data[i][testIndexCol]) === targetTestIndex) {
          sh.getRange(i + 1, displayOrderCol + 1).setValue(displayOrder);
          Logger.log(displayOrder + '. ' + targetTestIndex + ' → displayOrder=' + displayOrder);
          displayOrder++;
          break;
        }
      }
    }
  }

  Logger.log('');
  Logger.log('=== 完了 ===');
  Logger.log('displayOrderを設定しました');
}

