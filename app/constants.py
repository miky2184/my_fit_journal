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
