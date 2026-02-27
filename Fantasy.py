"""-- Tables
CREATE TABLE IF NOT EXISTS Classe (
        id_classe INTEGER PRIMARY KEY,
        nom TEXT NOT NULL,
        pv_base INTEGER,
        attaque_base INTEGER,
        nom_competence TEXT NOT NULL,
        effet TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS Competence (
    id_competence INTEGER PRIMARY KEY,
    id_classe INTEGER,
    nom TEXT,
    effet TEXT,          -- texte décrivant l'effet (pour affichage)
    bonus_pv INTEGER,    -- en général 0 sauf compétence PV
    bonus_attaque INTEGER,
    duree_tours INTEGER,  -- si applicable (ex: 2 tours)
    FOREIGN KEY (id_classe) REFERENCES Classe(id_classe)
);

CREATE TABLE IF NOT EXISTS Joueur (
    id_joueur INTEGER PRIMARY KEY,
    nom TEXT,
    id_classe INTEGER,
    id_competence INTEGER,
    exp INTEGER,
    pv INTEGER,
    attaque INTEGER,
    niveau INTEGER,
    FOREIGN KEY (id_classe) REFERENCES Classe(id_classe),
    FOREIGN KEY (id_competence) REFERENCES Competence(id_competence)
);

CREATE TABLE IF NOT EXISTS Ennemi (
    id_ennemi INTEGER PRIMARY KEY,
    nom TEXT,
    pv INTEGER,
    attaque INTEGER,
    type TEXT        -- 'boss' ou 'basique'
);

-- Insert classes (id 1..5)
INSERT OR IGNORE INTO Classe (id_classe, nom, pv_base, attaque_base) VALUES
(1, 'Sorcier', 12, 10),
(2, 'Archer', 10, 9),
(3, 'Chevalier', 16, 14),
(4, 'Barbare', 14, 12),
(5, 'Assassin', 10, 12);

-- Insert compétences (1 par classe)
INSERT OR IGNORE INTO Competence (id_competence, id_classe, nom, effet, bonus_pv, bonus_attaque, duree_tours) VALUES
(1, 1, 'Gel', 'Gèle l''ennemi : il ne peut pas attaquer 1 tour (ou inflige 0 dégats pendant 1 tour)', 0, 0, 1),
(2, 2, 'Flèche explosive', 'Prochain attaque inflige +50% dégâts', 0, 0, 1),
(3, 3, 'Bouclier divin', 'Réduit de 70% les dégâts reçus pendant 2 tours', 0, 0, 2),
(4, 4, 'Fureur d''Odin', 'Augmente de 50% les dégâts pendant 2 tours', 0, 0, 2),
(5, 5, 'Esquive ultime', 'Vous subissez 0 dégât pendant ce tour (rattrape une attaque)', 0, 0, 1);

-- Insert ennemis de base et boss (IDs arbitraires)
INSERT OR IGNORE INTO Ennemi (id_ennemi, nom, pv, attaque, type) VALUES
(1, 'Zombie', 20, 4, 'basique'),
(2, 'Squelette', 15, 3, 'basique'),
(9, 'Jack Chistophe, Prêtre de l'Evangile de l'Eglise Ulmer Münster', 50, 4, 'boss'),
(10, 'Lothric, Prince cadet et Lorian, Prince aîné', 125, 10, 'boss'),
(11, 'Yhorm le Géant', 75, 7, 'boss');
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import random
import os
import math
import sys
import textwrap

DB = "fantasy.db"

# ---------------------------
# Création et initialisation
# ---------------------------

# On vérifie qu'il n'y pas de base de donnée du jeu déja existente, sinon on la supprime
# ca évite les problème en cas de modification de la base de donnée

def init_db():
    if os.path.exists(DB):
        os.remove(DB)
    need_setup = not os.path.exists(DB)
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    # On exécute le schema + inserts si nécessaire
    with open(__file__, 'r', encoding='utf-8') as f:
        pass

    # on crée les differentes tables.
    cur.execute("""CREATE TABLE IF NOT EXISTS Classe (
        id_classe INTEGER PRIMARY KEY,
        nom TEXT NOT NULL,
        pv_base INTEGER,
        attaque_base INTEGER,
        nom_competence TEXT NOT NULL,
        effet TEXT NOT NULL
    );""")

    cur.execute("""CREATE TABLE IF NOT EXISTS Competence (
        id_competence INTEGER PRIMARY KEY,
        id_classe INTEGER,
        nom TEXT,
        effet TEXT,
        bonus_pv INTEGER,
        bonus_attaque INTEGER,
        duree_tours INTEGER,
        FOREIGN KEY (id_classe) REFERENCES Classe(id_classe)
    );""")

    cur.execute("""CREATE TABLE IF NOT EXISTS Joueur (
        id_joueur INTEGER PRIMARY KEY,
        nom TEXT,
        id_classe INTEGER,
        id_competence INTEGER,
        exp INTEGER,
        pv INTEGER,
        attaque INTEGER,
        niveau INTEGER,
        FOREIGN KEY (id_classe) REFERENCES Classe(id_classe),
        FOREIGN KEY (id_competence) REFERENCES Competence(id_competence)
    );""")

    cur.execute("""CREATE TABLE IF NOT EXISTS Ennemi (
        id_ennemi INTEGER PRIMARY KEY,
        nom TEXT,
        pv INTEGER,
        attaque INTEGER,
        type TEXT
    );""")

    conn.commit()

    # On insere les données dans la base
    cur.execute("SELECT COUNT(*) FROM Classe")
    if cur.fetchone()[0] == 0:
        cur.executemany("INSERT INTO Classe (id_classe, nom, pv_base, attaque_base, nom_competence, effet) VALUES (?, ?, ?, ?, ?, ?)",
                       [
                           (1, 'Sorcier', 12, 10, "Gèle l'ennemi", "0 dégats de l'ennemi pendant 1 tour"),
                           (2, 'Archer', 10, 9, 'Flèche explosive', "Prochaine attaque inflige +50% dégâts"),
                           (3, 'Chevalier', 16, 14, 'Bouclier divin', "Réduit de 70% les dégâts reçus pendant 2 tours"),
                           (4, 'Barbare', 14, 12, 'Fureur d\'Odin', "Augmente de 50% les dégâts pendant 2 tours"),
                           (5, 'Assassin', 10, 12, 'Esquive ultime', "Vous subissez 0 dégât pendant ce tour"),
                       ])
    cur.execute("SELECT COUNT(*) FROM Competence")
    if cur.fetchone()[0] == 0:
        cur.executemany("""INSERT INTO Competence
            (id_competence, id_classe, nom, effet, bonus_pv, bonus_attaque, duree_tours)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            [
                (1, 1, 'Gel', "0 dégats de l'ennemi pendant 1 tour", 0, 0, 1),
                (2, 2, 'Flèche explosive', "Prochaine attaque inflige +50% dégâts", 0, 0, 1),
                (3, 3, 'Bouclier divin', "Réduit de 70% les dégâts reçus pendant 2 tours", 0, 0, 2),
                (4, 4, 'Fureur d\'Odin', "Augmente de 50% les dégâts pendant 2 tours", 0, 0, 2),
                (5, 5, 'Esquive ultime', "Vous subissez 0 dégât pendant ce tour", 0, 0, 1),
            ])

    cur.execute("SELECT COUNT(*) FROM Ennemi")
    if cur.fetchone()[0] == 0:
        cur.executemany("INSERT INTO Ennemi (id_ennemi, nom, pv, attaque, type) VALUES (?, ?, ?, ?, ?)",
                       [
                           (1, 'Zombie', 10, 4, 'basique'),
                           (2, 'Squelette', 8, 3, 'basique'),
                           (12, 'Lothric, Prince cadet et Lorian, Prince aîné', 125, 10, 'boss'),
                           (11, 'Yhorm le Géant', 75, 7, 'boss'),
                           (10, "Jack Chistophe, Prêtre de l'Evangile de l'Eglise Ulmer Münster", 50, 4, 'boss'),
                       ])

    conn.commit()
    return conn, cur

