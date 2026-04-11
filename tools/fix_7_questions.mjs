import { readFileSync, writeFileSync } from 'fs';
import { execSync } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const CSV_PATH = join(__dirname, 'questionbank_drive_import.csv');

// Step 0: Restore original from git to avoid corrupted state
try {
  execSync('git checkout HEAD -- tools/questionbank_drive_import.csv', {
    cwd: join(__dirname, '..'),
    encoding: 'utf8'
  });
  console.log('Restored original CSV from git HEAD');
} catch (e) {
  console.log('Warning: could not restore from git, using current file');
}

// Split CSV text into lines, respecting quoted fields that may contain newlines
function parseCSV(text) {
  const lines = [];
  let current = '';
  let inQuotes = false;

  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    if (ch === '"') {
      inQuotes = !inQuotes;
      current += ch;  // preserve quotes in line content
    } else if (ch === '\n' && !inQuotes) {
      if (current.endsWith('\r')) current = current.slice(0, -1);
      lines.push(current);
      current = '';
    } else {
      current += ch;
    }
  }
  if (current.trim()) lines.push(current);
  return lines;
}

function splitCSVLine(line) {
  const fields = [];
  let current = '';
  let inQuotes = false;

  for (let i = 0; i < line.length; i++) {
    const ch = line[i];
    if (ch === '"') {
      if (inQuotes && line[i + 1] === '"') {
        current += '"';
        i++;
      } else {
        inQuotes = !inQuotes;
      }
    } else if (ch === ',' && !inQuotes) {
      fields.push(current);
      current = '';
    } else {
      current += ch;
    }
  }
  fields.push(current);
  return fields;
}

function quoteField(val) {
  if (val.includes(',') || val.includes('"') || val.includes('\n') || val.includes('\r')) {
    return '"' + val.replace(/"/g, '""') + '"';
  }
  return val;
}

// Read file (UTF-8-sig: strip BOM)
let raw = readFileSync(CSV_PATH, 'utf8');
if (raw.charCodeAt(0) === 0xFEFF) raw = raw.slice(1);

const lines = parseCSV(raw);
const headerLine = lines[0];
const headers = splitCSVLine(headerLine);

const changes = [];

for (let i = 1; i < lines.length; i++) {
  const fields = splitCSVLine(lines[i]);
  const row = {};
  headers.forEach((h, idx) => row[h] = fields[idx] || '');

  const qid = row.qId;
  let modified = false;

  // Fix 1: R1gakkaB-017
  if (qid === 'R1gakkaB-017') {
    if (row.choiceB && row.choiceB.startsWith('回の降雨量')) {
      row.choiceB = '1' + row.choiceB;
      changes.push(`${qid}: choiceB prepended '1'`);
      modified = true;
    }
    if (row.choiceC && row.choiceC.startsWith('回の降雪量')) {
      row.choiceC = '1' + row.choiceC;
      changes.push(`${qid}: choiceC prepended '1'`);
      modified = true;
    }
    if (row.choiceD && row.choiceD.includes('震度階級以上')) {
      row.choiceD = row.choiceD.replace('震度階級以上の地震', '中震以上（震度4以上）の地震');
      changes.push(`${qid}: choiceD fixed → '${row.choiceD}'`);
      modified = true;
    }
  }

  // Fix 2: R1gakkaB-023
  if (qid === 'R1gakkaB-023') {
    if (row.choiceA && row.choiceA.includes('年以内ごとに回') && !row.choiceA.includes('1年以内ごとに1回')) {
      row.choiceA = row.choiceA.replace('年以内ごとに回', '1年以内ごとに1回');
      changes.push(`${qid}: choiceA fixed`);
      modified = true;
    }
    if (row.choiceB) {
      let b = row.choiceB;
      const origB = b;
      if (b.includes('除き週間当たり')) b = b.replace('除き週間当たり', '除き1週間当たり');
      // Match "時間が月" followed by optional whitespace then "当たり"
      b = b.replace(/時間が月(\s*)当たり/g, '時間が1月$1当たり');
      if (b !== origB) {
        row.choiceB = b;
        changes.push(`${qid}: choiceB fixed`);
        modified = true;
      }
    }
  }

  // Fix 3: R6gakkaB-021
  if (qid === 'R6gakkaB-021') {
    const newA = '\uff08\u30a4\uff09\u5206\u6563\u5316\uff08\u30ed\uff09\u5e02\u8ca9\u54c1\uff08\u30cf\uff09\u7d0d\u671f\uff08\u30cb\uff09\u90e8\u5206\u7684';
    if (row.choiceA !== newA) {
      changes.push(`${qid}: choiceA fixed from garbled text`);
      row.choiceA = newA;
      modified = true;
    }
  }

  // Fix 5: R4gakkaA-047
  if (qid === 'R4gakkaA-047') {
    const correct = row.correct;
    for (const lb of ['A', 'B', 'C', 'D']) {
      const key = `explain${lb}`;
      const val = row[key];
      if (!val) continue;
      if (['\u9069\u5f53\u3067\u3059', '\u4e0d\u9069\u5f53\u3067\u3059', '\u6b63\u3057\u3044', '\u8aa4\u308a'].some(p => val.startsWith(p))) continue;
      row[key] = (lb === correct ? '\u9069\u5f53\u3067\u3059\u3002' : '\u4e0d\u9069\u5f53\u3067\u3059\u3002') + val;
      changes.push(`${qid}: ${key} labeled`);
      modified = true;
    }
  }

  // Fix 6: R4gakkaA-051
  if (qid === 'R4gakkaA-051') {
    const correct = row.correct;
    for (const lb of ['A', 'B', 'C', 'D']) {
      const key = `explain${lb}`;
      const val = row[key];
      if (!val) continue;
      if (['\u9069\u5f53\u3067\u3059', '\u4e0d\u9069\u5f53\u3067\u3059', '\u6b63\u3057\u3044', '\u8aa4\u308a'].some(p => val.startsWith(p))) continue;
      row[key] = (lb === correct ? '\u8aa4\u308a\u3067\u3059\u3002' : '\u6b63\u3057\u3044\u3067\u3059\u3002') + val;
      changes.push(`${qid}: ${key} labeled`);
      modified = true;
    }
  }

  // Fix 7: R4gakkaA-052
  if (qid === 'R4gakkaA-052') {
    const correct = row.correct;
    for (const lb of ['A', 'B', 'C', 'D']) {
      const key = `explain${lb}`;
      const val = row[key];
      if (!val) continue;
      if (['\u9069\u5f53\u3067\u3059', '\u4e0d\u9069\u5f53\u3067\u3059', '\u6b63\u3057\u3044', '\u8aa4\u308a'].some(p => val.startsWith(p))) continue;
      row[key] = (lb === correct ? '\u6b63\u3057\u3044\u3067\u3059\u3002' : '\u8aa4\u308a\u3067\u3059\u3002') + val;
      changes.push(`${qid}: ${key} labeled`);
      modified = true;
    }
  }

  // Always rebuild every line to preserve proper quoting
  const newFields = headers.map(h => quoteField(row[h] || ''));
  lines[i] = newFields.join(',');
}

// Write back with BOM + LF (matching original format)
const output = '\uFEFF' + lines.join('\n') + '\n';
writeFileSync(CSV_PATH, output, 'utf8');

console.log(`\n=== ${changes.length} changes applied ===`);
changes.forEach(c => console.log(`  ${c}`));
console.log(`\nSaved to: ${CSV_PATH}`);
