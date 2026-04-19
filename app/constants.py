SPORT_SWIMMING = "swimming"
SPORT_GYM = "gym"
SPORT_RUNNING = "running"
SPORT_COURSE = "course"

SPORT_OPTIONS = [
    (SPORT_SWIMMING, "Nuoto"),
    (SPORT_GYM, "Sala pesi"),
    (SPORT_RUNNING, "Corsa"),
    (SPORT_COURSE, "Corsi"),
]

COURSE_OPTIONS = [
    "acqua circuit", "aquadynamic", "acquagym", "allegro pilates", "bio circuit",
    "dynamic pylates", "gagg", "get barre", "get boxe", "get circuit", "get cross",
    "get dane", "hatcha yoga", "hydrobyke", "indoor cycle", "indoor walking",
    "interval training", "lesmills bodyattack", "lesmills bodybalance", "lesmills bodypump",
    "lesmills grit", "lesmills sprint", "matwork pilates", "metodo feldenkrais", "pancafit",
    "postural training", "stretching", "stretching funzionale", "tonificazione funzionale",
    "total body workout", "trx circuit", "vinyasa yoga", "zumba",
]

BODY_ZONES = [
    ("full_body", "Total body"),
    ("chest", "Petto"),
    ("back", "Schiena"),
    ("shoulders", "Spalle"),
    ("arms", "Braccia"),
    ("core", "Core"),
    ("glutes", "Glutei"),
    ("quads", "Quadricipiti"),
    ("hamstrings", "Femorali"),
    ("calves", "Polpacci"),
]

OBJECTIVE_LABEL_BY_SPORT = {
    SPORT_GYM: "Kg target",
    SPORT_SWIMMING: "Stile",
    SPORT_RUNNING: "Zona / passo",
}

EXERCISE_CATALOG_SEED = [
    # Sala pesi
    {"sport_type": SPORT_GYM, "name": "shoulder press", "body_zone": "shoulders"},
    {"sport_type": SPORT_GYM, "name": "leg curl", "body_zone": "hamstrings"},
    {"sport_type": SPORT_GYM, "name": "leg extension", "body_zone": "quads"},
    {"sport_type": SPORT_GYM, "name": "chest press", "body_zone": "chest"},
    {"sport_type": SPORT_GYM, "name": "lat machine", "body_zone": "back"},
    {"sport_type": SPORT_GYM, "name": "pulley basso", "body_zone": "back"},
    {"sport_type": SPORT_GYM, "name": "panca piana", "body_zone": "chest"},
    {"sport_type": SPORT_GYM, "name": "squat", "body_zone": "quads"},
    {"sport_type": SPORT_GYM, "name": "affondi", "body_zone": "glutes"},
    {"sport_type": SPORT_GYM, "name": "stacchi rumeni", "body_zone": "hamstrings"},
    {"sport_type": SPORT_GYM, "name": "alzate laterali", "body_zone": "shoulders"},
    {"sport_type": SPORT_GYM, "name": "curl bilanciere", "body_zone": "arms"},
    {"sport_type": SPORT_GYM, "name": "push down cavo", "body_zone": "arms"},
    {"sport_type": SPORT_GYM, "name": "calf raise", "body_zone": "calves"},
    {"sport_type": SPORT_GYM, "name": "plank", "body_zone": "core"},
    # Nuoto
    {"sport_type": SPORT_SWIMMING, "name": "vasche stile libero", "body_zone": "full_body"},
    {"sport_type": SPORT_SWIMMING, "name": "vasche dorso", "body_zone": "back"},
    {"sport_type": SPORT_SWIMMING, "name": "vasche rana", "body_zone": "full_body"},
    {"sport_type": SPORT_SWIMMING, "name": "vasche farfalla", "body_zone": "shoulders"},
    {"sport_type": SPORT_SWIMMING, "name": "gambe con tavoletta", "body_zone": "quads"},
    {"sport_type": SPORT_SWIMMING, "name": "braccia pull buoy", "body_zone": "arms"},
    {"sport_type": SPORT_SWIMMING, "name": "tecnica respirazione", "body_zone": "core"},
    # Corsa
    {"sport_type": SPORT_RUNNING, "name": "corsa lenta", "body_zone": "full_body"},
    {"sport_type": SPORT_RUNNING, "name": "ripetute brevi", "body_zone": "quads"},
    {"sport_type": SPORT_RUNNING, "name": "ripetute medie", "body_zone": "quads"},
    {"sport_type": SPORT_RUNNING, "name": "progressivo", "body_zone": "full_body"},
    {"sport_type": SPORT_RUNNING, "name": "fartlek", "body_zone": "full_body"},
    {"sport_type": SPORT_RUNNING, "name": "corsa in salita", "body_zone": "glutes"},
    {"sport_type": SPORT_RUNNING, "name": "corsa rigenerante", "body_zone": "calves"},
]
