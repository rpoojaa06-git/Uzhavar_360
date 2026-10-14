import { useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import AppHeader from '../components/AppHeader';
import ContentBlocks from '../components/ContentBlocks';
import { getServiceById } from '../data/services';
import { uiStrings } from '../data/strings';
import { useLang } from '../lang/LangContext';

export default function ServicePage() {
  const { id } = useParams<{ id: string }>();
  const service = getServiceById(id);
  const { t } = useLang();
  const navigate = useNavigate();

  // Unknown deep link (e.g. RAG pipeline typo) → show notice, fall back home.
  useEffect(() => {
    if (!service) {
      const timer = setTimeout(() => navigate('/', { replace: true }), 1500);
      return () => clearTimeout(timer);
    }
  }, [service, navigate]);

  if (!service) {
    return (
      <div className="min-h-screen">
        <AppHeader showBack />
        <p className="mx-auto max-w-md px-4 pt-10 text-center text-sm text-slate-500">
          {t(uiStrings.notFound)}
        </p>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <AppHeader showBack />
      <main className="mx-auto w-full max-w-md px-3 pb-10 pt-4">
        <div className="mb-4 flex items-center gap-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <span
            className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full text-2xl"
            style={{ backgroundColor: `${service.accent}1A` }}
            aria-hidden
          >
            {service.icon}
          </span>
          <div>
            <h1 className="text-lg font-bold leading-tight text-slate-800">
              {t(service.label)}
            </h1>
            <p className="mt-0.5 text-xs text-slate-500">
              {t(uiStrings.lastUpdated)}: {service.updated}
            </p>
          </div>
        </div>

        <ContentBlocks blocks={service.blocks} />

        <p className="mt-6 text-center text-xs text-slate-400">{t(uiStrings.demoNote)}</p>
      </main>
    </div>
  );
}
