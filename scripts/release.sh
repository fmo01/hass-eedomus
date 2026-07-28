#!/usr/bin/env bash

set -e

if [ $# -ne 1 ]; then
    echo "Missing version"
    echo "Usage: $0 version"
    exit 1
fi

ROOT=$(realpath "$(dirname "$0")/..")

# 1. Cherche directement le fichier manifest.json dans custom_components
MANIFEST=$(find "${ROOT}/custom_components" -name "manifest.json" | head -n 1)

if [ -z "${MANIFEST}" ]; then
    echo "❌ Erreur : Aucun fichier manifest.json trouvé dans custom_components/"
    exit 1
fi

# 2. Récupère le dossier parent du manifest.json
CUSTOM_COMPONENT=$(dirname "${MANIFEST}")

echo "Setting version to ${1} in ${MANIFEST}"
cat <<<$(jq ".version=\"${1}\"" "${MANIFEST}") >"${MANIFEST}"

echo "Creating release zip"
cd "${CUSTOM_COMPONENT}" && zip "${ROOT}/release.zip" -r ./
