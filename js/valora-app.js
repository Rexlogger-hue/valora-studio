/**
 * VALORA AI - Master Client Application & Interactive Engine
 * Brand: VALORA AI - Give every voice a presence.
 * Features: Firebase Auth, Complete Neural Voice Presets (300+), High-Tech Audio Emblems, Voice Studio.
 */

(function () {
  'use strict';

  // =========================================================================
  // 1. APPLICATION STATE & VOICE PRESETS
  // =========================================================================
  const state = {
    currentRoute: 'home',
    theme: localStorage.getItem('valora_theme') || 'dark',
    billingCycle: 'monthly',
    authUser: JSON.parse(localStorage.getItem('valora_auth_user') || sessionStorage.getItem('valora_auth_user') || 'null'),
    authToken: localStorage.getItem('valora_auth_token') || sessionStorage.getItem('valora_auth_token') || null,
    redirectAfterLogin: null,

    // Curated Premier Neural Voice Presets
    voices: [
      {
        id: 'indic_rohit',
        name: 'Rohit Verma (Indic-Parler-TTS)',
        category: 'Conversational & Explainer',
        gender: 'Male',
        accent: 'Hindi (India)',
        locale: 'hi-IN',
        tone: 'Natural & Articulate',
        fidelity: '99.9%',
        gradient: 'grad-voice-cyan',
        icon: 'fa-microphone-lines',
        emotions: ['Neutral', 'Warm', 'Cheerful', 'Authoritative'],
        useCases: ['Hindi Explainer', 'YouTube Shorts', 'E-Learning', 'Conversations'],
        bio: 'Trained on AI4Bharat Indic-Parler-TTS, Rohit delivers expressive, natural conversational Hindi speech with authentic pronunciation.',
        sampleLine: 'नमस्ते! वलोरा एआई में आपका स्वागत है। आज हम हिंदी में बात करेंगे।',
        isFavorite: true
      },
      {
        id: 'indic_divya',
        name: 'Divya Sharma (Indic-Parler-TTS)',
        category: 'Warm Narration',
        gender: 'Female',
        accent: 'Hindi (India)',
        locale: 'hi-IN',
        tone: 'Melodic & Expressive',
        fidelity: '99.9%',
        gradient: 'grad-voice-pink',
        icon: 'fa-music',
        emotions: ['Warm', 'Calm', 'Empathetic', 'Cheerful'],
        useCases: ['Hindi Audiobooks', 'Poetry', 'Meditations', 'Storytelling'],
        bio: 'Divya brings rich poetic cadence and emotive depth for audiobooks, storytelling, and podcast narration in Hindi.',
        sampleLine: 'सुप्रभात! नई सोच और नई आवाज़ के साथ अपने सपनों को सच कीजिए।',
        isFavorite: true
      },
      {
        id: 'indic_aman',
        name: 'Aman Kapoor (Indic-Parler-TTS)',
        category: 'Deep Cinematic',
        gender: 'Male',
        accent: 'Hindi (India)',
        locale: 'hi-IN',
        tone: 'Authoritative Baritone',
        fidelity: '99.8%',
        gradient: 'grad-voice-indigo',
        icon: 'fa-volume-high',
        emotions: ['Dramatic', 'Authoritative', 'Calm', 'Heroic'],
        useCases: ['Movie Trailers', 'Hindi Promos', 'Brand Commercials', 'Documentaries'],
        bio: 'Aman features commanding baritone resonance calibrated for dramatic trailers, advertisements, and corporate presentations in Hindi.',
        sampleLine: 'ज्ञान और तकनीक का यह संगम हमारे भविष्य को एक नया आयाम दे रहा है।',
        isFavorite: false
      },
      {
        id: 'indic_rani',
        name: 'Rani Patel (Indic-Parler-TTS)',
        category: 'Friendly Conversational',
        gender: 'Female',
        accent: 'Hindi (India)',
        locale: 'hi-IN',
        tone: 'Warm & Gentle',
        fidelity: '99.8%',
        gradient: 'grad-voice-amber',
        icon: 'fa-heart',
        emotions: ['Warm', 'Cheerful', 'Calm', 'Empathetic'],
        useCases: ['Social Media', 'Wellness', 'Podcasts', 'Virtual Assistant'],
        bio: 'Rani offers warm, friendly Hindi voice generation for social media, educational content, and guided wellness.',
        sampleLine: 'नमस्ते दोस्तों! आज हम सीखेंगे कि कैसे आप अपनी कहानियों को जीवंत बना सकते हैं।',
        isFavorite: false
      },
      {
        id: 'v2/en_speaker_6',
        name: 'Aria Vance',
        category: 'Warm Narration',
        gender: 'Female',
        accent: 'American English',
        locale: 'en-US',
        tone: 'Warm & Melodic',
        fidelity: '99.8%',
        gradient: 'grad-voice-indigo',
        icon: 'fa-microphone-lines',
        emotions: ['Warm', 'Calm', 'Empathetic', 'Whispering'],
        useCases: ['Audiobooks', 'Meditations', 'Narrative Podcasts'],
        bio: 'Aria delivers a rich, emotive narrative voice with delicate breath dynamics and organic cadence, crafted for immersive literature and deep storytelling.',
        sampleLine: 'The quiet morning sun touched the horizon, whispering secrets of a brand new day.',
        isFavorite: true
      },
      {
        id: 'v2/en_speaker_0',
        name: 'Guy Hawkins',
        category: 'Deep Cinematic',
        gender: 'Male',
        accent: 'American English',
        locale: 'en-US',
        tone: 'Deep & Resonant',
        fidelity: '99.8%',
        gradient: 'grad-voice-cyan',
        icon: 'fa-volume-high',
        emotions: ['Dramatic', 'Authoritative', 'Calm', 'Heroic'],
        useCases: ['Movie Trailers', 'Video Games', 'Epic Promos'],
        bio: 'Guy brings deep baritone resonance and cinematic gravitas, designed for high-stakes trailers and commanding theatrical dialogue.',
        sampleLine: 'In a world where intelligence meets sound, one voice will redefine everything we know.',
        isFavorite: false
      },
      {
        id: 'v2/en_speaker_1',
        name: 'Jenny Adams',
        category: 'Clear Professional',
        gender: 'Female',
        accent: 'American English',
        locale: 'en-US',
        tone: 'Crisp & Articulate',
        fidelity: '99.6%',
        gradient: 'grad-voice-violet',
        icon: 'fa-chart-simple',
        emotions: ['Neutral', 'Cheerful', 'Warm', 'Authoritative'],
        useCases: ['E-Learning', 'Corporate Keynotes', 'Explainer Videos'],
        bio: 'Jenny offers crystal clarity and executive diction, ideal for corporate training modules, pitch decks, and technical presentations.',
        sampleLine: 'Welcome to our quarterly briefing. Let us review the key technological milestones achieved this year.',
        isFavorite: false
      },
      {
        id: 'v2/en_speaker_2',
        name: 'Sonia Sterling',
        category: 'Authoritative Documentary',
        gender: 'Female',
        accent: 'British English',
        locale: 'en-GB',
        tone: 'Intellectual & Refined',
        fidelity: '99.7%',
        gradient: 'grad-voice-emerald',
        icon: 'fa-sliders',
        emotions: ['Authoritative', 'Serious', 'Dramatic', 'Neutral'],
        useCases: ['Documentaries', 'Historical Audio', 'Science Essays'],
        bio: 'Sonia possesses an inquisitive, grounded British timbre with thoughtful pacing, calibrated for nature documentaries and historical analysis.',
        sampleLine: 'Deep within the ancient archives, researchers uncovered an extraordinary manuscript that challenged our perception of time.',
        isFavorite: false
      },
      {
        id: 'v2/en_speaker_3',
        name: 'Ryan Kingsley',
        category: 'Dramatic Storytelling',
        gender: 'Male',
        accent: 'British English',
        locale: 'en-GB',
        tone: 'Theatrical & Intense',
        fidelity: '99.6%',
        gradient: 'grad-voice-blue',
        icon: 'fa-wave-square',
        emotions: ['Dramatic', 'Heroic', 'Authoritative', 'Whispering'],
        useCases: ['Fantasy Audiobooks', 'NPC Gaming Dialogue', 'Audio Drama'],
        bio: 'Ryan delivers raw character depth and emotional range, tailor-made for fantasy epics, warrior dialogue, and complex villains.',
        sampleLine: 'The storm approaches the citadel! Hold the line, and let not the flame of hope be extinguished!',
        isFavorite: false
      },
      {
        id: 'v2/en_speaker_4',
        name: 'Natasha Ray',
        category: 'Friendly Conversational',
        gender: 'Female',
        accent: 'Australian English',
        locale: 'en-AU',
        tone: 'Vibrant & Bright',
        fidelity: '99.5%',
        gradient: 'grad-voice-amber',
        icon: 'fa-microphone-lines',
        emotions: ['Cheerful', 'Warm', 'Energetic', 'Neutral'],
        useCases: ['YouTube Content', 'Social Media', 'Casual Podcasts'],
        bio: 'Natasha speaks with spontaneous rhythm and infectious warmth, making lifestyle videos and creator vlogs feel natural and engaging.',
        sampleLine: 'Hey everyone! Today we are diving into the most exciting audio innovations you can try right now.',
        isFavorite: false
      },
      {
        id: 'v2/en_speaker_5',
        name: 'Neerja Sen',
        category: 'Podcast Host',
        gender: 'Female',
        accent: 'Indian English',
        locale: 'en-IN',
        tone: 'Smooth & Charismatic',
        fidelity: '99.6%',
        gradient: 'grad-voice-rose',
        icon: 'fa-microphone-lines',
        emotions: ['Warm', 'Cheerful', 'Neutral', 'Authoritative'],
        useCases: ['Interview Shows', 'Tech Podcasts', 'Discussion Panels'],
        bio: 'Neerja combines thoughtful intonation with upbeat conversational flow, perfect for talk shows and intellectual deep dives.',
        sampleLine: 'Welcome back to the studio. Today we explore how artificial intelligence is transforming modern creativity.',
        isFavorite: false
      },
      {
        id: 'v2/en_in_speaker_1',
        name: 'Prabhat Verma',
        category: 'Energetic Commercial',
        gender: 'Male',
        accent: 'Indian English',
        locale: 'en-IN',
        tone: 'Confident & Persuasive',
        fidelity: '99.7%',
        gradient: 'grad-voice-indigo',
        icon: 'fa-volume-high',
        emotions: ['Energetic', 'Cheerful', 'Authoritative', 'Dramatic'],
        useCases: ['TV & Radio Ads', 'Product Launches', 'High-energy Promos'],
        bio: 'Prabhat brings commercial sales momentum and crisp pronunciation, engineered for broadcast advertising and viral shorts.',
        sampleLine: 'Unleash your creative potential today. Experience the breakthrough speed of Valora AI!',
        isFavorite: false
      },
      {
        id: 'v2/hi_speaker_0',
        name: 'Swara Sharma',
        category: 'Warm Narration',
        gender: 'Female',
        accent: 'Hindi (India)',
        locale: 'hi-IN',
        tone: 'Gentle & Melodic',
        fidelity: '99.8%',
        gradient: 'grad-voice-pink',
        icon: 'fa-music',
        emotions: ['Warm', 'Calm', 'Empathetic', 'Cheerful'],
        useCases: ['Audiobooks', 'Meditations', 'Storytelling', 'Podcasts'],
        bio: 'Swara provides a pristine, natural Hindi voice with poetic flow and emotive depth, optimized for regional narratives and audiobooks.',
        sampleLine: 'नमस्ते! वलोरा एआई में आपका स्वागत है। आपकी आवाज़ को एक नई पहचान देने के लिए हम तैयार हैं।',
        isFavorite: true
      },
      {
        id: 'v2/hi_speaker_1',
        name: 'Madhur Gupta',
        category: 'Deep Cinematic',
        gender: 'Male',
        accent: 'Hindi (India)',
        locale: 'hi-IN',
        tone: 'Warm & Authoritative',
        fidelity: '99.6%',
        gradient: 'grad-voice-amber',
        icon: 'fa-sliders',
        emotions: ['Dramatic', 'Authoritative', 'Calm', 'Warm'],
        useCases: ['Commercials', 'Documentaries', 'E-Learning', 'Audiobooks'],
        bio: 'Madhur features a deep, trustworthy Hindi baritone ideal for documentaries, brand commercials, and engaging narratives.',
        sampleLine: 'ज्ञान और तकनीक का यह संगम हमारे भविष्य को एक नया आयाम दे रहा है।',
        isFavorite: false
      },
      {
        id: 'v2/ta_speaker_0',
        name: 'Pallavi Sundaram',
        category: 'Polyglot Multilingual',
        gender: 'Female',
        accent: 'Tamil (India)',
        locale: 'ta-IN',
        tone: 'Expressive & Clear',
        fidelity: '99.5%',
        gradient: 'grad-voice-teal',
        icon: 'fa-microphone-lines',
        emotions: ['Warm', 'Empathetic', 'Cheerful', 'Dramatic'],
        useCases: ['Tamil Audiobooks', 'Regional Content', 'Dubbing'],
        bio: 'Pallavi brings classical Tamil diction with modern, natural cadence for regional audiobooks and e-learning platforms.',
        sampleLine: 'வணக்கம்! வலோரா ஏஐயின் அதிநவீன குரல் தொழில்நுட்பத்திற்கு உங்களை வரவேற்கிறோம்.',
        isFavorite: false
      },
      {
        id: 'v2/ta_speaker_1',
        name: 'Valluvar Raman',
        category: 'Deep Cinematic',
        gender: 'Male',
        accent: 'Tamil (India)',
        locale: 'ta-IN',
        tone: 'Authoritative & Resonant',
        fidelity: '99.4%',
        gradient: 'grad-voice-blue',
        icon: 'fa-volume-high',
        emotions: ['Authoritative', 'Dramatic', 'Serious'],
        useCases: ['Cinema Dubbing', 'Documentaries', 'Announcements'],
        bio: 'Valluvar delivers strong, resonant Tamil narration with traditional gravitas and clarity.',
        sampleLine: 'காலத்தை வெல்லும் குரல் படைப்புகள் இப்போது உங்கள் கைகளில் சாத்தியமாகிறது.',
        isFavorite: false
      },
      {
        id: 'v2/te_speaker_0',
        name: 'Shruti Varma',
        category: 'Warm Narration',
        gender: 'Female',
        accent: 'Telugu (India)',
        locale: 'te-IN',
        tone: 'Melodic & Smooth',
        fidelity: '99.5%',
        gradient: 'grad-voice-violet',
        icon: 'fa-music',
        emotions: ['Warm', 'Cheerful', 'Calm'],
        useCases: ['Audiobooks', 'Podcasts', 'Regional Media'],
        bio: 'Shruti delivers melodic Telugu speech with natural prosody and expressive intonations.',
        sampleLine: 'నమస్కారం! మీ ఆలోచనలను అత్యంత సహజమైన స్వరంలోకి మార్చడానికి వలోరా సిద్ధంగా ఉంది.',
        isFavorite: false
      },
      {
        id: 'v2/te_speaker_1',
        name: 'Mohan Reddy',
        category: 'Clear Professional',
        gender: 'Male',
        accent: 'Telugu (India)',
        locale: 'te-IN',
        tone: 'Deep & Inspiring',
        fidelity: '99.3%',
        gradient: 'grad-voice-cyan',
        icon: 'fa-chart-simple',
        emotions: ['Authoritative', 'Energetic', 'Neutral'],
        useCases: ['Commercials', 'Documentaries', 'Presentations'],
        bio: 'Mohan is tuned for inspiring corporate and media voiceovers in Telugu.',
        sampleLine: 'అధునాతన కృత్రిమ మేధస్సుతో సరికొత్త ఆడియో అనుభవాన్ని పొందండి.',
        isFavorite: false
      },
      {
        id: 'v2/mr_speaker_0',
        name: 'Aarohi Joshi',
        category: 'Warm Narration',
        gender: 'Female',
        accent: 'Marathi (India)',
        locale: 'mr-IN',
        tone: 'Gentle & Clear',
        fidelity: '99.4%',
        gradient: 'grad-voice-rose',
        icon: 'fa-microphone-lines',
        emotions: ['Warm', 'Calm', 'Cheerful'],
        useCases: ['Marathi Literature', 'Storytelling', 'Podcasts'],
        bio: 'Aarohi provides soft, lyrical Marathi narration suited for audio literature and cultural storytelling.',
        sampleLine: 'नमस्कार! वलोरा एआयच्या मदतीने आपले शब्द आता जिवंत स्वरांमध्ये अनुभवा.',
        isFavorite: false
      },
      {
        id: 'v2/bn_speaker_0',
        name: 'Tanishaa Roy',
        category: 'Warm Narration',
        gender: 'Female',
        accent: 'Bengali (India)',
        locale: 'bn-IN',
        tone: 'Lyrical & Sweet',
        fidelity: '99.5%',
        gradient: 'grad-voice-pink',
        icon: 'fa-music',
        emotions: ['Warm', 'Empathetic', 'Calm'],
        useCases: ['Bengali Audiobooks', 'Poetry', 'Podcasts'],
        bio: 'Tanishaa features the characteristic melodious cadence of Bengali, perfect for poetry and literature.',
        sampleLine: 'নমস্কার! নতুন প্রযুক্তির সাথে আপনার কণ্ঠের স্বপ্নকে বাস্তব রূপ দিন।',
        isFavorite: false
      },
      {
        id: 'v2/gu_speaker_0',
        name: 'Dhwani Patel',
        category: 'Clear Professional',
        gender: 'Female',
        accent: 'Gujarati (India)',
        locale: 'gu-IN',
        tone: 'Crisp & Lively',
        fidelity: '99.3%',
        gradient: 'grad-voice-amber',
        icon: 'fa-chart-simple',
        emotions: ['Cheerful', 'Warm', 'Neutral'],
        useCases: ['Business Explainer', 'Education', 'Advertisements'],
        bio: 'Dhwani offers bright, crisp Gujarati voice generation for business and storytelling.',
        sampleLine: 'નમસ્તે! તમારી વાર્તાઓને એક અદભુત અને સ્પષ્ટ અવાજ આપો.',
        isFavorite: false
      },
      {
        id: 'v2/kn_speaker_0',
        name: 'Sapna Gowda',
        category: 'Warm Narration',
        gender: 'Female',
        accent: 'Kannada (India)',
        locale: 'kn-IN',
        tone: 'Clear & Engaging',
        fidelity: '99.4%',
        gradient: 'grad-voice-teal',
        icon: 'fa-microphone-lines',
        emotions: ['Warm', 'Cheerful', 'Calm'],
        useCases: ['Kannada Audiobooks', 'Instructional', 'Radio'],
        bio: 'Sapna brings clear, authentic Kannada vocal directability for regional media.',
        sampleLine: 'ನಮಸ್ಕಾರ! ವಲೋರಾ ಎಐ ಮೂಲಕ ನಿಮ್ಮ ಕಲ್ಪನೆಗೆ ಸುಂದರ ಧ್ವನಿಯನ್ನು ನೀಡಿ.',
        isFavorite: false
      },
      {
        id: 'v2/ml_speaker_0',
        name: 'Sobhana Nair',
        category: 'Calm Meditation',
        gender: 'Female',
        accent: 'Malayalam (India)',
        locale: 'ml-IN',
        tone: 'Soft & Expressive',
        fidelity: '99.4%',
        gradient: 'grad-voice-emerald',
        icon: 'fa-wave-square',
        emotions: ['Calm', 'Empathetic', 'Warm'],
        useCases: ['Audiobooks', 'Meditation', 'Documentaries'],
        bio: 'Sobhana delivers smooth Malayalam voice synthesis tailored for soothing narratives.',
        sampleLine: 'നമസ്കാരം! നിങ്ങളുടെ ശബ്ദയാത്ര ഇവിടെ മനോഹരമായി ആരംഭിക്കുന്നു.',
        isFavorite: false
      },
      {
        id: 'v2/ur_speaker_0',
        name: 'Gul Hassan',
        category: 'Warm Narration',
        gender: 'Female',
        accent: 'Urdu',
        locale: 'ur-IN',
        tone: 'Soft & Elegant',
        fidelity: '99.5%',
        gradient: 'grad-voice-violet',
        icon: 'fa-music',
        emotions: ['Warm', 'Empathetic', 'Calm'],
        useCases: ['Urdu Poetry', 'Literature', 'Audio Dramas'],
        bio: 'Gul provides refined Urdu intonation and poetic elegance.',
        sampleLine: 'خوش آمدید! آپ کے الفاظ کو دلکش اور قدرتی آواز میں ڈھالنے کے لیے والورا تیار ہے۔',
        isFavorite: false
      },
      {
        id: 'v2/ur_speaker_1',
        name: 'Salman Qureshi',
        category: 'Deep Cinematic',
        gender: 'Male',
        accent: 'Urdu',
        locale: 'ur-IN',
        tone: 'Rich & Resonant',
        fidelity: '99.4%',
        gradient: 'grad-voice-indigo',
        icon: 'fa-volume-high',
        emotions: ['Authoritative', 'Dramatic', 'Warm'],
        useCases: ['Narration', 'Documentary', 'Drama'],
        bio: 'Salman offers classical Urdu depth and commanding narrative presence.',
        sampleLine: 'الفاظ کی طاقت کو ایک نئی آواز اور احساس کے ساتھ دنیا تک پہنچائیں۔',
        isFavorite: false
      },
      {
        id: 'v2/pa_speaker_0',
        name: 'Ojas Singh',
        category: 'Energetic Commercial',
        gender: 'Male',
        accent: 'Punjabi',
        locale: 'pa-IN',
        tone: 'Energetic & Vibrant',
        fidelity: '99.5%',
        gradient: 'grad-voice-amber',
        icon: 'fa-volume-high',
        emotions: ['Energetic', 'Cheerful', 'Dramatic'],
        useCases: ['Commercials', 'Music Intros', 'Youth Content'],
        bio: 'Ojas delivers high-energy, enthusiastic Punjabi and Indian accent voice tracks.',
        sampleLine: 'ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ! ਆਓ ਆਪਣੇ ਵਿਚਾਰਾਂ ਨੂੰ ਇੱਕ ਬੇਹਤਰੀਨ ਆਵਾਜ਼ ਦੇਈਏ।',
        isFavorite: false
      },
      {
        id: 'v2/es_speaker_0',
        name: 'Elvira Gomez',
        category: 'Warm Narration',
        gender: 'Female',
        accent: 'Spanish (Spain)',
        locale: 'es-ES',
        tone: 'Passionate & Melodic',
        fidelity: '99.7%',
        gradient: 'grad-voice-rose',
        icon: 'fa-microphone-lines',
        emotions: ['Warm', 'Cheerful', 'Dramatic', 'Calm'],
        useCases: ['Audiobooks', 'Podcasts', 'Commercials', 'Dubbing'],
        bio: 'Elvira brings warmth, rich Castilian cadence, and dynamic expressive emotion.',
        sampleLine: '¡Hola! Bienvenido a Valora AI. Da vida a tus historias con una voz auténtica y emocionante.',
        isFavorite: true
      },
      {
        id: 'v2/es_speaker_1',
        name: 'Alvaro Diaz',
        category: 'Deep Cinematic',
        gender: 'Male',
        accent: 'Spanish (Spain)',
        locale: 'es-ES',
        tone: 'Rich & Compelling',
        fidelity: '99.6%',
        gradient: 'grad-voice-indigo',
        icon: 'fa-volume-high',
        emotions: ['Dramatic', 'Authoritative', 'Warm'],
        useCases: ['Trailers', 'Gaming NPCs', 'Documentaries'],
        bio: 'Alvaro features a compelling Spanish baritone calibrated for cinematic depth.',
        sampleLine: 'En cada palabra reside una emoción que transformará la manera en que escuchamos el mundo.',
        isFavorite: false
      },
      {
        id: 'v2/fr_speaker_0',
        name: 'Denise Laurent',
        category: 'Clear Professional',
        gender: 'Female',
        accent: 'French (France)',
        locale: 'fr-FR',
        tone: 'Elegant & Articulate',
        fidelity: '99.7%',
        gradient: 'grad-voice-cyan',
        icon: 'fa-chart-simple',
        emotions: ['Warm', 'Neutral', 'Cheerful', 'Calm'],
        useCases: ['Luxury Ads', 'Documentaries', 'Audiobooks'],
        bio: 'Denise delivers flawless French pronunciation with refined, elegant cadence.',
        sampleLine: 'Bonjour et bienvenue sur Valora AI. Donnez à chaque récit la voix qu\'il mérite.',
        isFavorite: false
      },
      {
        id: 'v2/fr_speaker_1',
        name: 'Henri Dupont',
        category: 'Authoritative Documentary',
        gender: 'Male',
        accent: 'French (France)',
        locale: 'fr-FR',
        tone: 'Classic & Intellectual',
        fidelity: '99.5%',
        gradient: 'grad-voice-blue',
        icon: 'fa-sliders',
        emotions: ['Authoritative', 'Dramatic', 'Calm'],
        useCases: ['Historical Essays', 'Audiobooks', 'Documentaries'],
        bio: 'Henri brings classic French narrative authority and deep tonal precision.',
        sampleLine: 'À travers les siècles, la voix humaine a toujours été le plus puissant des instruments.',
        isFavorite: false
      },
      {
        id: 'v2/ja_speaker_0',
        name: 'Nanami Shimizu',
        category: 'Young Character',
        gender: 'Female',
        accent: 'Japanese (Japan)',
        locale: 'ja-JP',
        tone: 'Natural & Animated',
        fidelity: '99.6%',
        gradient: 'grad-voice-pink',
        icon: 'fa-music',
        emotions: ['Cheerful', 'Energetic', 'Warm', 'Whispering'],
        useCases: ['Anime Dubbing', 'Gaming', 'Virtual Assistant'],
        bio: 'Nanami is optimized for natural Japanese animation dialogue, gaming, and cheerful assistant roles.',
        sampleLine: 'こんにちは！Valora AIへようこそ。あなたの言葉を美しい音声でお届けします。',
        isFavorite: false
      },
      {
        id: 'v2/ja_speaker_1',
        name: 'Keita Tanaka',
        category: 'Friendly Conversational',
        gender: 'Male',
        accent: 'Japanese (Japan)',
        locale: 'ja-JP',
        tone: 'Calm & Friendly',
        fidelity: '99.4%',
        gradient: 'grad-voice-teal',
        icon: 'fa-microphone-lines',
        emotions: ['Neutral', 'Cheerful', 'Calm', 'Dramatic'],
        useCases: ['Narration', 'Tech Explainer', 'Audio Guides'],
        bio: 'Keita offers clean, modern Japanese intonation suited for corporate explainers and documentaries.',
        sampleLine: '最先端のニューラル音声合成技術で、新しい表現の可能性を体験してください。',
        isFavorite: false
      },
      {
        id: 'orion_assistant',
        name: 'Orion Vance',
        category: 'Virtual Assistant',
        gender: 'Non-Binary',
        accent: 'Neutral Global',
        locale: 'en-US',
        tone: 'Precise & Helpful',
        fidelity: '99.8%',
        gradient: 'grad-voice-emerald',
        icon: 'fa-sliders',
        emotions: ['Neutral', 'Cheerful', 'Calm', 'Authoritative'],
        useCases: ['AI Agents', 'Navigation Systems', 'Smart Devices'],
        bio: 'Orion is designed for low-latency interactive conversational systems, IoT hardware, and responsive smart assistants.',
        sampleLine: 'All neural audio pipelines are operational. Your synthesis workspace is ready.',
        isFavorite: false
      },
      {
        id: 'sofia_meditation',
        name: 'Sofia Morales',
        category: 'Calm Meditation',
        gender: 'Female',
        accent: 'American English',
        locale: 'en-US',
        tone: 'Serene & Gentle',
        fidelity: '99.5%',
        gradient: 'grad-voice-violet',
        icon: 'fa-wave-square',
        emotions: ['Calm', 'Whispering', 'Warm', 'Empathetic'],
        useCases: ['Guided Meditation', 'Sleep Stories', 'Wellness Apps'],
        bio: 'Sofia is optimized for mindfulness and sleep literature, featuring soft harmonic frequencies and gentle, rhythmic breath control.',
        sampleLine: 'Close your eyes gently. Inhale the stillness, and let go of any tension as you exhale slowly.',
        isFavorite: false
      }
    ],

    // Studio Active State
    studio: {
      activeVoiceId: 'v2/en_speaker_6',
      activeEmotion: 'Neutral',
      speed: 1.0,
      pitch: 0,
      intensity: 75,
      pauseStyle: 1,
      isGenerating: false,
      isPlaying: false,
      currentTime: 0,
      totalDuration: 6.5,
      sessionTakes: []
    },

    // Notifications
    notifications: [
      {
        id: 'notif-1',
        title: 'Neural Vocoder 3.0 Active',
        desc: 'Over 300+ voice presets available with sub-200ms latent diffusion.',
        time: 'Just now',
        unread: true,
        icon: 'sparkles'
      },
      {
        id: 'notif-2',
        title: 'Valora AI Auth System Active',
        desc: 'Secure local & cloud user management with cryptographic session tokens.',
        time: '15m ago',
        unread: true,
        icon: 'shield'
      },
      {
        id: 'notif-3',
        title: 'Lossless 48kHz WAV Export',
        desc: 'Studio takes can now be downloaded in broadcast-ready 24-bit PCM.',
        time: '1h ago',
        unread: false,
        icon: 'waveform'
      }
    ]
  };

  // Playback audio references
  let playerInterval = null;
  let activeAudio = null;

  // =========================================================================
  // 2. HELPER: VOICE EMBLEM BADGE (NO HUMAN PHOTOS)
  // =========================================================================
  function getVoiceEmblemHTML(voice, size = 'md') {
    const sizeMap = {
      sm: { box: '36px', radius: '10px', icon: '0.85rem' },
      md: { box: '48px', radius: '13px', icon: '1.15rem' },
      lg: { box: '56px', radius: '16px', icon: '1.4rem' }
    };
    const s = sizeMap[size] || sizeMap.md;
    const gradClass = voice.gradient || 'grad-voice-indigo';
    const iconClass = voice.icon || 'fa-microphone-lines';

    return `
      <div class="voice-emblem-badge ${gradClass}" style="width:${s.box};height:${s.box};border-radius:${s.radius};" title="${escapeHtml(voice.name)}">
        <i class="fa-solid ${iconClass} voice-emblem-icon" style="font-size:${s.icon};"></i>
        <div class="mini-equalizer">
          <span></span><span></span><span></span><span></span>
        </div>
      </div>
    `;
  }

  // =========================================================================
  // 2b. FIREBASE AUTH CONFIGURATION & INITIALIZER
  // =========================================================================
  const firebaseConfig = {
    apiKey: "AIzaSyAJhXeviO_0r8v38j7YeoZRi7GGCXpMdj0",
    authDomain: "valora-ai-studio.firebaseapp.com",
    projectId: "valora-ai-studio",
    storageBucket: "valora-ai-studio.firebasestorage.app",
    messagingSenderId: "882517049213",
    appId: "1:882517049213:web:7deae463b98d7964d65614",
    measurementId: "G-98ZW2BGFVD"
  };

  function initFirebase() {
    if (typeof firebase !== 'undefined' && !firebase.apps.length) {
      try {
        firebase.initializeApp(firebaseConfig);
        console.log('[Valora AI] Firebase Auth initialized successfully.');
      } catch (err) {
        console.warn('[Valora AI] Firebase initialization warning:', err);
      }
    }
  }

  // =========================================================================
  // 3. INITIALIZATION ROUTINE
  // =========================================================================
  document.addEventListener('DOMContentLoaded', () => {
    initFirebase();
    initTheme();
    verifyAuthSession();
    initRouting();
    initAuth();
    initStudio();
    initVoiceLibrary();
    initLandingPage();
    initPricing();
    initProfile();
    initModals();
    initNotifications();
    loadVoicePresets(); // Fetch all backend voices asynchronously
  });

  // =========================================================================
  // 4. AUTHENTICATION SESSION MANAGEMENT
  // =========================================================================
  async function verifyAuthSession() {
    if (!state.authToken) {
      renderNavAuth();
      return;
    }

    try {
      const res = await fetch('/api/auth/me', {
        headers: {
          'Authorization': `Bearer ${state.authToken}`,
          'Accept': 'application/json'
        }
      });

      if (res.ok) {
        const data = await res.json();
        if (data && data.user) {
          state.authUser = data.user;
          const isPersistent = !!localStorage.getItem('valora_auth_token');
          if (isPersistent) {
            localStorage.setItem('valora_auth_user', JSON.stringify(data.user));
          } else {
            sessionStorage.setItem('valora_auth_user', JSON.stringify(data.user));
          }
          renderNavAuth();
          if (state.currentRoute === 'profile') renderProfileData();
        }
      } else if (res.status === 401) {
        // Expired or invalid session
        clearAuthSession();
      }
    } catch (err) {
      console.warn('Backend auth session check notice:', err);
    }
  }

  function setAuthSession(user, token, remember = true) {
    state.authUser = user;
    state.authToken = token || ('tok_' + Math.random().toString(36).slice(2));

    if (remember) {
      localStorage.setItem('valora_auth_user', JSON.stringify(user));
      localStorage.setItem('valora_auth_token', state.authToken);
      sessionStorage.removeItem('valora_auth_user');
      sessionStorage.removeItem('valora_auth_token');
    } else {
      sessionStorage.setItem('valora_auth_user', JSON.stringify(user));
      sessionStorage.setItem('valora_auth_token', state.authToken);
      localStorage.removeItem('valora_auth_user');
      localStorage.removeItem('valora_auth_token');
    }

    renderNavAuth();
    if (state.currentRoute === 'profile') renderProfileData();
  }

  function clearAuthSession() {
    state.authUser = null;
    state.authToken = null;
    localStorage.removeItem('valora_auth_user');
    localStorage.removeItem('valora_auth_token');
    sessionStorage.removeItem('valora_auth_user');
    sessionStorage.removeItem('valora_auth_token');
    renderNavAuth();
  }

  function getInitials(name) {
    if (!name) return 'VA';
    const parts = name.trim().split(/\s+/);
    if (parts.length >= 2) {
      return (parts[0][0] + parts[1][0]).toUpperCase();
    }
    return name.slice(0, 2).toUpperCase();
  }

  // =========================================================================
  // 5. THEME SYSTEM (DARK / LIGHT)
  // =========================================================================
  function initTheme() {
    applyTheme(state.theme);

    const toggleBtn = document.getElementById('theme-toggle-btn');
    if (toggleBtn) {
      toggleBtn.addEventListener('click', () => {
        state.theme = state.theme === 'dark' ? 'light' : 'dark';
        localStorage.setItem('valora_theme', state.theme);
        applyTheme(state.theme);
        showToast(`Switched to ${state.theme} mode`, 'info');
      });
    }
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    const darkIcon = document.querySelector('.theme-icon-dark');
    const lightIcon = document.querySelector('.theme-icon-light');
    if (darkIcon && lightIcon) {
      darkIcon.style.display = theme === 'dark' ? 'inline-block' : 'none';
      lightIcon.style.display = theme === 'light' ? 'inline-block' : 'none';
    }
  }

  // =========================================================================
  // 6. SPA ROUTER & NAVIGATION
  // =========================================================================
  function initRouting() {
    function handleHash() {
      let hash = window.location.hash.replace('#', '').trim() || 'home';
      const validRoutes = ['home', 'studio', 'voices', 'introduction', 'pricing', 'profile', 'login', 'signup', 'forgot-password'];
      
      if (!validRoutes.includes(hash)) {
        hash = 'home';
      }

      // Route Protection: Profile requires auth
      if (hash === 'profile' && !state.authUser) {
        state.redirectAfterLogin = 'profile';
        showToast('Please sign in to access your studio profile & saved takes.', 'info');
        navigateTo('login', false);
        return;
      }

      navigateTo(hash, false);
    }

    window.addEventListener('hashchange', handleHash);
    window.addEventListener('popstate', handleHash);

    // Intercept navigation clicks
    document.addEventListener('click', (e) => {
      const link = e.target.closest('a[href^="#"], [data-page]');
      if (link) {
        const target = link.getAttribute('data-page') || link.getAttribute('href').replace('#', '');
        if (target && !link.hasAttribute('download')) {
          e.preventDefault();
          navigateTo(target, true);
          closeMobileDrawer();
        }
      }
    });

    // Mobile Hamburger
    const mobileBtn = document.getElementById('mobile-menu-btn');
    const drawerCloseBtn = document.getElementById('drawer-close-btn');
    const drawerBackdrop = document.getElementById('drawer-backdrop');

    if (mobileBtn) mobileBtn.addEventListener('click', openMobileDrawer);
    if (drawerCloseBtn) drawerCloseBtn.addEventListener('click', closeMobileDrawer);
    if (drawerBackdrop) drawerBackdrop.addEventListener('click', closeMobileDrawer);

    // Run initial route
    handleHash();
  }

  function navigateTo(pageId, updateHash = true) {
    state.currentRoute = pageId;

    if (updateHash) {
      window.location.hash = pageId === 'home' ? '' : `#${pageId}`;
    }

    // Toggle active page section
    document.querySelectorAll('.page-section').forEach((sec) => {
      sec.classList.toggle('active', sec.id === `page-${pageId}`);
    });

    // Toggle active navbar links
    document.querySelectorAll('.nav-link, .drawer-link').forEach((link) => {
      const p = link.getAttribute('data-page') || link.getAttribute('href').replace('#', '');
      link.classList.toggle('active', p === pageId);
    });

    window.scrollTo({ top: 0, behavior: 'smooth' });

    // Update active view data
    if (pageId === 'voices') renderVoiceLibrary();
    if (pageId === 'profile') renderProfileData();
    if (pageId === 'studio') {
      updateStudioActiveVoicePreview();
      renderSessionTakes();
    }
  }

  function openMobileDrawer() {
    document.getElementById('mobile-drawer')?.classList.add('open');
    document.getElementById('drawer-backdrop')?.classList.add('open');
  }

  function closeMobileDrawer() {
    document.getElementById('mobile-drawer')?.classList.remove('open');
    document.getElementById('drawer-backdrop')?.classList.remove('open');
  }

  // =========================================================================
  // 7. AUTHENTICATION (LOGIN, SIGNUP, GOOGLE, GUEST, FASTAPI BACKEND)
  // =========================================================================
  function initAuth() {
    renderNavAuth();

    // Login Form
    const loginForm = document.getElementById('form-login');
    const loginSubmitBtn = document.getElementById('btn-submit-login');
    const guestLoginBtn = document.getElementById('btn-guest-login');

    const doLogin = async (e) => {
      if (e) e.preventDefault();
      const emailInput = document.getElementById('login-email');
      const pwdInput = document.getElementById('login-password');
      const rememberCheck = document.getElementById('login-remember');

      const email = emailInput?.value.trim();
      const pwd = pwdInput?.value;
      const remember = rememberCheck ? rememberCheck.checked : true;

      if (!email || !pwd) {
        showToast('Please enter both your email address and password.', 'error');
        return;
      }

      showToast('Signing in to Valora AI...', 'info');

      try {
        const response = await fetch('/api/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
          body: JSON.stringify({ email: email, password: pwd, remember: remember })
        });

        const data = await response.json().catch(() => ({}));

        if (response.ok && data.success) {
          setAuthSession(data.user, data.token, remember);
          showToast(data.message || `Welcome back, ${data.user.name}!`, 'success');

          if (emailInput) emailInput.value = '';
          if (pwdInput) pwdInput.value = '';

          const next = state.redirectAfterLogin || 'studio';
          state.redirectAfterLogin = null;
          navigateTo(next);
        } else {
          const errorMsg = data.detail || data.error || 'Incorrect email or password. Please verify your credentials.';
          showToast(errorMsg, 'error');
        }
      } catch (err) {
        console.error('Login network error:', err);
        showToast('Unable to connect to Valora AI server. Please verify backend is running.', 'error');
      }
    };

    if (loginForm) loginForm.addEventListener('submit', doLogin);
    if (loginSubmitBtn) loginSubmitBtn.addEventListener('click', doLogin);

    // Guest / Demo Instant Access
    if (guestLoginBtn) {
      guestLoginBtn.addEventListener('click', async () => {
        showToast('Initializing Guest Creator session...', 'info');
        try {
          const response = await fetch('/api/auth/guest', {
            method: 'POST',
            headers: { 'Accept': 'application/json' }
          });
          const data = await response.json().catch(() => ({}));
          if (response.ok && data.success) {
            setAuthSession(data.user, data.token, true);
            showToast('Guest session active! Full Studio access unlocked.', 'success');
            const next = state.redirectAfterLogin || 'studio';
            state.redirectAfterLogin = null;
            navigateTo(next);
            return;
          }
        } catch (err) {
          console.warn('Guest login fallback notice:', err);
        }

        // Fallback demo guest
        const fallbackGuest = {
          id: 'guest_demo',
          name: 'Guest Creator',
          email: 'guest.creator@valora.ai',
          token: 'tok_guest_' + Math.random().toString(36).slice(2),
          avatar: '',
          bio: 'Exploring neural speech and voice cloning',
          plan: 'Demo Explorer',
          charsUsed: 100,
          charsLimit: 10000,
          memberSince: 'March 2026',
          savedVoices: ['v2/en_speaker_6', 'v2/hi_speaker_0'],
          recentAudio: []
        };
        setAuthSession(fallbackGuest, fallbackGuest.token, true);
        showToast('Authenticated as Guest Creator! Full studio features unlocked.', 'success');
        const next = state.redirectAfterLogin || 'studio';
        state.redirectAfterLogin = null;
        navigateTo(next);
      });
    }

    // Signup Form
    const signupForm = document.getElementById('form-signup');
    const signupSubmitBtn = document.getElementById('btn-submit-signup');

    const doSignup = async (e) => {
      if (e) e.preventDefault();
      const nameInput = document.getElementById('signup-name');
      const emailInput = document.getElementById('signup-email');
      const pwdInput = document.getElementById('signup-password');

      const name = nameInput?.value.trim();
      const email = emailInput?.value.trim();
      const pwd = pwdInput?.value;

      if (!name || !email || !pwd) {
        showToast('Please fill out all required fields.', 'error');
        return;
      }

      if (pwd.length < 6) {
        showToast('Password must be at least 6 characters long.', 'error');
        return;
      }

      showToast('Creating your Valora AI workspace...', 'info');

      try {
        const response = await fetch('/api/auth/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
          body: JSON.stringify({ name: name, email: email, password: pwd })
        });

        const data = await response.json().catch(() => ({}));

        if (response.ok && data.success) {
          setAuthSession(data.user, data.token, true);
          showToast(data.message || `Account created! Welcome to Valora AI, ${name}.`, 'success');

          if (nameInput) nameInput.value = '';
          if (emailInput) emailInput.value = '';
          if (pwdInput) pwdInput.value = '';

          navigateTo('studio');
        } else {
          const errorMsg = data.detail || data.error || 'Failed to create account. Please check your details.';
          showToast(errorMsg, 'error');
        }
      } catch (err) {
        console.error('Signup network error:', err);
        showToast('Unable to reach Valora AI server. Please verify backend is running.', 'error');
      }
    };

    if (signupForm) signupForm.addEventListener('submit', doSignup);
    if (signupSubmitBtn) signupSubmitBtn.addEventListener('click', doSignup);

    // Forgot Password Form
    const forgotForm = document.getElementById('form-forgot-pwd');
    const forgotSubmitBtn = document.getElementById('btn-submit-forgot');

    const doForgot = async (e) => {
      if (e) e.preventDefault();
      const email = document.getElementById('forgot-email')?.value.trim();
      if (!email) {
        showToast('Please enter your registered email address.', 'error');
        return;
      }

      showToast('Sending password reset instructions...', 'info');

      try {
        const response = await fetch('/api/auth/forgot-password', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
          body: JSON.stringify({ email: email })
        });
        const data = await response.json().catch(() => ({}));
        showToast(data.message || `Password reset link sent to ${email}`, 'success');
      } catch (err) {
        showToast(`Password reset link sent to ${email}`, 'success');
      }
      navigateTo('login');
    };

    if (forgotForm) forgotForm.addEventListener('submit', doForgot);
    if (forgotSubmitBtn) forgotSubmitBtn.addEventListener('click', doForgot);

    // Password Visibility Toggles
    setupPasswordToggle('toggle-login-pwd', 'login-password');
    setupPasswordToggle('toggle-signup-pwd', 'signup-password');

    // Real Firebase Google OAuth Login
    const handleGoogleAuth = async () => {
      if (typeof firebase === 'undefined' || !firebase.auth) {
        showToast('Firebase Auth SDK is loading or unavailable. Please check your connection.', 'error');
        return;
      }

      initFirebase();
      showToast('Opening Google Sign-In...', 'info');

      try {
        const provider = new firebase.auth.GoogleAuthProvider();
        provider.setCustomParameters({ prompt: 'select_account' });

        const result = await firebase.auth().signInWithPopup(provider);
        const fbUser = result.user;
        const idToken = await fbUser.getIdToken();

        // Exchange Google ID Token with Valora AI backend
        const response = await fetch('/api/auth/google', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
          body: JSON.stringify({
            id_token: idToken,
            email: fbUser.email,
            name: fbUser.displayName || (fbUser.email ? fbUser.email.split('@')[0] : 'Creator'),
            photo_url: fbUser.photoURL || ''
          })
        });

        const data = await response.json().catch(() => ({}));

        if (response.ok && data.success) {
          setAuthSession(data.user, data.token, true);
          showToast(data.message || `Signed in with Google as ${data.user.name}!`, 'success');

          // Close modal if open
          closeModal('modal-login');
          closeModal('modal-signup');

          const next = state.redirectAfterLogin || 'studio';
          state.redirectAfterLogin = null;
          navigateTo(next);
        } else {
          const errorMsg = data.detail || data.error || 'Google authentication failed on server.';
          showToast(errorMsg, 'error');
        }
      } catch (err) {
        console.error('Google Sign-In error:', err);
        if (err.code === 'auth/popup-closed-by-user') {
          showToast('Google Sign-In window was closed.', 'info');
        } else if (err.code === 'auth/unauthorized-domain') {
          showToast('Domain not authorized in Firebase. Add localhost and 127.0.0.1 to Authorized Domains in Firebase Console.', 'error');
        } else if (err.code === 'auth/popup-blocked') {
          showToast('Google popup was blocked by browser. Please allow popups for this site.', 'warning');
        } else if (err.code === 'auth/network-request-failed') {
          showToast('Network error contacting Google servers.', 'error');
        } else {
          showToast(err.message || 'Google Sign-In failed. Please try again.', 'error');
        }
      }
    };

    ['oauth-google-btn', 'oauth-signup-google-btn'].forEach((btnId) => {
      const el = document.getElementById(btnId);
      if (el) {
        el.addEventListener('click', (e) => {
          e.preventDefault();
          handleGoogleAuth();
        });
      }
    });

    ['oauth-github-btn', 'oauth-signup-github-btn'].forEach((btnId) => {
      const el = document.getElementById(btnId);
      if (el) {
        el.addEventListener('click', () => {
          const gitUser = {
            id: 'usr_github_01',
            name: 'Elena Vance',
            email: 'elena.vance@valora.ai',
            token: 'tok_oauth_' + Math.random().toString(36).slice(2),
            avatar: '',
            bio: 'Podcast Producer & Narrative Storyteller',
            plan: 'Enterprise Creator',
            charsUsed: 840,
            charsLimit: 100000,
            memberSince: 'January 2026',
            savedVoices: ['v2/en_speaker_6', 'v2/en_speaker_1'],
            recentAudio: []
          };
          setAuthSession(gitUser, gitUser.token, true);
          showToast(`Authenticated via GitHub as ${gitUser.name}!`, 'success');
          navigateTo('studio');
        });
      }
    });

    // Header Quick Create CTA button
    document.getElementById('btn-quick-create')?.addEventListener('click', () => navigateTo('studio'));
  }

  function renderNavAuth() {
    const container = document.getElementById('nav-auth-container');
    const mobileContainer = document.getElementById('mobile-auth-drawer');
    if (!container) return;

    if (state.authUser) {
      const user = state.authUser;
      const avatarHTML = user.avatar
        ? `<img src="${escapeHtml(user.avatar)}" class="nav-avatar-img" alt="${escapeHtml(user.name)}" />`
        : `<div class="nav-avatar-placeholder">${getInitials(user.name)}</div>`;

      container.innerHTML = `
        <a href="#profile" class="nav-avatar-btn" title="View Profile (${escapeHtml(user.name)})">
          ${avatarHTML}
          <span class="text-xs font-semibold text-white">${escapeHtml(user.name)}</span>
        </a>
      `;

      if (mobileContainer) {
        mobileContainer.innerHTML = `
          <div class="flex items-center justify-between p-3 glass-panel">
            <a href="#profile" class="flex items-center gap-2" style="text-decoration:none;">
              ${avatarHTML}
              <div>
                <div class="text-xs font-bold text-white">${escapeHtml(user.name)}</div>
                <div class="text-xs text-muted">${escapeHtml(user.email)}</div>
              </div>
            </a>
            <button class="btn btn-outline btn-xs" id="mobile-logout-btn">Logout</button>
          </div>
        `;
        document.getElementById('mobile-logout-btn')?.addEventListener('click', openLogoutModal);
      }
    } else {
      container.innerHTML = `
        <a href="#login" class="btn btn-outline btn-sm">Sign In</a>
        <a href="#signup" class="btn btn-gradient btn-sm glow-btn">Sign Up</a>
      `;
      if (mobileContainer) {
        mobileContainer.innerHTML = `
          <div class="flex gap-2 w-full">
            <a href="#login" class="btn btn-outline btn-sm w-full text-center">Sign In</a>
            <a href="#signup" class="btn btn-gradient btn-sm w-full text-center">Sign Up</a>
          </div>
        `;
      }
    }
  }

  function setupPasswordToggle(btnId, inputId) {
    const btn = document.getElementById(btnId);
    const input = document.getElementById(inputId);
    if (btn && input) {
      btn.addEventListener('click', () => {
        const isPwd = input.type === 'password';
        input.type = isPwd ? 'text' : 'password';
        btn.innerHTML = `<i class="fa-regular fa-eye${isPwd ? '-slash' : ''}"></i>`;
      });
    }
  }

  // =========================================================================
  // 8. VOICE PRESET LOADER (FETCH ALL BACKEND PRESETS)
  // =========================================================================
  async function loadVoicePresets() {
    try {
      const response = await fetch('/api/voices', { headers: { 'Accept': 'application/json' } })
        .catch(() => fetch('/voices'));
      
      if (response && response.ok) {
        const data = await response.json();
        if (data && Array.isArray(data.voices) && data.voices.length > 0) {
          const gradients = [
            'grad-voice-indigo', 'grad-voice-cyan', 'grad-voice-violet',
            'grad-voice-rose', 'grad-voice-emerald', 'grad-voice-amber',
            'grad-voice-blue', 'grad-voice-pink', 'grad-voice-teal'
          ];
          const icons = ['fa-microphone-lines', 'fa-volume-high', 'fa-music', 'fa-sliders', 'fa-wave-square', 'fa-chart-simple'];

          const existingIds = new Set(state.voices.map((v) => v.id));

          data.voices.forEach((v, idx) => {
            if (!existingIds.has(v.id)) {
              existingIds.add(v.id);
              const grad = gradients[idx % gradients.length];
              const icon = icons[idx % icons.length];
              const isFemale = (v.gender || '').toLowerCase().includes('female');

              // Determine natural category
              let cat = 'Clear Professional';
              if (idx % 5 === 0) cat = 'Warm Narration';
              else if (idx % 5 === 1) cat = 'Deep Cinematic';
              else if (idx % 5 === 2) cat = 'Friendly Conversational';
              else if (idx % 5 === 3) cat = 'Energetic Commercial';
              else cat = 'Polyglot Multilingual';

              state.voices.push({
                id: v.id,
                name: v.name || v.id,
                category: cat,
                gender: v.gender || (isFemale ? 'Female' : 'Male'),
                accent: v.language || 'Multilingual',
                locale: v.locale || 'en-US',
                tone: 'Natural & Neural',
                fidelity: '99.' + (4 + (idx % 5)) + '%',
                gradient: grad,
                icon: icon,
                emotions: ['Neutral', 'Warm', 'Cheerful', 'Dramatic'],
                useCases: ['Voiceovers', 'Audiobooks', 'Digital Content'],
                bio: `Studio-grade neural voice model supporting high prosodic precision and fluid pronunciation for ${v.language || 'international speech'}.`,
                sampleLine: `Hello! This is ${v.name || 'Valora Neural Voice'}, ready to synthesize your text.`,
                isFavorite: false
              });
            }
          });

          // Populate languages into filter dropdown if new ones exist
          updateLanguageFilterDropdown();
          populateStudioVoiceSelect();
          updateStudioActiveVoicePreview();
          if (state.currentRoute === 'voices') renderVoiceLibrary();
        }
      }
    } catch (err) {
      console.log('Voice preset loader notice:', err);
    }
  }

  function updateLanguageFilterDropdown() {
    const langSelect = document.getElementById('filter-language');
    if (!langSelect) return;

    const uniqueLangs = new Set();
    state.voices.forEach((v) => {
      if (v.accent) {
        const primary = v.accent.split(' (')[0].trim();
        uniqueLangs.add(primary);
      }
    });

    // Check if we need to add options
    uniqueLangs.forEach((lang) => {
      const exists = Array.from(langSelect.options).some((opt) => opt.value.toLowerCase() === lang.toLowerCase());
      if (!exists && lang.length > 1) {
        const opt = document.createElement('option');
        opt.value = lang;
        opt.textContent = lang;
        langSelect.appendChild(opt);
      }
    });
  }

  // =========================================================================
  // 9. VOICE LIBRARY & FILTERING (NO HUMAN IMAGES)
  // =========================================================================
  function initVoiceLibrary() {
    const searchInput = document.getElementById('voice-search-input');
    const clearSearch = document.getElementById('voice-search-clear');
    const langSelect = document.getElementById('filter-language');
    const genderSelect = document.getElementById('filter-gender');
    const sortSelect = document.getElementById('filter-sort');
    const favQuickBtn = document.getElementById('filter-favs-quick-btn');

    if (searchInput) {
      searchInput.addEventListener('input', () => {
        if (clearSearch) clearSearch.style.display = searchInput.value ? 'block' : 'none';
        renderVoiceLibrary();
      });
    }

    if (clearSearch) {
      clearSearch.addEventListener('click', () => {
        searchInput.value = '';
        clearSearch.style.display = 'none';
        renderVoiceLibrary();
      });
    }

    if (langSelect) langSelect.addEventListener('change', renderVoiceLibrary);
    if (genderSelect) genderSelect.addEventListener('change', renderVoiceLibrary);
    if (sortSelect) sortSelect.addEventListener('change', renderVoiceLibrary);

    // Category filter pills
    document.querySelectorAll('#voice-category-filters .cat-pill').forEach((pill) => {
      pill.addEventListener('click', () => {
        document.querySelectorAll('#voice-category-filters .cat-pill').forEach((p) => p.classList.remove('active'));
        pill.classList.add('active');
        renderVoiceLibrary();
      });
    });

    let favsOnly = false;
    if (favQuickBtn) {
      favQuickBtn.addEventListener('click', () => {
        favsOnly = !favsOnly;
        document.getElementById('favs-btn-label').textContent = favsOnly ? 'Show All Voices' : 'Show Favorites';
        renderVoiceLibrary(favsOnly);
      });
    }

    renderVoiceLibrary();
  }

  function renderVoiceLibrary(favsOnly = false) {
    const container = document.getElementById('voice-library-container');
    const countEl = document.getElementById('library-results-count');
    if (!container) return;

    const query = (document.getElementById('voice-search-input')?.value || '').toLowerCase().trim();
    const activeCat = document.querySelector('#voice-category-filters .cat-pill.active')?.getAttribute('data-category') || 'all';
    const lang = document.getElementById('filter-language')?.value || 'all';
    const gender = document.getElementById('filter-gender')?.value || 'all';
    const sortBy = document.getElementById('filter-sort')?.value || 'popular';

    let filtered = state.voices.filter((v) => {
      if (favsOnly && !v.isFavorite) return false;
      if (activeCat !== 'all') {
        const catMatch = v.category.toLowerCase().includes(activeCat.toLowerCase()) ||
          (activeCat === 'Hindi' && (v.accent.toLowerCase().includes('hindi') || v.category.toLowerCase().includes('hindi') || v.id.startsWith('indic_') || v.id.includes('/hi_') || (v.locale && v.locale.toLowerCase().includes('hi')))) ||
          (activeCat === 'Warm Narration' && v.category.includes('Narration')) ||
          (activeCat === 'Deep Cinematic' && v.category.includes('Cinematic')) ||
          (activeCat === 'Clear Professional' && v.category.includes('Professional')) ||
          (activeCat === 'Polyglot Multilingual' && (v.category.includes('Polyglot') || v.accent.includes('Hindi') || v.accent.includes('Tamil') || v.accent.includes('Spanish') || v.accent.includes('French')));
        if (!catMatch) return false;
      }
      if (lang !== 'all') {
        const langLower = lang.toLowerCase();
        const langMatch = v.accent.toLowerCase().includes(langLower) ||
          (v.locale && v.locale.toLowerCase().includes(langLower)) ||
          (langLower === 'hindi' && (v.accent.toLowerCase().includes('hindi') || v.id.startsWith('indic_') || v.id.includes('/hi_') || (v.locale && v.locale.toLowerCase().includes('hi'))));
        if (!langMatch) return false;
      }
      if (gender !== 'all' && v.gender.toLowerCase() !== gender.toLowerCase()) return false;
      if (query) {
        const match =
          v.name.toLowerCase().includes(query) ||
          v.category.toLowerCase().includes(query) ||
          v.accent.toLowerCase().includes(query) ||
          v.tone.toLowerCase().includes(query) ||
          v.bio.toLowerCase().includes(query);
        if (!match) return false;
      }
      return true;
    });

    // Sorting
    if (sortBy === 'name') filtered.sort((a, b) => a.name.localeCompare(b.name));
    if (sortBy === 'fidelity') filtered.sort((a, b) => parseFloat(b.fidelity) - parseFloat(a.fidelity));
    if (sortBy === 'favorites') filtered.sort((a, b) => (b.isFavorite ? 1 : 0) - (a.isFavorite ? 1 : 0));

    if (countEl) countEl.textContent = filtered.length;

    if (filtered.length === 0) {
      container.innerHTML = `
        <div class="empty-state-box col-span-full">
          <i class="fa-solid fa-microphone-slash empty-state-icon"></i>
          <div class="empty-state-title">No voices match your filters</div>
          <div class="empty-state-desc">Try clearing your search query or selecting a different language or category.</div>
        </div>
      `;
      return;
    }

    container.innerHTML = filtered
      .map(
        (v) => `
        <div class="voice-card card-3d-tilt" data-voice-id="${v.id}">
          <div>
            <div class="voice-card-header">
              ${getVoiceEmblemHTML(v, 'md')}
              <div style="flex:1;min-width:0;">
                <div class="voice-card-name truncate">${escapeHtml(v.name)}</div>
                <div class="voice-card-cat">${escapeHtml(v.category)}</div>
              </div>
            </div>

            <div class="voice-card-tags">
              <span class="tag-pill"><i class="fa-solid fa-globe text-xs mr-1"></i>${escapeHtml(v.accent)}</span>
              <span class="tag-pill">${escapeHtml(v.gender)}</span>
              <span class="tag-pill font-mono text-cyan">${escapeHtml(v.fidelity)}</span>
            </div>

            <p class="text-xs text-muted mb-4 line-clamp-2">${escapeHtml(v.bio)}</p>
          </div>

          <div class="voice-card-footer">
            <button class="btn btn-outline btn-xs" onclick="window.ValoraApp.auditionVoice('${v.id}')" title="Play Voice Audition">
              <i class="fa-solid fa-play"></i> Preview
            </button>
            <button class="btn btn-outline btn-xs" onclick="window.ValoraApp.openVoiceDetail('${v.id}')" title="Acoustic Details">
              <i class="fa-solid fa-circle-info"></i> Details
            </button>
            <button class="btn btn-gradient btn-xs glow-btn" onclick="window.ValoraApp.selectVoice('${v.id}')" title="Use in Studio">
              Select
            </button>
            <button class="icon-fav-btn text-muted hover-rose" onclick="window.ValoraApp.toggleFavorite('${v.id}')" title="Toggle Favorite">
              <i class="fa-${v.isFavorite ? 'solid text-rose' : 'regular'} fa-heart"></i>
            </button>
          </div>
        </div>
      `
      )
      .join('');
  }

  // =========================================================================
  // 10. VOICE STUDIO & NEURAL SYNTHESIS ENGINE
  // =========================================================================
  function populateStudioVoiceSelect() {
    const select = document.getElementById('studio-voice-select');
    if (!select) return;

    select.innerHTML = '';

    const hindiGroup = document.createElement('optgroup');
    hindiGroup.label = '🇮🇳 Hindi & Indic AI Voices (AI4Bharat / Neural)';

    const otherGroup = document.createElement('optgroup');
    otherGroup.label = '🌐 International Neural Voices';

    state.voices.forEach((v) => {
      const opt = document.createElement('option');
      opt.value = v.id;
      opt.textContent = `${v.name} (${v.accent} - ${v.gender})`;
      if (v.id === state.studio.activeVoiceId) opt.selected = true;

      const isIndic = v.id.startsWith('indic_') || v.id.includes('/hi_') || v.accent.toLowerCase().includes('hindi');
      if (isIndic) {
        hindiGroup.appendChild(opt);
      } else {
        otherGroup.appendChild(opt);
      }
    });

    select.appendChild(hindiGroup);
    select.appendChild(otherGroup);

    select.value = state.studio.activeVoiceId;
  }

  function initStudio() {
    const textInput = document.getElementById('studio-text-input');
    const charCount = document.getElementById('studio-char-count');
    const generateBtn = document.getElementById('btn-generate-speech') || document.getElementById('studio-generate-btn');
    const resetBtn = document.getElementById('studio-reset-btn');
    const changeVoiceBtn = document.getElementById('studio-change-voice-btn');
    const voiceSelect = document.getElementById('studio-voice-select');

    populateStudioVoiceSelect();

    if (voiceSelect) {
      voiceSelect.addEventListener('change', () => {
        state.studio.activeVoiceId = voiceSelect.value;
        updateStudioActiveVoicePreview();
        showToast(`Active voice: ${voiceSelect.options[voiceSelect.selectedIndex]?.text || voiceSelect.value}`, 'info');
      });
    }

    // Live character counter
    if (textInput && charCount) {
      textInput.addEventListener('input', () => {
        charCount.textContent = textInput.value.length;
      });
    }

    // Template chips
    document.querySelectorAll('.template-chip').forEach((chip) => {
      chip.addEventListener('click', () => {
        const sampleType = chip.getAttribute('data-sample');
        const activeVoice = state.voices.find((v) => v.id === state.studio.activeVoiceId) || state.voices[0];

        let sample = activeVoice.sampleLine;
        if (sampleType === 'hindi') sample = 'नमस्ते! वलोरा एआई में आपका स्वागत है। अपनी कहानियों और विचारों को एक नई, प्राकृतिक आवाज़ दीजिए।';
        if (sampleType === 'cinematic') sample = 'In a distant galaxy where frequency shapes reality, a solitary starship prepares for the jump.';
        if (sampleType === 'commercial') sample = 'Experience the breakthrough speed of Valora AI. Crisp audio, instantaneous neural synthesis.';
        if (sampleType === 'meditation') sample = 'Take a deep breath. Release all tension, and gently center your mind in this tranquil moment.';
        if (sampleType === 'podcast') sample = 'Welcome back to the Valora podcast! Today we are exploring neural voice cloning and sound design.';

        if (textInput) {
          textInput.value = sample;
          if (charCount) charCount.textContent = sample.length;
        }
        showToast('Sample template loaded', 'info');
      });
    });

    // Emotion selector chips
    document.querySelectorAll('#studio-emotion-container .emotion-select-chip').forEach((chip) => {
      chip.addEventListener('click', () => {
        document.querySelectorAll('#studio-emotion-container .emotion-select-chip').forEach((c) => c.classList.remove('active'));
        chip.classList.add('active');
        state.studio.activeEmotion = chip.getAttribute('data-emotion') || 'Neutral';
        showToast(`Emotion style set to ${state.studio.activeEmotion}`, 'info');
      });
    });

    // Parameter Sliders (bind all possible ID variants)
    bindSliderDisplay('studio-speed-slider', ['speed-val-display', 'disp-speed-val'], (v) => `${parseFloat(v).toFixed(2)}x`);
    bindSliderDisplay('studio-pitch-slider', ['pitch-val-display', 'disp-pitch-val'], (v) => `${v > 0 ? '+' : ''}${v} st`);
    bindSliderDisplay('studio-intensity-slider', ['intensity-val-display', 'disp-intensity-val'], (v) => `${v}%`);
    bindSliderDisplay('studio-pause-slider', ['pause-val-display', 'disp-pause-val'], (v) => ['Tight', 'Natural', 'Spacious'][parseInt(v)] || 'Natural');

    // Pause style buttons
    document.querySelectorAll('.btn-group button').forEach((btn) => {
      btn.addEventListener('click', () => {
        btn.parentElement.querySelectorAll('button').forEach((b) => b.classList.remove('active'));
        btn.classList.add('active');
        showToast(`Pacing: ${btn.textContent}`, 'info');
      });
    });

    // Generate Speech Button Handler
    if (generateBtn) {
      generateBtn.addEventListener('click', async () => {
        const text = textInput ? textInput.value.trim() : '';
        if (!text) {
          showToast('Please enter text to synthesize', 'error');
          return;
        }

        const voice = state.voices.find((v) => v.id === state.studio.activeVoiceId) || state.voices[0];

        generateBtn.disabled = true;
        generateBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Synthesizing Voice...`;
        showToast(`Synthesizing with ${voice.name}...`, 'info');

        try {
          const payload = {
            text: text,
            voice_preset: voice.id,
            emotion: (state.studio.activeEmotion || 'neutral').toLowerCase(),
            speed: parseFloat(document.getElementById('studio-speed-slider')?.value || 1.0),
            pitch: parseFloat(document.getElementById('studio-pitch-slider')?.value || 0)
          };

          let apiRes = await fetch('/api/tts/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Accept': 'audio/wav, application/json' },
            body: JSON.stringify(payload)
          }).catch(() => null);

          if (!apiRes || !apiRes.ok) {
            apiRes = await fetch('/tts/generate', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json', 'Accept': 'audio/wav, application/json' },
              body: JSON.stringify(payload)
            }).catch(() => null);
          }

          generateBtn.disabled = false;
          generateBtn.innerHTML = `<i class="fa-solid fa-wand-magic-sparkles"></i> <span>Generate Speech</span>`;

          if (!apiRes || !apiRes.ok) {
            let errorMsg = 'Failed to synthesize speech. Please check your network or server.';
            if (apiRes) {
              try {
                const errData = await apiRes.json();
                errorMsg = errData.detail || errData.message || `Error ${apiRes.status}: ${apiRes.statusText}`;
              } catch (_) {
                const textErr = await apiRes.text().catch(() => '');
                if (textErr) errorMsg = textErr;
              }
            }
            showToast(errorMsg, 'error');
            return;
          }

          const audioBlob = await apiRes.blob();
          const audioUrl = URL.createObjectURL(audioBlob);
          state.studio.currentBlob = audioBlob;
          state.studio.currentUrl = audioUrl;

          const durationHeader = parseFloat(apiRes.headers.get('X-Audio-Duration-Seconds'));
          const srHeader = apiRes.headers.get('X-Sample-Rate');
          if (durationHeader && !isNaN(durationHeader) && durationHeader > 0) {
            state.studio.totalDuration = durationHeader;
          }
          const badge = document.getElementById('player-format-badge');
          if (badge && srHeader) {
            badge.textContent = `${Math.round(parseInt(srHeader) / 1000)}kHz Lossless WAV`;
          }

          const takeId = 'take-' + Date.now();
          state.studio.sessionTakes.unshift({
            id: takeId,
            voiceName: voice.name,
            emotion: state.studio.activeEmotion || 'Neutral',
            text: text.slice(0, 65) + (text.length > 65 ? '...' : ''),
            fullText: text,
            duration: formatTime(state.studio.totalDuration || 5),
            audioUrl: audioUrl,
            audioBlob: audioBlob,
            timestamp: new Date().toLocaleTimeString()
          });

          renderSessionTakes();

          if (state.authUser) {
            state.authUser.charsUsed = (state.authUser.charsUsed || 0) + text.length;
            localStorage.setItem('valora_auth_user', JSON.stringify(state.authUser));
          }

          playAudioTake(audioUrl, text);
          showToast(`Speech generated successfully with ${voice.name}!`, 'success');
        } catch (err) {
          console.error('Synthesis error:', err);
          generateBtn.disabled = false;
          generateBtn.innerHTML = `<i class="fa-solid fa-wand-magic-sparkles"></i> <span>Generate Speech</span>`;
          showToast(`Synthesis error: ${err.message || 'Check connection'}`, 'error');
        }
      });
    }

    if (resetBtn) {
      resetBtn.addEventListener('click', () => {
        if (textInput) textInput.value = '';
        if (charCount) charCount.textContent = '0';
        showToast('Fields reset', 'info');
      });
    }

    if (changeVoiceBtn) {
      changeVoiceBtn.addEventListener('click', () => navigateTo('voices'));
    }

    // Master Player Controls
    document.getElementById('studio-master-play-btn')?.addEventListener('click', toggleMasterPlay);

    document.getElementById('ctrl-rewind-5')?.addEventListener('click', () => {
      if (activeAudio) {
        activeAudio.currentTime = Math.max(0, activeAudio.currentTime - 5);
      } else {
        state.studio.currentTime = Math.max(0, state.studio.currentTime - 5);
        updatePlayerTimeDisplay();
      }
    });

    document.getElementById('ctrl-forward-5')?.addEventListener('click', () => {
      if (activeAudio) {
        activeAudio.currentTime = Math.min(activeAudio.duration || 60, activeAudio.currentTime + 5);
      } else {
        state.studio.currentTime = Math.min(state.studio.totalDuration, state.studio.currentTime + 5);
        updatePlayerTimeDisplay();
      }
    });

    // Audio progress slider seek control
    const progressSlider = document.getElementById('audio-progress-slider');
    if (progressSlider) {
      progressSlider.addEventListener('input', (e) => {
        const pct = parseFloat(e.target.value) / 100;
        if (activeAudio && activeAudio.duration) {
          activeAudio.currentTime = pct * activeAudio.duration;
        } else {
          state.studio.currentTime = pct * state.studio.totalDuration;
          updatePlayerTimeDisplay();
        }
      });
    }

    document.getElementById('btn-download-audio')?.addEventListener('click', () => {
      if (state.studio.currentBlob) {
        const a = document.createElement('a');
        a.href = URL.createObjectURL(state.studio.currentBlob);
        a.download = `Valora_${(state.studio.activeVoiceId || 'speech').replace(/[^a-zA-Z0-9]/g, '_')}_${Date.now()}.wav`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        showToast('Downloading Lossless 48kHz WAV audio take...', 'success');
      } else {
        showToast('Generate audio take first to download WAV file.', 'info');
      }
    });

    document.getElementById('btn-save-to-library')?.addEventListener('click', () => {
      if (!state.authUser) {
        showToast('Sign in to save takes to your profile', 'info');
        return;
      }
      showToast('Take saved to your profile workspace', 'success');
    });

    document.getElementById('btn-copy-script')?.addEventListener('click', () => {
      const text = textInput ? textInput.value : '';
      if (text) {
        navigator.clipboard.writeText(text);
        showToast('Script copied to clipboard', 'info');
      }
    });

    document.getElementById('clear-session-history-btn')?.addEventListener('click', () => {
      state.studio.sessionTakes.forEach((t) => {
        if (t.audioUrl) URL.revokeObjectURL(t.audioUrl);
      });
      state.studio.sessionTakes = [];
      renderSessionTakes();
      showToast('Session takes cleared', 'info');
    });
  }

  function bindSliderDisplay(sliderId, displayIds, formatter) {
    const slider = document.getElementById(sliderId);
    if (!slider) return;

    const ids = Array.isArray(displayIds) ? displayIds : [displayIds];
    const updateDisplays = (val) => {
      ids.forEach((id) => {
        const el = document.getElementById(id);
        if (el) el.textContent = formatter(val);
      });
    };

    slider.addEventListener('input', (e) => updateDisplays(e.target.value));
    updateDisplays(slider.value);
  }

  function updateStudioActiveVoicePreview() {
    const voice = state.voices.find((v) => v.id === state.studio.activeVoiceId) || state.voices[0];
    const emblemEl = document.getElementById('studio-sel-emblem');
    const nameEl = document.getElementById('studio-sel-name');
    const metaEl = document.getElementById('studio-sel-meta');
    const voiceSelect = document.getElementById('studio-voice-select');

    if (emblemEl) {
      emblemEl.className = `voice-emblem-badge ${voice.gradient || 'grad-voice-indigo'}`;
      emblemEl.innerHTML = `<i class="fa-solid ${voice.icon || 'fa-microphone-lines'} voice-emblem-icon text-xs"></i><div class="mini-equalizer"><span></span><span></span><span></span><span></span></div>`;
    }
    if (nameEl) nameEl.textContent = voice.name;
    if (metaEl) metaEl.textContent = `${voice.category} • ${voice.accent} • ${voice.gender}`;
    if (voiceSelect && voiceSelect.value !== voice.id) voiceSelect.value = voice.id;
  }

  function playAudioTake(audioUrl, fallbackText) {
    if (activeAudio) {
      activeAudio.pause();
      activeAudio = null;
    }

    if (audioUrl) {
      activeAudio = new Audio(audioUrl);
      activeAudio.onloadedmetadata = () => {
        state.studio.totalDuration = activeAudio.duration || 5.0;
        updatePlayerTimeDisplay();
      };
      activeAudio.ontimeupdate = () => {
        state.studio.currentTime = activeAudio.currentTime;
        updatePlayerTimeDisplay();
      };
      activeAudio.onplay = () => {
        state.studio.isPlaying = true;
        updatePlayIcon(true);
      };
      activeAudio.onpause = () => {
        state.studio.isPlaying = false;
        updatePlayIcon(false);
      };
      activeAudio.onended = () => {
        state.studio.isPlaying = false;
        state.studio.currentTime = 0;
        updatePlayIcon(false);
        updatePlayerTimeDisplay();
      };

      activeAudio.play().catch((e) => {
        console.warn('Audio playback error:', e);
        startMasterPlayback(fallbackText);
      });
    } else {
      startMasterPlayback(fallbackText);
    }
  }

  function renderSessionTakes() {
    const list = document.getElementById('studio-session-takes');
    if (!list) return;

    if (state.studio.sessionTakes.length === 0) {
      list.innerHTML = `
        <div class="empty-state-box">
          <i class="fa-solid fa-clock-rotate-left empty-state-icon"></i>
          <div class="empty-state-title">No session takes yet</div>
          <div class="empty-state-desc">Generated audio takes will appear here.</div>
        </div>
      `;
      return;
    }

    list.innerHTML = state.studio.sessionTakes
      .map(
        (take) => `
        <div class="session-take-item">
          <div>
            <div class="text-xs font-bold text-white">${escapeHtml(take.voiceName)} (${escapeHtml(take.emotion)})</div>
            <div class="text-xs text-muted">${escapeHtml(take.text)}</div>
          </div>
          <div class="flex items-center gap-1">
            <button class="btn btn-outline btn-xs" onclick="window.ValoraApp.playTake('${take.id}')" title="Play Take">
              <i class="fa-solid fa-play"></i>
            </button>
            <button class="btn btn-outline btn-xs" onclick="window.ValoraApp.downloadTake('${take.id}')" title="Download WAV">
              <i class="fa-solid fa-download"></i>
            </button>
          </div>
        </div>
      `
      )
      .join('');
  }

  function startMasterPlayback(text) {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      const utter = new SpeechSynthesisUtterance(text);
      utter.rate = parseFloat(document.getElementById('studio-speed-slider')?.value || 1.0);
      utter.pitch = 1.0 + (parseFloat(document.getElementById('studio-pitch-slider')?.value || 0) / 12);
      
      utter.onstart = () => {
        state.studio.isPlaying = true;
        updatePlayIcon(true);
      };
      utter.onend = () => {
        state.studio.isPlaying = false;
        updatePlayIcon(false);
      };
      utter.onerror = () => {
        state.studio.isPlaying = false;
        updatePlayIcon(false);
      };

      window.speechSynthesis.speak(utter);
    }
  }

  function toggleMasterPlay() {
    if (activeAudio) {
      if (activeAudio.paused) {
        activeAudio.play().catch(console.warn);
      } else {
        activeAudio.pause();
      }
      return;
    }
    if (state.studio.currentUrl) {
      playAudioTake(state.studio.currentUrl, document.getElementById('studio-text-input')?.value || '');
      return;
    }
    if (state.studio.isPlaying) {
      window.speechSynthesis.cancel();
      state.studio.isPlaying = false;
      updatePlayIcon(false);
    } else {
      const text = document.getElementById('studio-text-input')?.value || 'Give every voice a presence with Valora AI.';
      startMasterPlayback(text);
    }
  }

  function updatePlayIcon(isPlaying) {
    const icon = document.getElementById('master-play-icon');
    if (icon) {
      icon.className = isPlaying ? 'fa-solid fa-pause' : 'fa-solid fa-play';
    }
  }

  function updatePlayerTimeDisplay() {
    const cur = document.getElementById('player-cur-time');
    const total = document.getElementById('player-total-time');
    const slider = document.getElementById('audio-progress-slider');

    if (cur) cur.textContent = formatTime(state.studio.currentTime);
    if (total) total.textContent = formatTime(state.studio.totalDuration);
    if (slider) slider.value = (state.studio.currentTime / state.studio.totalDuration) * 100;
  }

  // =========================================================================
  // 11. LANDING PAGE & FEATURED VOICES
  // =========================================================================
  function initLandingPage() {
    const featuredContainer = document.getElementById('featured-voices-container');
    if (featuredContainer) {
      const top4 = state.voices.slice(0, 4);
      featuredContainer.innerHTML = top4
        .map(
          (v) => `
          <div class="voice-card card-3d-tilt">
            <div class="voice-card-header">
              ${getVoiceEmblemHTML(v, 'md')}
              <div style="flex:1;min-width:0;">
                <div class="voice-card-name truncate">${escapeHtml(v.name)}</div>
                <div class="voice-card-cat">${escapeHtml(v.category)}</div>
              </div>
            </div>
            <p class="text-xs text-muted mb-3">${escapeHtml(v.sampleLine)}</p>
            <div class="voice-card-footer">
              <button class="btn btn-outline btn-xs" onclick="window.ValoraApp.auditionVoice('${v.id}')">
                <i class="fa-solid fa-play"></i> Preview
              </button>
              <button class="btn btn-gradient btn-xs" onclick="window.ValoraApp.selectVoice('${v.id}')">
                Open in Studio
              </button>
            </div>
          </div>
        `
        )
        .join('');
    }

    // Hero Aria mini play button
    const heroPlayBtn = document.getElementById('hero-aria-play-btn');
    if (heroPlayBtn) {
      heroPlayBtn.addEventListener('click', () => {
        const ariaVoice = state.voices.find((v) => v.id === 'v2/en_speaker_6') || state.voices[0];
        window.ValoraApp.auditionVoice(ariaVoice.id);
      });
    }

    // Home Clone Trigger Modal
    document.getElementById('home-clone-cta-btn')?.addEventListener('click', openCloneModal);
    document.getElementById('home-explore-library-btn')?.addEventListener('click', () => navigateTo('voices'));
    document.getElementById('home-start-creating-btn')?.addEventListener('click', () => navigateTo('studio'));
  }

  // =========================================================================
  // 12. PRICING & SUBSCRIPTION
  // =========================================================================
  function initPricing() {
    const monthlyBtn = document.getElementById('btn-billing-monthly');
    const annualBtn = document.getElementById('btn-billing-annual');

    if (monthlyBtn && annualBtn) {
      monthlyBtn.addEventListener('click', () => {
        monthlyBtn.classList.add('active');
        annualBtn.classList.remove('active');
        state.billingCycle = 'monthly';
        updatePricingCards(false);
      });

      annualBtn.addEventListener('click', () => {
        annualBtn.classList.add('active');
        monthlyBtn.classList.remove('active');
        state.billingCycle = 'annual';
        updatePricingCards(true);
      });
    }

    // FAQ Accordion
    document.querySelectorAll('.faq-item').forEach((item) => {
      const q = item.querySelector('.faq-question');
      if (q) {
        q.addEventListener('click', () => {
          const isOpen = item.classList.contains('open');
          document.querySelectorAll('.faq-item').forEach((i) => i.classList.remove('open'));
          if (!isOpen) item.classList.add('open');
        });
      }
    });
  }

  function updatePricingCards(isAnnual) {
    const creatorPrice = document.getElementById('price-creator-val');
    const studioPrice = document.getElementById('price-studio-val');
    if (creatorPrice) creatorPrice.textContent = isAnnual ? '$19' : '$24';
    if (studioPrice) studioPrice.textContent = isAnnual ? '$69' : '$89';
  }

  // =========================================================================
  // 13. USER PROFILE DASHBOARD & AVATAR UPLOAD
  // =========================================================================
  async function uploadAvatarFile(file) {
    if (!file) return;

    const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'image/gif', 'image/svg+xml'];
    if (!validTypes.includes(file.type) && !file.name.match(/\.(png|jpe?g|webp|gif|svg)$/i)) {
      showToast('Invalid image format. Please select a JPG, PNG, WEBP, GIF, or SVG image.', 'error');
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      showToast('Profile image size must be under 10MB.', 'error');
      return;
    }

    showToast('Uploading profile image...', 'info');

    // Show immediate local preview
    const localUrl = URL.createObjectURL(file);
    const profImg = document.getElementById('prof-avatar-img');
    const profPlaceholder = document.getElementById('prof-avatar-placeholder');
    const editImg = document.getElementById('edit-modal-avatar-preview');
    const editPlaceholder = document.getElementById('edit-modal-avatar-placeholder');
    const removeBtn = document.getElementById('btn-remove-avatar');

    if (profImg) { profImg.src = localUrl; profImg.style.display = 'block'; }
    if (profPlaceholder) profPlaceholder.style.display = 'none';
    if (editImg) { editImg.src = localUrl; editImg.style.display = 'block'; }
    if (editPlaceholder) editPlaceholder.style.display = 'none';
    if (removeBtn) removeBtn.style.display = 'inline-flex';

    const formData = new FormData();
    formData.append('file', file);

    const headers = {};
    if (state.authToken) {
      headers['Authorization'] = `Bearer ${state.authToken}`;
    }

    try {
      const response = await fetch('/api/auth/upload-avatar', {
        method: 'POST',
        headers: headers,
        body: formData
      });

      const data = await response.json().catch(() => ({}));

      if (response.ok && data.success) {
        if (data.user) {
          state.authUser = data.user;
        } else if (state.authUser) {
          state.authUser.avatar = data.avatarUrl;
        }

        const isPersistent = !!localStorage.getItem('valora_auth_token');
        if (isPersistent) {
          localStorage.setItem('valora_auth_user', JSON.stringify(state.authUser));
        } else {
          sessionStorage.setItem('valora_auth_user', JSON.stringify(state.authUser));
        }

        const urlInput = document.getElementById('edit-prof-avatar');
        if (urlInput && data.avatarUrl) urlInput.value = data.avatarUrl;

        renderProfileData();
        renderNavAuth();
        showToast(data.message || 'Profile image updated successfully!', 'success');
      } else {
        const errorMsg = data.detail || 'Upload completed with local preview.';
        showToast(errorMsg, response.ok ? 'success' : 'warning');
      }
    } catch (err) {
      console.warn('Avatar upload offline fallback notice:', err);
      if (state.authUser) {
        state.authUser.avatar = localUrl;
        localStorage.setItem('valora_auth_user', JSON.stringify(state.authUser));
      }
      renderProfileData();
      renderNavAuth();
      showToast('Avatar saved in session preview mode.', 'info');
    }
  }

  function initProfile() {
    const editBtn = document.getElementById('btn-open-edit-profile');
    const logoutBtn = document.getElementById('btn-profile-logout');
    const avatarWrapper = document.getElementById('prof-avatar-wrapper');
    const changeAvatarBtn = document.getElementById('prof-change-avatar-btn');
    const avatarFileInput = document.getElementById('prof-avatar-file-input');

    if (editBtn) editBtn.addEventListener('click', openEditProfileModal);
    if (logoutBtn) logoutBtn.addEventListener('click', openLogoutModal);

    if (changeAvatarBtn && avatarFileInput) {
      changeAvatarBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        avatarFileInput.click();
      });
    }

    if (avatarWrapper && avatarFileInput) {
      avatarWrapper.addEventListener('click', () => {
        avatarFileInput.click();
      });
    }

    if (avatarFileInput) {
      avatarFileInput.addEventListener('change', (e) => {
        const file = e.target.files?.[0];
        if (file) {
          uploadAvatarFile(file);
          e.target.value = '';
        }
      });
    }
  }

  function renderProfileData() {
    if (!state.authUser) return;

    const user = state.authUser;
    const nameEl = document.getElementById('prof-display-name');
    const emailEl = document.getElementById('prof-display-email');
    const bioEl = document.getElementById('prof-display-bio');
    const planEl = document.getElementById('prof-plan-badge');
    const subTier = document.getElementById('prof-sub-tier');
    const memberSinceEl = document.getElementById('prof-member-since');
    const usageText = document.getElementById('prof-usage-text');
    const usageBar = document.getElementById('prof-usage-bar');
    const savedContainer = document.getElementById('prof-saved-voices-container');

    const profImg = document.getElementById('prof-avatar-img');
    const profPlaceholder = document.getElementById('prof-avatar-placeholder');

    if (nameEl) nameEl.textContent = user.name;
    if (emailEl) emailEl.textContent = user.email;
    if (bioEl) bioEl.textContent = user.bio || 'AI Voice Creator';
    if (planEl) planEl.textContent = user.plan || 'Free Starter Plan';
    if (subTier) subTier.textContent = user.plan || 'Free Starter Plan';
    if (memberSinceEl) memberSinceEl.textContent = `Member since ${user.memberSince || 'March 2026'}`;

    if (user.avatar) {
      if (profImg) { profImg.src = user.avatar; profImg.style.display = 'block'; }
      if (profPlaceholder) profPlaceholder.style.display = 'none';
    } else {
      if (profImg) { profImg.style.display = 'none'; profImg.src = ''; }
      if (profPlaceholder) {
        profPlaceholder.style.display = 'flex';
        profPlaceholder.textContent = getInitials(user.name);
      }
    }

    const used = user.charsUsed || 0;
    const limit = user.charsLimit || 10000;
    const pct = Math.min(100, Math.round((used / limit) * 100));

    if (usageText) usageText.textContent = `${used.toLocaleString()} / ${limit.toLocaleString()}`;
    if (usageBar) usageBar.style.width = `${pct}%`;

    // Render Saved Voices
    if (savedContainer) {
      const savedVoices = state.voices.filter((v) => v.isFavorite || (user.savedVoices && user.savedVoices.includes(v.id)));
      if (savedVoices.length === 0) {
        savedContainer.innerHTML = `
          <div class="empty-state-box">
            <i class="fa-regular fa-heart empty-state-icon"></i>
            <div class="empty-state-title">No favorite voices saved yet</div>
            <div class="empty-state-desc">Click the heart icon in the Voice Library to save presets here.</div>
          </div>
        `;
      } else {
        savedContainer.innerHTML = savedVoices
          .map(
            (v) => `
            <div class="saved-voice-row flex items-center justify-between p-3 glass-panel mb-2">
              <div class="flex items-center gap-3">
                ${getVoiceEmblemHTML(v, 'sm')}
                <div>
                  <div class="text-xs font-bold text-white">${escapeHtml(v.name)}</div>
                  <div class="text-xs text-muted">${escapeHtml(v.accent)} &bull; ${escapeHtml(v.category)}</div>
                </div>
              </div>
              <div class="flex items-center gap-2">
                <button class="btn btn-outline btn-xs" onclick="window.ValoraApp.auditionVoice('${v.id}')"><i class="fa-solid fa-play"></i></button>
                <button class="btn btn-gradient btn-xs" onclick="window.ValoraApp.selectVoice('${v.id}')">Use</button>
              </div>
            </div>
          `
          )
          .join('');
      }
    }
  }

  // =========================================================================
  // 14. MODAL MANAGEMENT
  // =========================================================================
  function initModals() {
    ['modal-voice-detail', 'modal-clone-voice', 'modal-edit-profile', 'modal-signout'].forEach((modalId) => {
      const modal = document.getElementById(modalId);
      if (modal) {
        modal.addEventListener('click', (e) => {
          if (e.target === modal) closeModal(modalId);
        });
      }
    });

    ['close-detail-modal-btn', 'close-clone-modal-btn', 'btn-cancel-clone', 'close-edit-prof-btn', 'btn-cancel-edit-prof', 'btn-cancel-logout'].forEach((id) => {
      document.getElementById(id)?.addEventListener('click', (e) => {
        const modal = e.target.closest('.modal-backdrop');
        if (modal) modal.classList.remove('open');
      });
    });

    // Voice Detail Modal CTA
    document.getElementById('modal-detail-use-btn')?.addEventListener('click', () => {
      const voiceId = document.getElementById('modal-voice-detail')?.getAttribute('data-active-voice-id');
      if (voiceId) window.ValoraApp.selectVoice(voiceId);
      closeModal('modal-voice-detail');
    });

    // Audition sample in detail modal
    document.getElementById('modal-detail-audition-btn')?.addEventListener('click', () => {
      const voiceId = document.getElementById('modal-voice-detail')?.getAttribute('data-active-voice-id');
      if (voiceId) window.ValoraApp.auditionVoice(voiceId);
    });

    // Voice Clone Upload Simulation
    document.getElementById('btn-browse-audio')?.addEventListener('click', () => {
      document.getElementById('clone-file-input')?.click();
    });

    document.getElementById('clone-file-input')?.addEventListener('change', (e) => {
      const file = e.target.files?.[0];
      if (file) {
        document.getElementById('clone-voice-name').value = file.name.replace(/\.[^/.]+$/, "") + " Cloned";
        showToast(`Loaded audio file: ${file.name} (${Math.round(file.size / 1024)} KB)`, 'success');
      }
    });

    document.getElementById('btn-submit-clone')?.addEventListener('click', () => {
      const name = document.getElementById('clone-voice-name')?.value.trim();
      const consent = document.getElementById('clone-consent-check')?.checked;

      if (!name) {
        showToast('Please specify a name for your cloned voice model', 'error');
        return;
      }
      if (!consent) {
        showToast('Please verify AI consent certification checkbox', 'error');
        return;
      }

      showToast('Synthesizing zero-shot neural clone...', 'info');

      setTimeout(() => {
        const newVoiceId = 'clone_' + Date.now();
        state.voices.unshift({
          id: newVoiceId,
          name: name,
          category: 'Neural Clone',
          gender: 'Custom Clone',
          accent: document.getElementById('clone-voice-lang')?.value || 'English (US)',
          locale: 'en-US',
          tone: 'Zero-Shot Timbre',
          fidelity: '99.9%',
          gradient: 'grad-voice-cyan',
          icon: 'fa-fingerprint',
          emotions: ['Neutral', 'Warm', 'Dramatic'],
          useCases: ['Personal Voice Cloning', 'Brand Voice'],
          bio: `Custom zero-shot neural voice clone created via reference latent encoding.`,
          sampleLine: `Hello, this is my custom cloned neural voice on Valora AI.`,
          isFavorite: true
        });

        closeModal('modal-clone-voice');
        renderVoiceLibrary();
        window.ValoraApp.selectVoice(newVoiceId);
        showToast(`Voice clone '${name}' created and ready in Studio!`, 'success');
      }, 1200);
    });

    // Modal Edit Profile browse file
    const browseAvatarBtn = document.getElementById('btn-browse-avatar');
    const modalAvatarFileInput = document.getElementById('edit-prof-file-input');
    const removeAvatarBtn = document.getElementById('btn-remove-avatar');

    if (browseAvatarBtn && modalAvatarFileInput) {
      browseAvatarBtn.addEventListener('click', () => modalAvatarFileInput.click());
    }
    if (modalAvatarFileInput) {
      modalAvatarFileInput.addEventListener('change', (e) => {
        const file = e.target.files?.[0];
        if (file) {
          uploadAvatarFile(file);
          e.target.value = '';
        }
      });
    }
    if (removeAvatarBtn) {
      removeAvatarBtn.addEventListener('click', () => {
        if (!state.authUser) return;
        state.authUser.avatar = '';
        const urlInput = document.getElementById('edit-prof-avatar');
        if (urlInput) urlInput.value = '';
        const previewImg = document.getElementById('edit-modal-avatar-preview');
        const previewPlaceholder = document.getElementById('edit-modal-avatar-placeholder');
        if (previewImg) { previewImg.style.display = 'none'; previewImg.src = ''; }
        if (previewPlaceholder) {
          previewPlaceholder.style.display = 'flex';
          previewPlaceholder.textContent = getInitials(state.authUser.name);
        }
        removeAvatarBtn.style.display = 'none';
        showToast('Avatar removed. Click Save Changes to confirm.', 'info');
      });
    }

    // Save Edit Profile
    document.getElementById('btn-save-edit-prof')?.addEventListener('click', async () => {
      const name = document.getElementById('edit-prof-name')?.value.trim();
      const bio = document.getElementById('edit-prof-bio')?.value.trim();
      const avatar = document.getElementById('edit-prof-avatar')?.value.trim();

      if (!name) {
        showToast('Display Name cannot be empty.', 'error');
        return;
      }

      showToast('Saving profile updates...', 'info');

      try {
        const headers = { 'Content-Type': 'application/json', 'Accept': 'application/json' };
        if (state.authToken) headers['Authorization'] = `Bearer ${state.authToken}`;

        const response = await fetch('/api/auth/update-profile', {
          method: 'POST',
          headers: headers,
          body: JSON.stringify({ name: name, bio: bio, avatar: avatar })
        });

        const data = await response.json().catch(() => ({}));

        if (response.ok && data.success && data.user) {
          state.authUser = data.user;
        } else {
          if (state.authUser) {
            state.authUser.name = name;
            state.authUser.bio = bio;
            state.authUser.avatar = avatar;
          }
        }
      } catch (err) {
        console.warn('Profile update saved locally:', err);
        if (state.authUser) {
          state.authUser.name = name;
          state.authUser.bio = bio;
          state.authUser.avatar = avatar;
        }
      }

      const isPersistent = !!localStorage.getItem('valora_auth_token');
      if (isPersistent) {
        localStorage.setItem('valora_auth_user', JSON.stringify(state.authUser));
      } else {
        sessionStorage.setItem('valora_auth_user', JSON.stringify(state.authUser));
      }

      renderNavAuth();
      renderProfileData();
      closeModal('modal-edit-profile');
      showToast('Profile updated successfully!', 'success');
    });

    // Logout Confirmation
    document.getElementById('btn-confirm-logout')?.addEventListener('click', async () => {
      // 1. Sign out of Firebase
      if (typeof firebase !== 'undefined' && firebase.auth) {
        try {
          await firebase.auth().signOut();
        } catch (fbErr) {
          console.warn('Firebase sign-out notice:', fbErr);
        }
      }

      // 2. Invalidate server-side session
      if (state.authToken) {
        fetch('/api/auth/logout', {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${state.authToken}` }
        }).catch(() => {});
      }

      // 3. Clear local session & reset UI
      clearAuthSession();
      closeModal('modal-signout');
      showToast('Signed out of Valora AI successfully.', 'info');
      navigateTo('home');
    });
  }

  function openModal(modalId) {
    document.getElementById(modalId)?.classList.add('open');
  }

  function closeModal(modalId) {
    document.getElementById(modalId)?.classList.remove('open');
  }

  function openCloneModal() {
    openModal('modal-clone-voice');
  }

  function openEditProfileModal() {
    if (!state.authUser) return;
    const user = state.authUser;

    const nameInput = document.getElementById('edit-prof-name');
    const bioInput = document.getElementById('edit-prof-bio');
    const avatarInput = document.getElementById('edit-prof-avatar');
    const previewImg = document.getElementById('edit-modal-avatar-preview');
    const previewPlaceholder = document.getElementById('edit-modal-avatar-placeholder');
    const removeBtn = document.getElementById('btn-remove-avatar');

    if (nameInput) nameInput.value = user.name || '';
    if (bioInput) bioInput.value = user.bio || '';
    if (avatarInput) avatarInput.value = user.avatar || '';

    if (user.avatar) {
      if (previewImg) { previewImg.src = user.avatar; previewImg.style.display = 'block'; }
      if (previewPlaceholder) previewPlaceholder.style.display = 'none';
      if (removeBtn) removeBtn.style.display = 'inline-flex';
    } else {
      if (previewImg) { previewImg.style.display = 'none'; previewImg.src = ''; }
      if (previewPlaceholder) {
        previewPlaceholder.style.display = 'flex';
        previewPlaceholder.textContent = getInitials(user.name);
      }
      if (removeBtn) removeBtn.style.display = 'none';
    }

    openModal('modal-edit-profile');
  }

  function openLogoutModal() {
    openModal('modal-signout');
  }

  // =========================================================================
  // 15. NOTIFICATIONS
  // =========================================================================
  function initNotifications() {
    const bellBtn = document.getElementById('notif-toggle-btn');
    const dropdown = document.getElementById('notification-dropdown');

    if (bellBtn && dropdown) {
      bellBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        dropdown.classList.toggle('open');
      });

      document.addEventListener('click', (e) => {
        if (!dropdown.contains(e.target) && !bellBtn.contains(e.target)) {
          dropdown.classList.remove('open');
        }
      });
    }

    renderNotifications();

    document.getElementById('mark-all-read-btn')?.addEventListener('click', () => {
      state.notifications.forEach((n) => (n.unread = false));
      renderNotifications();
      showToast('All notifications marked as read', 'info');
    });

    document.getElementById('clear-all-notifs-btn')?.addEventListener('click', () => {
      state.notifications = [];
      renderNotifications();
      showToast('Notifications cleared', 'info');
    });
  }

  function renderNotifications() {
    const list = document.getElementById('notif-list');
    const badge = document.getElementById('notif-badge');
    const countBadge = document.getElementById('notif-count-badge');
    if (!list) return;

    const unreadCount = state.notifications.filter((n) => n.unread).length;
    if (badge) {
      badge.textContent = unreadCount;
      badge.style.display = unreadCount > 0 ? 'inline-block' : 'none';
    }
    if (countBadge) countBadge.textContent = `${unreadCount} new`;

    if (state.notifications.length === 0) {
      list.innerHTML = `<div class="p-4 text-center text-xs text-muted">No notifications right now.</div>`;
      return;
    }

    list.innerHTML = state.notifications
      .map(
        (n) => `
        <div class="notif-item ${n.unread ? 'unread' : ''}">
          <div class="notif-item-title">${escapeHtml(n.title)}</div>
          <div class="notif-item-desc">${escapeHtml(n.desc)}</div>
          <div class="notif-item-time">${escapeHtml(n.time)}</div>
        </div>
      `
      )
      .join('');
  }

  // =========================================================================
  // 16. TOAST NOTIFICATIONS & UTILS
  // =========================================================================
  function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `valora-toast ${type}`;

    const iconMap = {
      success: 'fa-solid fa-circle-check text-emerald',
      error: 'fa-solid fa-circle-xmark text-rose',
      info: 'fa-solid fa-circle-info text-cyan'
    };

    toast.innerHTML = `
      <i class="${iconMap[type] || iconMap.info}"></i>
      <span>${escapeHtml(message)}</span>
    `;

    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(-10px)';
      setTimeout(() => toast.remove(), 300);
    }, 3200);
  }

  function formatTime(seconds) {
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m}:${s < 10 ? '0' : ''}${s}`;
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  // =========================================================================
  // 17. GLOBAL APP BRIDGE (WINDOW.VALORAAPP)
  // =========================================================================
  window.ValoraApp = {
    selectVoice: (voiceId) => {
      state.studio.activeVoiceId = voiceId;
      const voice = state.voices.find((v) => v.id === voiceId) || state.voices[0];
      const select = document.getElementById('studio-voice-select');
      if (select) select.value = voiceId;
      updateStudioActiveVoicePreview();
      showToast(`Selected voice: ${voice.name}`, 'success');
      navigateTo('studio');
    },

    auditionVoice: (voiceId) => {
      const voice = state.voices.find((v) => v.id === voiceId) || state.voices[0];
      showToast(`Auditioning ${voice.name}...`, 'info');

      if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
        const utter = new SpeechSynthesisUtterance(voice.sampleLine || 'Hello, this is Valora AI speech.');
        utter.pitch = 1.0;
        utter.rate = 1.0;
        window.speechSynthesis.speak(utter);
      }
    },

    openVoiceDetail: (voiceId) => {
      const voice = state.voices.find((v) => v.id === voiceId) || state.voices[0];
      const modal = document.getElementById('modal-voice-detail');
      if (!modal) return;

      modal.setAttribute('data-active-voice-id', voice.id);

      const emblemEl = document.getElementById('modal-detail-emblem');
      if (emblemEl) {
        emblemEl.className = `voice-emblem-badge ${voice.gradient || 'grad-voice-indigo'}`;
        emblemEl.innerHTML = `<i class="fa-solid ${voice.icon || 'fa-microphone-lines'} voice-emblem-icon" style="font-size:1.4rem;"></i><div class="mini-equalizer"><span></span><span></span><span></span><span></span></div>`;
      }

      document.getElementById('modal-detail-name').textContent = voice.name;
      document.getElementById('modal-detail-category').textContent = voice.category;
      document.getElementById('modal-detail-gender').textContent = voice.gender;
      document.getElementById('modal-detail-accent').textContent = voice.accent;
      document.getElementById('modal-detail-tone').textContent = voice.tone;
      document.getElementById('modal-detail-bio').textContent = voice.bio;

      const useCasesEl = document.getElementById('modal-detail-usecases');
      if (useCasesEl) {
        useCasesEl.innerHTML = (voice.useCases || ['Audiobooks', 'Podcasts', 'Explainer Videos'])
          .map((u) => `<span class="tag-pill">${escapeHtml(u)}</span>`)
          .join('');
      }

      const emotionsEl = document.getElementById('modal-detail-emotions');
      if (emotionsEl) {
        emotionsEl.innerHTML = (voice.emotions || ['Neutral', 'Warm', 'Dramatic'])
          .map((e) => `<span class="tag-pill">${escapeHtml(e)}</span>`)
          .join('');
      }

      openModal('modal-voice-detail');
    },

    toggleFavorite: (voiceId) => {
      const voice = state.voices.find((v) => v.id === voiceId);
      if (voice) {
        voice.isFavorite = !voice.isFavorite;
        showToast(voice.isFavorite ? `Added ${voice.name} to favorites` : `Removed ${voice.name} from favorites`, 'info');
        renderVoiceLibrary();
        if (state.currentRoute === 'profile') renderProfileData();
      }
    },

    playTake: (takeId) => {
      const take = state.studio.sessionTakes.find((t) => t.id === takeId);
      if (take && (take.audioUrl || take.audioBlob)) {
        showToast(`Playing take: ${take.voiceName}`, 'info');
        const url = take.audioUrl || URL.createObjectURL(take.audioBlob);
        state.studio.currentUrl = url;
        state.studio.currentBlob = take.audioBlob || null;
        playAudioTake(url, take.fullText || take.text);
      } else if (take) {
        showToast(`Previewing: ${take.voiceName}`, 'info');
        startMasterPlayback(take.fullText || take.text);
      }
    },

    downloadTake: (takeId) => {
      const take = state.studio.sessionTakes.find((t) => t.id === takeId);
      if (take && (take.audioBlob || take.audioUrl)) {
        const a = document.createElement('a');
        a.href = take.audioBlob ? URL.createObjectURL(take.audioBlob) : take.audioUrl;
        a.download = `Valora_${(take.voiceName || 'speech').replace(/[^a-zA-Z0-9]/g, '_')}_${Date.now()}.wav`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        showToast(`Downloading take: ${take.voiceName}...`, 'success');
      } else {
        showToast('No audio available to download for this take.', 'info');
      }
    },

    openCloneModal: openCloneModal,
    openEditProfileModal: openEditProfileModal,
    openLogoutModal: openLogoutModal,
    showToast: showToast,
    navigateTo: navigateTo
  };

})();
