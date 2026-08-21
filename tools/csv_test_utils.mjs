// Small RFC 4180-compatible parser for local test fixtures. Git may rewrite
// text-file line endings on checkout, so CRLF/CR are normalized to LF both at
// record boundaries and inside quoted multiline fields.
export function parseCsv(text) {
  const rows = [];
  let row = [];
  let field = '';
  let quoted = false;

  const finishField = () => { row.push(field); field = ''; };
  const finishRow = () => { finishField(); rows.push(row); row = []; };

  for (let index = 0; index < text.length; index += 1) {
    const ch = text[index];
    if (quoted) {
      if (ch === '"') {
        if (text[index + 1] === '"') { field += '"'; index += 1; }
        else quoted = false;
      } else if (ch === '\r') {
        if (text[index + 1] === '\n') index += 1;
        field += '\n';
      } else {
        field += ch;
      }
    } else if (ch === '"') {
      quoted = true;
    } else if (ch === ',') {
      finishField();
    } else if (ch === '\r') {
      if (text[index + 1] === '\n') index += 1;
      finishRow();
    } else if (ch === '\n') {
      finishRow();
    } else {
      field += ch;
    }
  }
  if (quoted) throw new Error('CSV contains an unclosed quoted field');
  if (field !== '' || row.length > 0) finishRow();
  if (!rows.length) return { headers: [], rows: [] };
  const headers = rows.shift().map((header, index) =>
    (index === 0 ? header.replace(/^\uFEFF/, '') : header));
  return { headers, rows: rows.filter((values) => values.length > 1 || values[0]) };
}

export function parseCsvObjects(text) {
  const parsed = parseCsv(text);
  return parsed.rows.map((values) =>
    Object.fromEntries(parsed.headers.map((header, index) => [header, values[index] ?? ''])));
}
