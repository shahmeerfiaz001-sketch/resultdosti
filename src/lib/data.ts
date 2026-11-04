import { readFileSync, existsSync } from 'node:fs';
import { resolve } from 'node:path';
import site from '../../site.config.json';
import { indexable, hubCounts } from './indexable.mjs';

export type Field = { value?: string | number; values?: number[]; min?: number | null; max?: number | null; confidence?: string };
export type Item = {
  id: string;
  source: string;
  org: string;
  short: string;
  scope: string;
  title: string;
  url: string;
  is_doc: boolean;
  type: 'job' | 'admit' | 'result' | 'answer' | 'syllabus' | 'admission' | 'notice';
  list_date: string | null;
  first_seen: string;
  last_seen: string;
  advt: string | null;
  link_policy: string;
  official_home: string;
  slug: string;
  details: { fields: Record<string, Field>; parsed_at?: string | null } | null;
  tier: number;
  status?: string;
  last_date?: string;
  group?: string;
};
export type Exam = { key: string; source: string; short: string; org: string; scope: string; items: string[]; year: number | null; name: string; slug: string; types: string[]; latest: string };

const root = resolve(process.cwd(), 'data');

function readJson<T>(name: string, fallback: T): T {
  const p = resolve(root, name);
  if (!existsSync(p)) return fallback;
  try {
    return JSON.parse(readFileSync(p, 'utf8')) as T;
  } catch {
    return fallback;
  }
}

let cache: { items: Item[]; exams: Exam[]; updated: string | null } | null = null;

export function load() {
  if (cache) return cache;
  const db = readJson<{ updated: string | null; items: Item[] }>('items.json', { updated: null, items: [] });
  const ex = readJson<{ exams: Exam[] }>('exams.json', { exams: [] });
  const items = db.items.slice().sort((a, b) => dateKey(b).localeCompare(dateKey(a)) || b.first_seen.localeCompare(a.first_seen));
  cache = { items, exams: ex.exams, updated: db.updated };
  return cache;
}

export function dateKey(i: Item): string {
  return i.list_date || i.first_seen.slice(0, 10);
}

export const TYPES: Record<string, { en: string; hi: string; path: string; list: string; listHi: string; color: string; short: string }> = {
  job: { en: 'Latest Jobs', hi: 'नई भर्ती', path: site.paths.job, list: 'Latest Govt Jobs', listHi: 'नई सरकारी नौकरी', color: 'var(--c-job)', short: 'Job' },
  admit: { en: 'Admit Card', hi: 'एडमिट कार्ड', path: site.paths.admit, list: 'Admit Card', listHi: 'एडमिट कार्ड', color: 'var(--c-admit)', short: 'Admit Card' },
  result: { en: 'Result', hi: 'रिजल्ट', path: site.paths.result, list: 'Sarkari Result', listHi: 'सरकारी रिजल्ट', color: 'var(--c-result)', short: 'Result' },
  answer: { en: 'Answer Key', hi: 'आंसर की', path: site.paths.answer, list: 'Answer Key', listHi: 'आंसर की', color: 'var(--c-answer)', short: 'Answer Key' },
  syllabus: { en: 'Syllabus', hi: 'सिलेबस', path: site.paths.syllabus, list: 'Syllabus', listHi: 'सिलेबस', color: 'var(--c-notice)', short: 'Syllabus' },
  admission: { en: 'Admission', hi: 'एडमिशन', path: site.paths.admission, list: 'Admission', listHi: 'एडमिशन', color: 'var(--c-notice)', short: 'Admission' },
  notice: { en: 'Notice', hi: 'सूचना', path: site.paths.notice, list: 'Important Notices', listHi: 'जरूरी सूचना', color: 'var(--c-notice)', short: 'Notice' }
};

export function itemPath(i: Item): string {
  return `/${TYPES[i.type].path}/${i.slug}/`;
}

export function examPath(e: Exam): string {
  return `/exam/${e.slug}/`;
}

export function scopeName(s: string): { name: string; nameHi: string } {
  return (site.scopes as Record<string, { name: string; nameHi: string }>)[s] ?? { name: s, nameHi: s };
}

const MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
export function fmt(d?: string | null): string {
  if (!d) return '';
  const [y, m, day] = d.slice(0, 10).split('-').map(Number);
  if (!y || !m || !day) return '';
  return `${String(day).padStart(2, '0')} ${MON[m - 1]} ${y}`;
}

export function istToday(): string {
  const now = new Date(Date.now() + 5.5 * 3600 * 1000);
  return now.toISOString().slice(0, 10);
}

export function daysLeft(d?: string | null): number | null {
  if (!d) return null;
  const a = Date.parse(istToday() + 'T00:00:00Z');
  const b = Date.parse(d.slice(0, 10) + 'T00:00:00Z');
  if (Number.isNaN(b)) return null;
  return Math.round((b - a) / 86400000);
}

export function officialLink(i: Item): { href: string; label: string; deep: boolean } {
  if (i.link_policy === 'home_only') return { href: i.official_home, label: new URL(i.official_home).hostname.replace(/^www\./, ''), deep: false };
  return { href: i.url, label: new URL(i.url).hostname.replace(/^www\./, ''), deep: true };
}

export function displayTitle(i: Item): string {
  const t = i.title.trim();
  return t.toLowerCase().includes(i.short.toLowerCase()) ? t : `${i.short} ${t}`;
}

export function examOf(i: Item): Exam | undefined {
  return liveExams().find((e) => e.key === i.group);
}

export function byId(id: string): Item | undefined {
  return load().items.find((i) => i.id === id);
}

let liveCache: Item[] | null = null;
let examCache: Exam[] | null = null;
export function live(): Item[] {
  if (liveCache) return liveCache;
  const today = Date.parse(istToday());
  liveCache = load().items.filter((i) => {
    if (!i.tier || i.tier < 1) return false;
    const age = (today - Date.parse(dateKey(i))) / 86400000;
    if (i.type === 'notice' || i.type === 'admit' || i.type === 'answer') return age <= 365;
    return age <= 548;
  });
  return liveCache;
}

export function liveExams(): Exam[] {
  if (examCache) return examCache;
  const ids = new Set(live().map((i) => i.id));
  examCache = load().exams.filter((e) => e.items.filter((x) => ids.has(x)).length >= 2);
  return examCache;
}

export function fieldsOf(i: Item): Record<string, Field> {
  return (i.details && i.details.fields) || {};
}

let hubCache: Map<string, number> | null = null;
export function isIndexable(i: Item): boolean {
  if (!hubCache) hubCache = hubCounts(load().exams, new Set(live().map((x) => x.id)));
  return indexable(i, istToday(), hubCache);
}
