function debugR3gakkaB_() {
  Logger.log('=== R3gakkaB チE��チE�� ===');

  // QuestionBankからR3gakkaBを検索
  var sh = getSheet_(SHEETS.QuestionBank);
  var data = sh.getDataRange().getValues();
  var headers = data[0];

  var segmentIdCol = headers.indexOf('segmentId');
  var qIdCol = headers.indexOf('qId');

  var r3gakkaBCount = 0;
  var r3gakkaBIds = [];

  for (var i = 1; i < data.length; i++) {
    if (data[i][segmentIdCol] === 'R3gakkaB') {
      r3gakkaBCount++;
      r3gakkaBIds.push(data[i][qIdCol]);
    }
  }

  Logger.log('R3gakkaB問題数: ' + r3gakkaBCount);
  Logger.log('最初�E5件: ' + r3gakkaBIds.slice(0, 5).join(', '));

  // TestPlan14のR3gakkaBエントリーを確誁E
  var testPlanSh = getSheet_(SHEETS.TestPlan14);
  var testPlanData = testPlanSh.getDataRange().getValues();
  var testPlanHeaders = testPlanData[0];

  var testIndexCol = testPlanHeaders.indexOf('testIndex');
  var targetSegmentsCol = testPlanHeaders.indexOf('targetSegments');

  Logger.log('\n=== TestPlan14 R3エントリー ===');
  for (var i = 1; i < testPlanData.length; i++) {
    var testIndex = String(testPlanData[i][testIndexCol] || '');
    if (testIndex.indexOf('R3') === 0) {
      Logger.log('testIndex: ' + testIndex + ', targetSegments: ' + testPlanData[i][targetSegmentsCol]);
    }
  }
}

