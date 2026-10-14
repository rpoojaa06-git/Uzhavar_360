import type { Lang } from './strings';

export interface Bi {
  en: string;
  ta: string;
}

export type ContentBlock =
  | { kind: 'info'; heading: Bi; intro?: Bi; bullets: Bi[] }
  | { kind: 'table'; heading: Bi; columns: [Bi, Bi]; rows: [Bi, Bi][] }
  | { kind: 'cards'; heading?: Bi; items: { icon: string; title: Bi; snippet: Bi }[] }
  | {
      kind: 'form';
      heading: Bi;
      intro?: Bi;
      fields: { label: Bi; placeholder?: Bi; textarea?: boolean }[];
    };

export interface Service {
  id: string;
  label: Bi;
  icon: string;
  accent: string;
  updated: string;
  blocks: ContentBlock[];
}

export const services: Service[] = [
  {
    id: 'tamil-mannvalam',
    icon: '🌍',
    accent: '#1B7A43',
    label: { en: 'Tamil Mannvalam', ta: 'தமிழ் மண்வளம்' },
    updated: '05 Oct 2026',
    blocks: [
      {
        kind: 'info',
        heading: { en: 'Tamil Mannvalam Scheme', ta: 'தமிழ் மண்வளம் திட்டம்' },
        intro: {
          en: 'Soil health and water conservation programme promoting organic farming and traditional paddy varieties across Tamil Nadu.',
          ta: 'தமிழ்நாடு முழுவதும் இயற்கை வேளாண்மை மற்றும் பாரம்பரிய நெல் வகைகளை ஊக்குவிக்கும் மண் வளம் மற்றும் நீர் பாதுகாப்புத் திட்டம்.',
        },
        bullets: [
          { en: 'Free soil health cards for all farmers', ta: 'அனைத்து விவசாயிகளுக்கும் இலவச மண் சுகாதார அட்டை' },
          { en: 'Training on organic inputs (panchakavya, jeevamirtham)', ta: 'இயற்கை உரங்கள் பயிற்சி (பஞ்சகவ்யா, ஜீவாமிர்தம்)' },
          { en: 'Support for traditional varieties like Seeraga Samba & Kattuyanam', ta: 'சீரக சம்பா, காட்டுயாணம் போன்ற பாரம்பரிய விதை இனங்களுக்கு ஆதரவு' },
          { en: 'Village-level soil testing camps every month', ta: 'ஒவ்வொரு மாதமும் கிராம அளவில் மண் பரிசோதனை முகாம்கள்' },
        ],
      },
    ],
  },
  {
    id: 'subsidy-scheme',
    icon: '💰',
    accent: '#D98E04',
    label: { en: 'Subsidy Scheme', ta: 'மானிய திட்டம்' },
    updated: '03 Oct 2026',
    blocks: [
      {
        kind: 'info',
        heading: { en: 'Farm Subsidy Schemes', ta: 'விவசாய மானியத் திட்டங்கள்' },
        intro: {
          en: 'Central and State government subsidies available for farm equipment, drip irrigation, solar pumps and more.',
          ta: 'விவசாய இயந்திரங்கள், சொட்டு நீர் பாசனம், சூரிய மின்சார மோட்டார் போன்றவற்றுக்கான நடுவண் மற்றும் மாநில அரசு மானியங்கள்.',
        },
        bullets: [
          { en: '50% subsidy on drip & sprinkler irrigation', ta: 'சொட்டு & தெளிப்பு பாசனத்திற்கு 50% மானியம்' },
          { en: 'Solar pump subsidy up to ₹1.5 lakh', ta: 'சூரிய மின் மோட்டாருக்கு ₹1.5 லட்சம் வரை மானியம்' },
          { en: 'Rotavator & power tiller subsidy for small farmers', ta: 'சிறு விவசாயிகளுக்கு ரோட்டாவேட்டர் & பவர் டில்லர் மானியம்' },
          { en: 'Apply through your local Agriculture Officer or Uzhavan app', ta: 'உள்ளூர் வேளாண் அதிகாரி அல்லது உழவன் செயலி வழியாக விண்ணப்பிக்கலாம்' },
        ],
      },
    ],
  },
  {
    id: 'benefit-registration',
    icon: '🤝',
    accent: '#B06000',
    label: { en: 'Benefit Registration', ta: 'நல பதிவு' },
    updated: '05 Oct 2026',
    blocks: [
      {
        kind: 'form',
        heading: { en: 'Farmer Benefit Registration', ta: 'விவசாயி நல பதிவு' },
        intro: {
          en: 'Register to receive scheme benefits, advisories and subsidies directly.',
          ta: 'திட்ட நலன்கள், ஆலோசனைகள் மற்றும் மானியங்களை நேரடியாகப் பெற பதிவு செய்யுங்கள்.',
        },
        fields: [
          { label: { en: 'Full Name', ta: 'முழு பெயர்' } },
          { label: { en: 'Aadhaar Number', ta: 'ஆதார் எண்' }, placeholder: { en: 'XXXX XXXX XXXX', ta: 'XXXX XXXX XXXX' } },
          { label: { en: 'Mobile Number', ta: 'கைபேசி எண்' } },
          { label: { en: 'District', ta: 'மாவட்டம்' } },
          { label: { en: 'Land Size (acres)', ta: 'நில அளவு (ஏக்கர்)' } },
        ],
      },
    ],
  },
  {
    id: 'crop-insurance',
    icon: '🛡️',
    accent: '#7A1FA2',
    label: { en: 'Crop Insurance', ta: 'பயிர் காப்பீடு' },
    updated: '01 Oct 2026',
    blocks: [
      {
        kind: 'info',
        heading: { en: 'PMFBY Crop Insurance', ta: 'பயிர் காப்பீடு (PMFBY)' },
        intro: {
          en: 'Insurance cover for notified crops against drought, flood, pest attack and yield loss.',
          ta: 'வறட்சி, வெள்ளம், பூச்சி தாக்குதல் மற்றும் விளைச்சல் இழப்புக்கு எதிராக அறிவிக்கப்பட்ட பயிர்களுக்கான காப்பீடு.',
        },
        bullets: [
          { en: 'Premium: 2% for Kharif, 1.5% for Rabi crops', ta: 'பிரீமியம்: கரீப் 2%, ரபி 1.5%' },
          { en: 'Covers sowing to post-harvest losses', ta: 'விதைப்பு முதல் அறுவடைக்குப் பிந்தைய இழப்புகள் வரை பாதுகாப்பு' },
          { en: 'Claim within 30 days of crop damage', ta: 'பயிர் சேதம் ஏற்பட்ட 30 நாட்களுக்குள் உரிமைகோரல்' },
          { en: 'Enrollment open before seasonal cut-off dates', ta: 'பருவ கால கடைசி தேதிக்கு முன் பதிவு செய்யவும்' },
        ],
      },
    ],
  },
  {
    id: 'fertilizer-stock',
    icon: '🧪',
    accent: '#C62828',
    label: { en: 'Fertilizer Stock', ta: 'உரம் கையிருப்பு' },
    updated: 'Today',
    blocks: [
      {
        kind: 'table',
        heading: { en: 'Fertilizer Stock Availability', ta: 'உரம் கிடைக்கும் நிலவரம்' },
        columns: [
          { en: 'Item', ta: 'உரம்' },
          { en: 'Availability', ta: 'கிடைக்கும் அளவு' },
        ],
        rows: [
          [
            { en: 'Urea', ta: 'யூரியா' },
            { en: 'In stock — 450 t', ta: 'கையிருப்பு — 450 டன்' },
          ],
          [
            { en: 'DAP', ta: 'டிஏபி' },
            { en: 'In stock — 180 t', ta: 'கையிருப்பு — 180 டன்' },
          ],
          [
            { en: 'MOP', ta: 'MOP' },
            { en: 'Low stock — 42 t', ta: 'குறைவு — 42 டன்' },
          ],
          [
            { en: 'Complex 17:17:17', ta: '17:17:17 கலப்பு உரம்' },
            { en: 'Out of stock', ta: 'இல்லை' },
          ],
          [
            { en: 'Neem-coated Urea', ta: 'வேப்பம் பூசிய யூரியா' },
            { en: 'In stock — 300 t', ta: 'கையிருப்பு — 300 டன்' },
          ],
        ],
      },
    ],
  },
  {
    id: 'seed-stock',
    icon: '🌱',
    accent: '#2E7D32',
    label: { en: 'Seed Stock', ta: 'விதை கையிருப்பு' },
    updated: 'Today',
    blocks: [
      {
        kind: 'table',
        heading: { en: 'Certified Seed Availability', ta: 'சான்றளிக்கப்பட்ட விதை நிலவரம்' },
        columns: [
          { en: 'Seed Variety', ta: 'விதை இனம்' },
          { en: 'Availability', ta: 'கிடைக்கும் அளவு' },
        ],
        rows: [
          [
            { en: 'Paddy (CO 51)', ta: 'நெல் (CO 51)' },
            { en: 'In stock — 12 t', ta: 'கையிருப்பு — 12 டன்' },
          ],
          [
            { en: 'Cotton (CO 17)', ta: 'பருத்தி (CO 17)' },
            { en: 'Low stock', ta: 'குறைவு' },
          ],
          [
            { en: 'Maize (COH 6)', ta: 'மக்காச்சோளம் (COH 6)' },
            { en: 'In stock — 8 t', ta: 'கையிருப்பு — 8 டன்' },
          ],
          [
            { en: 'Blackgram (VBN 8)', ta: 'உளுத்தம்பருப்பு (VBN 8)' },
            { en: 'Out of stock', ta: 'இல்லை' },
          ],
          [
            { en: 'Groundnut (CO 7)', ta: 'நிலக்கடலை (CO 7)' },
            { en: 'In stock — 5 t', ta: 'கையிருப்பு — 5 டன்' },
          ],
        ],
      },
    ],
  },
  {
    id: 'machinery-rental',
    icon: '🚜',
    accent: '#37474F',
    label: { en: 'Agricultural Machinery for Rental', ta: 'விவசாய இயந்திர வாடகை' },
    updated: '04 Oct 2026',
    blocks: [
      {
        kind: 'form',
        heading: { en: 'Agricultural Machinery Rental', ta: 'விவசாய இயந்திர வாடகை' },
        intro: {
          en: 'Book tractors, rotavators, transplanters and harvesters from the nearby Custom Hiring Centre.',
          ta: 'டிராக்டர், ரோட்டாவேட்டர், நடவு இயந்திரம் மற்றும் அறுவடை இயந்திரங்களை அருகிலுள்ள மையத்தில் முன்பதிவு செய்யுங்கள்.',
        },
        fields: [
          { label: { en: 'Your Name', ta: 'உங்கள் பெயர்' } },
          { label: { en: 'Machine Needed', ta: 'தேவையான இயந்திரம்' }, placeholder: { en: 'Tractor / Rotavator / Harvester', ta: 'டிராக்டர் / ரோட்டாவேட்டர் / அறுவடை இயந்திரம்' } },
          { label: { en: 'Date Needed', ta: 'தேவைப்படும் தேதி' } },
          { label: { en: 'Village / Taluk', ta: 'கிராமம் / வட்டம்' } },
          { label: { en: 'Mobile Number', ta: 'கைபேசி எண்' } },
        ],
      },
    ],
  },
  {
    id: 'market-price',
    icon: '💹',
    accent: '#B3360A',
    label: { en: 'Market Price', ta: 'சந்தை விலை' },
    updated: 'Today',
    blocks: [
      {
        kind: 'table',
        heading: { en: "Today's Market Prices", ta: 'இன்றைய சந்தை விலை' },
        columns: [
          { en: 'Crop', ta: 'பயிர்' },
          { en: 'Price (₹/quintal)', ta: 'விலை (₹/குவிண்டால்)' },
        ],
        rows: [
          [{ en: 'Paddy', ta: 'நெல்' }, { en: '₹2,450', ta: '₹2,450' }],
          [{ en: 'Cotton', ta: 'பருத்தி' }, { en: '₹7,200', ta: '₹7,200' }],
          [{ en: 'Maize', ta: 'மக்காச்சோளம்' }, { en: '₹2,150', ta: '₹2,150' }],
          [{ en: 'Groundnut', ta: 'நிலக்கடலை' }, { en: '₹6,500', ta: '₹6,500' }],
          [{ en: 'Blackgram', ta: 'உளுத்தம்பருப்பு' }, { en: '₹7,800', ta: '₹7,800' }],
          [{ en: 'Chilli (dry)', ta: 'காய்ந்த மிளகாய்' }, { en: '₹18,000', ta: '₹18,000' }],
        ],
      },
      {
        kind: 'info',
        heading: { en: 'eNAM Tip', ta: 'eNAM ஆலோசனை' },
        bullets: [
          { en: 'Prices update daily at 6 AM', ta: 'விலைகள் தினமும் காலை 6 மணிக்குப் புதுப்பிக்கப்படும்' },
          { en: 'Sell at Uzhavar e-Market or eNAM mandi', ta: 'உழவர் இ-சந்தை அல்லது eNAM மண்டியில் விற்பனை செய்யலாம்' },
          { en: 'Compare prices across nearby markets before selling', ta: 'விற்பதற்கு முன் அருகிலுள்ள சந்தைகளின் விலையை ஒப்பிடுங்கள்' },
        ],
      },
    ],
  },
  {
    id: 'weather-advisory',
    icon: '🌦️',
    accent: '#0277BD',
    label: { en: 'Weather Advisory', ta: 'வானிலை ஆலோசனை' },
    updated: 'Today',
    blocks: [
      {
        kind: 'cards',
        heading: { en: '3-Day Weather Advisory — Vellore District', ta: '3 நாள் வானிலை ஆலோசனை — வேலூர் மாவட்டம்' },
        items: [
          {
            icon: '☀️',
            title: { en: 'Today', ta: 'இன்று' },
            snippet: {
              en: '28–34°C, partly cloudy. Good day for spraying.',
              ta: '28–34°C, ஓரளவு மேகம். தெளிப்புப் பணிகளுக்கு ஏற்ற நாள்.',
            },
          },
          {
            icon: '🌧️',
            title: { en: 'Tomorrow', ta: 'நாளை' },
            snippet: {
              en: 'Light rain expected after 2 PM. Postpone fertilizer application.',
              ta: 'மதியம் 2 மணிக்குப் பிறகு லேசான மழை. உரமிடும் பணியை ஒத்திவைக்கவும்.',
            },
          },
          {
            icon: '⛅',
            title: { en: 'Day After', ta: 'நாளை மறுநாள்' },
            snippet: {
              en: 'Cloudy, 26–31°C. Ideal for irrigation scheduling.',
              ta: 'மேகமூட்டம், 26–31°C. பாசன அட்டவணைப்படுத்தலுக்கு ஏற்றது.',
            },
          },
        ],
      },
    ],
  },
  {
    id: 'officer-contact',
    icon: '👥',
    accent: '#455A64',
    label: { en: 'Farmer Officer Contact Program', ta: 'அதிகாரி தொடர்பு திட்டம்' },
    updated: '02 Oct 2026',
    blocks: [
      {
        kind: 'cards',
        heading: { en: 'District Agriculture Officers', ta: 'மாவட்ட வேளாண் அதிகாரிகள்' },
        items: [
          {
            icon: '👤',
            title: { en: 'Joint Director of Agriculture', ta: 'மாவட்ட இணை இயக்குநர் (வேளாண்மை)' },
            snippet: { en: 'Vellore District — 0416-224 XXXX', ta: 'வேலூர் மாவட்டம் — 0416-224 XXXX' },
          },
          {
            icon: '👤',
            title: { en: 'Assistant Director (Vellore)', ta: 'உதவி இயக்குநர் (வேலூர்)' },
            snippet: { en: 'Contact: 0416-224 XXXX', ta: 'தொடர்பு: 0416-224 XXXX' },
          },
          {
            icon: '👤',
            title: { en: 'Agriculture Officer (Katpadi Block)', ta: 'வேளாண் அதிகாரி (காட்பாடி ஒன்றியம்)' },
            snippet: { en: 'Contact: 0416-224 XXXX', ta: 'தொடர்பு: 0416-224 XXXX' },
          },
        ],
      },
    ],
  },
  {
    id: 'farm-guide',
    icon: '📚',
    accent: '#8D6E63',
    label: { en: 'Farm Guide', ta: 'பண்ணை வழிகாட்டி' },
    updated: '28 Sep 2026',
    blocks: [
      {
        kind: 'info',
        heading: { en: 'Farm Guide', ta: 'பண்ணை வழிகாட்டி' },
        intro: {
          en: 'Season-wise cultivation practices for major crops of Tamil Nadu.',
          ta: 'தமிழ்நாட்டின் முக்கிய பயிர்களுக்கான பருவகால சாகுபடி முறைகள்.',
        },
        bullets: [
          { en: 'Kuruvai & Samba paddy calendar for Cauvery delta', ta: 'காவிரி டெல்டா குருவை & சம்பா நெல் நாட்காட்டி' },
          { en: 'Best sowing windows for Kharif vegetables', ta: 'கரீப் காய்கறிகளுக்கான சிறந்த விதைப்பு நேரம்' },
          { en: 'Intercropping: pulses with cotton & groundnut', ta: 'இடைவேளாண்மை: பருத்தி & நிலக்கடலையுடன் பருப்பு வகைகள்' },
          { en: 'Post-harvest storage & grading tips', ta: 'அறுவடைக்குப் பிந்தைய சேமிப்பு & வகைப்படுத்தல் குறிப்புகள்' },
        ],
      },
    ],
  },
  {
    id: 'organic-products',
    icon: '🍃',
    accent: '#33691E',
    label: { en: 'Organic Products', ta: 'இயற்கை பொருட்கள்' },
    updated: '30 Sep 2026',
    blocks: [
      {
        kind: 'cards',
        heading: { en: 'Certified Organic Inputs', ta: 'சான்றளிக்கப்பட்ட இயற்கை உள்ளீடுகள்' },
        items: [
          {
            icon: '🌿',
            title: { en: 'Vermicompost', ta: 'வர்மிகாம்போஸ்ட்' },
            snippet: { en: '₹8/kg — 50kg bags at TNAU Agri Hub', ta: '₹8/கிலோ — TNAU வேளாண் மையத்தில் 50 கிலோ பைகள்' },
          },
          {
            icon: '🌿',
            title: { en: 'Panchakavya', ta: 'பஞ்சகவ்யா' },
            snippet: { en: 'Bio-input for growth — 500ml @ ₹120', ta: 'வளர்ச்சிக்கான உயிர்-உரம் — 500 மி.லி @ ₹120' },
          },
          {
            icon: '🌿',
            title: { en: 'Trichoderma viride', ta: 'ட்ரைக்கோடெர்மா விரைடி' },
            snippet: { en: 'Bio-control agent — 1kg @ ₹95', ta: 'உயிர்-பாதுகாப்பு மருந்து — 1 கிலோ @ ₹95' },
          },
        ],
      },
    ],
  },
  {
    id: 'fpo-products',
    icon: '🛍️',
    accent: '#AD1457',
    label: { en: 'FPO Products', ta: 'FPO பொருட்கள்' },
    updated: '29 Sep 2026',
    blocks: [
      {
        kind: 'cards',
        heading: { en: 'Farmer Producer Organisations', ta: 'விவசாயிகள் உற்பத்தியாளர் நிறுவனங்கள்' },
        items: [
          {
            icon: '🏪',
            title: { en: 'Kalasapakkam FPO', ta: 'கல்லாப்பட்டு FPO' },
            snippet: { en: 'Cold-pressed groundnut oil — 1L @ ₹280', ta: 'கச்சாக்கல் நிலக்கடலை எண்ணெய் — 1 லி @ ₹280' },
          },
          {
            icon: '🏪',
            title: { en: 'Thally FPO', ta: 'தளி FPO' },
            snippet: { en: 'Hill banana & vegetables — weekly box @ ₹350', ta: 'மலை வாழை & காய்கறிகள் — வாராந்திர பெட்டி @ ₹350' },
          },
          {
            icon: '🏪',
            title: { en: 'Uthukuli FPO', ta: 'உத்துக்குளி FPO' },
            snippet: { en: 'Organic ghee — 500ml @ ₹450', ta: 'இயற்கை நெய் — 500 மி.லி @ ₹450' },
          },
        ],
      },
    ],
  },
  {
    id: 'reservoir-levels',
    icon: '🌊',
    accent: '#01579B',
    label: { en: 'Reservoir Levels', ta: 'அணை நீர்மட்டம்' },
    updated: 'Today',
    blocks: [
      {
        kind: 'table',
        heading: { en: 'Reservoir Levels (Today)', ta: 'நீர்நிலைகள் (இன்று)' },
        columns: [
          { en: 'Reservoir', ta: 'நீர்த்தேக்கம்' },
          { en: 'Level (Ft)', ta: 'நீர்மட்டம் (அடி)' },
        ],
        rows: [
          [{ en: 'Mettur Dam', ta: 'மேட்டூர் அணை' }, { en: '98.2 / 120', ta: '98.2 / 120' }],
          [{ en: 'Bhavanisagar', ta: 'பவானிசாகர்' }, { en: '89.5 / 105', ta: '89.5 / 105' }],
          [{ en: 'Vaigai', ta: 'வைகை' }, { en: '52.1 / 69', ta: '52.1 / 69' }],
          [{ en: 'Amaravathi', ta: 'அமராவதி' }, { en: '41.7 / 53', ta: '41.7 / 53' }],
          [{ en: 'Papanasam', ta: 'பாபநாசம்' }, { en: '122.4 / 143', ta: '122.4 / 143' }],
        ],
      },
    ],
  },
  {
    id: 'agri-news',
    icon: '📰',
    accent: '#0F172A',
    label: { en: 'Agriculture News', ta: 'வேளாண் செய்திகள்' },
    updated: 'Today',
    blocks: [
      {
        kind: 'cards',
        heading: { en: 'Latest Agriculture News', ta: 'சமீபத்திய வேளாண் செய்திகள்' },
        items: [
          {
            icon: '📰',
            title: { en: 'Kuruvai package announced for delta districts', ta: 'டெல்டா மாவட்டங்களுக்கு குருவை தொகுப்பு அறிவிப்பு' },
            snippet: {
              en: '₹116 crore special package; short-term Kuruvai loans at 4% interest.',
              ta: '₹116 கோடி சிறப்புத் தொகுப்பு; குறுகிய கால கடன்கள் 4% வட்டியில்.',
            },
          },
          {
            icon: '🥭',
            title: { en: 'New mango export facility opens in Krishnagiri', ta: 'கிருஷ்ணகிரியில் புதிய மாம்பழ ஏற்றுமதி வசதி' },
            snippet: {
              en: 'Farmers can now send produce directly to Gulf markets.',
              ta: 'விவசாயிகள் நேரடியாக வளைகுடா சந்தைகளுக்கு அனுப்பலாம்.',
            },
          },
          {
            icon: '📰',
            title: { en: 'eNAM procurement crosses 10 lakh tonnes', ta: 'eNAM கொள்முதல் 10 லட்சம் டன்னை தாண்டியது' },
            snippet: {
              en: 'Direct online sales brought better prices for paddy farmers.',
              ta: 'நேரடி ஆன்லைன் விற்பனையால் நெல் விவசாயிகளுக்கு நல்ல விலை.',
            },
          },
        ],
      },
    ],
  },
  {
    id: 'feedback',
    icon: '💬',
    accent: '#00838F',
    label: { en: 'Feedback', ta: 'கருத்து தெரிவிப்பு' },
    updated: '—',
    blocks: [
      {
        kind: 'form',
        heading: { en: 'Share Your Feedback', ta: 'உங்கள் கருத்தைப் பதிவு செய்யுங்கள்' },
        intro: {
          en: 'Tell us what to improve in the Uzhavar app.',
          ta: 'உழவர் செயலியில் மேம்படுத்த வேண்டியவற்றை எங்களிடம் தெரிவிக்கவும்.',
        },
        fields: [
          { label: { en: 'Name', ta: 'பெயர்' } },
          { label: { en: 'Mobile Number', ta: 'கைபேசி எண்' } },
          { label: { en: 'Your Feedback', ta: 'உங்கள் கருத்து' }, textarea: true },
        ],
      },
    ],
  },
  {
    id: 'pest-disease',
    icon: '🐛',
    accent: '#558B2F',
    label: { en: 'Pest/Disease Monitoring', ta: 'பூச்சி/நோய் கண்காணிப்பு' },
    updated: 'Today',
    blocks: [
      {
        kind: 'info',
        heading: { en: 'Pest & Disease Advisory', ta: 'பூச்சி & நோய் ஆலோசனை' },
        intro: {
          en: 'Recent alerts for your district — identify and treat early.',
          ta: 'உங்கள் மாவட்டத்திற்கான சமீபத்திய எச்சரிக்கைகள் — முன்கூட்டியே கண்டறிந்து சிகிச்சை அளிக்கவும்.',
        },
        bullets: [
          { en: 'Fall Armyworm alert on maize — neem oil 3ml/litre in evening', ta: 'மக்காச்சோளத்தில் இராணுவப் புழு அபாயம் — மாலை நேரத்தில் வேப்பெண்ணெய் 3 மி.லி/லிட்டர்' },
          { en: 'Blast disease in paddy (delta) — Tricyclazole 0.6g/litre', ta: 'நெல்லில் கருக்கல் நோய் (டெல்டா) — ட்ரைசைக்ளசோல் 0.6 கிரா/லிட்டர்' },
          { en: 'Whitefly on cotton — yellow sticky traps @ 10/acre', ta: 'பருத்தியில் வெள்ளை ஈ — ஏக்கருக்கு 10 மஞ்சள் பொறி' },
          { en: 'Upload a leaf photo in Uzhavan app for AI-based diagnosis', ta: 'இலை புகைப்படத்தை உழவன் செயலியில் பதிவேற்றி AI நோய் கண்டறிதல்' },
        ],
      },
    ],
  },
  {
    id: 'atma-training',
    icon: '🎓',
    accent: '#1565C0',
    label: { en: 'ATMA Training & Demonstration', ta: 'ATMA பயிற்சி & காட்சி' },
    updated: '04 Oct 2026',
    blocks: [
      {
        kind: 'cards',
        heading: { en: 'Upcoming Training Events', ta: 'வரவிருக்கும் பயிற்சி நிகழ்வுகள்' },
        items: [
          {
            icon: '🎓',
            title: { en: 'Soil Health Management', ta: 'மண் வளம் மேலாண்மை' },
            snippet: { en: 'Oct 12 — ATMA Centre, Vellore — free with lunch', ta: 'அக் 12 — ATMA மையம், வேலூர் — இலவசம் (உணவுடன்)' },
          },
          {
            icon: '🌾',
            title: { en: 'Natural Farming Workshop', ta: 'இயற்கை வேளாண்மை பட்டறை' },
            snippet: { en: 'Oct 19 — Villupuram — limited to 40 farmers', ta: 'அக் 19 — விழுப்புரம் — 40 விவசாயிகளுக்கு மட்டும்' },
          },
          {
            icon: '📦',
            title: { en: 'Post-Harvest Technology Demo', ta: 'அறுவடைக்குப் பிந்தைய தொழில்நுட்ப காட்சி' },
            snippet: { en: 'Oct 26 — Hosur — hands-on grading & packing', ta: 'அக் 26 — ஓசூர் — வகைப்படுத்தல் & பேக்கிங் பயிற்சி' },
          },
        ],
      },
    ],
  },
  {
    id: 'e-market',
    icon: '🛒',
    accent: '#EF6C00',
    label: { en: 'Uzhavar e-Market', ta: 'உழவர் இ-சந்தை' },
    updated: 'Today',
    blocks: [
      {
        kind: 'cards',
        heading: { en: 'Uzhavar e-Market', ta: 'உழவர் இ-சந்தை' },
        items: [
          {
            icon: '🌱',
            title: { en: 'Certified Seeds', ta: 'சான்றளிக்கப்பட்ட விதைகள்' },
            snippet: { en: 'Paddy, millets & pulses — home delivery in 3 days', ta: 'நெல், தினை & பருப்பு — 3 நாட்களில் வீட்டுக்கு டெலிவரி' },
          },
          {
            icon: '🔧',
            title: { en: 'Farm Tools', ta: 'விவசாயக் கருவிகள்' },
            snippet: { en: 'Sprayers, sickles, drip kits at subsidised rates', ta: 'தெளிப்பான், அரிவாள், சொட்டு பாசன கிட்கள் மானிய விலையில்' },
          },
          {
            icon: '📦',
            title: { en: 'Bulk Orders', ta: 'மொத்த ஆர்டர்' },
            snippet: { en: 'FPOs can order fertilizer in bulk with transport support', ta: 'FPO-கள் போக்குவரத்து உதவியுடன் மொத்தமாக உரம் ஆர்டர் செய்யலாம்' },
          },
        ],
      },
    ],
  },
  {
    id: 'sericulture',
    icon: '🧵',
    accent: '#6A1B9A',
    label: { en: 'Department of Sericulture', ta: 'பட்டு வளர்ப்புத் துறை' },
    updated: '25 Sep 2026',
    blocks: [
      {
        kind: 'info',
        heading: { en: 'Department of Sericulture', ta: 'பட்டு வளர்ப்புத் துறை' },
        intro: {
          en: 'Support for mulberry silk farming — from planting to marketing.',
          ta: 'மல்பெரி பட்டு வேளாண்மைக்கு — நடவு முதல் விற்பனை வரை ஆதரவு.',
        },
        bullets: [
          { en: 'Free mulberry saplings for new farmers', ta: 'புதிய விவசாயிகளுக்கு இலவச மல்பெரி நாற்றங்கால்' },
          { en: '40% capital subsidy for silk reeling equipment', ta: 'பட்டு நூற்கும் இயந்திரங்களுக்கு 40% மானியம்' },
          { en: 'Training at Government Sericulture Farms (Krishnagiri, Hosur)', ta: 'அரசு பட்டு பண்ணைகளில் பயிற்சி (கிருஷ்ணகிரி, ஓசூர்)' },
          { en: 'Buy-back guarantee for cocoons at government rates', ta: 'அரசு விலையில் புழுக்கூடுகள் கொள்முதல் உத்தரவாதம்' },
        ],
      },
    ],
  },
  {
    id: 'agri-budget',
    icon: '📊',
    accent: '#283593',
    label: { en: 'Agri Budget', ta: 'வேளாண் நிதிநிலை' },
    updated: '15 Sep 2026',
    blocks: [
      {
        kind: 'table',
        heading: { en: 'Agriculture Budget (FY 2026-27)', ta: 'வேளாண் நிதிநிலை அறிக்கை (2026-27)' },
        columns: [
          { en: 'Sector', ta: 'துறை' },
          { en: 'Allocation (₹ crore)', ta: 'ஒதுக்கீடு (₹ கோடி)' },
        ],
        rows: [
          [{ en: 'Crop production & inputs', ta: 'பயிர் உற்பத்தி & உள்ளீடுகள்' }, { en: '12,400', ta: '12,400' }],
          [{ en: 'Irrigation & water management', ta: 'பாசன & நீர் மேலாண்மை' }, { en: '8,600', ta: '8,600' }],
          [{ en: 'Horticulture', ta: 'தோட்டக்கலை' }, { en: '3,100', ta: '3,100' }],
          [{ en: 'Agricultural engineering', ta: 'வேளாண் பொறியியல்' }, { en: '2,400', ta: '2,400' }],
          [{ en: 'Marketing & storage', ta: 'சந்தைப்படுத்தல் & சேமிப்பு' }, { en: '1,800', ta: '1,800' }],
        ],
      },
    ],
  },
  {
    id: 'kadp',
    icon: '🏛️',
    accent: '#00695C',
    label: { en: 'KADP', ta: 'கலைஞர் வேளாண் திட்டம்' },
    updated: '20 Sep 2026',
    blocks: [
      {
        kind: 'info',
        heading: { en: 'Kalaignar Agriculture Development Programme', ta: 'கலைஞர் வேளாண் வளர்ச்சித் திட்டம்' },
        intro: {
          en: 'Holistic scheme bundling subsidies, advisories and market support for small farmers.',
          ta: 'சிறு விவசாயிகளுக்கு மானியங்கள், ஆலோசனைகள் மற்றும் சந்தை ஆதரவு ஒருங்கிணைந்த திட்டம்.',
        },
        bullets: [
          { en: 'Direct benefit transfer of ₹1,000/acre per season', ta: 'பருவத்திற்கு ஏக்கருக்கு ₹1,000 நேரடி நிதியுதவி' },
          { en: 'Free crop advisory SMS in Tamil', ta: 'தமிழில் இலவச பயிர் ஆலோசனை SMS' },
          { en: 'Priority access to machinery Custom Hiring Centres', ta: 'இயந்திர வாடகை மையங்களில் முன்னுரிமை அணுகல்' },
          { en: 'One-time grant for micro-irrigation conversion', ta: 'நுண் பாசன மாற்றத்திற்கு ஒருமுறை மானியம்' },
        ],
      },
    ],
  },
  {
    id: 'palmyra-felling',
    icon: '🌴',
    accent: '#795548',
    label: { en: 'Applying for Felling of Palmyra Trees', ta: 'பனை வெட்டு அனுமதி' },
    updated: '18 Sep 2026',
    blocks: [
      {
        kind: 'info',
        heading: { en: 'Applying for Felling of Palmyra Trees', ta: 'பனை மரம் வெட்ட விண்ணப்பம்' },
        intro: {
          en: 'Permission procedure to cut palmyrah trees on private land — protect first, cut only with approval.',
          ta: 'தனியார் நிலத்தில் உள்ள பனை மரங்களை வெட்ட அனுமதி — முதலில் பாதுகாப்பு, அனுமதியுடன் மட்டுமே வெட்டு.',
        },
        bullets: [
          { en: 'Apply to the local Tahsildar with tree count & survey number', ta: 'மர எண்ணிக்கை & புல எண்ணுடன் உள்ளூர் வட்டாட்சியரிடம் விண்ணப்பிக்கவும்' },
          { en: 'Inspection by Revenue & Agriculture officials within 15 days', ta: '15 நாட்களுக்குள் வருவாய் & வேளாண் அதிகாரிகள் ஆய்வு' },
          { en: 'Only dead/diseased trees permitted for felling', ta: 'இறந்த/நோயுற்ற மரங்களுக்கு மட்டுமே அனுமதி' },
          { en: 'Fine up to ₹5,000 per tree for illegal cutting', ta: 'சட்டவிரோத வெட்டுவதற்கு மரத்திற்கு ₹5,000 வரை அபராதம்' },
        ],
      },
    ],
  },
  {
    id: 'green-mission',
    icon: '🌳',
    accent: '#1B5E20',
    label: { en: 'TN Green Mission — Tree Seedlings', ta: 'பசுமை இயக்கம் — மரக்கன்றுகள்' },
    updated: '12 Sep 2026',
    blocks: [
      {
        kind: 'info',
        heading: { en: 'TN Green Mission — Tree Seedlings', ta: 'தமிழ்நாடு பசுமை இயக்கம் — மரக்கன்றுகள்' },
        intro: {
          en: "Free tree seedling distribution to increase the State's green cover.",
          ta: 'மாநில பசுமை பரப்பை அதிகரிக்க இலவச மரக்கன்று விநியோகம்.',
        },
        bullets: [
          { en: 'Free seedlings: teak, mango, neem, naval & more', ta: 'இலவச கன்றுகள்: தேக்கு, மா, வேப்பம், நவல் மற்றும் பல' },
          { en: 'Distributed at nurseries & village offices from July', ta: 'ஜூலை முதல் நர்சரிகள் & கிராம அலுவலகங்களில் கிடைக்கும்' },
          { en: 'Survival incentive ₹10 per tree after 2 years', ta: '2 ஆண்டுகளுக்குப் பிறகு மரத்திற்கு ₹10 ஊக்கத்தொகை' },
          { en: 'Target: 10 lakh seedlings per district', ta: 'இலக்கு: மாவட்டத்திற்கு 10 லட்சம் கன்றுகள்' },
        ],
      },
    ],
  },
];

export function getServiceById(id: string | undefined): Service | undefined {
  if (!id) return undefined;
  return services.find((s) => s.id === id);
}

export type { Lang };
