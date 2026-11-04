import { fmt, scopeName, type Item, type Field } from './data';

const one = (f?: Field) => (f && f.value !== undefined ? String(f.value) : '');

export function lead(i: Item, f: Record<string, Field>): string {
  const d = fmt(i.list_date);
  const where = scopeName(i.scope).name;
  const last = one(f.last_date);
  switch (i.type) {
    case 'job':
      return `${i.org} has published a recruitment notice titled "${i.title}" on its official website${d ? ` on ${d}` : ''}.${last ? ` The last date to apply read from the notification is ${fmt(last)}.` : ' Check the official notification for the full eligibility, dates and fee before applying.'} ${i.scope === 'central' ? 'Central government posts are generally open to eligible candidates from all states.' : `This is a ${where} recruitment; check the notification for domicile rules.`} This page lists the key details and the official link.`;
    case 'admit':
      return `${i.org} has released "${i.title}"${d ? ` on ${d}` : ''}. Candidates can download the admit card or hall ticket from the official website using their registration number and date of birth or password. Check the exam date, reporting time and exam centre printed on it carefully.`;
    case 'result':
      return `${i.org} has declared "${i.title}"${d ? ` on ${d}` : ''}. Candidates can check the result, merit list or cut off on the official website. Keep your roll number or registration number ready.`;
    case 'answer':
      return `${i.org} has published "${i.title}"${d ? ` on ${d}` : ''}. Candidates can match their responses with the official answer key and, if the commission allows, submit objections within the window given in the notice.`;
    case 'syllabus':
      return `${i.org} has published "${i.title}"${d ? ` on ${d}` : ''}. The official syllabus and exam pattern explain the subjects, marks and stages of the exam.`;
    case 'admission':
      return `${i.org} has published "${i.title}"${d ? ` on ${d}` : ''}. Read the official notice for eligibility, important dates and the application process.`;
    default:
      return `${i.org} has published a notice titled "${i.title}"${d ? ` on ${d}` : ''}. Read the official notice for full details.`;
  }
}

export function steps(i: Item, deep: boolean, host: string): string[] {
  const open = deep ? `Click the official link button on this page. It opens the notice or page directly on ${host}.` : `Open the official website ${host} using the button on this page.`;
  const find = deep ? '' : `On the home page, look for the latest notices, "What's New" or recruitment section and find "${i.title}".`;
  const base = [open, find].filter(Boolean);
  switch (i.type) {
    case 'admit':
      return [...base, 'Enter your registration number or application number and date of birth or password.', 'Download the admit card and check your name, photo, exam date, time and centre.', 'Take a clear printout and carry it with a valid photo ID to the exam centre.'];
    case 'result':
      return [...base, 'Open the result PDF or enter your roll number on the result page.', 'Search your roll number in the PDF using Ctrl+F or the find option on mobile.', 'Download and save the result. Note any cut off marks and the next stage dates.'];
    case 'answer':
      return [...base, 'Open the answer key PDF or log in to the response sheet page.', 'Match each answer with your response sheet and count your expected marks.', 'If you find an error, submit an objection only through the official portal before the deadline.'];
    case 'job':
      return [...base, 'Read the full notification: eligibility, age limit, fee, selection process and important dates.', 'Apply only through the official online form linked in the notification and pay the fee only on the official portal.', 'Save the final submitted form and fee receipt for later stages.'];
    default:
      return [...base, 'Open and read the notice carefully, including any dates it mentions.', 'Save a copy of the notice for your records.'];
  }
}

export function feeText(f?: Field): string {
  if (!f || !f.values || !f.values.length) return '';
  const v = f.values;
  if (v.length === 1) return v[0] === 0 ? 'No fee' : `₹${v[0]}`;
  return `₹${Math.min(...v)} to ₹${Math.max(...v)} (depends on category)`;
}

export function ageText(f?: Field): string {
  if (!f) return '';
  if (f.min && f.max) return `${f.min} to ${f.max} years`;
  if (f.max) return `Up to ${f.max} years`;
  return '';
}

export function metaDesc(i: Item, f: Record<string, Field>): string {
  const d = fmt(i.list_date);
  const last = one(f.last_date);
  const t = i.title.length > 150 ? i.title.slice(0, 147) + '...' : i.title;
  const kind = { job: 'recruitment notice', admit: 'admit card', result: 'result', answer: 'answer key', syllabus: 'syllabus', admission: 'admission notice', notice: 'notice' }[i.type];
  return `${i.short} ${kind}: ${t}.${d ? ` Dated ${d}.` : ''}${last ? ` Last date ${fmt(last)}.` : ''} Official link, key dates and how to download.`;
}

export function jobTitle(i: Item): string | null {
  const raw = i.title;
  if (/corrigendum|addendum|extension|extended|revised|cancel|postpone|result|admit|answer|interview|merit|syllabus|schedule/i.test(raw)) return null;
  if (/various|multiple|different|several|विभिन्न/i.test(raw)) return null;
  let t = raw
    .replace(/\(.*?\)/g, ' ')
    .replace(/\b(advt|advertisement|notification|notice|recruitment|online\s+form|apply\s+online|vacancy|vacancies|post\s+of|posts\s+of|for\s+the|no\.?|cen|crp)\b/gi, ' ')
    .replace(/\b\d{1,4}\s*\/\s*\d{2,4}\b/g, ' ')
    .replace(/\b20\d{2}(\s*-\s*\d{2,4})?\b/g, ' ')
    .replace(/[:;,|–—_]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
  if (t.toLowerCase().startsWith(i.short.toLowerCase() + ' ')) t = t.slice(i.short.length).trim();
  t = t.replace(/^[-.\s]+|[-.\s]+$/g, '');
  if (t.length < 4 || !/[a-z]/i.test(t)) return null;
  return t.slice(0, 100);
}
