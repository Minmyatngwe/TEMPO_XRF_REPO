#!/usr/bin/env bash
# TEMPO_XRF_REPO - Fedora / RHEL-family machine setup (dnf)
#
# Usage on a NEW machine:
#
#   git clone --branch front --single-branch \
#     https://github.com/Minmyatngwe/TEMPO_XRF_REPO.git
#   cd TEMPO_XRF_REPO
#   chmod +x setup_tempo_xrf.sh
#   ./setup_tempo_xrf.sh
#
# To only display the commands:
#
#   cat setup_tempo_xrf.sh
#
# This script installs:
#   - Fedora/RHEL build tools and libraries
#   - xraylib C/C++ development library
#   - Geant4 11.4.2 + Geant4 datasets
#   - Node.js 22
#   - Python virtual environment and XRF Python packages
#   - Frontend requirements
#   - Three.js / Plotly.js / Vite npm dependencies
#
# It is designed for dnf-based Fedora/RHEL-family systems and is safe to rerun.

set -Eeuo pipefail

trap 'echo; echo "ERROR: setup failed at line $LINENO"; exit 1' ERR

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

GEANT4_VERSION="${GEANT4_VERSION:-11.4.2}"
GEANT4_BASE="${GEANT4_BASE:-$HOME/geant4}"

GEANT4_SOURCE_DIR="$GEANT4_BASE/geant4-v${GEANT4_VERSION}"
GEANT4_BUILD_DIR="$GEANT4_BASE/geant4-v${GEANT4_VERSION}-build"
GEANT4_INSTALL_DIR="$GEANT4_BASE/geant4-install"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$SCRIPT_DIR"
VENV_DIR="$REPO_DIR/.venv"

FRONTEND_DIR="$REPO_DIR/python_code/roboai_xrf_frontend"
VIS_DIR="$REPO_DIR/roboaixrf/vis"

echo "============================================================"
echo " TEMPO XRF machine setup"
echo "============================================================"
echo "Repository : $REPO_DIR"
echo "Geant4     : $GEANT4_VERSION"
echo "Geant4 dir : $GEANT4_INSTALL_DIR"
echo "Python venv: $VENV_DIR"
echo "============================================================"

# ---------------------------------------------------------------------------
# 0. Check operating system
# ---------------------------------------------------------------------------

if [[ -f /etc/os-release ]]; then
    . /etc/os-release
    echo "Detected OS: ${PRETTY_NAME:-unknown}"

    if ! command -v dnf >/dev/null 2>&1; then
        echo "ERROR: dnf was not found."
        echo "This setup script is intended for Fedora/RHEL-family systems."
        exit 1
    fi
else
    echo "ERROR: /etc/os-release was not found."
    exit 1
fi

# Ask for sudo once near the beginning.
sudo -v

# ---------------------------------------------------------------------------
# 1. Fedora/RHEL system packages
# ---------------------------------------------------------------------------

echo
echo ">>> Installing Fedora/RHEL packages..."

sudo dnf -y upgrade --refresh

# Fedora/RHEL package names differ from Debian/Ubuntu:
#   build-essential      -> gcc gcc-c++ make
#   libexpat1-dev        -> expat-devel
#   zlib1g-dev           -> zlib-devel
#   libxerces-c-dev      -> xerces-c-devel
#   nlohmann-json3-dev   -> json-devel
#   libx11-dev           -> libX11-devel
#   libxmu-dev           -> libXmu-devel
#   libxi-dev            -> libXi-devel