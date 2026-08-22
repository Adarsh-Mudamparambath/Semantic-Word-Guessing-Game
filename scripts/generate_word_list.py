"""
Generate the curated secret-word dataset.

Reads the hand-curated CATEGORY_WORDS bank below, dedupes across categories
(a word may only be a secret word once, even if it fits multiple themes),
normalizes, and writes:

    data/candidate_words.csv   (word, normalized_word, category)
    data/approved_words.csv    (same, after dedup + basic filtering)

Run:
    python scripts/generate_word_list.py
"""

import csv
import re
from pathlib import Path

try:
    from wordfreq import top_n_list
except ImportError:
    top_n_list = None

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"

# Curated, semantically-diverse word bank spread across categories.
# Kept to common, everyday English words, supplemented by wordfreq.
CATEGORY_WORDS = {
    "Animals": """dog cat lion tiger elephant giraffe zebra monkey bear wolf fox rabbit deer
        horse cow pig sheep goat chicken duck eagle owl sparrow penguin dolphin whale shark
        octopus crab lobster snake lizard turtle frog butterfly bee ant spider mouse squirrel
        kangaroo koala panda cheetah rhinoceros hippopotamus camel llama otter beaver hedgehog
        raccoon skunk bat falcon parrot flamingo peacock swan crocodile alligator seal walrus
        jellyfish starfish snail worm scorpion""".split(),

    "Nature": """mountain river forest desert valley waterfall volcano glacier canyon island
        lake cave cliff meadow jungle swamp coral reef dune hill stream pond cavern prairie
        tundra oasis peninsula bay delta plateau ridge grove thicket marsh geyser lagoon
        crater fjord wetland savanna rainforest boulder pebble soil bedrock""".split(),

    "Food": """bread cheese apple banana orange grape strawberry pizza pasta rice soup salad
        beef fish egg milk butter honey sugar salt pepper coffee tea chocolate cookie cake
        pie sandwich burger taco sushi noodle potato tomato onion garlic carrot corn wheat
        oatmeal yogurt bacon sausage pancake""".split(),

    "Objects": """chair table lamp mirror clock book pen pencil phone camera key wallet
        umbrella basket bottle cup plate spoon fork knife box bag suitcase ladder rope chain
        hammer nail screw bucket broom candle mattress pillow blanket curtain shelf drawer
        vase frame calendar notebook envelope stamp ticket""".split(),

    "Places": """school hospital library airport station museum market restaurant hotel
        church temple castle palace stadium park garden zoo farm factory office bank prison
        harbor bridge tunnel tower monument cemetery courthouse theater cinema gallery
        laboratory warehouse mall plaza village town city capital suburb campus embassy
        shrine lighthouse""".split(),

    "Technology": """computer internet robot satellite drone laptop smartphone software
        algorithm database keyboard monitor printer router server sensor battery circuit
        processor microchip television radio telescope microscope calculator headphones
        speaker charger antenna network password firewall browser application virus
        download upload bluetooth wifi hardware interface cloud""".split(),

    "Sports": """football basketball baseball tennis golf swimming boxing wrestling cycling
        running skiing skating surfing volleyball cricket rugby hockey archery fencing
        gymnastics marathon triathlon karate judo badminton bowling billiards darts rowing
        sailing diving climbing skateboarding snowboarding weightlifting javelin discus
        hurdles relay referee coach trophy medal tournament""".split(),

    "Transportation": """car bicycle motorcycle bus train airplane helicopter boat ship
        submarine truck van taxi subway tram ferry canoe kayak scooter wagon sled rocket jet
        glider balloon carriage cart trolley yacht tractor ambulance firetruck limousine
        minivan spacecraft hovercraft rickshaw gondola raft sailboat freighter tanker moped
        unicycle skateboard""".split(),

    "Human_Activities": """dancing singing painting writing reading cooking cleaning
        shopping traveling hiking camping fishing hunting gardening sewing knitting drawing
        sculpting photography meditation yoga prayer celebration wedding funeral festival
        parade protest negotiation debate interview lecture rehearsal performance exercise
        stretching jogging walking sleeping eating drinking laughing crying arguing
        teaching""".split(),

    "Professions": """doctor teacher lawyer engineer nurse farmer chef pilot artist musician
        writer scientist dentist plumber electrician carpenter mechanic architect accountant
        journalist photographer firefighter librarian professor surgeon veterinarian
        pharmacist therapist translator actor dancer comedian athlete judge senator
        president banker cashier waiter tailor""".split(),

    "Emotions": """happiness sadness anger fear joy love hate jealousy pride shame guilt
        anxiety excitement boredom loneliness gratitude hope despair surprise disgust envy
        contentment frustration relief curiosity nostalgia embarrassment confidence
        confusion empathy compassion grief delight worry calm panic affection resentment
        admiration regret satisfaction longing awe trust disappointment""".split(),

    "Abstract_Concepts": """freedom justice truth beauty wisdom knowledge power destiny fate
        chaos order balance harmony unity equality honor courage loyalty betrayal faith
        peace victory defeat identity memory dream reality illusion infinity eternity
        existence consciousness morality logic reason imagination creativity ambition
        greed humility patience""".split(),

    "Science": """atom molecule gravity energy electricity magnetism evolution genetics
        chemistry physics biology ecosystem cell bacteria protein enzyme hormone neuron
        gene chromosome mutation photosynthesis radiation isotope particle velocity
        momentum friction pressure density reaction catalyst compound element mixture
        crystal experiment hypothesis theory""".split(),

    "Space": """planet star galaxy comet asteroid meteor moon sun orbit universe nebula
        constellation eclipse supernova cosmos mars venus jupiter saturn mercury neptune
        uranus pluto aurora meteorite astronaut quasar pulsar horizon""".split(),

    "Geography": """continent country ocean sea border latitude longitude hemisphere equator
        archipelago isthmus strait gulf steppe highland lowland coastline terrain landscape
        territory province region district metropolis colony empire kingdom nation
        population migration climate timezone atlas compass globe map""".split(),

    "Architecture": """skyscraper cathedral pyramid dome arch column facade balcony
        staircase foundation rooftop courtyard mansion cottage bungalow apartment
        condominium fortress citadel pavilion veranda mezzanine basement attic chimney
        gateway corridor terrace colonnade spire minaret pagoda amphitheater aqueduct
        mausoleum obelisk rotunda gazebo lobby atrium""".split(),

    "Entertainment": """movie concert circus carnival opera ballet orchestra symphony comedy
        drama tragedy novel poem sculpture animation cartoon videogame boardgame puzzle
        magic magician clown puppet karaoke playlist soundtrack screenplay script audience
        applause spotlight premiere sequel blockbuster celebrity fanbase""".split(),

    "Clothing": """shirt pants dress skirt jacket coat sweater scarf glove hat cap shoe boot
        sandal sock belt tie suit jeans shorts pajama robe uniform veil apron mitten poncho
        cloak vest blouse gown tunic turban sari kimono sombrero necklace bracelet
        earring""".split(),

    "Household_Objects": """sofa refrigerator oven stove sink faucet toilet bathtub shower
        wardrobe dresser cabinet cupboard carpet rug wallpaper doorknob hinge windowsill
        fireplace thermostat dishwasher microwave blender toaster kettle vacuum iron hanger
        hamper mop dustpan showerhead doormat chandelier lampshade bookshelf nightstand
        recliner""".split(),

    "Tools": """wrench screwdriver drill saw chisel pliers level sandpaper crowbar axe
        shovel rake pickaxe wheelbarrow toolbox clamp vise file ruler blowtorch welder
        grinder sander jackhammer scaffold forklift crane bulldozer pulley lever gear
        spanner""".split(),

    "Materials": """wood metal steel iron copper gold silver bronze plastic rubber glass
        ceramic cotton wool silk leather concrete cement marble granite clay gravel brick
        plywood aluminum titanium nylon polyester velvet denim canvas foam wax
        fiberglass""".split(),

    "Weather": """rain snow storm thunder lightning wind fog mist hail frost drought flood
        hurricane tornado blizzard humidity sunshine cloud rainbow drizzle breeze gale
        monsoon heatwave avalanche sleet dew overcast forecast""".split(),

    "Plants": """tree flower grass bush vine moss fern cactus rose tulip daisy sunflower
        orchid lily ivy bamboo oak pine maple willow palm fungus mushroom algae seed root
        leaf branch blossom petal thorn herb weed shrub sprout""".split(),

    "Everyday": """water air earth fire day night morning evening time year month week
        season world life person people man woman child family friend home house room door
        window floor wall roof street road place work job money story idea question answer
        name word number thing way part side end beginning center top bottom hand head face
        eye ear mouth hair heart body mind voice sound light color shape size line point
        group team game music picture paper letter message story problem change chance reason
        truth fact example kind type sort amount space area age age food drink clothes
        body weather ground sky sun moon rain snow wind heat cold
        love help need use want hope dream plan choice answer result start move turn stop
        open close bring take give make get put keep find know think feel see look hear speak
        read learn teach remember believe understand""".split(),
}

