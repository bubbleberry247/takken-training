import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import { parseCsv, parseCsvObjects } from './csv_test_utils.mjs';

const lf = '\uFEFFid,stem,note\n1,"first\n\nア　item","escaped ""quote"""\n2,plain,end\n';
const crlf = lf.replace(/\n/g, '\r\n');
const bareCr = lf.replace(/\n/g, '\r');
const mixed = '\uFEFFid,stem,note\r\n1,"first\r\n\rア　item","escaped ""quote"""\r2,plain,end\n';
const expected = parseCsv(lf);

for (const [name, fixture] of Object.entries({ lf, crlf, bareCr, mixed })) {
  assert.deepEqual(parseCsv(fixture), expected, `${name} must have LF-normalized CSV semantics`);
  assert.deepEqual(parseCsvObjects(fixture), parseCsvObjects(lf), `${name} object rows differ`);
  const stem = parseCsvObjects(fixture)[0].stem;
  assert.equal(crypto.createHash('sha256').update(stem, 'utf8').digest('hex'),
    crypto.createHash('sha256').update('first\n\nア　item', 'utf8').digest('hex'));
}

assert.throws(() => parseCsv('id,stem\n1,"unclosed'), /unclosed quoted field/);
console.log(JSON.stringify({ ok: true, tests: 13, fixtures: ['lf', 'crlf', 'bare-cr', 'mixed'], quotedMultiline: true }));
