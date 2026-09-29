#!/usr/bin/env bash
# TEMPO_XRF_REPO one-shot installer
# Supports:
#   - Ubuntu / Debian family (apt)
#   - Rocky Linux 9 / RHEL-like family (dnf)
#
# What it does:
#   1. Installs system build/runtime dependencies
#   2. Installs Node.js 22
#   3. Clones/switches TEMPO_XRF_REPO to new_geant4
#   4. Builds xraylib 4.2.1 C/C++ library if needed
#   5. Downloads Geant4 11.4.2
#   6. Patches G4EmBiasingManager.cc for nullptr secondaries
#   7. Builds and installs patched Geant4
#   8. Builds the XRF C++ backend
#   9. Creates Python venv and installs requirement.txt
#  10. Installs Three.js + Vite
#  11. Starts Streamlit (disable with START_STREAMLIT=0)

set -Eeuo pipefail

trap 'echo; echo "ERROR: setup failed at line $LINENO" >&2' ERR

# -----------------------------------------------------------------------------
# Configuration (override any of these before running the script)
# -----------------------------------------------------------------------------
REPO_URL="${REPO_URL:-https://github.com/Minmyatngwe/TEMPO_XRF_REPO.git}"
REPO_BRANCH="${REPO_BRANCH:-new_geant4}"
REPO_DIR="${REPO_DIR:-$HOME/TEMPO_XRF_REPO}"

GEANT4_VERSION="${GEANT4_VERSION:-11.4.2}"
GEANT4_BASE="${GEANT4_BASE:-$HOME/geant4}"
GEANT4_SOURCE_DIR="$GEANT4_BASE/geant4-v${GEANT4_VERSION}"
GEANT4_BUILD_DIR="$GEANT4_BASE/geant4-v${GEANT4_VERSION}-build"
GEANT4_INSTALL_DIR="$GEANT4_BASE/geant4-install"
GEANT4_PATCH_MARKER="$GEANT4_INSTALL_DIR/.tempo_null_secondary_patch"

XRAYLIB_VERSION="${XRAYLIB_VERSION:-4.2.1}"
XRAYLIB_BASE="${XRAYLIB_BASE:-$HOME/xraylib}"
XRAYLIB_SOURCE_DIR="$XRAYLIB_BASE/xraylib-${XRAYLIB_VERSION}"
XRAYLIB_BUILD_DIR="$XRAYLIB_BASE/xraylib-${XRAYLIB_VERSION}-build"

# ON keeps the Qt5/OpenGL Geant4 UI from your Ubuntu script.
# For a compute-only/headless node, run: GEANT4_GUI=OFF ./setup_tempo_xrf_all.sh
GEANT4_GUI="${GEANT4_GUI:-ON}"
START_STREAMLIT="${START_STREAMLIT:-1}"

log() {
    echo
    echo "======================================================================"
    echo ">>> $*"
    echo "======================================================================"
}

# sudo wrapper that also works when the script is run as root.
if [[ "${EUID}" -eq 0 ]]; then
    SUDO=()
else
    if ! command -v sudo >/dev/null 2>&1; then
        echo "ERROR: sudo is required when not running as root." >&2
        exit 1
    fi
    sudo -v
    SUDO=(sudo)
fi

# -----------------------------------------------------------------------------
# 0. Detect operating system
# -----------------------------------------------------------------------------
log "Detecting operating system"

if [[ ! -r /etc/os-release ]]; then
    echo "ERROR: /etc/os-release not found." >&2
    exit 1
fi

# shellcheck disable=SC1091
source /etc/os-release
OS_ID="${ID:-unknown}"
OS_LIKE="${ID_LIKE:-}"

echo "Detected: ${PRETTY_NAME:-$OS_ID}"

PKG_FAMILY=""
if command -v apt-get >/dev/null 2>&1; then
    PKG_FAMILY="apt"
elif command -v dnf >/dev/null 2>&1; then
    PKG_FAMILY="dnf"
else
    echo "ERROR: This script currently supports apt or dnf based systems." >&2
    exit 1
fi

# -----------------------------------------------------------------------------
# 1. System dependencies
# -----------------------------------------------------------------------------
log "Installing system dependencies"

