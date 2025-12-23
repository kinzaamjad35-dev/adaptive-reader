"""Built-in practice library: graded passages, phonics patterns and sight-word lists. All texts are original."""

PASSAGES = [
    # --- Beginner ---
    {"title": "The Red Kite", "level": "Beginner", "type": "Short story", "text":
     "Sam has a red kite. The kite is big and light. Sam runs up the hill with it. The wind is strong today. "
     "The kite goes up, up, up. It flies over the trees. Sam holds the string tight. A dog runs next to him. "
     "The dog jumps and barks at the kite. Sam laughs. Then the wind stops. The kite falls down on the grass. "
     "Sam picks it up. \"We will try again,\" he says. The wind comes back, and the kite flies once more."},
    {"title": "My Morning", "level": "Beginner", "type": "Everyday text", "text":
     "I wake up at seven. I wash my face and brush my teeth. Then I get dressed. I put on my blue shirt. "
     "Mum makes eggs and toast. I drink a glass of milk. I pack my bag for school. I put in my book, my pen and my lunch. "
     "I put on my shoes. I say goodbye to Mum. Then I walk to the bus stop with my sister."},
    {"title": "Frogs", "level": "Beginner", "type": "Science", "text":
     "A frog is a small animal. It can live on land and in water. Frogs have long back legs. They use them to jump and swim. "
     "A frog starts life as an egg in a pond. The egg turns into a tadpole. A tadpole has a tail and no legs. "
     "Slowly it grows legs. Its tail gets smaller. Then it becomes a frog. Frogs eat bugs. They catch them with their long, sticky tongue."},
    # --- Elementary ---
    {"title": "The Lost Library Book", "level": "Elementary", "type": "Short story", "text":
     "Maya could not find her library book anywhere. She looked under her bed, inside her school bag and behind the sofa. "
     "The book was due back the next day, and she was worried. Her little brother Ali watched her search. "
     "\"Is it the one with the dragon on the cover?\" he asked. Maya nodded. Ali went quiet, then ran to his room. "
     "He came back holding the book. \"I wanted to look at the pictures,\" he said. Maya smiled and sat down next to him. "
     "\"Then let's read it together before it goes back,\" she said. They read the whole story that evening."},
    {"title": "How to Make a Sandwich", "level": "Elementary", "type": "Everyday text", "text":
     "First, wash your hands with soap and water. Next, take two slices of bread and put them on a clean plate. "
     "Spread a thin layer of butter on each slice. Then add your filling. You could use cheese, tomato, cucumber or egg. "
     "Put the second slice of bread on top, butter side down. Press it gently. Finally, cut the sandwich in half with a "
     "butter knife. Ask an adult for help if you need a sharp knife. Now your sandwich is ready to eat."},
    {"title": "Why Do We Have Seasons?", "level": "Elementary", "type": "Science", "text":
     "The Earth travels around the Sun once every year. The Earth is also tilted, a bit like a spinning top that leans to one side. "
     "Because of this tilt, different parts of the Earth get more sunlight at different times of the year. "
     "When your part of the world leans towards the Sun, the days are long and warm. This is summer. "
     "When it leans away, the days are short and cold. This is winter. Spring and autumn happen in between."},
    # --- Intermediate ---
    {"title": "The Great Wall of China", "level": "Intermediate", "type": "History", "text":
     "The Great Wall of China is not one single wall. It is a series of walls and towers built over about two thousand years. "
     "Different rulers added sections to protect their land from invading groups in the north. Many of the parts we can visit today "
     "were built during the Ming dynasty, between the 1300s and 1600s. Workers used stone, brick, wood and even packed earth. "
     "The work was hard and dangerous, and many builders lost their lives. Guards in the watchtowers could send signals with smoke "
     "or fire to warn others that an attack was coming. Today the wall is one of the most famous landmarks in the world."},
    {"title": "Reading a Bus Timetable", "level": "Intermediate", "type": "Everyday text", "text":
     "A bus timetable tells you when buses leave each stop. Along the top you will usually see the days the timetable is for, "
     "such as Monday to Friday. Down the side is a list of stops in the order the bus reaches them. To plan a journey, "
     "find your stop on the list, then read across to see the times. If a box is empty, the bus does not stop there on that trip. "
     "It is a good idea to arrive a few minutes early, because buses can sometimes run ahead of time. "
     "Many cities also have apps that show where the bus is right now."},
    {"title": "The Girl Who Counted Stars", "level": "Intermediate", "type": "Short story", "text":
     "Every clear night, Lena climbed onto the flat roof of her apartment building with a notebook and a torch covered in red paper. "
     "She had read that red light helps your eyes stay used to the dark. She drew the patterns she saw and gave them her own names "
     "before she learned the real ones. One night she noticed a bright point that had moved since the week before. "
     "Her teacher explained that it was probably a planet, because planets drift slowly across the background of stars. "
     "Lena checked a star map and found she was right: it was Jupiter. From then on, she kept a record of its journey across the sky."},
    # --- Advanced ---
    {"title": "How Vaccines Train the Immune System", "level": "Advanced", "type": "Science", "text":
     "The immune system protects the body by recognising substances that do not belong there, such as viruses and bacteria. "
     "When it meets a new germ, it takes time to produce antibodies that fit that particular invader, which is why people often "
     "become ill the first time they are infected. A vaccine works by showing the immune system a harmless version or part of a germ, "
     "so that it can prepare without the person getting seriously sick. Afterwards, memory cells remain in the body for months or years. "
     "If the real germ appears later, these cells recognise it and respond much more quickly. When enough people in a community are "
     "vaccinated, the germ finds it harder to spread, which also protects those who cannot be vaccinated."},
    {"title": "The Printing Press", "level": "Advanced", "type": "History", "text":
     "Before the fifteenth century, most books in Europe were copied by hand, which made them rare and expensive. "
     "Around 1440, Johannes Gutenberg developed a printing press that used movable metal type, building on earlier ideas from "
     "China and Korea. Individual letters could be arranged into pages, inked and pressed onto paper, then rearranged for the next job. "
     "Within decades, printing shops had spread across the continent and millions of books were produced. "
     "Cheaper books meant that ideas, scientific discoveries and news could travel much further and faster than before. "
     "Many historians argue that the printing press helped make possible the Renaissance, the Reformation and the scientific revolution."},
    {"title": "Understanding a Tenancy Agreement", "level": "Advanced", "type": "Everyday text", "text":
     "A tenancy agreement is a contract between a tenant and a landlord. It sets out how much rent is due, when it must be paid, "
     "and how long the tenancy lasts. Most agreements also explain who is responsible for repairs, whether pets are allowed, "
     "and how much notice either side must give before ending the arrangement. A deposit is usually paid at the start; in many "
     "countries it must be kept in a protected scheme and returned at the end, minus the cost of any damage beyond normal wear and tear. "
     "Before signing, it is sensible to read every clause carefully, take dated photographs of the property, and ask questions "
     "about anything that is unclear."},
]

