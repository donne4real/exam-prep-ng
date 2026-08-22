#!/usr/bin/env python3
"""
merge_questions.py
Converts Ẹ̀kọ́ questions to ExamPrep NG format and merges into questions.json
"""
import json
import os
from pathlib import Path

SRC = Path(__file__).parent.parent / "public" / "data" / "questions.json"
OUT = SRC

# ── Mapping: eko-learn level → exam ──────────────────────────────
LEVEL_MAP = {
    "prim6":  "BECE",
    "js3":    "BECE",
    "wassce": "WAEC",
    "jamb":   "JAMB",
}

# ── Subject name normalisation ────────────────────────────────────
SUBJECT_MAP = {
    "english":     "English Language",
    "mathematics": "Mathematics",
    "civic":       "Civic Education",
    "government":  "Government",
}

# ── Ẹ̀kọ́ questions ─────────────────────────────────────────────
QUESTIONS = [
    # ── English: Primary 6 ───────────────────────────────────────
    {"id":"en-p6-01","level":"prim6","subject":"english","question":"Choose the correct plural form: child","options":["childs","children","childes","childrens"],"answer":1,"explanation":"Children is the correct plural of child."},
    {"id":"en-p6-02","level":"prim6","subject":"english","question":"Which sentence is correctly punctuated?","options":["the boy ran home","The boy ran home.","The boy ran home","The boy, ran home."],"answer":1,"explanation":"Sentences begin with a capital letter and end with a full stop."},
    {"id":"en-p6-03","level":"prim6","subject":"english","question":"Which word is a noun?","options":["quickly","beautiful","garden","running"],"answer":2,"explanation":"Garden is a person, place, or thing — a noun."},
    {"id":"en-p6-04","level":"prim6","subject":"english","question":"Choose the correct spelling:","options":["recieve","receive","receeve","recive"],"answer":1,"explanation":"The word receive follows the i-before-e rule (except after c)."},
    {"id":"en-p6-05","level":"prim6","subject":"english","question":"What is the opposite of ancient?","options":["old","modern","history","king"],"answer":1,"explanation":"Ancient means very old; modern means recent or new."},
    {"id":"en-p6-06","level":"prim6","subject":"english","question":"Fill in the blank: There are ___ books on the table.","options":["much","any","some","a"],"answer":2,"explanation":"Some is used with plural countable nouns in positive statements."},
    {"id":"en-p6-07","level":"prim6","subject":"english","question":"Which word rhymes with cat?","options":["hat","bite","moon","tree"],"answer":0,"explanation":"Hat rhymes with cat — both end with the -at sound."},
    {"id":"en-p6-08","level":"prim6","subject":"english","question":"Which sentence uses the correct article?","options":["He is a honest man.","He is an honest man.","He is the honest man.","He is an honest men."],"answer":1,"explanation":"An is used before words beginning with a vowel sound. Honest starts with a vowel sound."},
    {"id":"en-p6-09","level":"prim6","subject":"english","question":"Which word is a verb?","options":["happiness","quick","jump","beautiful"],"answer":2,"explanation":"Jump describes an action — it is a verb."},
    {"id":"en-p6-10","level":"prim6","subject":"english","question":"Choose the correct word: The dog ___ under the tree.","options":["sit","sits","sitted","sitting"],"answer":1,"explanation":"With the dog (singular subject), the verb takes s."},
    {"id":"en-p6-11","level":"prim6","subject":"english","question":"What is the past tense of go?","options":["goed","gone","went","going"],"answer":2,"explanation":"Went is the irregular past tense of go."},
    {"id":"en-p6-12","level":"prim6","subject":"english","question":"Which word is a pronoun?","options":["table","she","run","green"],"answer":1,"explanation":"She replaces a noun — it is a pronoun."},
    {"id":"en-p6-13","level":"prim6","subject":"english","question":"Identify the adjective in: The tall boy ran fast.","options":["boy","tall","ran","fast"],"answer":1,"explanation":"Tall describes the boy — it is an adjective."},
    {"id":"en-p6-14","level":"prim6","subject":"english","question":"Which of these is a compound word?","options":["sunshine","beautiful","happily","running"],"answer":0,"explanation":"Sunshine is made of two words: sun + shine."},
    {"id":"en-p6-15","level":"prim6","subject":"english","question":"Choose the correct preposition: The cat is ___ the table.","options":["in","on","to","at"],"answer":1,"explanation":"On indicates the cat is resting on top of the table surface."},

    # ── English: JSS3 ──────────────────────────────────────────
    {"id":"en-js3-01","level":"js3","subject":"english","question":"The teacher gave the students __ assignment. Choose the correct article.","options":["a","an","the","some"],"answer":1,"explanation":"An is used before words beginning with a vowel sound. Assignment starts with the sound a."},
    {"id":"en-js3-02","level":"js3","subject":"english","question":"Identify the verb in: She quietly opened the door.","options":["quietly","opened","door","the"],"answer":1,"explanation":"Opened is the action word (verb) in this sentence."},
    {"id":"en-js3-03","level":"js3","subject":"english","question":"Which sentence contains a metaphor?","options":["Her smile is like sunshine.","The sea was a mirror.","He runs like a cheetah.","She sings beautifully."],"answer":1,"explanation":"The sea was a mirror compares the sea to a mirror without using like or as — a metaphor."},
    {"id":"en-js3-04","level":"js3","subject":"english","question":"What type of noun is Abuja?","options":["common noun","proper noun","collective noun","abstract noun"],"answer":1,"explanation":"Abuja is the name of a specific city — a proper noun."},
    {"id":"en-js3-05","level":"js3","subject":"english","question":"Choose the correct tense: By next year, she ___ in Lagos for five years.","options":["has lived","will have lived","lived","is living"],"answer":1,"explanation":"Will have lived is the future perfect — action completed by a specific future time."},
    {"id":"en-js3-06","level":"js3","subject":"english","question":"Which word is an adverb?","options":["quick","beautiful","slowly","happy"],"answer":2,"explanation":"Slowly describes how an action is done — it is an adverb."},
    {"id":"en-js3-07","level":"js3","subject":"english","question":"Identify the subject in: The young girls sang at the festival.","options":["young girls","sang","festival","at"],"answer":0,"explanation":"The young girls is the subject — the ones performing the action."},
    {"id":"en-js3-08","level":"js3","subject":"english","question":"Which sentence uses direct speech correctly?","options":["She said that she was tired.","I am tired, she said.","She said, I am tired.","I am tired she said."],"answer":1,"explanation":"Direct speech uses quotation marks and the exact words of the speaker."},
    {"id":"en-js3-09","level":"js3","subject":"english","question":"Choose the correct conditional: If it ___ tomorrow, we will stay indoors.","options":["rains","rained","rain","will rain"],"answer":0,"explanation":"In first conditional sentences, we use the present simple after if for future possibilities."},
    {"id":"en-js3-10","level":"js3","subject":"english","question":"What figure of speech is The wind howled?","options":["personification","simile","metaphor","hyperbole"],"answer":0,"explanation":"Wind cannot howl — this gives human qualities to the wind, making it personification."},
    {"id":"en-js3-11","level":"js3","subject":"english","question":"Which of these is a collective noun?","options":["team","book","happy","quickly"],"answer":0,"explanation":"Team refers to a group of people — a collective noun."},
    {"id":"en-js3-12","level":"js3","subject":"english","question":"Choose the correct passive voice: Someone has stolen my bag.","options":["My bag has been stolen.","My bag has stole.","My bag was stealing.","My bag is stealing."],"answer":0,"explanation":"In passive voice, the object becomes the subject."},
    {"id":"en-js3-13","level":"js3","subject":"english","question":"Which sentence is grammatically correct?","options":["Him and I went to school.","He and I went to school.","Him and me went to school.","He and me went to school."],"answer":1,"explanation":"He and I are the correct subject pronouns to use as the subject of a sentence."},
    {"id":"en-js3-14","level":"js3","subject":"english","question":"Identify the antonym of generous:","options":["kind","stingy","helpful","giving"],"answer":1,"explanation":"Generous means giving freely; stingy means unwilling to give."},
    {"id":"en-js3-15","level":"js3","subject":"english","question":"Which prefix means not or opposite?","options":["un-","re-","pre-","mis-"],"answer":0,"explanation":"Un- is a negative prefix meaning not (e.g., unhappy, unhealthy)."},
    {"id":"en-js3-16","level":"js3","subject":"english","question":"What is the comparative form of good?","options":["gooder","better","best","more good"],"answer":1,"explanation":"Good is an irregular adjective — its comparative form is better."},
    {"id":"en-js3-17","level":"js3","subject":"english","question":"Which sentence contains a homophone error?","options":["I can see the sea from here.","The knight wore armor.","He past the exam yesterday.","Their bags are missing."],"answer":2,"explanation":"Past is a noun/time word; the verb form should be passed."},
    {"id":"en-js3-18","level":"js3","subject":"english","question":"What does acronym mean?","options":["a type of poem","a word formed from the first letters of a phrase","a shortened form of a word","a type of rhyme"],"answer":1,"explanation":"An acronym is formed from the initial letters of a phrase, e.g., JAMB."},
    {"id":"en-js3-19","level":"js3","subject":"english","question":"Which of these is an example of an interjection?","options":["quickly","oh","garden","jump"],"answer":1,"explanation":"Oh! expresses emotion and stands alone — it is an interjection."},
    {"id":"en-js3-20","level":"js3","subject":"english","question":"Choose the correct conjunction: She studied hard ___ she passed.","options":["or","but","so","because"],"answer":3,"explanation":"Because shows a reason — she studied hard as a result of wanting to pass."},
    {"id":"en-js3-21","level":"js3","subject":"english","question":"What is the superlative form of bad?","options":["badder","worse","worst","most bad"],"answer":2,"explanation":"Bad is irregular — its superlative form is worst."},
    {"id":"en-js3-22","level":"js3","subject":"english","question":"Identify the transitive verb:","options":["sleep","laugh","eat","arrive"],"answer":2,"explanation":"Eat takes a direct object (e.g., eat food) — it is transitive."},
    {"id":"en-js3-23","level":"js3","subject":"english","question":"Which sentence uses fewer correctly?","options":["There are fewer water.","She has fewer friends now.","I have less books.","There is fewer time."],"answer":1,"explanation":"Fewer is used for countable nouns; less is for uncountable nouns."},
    {"id":"en-js3-24","level":"js3","subject":"english","question":"What is a palindrome?","options":["a word that rhymes","a word that reads the same backwards and forwards","a word with multiple meanings","a word opposite in meaning"],"answer":1,"explanation":"A palindrome reads the same backwards and forwards, e.g., level, radar."},
    {"id":"en-js3-25","level":"js3","subject":"english","question":"Choose the correct relative pronoun: The girl ___ won the prize is my sister.","options":["which","whom","who","whose"],"answer":2,"explanation":"Who is used for people as the subject of a relative clause."},

    # ── English: WASSCE ─────────────────────────────────────────
    {"id":"en-ws-01","level":"wassce","subject":"english","question":"Choose the word closest in meaning to benevolent:","options":["cruel","kind","indifferent","noisy"],"answer":1,"explanation":"Benevolent means well-meaning and kind."},
    {"id":"en-ws-02","level":"wassce","subject":"english","question":"Which of the following is a compound sentence?","options":["She sang and danced.","Because it rained, we stayed inside.","The dog barked loudly.","Although tired, he continued."],"answer":0,"explanation":"A compound sentence has two independent clauses joined by a coordinating conjunction."},
    {"id":"en-ws-03","level":"wassce","subject":"english","question":"Which option contains a dangling modifier?","options":["Walking down the street, the shop looked attractive.","After reading the book, the movie was disappointing.","Being late, the meeting was difficult to follow.","All of the above"],"answer":3,"explanation":"All sentences above have modifiers that do not clearly attach to the subject of the main clause."},
    {"id":"en-ws-04","level":"wassce","subject":"english","question":"Identify the semantic relationship: parent : child","options":["synonym","antonym","hyponym","meronym"],"answer":2,"explanation":"A parent and child are hyponyms — specific types of a broader category."},
    {"id":"en-ws-05","level":"wassce","subject":"english","question":"Which sentence uses the subjunctive mood correctly?","options":["If I was you, I would go.","If I were you, I would go.","If I am you, I will go.","If I be you, I go."],"answer":1,"explanation":"The subjunctive were is used in hypothetical or contrary-to-fact conditions."},
    {"id":"en-ws-06","level":"wassce","subject":"english","question":"What is the function of a topic sentence?","options":["to conclude an argument","to introduce and control the main idea of a paragraph","to provide evidence","to transition between paragraphs"],"answer":1,"explanation":"A topic sentence introduces the main idea that the rest of the paragraph develops."},
    {"id":"en-ws-07","level":"wassce","subject":"english","question":"Which of these words is NOT typically used in academic writing?","options":["however","consequently","gonna","therefore"],"answer":2,"explanation":"Gonna is informal and should not be used in academic writing."},
    {"id":"en-ws-08","level":"wassce","subject":"english","question":"Identify the correct APA in-text citation for a book by Adaobi (2020):","options":["(Adaobi, 2020)","[Adaobi, 2020]","{Adaobi 2020}","(Adaobi 2020)"],"answer":0,"explanation":"APA style uses parentheses with the author surname and year."},
    {"id":"en-ws-09","level":"wassce","subject":"english","question":"Which of the following is an example of a cleft sentence?","options":["The cat sat on the mat.","It was the cat that sat on the mat.","The cat that sat on the mat.","The mat had a cat."],"answer":1,"explanation":"A cleft sentence uses it is/was... that/who to emphasize one element."},
    {"id":"en-ws-10","level":"wassce","subject":"english","question":"Which register is most appropriate for a formal letter to a university admissions office?","options":["colloquial","slang","frozen","intimate"],"answer":2,"explanation":"Frozen register is formal and unchanging — used for official letters and formal academic communication."},
    {"id":"en-ws-11","level":"wassce","subject":"english","question":"Which speech act is Could you pass the salt?","options":["declarative","expressive","directive","representative"],"answer":2,"explanation":"Could you pass the salt? is a directive — it attempts to get the listener to do something."},
    {"id":"en-ws-12","level":"wassce","subject":"english","question":"What is the difference between less and fewer?","options":["There is no difference","less is for countable nouns; fewer is for uncountable","less is for uncountable nouns; fewer is for countable nouns","both are for verbs only"],"answer":2,"explanation":"Less is used with uncountable nouns (water, sugar); fewer with countable nouns (bottles, cups)."},
    {"id":"en-ws-13","level":"wassce","subject":"english","question":"Which option best describes register in linguistics?","options":["a type of verb tense","a variety of language used in a particular social context","a grammatical rule","a type of dictionary"],"answer":1,"explanation":"Register refers to the level of formality or language variety used depending on the social situation."},
    {"id":"en-ws-14","level":"wassce","subject":"english","question":"Choose the sentence with correct pronoun reference:","options":["Everyone brought their books.","Everyone brought his books.","Everyone brought her books.","Everyone brought its books."],"answer":0,"explanation":"Their is increasingly accepted as a singular pronoun when gender is unknown."},
    {"id":"en-ws-15","level":"wassce","subject":"english","question":"What type of essay is To what extent has technology improved education in Nigeria?","options":["narrative","expository","argumentative","persuasive"],"answer":2,"explanation":"This question invites the writer to present arguments and evaluate a position — an argumentative essay."},
    {"id":"en-ws-16","level":"wassce","subject":"english","question":"Which sentence is grammatically correct?","options":["Neither the teachers nor the principal were present.","Neither the teachers nor the principal was present.","Neither the teachers nor the principal are present.","Neither the teachers nor the principal be present."],"answer":1,"explanation":"With neither...nor, the verb agrees with the nearer subject."},
    {"id":"en-ws-17","level":"wassce","subject":"english","question":"Identify the lexical ambiguity: The chicken is ready.","options":["ready means finished","chicken could mean the bird or a coward","ready means prepared","chicken is always the bird"],"answer":1,"explanation":"Chicken has more than one meaning — the animal or a slang term for a coward."},
    {"id":"en-ws-18","level":"wassce","subject":"english","question":"Which word has the same meaning as ephemeral?","options":["permanent","lasting","short-lived","eternal"],"answer":2,"explanation":"Ephemeral means lasting for a very short time."},
    {"id":"en-ws-19","level":"wassce","subject":"english","question":"In The book was read by the students, the phrase by the students is a:","options":["direct object","indirect object","adverbial phrase","agent phrase"],"answer":3,"explanation":"In passive voice, the by + agent phrase shows who performed the action."},
    {"id":"en-ws-20","level":"wassce","subject":"english","question":"What is the purpose of a thesis statement?","options":["to summarize the entire essay","to present the main argument or claim of the essay","to list all sources used","to transition to the next paragraph"],"answer":1,"explanation":"A thesis statement presents the central argument that the essay will support and develop."},
    {"id":"en-ws-21","level":"wassce","subject":"english","question":"Which of the following is a phrasal verb meaning to cancel?","options":["call off","come about","look into","carry on"],"answer":0,"explanation":"Call off means to cancel or stop something that was planned."},
    {"id":"en-ws-22","level":"wassce","subject":"english","question":"What does the prefix semi- mean?","options":["half","full","none","double"],"answer":0,"explanation":"Semi- means half or partially (e.g., semi-final, semi-circle)."},
    {"id":"en-ws-23","level":"wassce","subject":"english","question":"Identify the correct sentence:","options":["The data shows that sales have increased.","The data show that sales has increased.","The data showing that sales has increased.","The data shown that sales has increased."],"answer":0,"explanation":"Data is technically plural (singular: datum), so the verb should agree: data show."},
    {"id":"en-ws-24","level":"wassce","subject":"english","question":"Which style guide is commonly used in Nigerian universities?","options":["MLA only","APA only","APA, MLA, and Chicago vary by institution","Harvard only"],"answer":2,"explanation":"Different Nigerian universities specify different citation styles."},
    {"id":"en-ws-25","level":"wassce","subject":"english","question":"The sentence No news is good news contains which literary device?","options":["metaphor","alliteration","antithesis","paradox"],"answer":3,"explanation":"A paradox is a statement that seems contradictory but contains a truth."},
    {"id":"en-ws-26","level":"wassce","subject":"english","question":"What is code-switching?","options":["changing spelling between British and American English","alternating between two languages or dialects in conversation","writing in informal language","translating one language to another"],"answer":1,"explanation":"Code-switching is the practice of alternating between languages or dialects within a conversation."},
    {"id":"en-ws-27","level":"wassce","subject":"english","question":"Which of these is an example of collocation?","options":["heavy rain","big small","old new","run walk"],"answer":0,"explanation":"Heavy rain is a natural collocation — certain words naturally go together in English."},
    {"id":"en-ws-28","level":"wassce","subject":"english","question":"In comprehension questions, infer means to:","options":["state exactly what the text says","use clues in the text to reach a conclusion not directly stated","identify the main topic","spell all difficult words"],"answer":1,"explanation":"Infer means to deduce information that is implied but not directly stated in the text."},
    {"id":"en-ws-29","level":"wassce","subject":"english","question":"Which sentence uses an oxymoron?","options":["The room was terribly beautiful.","The silence was deafening.","She is a living legend.","He is incredibly average."],"answer":1,"explanation":"Deafening silence combines contradictory terms — silence cannot be heard, yet it is described as deafening."},
    {"id":"en-ws-30","level":"wassce","subject":"english","question":"What does diaspora mean in modern usage?","options":["a type of dance","people who have spread from their original homeland","a language family","a religious festival"],"answer":1,"explanation":"Diaspora refers to communities dispersed from their ancestral homeland."},

    # ── English: JAMB ───────────────────────────────────────────
    {"id":"en-jb-01","level":"jamb","subject":"english","question":"The chairman ___ the report by tomorrow. Choose the correct tense.","options":["has submitted","will have submitted","submitted","is submitting"],"answer":1,"explanation":"Will have submitted is the future perfect tense — action completed before a future time."},
    {"id":"en-jb-02","level":"jamb","subject":"english","question":"Which option contains a dangling modifier?","options":["Walking down the street, the shop looked attractive.","After reading the book, the movie was disappointing.","Being late, the meeting was difficult to follow.","All of the above"],"answer":3,"explanation":"All sentences above have modifiers that do not clearly attach to the subject of the main clause."},
    {"id":"en-jb-03","level":"jamb","subject":"english","question":"Choose the correct option: Neither the chairman nor the members ___ satisfied.","options":["is","are","was","been"],"answer":1,"explanation":"With neither...nor, the verb agrees with the nearer noun — members is plural."},
    {"id":"en-jb-04","level":"jamb","subject":"english","question":"Which of the following is NOT a type of phrase?","options":["noun phrase","verb phrase","adjective phrase","emotion phrase"],"answer":3,"explanation":"Emotion phrase is not a recognized phrase type in English grammar."},
    {"id":"en-jb-05","level":"jamb","subject":"english","question":"The sentence The news is alarming contains a ___ structure.","options":["subject + verb + object","subject + verb + complement","subject + verb + adverbial","subject + linking verb + adjective"],"answer":3,"explanation":"Is is a linking verb; alarming is an adjective complement."},
    {"id":"en-jb-06","level":"jamb","subject":"english","question":"Identify the class of the word: He was QUICKLY approaching.","options":["adjective","verb","adverb","preposition"],"answer":2,"explanation":"Quickly modifies the verb approaching — it tells us how he was approaching."},
    {"id":"en-jb-07","level":"jamb","subject":"english","question":"Which of these is a stative verb?","options":["go","eat","believe","write"],"answer":2,"explanation":"Believe describes a state, not an action. Stative verbs are not usually used in continuous tenses."},
    {"id":"en-jb-08","level":"jamb","subject":"english","question":"Choose the correct article: She is ___ UNESCO representative.","options":["a","an","the","no article"],"answer":1,"explanation":"UNESCO begins with the vowel sound U — /juː/, so an is correct."},
    {"id":"en-jb-09","level":"jamb","subject":"english","question":"Which sentence correctly uses the semicolon?","options":["I love reading; and writing.","She studied; she passed.","He went home; because he was tired.","They came; and left quickly;"],"answer":1,"explanation":"A semicolon joins two independent clauses that are closely related."},
    {"id":"en-jb-10","level":"jamb","subject":"english","question":"What type of error is in: Her and I went to the market?","options":["spelling error","wrong tense","wrong pronoun case","missing punctuation"],"answer":2,"explanation":"Her is an object pronoun — the subject should be She and I."},
    {"id":"en-jb-11","level":"jamb","subject":"english","question":"Which option shows correct concord (subject-verb agreement)?","options":["Each of the students have passed.","Each of the students has passed.","Each of the students are passed.","Each of the students is passing."],"answer":1,"explanation":"Each of the students takes a singular verb — has passed."},
    {"id":"en-jb-12","level":"jamb","subject":"english","question":"He said he would come yesterday is an example of:","options":["direct speech","indirect speech","reported speech only","free indirect speech"],"answer":1,"explanation":"This is indirect (reported) speech — the exact words are not in quotes."},
    {"id":"en-jb-13","level":"jamb","subject":"english","question":"Which word describes a group of words with a finite verb?","options":["phrase","clause","sentence","paragraph"],"answer":1,"explanation":"A clause contains a subject and a finite verb."},
    {"id":"en-jb-14","level":"jamb","subject":"english","question":"In The man whom we saw was tall, whom is a:","options":["demonstrative pronoun","relative pronoun","indefinite pronoun","personal pronoun"],"answer":1,"explanation":"Whom introduces a relative clause and refers to the man."},
    {"id":"en-jb-15","level":"jamb","subject":"english","question":"Which lexical item is most appropriate in formal academic writing?","options":["kids","get","therefore","gonna"],"answer":2,"explanation":"Therefore is a formal discourse marker appropriate for academic writing."},
    {"id":"en-jb-16","level":"jamb","subject":"english","question":"The sentence To err is human is a:","options":["complex sentence","simple sentence","compound sentence","infinitive phrase"],"answer":1,"explanation":"To err is human has one subject-verb relationship — it is a simple sentence."},
    {"id":"en-jb-17","level":"jamb","subject":"english","question":"Which of the following is NOT a silent consonant cluster?","options":["knight","write","psychology","thumb"],"answer":3,"explanation":"Thumb has an audible mb ending. Knight, write, and psychology all have silent letters."},
    {"id":"en-jb-18","level":"jamb","subject":"english","question":"Which sentence contains a cataphoric reference?","options":["I saw the dog. It was huge.","When the soldier arrived, he was tired.","John is kind; he helps everyone.","The following will be discussed: maths and science."],"answer":3,"explanation":"Cataphoric reference points forward to later information."},
    {"id":"en-jb-19","level":"jamb","subject":"english","question":"In phonology, /p/, /t/, /k/ are examples of:","options":["vowels","voiced stops","voiceless stops","fricatives"],"answer":2,"explanation":"/p/, /t/, /k/ are voiceless plosive consonants."},
    {"id":"en-jb-20","level":"jamb","subject":"english","question":"Which vowel sound is found in the word boot?","options":["/ɪ/","/uː/","/e/","/æ/"],"answer":1,"explanation":"Boot has the long vowel /uː/."},
    {"id":"en-jb-21","level":"jamb","subject":"english","question":"Identify the error: The committee have reached its decision.","options":["tense error","concord error","preposition error","spelling error"],"answer":1,"explanation":"Committee is a collective noun taking a plural verb when referring to members individually."},
    {"id":"en-jb-22","level":"jamb","subject":"english","question":"The plural of criterion is:","options":["criterions","criteria","criterium","criterias"],"answer":1,"explanation":"Criteria is already the plural form of criterion."},
    {"id":"en-jb-23","level":"jamb","subject":"english","question":"Which word contains a diphthong?","options":["cat","boat","sit","pot"],"answer":1,"explanation":"Boat contains the diphthong /əʊ/."},
    {"id":"en-jb-24","level":"jamb","subject":"english","question":"The police have arrested the thieves — police is:","options":["a singular noun","a plural noun used with a plural verb","an uncountable noun","an abstract noun"],"answer":1,"explanation":"Police is grammatically plural — it takes a plural verb."},
    {"id":"en-jb-25","level":"jamb","subject":"english","question":"Which is the correct phonetic transcription of thought?","options":["/θɔːt/","/θaʊt/","/θuːt/","/ðɔːt/"],"answer":0,"explanation":"Thought is transcribed as /θɔːt/ in most standard English pronunciation guides."},
    {"id":"en-jb-26","level":"jamb","subject":"english","question":"In the phrase She insisted on coming, the underlined function is:","options":["subject","object","complement","adjunct"],"answer":1,"explanation":"On coming is the object of the preposition on."},
    {"id":"en-jb-27","level":"jamb","subject":"english","question":"Which option shows the correct use of the comma?","options":["She likes coffee, tea, and juice.","She likes, coffee, tea and juice.","She likes coffee tea and, juice.","She likes, coffee, tea and juice."],"answer":0,"explanation":"Commas separate items in a list, with a serial comma before and."},
    {"id":"en-jb-28","level":"jamb","subject":"english","question":"In discourse analysis, turn-taking refers to:","options":["how actors take stage turns in drama","how speakers exchange speaking roles in conversation","the number of words in a sentence","how students alternate in class"],"answer":1,"explanation":"Turn-taking describes how conversationalists manage speaker change."},
    {"id":"en-jb-29","level":"jamb","subject":"english","question":"Which sentence contains a double negative?","options":["I cannot help but agree.","I don t need nothing.","I need something.","Nothing is impossible."],"answer":1,"explanation":"Dont and nothing are both negatives — a double negative is non-standard."},
    {"id":"en-jb-30","level":"jamb","subject":"english","question":"The sentence No news is good news is an example of:","options":["metaphor","alliteration","antithesis","paradox"],"answer":3,"explanation":"A paradox is a statement that seems contradictory but contains a truth."},

    # ── Mathematics: Primary 6 ─────────────────────────────────
    {"id":"ma-p6-01","level":"prim6","subject":"mathematics","question":"What is 48 ÷ 6?","options":["6","8","7","9"],"answer":1,"explanation":"48 divided by 6 equals 8."},
    {"id":"ma-p6-02","level":"prim6","subject":"mathematics","question":"Simplify: 3/4 + 1/4","options":["4/8","1","4/4","1/2"],"answer":1,"explanation":"3/4 + 1/4 = 4/4 = 1"},
    {"id":"ma-p6-03","level":"prim6","subject":"mathematics","question":"What is 7 × 8?","options":["54","56","48","64"],"answer":1,"explanation":"7 × 8 = 56."},
    {"id":"ma-p6-04","level":"prim6","subject":"mathematics","question":"Which of these is a prime number?","options":["9","12","7","15"],"answer":2,"explanation":"7 has only two factors (1 and 7) — it is prime."},
    {"id":"ma-p6-05","level":"prim6","subject":"mathematics","question":"Find the HCF of 12 and 18.","options":["2","3","6","9"],"answer":2,"explanation":"HCF of 12 and 18 is 6."},
    {"id":"ma-p6-06","level":"prim6","subject":"mathematics","question":"What is 25% of 80?","options":["15","20","25","30"],"answer":1,"explanation":"25% of 80 = 80 × 25/100 = 20."},
    {"id":"ma-p6-07","level":"prim6","subject":"mathematics","question":"Convert 0.75 to a fraction in simplest form.","options":["3/4","7/10","75/100","2/3"],"answer":0,"explanation":"0.75 = 75/100 = 3/4."},
    {"id":"ma-p6-08","level":"prim6","subject":"mathematics","question":"What is the next number: 2, 4, 6, 8, ___?","options":["9","10","11","12"],"answer":1,"explanation":"Arithmetic sequence adding 2 each time. 8 + 2 = 10."},
    {"id":"ma-p6-09","level":"prim6","subject":"mathematics","question":"How many sides does a hexagon have?","options":["5","6","7","8"],"answer":1,"explanation":"A hexagon has 6 sides."},
    {"id":"ma-p6-10","level":"prim6","subject":"mathematics","question":"What is 3² + 4²?","options":["25","24","20","49"],"answer":0,"explanation":"3² = 9, 4² = 16. 9 + 16 = 25."},
    {"id":"ma-p6-11","level":"prim6","subject":"mathematics","question":"Find the LCM of 4 and 6.","options":["2","12","24","4"],"answer":1,"explanation":"LCM of 4 and 6 is 12."},
    {"id":"ma-p6-12","level":"prim6","subject":"mathematics","question":"A rectangle has length 9cm and width 4cm. What is its perimeter?","options":["13cm","26cm","36cm","22cm"],"answer":1,"explanation":"Perimeter = 2(l + w) = 2(9 + 4) = 26 cm."},
    {"id":"ma-p6-13","level":"prim6","subject":"mathematics","question":"Express 3/5 as a decimal.","options":["0.3","0.35","0.6","0.5"],"answer":2,"explanation":"3 ÷ 5 = 0.6"},
    {"id":"ma-p6-14","level":"prim6","subject":"mathematics","question":"What is the place value of 5 in 3,547?","options":["ones","tens","hundreds","thousands"],"answer":1,"explanation":"5 is in the tens place (50 = 5 tens)."},
    {"id":"ma-p6-15","level":"prim6","subject":"mathematics","question":"Which is the largest fraction: 1/2, 2/3, 3/4, 4/5?","options":["1/2","2/3","3/4","4/5"],"answer":3,"explanation":"4/5 = 0.8 is the largest."},

    # ── Mathematics: JSS3 ──────────────────────────────────────
    {"id":"ma-js3-01","level":"js3","subject":"mathematics","question":"Solve for x: 2x + 6 = 14","options":["x = 4","x = 5","x = 3","x = 10"],"answer":0,"explanation":"2x = 14 - 6 = 8, so x = 8 ÷ 2 = 4."},
    {"id":"ma-js3-02","level":"js3","subject":"mathematics","question":"What is the area of a rectangle with length 8 cm and width 5 cm?","options":["13 cm²","40 cm²","26 cm²","80 cm²"],"answer":1,"explanation":"Area = length × width = 8 × 5 = 40 cm²."},
    {"id":"ma-js3-03","level":"js3","subject":"mathematics","question":"Simplify: 3(x + 2) - 2(x - 1)","options":["x + 8","5x + 8","x + 4","5x + 4"],"answer":0,"explanation":"3x + 6 - 2x + 2 = x + 8."},
    {"id":"ma-js3-04","level":"js3","subject":"mathematics","question":"Find the circumference of a circle with radius 7 cm (π = 22/7).","options":["22 cm","44 cm","154 cm","14 cm"],"answer":1,"explanation":"C = 2πr = 2 × 22/7 × 7 = 44 cm."},
    {"id":"ma-js3-05","level":"js3","subject":"mathematics","question":"What is the sum of angles in a triangle?","options":["90°","180°","270°","360°"],"answer":1,"explanation":"The sum of interior angles in any triangle is 180°."},
    {"id":"ma-js3-06","level":"js3","subject":"mathematics","question":"Factorize: x² - 9","options":["(x-3)(x-3)","(x+3)(x+3)","(x-3)(x+3)","(x-9)(x+1)"],"answer":2,"explanation":"x² - 9 is a difference of two squares: (x-3)(x+3)."},
    {"id":"ma-js3-07","level":"js3","subject":"mathematics","question":"If y = 3x - 5, what is y when x = 4?","options":["7","-7","12","-5"],"answer":0,"explanation":"y = 3(4) - 5 = 12 - 5 = 7."},
    {"id":"ma-js3-08","level":"js3","subject":"mathematics","question":"A car travels 240 km in 4 hours. What is its average speed?","options":["50 km/h","60 km/h","80 km/h","40 km/h"],"answer":1,"explanation":"Speed = distance ÷ time = 240 ÷ 4 = 60 km/h."},
    {"id":"ma-js3-09","level":"js3","subject":"mathematics","question":"Simplify: √144","options":["10","11","12","14"],"answer":2,"explanation":"√144 = 12 because 12 × 12 = 144."},
    {"id":"ma-js3-10","level":"js3","subject":"mathematics","question":"What is the median of: 3, 7, 2, 9, 5?","options":["3","5","7","6"],"answer":1,"explanation":"Arrange: 2,3,5,7,9. The middle value is 5."},
    {"id":"ma-js3-11","level":"js3","subject":"mathematics","question":"Convert 0.125 to a fraction.","options":["1/4","1/8","1/2","3/8"],"answer":1,"explanation":"0.125 = 1/8."},
    {"id":"ma-js3-12","level":"js3","subject":"mathematics","question":"A man is 45 years old. His son is 15. What is the ratio of their ages?","options":["3:1","2:1","4:1","1:3"],"answer":0,"explanation":"45:15 = 3:1."},
    {"id":"ma-js3-13","level":"js3","subject":"mathematics","question":"If 3x = 27, find x.","options":["7","8","9","6"],"answer":2,"explanation":"x = 27 ÷ 3 = 9."},
    {"id":"ma-js3-14","level":"js3","subject":"mathematics","question":"What is the volume of a cuboid 5 cm × 3 cm × 2 cm?","options":["10 cm³","30 cm³","25 cm³","15 cm³"],"answer":1,"explanation":"Volume = l × w × h = 5 × 3 × 2 = 30 cm³."},
    {"id":"ma-js3-15","level":"js3","subject":"mathematics","question":"Simplify: 2a + 3b - a + b","options":["a + 4b","a + 2b","3a + 4b","2a + 2b"],"answer":0,"explanation":"2a - a = a; 3b + b = 4b."},
    {"id":"ma-js3-16","level":"js3","subject":"mathematics","question":"Find the simple interest on ₦2000 at 5% per annum for 3 years.","options":["₦200","₦300","₦500","₦600"],"answer":1,"explanation":"SI = (P×R×T)/100 = (2000×5×3)/100 = ₦300."},
    {"id":"ma-js3-17","level":"js3","subject":"mathematics","question":"A store offers 20% discount on an item priced at ₦500. What is the selling price?","options":["₦400","₦480","₦450","₦420"],"answer":0,"explanation":"Discount = 20% of 500 = ₦100. Selling price = 500 - 100 = ₦400."},
    {"id":"ma-js3-18","level":"js3","subject":"mathematics","question":"Which of the following is NOT a factor of 24?","options":["6","8","12","9"],"answer":3,"explanation":"24 ÷ 9 = 2.67, not a whole number. 9 is not a factor of 24."},
    {"id":"ma-js3-19","level":"js3","subject":"mathematics","question":"Find the mode of: 2, 4, 2, 6, 3, 2, 5","options":["2","3","4","2 and 3"],"answer":0,"explanation":"2 appears 3 times — more than any other number. Mode is 2."},
    {"id":"ma-js3-20","level":"js3","subject":"mathematics","question":"What is the value of 2³ × 3²?","options":["48","72","54","64"],"answer":1,"explanation":"2³ = 8, 3² = 9. 8 × 9 = 72."},
    {"id":"ma-js3-21","level":"js3","subject":"mathematics","question":"Solve: x/3 = 12","options":["x = 4","x = 36","x = 15","x = 9"],"answer":1,"explanation":"Multiply both sides by 3: x = 12 × 3 = 36."},
    {"id":"ma-js3-22","level":"js3","subject":"mathematics","question":"Find the area of a triangle with base 8 cm and height 5 cm.","options":["20 cm²","40 cm²","13 cm²","10 cm²"],"answer":0,"explanation":"Area = ½ × base × height = ½ × 8 × 5 = 20 cm²."},
    {"id":"ma-js3-23","level":"js3","subject":"mathematics","question":"A boy shares 24 sweets among 3 friends equally. How many does each get?","options":["6","8","9","12"],"answer":1,"explanation":"24 ÷ 3 = 8 sweets each."},
    {"id":"ma-js3-24","level":"js3","subject":"mathematics","question":"What is the mean of: 10, 20, 30, 40, 50?","options":["20","30","25","40"],"answer":1,"explanation":"Mean = (10+20+30+40+50) ÷ 5 = 150 ÷ 5 = 30."},
    {"id":"ma-js3-25","level":"js3","subject":"mathematics","question":"Express 8 as a percentage of 200.","options":["2%","4%","8%","16%"],"answer":1,"explanation":"(8/200) × 100 = 4%."},

    # ── Mathematics: WASSCE ────────────────────────────────────
    {"id":"ma-ws-01","level":"wassce","subject":"mathematics","question":"Find the derivative of f(x) = 3x² + 2x.","options":["6x + 2","3x + 2","6x² + 2x","6 + 2"],"answer":0,"explanation":"Using the power rule: d/dx(3x²) = 6x and d/dx(2x) = 2."},
    {"id":"ma-ws-02","level":"wassce","subject":"mathematics","question":"If sin θ = 3/5, what is cos θ?","options":["3/5","4/5","5/4","5/3"],"answer":1,"explanation":"Using sin²θ + cos²θ = 1: cos²θ = 1 - 9/25 = 16/25, so cosθ = 4/5."},
    {"id":"ma-ws-03","level":"wassce","subject":"mathematics","question":"Find the equation of the line through (2, 3) and (4, 7).","options":["y = 2x - 1","y = 2x + 1","y = x + 1","y = 2x - 3"],"answer":0,"explanation":"Slope m = (7-3)/(4-2) = 2. Using point (2,3): y = 2x - 1."},
    {"id":"ma-ws-04","level":"wassce","subject":"mathematics","question":"Simplify: log₂8 + log₂4","options":["log₂32","5","32","log₂12"],"answer":1,"explanation":"log₂8 = 3, log₂4 = 2. So 3 + 2 = 5."},
    {"id":"ma-ws-05","level":"wassce","subject":"mathematics","question":"Differentiate y = x³ - 5x + 2","options":["3x² - 5","3x² + 5","x² - 5","3x - 5"],"answer":0,"explanation":"dy/dx = 3x² - 5."},
    {"id":"ma-ws-06","level":"wassce","subject":"mathematics","question":"Find the integral: ∫(2x + 1)dx","options":["x² + x + C","x² + x","2x² + x + C","x² + 2x + C"],"answer":0,"explanation":"∫2x dx = x² + C₁, ∫1 dx = x + C₂. So x² + x + C."},
    {"id":"ma-ws-07","level":"wassce","subject":"mathematics","question":"If a sequence has a₄ = 3 and a₁ = 15 with d = -4, what is the formula?","options":["aₙ = 15 - 4(n-1)","aₙ = 15 + 4(n-1)","aₙ = 3 - 4(n-1)","aₙ = 3 + 15(n-1)"],"answer":0,"explanation":"Arithmetic sequence: aₙ = a₁ + (n-1)d = 15 - 4(n-1)."},
    {"id":"ma-ws-08","level":"wassce","subject":"mathematics","question":"Find the sum of the first 5 terms of 2, 6, 18, 54,...","options":["242","162","726","484"],"answer":0,"explanation":"Geometric series: S₅ = a(rⁿ-1)/(r-1) = 2(3⁵-1)/(3-1) = 242."},
    {"id":"ma-ws-09","level":"wassce","subject":"mathematics","question":"A cone has radius 3 cm and height 4 cm. Find its volume (π = 3.142).","options":["37.70 cm³","113.10 cm³","75.40 cm³","150.80 cm³"],"answer":0,"explanation":"V = ⅓πr²h = ⅓ × 3.142 × 9 × 4 ≈ 37.70 cm³."},
    {"id":"ma-ws-10","level":"wassce","subject":"mathematics","question":"Find the angle between the vectors (1,2) and (3,1).","options":["30°","45°","60°","approximately 26.6°"],"answer":1,"explanation":"cos θ = (1×3 + 2×1)/(√5 × √10) = 5/√50 ≈ 0.707, so θ ≈ 45°."},
    {"id":"ma-ws-11","level":"wassce","subject":"mathematics","question":"Solve: x² - 5x + 6 = 0","options":["x = 2 or x = 3","x = 1 or x = 6","x = -2 or x = -3","x = 2 only"],"answer":0,"explanation":"Factor: (x-2)(x-3) = 0, so x = 2 or x = 3."},
    {"id":"ma-ws-12","level":"wassce","subject":"mathematics","question":"Find dy/dx if y = sin(3x)","options":["cos(3x)","3cos(3x)","-3cos(3x)","3sin(3x)"],"answer":1,"explanation":"Using the chain rule: dy/dx = cos(3x) × 3 = 3cos(3x)."},
    {"id":"ma-ws-13","level":"wassce","subject":"mathematics","question":"Find the distance between points (3, 4) and (7, 1).","options":["3","4","5","6"],"answer":2,"explanation":"d = √[(7-3)² + (1-4)²] = √[16 + 9] = √25 = 5."},
    {"id":"ma-ws-14","level":"wassce","subject":"mathematics","question":"If a matrix A is 2×3, and B is 3×4, what is the size of AB?","options":["2×4","3×3","2×3","3×4"],"answer":0,"explanation":"Result has rows of first × columns of second: 2×3 × 3×4 = 2×4."},
    {"id":"ma-ws-15","level":"wassce","subject":"mathematics","question":"Find the value of sin 60°.","options":["1/2","√3/2","√2/2","1"],"answer":1,"explanation":"sin 60° = √3/2 (from the 30-60-90 triangle)."},
    {"id":"ma-ws-16","level":"wassce","subject":"mathematics","question":"Find the equation of the tangent to y = x² at x = 1.","options":["y = 2x - 1","y = 2x + 1","y = x + 1","y = 2x"],"answer":0,"explanation":"dy/dx = 2x. At x=1, slope = 2. Point: (1,1). So y - 1 = 2(x - 1): y = 2x - 1."},
    {"id":"ma-ws-17","level":"wassce","subject":"mathematics","question":"If two events are mutually exclusive, what is P(A and B)?","options":["P(A) + P(B)","P(A) × P(B)","0","1"],"answer":2,"explanation":"Mutually exclusive events cannot happen together, so P(A and B) = 0."},
    {"id":"ma-ws-18","level":"wassce","subject":"mathematics","question":"Find the area between the curve y = x² and the line y = 4.","options":["10.67 sq units","16 sq units","8 sq units","5.33 sq units"],"answer":0,"explanation":"Area = ∫(-2 to 2) (4 - x²) dx = 32/3 ≈ 10.67."},
    {"id":"ma-ws-19","level":"wassce","subject":"mathematics","question":"Solve: 2ˣ = 32","options":["x = 4","x = 5","x = 6","x = 8"],"answer":1,"explanation":"32 = 2⁵, so 2ˣ = 2⁵ gives x = 5."},
    {"id":"ma-ws-20","level":"wassce","subject":"mathematics","question":"What is the limit of (x²-1)/(x-1) as x approaches 1?","options":["0","1","2","undefined"],"answer":2,"explanation":"Factor: (x-1)(x+1)/(x-1) = x+1. As x → 1, limit = 1+1 = 2."},

    # ── Mathematics: JAMB ──────────────────────────────────────
    {"id":"ma-jb-01","level":"jamb","subject":"mathematics","question":"Evaluate: log₂(32)","options":["4","5","6","8"],"answer":1,"explanation":"2⁵ = 32, so log₂(32) = 5."},
    {"id":"ma-jb-02","level":"jamb","subject":"mathematics","question":"The sum of the interior angles of a hexagon is:","options":["360°","540°","720°","900°"],"answer":2,"explanation":"Interior angle sum = (n-2) × 180°. For hexagon (n=6): (6-2) × 180 = 720°."},
    {"id":"ma-jb-03","level":"jamb","subject":"mathematics","question":"Find the derivative of f(x) = 5x³ - 3x + 7.","options":["15x² - 3","15x² + 3","5x² - 3","3x² - 3"],"answer":0,"explanation":"f'(x) = 3×5x² - 3 = 15x² - 3."},
    {"id":"ma-jb-04","level":"jamb","subject":"mathematics","question":"If P = {2, 4, 6} and Q = {4, 6, 8}, what is P ∪ Q?","options":["{2,4,6,8}","{4,6}","{2,8}","{}"],"answer":0,"explanation":"The union contains all elements in either set: {2,4,6,8}."},
    {"id":"ma-jb-05","level":"jamb","subject":"mathematics","question":"Simplify: (x²y³)²","options":["x⁴y⁵","x⁴y⁶","x⁴y⁹","x²y⁶"],"answer":1,"explanation":"(x²)² = x⁴, (y³)² = y⁶. So x⁴y⁶."},
    {"id":"ma-jb-06","level":"jamb","subject":"mathematics","question":"If tan θ = 1, what is θ?","options":["30°","45°","60°","90°"],"answer":1,"explanation":"tan 45° = 1. So θ = 45°."},
    {"id":"ma-jb-07","level":"jamb","subject":"mathematics","question":"The 7th term of an AP is 20 and the first term is 8. Find the common difference.","options":["2","12/7","3","4"],"answer":0,"explanation":"a₇ = a₁ + 6d → 20 = 8 + 6d → 6d = 12 → d = 2."},
    {"id":"ma-jb-08","level":"jamb","subject":"mathematics","question":"Solve: x² - 4x + 4 = 0","options":["x = 2","x = -2","x = 2 or x = -2","x = 4"],"answer":0,"explanation":"(x-2)² = 0, so x = 2 (repeated root)."},
    {"id":"ma-jb-09","level":"jamb","subject":"mathematics","question":"If 3ˣ⁺¹ = 81, find x.","options":["1","2","3","4"],"answer":2,"explanation":"81 = 3⁴. So 3ˣ⁺¹ = 3⁴ → x+1 = 4 → x = 3."},
    {"id":"ma-jb-10","level":"jamb","subject":"mathematics","question":"Find the range of the data: 3, 7, 2, 9, 5, 12","options":["7","10","12","2"],"answer":1,"explanation":"Range = highest - lowest = 12 - 2 = 10."},
    {"id":"ma-jb-11","level":"jamb","subject":"mathematics","question":"What is the 5th term of the GP: 3, 6, 12, 24,...?","options":["24","36","48","96"],"answer":2,"explanation":"GP: a=3, r=2. T₅ = ar⁴ = 3×2⁴ = 48."},
    {"id":"ma-jb-12","level":"jamb","subject":"mathematics","question":"Find the gradient of the line 2y - 4x = 6.","options":["2","-2","4","-4"],"answer":0,"explanation":"2y = 4x + 6 → y = 2x + 3. Gradient = 2."},
    {"id":"ma-jb-13","level":"jamb","subject":"mathematics","question":"The probability that a tossed coin lands on heads is:","options":["0","1/4","1/2","1"],"answer":2,"explanation":"A fair coin has two equally likely outcomes. P(heads) = 1/2."},
    {"id":"ma-jb-14","level":"jamb","subject":"mathematics","question":"Simplify: (a+b)² - (a-b)²","options":["4ab","2a²b²","2ab","a² - b²"],"answer":0,"explanation":"Using the difference of squares identity: (a+b)² - (a-b)² = 4ab."},
    {"id":"ma-jb-15","level":"jamb","subject":"mathematics","question":"Find the LCM of 8, 12, and 16.","options":["24","32","48","96"],"answer":2,"explanation":"LCM = 2⁴ × 3 = 48."},
    {"id":"ma-jb-16","level":"jamb","subject":"mathematics","question":"If y varies directly as x and y = 12 when x = 4, find y when x = 10.","options":["24","30","48","20"],"answer":1,"explanation":"y = kx. 12 = k×4 → k = 3. When x=10, y = 3×10 = 30."},
    {"id":"ma-jb-17","level":"jamb","subject":"mathematics","question":"Find the discriminant of x² + 4x + 4 = 0.","options":["0","8","16","32"],"answer":0,"explanation":"Discriminant = b² - 4ac = 16 - 16 = 0."},
    {"id":"ma-jb-18","level":"jamb","subject":"mathematics","question":"The point (3, -2) lies in which quadrant?","options":["I","II","III","IV"],"answer":3,"explanation":"Positive x, negative y = Quadrant IV."},
    {"id":"ma-jb-19","level":"jamb","subject":"mathematics","question":"Simplify: 2⁴ × 2⁵","options":["2⁹","2²⁰","4⁹","4²⁰"],"answer":0,"explanation":"When multiplying powers with the same base, add exponents: 2⁴⁺⁵ = 2⁹."},
    {"id":"ma-jb-20","level":"jamb","subject":"mathematics","question":"Find ∫sin x dx","options":["cos x + C","-cos x + C","sin x + C","-sin x + C"],"answer":1,"explanation":"The integral of sin x is -cos x + C."},
    {"id":"ma-jb-21","level":"jamb","subject":"mathematics","question":"What is the complement of P(A) = 0.35?","options":["0.35","0.65","0.5","0.1"],"answer":1,"explanation":"P(not A) = 1 - P(A) = 1 - 0.35 = 0.65."},
    {"id":"ma-jb-22","level":"jamb","subject":"mathematics","question":"Simplify: √50","options":["5√2","2√5","25","10"],"answer":0,"explanation":"√50 = √(25×2) = 5√2."},
    {"id":"ma-jb-23","level":"jamb","subject":"mathematics","question":"How many ways can 3 books be arranged on a shelf from 5 different books?","options":["15","60","120","5"],"answer":1,"explanation":"P(5,3) = 5×4×3 = 60 arrangements."},
    {"id":"ma-jb-24","level":"jamb","subject":"mathematics","question":"If cos A = 5/13, find sin A (A in the first quadrant).","options":["5/13","12/13","13/5","13/12"],"answer":1,"explanation":"sin²A + cos²A = 1. sin²A = 1 - 25/169 = 144/169. sin A = 12/13."},
    {"id":"ma-jb-25","level":"jamb","subject":"mathematics","question":"Express 0.00347 in standard form.","options":["3.47 × 10⁻³","3.47 × 10⁻²","34.7 × 10⁻⁴","3.47 × 10³"],"answer":0,"explanation":"0.00347 = 3.47 × 10⁻³."},

    # ── Civic Education: Primary 6 ──────────────────────────────
    {"id":"cv-p6-01","level":"prim6","subject":"civic","question":"Nigeria's national anthem was written by:","options":["Wole Soyinka","John Sowah","Edna O'Loughlin","Nnamdi Azikiwe"],"answer":2,"explanation":"The former national anthem was written by a joint committee including Edna O'Loughlin."},
    {"id":"cv-p6-02","level":"prim6","subject":"civic","question":"How many local government areas does Nigeria have?","options":["360","774","36","63"],"answer":1,"explanation":"Nigeria has 774 local government areas."},
    {"id":"cv-p6-03","level":"prim6","subject":"civic","question":"Nigeria has how many states?","options":["36","37","35","34"],"answer":0,"explanation":"Nigeria has 36 states and the FCT Abuja."},
    {"id":"cv-p6-04","level":"prim6","subject":"civic","question":"The Nigerian coat of arms has how many stars?","options":["36","12","7","6"],"answer":2,"explanation":"The Nigerian coat of arms has 7 stars representing the 7 Northern protectorates."},
    {"id":"cv-p6-05","level":"prim6","subject":"civic","question":"Which of these is a right of a Nigerian child?","options":["Right to work","Right to free education","Right to vote","Right to drive"],"answer":1,"explanation":"The Child's Rights Act guarantees the right to free basic education."},
    {"id":"cv-p6-06","level":"prim6","subject":"civic","question":"What is the capital of Nigeria?","options":["Lagos","Kano","Abuja","Ibadan"],"answer":2,"explanation":"Abuja became Nigeria's capital on 12 December 1991."},
    {"id":"cv-p6-07","level":"prim6","subject":"civic","question":"Nigeria became a republic in:","options":["1960","1963","1979","1999"],"answer":1,"explanation":"Nigeria became a republic on 1 October 1963."},
    {"id":"cv-p6-08","level":"prim6","subject":"civic","question":"Which animal appears on the Nigerian coat of arms?","options":["Lion","Eagle","Tiger","Camel"],"answer":1,"explanation":"The Nigerian coat of arms features an eagle on top."},
    {"id":"cv-p6-09","level":"prim6","subject":"civic","question":"What is the motto of Nigeria?","options":["Unity and Faith","Peace and Progress","Order and Unity","Freedom and Justice"],"answer":0,"explanation":"Nigeria's motto is Unity and Faith, Peace and Progress."},
    {"id":"cv-p6-10","level":"prim6","subject":"civic","question":"Which ethnic group is the most populous in Nigeria?","options":["Igbo","Yoruba","Hausa-Fulani","Ijaw"],"answer":2,"explanation":"The Hausa-Fulani are generally considered the largest ethnic group."},
    {"id":"cv-p6-11","level":"prim6","subject":"civic","question":"What colour is the middle stripe of the Nigerian flag?","options":["Red","Green","White","Black"],"answer":2,"explanation":"The Nigerian flag has three vertical bands: green, white, green."},
    {"id":"cv-p6-12","level":"prim6","subject":"civic","question":"Nigeria gained independence on:","options":["October 1, 1960","June 12, 1993","January 15, 1966","May 29, 1999"],"answer":0,"explanation":"Nigeria gained independence from Britain on October 1, 1960."},
    {"id":"cv-p6-13","level":"prim6","subject":"civic","question":"The Nigerian currency is called the:","options":["Naira","Cedi","Pound","Dollar"],"answer":0,"explanation":"Nigeria's currency is the Naira (₦), introduced in 1973."},
    {"id":"cv-p6-14","level":"prim6","subject":"civic","question":"How many geo-political zones does Nigeria have?","options":["5","6","7","8"],"answer":1,"explanation":"Nigeria has 6 geo-political zones."},
    {"id":"cv-p6-15","level":"prim6","subject":"civic","question":"Which of these is a value of good citizenship?","options":["Corruption","Honesty","Dishonesty","Indifference"],"answer":1,"explanation":"Honesty is a core value of good citizenship."},

    # ── Civic Education: JSS3 ──────────────────────────────────
    {"id":"cv-js3-01","level":"js3","subject":"civic","question":"The fundamental objectives of the Nigerian state are outlined in which section of the 1999 Constitution?","options":["Section 1","Section 14","Section 34","Section 17"],"answer":3,"explanation":"Section 17 of the 1999 Constitution outlines the Fundamental Objectives."},
    {"id":"cv-js3-02","level":"js3","subject":"civic","question":"What is the minimum age for voting in Nigeria?","options":["16","18","21","25"],"answer":1,"explanation":"The minimum voting age in Nigeria is 18 years."},
    {"id":"cv-js3-03","level":"js3","subject":"civic","question":"Which arm of government is responsible for making laws in Nigeria?","options":["Executive","Legislature","Judiciary","Military"],"answer":1,"explanation":"The Legislature makes laws at federal and state levels."},
    {"id":"cv-js3-04","level":"js3","subject":"civic","question":"The principle of Rule of Law means:","options":["The president can do anything","Everyone, including government, is subject to the law","Only lawyers can interpret laws","Laws are not needed"],"answer":1,"explanation":"The Rule of Law means no one is above the law."},
    {"id":"cv-js3-05","level":"js3","subject":"civic","question":"A person who is above 18 years and has Nigerian citizenship is eligible to:","options":["vote only","vote and be voted for","drive only","pay taxes only"],"answer":1,"explanation":"Citizens above 18 can both vote and contest elections."},
    {"id":"cv-js3-06","level":"js3","subject":"civic","question":"INEC is responsible for:","options":["Building roads","Conducting elections","Printing money","Managing the military"],"answer":1,"explanation":"INEC organizes and conducts all federal and state elections."},
    {"id":"cv-js3-07","level":"js3","subject":"civic","question":"Which of these is a fundamental human right in Nigeria's Constitution?","options":["Right to free housing","Right to personal liberty","Right to free cars","Right to free healthcare"],"answer":1,"explanation":"The right to personal liberty is guaranteed in Chapter IV of the 1999 Constitution."},
    {"id":"cv-js3-08","level":"js3","subject":"civic","question":"National consciousness can be promoted through:","options":["Tribalism and discrimination","Patriotism, education and cultural unity","Isolation from other nations","Religious conflicts"],"answer":1,"explanation":"National consciousness is built through patriotism, education, and promoting unity."},
    {"id":"cv-js3-09","level":"js3","subject":"civic","question":"A person who owes loyalty only to himself and not to the state is practicing:","options":["Patriotism","Citizen diplomacy","National disloyalty","Civic responsibility"],"answer":2,"explanation":"Refusing to show loyalty to one's country is an act of disloyalty."},
    {"id":"cv-js3-10","level":"js3","subject":"civic","question":"Which of these is a duty of a Nigerian citizen?","options":["Avoid paying taxes","Disrespect the national anthem","Defend the nation","Engage in corruption"],"answer":2,"explanation":"Defending the nation is one of the fundamental duties in the Constitution."},
    {"id":"cv-js3-11","level":"js3","subject":"civic","question":"The police in Nigeria is under which level of government?","options":["Local government","State government","Federal government","Traditional rulers"],"answer":2,"explanation":"The Nigeria Police Force is a federal institution."},
    {"id":"cv-js3-12","level":"js3","subject":"civic","question":"What does federal character mean?","options":["All positions go to one region","Fair representation of states and ethnic groups in government appointments","Only federal workers matter","States should not exist"],"answer":1,"explanation":"Federal character ensures government appointments reflect Nigeria's diversity."},
    {"id":"cv-js3-13","level":"js3","subject":"civic","question":"The 1999 Constitution came into effect on:","options":["October 1, 1960","May 29, 1999","January 15, 1966","June 12, 1993"],"answer":1,"explanation":"The 1999 Constitution came into effect on 29 May 1999."},
    {"id":"cv-js3-14","level":"js3","subject":"civic","question":"National unity is important because it:","options":["Creates division","Promotes peace, stability and development","Increases ethnic conflicts","Weakens the nation"],"answer":1,"explanation":"National unity fosters peace, stability, and development."},
    {"id":"cv-js3-15","level":"js3","subject":"civic","question":"Which of these is a means of promoting national unity?","options":["Election rigging","Observing public holidays like Independence Day","Bribery and corruption","Violence and destruction"],"answer":1,"explanation":"Celebrating national holidays reinforces shared identity and national pride."},
    {"id":"cv-js3-16","level":"js3","subject":"civic","question":"A refugee is:","options":["Someone who travels for vacation","A person who flees their country due to persecution or war","A person who lives permanently in another country","Someone who crosses borders for trade"],"answer":1,"explanation":"A refugee is someone forced to flee due to war, persecution, or natural disaster."},
    {"id":"cv-js3-17","level":"js3","subject":"civic","question":"Which body makes laws for the Federal Capital Territory (FCT)?","options":["State house of assembly","National Assembly","Local government council","Traditional council"],"answer":1,"explanation":"The National Assembly makes laws for the FCT."},
    {"id":"cv-js3-18","level":"js3","subject":"civic","question":"Civic responsibility means:","options":["Only paying taxes","The obligations citizens owe to the state and society","Staying away from politics","Having no duties"],"answer":1,"explanation":"Civic responsibility includes duties like paying taxes and obeying laws."},
    {"id":"cv-js3-19","level":"js3","subject":"civic","question":"Which document guarantees the rights of a Nigerian child?","options":["The Criminal Code","The Child's Rights Act 2003","The Electoral Act","The Land Use Act"],"answer":1,"explanation":"The Child's Rights Act 2003 provides a comprehensive legal framework for protecting children."},
    {"id":"cv-js3-20","level":"js3","subject":"civic","question":"Human trafficking is the:","options":["Legal movement of people","Illegal recruitment and transportation of people for exploitation","Export of goods","A form of tourism"],"answer":1,"explanation":"Human trafficking involves recruitment and exploitation of people."},

    # ── Civic Education: WASSCE ────────────────────────────────
    {"id":"cv-ws-01","level":"wassce","subject":"civic","question":"Which arm of government is responsible for interpreting laws?","options":["Executive","Legislature","Judiciary","Police"],"answer":2,"explanation":"The Judiciary interprets laws and administers justice."},
    {"id":"cv-ws-02","level":"wassce","subject":"civic","question":"The fundamental objectives of the Nigerian state are in:","options":["Chapter I","Chapter II","Chapter III","Chapter IV"],"answer":1,"explanation":"Chapter II of the 1999 Constitution contains the Fundamental Objectives."},
    {"id":"cv-ws-03","level":"wassce","subject":"civic","question":"The doctrine of separation of powers means:","options":["Three arms completely independent with checks","One person controls all arms","Only the executive matters","The legislature controls the police"],"answer":0,"explanation":"Separation of powers divides government into three branches with mutual checks."},
    {"id":"cv-ws-04","level":"wassce","subject":"civic","question":"Which body has the power to impeach the President in Nigeria?","options":["Supreme Court","Armed Forces","National Assembly by two-thirds majority","State Governors"],"answer":2,"explanation":"The National Assembly can impeach the President by a two-thirds majority."},
    {"id":"cv-ws-05","level":"wassce","subject":"civic","question":"A writ of habeas corpus is used to:","options":["Punish a criminal","Release a person who has been unlawfully detained","Tax citizens","Appoint judges"],"answer":1,"explanation":"Habeas corpus is a court order to produce a detained person before a judge."},
    {"id":"cv-ws-06","level":"wassce","subject":"civic","question":"The right to privacy is guaranteed under which fundamental right?","options":["Right to life","Right to dignity","Right to private and family life","Right to assembly"],"answer":2,"explanation":"The right to private and family life protects citizens from arbitrary intrusion."},
    {"id":"cv-ws-07","level":"wassce","subject":"civic","question":"Which of these is NOT a fundamental human right in Nigeria's Constitution?","options":["Right to life","Right to own property anywhere in Nigeria","Right to free university education","Right to dignity"],"answer":2,"explanation":"The Constitution guarantees free basic (not university) education."},
    {"id":"cv-ws-08","level":"wassce","subject":"civic","question":"The principle of supremacy of the Constitution means:","options":["The president is above the law","The Constitution is the highest law of the land","State governors are above the Constitution","Only courts can make rules"],"answer":1,"explanation":"All laws and authorities must conform to the Constitution."},
    {"id":"cv-ws-09","level":"wassce","subject":"civic","question":"The National Assembly consists of:","options":["The Senate only","The House of Representatives only","The Senate and House of Representatives","The President and Vice President"],"answer":2,"explanation":"The National Assembly is bicameral: Senate + House of Representatives."},
    {"id":"cv-ws-10","level":"wassce","subject":"civic","question":"The power of judicial review means:","options":["The judiciary can make laws","Courts can declare laws unconstitutional","The police control the courts","Only the Supreme Court can make decisions"],"answer":1,"explanation":"Judicial review is the power of courts to invalidate unconstitutional laws."},
    {"id":"cv-ws-11","level":"wassce","subject":"civic","question":"A bill becomes an Act when:","options":["The President signs it","Only the Senate approves it","The governor approves it","It is published in the newspaper"],"answer":0,"explanation":"After both chambers pass a bill, the President signs it for it to become law."},
    {"id":"cv-ws-12","level":"wassce","subject":"civic","question":"The right to a fair hearing means:","options":["A person can be tried without evidence","Every accused person has the right to be heard","Only the rich can have hearings","The police can judge cases"],"answer":1,"explanation":"Fair hearing (audi alteram partem) means no one shall be condemned without being given a chance to respond."},
    {"id":"cv-ws-13","level":"wassce","subject":"civic","question":"Civil society organizations (CSOs) perform which of these functions?","options":["Only electing the president","Monitoring government and advocating for citizens","Only collecting taxes","Controlling the military"],"answer":1,"explanation":"CSOs serve as watchdogs, advocate for citizens, and promote accountability."},
    {"id":"cv-ws-14","level":"wassce","subject":"civic","question":"Which arm of government implements and enforces laws?","options":["Legislature","Executive","Judiciary","Police"],"answer":1,"explanation":"The Executive implements and enforces laws."},

    # ── Government: JSS3 ───────────────────────────────────────
    {"id":"gv-js3-01","level":"js3","subject":"government","question":"Nigeria practices which system of government?","options":["Presidential","Parliamentary","Monarchical","Military"],"answer":0,"explanation":"Nigeria uses a Presidential system."},
    {"id":"gv-js3-02","level":"js3","subject":"government","question":"Nigeria became a republic in what year?","options":["1960","1963","1979","1999"],"answer":1,"explanation":"Nigeria became a republic on 1 October 1963."},
    {"id":"gv-js3-03","level":"js3","subject":"government","question":"How many senators represent each state in Nigeria's Senate?","options":["2","3","4","5"],"answer":1,"explanation":"Each of Nigeria's 36 states is represented by 3 senators."},
    {"id":"gv-js3-04","level":"js3","subject":"government","question":"The Federal Character Commission was established to:","options":["Increase presidential powers","Ensure fair representation across states and ethnic groups","Appoint all civil servants","Control state governors"],"answer":1,"explanation":"The FCC ensures government appointments reflect Nigeria's federal character."},
    {"id":"gv-js3-05","level":"js3","subject":"government","question":"The 1960 Constitution of Nigeria was a:","options":["Republican constitution","Colonial (Independence) constitution","Military constitution","Revolutionary constitution"],"answer":1,"explanation":"The 1960 Constitution was the Independence Constitution."},
    {"id":"gv-js3-06","level":"js3","subject":"government","question":"A monarchy with a Prime Minister is found in:","options":["Nigeria","Saudi Arabia","United Kingdom","United States"],"answer":2,"explanation":"The UK is a constitutional monarchy with a Prime Minister."},
    {"id":"gv-js3-07","level":"js3","subject":"government","question":"Which of these is a feature of a federal system?","options":["Concentration of power in one level","Sharing of powers between two or more levels of government","A single central government only","No written constitution"],"answer":1,"explanation":"Federalism divides governmental powers between central and state governments."},
    {"id":"gv-js3-08","level":"js3","subject":"government","question":"The first military coup in Nigeria took place in:","options":["1966","1970","1979","1993"],"answer":0,"explanation":"The first military coup occurred on 15 January 1966."},
    {"id":"gv-js3-09","level":"js3","subject":"government","question":"In a parliamentary system, the head of government is the:","options":["President","Governor","Prime Minister","Monarch"],"answer":2,"explanation":"In parliamentary systems, the Prime Minister is the head of government."},
    {"id":"gv-js3-10","level":"js3","subject":"government","question":"The political party formed by Nnamdi Azikiwe was the:","options":["Action Group","Northern People's Congress","National Council of Nigeria and the Cameroons (NCNC)","UPGA"],"answer":2,"explanation":"Nnamdi Azikiwe founded the NCNC in 1947."},
    {"id":"gv-js3-11","level":"js3","subject":"government","question":"Which organ of government can remove a governor from office?","options":["The Supreme Court","The State House of Assembly","The Federal Executive Council","The Police"],"answer":1,"explanation":"A governor can be removed by impeachment by two-thirds of the State House of Assembly."},
    {"id":"gv-js3-12","level":"js3","subject":"government","question":"The process by which citizens choose their representatives is called:","options":["Apportionment","Election","Nomination","Census"],"answer":1,"explanation":"An election is the process by which citizens choose their representatives."},
    {"id":"gv-js3-13","level":"js3","subject":"government","question":"A confederation is characterized by:","options":["A strong central government","Sovereign states with a weak central body","A single unified state","No government at all"],"answer":1,"explanation":"In a confederation, member states retain sovereignty while forming a weak central body."},
    {"id":"gv-js3-14","level":"js3","subject":"government","question":"The Aburi Accord was signed in:","options":["January 1966","September 1966","January 1967","June 1966"],"answer":0,"explanation":"The Aburi Accord was signed in January 1966."},
    {"id":"gv-js3-15","level":"js3","subject":"government","question":"The 1979 Constitution introduced:","options":["Parliamentary system","Presidential system","Military rule","Confederation"],"answer":1,"explanation":"The 1979 Constitution introduced the American-style Presidential system."},

    # ── Government: WASSCE ────────────────────────────────────
    {"id":"gv-ws-01","level":"wassce","subject":"government","question":"The principle of separation of powers means:","options":["Three arms completely independent","Powers divided among executive, legislature, and judiciary with checks","Only the president can make laws","The military controls all branches"],"answer":1,"explanation":"Separation of powers divides government into three branches with distinct functions and mutual checks."},
    {"id":"gv-ws-02","level":"wassce","subject":"government","question":"The power to approve treaties and appointments belongs to the:","options":["Executive","Legislature","Judiciary","State governments"],"answer":1,"explanation":"The Senate has the power to confirm treaties, appointments, and impeachments."},
    {"id":"gv-ws-03","level":"wassce","subject":"government","question":"Which body has the power to declare a state of emergency?","options":["The Senate alone","The President alone","The National Assembly by a two-thirds majority","State governors"],"answer":2,"explanation":"A state of emergency requires approval by two-thirds of both chambers."},
    {"id":"gv-ws-04","level":"wassce","subject":"government","question":"The doctrine of checks and balances is used to:","options":["Allow unlimited power to the president","Prevent any one arm of government from abusing its power","Remove all government checks","Prevent elections"],"answer":1,"explanation":"Checks and balances allow each arm to limit the powers of the others."},
    {"id":"gv-ws-05","level":"wassce","subject":"government","question":"Which of these is a function of the judiciary?","options":["Making policies","Enforcing laws","Interpreting and applying the law","Printing money"],"answer":2,"explanation":"The judiciary interprets the law and applies it in courts."},
    {"id":"gv-ws-06","level":"wassce","subject":"government","question":"The power of the National Assembly to investigate the executive is called:","options":["Appropriation","Impeachment","Oversight","Confirmation"],"answer":2,"explanation":"Oversight powers allow the National Assembly to investigate government activities."},
    {"id":"gv-ws-07","level":"wassce","subject":"government","question":"A constitution is defined as:","options":["A book about history","The supreme law of a country","A list of government employees","A guide for the military"],"answer":1,"explanation":"A constitution is the supreme law that outlines government structure and rights."},
    {"id":"gv-ws-08","level":"wassce","subject":"government","question":"The Supreme Court of Nigeria is the:","options":["Lowest court of appeal","Final court of appeal in Nigeria","Court of first instance for criminal cases","Court for military personnel only"],"answer":1,"explanation":"The Supreme Court is the highest court in Nigeria."},
    {"id":"gv-ws-09","level":"wassce","subject":"government","question":"The Federal Character principle ensures that government appointments:","options":["Go to the president only","Reflect the diversity of Nigeria","Go to the military","Go to the courts"],"answer":1,"explanation":"Federal character requires appointments to reflect Nigeria's ethnic, regional, and religious diversity."},
    {"id":"gv-ws-10","level":"wassce","subject":"government","question":"A political party is best described as:","options":["A social club","An organization that seeks to control government by winning elections","A religious organization","A sports team"],"answer":1,"explanation":"A political party is an organized group that seeks political power through elections."},
    {"id":"gv-ws-11","level":"wassce","subject":"government","question":"The concept of federation means:","options":["One central government with no states","A union of states with a shared central government","A single state with no government","A military government"],"answer":1,"explanation":"A federation is a union of semi-autonomous states sharing power with a central government."},
    {"id":"gv-ws-12","level":"wassce","subject":"government","question":"Which system of government originated in the United States?","options":["Parliamentary system","Presidential system","Monarchical system","Confucian system"],"answer":1,"explanation":"The Presidential system originated in the United States."},
    {"id":"gv-ws-13","level":"wassce","subject":"government","question":"The power to originate money bills belongs to the:","options":["Senate","House of Representatives","President","Supreme Court"],"answer":1,"explanation":"Only the House of Representatives can originate money bills."},
    {"id":"gv-ws-14","level":"wassce","subject":"government","question":"A referendum is:","options":["A general election","A direct vote by citizens on a specific issue or law","A parliamentary debate","A court judgment"],"answer":1,"explanation":"A referendum is a direct vote in which citizens approve or reject a specific proposal."},
    {"id":"gv-ws-15","level":"wassce","subject":"government","question":"The 1999 Constitution can be amended by:","options":["The President alone","Two-thirds of National Assembly and two-thirds of state assemblies","Simple majority of citizens","The military"],"answer":1,"explanation":"Amending the Constitution requires two-thirds of the National Assembly and two-thirds of state assemblies."},
    {"id":"gv-ws-16","level":"wassce","subject":"government","question":"What is the main function of political socialization?","options":["To elect leaders","To transmit political values from one generation to the next","To create political parties","To fight wars"],"answer":1,"explanation":"Political socialization teaches citizens about politics through family, school, and media."},
    {"id":"gv-ws-17","level":"wassce","subject":"government","question":"Public opinion is best described as:","options":["The opinion of the government only","The aggregate views of citizens on public issues","The opinion of one person","The opinion of the court"],"answer":1,"explanation":"Public opinion is the collective views of the population on matters affecting the nation."},
    {"id":"gv-ws-18","level":"wassce","subject":"government","question":"Which agency is responsible for anti-corruption in Nigeria?","options":["INEC","EFCC and ICPC","NSA","DSS"],"answer":1,"explanation":"The EFCC and ICPC fight corruption in Nigeria."},
    {"id":"gv-ws-19","level":"wassce","subject":"government","question":"A constitution that cannot be easily changed is said to be:","options":["Flexible","Rigid","Democratic","Dictatorial"],"answer":1,"explanation":"A rigid (entrenched) constitution requires a special, difficult process for amendment."},
    {"id":"gv-ws-20","level":"wassce","subject":"government","question":"Which of the following is a characteristic of a good constitution?","options":["It should be long and complex","It should be supreme, clear, and protect fundamental rights","It should be written by only one person","It should favor one group over others"],"answer":1,"explanation":"A good constitution is supreme, clear, comprehensive, and protects rights."},
]


