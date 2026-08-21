import assert from 'node:assert/strict';
import fs from 'node:fs';

const source = fs.readFileSync(new URL('../src/index.html', import.meta.url), 'utf8');
const desktopBlocks = [...source.matchAll(/@media\s*\(min-width:768px\)\s*\{([\s\S]*?)\n\s*\}/g)]
  .map((match) => match[1])
  .join('\n');

assert.match(source, /\.exam-rules-panel h3\{font-size:4\.5vw/, 'mobile rules title remains viewport-responsive');
assert.match(source, /\.exam-rules-list \.rule-line\{[^}]*font-size:3\.3vw/, 'mobile rule lines remain viewport-responsive');
assert.match(source, /\.exam-section-instruction\{[^}]*font-size:3\.2vw/, 'mobile section instruction remains viewport-responsive');

assert.match(desktopBlocks, /\.exam-rules-panel h3\{font-size:20px/, 'desktop rules title uses a bounded font size');
assert.match(desktopBlocks, /\.exam-rules-list \.rule-line\{[^}]*font-size:14px/, 'desktop rule lines use a bounded font size');
assert.match(desktopBlocks, /\.rule-summary\{font-size:15px/, 'desktop summary uses a bounded font size');
assert.match(desktopBlocks, /\.exam-rules-panel \.penalty-info\{[^}]*font-size:13px/, 'desktop penalty note uses a bounded font size');
assert.match(desktopBlocks, /\.exam-rules-panel \.start-btn\{[^}]*font-size:15px/, 'desktop start button uses a bounded font size');
assert.match(desktopBlocks, /\.exam-section-divider\{[^}]*font-size:15px/, 'desktop section divider uses a bounded font size');
assert.match(desktopBlocks, /\.exam-section-instruction\{[^}]*font-size:14px/, 'desktop in-exam instruction uses a bounded font size');

console.log('exam rules responsive contract: mobile scale and bounded desktop sizes passed');
