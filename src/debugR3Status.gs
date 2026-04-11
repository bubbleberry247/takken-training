function debugR3Status_() {
  Logger.log('=== R3gakkaB status遒ｺ隱・===');

  var sh = getSheet_(SHEETS.QuestionBank);
  var data = sh.getDataRange().getValues();
  var headers = data[0];

  var qIdCol = headers.indexOf('qId');
  var statusCol = headers.indexOf('status');

  var publishedCount = 0;
  var otherStatus = {};

  for (var i = 1; i < data.length; i++) {
    var qId = String(data[i][qIdCol] || '');
    if (qId.indexOf('R3gakkaB') === 0) {
      var status = String(data[i][statusCol] || '');
      if (status === 'published') {
        publishedCount++;
      } else {
        if (!otherStatus[status]) {
          otherStatus[status] = [];
        }
        otherStatus[status].push(qId);
      }
    }
  }

  Logger.log('R3gakkaB published: ' + publishedCount + '莉ｶ');
  Logger.log('縺昴・莉悶・status:');
  for (var s in otherStatus) {
    Logger.log('  ' + s + ': ' + otherStatus[s].length + '莉ｶ');
    if (otherStatus[s].length <= 5) {
      Logger.log('    竊・' + otherStatus[s].join(', '));
    } else {
      Logger.log('    竊・' + otherStatus[s].slice(0, 5).join(', ') + '...');
    }
  }
}

