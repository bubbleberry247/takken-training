import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import { parseCsvObjects } from './csv_test_utils.mjs';

const source = fs.readFileSync(new URL('../src/index.html', import.meta.url), 'utf8');

function extractFunction(name) {
  const start = source.indexOf(`function ${name}(`);
  assert.notEqual(start, -1, `${name} must remain defined in index.html`);
  const open = source.indexOf('{', start);
  let depth = 0;
  for (let i = open; i < source.length; i += 1) {
    if (source[i] === '{') depth += 1;
    if (source[i] === '}') {
      depth -= 1;
      if (depth === 0) return source.slice(start, i + 1);
    }
  }
  throw new Error(`Could not extract ${name}`);
}

const context = {};
vm.createContext(context);
vm.runInContext([
  extractFunction('escapeHtml'),
  extractFunction('hasStatementListMarkers_'),
  extractFunction('isCountQuestionStem_'),
  extractFunction('isCombinationQuestionStem_'),
  extractFunction('hasUnlabelledCountStatements_'),
  extractFunction('hasUnlabelledCombinationStatements_'),
  extractFunction('getStatementPromptMatch_'),
  extractFunction('isOpeningStatementBracket_'),
  extractFunction('isClosingStatementBracket_'),
  extractFunction('insertSafeStatementBreaks_'),
  extractFunction('shouldFormatStatementBreaks_'),
  extractFunction('formatStatementBreaks_'),
  extractFunction('formatCaseBreaks_'),
  extractFunction('formatChoiceText_'),
  extractFunction('fmtStem'),
  extractFunction('boldMarkers'),
].join('\n'), context);

const fmtStem = context.fmtStem;

const csv = fs.readFileSync(new URL('../data/takken_all_final.csv', import.meta.url), 'utf8');
const rows = parseCsvObjects(csv);
const countRows = rows.filter((row) => /(いくつあるか|何個あるか|何人いるか)/.test(row.stem));
const combinationRows = rows.filter((row) =>
  /(?:組合せ|組み合わせ)[^。！？\n]{0,100}(?:どれか|1から4)/.test(row.stem) ||
  /(?:全て|すべて)掲げた/.test(row.stem),
);
const rowById = new Map(rows.map((row) => [row.qId, row]));

assert.equal(rows.length, 600, 'canonical inventory must contain 600 questions');
assert.equal(countRows.length, 70, 'all 70 count questions must be inventoried');
assert.equal(combinationRows.length, 12, 'all 12 combination questions must be inventoried');
assert.equal(
  countRows.filter((row) => combinationRows.some((combo) => combo.qId === row.qId)).length,
  0,
  'count and combination inventories must not overlap',
);

for (const row of countRows) {
  assert.equal(context.shouldFormatStatementBreaks_(row.stem), true, `${row.qId} must be display-formatted`);
  assert.match(fmtStem(row.stem, row.qId), /<br>/, `${row.qId} must render at least one display break`);
}

// R6-040 keeps its combination statements in the answer choices, not the stem.
// All other combination stems have a display-level break without changing CSV.
for (const row of combinationRows) {
  if (row.qId === 'R6takken-040') continue;
  assert.equal(context.shouldFormatStatementBreaks_(row.stem), true, `${row.qId} must be display-formatted`);
  assert.match(fmtStem(row.stem, row.qId), /<br>/, `${row.qId} must render at least one display break`);
}

