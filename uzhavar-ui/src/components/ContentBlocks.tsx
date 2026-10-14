import { useState } from 'react';
import type { FormEvent } from 'react';
import { CheckCircle2 } from 'lucide-react';
import type { ContentBlock } from '../data/services';
import { uiStrings } from '../data/strings';
import { useLang } from '../lang/LangContext';

function InfoBlock({ block }: { block: Extract<ContentBlock, { kind: 'info' }> }) {
  const { t } = useLang();
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <h2 className="mb-2 text-base font-bold text-slate-800">{t(block.heading)}</h2>
      {block.intro && (
        <p className="mb-3 text-sm leading-relaxed text-slate-600">{t(block.intro)}</p>
      )}
      <ul className="space-y-2">
        {block.bullets.map((b, i) => (
          <li key={i} className="flex gap-2 text-sm leading-relaxed text-slate-700">
            <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-brand-500" aria-hidden />
            <span>{t(b)}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}

function TableBlock({ block }: { block: Extract<ContentBlock, { kind: 'table' }> }) {
  const { t } = useLang();
  return (
    <section className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
      <h2 className="bg-brand-50 px-4 py-3 text-base font-bold text-slate-800">
        {t(block.heading)}
      </h2>
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-slate-200 text-left text-xs uppercase tracking-wide text-slate-500">
            <th className="px-4 py-2 font-semibold">{t(block.columns[0])}</th>
            <th className="px-4 py-2 font-semibold">{t(block.columns[1])}</th>
          </tr>
        </thead>
        <tbody>
          {block.rows.map((row, i) => (
            <tr key={i} className="border-b border-slate-100 last:border-0">
              <td className="px-4 py-2.5 font-medium text-slate-700">{t(row[0])}</td>
              <td className="px-4 py-2.5 text-slate-600">{t(row[1])}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

function CardsBlock({ block }: { block: Extract<ContentBlock, { kind: 'cards' }> }) {
  const { t } = useLang();
  return (
    <section className="space-y-3">
      {block.heading && (
        <h2 className="text-base font-bold text-slate-800">{t(block.heading)}</h2>
      )}
      {block.items.map((item, i) => (
        <article
          key={i}
          className="flex gap-3 rounded-xl border border-slate-200 bg-white p-3.5 shadow-sm"
        >
          <span className="text-2xl leading-none" aria-hidden>
            {item.icon}
          </span>
          <div>
            <h3 className="text-sm font-bold text-slate-800">{t(item.title)}</h3>
            <p className="mt-0.5 text-sm leading-relaxed text-slate-600">{t(item.snippet)}</p>
          </div>
        </article>
      ))}
    </section>
  );
}

function FormBlock({ block }: { block: Extract<ContentBlock, { kind: 'form' }> }) {
  const { t } = useLang();
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setSubmitted(true);
    setTimeout(() => setSubmitted(false), 3000);
  };

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <h2 className="mb-1 text-base font-bold text-slate-800">{t(block.heading)}</h2>
      {block.intro && (
        <p className="mb-3 text-sm leading-relaxed text-slate-600">{t(block.intro)}</p>
      )}
      <form onSubmit={handleSubmit} className="space-y-3">
        {block.fields.map((f, i) => (
          <label key={i} className="block">
            <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">
              {t(f.label)}
            </span>
            {f.textarea ? (
              <textarea
                rows={3}
                required
                placeholder={f.placeholder ? t(f.placeholder) : undefined}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-100"
              />
            ) : (
              <input
                type="text"
                required
                placeholder={f.placeholder ? t(f.placeholder) : undefined}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-100"
              />
            )}
          </label>
        ))}
        <button
          type="submit"
          className="w-full rounded-lg bg-brand-600 py-2.5 text-sm font-bold text-white transition hover:bg-brand-700 active:bg-brand-900"
        >
          {t(uiStrings.submit)}
        </button>
      </form>
      {submitted && (
        <div
          role="status"
          className="mt-3 flex items-center gap-2 rounded-lg bg-green-50 px-3 py-2 text-sm font-medium text-green-700"
        >
          <CheckCircle2 size={18} aria-hidden />
          {t(uiStrings.submitted)}
        </div>
      )}
    </section>
  );
}

export default function ContentBlocks({ blocks }: { blocks: ContentBlock[] }) {
  return (
    <div className="space-y-4">
      {blocks.map((block, i) => {
        switch (block.kind) {
          case 'info':
            return <InfoBlock key={i} block={block} />;
          case 'table':
            return <TableBlock key={i} block={block} />;
          case 'cards':
            return <CardsBlock key={i} block={block} />;
          case 'form':
            return <FormBlock key={i} block={block} />;
        }
      })}
    </div>
  );
}
