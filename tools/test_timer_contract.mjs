import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const context = {
  console,
  Utilities: {
    parseDate(value) {
      const parsed = new Date(String(value).replace(' ', 'T') + '+09:00');
      if (Number.isNaN(parsed.getTime())) throw new Error('invalid date');
      return parsed;
    },
  },
};
vm.createContext(context);
vm.runInContext(fs.readFileSync(new URL('../src/logic.gs', import.meta.url), 'utf8'), context);

assert.equal(context.parseDateTime_('', 'Asia/Tokyo'), null);
assert.equal(context.parseDateTime_('not-a-date', 'Asia/Tokyo'), null);
assert.equal(
  context.parseDateTime_('2026-07-28 17:04:46', 'Asia/Tokyo').toISOString(),
  '2026-07-28T08:04:46.000Z',
);
const dateObject = new Date('2026-07-28T08:04:46.000Z');
assert.equal(context.parseDateTime_(dateObject, 'Asia/Tokyo').getTime(), dateObject.getTime());
const now = new Date('2026-07-28T08:04:46.000Z');
assert.equal(context.isAttemptExpired_({ mode: 'test', endsAt: '' }, now, 'Asia/Tokyo'), true);
assert.equal(context.isAttemptExpired_({ mode: 'mock', endsAt: 'invalid' }, now, 'Asia/Tokyo'), true);
assert.equal(context.isAttemptExpired_({ mode: 'field', endsAt: '2026-07-28 18:04:46' }, now, 'Asia/Tokyo'), false);
assert.equal(context.isAttemptExpired_({ mode: 'practice', endsAt: '' }, now, 'Asia/Tokyo'), false);
assert.equal(context.isAttemptExpired_({ mode: 'practice', endsAt: 'invalid' }, now, 'Asia/Tokyo'), true);

const apiSource = fs.readFileSync(new URL('../src/api.gs', import.meta.url), 'utf8');
assert.doesNotMatch(apiSource, /endsAt:\s*String\(existing\.row\.endsAt/);
assert.match(apiSource, /endsAt:\s*formatDateTime_\(endsAt, tz\)/);
assert.doesNotMatch(apiSource, /Boolean\(attempt\.endsAt\) && \(!endsAt \|\| now > endsAt\)/);
assert.match(apiSource, /var expired = isAttemptExpired_\(attempt, now, tz\)/);

console.log('timer contract: 13 assertions passed');
