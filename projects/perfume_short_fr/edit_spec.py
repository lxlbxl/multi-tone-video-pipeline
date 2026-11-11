"""Edit decision list for the perfume short. All times are SOURCE seconds."""

T0 = 1.70          # trim dead air before he speaks
T_END = 90.0

# product colours
TEAL, ORANGE, GOLD, RED, YELLOW, PINK = "#22E3D3", "#FF5A1F", "#F5B83D", "#FF2E63", "#FFE234", "#FF3D9A"

# caption groups: (text, word start times). *WORD = emphasised (colour box)
CAPTIONS = [
    ("SALUT LES AMIS", [2.2, 2.6, 3.1]),
    ("J'ESPÈRE QUE VOUS", [3.8, 4.2, 4.35]),
    ("ALLEZ TRÈS BIEN", [4.5, 4.7, 4.9]),
    ("D'ACCORD ?", [5.2]),
    ("VOUS ME CONNAISSEZ", [6.1, 6.3, 6.5]),
    ("C'EST ÇA", [7.4, 7.7]),
    ("AUJOURD'HUI", [8.6]),
    ("POUR VOUS PRÉSENTER", [9.15, 9.3, 9.5]),
    ("QUELQUES *PÉPITES", [10.0, 10.3]),
    ("DES PARFUMS", [10.9, 11.3]),
    ("QUE VOUS NE *CONNAISSEZ *PAS", [12.85, 13.0, 13.2, 13.4, 13.9]),
    ("LES PARFUMS", [15.4, 15.7]),
    ("LES *RÔLES QU'ILS JOUENT", [16.4, 16.5, 16.8, 17.1]),
    ("ET SI VOUS AVEZ", [18.0, 18.2, 18.3, 18.4]),
    ("LA *CHANCE", [18.6, 18.8]),
    ("PEUT-ÊTRE COMMENT L'UTILISER", [19.0, 19.3, 19.6]),
    ("ALORS JE VOUS PRÉSENTE", [20.4, 20.6, 20.75, 20.9]),
    ("CE PARFUM", [21.8, 21.95]),
    ("LE PARFUM *JÉRUSALEM", [22.6, 22.85, 23.3]),
    ("VOUS VOYEZ ?", [24.3, 24.5]),
    ("C'EST POUR CEUX", [25.4, 25.6, 25.8]),
    ("QUI FONT LA *SPIRITUALITÉ", [25.9, 26.0, 26.2, 26.4]),
    ("TU AS ENVIE", [27.0, 27.25, 27.45]),
    ("DE FAIRE UN", [27.7, 27.8, 27.9]),
    ("*VOYAGE *SPIRITUEL", [28.0, 28.4]),
    ("OU UN *RITUEL", [29.4, 29.7, 30.0]),
    ("DE SPIRITUALITÉ", [30.5, 30.8]),
    ("TU AS BESOIN", [31.7, 31.9, 32.0]),
    ("D'ÊTRE *CONCENTRÉ", [32.4, 32.7]),
    ("SPIRITUELLEMENT", [33.2]),
    ("CE PARFUM", [34.1, 34.4]),
    ("IL EST *MEILLEUR", [34.9, 34.95, 35.0]),
    ("POUR TOI", [35.4, 35.6]),
    ("CE PARFUM-LÀ", [40.0, 40.4]),
    ("LES *BUSINESSMEN", [41.2, 41.3]),
    ("CONNAISSENT ÇA", [42.1, 42.6]),
    ("VOUS CONNAISSEZ ÇA", [44.8, 45.0, 45.3]),
    ("TRÈS BIEN", [45.5, 45.9]),
    ("C'EST UN PARFUM", [46.5, 46.6, 46.7]),
    ("DE *DÉBLOCAGE", [47.0, 47.2]),
    ("TRÈS *PUISSANT", [47.8, 48.0]),
    ("JE TE JURE", [49.1, 49.3, 49.5]),
    ("VIENS *ACHETER !", [49.9, 50.3]),
    ("UNE FOIS", [54.2, 54.4]),
    ("QUE TU VIENS", [54.6, 54.7, 54.9]),
    ("ON TE DONNE", [55.1, 55.25, 55.4]),
    ("LE *SECRET", [55.6, 55.8]),
    ("DE COMMENT LE *FORTIFIER", [56.6, 56.8, 57.1, 57.3]),
    ("ET COMMENT L'UTILISER", [57.9, 58.1, 58.4]),
    ("TOUJOURS", [60.2]),
    ("DANS L'OPTIQUE", [60.5, 60.7]),
    ("DES *BONNES PERSONNES", [61.6, 61.8, 62.1]),
    ("POUR LE *DÉBLOCAGE", [62.9, 63.0, 63.1]),
    ("IL Y A CE PARFUM-LÀ", [64.0, 64.1, 64.2, 64.3, 64.5]),
    ("LE *MEILLEUR PARFUM", [65.6, 66.0, 66.4]),
    ("LE PARFUM", [67.4, 67.6]),
    ("*MODERN *OUD", [68.0, 68.6]),
    ("C'EST TRÈS BIEN", [69.15, 69.3, 69.5]),
    ("POUR LES *HOMMES", [69.65, 69.85, 70.1]),
    ("QUI N'AIMENT PAS", [70.5, 70.6, 71.0]),
    ("UTILISER", [72.0]),
    ("DES PARFUMS *SPIRITUELS", [73.0, 73.6, 74.6]),
    ("POUR *SORTIR", [75.0, 75.3]),
    ("POUR QU'ON DISE", [75.8, 76.0, 76.3]),
    ("CELUI-LÀ", [77.3]),
    ("IL EST SPIRITUEL", [77.8, 78.0, 78.3]),
    ("TOUT ET TOUT", [78.75, 78.9, 79.05]),
    ("LE MEILLEUR PARFUM", [79.6, 79.8, 80.1]),
    ("QUAND TU L'UTILISES", [80.9, 81.05, 81.2]),
    ("ON NE LE *SENT *PAS", [81.7, 81.8, 81.9, 82.0, 82.2]),
    ("SUR TOI", [82.4, 82.6]),
    ("VOUS VOYEZ", [82.9, 83.05]),
    ("J'AI DES *BONNES CHOSES", [83.2, 83.6, 84.1, 84.4]),
    ("POUR VOUS", [84.8, 85.0]),
]

