import json
import os
import shutil

# Chemins vers les fichiers de registre de Home Assistant
REGISTRY_PATH = ".storage/core.entity_registry"
BACKUP_PATH = ".storage/core.entity_registry.backup_eedomus"

def migrate_ids():
    if not os.path.exists(REGISTRY_PATH):
        print(f"❌ Erreur : Le fichier {REGISTRY_PATH} est introuvable. Exécutez ce script depuis le dossier /config.")
        return

    # 1. Création d'une sauvegarde de sécurité
    print(f"💾 Création d'une sauvegarde vers {BACKUP_PATH}...")
    shutil.copy2(REGISTRY_PATH, BACKUP_PATH)

    # 2. Lecture du registre
    print("📂 Lecture du registre des entités...")
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    entities = data.get("data", {}).get("entities", [])
    modified_count = 0

    # 3. Parcours et modification des entités eedomus
    for entity in entities:
        if entity.get("platform") == "eedomus":
            old_id = entity.get("unique_id", "")
            entry_id = entity.get("config_entry_id", "")

            if not entry_id:
                continue

            # ========================================================
            # ÉTAPE A : NORMALISATION
            # On retire les préfixes éventuels ("eedomus_" ou "{entry_id}_")
            # pour isoler la "racine" de l'identifiant, quel que soit 
            # l'état actuel de l'entité (jamais migrée, ou partiellement).
            # ========================================================
            temp_id = old_id
            if temp_id.startswith("eedomus_"):
                temp_id = temp_id[8:] # retire "eedomus_"
            if temp_id.startswith(f"{entry_id}_"):
                temp_id = temp_id[len(entry_id)+1:] # retire "IDDELABOX_"

            new_id = ""
            domain = entity.get("domain")

            # ========================================================
            # ÉTAPE B : RECONSTRUCTION AU FORMAT CIBLE STRICT
            # Format: eedomus_{entry_id}_{periph_id}_[suffixe]
            # ========================================================
            if temp_id == "history_stats":
                new_id = f"eedomus_{entry_id}_history_stats"
            elif temp_id == "history_progress_global":
                new_id = f"eedomus_{entry_id}_history_progress_global"
                
            # Historique (Anciennes conventions qui commençaient par history_progress)
            elif temp_id.startswith("history_progress_"):
                periph = temp_id.replace("history_progress_", "")
                new_id = f"eedomus_{entry_id}_{periph}_history_progress"
                
            # Les cas avec suffixes classiques
            elif temp_id.endswith("_history_progress"):
                periph = temp_id.replace("_history_progress", "")
                new_id = f"eedomus_{entry_id}_{periph}_history_progress"
            elif temp_id.endswith("_battery"):
                periph = temp_id.replace("_battery", "")
                new_id = f"eedomus_{entry_id}_{periph}_battery"
            elif temp_id.endswith("_history"):
                periph = temp_id.replace("_history", "")
                new_id = f"eedomus_{entry_id}_{periph}_history"
            elif temp_id.endswith("_climate"):
                periph = temp_id.replace("_climate", "")
                new_id = f"eedomus_{entry_id}_{periph}_climate"
            elif temp_id.endswith("_scene"):
                periph = temp_id.replace("_scene", "")
                new_id = f"eedomus_{entry_id}_{periph}_scene"
            elif temp_id.endswith("_select"):
                periph = temp_id.replace("_select", "")
                new_id = f"eedomus_{entry_id}_{periph}_select"
            else:
                # Vérification des domaines sans suffixe dans leur ancien ID
                if domain in ["climate", "scene", "select"]:
                    new_id = f"eedomus_{entry_id}_{temp_id}_{domain}"
                else:
                    # Capteurs classiques, relais, lumières, timing, volume...
                    new_id = f"eedomus_{entry_id}_{temp_id}"

            # ========================================================
            # ÉTAPE C : APPLICATION (Uniquement si changement nécessaire)
            # ========================================================
            if old_id != new_id:
                print(f"🔄 Migration [{domain}] : {old_id}  ->  {new_id}")
                entity["unique_id"] = new_id
                modified_count += 1

    # 4. Écriture du fichier modifié
    if modified_count > 0:
        print(f"\n✍️ Écriture des modifications ({modified_count} entités mises à jour)...")
        with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print("✅ Migration terminée avec succès ! Vous pouvez redémarrer Home Assistant.")
    else:
        print("\nℹ️ Aucune entité à migrer. Elles ont toutes déjà le format parfait !")

if __name__ == "__main__":
    migrate_ids()