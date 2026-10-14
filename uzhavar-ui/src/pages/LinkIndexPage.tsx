import { useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, Check, Copy } from 'lucide-react';
import { services } from '../data/services';
import { uiStrings } from '../data/strings';
import { useLang } from '../lang/LangContext';

export default function LinkIndexPage() {
  const { t } = useLang();
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const baseUrl = `${window.location.origin}${window.location.pathname}`;
  const urlFor = (id: string) => `${baseUrl}#/${id}`;

  const copy = async (id: string) => {
    try {
      await navigator.clipboard.writeText(urlFor(id));
      setCopiedId(id);
      setTimeout(() => setCopiedId(null), 1500);
    } catch {
      /* clipboard unavailable — user can select manually */
    }
  };

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-10 bg-brand-600 text-white shadow-md">
        <div className="flex items-center gap-3 px-3 py-3">
          <button
            onClick={() => history.back()}
            aria-label={t(uiStrings.back)}
            className="rounded-full p-1 hover:bg-white/15"
          >
            <ArrowLeft size={24} />
          </button>
          <h1 className="text-lg font-bold">{t(uiStrings.linksTitle)}</h1>
        </div>
      </header>

      <main className="mx-auto w-full max-w-md px-3 pb-10 pt-3">
        <p className="mb-3 text-xs leading-relaxed text-slate-500">{t(uiStrings.linksIntro)}</p>

        <ul className="space-y-1.5">
          {services.map((s) => (
            <li
              key={s.id}
              className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 shadow-sm"
            >
              <span aria-hidden>{s.icon}</span>
              <Link
                to={`/${s.id}`}
                className="min-w-0 flex-1 truncate text-xs font-medium text-brand-600 hover:underline"
                title={urlFor(s.id)}
              >
                #/{s.id}
              </Link>
              <button
                onClick={() => copy(s.id)}
                aria-label={t(uiStrings.copy)}
                className="shrink-0 rounded-md p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
              >
                {copiedId === s.id ? (
                  <Check size={15} className="text-green-600" />
                ) : (
                  <Copy size={15} />
                )}
              </button>
            </li>
          ))}
        </ul>
      </main>
    </div>
  );
}