# -----------------------------------------
# Fonctions utiles pour la base de donnée
# -----------------------------------------
def fetch_classes(cur):
    cur.execute("SELECT id_classe, nom, pv_base, attaque_base FROM Classe")
    return cur.fetchall()

def fetch_classes_with_competence(cur):
    cur.execute("""
        SELECT
            Classe.id_classe,
            Classe.nom,
            Classe.pv_base,
            Classe.attaque_base,
            Competence.nom,
            Competence.effet
        FROM Classe
        JOIN Competence ON Classe.id_classe = Competence.id_classe
        ORDER BY Classe.id_classe
    """)
    return cur.fetchall()


def fetch_comp_for_class(cur, id_classe):
    cur.execute("SELECT id_competence, nom, effet, bonus_pv, bonus_attaque, duree_tours FROM Competence WHERE id_classe = ?", (id_classe,))
    return cur.fetchone()

def create_player(cur, conn, nom, id_classe):
    comp = fetch_comp_for_class(cur, id_classe)
    cur.execute("SELECT pv_base, attaque_base FROM Classe WHERE id_classe = ?", (id_classe,))
    pv_base, atk_base = cur.fetchone()
    attaque = atk_base + (comp[4] if comp else 0)
    pv_total = pv_base + (comp[3] if comp else 0)
    cur.execute("""INSERT INTO Joueur (nom, id_classe, id_competence, exp, pv, attaque, niveau)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""", (nom, id_classe, comp[0] if comp else None, 0, pv_total, attaque, 1))
    conn.commit()

