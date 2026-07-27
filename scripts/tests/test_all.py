"""Main test file to run all entity tests."""

import os
import sys
import pytest

# 1. Déterminer le dossier actuel du script (scripts/tests/)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# 2. Déterminer la racine du projet (deux dossiers plus haut)
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "../.."))

# 3. Injecter la racine dans le chemin Python pour trouver 'custom_components'
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

def main():
    """Run all tests."""
    print("🧪 Running Eedomus integration tests...")

    # 4. Liste exacte des fichiers de test à lancer
    test_files = [
        "test_cover.py",
        "test_switch.py",
        "test_light.py",
        "test_sensor.py",
        "test_integration.py",
    ]

    # 5. Convertir les noms de fichiers en chemins absolus
    pytest_args = [os.path.join(SCRIPT_DIR, f) for f in test_files]

    # 6. Ajouter les options pytest
    pytest_args.extend([
        "-v",
        "--tb=short",
    ])

    # Exécuter pytest AVEC les arguments ciblés
    exit_code = pytest.main(pytest_args)

    if exit_code == 0:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")

    return exit_code

if __name__ == "__main__":
    # Exécution synchrone standard (Pytest gère l'async en interne)
    sys.exit(main())
