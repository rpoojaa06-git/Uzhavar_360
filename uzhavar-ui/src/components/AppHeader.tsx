import { ArrowLeft, BookOpenText, Users } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useLang } from '../lang/LangContext';
import { uiStrings } from '../data/strings';

interface Props {
  /** Show the back arrow (detail pages). Home shows a spacer instead. */
  showBack?: boolean;
}

export default function AppHeader({ showBack = false }: Props) {
  const { t, lang, toggle } = useLang();
  const navigate = useNavigate();

  return (
    <header className="sticky top-0 z-10 bg-brand-600 text-white shadow-md">
      <div className="flex items-center gap-3 px-3 py-3">
        {showBack ? (
          <button
            onClick={() => navigate(-1)}
            aria-label={t(uiStrings.back)}
            className="rounded-full p-1 hover:bg-white/15 active:bg-white/25"
          >
            <ArrowLeft size={24} />
          </button>
        ) : (
          <span className="w-8" />
        )}

        <h1 className="flex-1 truncate text-xl font-bold tracking-wide">
          {t(uiStrings.appName)}
        </h1>

        <Users size={22} className="opacity-90" aria-hidden />
        <BookOpenText size={22} className="opacity-90" aria-hidden />

        <button
          onClick={toggle}
          className="rounded-md bg-white/15 px-2.5 py-1 text-sm font-semibold hover:bg-white/25 active:bg-white/30"
          aria-label="Switch language"
        >
          {lang === 'en' ? 'தமிழ்' : 'English'}
        </button>
      </div>
    </header>
  );
}
