var APP_NAME_ = 'takken-training';
var APP_TITLE_ = '宅地建物取引士（宅建）過去問演習';
var APP_SHORT_TITLE_ = '宅建 過去問演習';
var APP_DIAG_KEY_ = 'takken2026';
var APP_DB_PREFIX_ = 'TakkenTraining_DB_';
var APP_IMAGE_FOLDER_NAME_ = 'TakkenTraining_QuestionBankImages';
var APP_IMPORT_FOLDER_NAME_ = 'TakkenTraining_Imports';
var SEKISAN_LOCAL_STORAGE_PREFIX_ = 'takkenTraining_';
var SEKISAN_YEARS_ = ['H28', 'H29', 'H30', 'R1', 'R2A', 'R2B', 'R3A', 'R3B', 'R4', 'R5', 'R6', 'R7'];
var SEKISAN_MOCK_PARTS_ = ['FULL'];
var SEKISAN_GITHUB_IMAGE_BASE_URL_ = 'https://raw.githubusercontent.com/bubbleberry247/takken-training/main/images/takken/';

function formatSekisanYear_(code) {
  var text = String(code || '').toUpperCase();
  var special = text.match(/^R(\d+)([AB])$/);
  if (special) {
    return '令和' + Number(special[1]) + '年' + (special[2] === 'A' ? '10月試験' : '12月試験');
  }
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
  if (n >= 1 && n <= 14) return '権利関係';
  if (n >= 15 && n <= 22) return '法令上の制限';
  if (n >= 23 && n <= 25) return '税・その他';
  if (n >= 26 && n <= 45) return '宅地建物取引業法等';
  if (n >= 46 && n <= 50) return '税・その他';
  return '';
}

function sekisanSectionFromNo_(no) {
  var n = Number(no || 0);
  if (n >= 1 && n <= 14) return 'RIGHTS';
  if (n >= 15 && n <= 22) return 'LAW';
  if (n >= 23 && n <= 25) return 'OTHER';
  if (n >= 26 && n <= 45) return 'BUSINESS';
  if (n >= 46 && n <= 50) return 'OTHER';
  return 'FULL';
}

function sekisanSegmentLabel_(segmentId) {
  var seg = String(segmentId || '').trim();
  if (seg === 'takken_rights') return '権利関係';
  if (seg === 'takken_law') return '法令上の制限';
  if (seg === 'takken_business') return '宅地建物取引業法等';
  if (seg === 'takken_other') return '税・その他';
  return seg;
}

function sekisanMockPartLabel_(part) {
  var p = String(part || 'FULL').toUpperCase();
  if (p === 'RIGHTS') return '権利関係';
  if (p === 'LAW') return '法令上の制限';
  if (p === 'BUSINESS') return '宅地建物取引業法等';
  if (p === 'OTHER') return '税・その他';
  return '本試験（50問）';
}

function buildSekisanTestIndex_(year, part) {
  var y = String(year || '').toUpperCase();
  var p = String(part || 'FULL').toUpperCase();
  return p === 'FULL' ? y + 'takken' : y + 'takken_' + p;
}

function parseSekisanQId_(qId) {
  var text = String(qId || '').trim();
  var match = text.match(/^((?:H|R)\d+[A-Z]?)(?:takken|sekisan)-(\d{3})$/i);
  if (!match) return null;
  return {
    qId: text,
    year: match[1].toUpperCase(),
    number: match[2]
  };
}

function sekisanImageBaseNameFromQId_(qId) {
  var parsed = parseSekisanQId_(qId);
  if (!parsed) return '';
  return 'takken_' + parsed.year + '_' + parsed.number;
}

function sekisanQIdFromImageBaseName_(baseName) {
  var text = String(baseName || '').trim().replace(/\.[^.]+$/, '');
  var parsed = text.match(/^takken_((?:H|R)\d+[A-Z]?)_(\d{3})$/i);
  if (parsed) return parsed[1].toUpperCase() + 'takken-' + parsed[2];
  parsed = text.match(/^((?:H|R)\d+[A-Z]?)takken_(\d{3})$/i);
  if (parsed) return parsed[1].toUpperCase() + 'takken-' + parsed[2];
  return '';
}

function getSekisanGitHubImageBaseUrl_() {
  var props = PropertiesService.getScriptProperties();
  return props.getProperty('TAKKEN_GITHUB_IMAGE_BASE_URL') ||
    props.getProperty('SEKISAN_GITHUB_IMAGE_BASE_URL') ||
    SEKISAN_GITHUB_IMAGE_BASE_URL_;
}