def convert_question(q: dict) -> dict:
    """Convert eko-learn format to ExamPrep NG format."""
    level   = q["id"].split("-")[1]  # e.g. "p6", "js3", "ws", "jb"
    exam    = LEVEL_MAP.get(level, "BECE")
    subject = SUBJECT_MAP.get(q["subject"], q["subject"])
    options = q["options"]

    # Build options list with letter IDs
    letters = ["a", "b", "c", "d"]
    option_list = [{"id": letters[i], "text": options[i]} for i in range(len(options))]
    correct_id = letters[q["answer"]] if q["answer"] < len(letters) else "a"

    return {
        "id":          f"eko-{q['id']}",
        "exam":        exam,
        "subject":     subject,
        "year":        2024,
        "topic":       "General",
        "prompt":      q["question"],
        "options":     option_list,
        "correctOptionId": correct_id,
        "explanation": q.get("explanation", ""),
    }


def main():
    # Load existing questions.json
    with open(SRC, "r", encoding="utf-8") as f:
        data = json.load(f)

    existing_ids = {q["id"] for q in data["questions"]}
    print(f"Existing questions: {len(data['questions'])}")

    # Add WAEC exam if missing
    exam_ids = {e["id"] for e in data["exams"]}
    if "WAEC" not in exam_ids:
        data["exams"].insert(0, {
            "id": "WAEC",
            "name": "WAEC",
            "fullName": "West African Examinations Council (SSCE)",
            "description": "Senior secondary school leaving exam (West Africa).",
            "durationMinutes": 60,
        })
        print("Added WAEC exam")

    # Convert and deduplicate
    new_qs = []
    for q in QUESTIONS:
        converted = convert_question(q)
        if converted["id"] not in existing_ids:
            new_qs.append(converted)

    data["questions"].extend(new_qs)

    # Deduplicate entire questions array by id
    seen = set()
    unique_qs = []
    for q in data["questions"]:
        if q["id"] not in seen:
            seen.add(q["id"])
            unique_qs.append(q)
    data["questions"] = unique_qs

    # Update version and timestamp
    data["version"] = data.get("version", 0) + 1
    import datetime
    data["generatedAt"] = datetime.datetime.now().isoformat() + "Z"

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"New questions added: {len(new_qs)}")
    print(f"Total questions: {len(data['questions'])}")
    print("Done! questions.json updated.")


if __name__ == "__main__":
    main()