if [[ "$PKG_FAMILY" == "apt" ]]; then
    "${SUDO[@]}" apt-get update
    DEBIAN_FRONTEND=noninteractive "${SUDO[@]}" apt-get upgrade -y

    DEBIAN_FRONTEND=noninteractive "${SUDO[@]}" apt-get install -y \
        git \
        git-lfs \
        curl \
        wget \
        ca-certificates \
        build-essential \
        cmake \
        ninja-build \
        meson \
        pkg-config \
        python3 \
        python3-dev \
        python3-venv \
        python3-pip \
        ffmpeg \
        nlohmann-json3-dev \
        libexpat1-dev \
        libxerces-c-dev \
        libxml2-dev \
        zlib1g-dev \
        libx11-dev \
        libxmu-dev \
        libxi-dev \
        libxext-dev \
        libxrender-dev \
        libgl1-mesa-dev \
        libglu1-mesa-dev \
        freeglut3-dev \
        mesa-common-dev \
        qtbase5-dev \
        libqt5opengl5-dev \
        libcairo2-dev \
        libpango1.0-dev \
        tar \
        gzip \
        unzip

    SYSTEM_PYTHON="python3"
    XRAYLIB_LIBDIR="lib"

else
    "${SUDO[@]}" dnf install -y dnf-plugins-core

    # EPEL is available directly on Rocky Linux. On some RHEL-derived systems
    # the package may not exist until EPEL is configured, so do not abort here.
    "${SUDO[@]}" dnf install -y epel-release || true
    "${SUDO[@]}" dnf config-manager --set-enabled crb || true
    "${SUDO[@]}" dnf makecache

    "${SUDO[@]}" dnf install -y \
        gcc \
        gcc-c++ \
        make \
        cmake \
        ninja-build \
        meson \
        pkgconf-pkg-config \
        git \
        git-lfs \
        curl \
        wget \
        ca-certificates \
        tar \
        gzip \
        unzip \
        python3.11 \
        python3.11-devel \
        python3.11-pip \
        expat-devel \
        zlib-devel \
        xerces-c-devel \
        libxml2-devel \
        libX11-devel \
        libXmu-devel \
        libXi-devel \
        libXext-devel \
        libXrender-devel \
        mesa-libGL-devel \
        mesa-libGLU-devel \
        freeglut-devel \
        qt5-qtbase-devel \
        cairo-devel \
        pango-devel

    # Different EL9 repositories expose nlohmann-json under different package
    # names. Try the one already used by your Rocky setup first.
    if ! "${SUDO[@]}" dnf install -y json-devel; then
        "${SUDO[@]}" dnf install -y nlohmann-json-devel
    fi

    # ffmpeg is not present in every stock EL9 repository. It is not required
    # for compiling Geant4, so install it when available without breaking setup.
    "${SUDO[@]}" dnf install -y ffmpeg-free 2>/dev/null || \
        "${SUDO[@]}" dnf install -y ffmpeg 2>/dev/null || \
        echo "WARNING: ffmpeg was not available from the enabled dnf repositories."

    SYSTEM_PYTHON="python3.11"
    XRAYLIB_LIBDIR="lib64"
fi

git lfs install

echo "Compiler: $(g++ --version | head -n 1)"
echo "CMake   : $(cmake --version | head -n 1)"
echo "Python  : $($SYSTEM_PYTHON --version)"

# -----------------------------------------------------------------------------
# 2. Node.js 22
# -----------------------------------------------------------------------------
log "Installing/checking Node.js 22"

NEED_NODE=1
if command -v node >/dev/null 2>&1; then
    NODE_MAJOR="$(node -p 'process.versions.node.split(".")[0]' 2>/dev/null || echo 0)"
    if [[ "$NODE_MAJOR" -ge 22 ]]; then
        NEED_NODE=0
    fi
fi

if [[ "$NEED_NODE" -eq 1 ]]; then
    if [[ "$PKG_FAMILY" == "apt" ]]; then
        "${SUDO[@]}" apt-get remove -y nodejs npm || true
        "${SUDO[@]}" apt-get autoremove -y || true
        curl -fsSL https://deb.nodesource.com/setup_22.x -o /tmp/nodesource_setup.sh
        if [[ "${EUID}" -eq 0 ]]; then
            bash /tmp/nodesource_setup.sh
        else
            sudo -E bash /tmp/nodesource_setup.sh
        fi
        rm -f /tmp/nodesource_setup.sh
        "${SUDO[@]}" apt-get install -y nodejs
    else
        "${SUDO[@]}" dnf remove -y nodejs npm || true
        curl -fsSL https://rpm.nodesource.com/setup_22.x -o /tmp/nodesource_setup.sh
        "${SUDO[@]}" bash /tmp/nodesource_setup.sh
        "${SUDO[@]}" dnf install -y nodejs
        rm -f /tmp/nodesource_setup.sh
    fi
