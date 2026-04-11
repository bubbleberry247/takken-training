var APP_NAME_ = 'sekisan-training';
var APP_TITLE_ = '建築積算士 一次試験 過去問演習';
var APP_SHORT_TITLE_ = '建築積算士 一次試験';
var APP_DIAG_KEY_ = 'sekisan2026';
var APP_DB_PREFIX_ = 'SekisanTraining_DB_';
var APP_IMAGE_FOLDER_NAME_ = 'SekisanTraining_QuestionBankImages';
var APP_IMPORT_FOLDER_NAME_ = 'SekisanTraining_Imports';
var SEKISAN_LOCAL_STORAGE_PREFIX_ = 'sekisanTraining_';
var SEKISAN_YEARS_ = ['H25', 'H26', 'H27', 'H28', 'H29', 'H30', 'R1', 'R2', 'R3', 'R4', 'R5', 'R6', 'R7'];
var SEKISAN_MOCK_PARTS_ = ['FULL', 'I', 'II'];
var SEKISAN_GITHUB_IMAGE_BASE_URL_ = 'https://raw.githubusercontent.com/bubbleberry247/sekisan-training/main/images/sekisan/';

function formatSekisanYear_(code) {
  var text = String(code || '').toUpperCase();
  var m = text.match(/^H(\d+)$/);
  if (m) return '平成' + Number(m[1]) + '年';
  m = text.match(/^R(\d+)$/);
  if (m) {
    var yearNum = Number(m[1]);
    return yearNum === 1 ? '令和元年' : '令和' + yearNum + '年';
  }
  return text;
}

function sekisanSectionLabelByNo_(no) {
  var n = Number(no || 0);
  if (n >= 1 && n <= 25) return 'Ⅰ建築一般';
  if (n >= 26 && n <= 50) return 'Ⅱ数量積算';
  return '';
}

function sekisanSectionFromNo_(no) {
  var n = Number(no || 0);
  if (n >= 1 && n <= 25) return 'I';
  if (n >= 26 && n <= 50) return 'II';
  return 'FULL';
}

function sekisanSegmentLabel_(segmentId) {
  var seg = String(segmentId || '').trim();
  if (seg === 'sekisan_I') return 'Ⅰ建築一般';
  if (seg === 'sekisan_II') return 'Ⅱ数量積算';
  return seg;
}

function sekisanMockPartLabel_(part) {
  var p = String(part || 'FULL').toUpperCase();
  if (p === 'I') return 'Ⅰ建築一般';
  if (p === 'II') return 'Ⅱ数量積算';
  return '本試験';
}

function buildSekisanTestIndex_(year, part) {
  var y = String(year || '').toUpperCase();
  var p = String(part || 'FULL').toUpperCase();
  return p === 'FULL' ? y + 'sekisan' : y + 'sekisan_' + p;
}

function parseSekisanQId_(qId) {
  var text = String(qId || '').trim();
  var match = text.match(/^((?:H|R)\d+)sekisan-(\d{3})$/);
  if (!match) return null;
  return {
    qId: text,
    year: match[1],
    number: match[2]
  };
}

function sekisanImageBaseNameFromQId_(qId) {
  var parsed = parseSekisanQId_(qId);
  if (!parsed) return '';
  return 'sekisan_' + parsed.year + '_' + parsed.number;
}

function sekisanQIdFromImageBaseName_(baseName) {
  var text = String(baseName || '').trim().replace(/\.[^.]+$/, '');
  var parsed = text.match(/^sekisan_((?:H|R)\d+)_(\d{3})$/);
  if (parsed) return parsed[1] + 'sekisan-' + parsed[2];
  parsed = text.match(/^((?:H|R)\d+)sekisan_(\d{3})$/);
  if (parsed) return parsed[1] + 'sekisan-' + parsed[2];
  return '';
}

function getSekisanGitHubImageBaseUrl_() {
  var props = PropertiesService.getScriptProperties();
  return props.getProperty('SEKISAN_GITHUB_IMAGE_BASE_URL') || SEKISAN_GITHUB_IMAGE_BASE_URL_;
}