def get_player(cur):
    cur.execute("""SELECT id_joueur, Joueur.nom, Joueur.id_classe, Joueur.id_competence,
                          Joueur.exp, Joueur.pv, Joueur.attaque, Joueur.niveau, Classe.nom
                   FROM Joueur JOIN Classe ON Joueur.id_classe = Classe.id_classe
                   ORDER BY id_joueur DESC LIMIT 1""")
    return cur.fetchone()

def update_player_stats(cur, conn, id_joueur, pv=None, exp=None, attaque=None, niveau=None):
    q = "UPDATE Joueur SET "
    updates = []
    params = []
    if pv is not None:
        updates.append("pv = ?"); params.append(pv)
    if exp is not None:
        updates.append("exp = ?"); params.append(exp)
    if attaque is not None:
        updates.append("attaque = ?"); params.append(attaque)
    if niveau is not None:
        updates.append("niveau = ?"); params.append(niveau)
    q += ", ".join(updates) + " WHERE id_joueur = ?"
    params.append(id_joueur)
    cur.execute(q, tuple(params))
    conn.commit()

def fetch_enemy_by_name(cur, name):
    cur.execute("SELECT id_ennemi, nom, pv, attaque, type FROM Ennemi WHERE nom = ?", (name,))
    return cur.fetchone()

# crée une instance de l'enemie
def new_enemy_instance(base_enemy, scale=1.0):
    # table_enemi: (id, nom, pv, attaque, type)
    return {
        'id': base_enemy[0],
        'nom': base_enemy[1],
        'pv': int(math.ceil(base_enemy[2] * scale)),
        'attaque': int(max(1, math.ceil(base_enemy[3] * scale))),
        'type': base_enemy[4]
    }