fi

echo "Node: $(node --version)"
echo "npm : $(npm --version)"
echo "npx : $(npx --version)"

# -----------------------------------------------------------------------------
# 3. Use existing TEMPO_XRF_REPO
# -----------------------------------------------------------------------------
log "Using existing TEMPO_XRF_REPO"

# Do NOT clone, fetch, pull, checkout, switch, stash, reset, or modify Git state.
if [[ ! -d "$REPO_DIR" ]]; then
    echo "ERROR: Repository directory does not exist: $REPO_DIR" >&2
    exit 1
fi

echo "Repository: $REPO_DIR"

if [[ -d "$REPO_DIR/.git" ]]; then
    echo "Branch    : $(git -C "$REPO_DIR" branch --show-current 2>/dev/null || true)"
    echo "Commit    : $(git -C "$REPO_DIR" rev-parse --short HEAD 2>/dev/null || true)"
fi

# Current branch paths first; older repo layouts remain supported as fallbacks.
if [[ -f "$REPO_DIR/python_code/frontend/main.py" ]]; then
    FRONTEND_DIR="$REPO_DIR/python_code/frontend"
elif [[ -f "$REPO_DIR/python_code/roboai_xrf_frontend/main.py" ]]; then
    FRONTEND_DIR="$REPO_DIR/python_code/roboai_xrf_frontend"
else
    echo "ERROR: Could not locate Streamlit main.py." >&2
    exit 1
fi

if [[ -f "$REPO_DIR/python_code/vis/package.json" ]]; then
    VIS_DIR="$REPO_DIR/python_code/vis"
elif [[ -f "$REPO_DIR/roboaixrf/vis/package.json" ]]; then
    VIS_DIR="$REPO_DIR/roboaixrf/vis"
else
    VIS_DIR=""
fi

if [[ -f "$REPO_DIR/requirement.txt" ]]; then
    REQUIREMENTS_FILE="$REPO_DIR/requirement.txt"
elif [[ -f "$REPO_DIR/requirements.txt" ]]; then
    REQUIREMENTS_FILE="$REPO_DIR/requirements.txt"
elif [[ -f "$FRONTEND_DIR/requirements.txt" ]]; then
    REQUIREMENTS_FILE="$FRONTEND_DIR/requirements.txt"
else
    REQUIREMENTS_FILE=""
fi

echo "Frontend   : $FRONTEND_DIR"
echo "Visualiser : ${VIS_DIR:-not found}"
echo "Requirements: ${REQUIREMENTS_FILE:-not found}"

# -----------------------------------------------------------------------------
# 4. xraylib C/C++ library
# -----------------------------------------------------------------------------
log "Installing/checking xraylib ${XRAYLIB_VERSION} C/C++ library"

export PKG_CONFIG_PATH="/usr/local/lib64/pkgconfig:/usr/local/lib/pkgconfig:${PKG_CONFIG_PATH:-}"
export LD_LIBRARY_PATH="/usr/local/lib64:/usr/local/lib:${LD_LIBRARY_PATH:-}"

if pkg-config --exists libxrl 2>/dev/null; then
    echo "xraylib already installed: $(pkg-config --modversion libxrl)"
else
    mkdir -p "$XRAYLIB_BASE"
    XRAYLIB_ARCHIVE="$XRAYLIB_BASE/xraylib-${XRAYLIB_VERSION}.tar.gz"
    XRAYLIB_URL="https://github.com/tschoonj/xraylib/archive/refs/tags/xraylib-${XRAYLIB_VERSION}.tar.gz"

    if [[ ! -f "$XRAYLIB_ARCHIVE" ]]; then
        curl -fL "$XRAYLIB_URL" -o "$XRAYLIB_ARCHIVE"
    fi

    rm -rf "$XRAYLIB_SOURCE_DIR" "$XRAYLIB_BUILD_DIR"
    mkdir -p "$XRAYLIB_SOURCE_DIR"

    tar -xzf "$XRAYLIB_ARCHIVE" \
        -C "$XRAYLIB_SOURCE_DIR" \
        --strip-components=1

    meson setup \
        "$XRAYLIB_BUILD_DIR" \
        "$XRAYLIB_SOURCE_DIR" \
        --prefix=/usr/local \
        --libdir="$XRAYLIB_LIBDIR" \
        --buildtype=release \
        -Dpython-bindings=disabled \
        -Dpython-numpy-bindings=disabled \
        -Dfortran-bindings=disabled

    meson compile -C "$XRAYLIB_BUILD_DIR" -j "$(nproc)"
    "${SUDO[@]}" meson install -C "$XRAYLIB_BUILD_DIR"
    "${SUDO[@]}" ldconfig
