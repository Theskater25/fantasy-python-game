"""-- Tables
CREATE TABLE IF NOT EXISTS Classe (
    id_classe INTEGER PRIMARY KEY,
    nom TEXT NOT NULL,
    pv_base INTEGER,
    attaque_base INTEGER
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
(1, 'Sorcier', 8, 5),
(2, 'Archer', 6, 5),
(3, 'Chevalier', 12, 3),
(4, 'Barbare', 10, 4),
(5, 'Assassin', 6, 6);

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
(2, 'Squelette', 15, 3, 'basique'),  -- j'ai pris 3 dégâts pour le squelette
(10, 'Dragon infernal', 150, 10, 'boss'),
(11, 'Golem impitoyable', 250, 7, 'boss'),
(12, 'Jack Chistophe, Prêtre de l'Evangile de l'Eglise Ulmer Münster', 50, 4;
"""


















# ---------------------------
# Fonctions BDD utiles
# ---------------------------
def fetch_classes(cur):
    cur.execute("SELECT id_classe, nom, pv_base, attaque_base FROM Classe")
    return cur.fetchall()

def fetch_comp_for_class(cur, id_classe):
    cur.execute("SELECT id_competence, nom, effet, bonus_pv, bonus_attaque, duree_tours FROM Competence WHERE id_classe = ?", (id_classe,))
    return cur.fetchone()

def create_player(cur, conn, nom, id_classe):
    comp = fetch_comp_for_class(cur, id_classe)
    cur.execute("SELECT pv_base, attaque_base FROM Classe WHERE id_classe = ?", (id_classe,))
    pv_base, atk_base = cur.fetchone()
    # initial attack may be modified by competence bonuses (none here)
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

# utility: create a fresh enemy instance (dict) possibly scaled by multiplier
def new_enemy_instance(base_enemy, scale=1.0):
    # base_enemy: (id, nom, pv, attaque, type)
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
    # track temporary buffs/debuffs
    player_atk = player['attaque']
    player_pv = player['pv']
    enemy_pv = enemy['pv']
    enemy_atk = enemy['attaque']

    # skill usage allowed once per combat
    skill_used = False
    # track durations: dict name -> remaining turns
    durations = {'player_buff_atk':0, 'player_def_reduce_pct':0, 'enemy_frozen':0, 'player_invincible':0, 'player_atk_mult':1.0}

    # compute effect mapping per class id
    class_id = player['id_classe']
    # We'll map based on comp_data name/effect (we inserted known names)
    if comp_data:
        comp_name = comp_data[1]
    else:
        comp_name = None

    turn = 1
    while player_pv > 0 and enemy_pv > 0:
        print(f"\n-- Tour {turn} --")
        print(f"Votre PV : {player_pv} | Attaque : {player_atk} | Ennemi ({enemy['nom']}) PV : {enemy_pv} | Ennemi ATK : {enemy_atk}")
        # Player choice
        print("Choix : 1) Attaquer  2) Ne rien faire (prendre les dégats)  3) Utiliser compétence (1x/combat)")
        choix = input("Votre action (1/2/3) : ").strip()
        while choix not in ('1','2','3'):
            choix = input("Choix invalide, entrez 1, 2 ou 3 : ").strip()

        # Player action resolution
        if choix == '1':
            # attack: compute damage with possible buffs
            atk_multiplier = 1.0
            if durations['player_atk_mult'] != 1.0:
                atk_multiplier = durations['player_atk_mult']  # defined as multiplier stored here
            dmg = int(math.ceil(player_atk * atk_multiplier))
            print(f"> Vous attaquez et infligez {dmg} dégâts.")
            enemy_pv -= dmg
        elif choix == '2':
            print("> Vous attendez, vous prenez le prochain coup sans riposte.")
            # no damage to enemy, will take enemy attack below
        else:  # use competence
            if skill_used:
                print("> Compétence déjà utilisée ce combat ! Vous ratez votre action.")
            else:
                skill_used = True
                print(f"> Vous utilisez votre compétence : {comp_data[1]} - {comp_data[2]}")
                # apply skill effects according to class/comp name
                if comp_name == 'Gel':
                    durations['enemy_frozen'] = comp_data[5]  # e.g. 1 turn
                    print("L'ennemi est gelé et ne pourra pas attaquer ce tour.")
                elif comp_name == 'Flèche explosive':
                    durations['player_atk_mult'] = 1.5  # next attack deals 150% (1 turn)
                    print("Votre prochaine attaque infligera +50% dégâts.")
                elif comp_name == 'Bouclier divin':
                    durations['player_def_reduce_pct'] = 0.7  # reduce incoming by 70% for durée
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

        # After player's action, check if enemy died
        if enemy_pv <= 0:
            print(f"✅ Vous avez vaincu {enemy['nom']} !")
            # grant XP
            xp_gain = 10 if enemy['type']=='basique' else 50
            print(f"Vous gagnez {xp_gain} EXP !")
            player['exp'] += xp_gain
            # update player DB: new pv and exp stored
            player['pv'] = max(0, player_pv)
            update_player_stats(cur, conn, player['id_joueur'], pv=player['pv'], exp=player['exp'])
            return True  # win

        # Enemy's turn: check if frozen
        if durations.get('enemy_frozen',0) > 0:
            print("> L'ennemi est gelé et ne peut pas attaquer.")
            durations['enemy_frozen'] -= 1
        else:
            # enemy attacks
            dmg_received = enemy_atk
            if durations.get('player_def_reduce_pct',0):
                # reduce by the percentage (70% less means receive 30%)
                reduce_pct = durations['player_def_reduce_pct']
                dmg_received = int(math.ceil(dmg_received * (1 - reduce_pct)))
            if durations.get('player_invincible',0) > 0:
                print("> Vous êtes invincible ce tour : vous ne subissez aucun dégât.")
                dmg_received = 0

            # If player chose to "do nothing" (choice 2), they simply take damage (we already do that)
            print(f"> L'ennemi attaque et vous inflige {dmg_received} dégâts.")
            player_pv -= dmg_received

            # decrease durations counters for buffs that are counted in turns
            if durations.get('player_buff_atk',0) > 0:
                durations['player_buff_atk'] -= 1
                if durations['player_buff_atk'] == 0:
                    durations['player_atk_mult'] = 1.0
            if durations.get('player_def_reduce_turns',0):
                durations['player_def_reduce_turns'] -= 1
                if durations['player_def_reduce_turns'] == 0:
                    durations['player_def_reduce_pct'] = 0
            if durations.get('player_invincible',0) > 0:
                durations['player_invincible'] -= 1
            # player_atk_mult reset if it was a single-use (we used multiplier as one-turn effect most times)
            if choix == '1' and durations.get('player_atk_mult',1.0) != 1.0:
                # if player attacked and used a multiplier, reset it (single attack)
                # but if a buff with duration >1 exists it will be handled via player_buff_atk
                if durations.get('player_buff_atk',0) == 0:
                    durations['player_atk_mult'] = 1.0

        # check player death
        if player_pv <= 0:
            print("💀 Vous êtes tombé·e au combat...")
            player['pv'] = 0
            update_player_stats(cur, conn, player['id_joueur'], pv=player['pv'], exp=player['exp'])
            return False

        # continue to next turn
        turn += 1

    # end loop
    player['pv'] = player_pv
    update_player_stats(cur, conn, player['id_joueur'], pv=player['pv'], exp=player['exp'])
    return player_pv > 0









