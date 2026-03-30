# Fantasy
Plonge dans une aventure Donjons &amp; Dragons en Python ! Choisis une classe, explore des donjons, combats ennemis et boss, utilise des compétences spéciales, gagne de l’expérience et monte en niveau. Une aventure tour par tour avec base SQLite et événements aléatoires.

Jeu Donjon & Dragon – Python (NSI)
Plonge dans une aventure épique inspirée de Donjons & Dragons !
Incarne un héros, explore des donjons, affronte des ennemis et des boss, et fais évoluer ton personnage grâce à l’expérience.

Classes et compétences :
Choisis ta classe parmi 5 héros uniques :
Sorcier → Gel l’ennemi pendant 1 tour
Archer → Flèche explosive : prochaine attaque +50% dégâts
Chevalier → Bouclier divin : réduit 70% des dégâts pendant 2 tours
Barbare → Fureur d’Odin : augmente les dégâts pendant 2 tours
Assassin → Esquive ultime : 0 dégât ce tour
et bien plus encore...

Chaque classe a ses points de vie et sa puissance d’attaque propres.

Ennemis et boss :
Affronte des ennemis basiques comme les zombies et squelettes, ou des boss puissants avec des capacités spéciales.
Les boss apparaissent régulièrement pour tester ta stratégie et tes compétences.

Système de combat :
Le combat se déroule tour par tour.
À chaque tour, tu peux : Attaquer l’ennemi, ne rien faire (prendre les dégâts), utiliser ta compétence spéciale (une fois par combat).
Les dégâts, effets et buffs sont calculés selon la classe, la compétence et le choix du joueur.

Aventure et événements :
Explore le monde grâce à des événements aléatoires : Trouver un coffre ancien, rencontrer un marchand, découvrir une grotte mystérieuse, faire face à un embuscade.
Tes choix influencent ton expérience, tes points de vie et tes rencontres.

Progression du héros :
Gagne de l’expérience (XP) à chaque combat ou action réussie
Monte de niveau pour augmenter tes PV et ton attaque
Prépare-toi à affronter des ennemis de plus en plus puissants

Base de données SQLite
Le jeu utilise SQLite avec 4 tables principales :
Classe → statistiques et compétences des héros
Competence → détails des compétences
Joueur → informations du joueur et progression
Ennemi → caractéristiques des ennemis et boss
La base de données est automatiquement créée à l’installation et mise à jour au fil du jeu.
