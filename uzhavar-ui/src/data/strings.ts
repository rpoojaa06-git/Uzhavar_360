export type Lang = 'en' | 'ta';

export const uiStrings = {
  appName: { en: 'Uzhavar', ta: 'உழவர்' },
  appTagline: {
    en: 'TN Farmers’ Assistant',
    ta: 'தமிழ்நாடு விவசாயிகள் உதவியாளர்',
  },
  homeTitle: { en: 'All Services', ta: 'அனைத்து சேவைகளும்' },
  back: { en: 'Back', ta: 'பின்செல்' },
  toggleLabel: { en: 'தமிழ்', ta: 'English' },
  lastUpdated: { en: 'Last updated', ta: 'கடைசி புதுப்பிப்பு' },
  demoNote: {
    en: 'Demo sample data — for presentation only',
    ta: 'மாதிரி தரவு — நிகழ்ச்சிக்கு மட்டுமே',
  },
  submit: { en: 'Submit', ta: 'சமர்ப்பி' },
  submitted: { en: 'Submitted successfully! (demo)', ta: 'வெற்றிகரமாக சமர்ப்பிக்கப்பட்டது! (மாதிரி)' },
  linksTitle: { en: 'Deep Links', ta: 'ஆழ் இணைப்புகள்' },
  linksIntro: {
    en: 'Copy any URL below and hand it to the RAG pipeline — it opens that service directly.',
    ta: 'கீழே உள்ள எந்த URL-ஐயும் நகலெடுத்து RAG பைப்லைனுக்கு வழங்கவும் — அது நேரடியாக அந்த சேவையைத் திறக்கும்.',
  },
  copy: { en: 'Copy', ta: 'நகல்' },
  copied: { en: 'Copied!', ta: 'நகலெடுக்கப்பட்டது!' },
  notFound: { en: 'Service not found — redirecting home…', ta: 'சேவை கிடைக்கவில்லை — முகப்புப்பக்கம் செல்கிறது…' },
  searchPlaceholder: { en: 'Search services…', ta: 'சேவைகளைத் தேடுங்கள்…' },
} as const;
