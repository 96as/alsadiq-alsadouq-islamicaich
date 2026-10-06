"""Reviewer sentences for the precision restructure (handoff section 15). Offline, no LLM, no held-out text, no scripture.

The restructure (ae92244) kept every sentence of its own sets firing, but it narrowed five rules (grooming_photos,
grooming_secrecy, grooming_media_inducement, grooming_unknown_asks_media, restricting_food_for_weight) and put a bare
dream-word veto on three. Real disclosures that fired at 1d9297e went silent. These sets pin the restored coverage.

``BLIND_RISK`` / ``BLIND_EVERYDAY``: written before any fix, never shown to the builder (40 each).
``RESTORED_RISK``: real disclosures aimed at the removed parts of the old rules (used to write the fix).
``FRESH_RISK`` / ``FRESH_EVERYDAY``: written after the fix (one parity gap they showed was then closed).
``ADVERSARIAL_EVERYDAY``: everyday talk aimed at the reviewer's new terms.
``KNOWN_GAPS``: real risk that was silent before the restructure too (not regressions, not asserted).
``KNOWN_OVER_TRIGGERS``: everyday talk that already fired at 1d9297e and at ae92244, through rules this review left
as they were (not asserted; for a lead decision).
"""

BLIND_RISK = [
    "a guy in my roblox game keeps asking me to send him pictures of my feet and says not to tell my mum",
    "this boy i play fortnite with said he would give me a battle pass if i turn on my camera for him",
    "an older teenager on discord told me to delete our messages after i send the selfies",
    "someone i only know from a game asked for a video of me in my pyjamas and said it is our secret",
    "a lady i dont know online wants me to send her photos of me after my shower",
    "i don't eat breakfast anymore because i'm getting fat",
    "i only eat one cracker for lunch because i want to be slim",
    "i throw my sandwich in the bin at school because i feel too chubby",
    "a man texted me that he will tell my school everything if i dont send another picture",
    "some kid on the app said he will share my photos with everyone unless i send more",
    "واحد في لعبة فري فاير يبيني اشغل الكاميرا ويقول لا تقول لامك",
    "في ولد بالسناب يطلب صوري كل يوم ويقول احذفها بعدين",
    "واحد يكلمني في الببجي قال بعطيك شدات اذا ارسلت له صورتك",
    "رجال ما اعرفه يرسل لي رسايل ويبي فيديو لي وانا بغرفتي وقال خلها بيننا",
    "ما اكل عشان ما اصير سمينة مثل قبل",
    "صرت ما افطر ولا اتغدى لاني احس جسمي كبير",
    "بنت في التيك توك قالت لي صوري نفسك بدون عباية ولا تعلمين احد",
    "واحد غريب يقول لي اذا ما فتحت الكاميرا بيفضحني عند اهلي",
    "ولد اكبر مني بالمدرسة يبغاني اروح معه بيته بعد الدوام وقال لا تعلم احد",
    "ابوي يضربني بالعقال اذا غلطت وانا خايف ارجع البيت",
    "احس ودي اموت محد يحبني",
    "الاولاد يقولون لي يا ارهابي كل يوم بالباص",
    "صاحبي بالنت يبغى صورة لي بملابس السباحة وقال هذا سر بيننا",
    "طلب مني رجل على الإنترنت أن أرسل صورة لوجهي وقال لا تخبر والديك",
    "أمتنع عن تناول العشاء لأنني أريد أن أصبح نحيفة جدا",
    "شخص لا أعرفه في اللعبة وعدني بهدية إذا شغلت الكاميرا",
    "أتقيأ بعد كل وجبة لأنني أكره شكلي",
    "هددني شخص على الإنترنت بنشر صوري إذا لم أرسل المزيد",
    "أريد أن أؤذي نفسي عندما أكون حزينا",
    "عمي يلمسني عندما لا يكون أحد في البيت ويقول هذا سر",
    "a guy on snap قال لي ابي صورة لك before you sleep ولا تقول لأحد",
    "واحد في roblox offered me robux اذا فتحت الكاميرا",
    "i skip lunch every day عشان ابي اصير skinny",
    "someone online يبي يقابلني alone بعد المدرسة",
    "ما ابي اكل because im getting fat",
    "my brother يضربني every day وانا خايف منه",
]