# ---------------------------
# Story engine (35-40 questions)
# ---------------------------
def get_story_events():
    # ~36 events, some branching indicated by text
    events = [
        "Vous franchissez la porte du village désert.",
        "Un vieux vous tend une carte usée.",
        "Vous entendez un hurlement au loin.",
        "Un sentier s'enfonce dans une forêt épaisse.",
        "Vous découvrez un pont en ruines.",
        "Une rivière bouillonnante bloque votre route.",
        "Un panneau indique 'Cimetière ancien' — allez-vous passer ?",
        "Un marchand ambulant vous propose une potion (payante).",
        "Vous apercevez des traces de pas récentes.",
        "Une grotte fume légèrement — voulez-vous entrer ?",
        "Vous trouvez un petit autel couvert de runes.",
        "Un enfant perdu vous demande de l'aide.",
        "Une lumière bleue jaillit d'un arbuste.",
        "Vous trouvez un coffre ancien.",
        "Une silhouette encapuchonnée vous observe.",
        "Un sentier mène à une claire où chantent des oiseaux.",
        "Un fermier vous parle d'un dragon aperçu plus haut.",
        "Vous sentez le sol trembler légèrement.",
        "Un rocher semble dissimuler une cavité.",
        "Un ermite vous met en garde contre des golems.",
        "Un passage étroit entre les arbres semble intéressant.",
        "Une vieille tour se dresse à l'horizon.",
        "Un pont-levis se met en mouvement soudainement.",
        "Un ruisseau aux reflets étranges coule ici.",
        "Vous trouvez une croix de pierre gravée.",
        "Une odeur de soufre vous prend à la gorge.",
        "Un troupeau de corbeaux s'envole au-dessus de vous.",
        "Vous débouchez sur une clairière remplie d'ossements.",
        "Un bruit métallique — une armure traînée ?",
        "Un chemin caché monte vers la montagne.",
        "Vous trouvez des inscriptions qui parlent d'un trésor.",
        "La nuit commence à tomber rapidement.",
        "Une voix murmure votre nom depuis l'obscurité.",
        "Un vieux pont branlant semble mener à un donjon.",
        "Vous remarquez des empreintes brûlées sur la terre.",
        "Un autel brisé fume encore d'une magie noire.",
        "Vous sentez une présence malveillante tout près.",
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
    total_steps = len(events)  # 36 events
    step = 0
    xp = 0
    # get player
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

    # We'll define boss encounters at steps 10, 20, 30 (3 bosses). Scale bosses by factor = 1 + (step/20) so they get harder as you progress.
    boss_base = [fetch_enemy_by_name(cur, "Jack Chistophe, Prêtre de l'Evangile de l'Eglise Ulmer Münster"), fetch_enemy_by_name(cur, 'Dragon infernal'), fetch_enemy_by_name(cur, 'Golem impitoyable')]

    while step < total_steps:
        event_text = events[step]
        print(f"\n== Étape {step+1}/{total_steps} ==")
        chc = ask_yes_no(event_text + " Voulez-vous agir ?")
        if chc:
            # reward: exp always
            reward = 5
            # sometimes you find extra reward or fight
            # 30% chance to encounter a basique ennemi when you say O
            if random.random() < 0.30:
                # pick basique
                be = random.choice(basic_enemies)
                scale = 1.0 + (step / total_steps) * 0.5  # scale up to +50% towards the end
                enemy = new_enemy_instance(be, scale=scale)
                print(f"⚠️ Rencontre : {enemy['nom']} (PV {enemy['pv']}, ATK {enemy['attaque']})")
                # fight
                success = combat_turn_by_turn(cur, conn, player, enemy, comp_data)
                if not success:
                    print("Fin de la partie.")
                    return
                else:
                    reward += 5
            else:
                print("Vous avancez sans rencontrer d'ennemis pour l'instant.")
            xp += reward
            print(f"+{reward} XP (Total local = {xp})")
        else:
            # negative choice: small penalty (lose 1-3 PV randomly)
            loss = random.randint(1,3)
            player['pv'] -= loss
            print(f"Vous avez choisi de ne pas agir : vous perdez {loss} PV en conséquence (embuscade, fatigue...). PV restants : {player['pv']}")
            if player['pv'] <= 0:
                print("Vous êtes mort·e à cause d'une mauvaise décision...")
                update_player_stats(cur, conn, player['id_joueur'], pv=0, exp=player['exp'])
                return

        step += 1

        # every 10 steps -> boss
        if step % 10 == 0:
            boss_index = (step // 10) - 1
            # alternate bosses; scale more the later you get
            base_boss = boss_base[boss_index % len(boss_base)]
            scale = 1.0 + (step/total_steps) * 1.2  # become significantly harder
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

        # Level up logic: every 20 XP gained in this session -> +1 niveau
        # We'll compare current DB exp + xp
        total_exp_after = player['exp'] + xp
        new_level = 1 + (total_exp_after // 20)
        if new_level > player['niveau']:
            levels_gained = new_level - player['niveau']
            print(f"\n✨ NIVEAU ! Vous montez de {levels_gained} niveau(s) : {player['niveau']} -> {new_level}")
            # apply bonuses per level
            for _ in range(levels_gained):
                player['attaque'] += 1
                player['pv'] += 5  # increase current max (simple model)
            player['niveau'] = new_level
            # store update (but exp stored after loop)
            update_player_stats(cur, conn, player['id_joueur'], pv=player['pv'], attaque=player['attaque'], niveau=player['niveau'])

    # end while all events done
    # persist final EXP and PV
    player['exp'] += xp
    update_player_stats(cur, conn, player['id_joueur'], pv=player['pv'], exp=player['exp'], attaque=player['attaque'], niveau=player['niveau'])
    print("\n🏁 Vous avez terminé l'aventure ! Résumé final :")
    print(f"Héros : {player['nom']} | Classe : {player['classe_nom']} | Niveau : {player['niveau']} | EXP : {player['exp']} | PV restants : {player['pv']} | ATQ : {player['attaque']}")
    print("Bravo !")





# ---------------------------
# Main
# ---------------------------
def main():
    conn, cur = init_db()

    print("=== JEU FANTASY (NSI) ===")
    nom = input("Nom de votre héros : ").strip()
    classes = fetch_classes(cur)
    print("\nChoisissez une classe :")
    for c in classes:
        print(f"{c[0]} - {c[1]} (PV de base: {c[2]}, ATQ de base: {c[3]})")

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