# ---------------------------
# Combat tour par tour
# ---------------------------
def combat_turn_by_turn(cur, conn, player, enemy, comp_data):
    """
    player: dict with fields id_joueur, nom, id_classe, id_competence, exp, pv, attaque, niveau
    enemy: dict with fields nom, pv, attaque, type
    comp_data: (id_comp, nom, effet, bonus_pv, bonus_atk, duree)
    """
    print("\n--- COMBAT : {} (PV {}) vs {} (PV {}) ---".format(player['nom'], player['pv'], enemy['nom'], enemy['pv']))
    # suit les boosts et les nerfs temporaire
    player_atk = player['attaque']
    player_pv = player['pv']
    enemy_pv = enemy['pv']
    enemy_atk = enemy['attaque']

    # utilisation de la compétence une fois par combat
    skill_used = False
    durations = {'player_buff_atk':0, 'player_def_reduce_pct':0, 'enemy_frozen':0, 'player_invincible':0, 'player_atk_mult':1.0}

    class_id = player['id_classe']

    if comp_data:
        comp_name = comp_data[1]
    else:
        comp_name = None

    turn = 1
    while player_pv > 0 and enemy_pv > 0:
        print(f"\n-- Tour {turn} --")
        print(f"Votre PV : {player_pv} | Attaque : {player_atk} | Ennemi ({enemy['nom']}) PV : {enemy_pv} | Ennemi ATK : {enemy_atk}")
        # choix du joueur dans le combat
        print("Choix : 1) Attaquer  2) Ne rien faire (prendre les dégats)  3) Utiliser compétence (1x/combat)")
        choix = input("Votre action (1/2/3) : ").strip()
        while choix not in ('1','2','3'):
            choix = input("Choix invalide, entrez 1, 2 ou 3 : ").strip()

        # réalisation de l'action choisie par le joueur
        if choix == '1':
            # Prend en compte si le choix est attaquer lees degats du personnages et les possibles boosts
            atk_multiplier = 1.0
            if durations['player_atk_mult'] != 1.0:
                atk_multiplier = durations['player_atk_mult']
            dmg = int(math.ceil(player_atk * atk_multiplier))
            print(f"> Vous attaquez et infligez {dmg} dégâts.")
            enemy_pv -= dmg
        elif choix == '2':
            print("> Vous attendez, vous prenez le prochain coup sans riposte.")
            # Prend en compte le choix de ne rien faire
        else:  # Prend en compte le choix d'utiliser la compétence du personnage
            if skill_used:
                print("> Compétence déjà utilisée ce combat ! Vous ratez votre action.")
            else:
                skill_used = True
                print(f"> Vous utilisez votre compétence : {comp_data[1]} - {comp_data[2]}")
                # appleique la compétence relié au personnage dans la table Competence
                if comp_name == 'Gel':
                    durations['enemy_frozen'] = comp_data[5]  #joueur gelé pendant 1 tour
                    print("L'ennemi est gelé et ne pourra pas attaquer ce tour.")
                elif comp_name == 'Flèche explosive':
                    durations['player_atk_mult'] = 1.5  # la prochaine attaque inflige 150% de dégats supplémentaire
                    print("Votre prochaine attaque infligera +50% dégâts.")
                elif comp_name == 'Bouclier divin':
                    durations['player_def_reduce_pct'] = 0.7  # reduit les degats subis de 70% pendant 2 tours
                    durations['player_def_reduce_turns'] = comp_data[5]
                    print("Vous êtes protégé·e : -70% dégâts reçus pendant 2 tours.")
                elif comp_name == 'Fureur d\'Odin':
                    durations['player_atk_mult'] = 1.5
                    durations['player_buff_atk'] = comp_data[5]
                    print("Vos dégâts augmentent de 50% pendant 2 tours.")
                elif comp_name == 'Esquive ultime':
                    durations['player_invincible'] = comp_data[5]  # 1 turn
                    print("Vous esquivez tout : 0 dégât subi pour ce tour.")
                else:
                    print("(Compétence inconnue : aucun effet appliqué.)")

        # On regarde si l'adversaire a encore des PV apres l'action du joueur
        if enemy_pv <= 0:
            print(f"✅ Vous avez vaincu {enemy['nom']} !")
            # Ici on gagne de l'XP
            xp_gain = 14 if enemy['type']=='basique' else 70
            print(f"Vous gagnez {xp_gain} EXP !")
            player['exp'] += xp_gain
            # On update la base de donnée pour changer le LVL et les PV du joueur en fonction de son LVL
            player['pv'] = max(0, player_pv)
            update_player_stats(cur, conn, player['id_joueur'], pv=player['pv'], exp=player['exp'])
            return True

        # On regarde si l'enemi est gelé pendant son tour
        if durations.get('enemy_frozen',0) > 0:
            print("> L'ennemi est gelé et ne peut pas attaquer.")
            durations['enemy_frozen'] -= 0.5
        else:
            # L'enemi attaque
            dmg_received = enemy_atk
            if durations.get('player_def_reduce_pct',0):
                # si le joueur a activé sa compétence, on lui inflige seulement 30% de dégats
                reduce_pct = durations['player_def_reduce_pct']
                dmg_received = int(math.ceil(dmg_received * (1 - reduce_pct)))
            if durations.get('player_invincible',0) > 0:
                print("> Vous êtes invincible ce tour : vous ne subissez aucun dégât.")
                dmg_received = 0

            # Si le joueur a choisi de ne rien faire, on lui inflige juste les dégats normal du monstre dans la base de donnée
            print(f"> L'ennemi attaque et vous inflige {dmg_received} dégâts.")
            player_pv -= dmg_received

            # On fait en sorte que le compte des tours se fasse pour que les compétences s'arretent
            if durations.get('player_buff_atk',0) > 0:
                durations['player_buff_atk'] -= 1
                if durations['player_buff_atk'] == 0:
                    durations['player_atk_mult'] = 1.0
            if durations.get('player_def_reduce_turns',0):
                durations['player_def_reduce_turns'] -= 1
                if durations['player_def_reduce_turns'] == 0:
                    durations['player_def_reduce_pct'] = 0
            if durations.get('player_invincible',0) > 0:
                durations['player_invincible'] -= 0.5
            if choix == '1' and durations.get('player_atk_mult',1.0) != 1.0:
                if durations.get('player_buff_atk',0) == 0:
                    durations['player_atk_mult'] = 1.0

        # O regarde si le joueur est mort, si oui on envoie un message de fin.
        if player_pv <= 0:
            print("💀 Vous êtes tombé·e au combat...")
            player['pv'] = 0
            update_player_stats(cur, conn, player['id_joueur'], pv=player['pv'], exp=player['exp'])
            return False

        # sinon on continue
        turn += 1

    player['pv'] = player_pv
    update_player_stats(cur, conn, player['id_joueur'], pv=player['pv'], exp=player['exp'])
    return player_pv > 0