fi

if ! pkg-config --exists libxrl; then
    echo "ERROR: xraylib C/C++ library was not detected after installation." >&2
    exit 1
fi

echo "xraylib C/C++: $(pkg-config --modversion libxrl)"

# -----------------------------------------------------------------------------
# 5. Download Geant4 source
# -----------------------------------------------------------------------------
log "Preparing Geant4 ${GEANT4_VERSION} source"

mkdir -p "$GEANT4_BASE"
GEANT4_ARCHIVE="$GEANT4_BASE/geant4-v${GEANT4_VERSION}.tar.gz"
GEANT4_URL="https://gitlab.cern.ch/geant4/geant4/-/archive/v${GEANT4_VERSION}/geant4-v${GEANT4_VERSION}.tar.gz"

if [[ ! -f "$GEANT4_ARCHIVE" ]]; then
    curl -fL "$GEANT4_URL" -o "$GEANT4_ARCHIVE"
fi

if [[ ! -d "$GEANT4_SOURCE_DIR" ]]; then
    tar -xzf "$GEANT4_ARCHIVE" -C "$GEANT4_BASE"
fi

if [[ ! -d "$GEANT4_SOURCE_DIR" ]]; then
    echo "ERROR: Expected Geant4 source directory was not created:" >&2
    echo "  $GEANT4_SOURCE_DIR" >&2
    exit 1
fi

# -----------------------------------------------------------------------------
# 6. Patch G4EmBiasingManager.cc
# -----------------------------------------------------------------------------
log "Applying Geant4 nullptr-secondary patch"

set +e
"$SYSTEM_PYTHON" - "$GEANT4_SOURCE_DIR" <<'PY'
from pathlib import Path
import sys

if len(sys.argv) != 2:
    print("ERROR: internal patch invocation requires the Geant4 source folder")
    sys.exit(2)

geant4_source = Path(sys.argv[1]).resolve()

preferred = (
    geant4_source
    / "source/processes/electromagnetic/utils/src/G4EmBiasingManager.cc"
)

if preferred.is_file():
    files = [preferred]
else:
    files = list(geant4_source.rglob("G4EmBiasingManager.cc"))

if not files:
    print("ERROR: G4EmBiasingManager.cc not found")
    sys.exit(2)

if len(files) > 1:
    print("ERROR: Multiple G4EmBiasingManager.cc files found:")
    for file in files:
        print(file)
    sys.exit(2)

file_path = files[0]
print(f"Found: {file_path}")

text = file_path.read_text()
function_name = "G4EmBiasingManager::ApplyDirectionalSplitting"
function_position = text.find(function_name)

if function_position == -1:
    print("ERROR: ApplyDirectionalSplitting function not found")
    sys.exit(2)

target = (
    "if (tmpSecondaries[kk]->GetParticleDefinition() "
    "== theGamma)"
)

target_position = text.find(target, function_position)

# Some Geant4 formatting may put the comparison on one line with different
# whitespace. Fall back to locating the dereference itself inside the function.
if target_position == -1:
    dereference = "tmpSecondaries[kk]->GetParticleDefinition()"
    target_position = text.find(dereference, function_position)

if target_position == -1:
    print("ERROR: Could not find tmpSecondaries gamma check")
    sys.exit(2)

line_start = text.rfind("\n", 0, target_position) + 1

# Do not patch twice.
search_start = max(function_position, line_start - 600)
before_target = text[search_start:line_start]
if "tmpSecondaries[kk] == nullptr" in before_target:
    print("Geant4 source is already patched.")
    sys.exit(0)