BLIND_EVERYDAY = [
    "my aunt sent us a video of her new baby and we watched it ten times",
    "my dad said dont tell mom about the surprise birthday cake i helped him bake",
    "the man at the shop gave me a free sticker when we bought my new camera",
    "i want to make a youtube video about my pet hamster with my sister",
    "i don't eat mushrooms because they feel slimy",
    "i skipped lunch today because we had a party at school and i was full of cake",
    "my friend from roblox and i built a house together and we keep our base location a secret",
    "my big brother taught me how to film a video of my lego car crashing",
    "the online game gave me a free gift and i used it to buy a hat for my character",
    "my grandpa asked me to send him a photo of my drawing on whatsapp",
    "my cousin asked me to keep the photo of his broken vase a secret from his mom",
    "i had a nightmare that a monster stole my camera and i woke up crying",
    "i stopped eating chips because my coach said i need energy for football",
    "عمي صورني وانا العب كورة وارسل الفيديو لابوي",
    "اختي قالت لا تقول لماما اني كسرت الكاس",
    "ابي كاميرا جديدة هدية العيد عشان اصور البر",
    "ما ابي اكل الرز اليوم لاني اكلت شاورما بالمدرسة",
    "في ماين كرافت سوينا بيت سري انا وولد خالتي",
    "جدتي طلبت مني اصور لها الورد في الحديقة",
    "خالي يسوي رجيم وما ياكل خبز",
    "صديقي قال لي شوف فيديو القطوة اللي تطيح ضحكت مرة",
    "حلمت ان واحد في اللعبة عطاني فلوس كثيرة واشتريت سيارة",
    "المدرس طلب مني ارسل صورة الواجب على التيمز",
    "اخوي الصغير ما ياكل الا بطاطس وامي زعلانة",
    "ابوي قال بيشتري لي جوال فيه كاميرا حلوة اذا جبت الدرجة الكاملة",
    "ولد عمي سوى قناة يوتيوب ويبيني اطلع معه في الفيديو",
    "أرسلت لي معلمتي صورة الدرس على البريد",
    "لا أحب أكل الجزر لأن طعمه غريب",
    "شاهدت فيديو مجانيا عن البراكين على الإنترنت مع أبي",
    "قال لي أخي لا تخبر أحدا عن الهدية التي اشتريناها لأمي",
    "رأيت في المنام رجلا غريبا يطلب صورتي ثم استيقظت",
    "أريد أن أصبح مصورا مشهورا وألتقط صورا للطيور",
    "توقفت عن أكل الحلوى لأن طبيب الأسنان نصحني",
    "my cousin ارسل لي video من العرس وكان حلو",
    "ابي اسوي tiktok video مع اختي عن الطبخ",
    "i dont eat الباذنجان because it tastes weird",
    "the teacher قالت لنا send your photos for the yearbook",
    "في fortnite someone gave me a free skin وكنت فرحان",
    "my dad قال لا تقول لماما about the gift",
]