# ---------------------------
# Liste des événements(35-40 questions)
# ---------------------------
def get_story_events():
    events = [
        "Vous franchissez la porte du village désert.(Voulez-vous y entrez ?)",
        "Un vieux vous tend une carte usée.(Voulez-vous la prendre ?)",
        "Vous entendez un hurlement au loin.(Voulez-vous allez voir ?)",
        "Un sentier s'enfonce dans une forêt épaisse.(Voulez-vous y entrez ?)",
        "Vous découvrez un pont en ruines.(Voulez-vous le traverser ?)",
        "Une rivière bouillonnante bloque votre route.(Voulez-vous la franchir ?)",
        "Un panneau indique 'Cimetière ancien' — allez-vous passer ?",
        "Un marchand ambulant vous propose une potion (payante).(Voulez-vous la boire ?)",
        "Vous apercevez des traces de pas récentes.(Voulez-vous les suivres ?)",
        "Une grotte fume légèrement — voulez-vous entrer ?",
        "Vous trouvez un petit autel couvert de runes.(Voulez-vous interagir avec ?)",
        "Un enfant perdu vous demande de l'aide.(Voulez-vous l'aider ?)",
        "Une lumière bleue jaillit d'un arbuste.(Voulez-vous aller voir ?)",
        "Vous trouvez un coffre ancien.(Voulez-vous l'ouvrir ?)",
        "Une silhouette encapuchonnée vous observe.(Voulez-vous la salué ?)",
        "Un sentier mène à une claire où chantent des oiseaux.(Voulez-vous allez y marcher ?)",
        "Un fermier vous parle d'un dragon aperçu plus haut.(Voulez-vous l'ecouter ?)",
        "Vous sentez le sol trembler légèrement.(Continuer)",
        "Un rocher semble dissimuler une cavité.(Voulez-vous bouger le rocher ?)",
        "Un ermite vous met en garde contre des golems.(Voulez-vous y l'ecouter ?)",
        "Un passage étroit entre les arbres semble intéressant.(Voulez-vous vous y enfoncez ?)",
        "Une vieille tour se dresse à l'horizon.(Voulez-vous aller la voir ?)",
        "Un pont-levis se met en mouvement soudainement.(Continuer)",
        "Un ruisseau aux reflets étranges coule ici.(Voulez-vous vous approchez ?)",
        "Vous trouvez une croix de pierre gravée.(Voulez-vous la ramasée ?)",
        "Une odeur de soufre vous prend à la gorge.(Continuer d'avancer ?)",
        "Un troupeau de corbeaux s'envole au-dessus de vous.(Continuer)",
        "Vous débouchez sur une clairière remplie d'ossements.(Continuer)",
        "Un bruit métallique — une armure traînée ?(Restez sur vos garde ?)",
        "Un chemin caché monte vers la montagne.(Continuer)",
        "Vous trouvez des inscriptions qui parlent d'un trésor.(Prendre le temps de lire ?)",
        "La nuit commence à tomber rapidement.(Trouvez un abri ?)",
        "Une voix murmure votre nom depuis l'obscurité.(Suivre le bruit ?)",
        "Un vieux pont branlant semble mener à un donjon.(S'y enfoncer ?)",
        "Vous remarquez des empreintes brûlées sur la terre.(Continuer)",
        "Un autel brisé fume encore d'une magie noire.(Sortir votre arme ?)",
        "Vous sentez une présence malveillante tout près.(Vous mettre sur vos gardes ?)",
    ]
    return events