indent = text[line_start:target_position]
if indent.strip():
    # If target_position is in the middle of a line because fallback matching
    # was used, keep only leading whitespace as indentation.
    indent = indent[: len(indent) - len(indent.lstrip())]

patch = (
    f"{indent}if (tmpSecondaries[kk] == nullptr) {{\n"
    f"{indent}  continue;\n"
    f"{indent}}}\n\n"
)

backup = file_path.with_suffix(file_path.suffix + ".bak")
if not backup.exists():
    backup.write_text(text)
    print(f"Backup created: {backup}")
else:
    print(f"Backup already exists: {backup}")

new_text = text[:line_start] + patch + text[line_start:]
file_path.write_text(new_text)

# Verify the exact inserted guard is now present near the target.
verify = file_path.read_text()
verify_position = verify.find("tmpSecondaries[kk] == nullptr", function_position)
if verify_position == -1:
    print("ERROR: patch verification failed")
    sys.exit(2)

print("Geant4 patch successfully applied.")
print("Inserted:")
print("if (tmpSecondaries[kk] == nullptr) {")
print("  continue;")
print("}")

# Exit 10 tells the Bash script that the source changed and Geant4 must rebuild.
sys.exit(10)
PY
PATCH_STATUS=$?
set -e

if [[ "$PATCH_STATUS" -eq 10 ]]; then
    PATCH_CHANGED=1
elif [[ "$PATCH_STATUS" -eq 0 ]]; then
    PATCH_CHANGED=0
else
    echo "ERROR: Geant4 patch step failed with status $PATCH_STATUS." >&2
    exit "$PATCH_STATUS"
fi

# -----------------------------------------------------------------------------
# 7. Build/install Geant4
# -----------------------------------------------------------------------------
log "Building/installing patched Geant4 ${GEANT4_VERSION}"

NEED_GEANT4_BUILD=0

if [[ ! -x "$GEANT4_INSTALL_DIR/bin/geant4-config" ]]; then
    NEED_GEANT4_BUILD=1
else
    INSTALLED_G4_VERSION="$("$GEANT4_INSTALL_DIR/bin/geant4-config" --version 2>/dev/null || true)"
    if [[ "$INSTALLED_G4_VERSION" != "$GEANT4_VERSION" ]]; then
        NEED_GEANT4_BUILD=1
    fi
fi

if [[ "$PATCH_CHANGED" -eq 1 || ! -f "$GEANT4_PATCH_MARKER" ]]; then
    NEED_GEANT4_BUILD=1
fi

if [[ "$NEED_GEANT4_BUILD" -eq 1 ]]; then
    rm -rf "$GEANT4_BUILD_DIR"
    mkdir -p "$GEANT4_BUILD_DIR" "$GEANT4_INSTALL_DIR"

    G4_CMAKE_ARGS=(
        -S "$GEANT4_SOURCE_DIR"
        -B "$GEANT4_BUILD_DIR"
        -G Ninja
        -DCMAKE_BUILD_TYPE=Release
        -DCMAKE_INSTALL_PREFIX="$GEANT4_INSTALL_DIR"
        -DGEANT4_INSTALL_DATA=ON
        -DGEANT4_BUILD_MULTITHREADED=ON
        -DGEANT4_INSTALL_EXAMPLES=OFF
        -DGEANT4_USE_GDML=ON
        -DGEANT4_USE_SYSTEM_EXPAT=ON
        -DGEANT4_USE_SYSTEM_XERCESC=ON
        -DGEANT4_USE_VTK=OFF
    )

    if [[ "${GEANT4_GUI^^}" == "ON" || "${GEANT4_GUI}" == "1" ]]; then
        G4_CMAKE_ARGS+=(
            -DGEANT4_USE_QT=ON
            -DGEANT4_USE_QT_QT5=ON
            -DGEANT4_USE_OPENGL_X11=ON
        )
    else
        G4_CMAKE_ARGS+=(
            -DGEANT4_USE_QT=OFF
            -DGEANT4_USE_OPENGL_X11=OFF
        )
    fi

    cmake "${G4_CMAKE_ARGS[@]}"
    cmake --build "$GEANT4_BUILD_DIR" -j "$(nproc)"
    cmake --install "$GEANT4_BUILD_DIR"
    touch "$GEANT4_PATCH_MARKER"
else
    echo "Patched Geant4 ${GEANT4_VERSION} is already installed; skipping rebuild."
fi