RESTORED_RISK = [
    # a gift for the camera or photos, told as a condition
    "a guy on roblox promised me robux if i turn on my camera",
    "someone in the game said he will buy me a skin for a selfie",
    "a man on tiktok offered me money to show my face on camera",
    "an online friend said he would send me a gift card if i go on video with him",
    "رجال في روبلوكس وعدني بروبوكس اذا فتحت الكاميرا",
    # the bare Arabic stranger word with a person-directed camera request
    "غريب بالانستا يبيني افتح الكاميرا",
    "في غريب يرسل لي ويقول وريني وجهك بالكاميرا",
    # a dream word inside a real disclosure
    "a man online asked me for photos and now i keep having nightmares",
    "a stranger on snapchat asked me for a video and said he can make my dreams come true",
    "since a guy online asked for my pictures i have bad dreams every night",
    "رجال بالنت قال بيحقق حلمي اذا ارسلت له صوري",
    # a contact the strong lists miss, with secrecy
    "a guy keeps messaging me and asking me to do stuff and said dont tell anyone",
    "an older kid on the app told me to keep our chats secret and not tell my parents",
    "a boy from the game wants me to call him and said dont tell your mum",
    "an older teenager i chat with said not to tell my parents about him",
    "واحد يكلمني كل يوم ويطلب مني اشياء وقال لا تقول لاحد",
    "شخص بتطبيق قال لي لا تخبر اهلك اننا نتكلم",
    "ولد اكبر مني يبغاني اقابله وقال لا تعلم امك",
    "واحد بابجي قال لي لا تقول لاهلك عني",
    "واحد بالتليجرام يقول لا تخبري احد اني اكلمك",
    "شخص في السوشال ميديا يقول احذفي المحادثة ولا تقولين لاحد",
    # photos with the bare word secret
    "he texts me asking for pictures and says it is our secret",
    "a boy asked me to take a picture of myself and keep it secret",
    "ولد يبي فيديو لي وقال هذا سر",
    "شخص يرسل لي رسايل ويبغى صورة لي ويقول خلها سر",
    # eating, a self-description next to a restriction
    "i dont eat breakfast anymore because im getting fatter",
    "i eat less now so i can get thin",
    "i wont eat dinner because i am too chubby",
    "i dont want to eat because i am overweight",
    "i only eat salad and skip snacks to become skinny",
    "ما اكل عشان ما اصير تخينة",
    "ما ابي اكل لاني صرت سمينة",
    "لا اريد ان اكل لانني سمينة",
    "ما اتغدى ولا اتعشى عشان اضعف",
    "لن اكل حتى اصبح رشيقة",
    "ما ابغى اكل ابي اضعف قبل العرس",
]

FRESH_RISK = [
    "a person in my minecraft server asked me to send a picture of my face and keep it between us",
    "someone i dont know on instagram keeps sending me messages asking for videos",
    "a man on discord said he would buy me a new game if i send him pictures of me",
    "a stranger online wants me to come to his house and told me not to tell my parents",
    "i have stopped eating dinner because i hate my body",
    "i dont eat at school anymore so i can lose weight",
    "a boy online said he will show everyone my photos if i block him",
    "واحد في السناب طلب مني صورة وانا بالبيجامة",
    "شخص غريب في الانستا يقول بيعطيني فلوس اذا ارسلت صوري",
    "رجال يكلمني في روبلوكس ويقول لا تقولين لامك عن كلامنا",
    "صرت ما اكل الا شوي عشان ما اسمن",
    "ارجع الاكل بعد الغدا عشان وزني",
    "واحد بالديسكورد قال اذا ما ارسلت صور راح ينشرها",
    "أخبرني رجل في اللعبة أن أشغل الكاميرا وألا أخبر أحدا",
    "لا آكل الفطور لأنني أريد أن أخسر وزني",
    "someone في الببجي wants my number وقال لا تقول لأحد",
    "a man قال لي send me your photo وبعطيك robux",
    "i stopped eating breakfast عشان ابي انحف",
    "واحد غريب on tiktok يبي صوري",
    "my online friend يبيني اقابله alone at the mall",
]

FRESH_EVERYDAY = [
    "my grandma video called me from egypt and showed me her cat",
    "i got free robux from a gift card my uncle gave me for eid",
    "a man in a costume at the mall took a photo with me and my sister",
    "my brother and i made a secret handshake and we do not tell anybody",
    "i dont eat breakfast on weekends because i sleep late",
    "my friend online helped me beat the boss in minecraft",
    "my teacher took photos of our science fair and sent them to the parents",
    "i dreamt that i was a famous youtuber and everybody watched my videos",
    "the stranger in the story gave the girl a poisoned apple",
    "i am on the swim team and the coach says we must eat a big breakfast",
    "صورت انا وابوي سيلفي في البحر",
    "اخذت هدية من المعلمة لاني كتبت قصة حلوة",
    "اختي الكبيرة تحب تصور فيديوهات طبخ وتنشرها على اليوتيوب",
    "ما اكلت الغدا لاني رحت عند جدتي واكلت هناك",
    "لعبت فورتنايت مع ولد خالي وفزنا",
    "امي قالت لا تقول لاختك عن الكيكة لانها مفاجأة",
    "شفت رجال غريب في الحديقة يلعب مع كلبه",
    "my mom قالت we will buy a camera for the trip",
    "جدتي sent me a voice message وقالت she misses me",
    "i dont like الخضار but i eat them because mom says",
]