def ask_yes_no(question):
    print("\n" + textwrap.fill(question, 80))
    r = input("O/N : ").strip().lower()
    while r not in ('o','n'):
        r = input("Réponds par O ou N : ").strip().lower()
    return r == 'o'

def play_adventure(cur, conn):
    events = get_story_events()
    total_steps = len(events)
    step = 0
    xp = 0
    row = get_player(cur)
    if not row:
        print("Aucun joueur trouvé, quittez et créez un joueur.")
        return
    player = {
        'id_joueur': row[0],
        'nom': row[1],
        'id_classe': row[2],
        'id_competence': row[3],
        'exp': row[4],
        'pv': row[5],
        'attaque': row[6],
        'niveau': row[7],
        'classe_nom': row[8]
    }
    comp_row = fetch_comp_for_class(cur, player['id_classe'])
    comp_data = (comp_row[0], comp_row[1], comp_row[2], comp_row[3], comp_row[4], comp_row[5])  # (id, nom, effet, bonus_pv, bonus_atk, duree)

    print(f"\nDébut de l'aventure de {player['nom']} le {player['classe_nom']} (PV={player['pv']}, ATQ={player['attaque']})")
    basic_enemies = [fetch_enemy_by_name(cur, 'Zombie'), fetch_enemy_by_name(cur, 'Squelette')]

    # On définit les boss qui apparaitront toutes les 10 étapes
    boss_base = [fetch_enemy_by_name(cur, "Jack Chistophe, Prêtre de l'Evangile de l'Eglise Ulmer Münster"), fetch_enemy_by_name(cur, 'Yhorm le Géant'), fetch_enemy_by_name(cur,'Lothric, Prince cadet et Lorian, Prince aîné')]

    while step < total_steps:
        event_text = events[step]
        print(f"\n== Étape {step+1}/{total_steps} ==")
        chc = ask_yes_no(event_text + "")
        if chc:
            # On gagne de toujours au moins 7XP
            reward = 7
            # On peut trouver du loot ou des combats
            # On a 30% de chance de devoir se battre quand on dit 'o' dans l'histoire
            if random.random() < 0.30:
                # prend un enemi basique
                be = random.choice(basic_enemies)
                scale = 1.0 + (step / total_steps) * 0.5
                enemy = new_enemy_instance(be, scale=scale)
                print(f"⚠️ Rencontre : {enemy['nom']} (PV {enemy['pv']}, ATK {enemy['attaque']})")
                # combat
                success = combat_turn_by_turn(cur, conn, player, enemy, comp_data)
                if not success:
                    print("Fin de la partie.")
                    return
                else:
                    reward += 7
            else:
                print("Vous avancez sans rencontrer d'ennemis pour l'instant.")
            xp += reward
            print(f"+{reward} XP (Total local = {xp})")
        else:
            # Lorsqu'on choisit 'N' dans la campagne, on a une chance de perdre entre (0;2 PV)
            loss = random.randint(0,2)
            player['pv'] -= loss
            print(f"Vous avez choisi de ne pas agir : vous perdez {loss} PV en conséquence (embuscade, fatigue...). PV restants : {player['pv']}")
            if player['pv'] <= 0:
                print("Vous êtes mort·e à cause d'une mauvaise décision...")
                update_player_stats(cur, conn, player['id_joueur'], pv=0, exp=player['exp'])
                return

        step += 1

        # toutes les 10 étapes il y a un boss qui spawn
        if step % 10 == 0:
            boss_index = (step // 10) - 1
            base_boss = boss_base[boss_index % len(boss_base)]
            scale = 1.0 + (step/total_steps) * 1.2
            boss = new_enemy_instance(base_boss, scale=scale)
            print(f"\n!!! Rencontre majeure : Boss {boss['nom']} (PV {boss['pv']}, ATK {boss['attaque']}) !!!")
            success = combat_turn_by_turn(cur, conn, player, boss, comp_data)
            if not success:
                print("Vous avez été vaincu par le boss... fin.")
                return
            else:
                # big XP
                gained = 50 + step*2
                print(f"Boss terrassé ! +{gained} XP")
                xp += gained

        # Tout les 20XP on gagne 1 LVL dans l'histoire
        # On compare l'XP de la base de donnée et on ajoute l'XP gagnée a lXP deja dans la base
        total_exp_after = player['exp'] + xp
        new_level = 1 + (total_exp_after // 20)
        if new_level > player['niveau']:
            levels_gained = new_level - player['niveau']
            print(f"\n✨ NIVEAU ! Vous montez de {levels_gained} niveau(s) : {player['niveau']} -> {new_level}")
            for _ in range(levels_gained):
                player['attaque'] += 1
                player['pv'] += 5  # On augmente les PV max du joueurs a chaque LVL
            player['niveau'] = new_level
            # On update les nouvelles stats du joueurs dans la base de donnée
            update_player_stats(cur, conn, player['id_joueur'], pv=player['pv'], attaque=player['attaque'], niveau=player['niveau'])

    # On fini le jeu quand il n'y a plsu d'événements
    player['exp'] += xp
    update_player_stats(cur, conn, player['id_joueur'], pv=player['pv'], exp=player['exp'], attaque=player['attaque'], niveau=player['niveau'])
    print("\n🏁 Vous avez terminé l'aventure ! Résumé final :")
    print(f"Héros : {player['nom']} | Classe : {player['classe_nom']} | Niveau : {player['niveau']} | EXP : {player['exp']} | PV restants : {player['pv']} | ATQ : {player['attaque']}")
    print("Bravo !")

# ---------------------------
# Lancement du jeu
# ---------------------------
def main():
    conn, cur = init_db()

    print("=== JEU FANTASY (NSI) ===")
    nom = input("Nom de votre héros : ").strip()
    classes = fetch_classes_with_competence(cur)
    print("\nChoisissez une classe :\n")
    for c in classes:
        print(f"{c[0]} - {c[1]}")
        print(f"   PV : {c[2]} | ATQ : {c[3]}")
        print(f"   Capacité : {c[4]}")
        print(f"   Effet : {c[5]}\n")
    while True:
        try:
            choix = int(input("Id de la classe choisie : ").strip())
            if any(c[0] == choix for c in classes):
                break
            else:
                print("Id invalide.")
        except:
            print("Entrez un nombre.")

    create_player(cur, conn, nom, choix)
    player_row = get_player(cur)
    print(f"\nBienvenue {player_row[1]} le {player_row[8]} ! (PV: {player_row[5]}, ATQ: {player_row[6]})")
    input("\nAppuyez sur Entrée pour commencer l'aventure...")

    play_adventure(cur, conn)
    conn.close()

if __name__ == "__main__":
    main()