const focusedRegressions = [
  ['R7takken-003', /か。<br>ア　/],
  ['R5takken-028', /か。<br>1\. /],
  ['R7takken-034', /か。<br>1\. /],
  ['R5takken-004', /ものとする。<br>ア /],
  ['R7takken-005', /どれか。<br>ア /],
  ['R7takken-026', /なお、代理、媒介に当たり、広告の依頼は行われていないものとする。<br>ア /],
  ['R4takken-007', /について、<br>（ア）/],
];
for (const [qId, expected] of focusedRegressions) {
  assert.ok(rowById.has(qId), `${qId} must remain in the canonical inventory`);
  assert.match(fmtStem(rowById.get(qId).stem, qId), expected, `${qId} focused display regression`);
}
const repeatedStartLegacy = fmtStem(rowById.get('R2atakken-040').stem, 'R2atakken-040');
const repeatedStart = 'Bが喫茶店で当該宅地の買受けの申込みをした場合において、';
const repeatedLines = repeatedStartLegacy.split('<br>');
assert.equal(repeatedLines.length, 5, 'R2atakken-040 should render prompt plus four item lines');
assert.deepEqual(
  repeatedLines.slice(1, 4).map((line) => line.includes(repeatedStart)),
  [true, true, true],
  'R2atakken-040 first three item lines should retain their repeated source label',
);
assert.equal(repeatedLines[3].endsWith('したとき'), true, 'R2atakken-040 third item should end at the source boundary');
assert.equal(
  repeatedLines[4].replace(/^[ア-エ]\u3000/, '').startsWith('Aの事務所ではないがAが継続的に'),
  true,
  'R2atakken-040 fourth item should begin on its own display line',
);
assert.equal(repeatedLines.reduce((total, line) => total + line.split(repeatedStart).length - 1, 0), 3);
const punctuationlessLegacy = fmtStem(rowById.get('R3btakken-042').stem, 'R3btakken-042');
assert.match(punctuationlessLegacy, /目的<br>イ　設計図書/);
assert.match(punctuationlessLegacy, /状況<br>ウ　契約の解除/);
assert.match(punctuationlessLegacy, /内容<br>エ　天災その他/);
const punctuationlessLines = punctuationlessLegacy.split('<br>');
const punctuationlessStarts = ['ア　借賃以外の金銭', 'イ　設計図書、点検記録', 'ウ　契約の解除に関する', 'エ　天災その他不可抗力'];
assert.equal(punctuationlessLines.length, 5, 'R3btakken-042 should render prompt and four labelled item lines');
assert.deepEqual(
  punctuationlessStarts.map((start) => punctuationlessLines.findIndex((line) => line.includes(start))),
  [1, 2, 3, 4],
);

const labelledCountStem = [
  '意思表示に関する次の記述のうち、民法の規定によれば、誤っているものはいくつあるか。',
  '',
  'ア　表意者の意思表示に関する記述。',
  'イ　相手方と通じてした虚偽の意思表示に関する記述。',
  'ウ　錯誤に関する記述。',
  'エ　詐欺に関する記述。',
].join('\n');

const labelledHtml = fmtStem(labelledCountStem);
assert.match(labelledHtml, /か。<br>ア　表意者/);
assert.match(labelledHtml, /記述。<br>イ　相手方/);
assert.match(labelledHtml, /記述。<br>ウ　錯誤/);
assert.match(labelledHtml, /記述。<br>エ　詐欺/);
assert.equal(labelledHtml.includes('\n'), false, 'display HTML should contain <br>, not raw newlines');

const slashSeparated = '次の記述のうち、誤っているものはいくつあるか。//ア　第一の記述。//イ　第二の記述。//ウ　第三の記述。';
const slashHtml = fmtStem(slashSeparated);
assert.match(slashHtml, /か。<br>ア　第一/);
assert.match(slashHtml, /記述。<br>イ　第二/);
assert.match(slashHtml, /記述。<br>ウ　第三/);
assert.equal(slashHtml.includes('//'), false, 'presentation-only separators must not leak into the rendered text');

const xssHtml = fmtStem('次の記述はいくつあるか。\nア　<img src=x onerror=alert(1)>');
assert.match(xssHtml, /<br>ア　&lt;img src=x onerror=alert\(1\)&gt;/);
assert.equal(xssHtml.includes('<img'), false, 'statement formatting must happen before HTML escaping');

const ordinary = fmtStem('アメリカについての説明。\nこの文章はいくつあるか。');
assert.equal(ordinary.includes('<br>アメリカ'), false, 'ア in a word must not be treated as an item label');

const ordinaryLabel = fmtStem('次の記述。\nア　これは通常問題の本文です。');
assert.equal(ordinaryLabel.includes('<br>ア　'), false, 'non-count questions must keep the existing formatting policy');

const ordinaryCountSource = '会場にいる人数はいくつあるか。確認方法を説明する。';
const ordinaryCount = fmtStem(ordinaryCountSource);
assert.equal(context.shouldFormatStatementBreaks_(ordinaryCountSource), false, 'ordinary count wording without a statement list stays unchanged');
assert.equal(ordinaryCount.includes('<br>'), false, 'ordinary count wording must not acquire a display break');

