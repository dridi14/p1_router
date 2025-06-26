import json
from collections import defaultdict

MAX_ENTITIES_PER_UNIVERSE = 170

def validate_config(path="config/config.json"):
    with open(path, "r", encoding="utf-8") as f:
        config = json.load(f)

    universes = defaultdict(set)

    for block in config:
        u = block["universe"]
        ids = set(range(block["from"], block["to"] + 1))

        # Vérifie les doublons d'entité
        overlap = universes[u].intersection(ids)
        if overlap:
            print(f"⚠️ Doublons dans l'univers {u}: {sorted(overlap)}")

        universes[u].update(ids)

    # Vérifie le dépassement DMX
    for u, ids in universes.items():
        if len(ids) > MAX_ENTITIES_PER_UNIVERSE:
            print(f"❌ Univers {u} contient {len(ids)} entités (limite = {MAX_ENTITIES_PER_UNIVERSE})")
        else:
            print(f"✅ Univers {u} OK ({len(ids)} entités)")

if __name__ == "__main__":
    validate_config()
