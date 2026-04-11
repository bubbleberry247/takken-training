// Temporary function to check database status
function checkDatabaseStatus_() {
  var dbId = PropertiesService.getScriptProperties().getProperty('DB_SPREADSHEET_ID');

  if (!dbId) {
    return {
      status: 'not_created',
      message: 'Database has not been created yet. Run setup() first.'
    };
  }

  try {
    var ss = SpreadsheetApp.openById(dbId);
    var sheets = ss.getSheets().map(function(s) { return s.getName(); });

    return {
      status: 'success',
      dbId: dbId,
      dbName: ss.getName(),
      dbUrl: ss.getUrl(),
      sheetCount: sheets.length,
      sheets: sheets
    };
  } catch (e) {
    return {
      status: 'error',
      message: e.toString(),
      dbId: dbId
    };
  }
}