const caseStemSource = '令和8年7月1日に下記ケースに関する次の記述のうち、正しいものはどれか。（ケース①）個人Aが金融機関Bから借入れをした場合（ケース②）個人Aが建物賃貸借契約を締結した場合';
const caseStem = fmtStem(caseStemSource, 'R2atakken-002');
assert.match(caseStem, /どれか。<br>（ケース①）/);
assert.match(caseStem, /場合<br>（ケース②）/);
assert.equal(caseStem.includes('\n'), false, 'case formatting must emit HTML breaks');
const otherCaseStem = fmtStem(caseStemSource, 'futuretakken-001');
assert.equal(otherCaseStem.includes('<br>（ケース①）'), false, 'same case label on another qId must remain unchanged');
assert.equal(otherCaseStem.includes('<br>（ケース②）'), false, 'second case label on another qId must remain unchanged');
const unidentifiedCaseStem = fmtStem(caseStemSource);
assert.equal(unidentifiedCaseStem.includes('<br>'), false, 'missing qId must not authorize the targeted repair');

const multiItemQuestion = { qId: 'R6takken-040' };
const multiItemChoice = context.formatChoiceText_(multiItemQuestion, 'ア 当該建物に係る租税その他の公課の負担、イ 敷金や共益費など借賃以外の金銭の授受に関する定めがあるときは、その額並びに当該金銭の授受の時期及び目的');
assert.match(multiItemChoice, /^ア 当該建物に係る租税その他の公課の負担、<br>イ 敷金/);
assert.equal((multiItemChoice.match(/<br>/g) || []).length, 1, 'R6takken-040 choice A has one safe item boundary');
const ordinaryChoice = context.formatChoiceText_({ qId: 'R5takken-028' }, 'ア 第一の記述、イ 第二の記述');
assert.equal(ordinaryChoice.includes('<br>'), false, 'ordinary legal choices must not be split by the targeted rule');

const bracketedStatement = fmtStem('導入（説明。内部）。次の記述のうち、正しいものはいくつあるか。第一（例。説明）項目。第二項目。第三項目。');
assert.equal(bracketedStatement.includes('説明。<br>内部'), false, 'parenthetical punctuation must not split');
assert.equal(bracketedStatement.includes('導入（説明。内部）。次の記述'), true, 'introductory text must remain intact');
assert.match(bracketedStatement, /第一（例。説明）項目。<br>第二項目。<br>第三項目。/);

const numberedCount = fmtStem('次の記述のうち、正しいものはいくつあるか。1. 第一の記述。2. 第二の記述。3. 第三の記述。4. 第四の記述。');
assert.match(numberedCount, /か。<br>1\. 第一/);
assert.match(numberedCount, /記述。<br>2\. 第二/);
assert.match(numberedCount, /記述。<br>3\. 第三/);
assert.match(numberedCount, /記述。<br>4\. 第四/);

const parenthesizedCombination = fmtStem('次の組合せのうち正しいものはどれか。 （ア）第一の記述。（イ）第二の記述。（ウ）第三の記述。（エ）第四の記述。');
assert.match(parenthesizedCombination, /か。<br>（ア）第一/);
assert.match(parenthesizedCombination, /記述。<br>（イ）第二/);
assert.match(parenthesizedCombination, /記述。<br>（ウ）第三/);
assert.match(parenthesizedCombination, /記述。<br>（エ）第四/);

const malformedLegacyCount = fmtStem('次の記述のうち、正しいものはいくつあるか。借賃以外の金銭の授受に関する定めがあるときは、その額並びに当該金銭の授受の時期及び目的設計図書、点検記録その他の保存の状況契約の解除に関する定めがあるときは、その内容天災その他不可抗力による損害の負担に関する定めがあるときは、その内容');
assert.match(malformedLegacyCount, /目的<br>設計図書/);
assert.match(malformedLegacyCount, /状況<br>契約の解除/);
assert.match(malformedLegacyCount, /内容<br>天災その他/);

const combinationChoiceOnly = '宅地建物取引業法の規定によれば、正しいものの組合せとして正しいものは次の1から4のうちどれか。';
assert.equal(context.shouldFormatStatementBreaks_(combinationChoiceOnly), false, 'choice-only combination stems remain unchanged');

const existingFormatting = fmtStem('本文。\n・箇条書き\n1数字項目');
assert.match(existingFormatting, /本文。<br>・箇条書き<br>1．数字項目/);

console.log(`stem formatting: inventory=${rows.length}, count=${countRows.length}, combination=${combinationRows.length}`);