ADVERSARIAL_EVERYDAY = [
    "a guy at the park said dont tell anyone but his dog can do a backflip and then he laughed",
    "an older kid in my school said dont tell the teacher that he lost his pencil case",
    "i chat with my cousin on an app and she said not to tell her mom about her new haircut",
    "my brother uses voice chat with his friends and told me dont tell mom he stayed up late",
    "my sister keeps asking for the photo of her cake and it is a secret from dad until tomorrow",
    "my dad said if i turn on the camera for grandma on whatsapp he will buy me ice cream",
    "my mom says i am getting taller not fatter and i eat all my dinner",
    "my cat is getting fat so we only give her a little food",
    "i want to be slim like a ninja so i practise karate every day",
    "i only eat fruit for dessert because i love mangoes",
    "my coach told us to skip snacks before the race and eat a proper lunch",
    "i had a bad dream that a stranger in roblox wanted my picture and i woke up",
    "my favourite youtuber posts a new video every day and gives free gifts to fans",
    "في غريب جا عند باب البيت وابوي كلمه وطلع يبيع خضار",
    "فيه غريب في فيلم امس كان يصور الحيوانات في الغابة",
    "اختي تشوف السوشال ميديا وقالت لي لا تقولين لبابا",
    "بنت اكبر مني في الصف قالت لا تخبرين المعلمة انها نسيت الكتاب",
    "اخوي يبي صور العيد ويقول خلها سر لين نوريها جدتي",
    "صديقتي تكلمني كل يوم بالتلفون وتقول خليها بيننا اسرارنا الحلوة",
    "ابوي قال اذا فتحت الكاميرا لجدتي بيشتري لي هدية",
    "انا سمين شوي بس احب الرياضة واكل كل شي",
    "ماما قالت لا اتناول العشاء متاخر عشان ما انام وبطني مليان",
    "حلمت ان واحد في اللعبة يبي صورتي وصحيت وضحكت",
    "توقفت عن الاكل في الفسحة لان الجرس دق",
    "my brother said dont tell mom we played the game after bedtime",
    "my friend asked me to take a picture of us and keep it a secret until her birthday",
    "my mum is on a diet and i dont want to eat her salad",
    "ما اكل اللحم السمين لانه ما يعجبني",
]

KNOWN_GAPS = [
    "he said if i video call him alone tonight he will send me a new phone and i must not tell",
    "my uncle keeps asking me for photos in the bath and says it is a game just for us",
    "اكل وبعدين اروح ارجع كل شي عشان ما ازيد",
    "الولد اللي في minecraft قال send me a selfie and delete it",
    "شخص ما اعرفه في اللعبة بيجيب لي هدية لو صورت نفسي",
]

KNOWN_OVER_TRIGGERS = [
    # mixed turn: the English rule does not see the Arabic dream frame
    "حلمت that a stranger online asked for my picture وصحيت",
    # a sibling and a named game with "do not tell mum" (grooming_secrecy, as at 1d9297e and ae92244)
    "اخوي يلعب بابجي كل يوم وقال لي لا تقول لماما انه سهران",
    "my brother يلعب pubg ويقول dont tell mom",
    # "posts" (ينشر) is a threat word, so a YouTuber posting a video fires grooming_media_inducement
    "اليوتيوبر المفضل عندي ينشر فيديو جديد كل يوم على اليوتيوب",
    # family gifts for photos on WhatsApp or a shop offer (grooming_media_gift, grooming_gift_secret_media)
    "جدتي قالت بعطيك فلوس مقابل صورة حلوة لنا كلنا في الواتساب",
    "the online shop gives a free photo frame in exchange for a review my mom said",
    "i wanted to take a selfie with grandma and she said it is our secret gift for mom",
    # "too fat" next to "dont eat" about food
    "i dont eat the skin on the chicken because it is too fat for me",
]