LEVELS = ["Beginner", "Elementary", "Intermediate", "Advanced"]

# Phonics patterns with example words (common English spelling patterns)
PHONICS = {
    "Short a (cat)": ["cat", "map", "bag", "hat", "jam", "sad", "van", "clap"],
    "Short e (bed)": ["bed", "pen", "leg", "net", "red", "web", "nest", "help"],
    "Short i (pig)": ["pig", "sit", "fin", "lip", "big", "milk", "swim", "gift"],
    "Short o (dog)": ["dog", "pot", "box", "hop", "log", "fox", "stop", "frog"],
    "Short u (sun)": ["sun", "cup", "bus", "mud", "rug", "jump", "duck", "plum"],
    "sh / ch / th": ["ship", "shop", "fish", "chip", "lunch", "chat", "thin", "bath"],
    "Magic e (a_e, i_e, o_e)": ["cake", "game", "bike", "time", "home", "rope", "cube", "late"],
    "ee / ea": ["tree", "feet", "green", "sleep", "sea", "read", "team", "beach"],
    "ai / ay": ["rain", "train", "paint", "wait", "day", "play", "stay", "tray"],
    "oa / ow": ["boat", "coat", "road", "soap", "snow", "grow", "slow", "window"],
    "ar / or / er": ["car", "star", "park", "fork", "storm", "short", "her", "letter"],
    "Blends (bl, cr, st)": ["black", "blue", "crab", "crisp", "stamp", "stick", "flag", "grip"],
    "-ing / -ed endings": ["jumping", "playing", "reading", "jumped", "played", "wanted", "helped", "looked"],
    "Tricky -tion / -ight": ["station", "action", "nation", "light", "night", "bright", "fight", "right"],
}

# Sight words: high-frequency words (in the style of Dolch / Fry first-100 lists)
SIGHT_WORDS = {
    "Set 1": ["the", "and", "a", "to", "said", "in", "he", "I", "of", "it", "was", "you", "they", "on", "she", "is"],
    "Set 2": ["for", "at", "his", "but", "that", "with", "all", "we", "can", "are", "up", "had", "my", "her", "what", "there"],
    "Set 3": ["out", "this", "have", "went", "be", "like", "some", "so", "not", "then", "were", "go", "little", "as", "no", "mum"],
    "Set 4": ["one", "them", "do", "me", "down", "dad", "big", "when", "it's", "see", "looked", "very", "look", "don't", "come", "will"],
    "Set 5": ["into", "back", "from", "children", "him", "Mr", "get", "just", "now", "came", "oh", "about", "got", "their", "people", "your"],
    "Set 6": ["because", "could", "would", "should", "where", "who", "why", "which", "friend", "again", "through", "thought", "know", "once", "laugh", "school"],
}


def by_level(level=None, kind=None):
    return [p for p in PASSAGES if (level in (None, "All", p["level"])) and (kind in (None, "All", p["type"]))]


def get_passage(title):
    return next((p for p in PASSAGES if p["title"] == title), None)


def scramble(word, rng):
    letters = list(word)
    for _ in range(10):
        rng.shuffle(letters)
        if "".join(letters) != word:
            break
    return "".join(letters)
