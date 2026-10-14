import { useState } from 'react';
import AppHeader from '../components/AppHeader';
import ServiceGrid from '../components/ServiceGrid';
import { services } from '../data/services';
import { uiStrings } from '../data/strings';
import { useLang } from '../lang/LangContext';
import { Link } from 'react-router-dom';
import { Link2 } from 'lucide-react';

export default function HomePage() {
  const { t } = useLang();
  const [query, setQuery] = useState('');

  const q = query.trim().toLowerCase();
  const filtered = q
    ? services.filter(
        (s) =>
          s.label.en.toLowerCase().includes(q) ||
          s.label.ta.includes(query.trim()) ||
          s.id.includes(q),
      )
    : services;

  return (
    <div className="min-h-screen">
      <AppHeader />
      <main className="mx-auto w-full max-w-md px-3 pb-8 pt-3">
        <div className="mb-2 flex items-center justify-between">
          <h2 className="text-sm font-bold text-slate-600">{t(uiStrings.homeTitle)}</h2>
          <Link
            to="/links"
            className="flex items-center gap-1 rounded-md px-2 py-1 text-xs font-semibold text-brand-600 hover:bg-brand-50"
          >
            <Link2 size={14} aria-hidden />
            {t(uiStrings.linksTitle)}
          </Link>
        </div>

        <input
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={t(uiStrings.searchPlaceholder)}
          className="mb-3 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-100"
        />

        <ServiceGrid services={filtered} />

        {filtered.length === 0 && (
          <p className="mt-6 text-center text-sm text-slate-500">
            {t({ en: 'No services match your search.', ta: 'தேடலுக்கு பொருந்தும் சேவைகள் இல்லை.' })}
          </p>
        )}

        <p className="mt-6 text-center text-xs text-slate-400">{t(uiStrings.demoNote)}</p>
      </main>
    </div>
  );
}