if [[ ! -f "$GEANT4_INSTALL_DIR/bin/geant4.sh" ]]; then
    echo "ERROR: Geant4 environment script not found:" >&2
    echo "  $GEANT4_INSTALL_DIR/bin/geant4.sh" >&2
    exit 1
fi

# shellcheck disable=SC1091
source "$GEANT4_INSTALL_DIR/bin/geant4.sh"

echo "Geant4: $(geant4-config --version)"

# -----------------------------------------------------------------------------
# 8. Persist environment
# -----------------------------------------------------------------------------
log "Saving Geant4/xraylib environment in ~/.bashrc"

ENV_START="# >>> TEMPO_XRF environment >>>"
ENV_END="# <<< TEMPO_XRF environment <<<"

# Remove an older copy of our block so rerunning the installer updates paths.
if grep -Fq "$ENV_START" "$HOME/.bashrc" 2>/dev/null; then
    "$SYSTEM_PYTHON" - "$HOME/.bashrc" "$ENV_START" "$ENV_END" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
start = sys.argv[2]
end = sys.argv[3]
text = path.read_text() if path.exists() else ""

while start in text and end in text:
    a = text.index(start)
    b = text.index(end, a) + len(end)
    # Remove one following newline too when present.
    if b < len(text) and text[b:b+1] == "\n":
        b += 1
    text = text[:a].rstrip() + "\n" + text[b:].lstrip("\n")

path.write_text(text)
PY
fi

cat >> "$HOME/.bashrc" <<EOF

$ENV_START
export PKG_CONFIG_PATH="/usr/local/lib64/pkgconfig:/usr/local/lib/pkgconfig:\${PKG_CONFIG_PATH:-}"
export LD_LIBRARY_PATH="/usr/local/lib64:/usr/local/lib:\${LD_LIBRARY_PATH:-}"
source "$GEANT4_INSTALL_DIR/bin/geant4.sh"
export PYTHONPATH="$REPO_DIR:\${PYTHONPATH:-}"
$ENV_END
EOF

export PYTHONPATH="$REPO_DIR:${PYTHONPATH:-}"

# -----------------------------------------------------------------------------
# 9. Build the XRF C++ backend
# -----------------------------------------------------------------------------
log "Building TEMPO XRF C++ backend"

if [[ -f "$REPO_DIR/CMakeLists.txt" ]]; then
    PROJECT_CMAKE_DIR="$REPO_DIR"
elif [[ -f "$REPO_DIR/geant4_code/CMakeLists.txt" ]]; then
    PROJECT_CMAKE_DIR="$REPO_DIR/geant4_code"
elif [[ -f "$REPO_DIR/roboaixrf/geant4_code/CMakeLists.txt" ]]; then
    PROJECT_CMAKE_DIR="$REPO_DIR/roboaixrf/geant4_code"
else
    echo "ERROR: Could not find the project CMakeLists.txt." >&2
    exit 1
fi

# Current new_geant4 branch expects repo/build.
if [[ "$PROJECT_CMAKE_DIR" == "$REPO_DIR" ]]; then
    PROJECT_BUILD_DIR="$REPO_DIR/build"
else
    PROJECT_BUILD_DIR="$PROJECT_CMAKE_DIR/build"
fi

rm -rf "$PROJECT_BUILD_DIR"

cmake \
    -S "$PROJECT_CMAKE_DIR" \
    -B "$PROJECT_BUILD_DIR" \
    -G Ninja \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_PREFIX_PATH="$GEANT4_INSTALL_DIR;/usr/local"

cmake --build "$PROJECT_BUILD_DIR" -j "$(nproc)"

if [[ -x "$PROJECT_BUILD_DIR/sim" ]]; then
    echo "Simulation binary: $PROJECT_BUILD_DIR/sim"
    ls -lh "$PROJECT_BUILD_DIR/sim"
else
    echo "WARNING: build completed, but $PROJECT_BUILD_DIR/sim was not found."
fi

# -----------------------------------------------------------------------------
# 10. Python virtual environment + dependencies
# -----------------------------------------------------------------------------
log "Creating Python virtual environment"

VENV_DIR="$REPO_DIR/.venv"

