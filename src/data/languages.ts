// Language learning data for Ẹ̀kọ́
// Phase 1: Yoruba (active) | Hausa & Igbo: coming soon

export interface Phrase {
  id: string;
  english: string;
  native: string;
  pronunciation: string;
  notes?: string;
}

export interface Language {
  id: string;
  name: string;
  nativeName: string;
  status: 'active' | 'coming';
  color: string;
  phrases: Phrase[];
}

export const LANGUAGES: Language[] = [
  {
    id: 'yoruba',
    name: 'Yoruba',
    nativeName: 'Yorùbá',
    status: 'active',
    color: '#059669',
    phrases: [
      { id: 'yo-01', english: 'Hello', native: 'Ẹ kú àárọ̀', pronunciation: 'eh-KOO ah-ROH', notes: 'Used in the morning' },
      { id: 'yo-02', english: 'Good morning', native: 'Ẹ kú ọ̀sán', pronunciation: 'eh-KOO oh-SHAN' },
      { id: 'yo-03', english: 'Good afternoon', native: 'Ẹ kú ọ́sọ̀', pronunciation: 'eh-KOO oh-SOH' },
      { id: 'yo-04', english: 'Good evening', native: 'Ẹ kú irọ́lẹ́', pronunciation: 'eh-KOO ee-roh-LEH' },
      { id: 'yo-05', english: 'Thank you', native: 'Ẹ ṣé', pronunciation: 'eh-SHEH' },
      { id: 'yo-06', english: 'Goodbye', native: 'Ó dàbọ̀', pronunciation: 'oh-DAH-boh' },
      { id: 'yo-07', english: 'Yes', native: 'Bẹ́ẹ̀ni', pronunciation: 'BEH-eh-nee' },
      { id: 'yo-08', english: 'No', native: 'Rii', pronunciation: 'ree' },
      { id: 'yo-09', english: 'How are you?', native: 'Báwo ni?', pronunciation: 'BAH-woh nee' },
      { id: 'yo-10', english: "I'm fine", native: 'Mo wà dáadá', pronunciation: 'moh WAH dah-DAH' },
      { id: 'yo-11', english: 'Please', native: 'Jọ̀wẹ́', pronunciation: 'JOH-weh' },
      { id: 'yo-12', english: 'Excuse me', native: 'Má bínu', pronunciation: 'mah-BEE-noo' },
      { id: 'yo-13', english: "I don't understand", native: 'Emi kì í ye mí', pronunciation: 'eh-mee kee EE yeh-mee' },
      { id: 'yo-14', english: 'Please say again', native: 'Ẹ jọ̀ọ́wọ́', pronunciation: 'eh-JOH-oh-WOH' },
      { id: 'yo-15', english: 'My name is...', native: 'Orúkọ mi ni...', pronunciation: 'oh-ROO-koh mee nee' },
      { id: 'yo-16', english: 'What is your name?', native: 'Kí ni orúkọ rẹ?', pronunciation: 'kee nee oh-ROO-koh reh' },
      { id: 'yo-17', english: 'Where are you from?', native: 'Níni aarọ̀ yín?', pronunciation: 'nee-nee AH-ah-roh yeen' },
      { id: 'yo-18', english: 'I am from Nigeria', native: 'Mo ti ngbà láti Nigeria', pronunciation: 'moh tee ng-BAH LAH-tee nee-JEHR-ee-ah' },
      { id: 'yo-19', english: 'How much is this?', native: 'Melo ni é?', pronunciation: 'MEH-loh nee EH' },
      { id: 'yo-20', english: 'I love you', native: 'Mo fẹ́ẹ́ rẹ́', pronunciation: 'moh FEH-eh reh' },
      { id: 'yo-21', english: 'God bless you', native: 'Oláún', pronunciation: 'oh-LAH-oon' },
      { id: 'yo-22', english: 'See you later', native: 'Àti láiyo', pronunciation: 'AH-tee LAH-ee-yoh' },
      { id: 'yo-23', english: 'Welcome', native: 'Ẹ kú i dọ́wọ́', pronunciation: 'eh-KOO ee DOH-woh' },
      { id: 'yo-24', english: 'Congratulations', native: 'Olúwa fún yín', pronunciation: 'oh-LOO-wah FOON yeen' },
      { id: 'yo-25', english: 'Happy birthday', native: 'Ọjọ́ àbísọ́ rẹ́', pronunciation: 'OH-joh AH-bee-SHoh reh' },
      { id: 'yo-26', english: 'Good luck', native: 'Ó ti yọ̀', pronunciation: 'oh tee YOH' },
      { id: 'yo-27', english: 'Help!', native: 'Àlàáfíà!', pronunciation: 'AH-lah-AH-fee-ah' },
      { id: 'yo-28', english: 'Water', native: 'Omi', pronunciation: 'OH-mee' },
      { id: 'yo-29', english: 'Food', native: 'Oúnjẹ́', pronunciation: 'oh-OON-jeh' },
      { id: 'yo-30', english: 'House', native: 'Ilé', pronunciation: 'ee-LEH' },
      { id: 'yo-31', english: 'Road', native: 'Ọ̀pọ̀lọ̀pọ̀', pronunciation: 'OH-poh-LOH-poh' },
      { id: 'yo-32', english: 'Peace', native: 'Alàáfíà', pronunciation: 'ah-lah-AH-fee-ah' },
      { id: 'yo-33', english: 'Nigerian greeting', native: 'Ẹ kú ọ́run', pronunciation: 'eh-KOO OH-roon' },
      { id: 'yo-34', english: 'Tomorrow', native: 'Ọ̀la', pronunciation: 'OH-lah' },
      { id: 'yo-35', english: 'Today', native: 'Ọ̀nà', pronunciation: 'OH-nah' },
    ],
  },
  {
    id: 'hausa',
    name: 'Hausa',
    nativeName: 'Harshen Hausa',
    status: 'coming',
    color: '#dc2626',
    phrases: [],
  },
  {
    id: 'igbo',
    name: 'Igbo',
    nativeName: 'Ásụ̀sụ̀ Ìgbò',
    status: 'coming',
    color: '#2563eb',
    phrases: [],
  },
];
