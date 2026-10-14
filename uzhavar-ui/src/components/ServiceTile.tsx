import { Link } from 'react-router-dom';
import type { Service } from '../data/services';
import { useLang } from '../lang/LangContext';

export default function ServiceTile({ service }: { service: Service }) {
  const { t } = useLang();

  return (
    <Link
      to={`/${service.id}`}
      className="flex min-h-24 flex-col items-center justify-center gap-1.5 rounded-lg border border-slate-200 bg-white p-2 text-center shadow-sm transition hover:-translate-y-0.5 hover:shadow-md active:translate-y-0 active:shadow-sm"
    >
      <span
        className="text-2xl leading-none"
        style={{ color: service.accent }}
        aria-hidden
      >
        {service.icon}
      </span>
      <span className="text-[11px] font-semibold leading-tight text-slate-700">
        {t(service.label)}
      </span>
    </Link>
  );
}