# big words placed BEHIND him (subject moves down to make room)
HEADLINES = [
    # start, end, lines, colour
    (9.9, 13.9, ["PÉPITES"], YELLOW),
    (25.4, 29.2, ["SPIRITUEL"], TEAL),
    (46.4, 50.6, ["DÉBLOCAGE"], ORANGE),
    (55.5, 58.9, ["SECRET"], PINK),
    (69.1, 73.2, ["MODERN", "OUD"], GOLD),
    (81.6, 85.5, ["DISCRET"], GOLD),
]

# product sections: start, end, number, name, subtitle, colour, chips[(t, text)]
PRODUCTS = [
    (21.8, 36.4, "01", "JÉRUSALEM", "Eau de Cologne · Spirituel", TEAL,
     [(28.0, "Voyage spirituel"), (29.5, "Rituels"), (32.6, "Concentration")]),
    (40.0, 63.9, "02", "DÉBLOCAGE", "Parfum spray · Très puissant", ORANGE,
     [(41.3, "Adoré des businessmen"), (47.8, "Très puissant"), (55.8, "Le secret pour le fortifier")]),
    (64.0, 85.6, "03", "MODERN OUD", "Eau de Cologne · Discret", GOLD,
     [(70.1, "Pour hommes"), (75.0, "Pour sortir"), (82.0, "Personne ne le sent")]),
    (85.7, 90.0, "+1", "BONUS", "Le petit dernier…", RED, []),
]

# bottle bounding boxes (normalised to the source frame) while held up to camera
BOTTLE_TRACKS = [
    (TEAL, [(21.5, (0.00, 0.50, 0.40, 1.00)), (22.0, (0.00, 0.30, 0.45, 0.97)),
            (22.5, (0.00, 0.15, 0.50, 1.00)), (23.0, (0.05, 0.01, 0.60, 1.00)),
            (23.5, (0.10, 0.01, 0.80, 1.00)), (24.5, (0.15, 0.01, 0.85, 1.00)),
            (25.0, (0.05, 0.01, 0.75, 1.00))]),
    (ORANGE, [(41.5, (0.00, 0.42, 0.60, 1.00)), (42.0, (0.00, 0.40, 0.60, 1.00)),
              (42.5, (0.10, 0.30, 0.45, 1.00)), (43.0, (0.05, 0.25, 0.50, 1.00)),
              (43.5, (0.10, 0.21, 0.60, 1.00)), (44.0, (0.10, 0.25, 0.55, 1.00)),
              (44.5, (0.20, 0.25, 0.60, 1.00)), (45.0, (0.20, 0.25, 0.65, 1.00))]),
    (GOLD, [(65.0, (0.00, 0.35, 0.45, 1.00)), (65.5, (0.04, 0.38, 0.45, 1.00)),
            (66.0, (0.00, 0.37, 0.45, 1.00)), (67.0, (0.00, 0.37, 0.45, 1.00)),
            (67.5, (0.00, 0.38, 0.38, 1.00)), (68.0, (0.00, 0.40, 0.36, 1.00)),
            (68.5, (0.00, 0.45, 0.45, 1.00))]),
    (RED, [(86.0, (0.45, 0.45, 0.75, 0.90)), (86.5, (0.42, 0.45, 0.75, 0.90)),
           (87.0, (0.38, 0.47, 0.70, 0.86)), (87.5, (0.20, 0.58, 0.60, 0.95)),
           (88.0, (0.33, 0.55, 0.60, 0.86)), (88.5, (0.12, 0.58, 0.55, 0.90)),
           (89.0, (0.36, 0.66, 0.66, 0.99))]),
]

HOOK = (T0, T0 + 2.6, ["3 PARFUMS", "QUE VOUS NE", "CONNAISSEZ PAS"])
END_CARD_START = 85.7