if [[ -x "$VENV_DIR/bin/python" ]]; then
    VENV_MAJOR_MINOR="$($VENV_DIR/bin/python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || true)"
    SYSTEM_MAJOR_MINOR="$($SYSTEM_PYTHON -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
    if [[ "$VENV_MAJOR_MINOR" != "$SYSTEM_MAJOR_MINOR" ]]; then
        echo "Existing venv uses Python $VENV_MAJOR_MINOR; recreating with $SYSTEM_MAJOR_MINOR."
        rm -rf "$VENV_DIR"
    fi
fi

if [[ ! -d "$VENV_DIR" ]]; then
    "$SYSTEM_PYTHON" -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

python -m pip install --upgrade pip setuptools wheel

if [[ -n "$REQUIREMENTS_FILE" ]]; then
    python -m pip install -r "$REQUIREMENTS_FILE"
else
    echo "WARNING: No requirements file found; installing core Python packages."
    python -m pip install \
        streamlit \
        pandas \
        plotly \
        numpy \
        pydantic \
        spekpy \
        uproot \
        awkward \
        xraylib
fi

# Ensure Python xraylib is available even if an older requirements file omitted it.
python -m pip install xraylib

# Install the repository itself when Python package metadata exists.
if [[ -f "$REPO_DIR/pyproject.toml" || -f "$REPO_DIR/setup.py" || -f "$REPO_DIR/setup.cfg" ]]; then
    python -m pip install -e "$REPO_DIR"
fi

# -----------------------------------------------------------------------------
# 11. Three.js + Vite
# -----------------------------------------------------------------------------
log "Installing JavaScript visualisation dependencies"

if [[ -n "$VIS_DIR" ]]; then
    cd "$VIS_DIR"

    if [[ -f package-lock.json ]]; then
        npm ci
    else
        npm install
    fi

    # Keep exactly the dependencies requested by your original installer.
    npm install three
    npm install --save-dev vite@5

    npm ls three
    npm ls vite
else
    echo "WARNING: visualization package.json was not found; skipping npm setup."
fi

# -----------------------------------------------------------------------------
# 12. Verification
# -----------------------------------------------------------------------------
log "Verifying installation"

cd "$REPO_DIR"

echo "OS          : ${PRETTY_NAME:-$OS_ID}"
echo "Repository  : $REPO_DIR"
echo "Git branch  : $(git branch --show-current)"
echo "Git commit  : $(git rev-parse --short HEAD)"
echo "G++         : $(g++ --version | head -n 1)"
echo "CMake       : $(cmake --version | head -n 1)"
echo "Geant4      : $(geant4-config --version)"
echo "xraylib C   : $(pkg-config --modversion libxrl)"
echo "Python      : $(python --version)"
echo "pip         : $(python -m pip --version)"
echo "Node        : $(node --version)"
echo "npm         : $(npm --version)"
echo "Frontend    : $FRONTEND_DIR"
echo "Backend     : $PROJECT_BUILD_DIR"

python - <<'PY'
mods = [
    "numpy",
    "pandas",
    "plotly",
    "pydantic",
    "streamlit",
    "spekpy",
    "uproot",
    "awkward",
    "xraylib",
]

for name in mods:
    module = __import__(name)
    version = getattr(module, "__version__", "imported")
    print(f"{name:12s}: {version}")
PY

log "SETUP COMPLETE"

echo "For future terminals:"
echo "  cd \"$REPO_DIR\""
echo "  source \"$GEANT4_INSTALL_DIR/bin/geant4.sh\""
echo "  source \"$VENV_DIR/bin/activate\""
echo

echo "To rebuild the XRF backend later:"
echo "  source \"$GEANT4_INSTALL_DIR/bin/geant4.sh\""
echo "  cmake --build \"$PROJECT_BUILD_DIR\" -j\$(nproc)"
echo

echo "To force a full Geant4 rebuild later:"
echo "  rm -f \"$GEANT4_PATCH_MARKER\""
echo "  bash \"$0\""
echo

# -----------------------------------------------------------------------------
# 13. Start Streamlit
# -----------------------------------------------------------------------------
if [[ "$START_STREAMLIT" == "1" ]]; then
    log "Starting Streamlit"
    cd "$FRONTEND_DIR"
    exec python -m streamlit run main.py
else
    echo "Streamlit was not started because START_STREAMLIT=$START_STREAMLIT"
    echo "Start it manually with:"
    echo "  cd \"$FRONTEND_DIR\""
    echo "  source \"$VENV_DIR/bin/activate\""
    echo "  python -m streamlit run main.py"
fi