COMMON_WORD_LIMIT = 10_000


def normalize(word: str) -> str:
    word = word.strip().lower()
    word = re.sub(r"[^a-z]", "", word)
    return word


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    seen = set()
    rows = []
    dropped = []

    for category, words in CATEGORY_WORDS.items():
        for w in words:
            norm = normalize(w)
            if not norm:
                continue
            if norm in seen:
                dropped.append((w, category, "duplicate_across_categories"))
                continue
            seen.add(norm)
            rows.append({"word": w, "normalized_word": norm, "category": category})

    if top_n_list is None:
        raise RuntimeError(
            "The wordfreq package is required. Install backend/requirements.txt "
            "before generating the dictionary."
        )

    for word in top_n_list("en", COMMON_WORD_LIMIT):
        norm = normalize(word)
        if not norm or len(norm) < 2 or len(norm) > 30 or norm in seen:
            continue
        if not re.fullmatch(r"[a-z]+", norm):
            continue
        seen.add(norm)
        rows.append({"word": norm, "normalized_word": norm, "category": "Common_English"})

    candidate_path = DATA_DIR / "candidate_words.csv"
    approved_path = DATA_DIR / "approved_words.csv"

    for path in (candidate_path, approved_path):
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["word", "normalized_word", "category"])
            writer.writeheader()
            writer.writerows(rows)

    print(f"Wrote {len(rows)} unique words to {candidate_path.name} and {approved_path.name}")
    print(f"Categories: {len(CATEGORY_WORDS) + 1}")
    if dropped:
        print(f"Dropped {len(dropped)} duplicate entries (kept first occurrence):")
        for w, c, reason in dropped[:20]:
            print(f"  - {w} ({c}): {reason}")


if __name__ == "__main__":
    main()
