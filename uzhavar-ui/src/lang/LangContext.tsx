import { createContext, useContext, useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import type { Lang } from '../data/strings';

interface LangCtx {
  lang: Lang;
  setLang: (l: Lang) => void;
  toggle: () => void;
  t: (entry: { en: string; ta: string }) => string;
}

const Ctx = createContext<LangCtx | null>(null);

const STORAGE_KEY = 'uzhavar-lang';

export function LangProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>(() => {
    try {
      return (localStorage.getItem(STORAGE_KEY) as Lang) || 'en';
    } catch {
      return 'en';
    }
  });

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, lang);
    } catch {
      /* private mode */
    }
  }, [lang]);

  const value: LangCtx = {
    lang,
    setLang: setLangState,
    toggle: () => setLangState((l) => (l === 'en' ? 'ta' : 'en')),
    t: (entry) => entry[lang],
  };

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useLang(): LangCtx {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error('useLang must be used inside LangProvider');
  return ctx;
}
