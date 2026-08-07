import fs from 'node:fs';
import path from 'node:path';

const root = path.resolve(import.meta.dirname, '..');
const logic = fs.readFileSync(path.join(root, 'src', 'logic.gs'), 'utf8');
const api = fs.readFileSync(path.join(root, 'src', 'api.gs'), 'utf8');
const html = fs.readFileSync(path.join(root, 'src', 'index.html'), 'utf8');

let passed = 0;
function check(condition, label) {
  if (!condition) throw new Error('FAIL: ' + label);
  passed += 1;
  console.log('PASS:', label);
}

const yearTagPattern = /^(H|R)[0-9]+[A-Z]?(年度)?$/i;
['H28', 'R7', 'R2A', 'R7年度', 'r3b年度'].forEach((tag) => {
  check(yearTagPattern.test(tag), 'year-only tag is recognized: ' + tag);
});
['権利関係', '令和7年度', 'R7-法令', '', 'H'].forEach((tag) => {
  check(!yearTagPattern.test(tag), 'non-year tag is preserved: ' + (tag || '(blank)'));
});

check(logic.includes("function isYearOnlyTag_(tag)"), 'shared year-tag helper exists');
check(logic.includes("userTagRows.filter(function(r){ return !isYearOnlyTag_(r.tag); })"), 'legacy year rows are excluded from weak ranking');
check(logic.includes("if (!isYearOnlyTag_(r.tag)) tagMap[r.tag] = r;"), 'legacy year rows are excluded from field statistics');
check(logic.includes("if (!tag || isYearOnlyTag_(tag)) return;"), 'year tags are not written to TagStats');
check(api.includes("if (tag && !isYearOnlyTag_(tag)) tagSet[tag] = true;"), 'incoming practice year tags are ignored');
check(api.includes("return tag && !isYearOnlyTag_(tag) && tagSet[tag];"), 'question year tags are ignored during practice matching');

const notice = '本サイトの問題は、各年度の出題当時の法令・基準・試験形式に基づいています。現在の法令・基準とは異なる場合があります。';
check((html.match(new RegExp(notice, 'g')) || []).length === 3, 'notice appears exactly on home, exam, and result views');
check(html.includes('.content-version-notice{'), 'notice has shared presentation styling');

console.log(`All ${passed} contract checks passed.`);

