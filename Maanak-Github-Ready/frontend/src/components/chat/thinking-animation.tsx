"use client";

import { useState, useEffect } from "react";
import { Loader2 } from "lucide-react";

const LOCALIZED_STEPS: Record<string, string[]> = {
  en: [
    "Analyzing compliance request...",
    "Searching Maanak Database...",
    "Retrieving BIS legal clauses...",
    "Verifying citation accuracy...",
    "Generating strict response..."
  ],
  hi: [
    "अनुपालन अनुरोध का विश्लेषण...",
    "मानक डेटाबेस की खोज...",
    "BIS कानूनी खंडों की पुनर्प्राप्ति...",
    "उद्धरण सटीकता का सत्यापन...",
    "सटीक प्रतिक्रिया उत्पन्न कर रहा है..."
  ],
  te: [
    "అనుసరణ అభ్యర్థనను విశ్లేషిస్తోంది...",
    "మానక్ డేటాబేస్‌లో వెతుకుతోంది...",
    "BIS నిబంధనలను పొందుతోంది...",
    "ఖచ్చితత్వాన్ని ధృవీకరిస్తోంది...",
    "ప్రతిస్పందనను ఉత్పత్తి చేస్తోంది..."
  ],
  ta: [
    "கோரிக்கையை பகுப்பாய்வு செய்கிறது...",
    "Maanak தரவுத்தளத்தில் தேடுகிறது...",
    "BIS விதிகளை மீட்டெடுக்கிறது...",
    "துல்லியத்தை சரிபார்க்கிறது...",
    "பதிலை உருவாக்குகிறது..."
  ],
  mr: [
    "विनंतीचे विश्लेषण करत आहे...",
    "Maanak डेटाबेस शोधत आहे...",
    "BIS नियम प्राप्त करत आहे...",
    "अचूकता तपासत आहे...",
    "प्रतिसाद तयार करत आहे..."
  ],
  bn: [
    "অনুরোধ বিশ্লেষণ করা হচ্ছে...",
    "মানক ডেটাবেস অনুসন্ধান করা হচ্ছে...",
    "BIS ধারাগুলি পুনরুদ্ধার করা হচ্ছে...",
    "সঠিকতা যাচাই করা হচ্ছে...",
    "প্রতিক্রিয়া তৈরি করা হচ্ছে..."
  ],
  gu: [
    "વિનંતીનું વિશ્લેષણ કરી રહ્યું છે...",
    "માનક ડેટાબેઝ શોધી રહ્યું છે...",
    "BIS કલમો પ્રાપ્ત કરી રહ્યું છે...",
    "ચોકસાઈ ચકાસી રહ્યું છે...",
    "પ્રતિભાવ ઉત્પન્ન કરી રહ્યું છે..."
  ],
  kn: [
    "ವಿನಂತಿಯನ್ನು ವಿಶ್ಲೇಷಿಸಲಾಗುತ್ತಿದೆ...",
    "ಮಾನಕ್ ಡೇಟಾಬೇಸ್ ಹುಡುಕಲಾಗುತ್ತಿದೆ...",
    "BIS ನಿಯಮಗಳನ್ನು ಪಡೆಯಲಾಗುತ್ತಿದೆ...",
    "ನಿಖರತೆಯನ್ನು ಪರಿಶೀಲಿಸಲಾಗುತ್ತಿದೆ...",
    "ಪ್ರತಿಕ್ರಿಯೆಯನ್ನು ರಚಿಸಲಾಗುತ್ತಿದೆ..."
  ],
  ml: [
    "അഭ്യർത്ഥന വിശകലനം ചെയ്യുന്നു...",
    "Maanak ഡാറ്റാബേസ് തിരയുന്നു...",
    "BIS നിയമങ്ങൾ വീണ്ടെടുക്കുന്നു...",
    "കൃത്യത പരിശോധിക്കുന്നു...",
    "മറുപടി തയ്യാറാക്കുന്നു..."
  ],
  pa: [
    "ਬੇਨਤੀ ਦਾ ਵਿਸ਼ਲੇਸ਼ਣ ਕਰ ਰਿਹਾ ਹੈ...",
    "Maanak ਡੇਟਾਬੇਸ ਦੀ ਖੋਜ ਕਰ ਰਿਹਾ ਹੈ...",
    "BIS ਨਿਯਮ ਪ੍ਰਾਪਤ ਕਰ ਰਿਹਾ ਹੈ...",
    "ਸ਼ੁੱਧਤਾ ਦੀ ਜਾਂਚ ਕਰ ਰਿਹਾ ਹੈ...",
    "ਜਵਾਬ ਤਿਆਰ ਕਰ ਰਿਹਾ ਹੈ..."
  ],
  or: [
    "ଅନୁରୋଧର ବିଶ୍ଳେଷଣ କରୁଛି...",
    "Maanak ଡାଟାବେସ୍ ଖୋଜୁଛି...",
    "BIS ନିୟମଗୁଡିକ ପୁନରୁଦ୍ଧାର କରୁଛି...",
    "ସଠିକତା ଯାଞ୍ଚ କରୁଛି...",
    "ଉତ୍ତର ପ୍ରସ୍ତୁତ କରୁଛି..."
  ],
  as: [
    "অনুৰোধ বিশ্লেষণ কৰা হৈছে...",
    "মানক ডাটাবেছ সন্ধান কৰা হৈছে...",
    "BIS নিয়মসমূহ উদ্ধাৰ কৰা হৈছে...",
    "সঠিকতা পৰীক্ষা কৰা হৈছে...",
    "প্ৰতিক্ৰিয়া প্ৰস্তুত কৰা হৈছে..."
  ]
};

export function ThinkingAnimation({ lang = "en" }: { lang?: string }) {
  const [stepIndex, setStepIndex] = useState(0);

  const steps = LOCALIZED_STEPS[lang] || LOCALIZED_STEPS["en"];

  useEffect(() => {
    const interval = setInterval(() => {
      setStepIndex((prev) => (prev + 1) % steps.length);
    }, 1200);
    return () => clearInterval(interval);
  }, [steps.length]);

  return (
    <div className="flex items-center gap-3 text-emerald-600 dark:text-emerald-400 py-2">
      <div className="flex gap-1.5 px-1 relative">
        <span className="size-1.5 rounded-full bg-emerald-500 animate-bounce" style={{ animationDelay: '0ms' }} />
        <span className="size-1.5 rounded-full bg-emerald-500 animate-bounce" style={{ animationDelay: '150ms' }} />
        <span className="size-1.5 rounded-full bg-emerald-500 animate-bounce" style={{ animationDelay: '300ms' }} />
      </div>
      <span className="text-xs font-semibold tracking-wider uppercase transition-opacity duration-300">
        {steps[stepIndex]}
      </span>
    </div>
  );
}
