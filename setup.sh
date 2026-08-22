#!/usr/bin/env bash

set -e

# Update system
sudo apt update -y
sudo apt upgrade -y

# Install system dependencies
sudo apt install -y \
    git \
    curl \
    wget \
    build-essential \
    cmake \
    python3-dev \
    python3-venv \
    pkg-config \
    ffmpeg \
    nlohmann-json3-dev \
    libx11-dev \
    libxmu-dev \
    libxi-dev \
    libgl1-mesa-dev \
    libglu1-mesa-dev \
    freeglut3-dev \
    mesa-common-dev \
    qtbase5-dev \
    libqt5opengl5-dev \
    libcairo2-dev \
    libpango1.0-dev

# Remove old Node/npm if installed
sudo apt remove -y nodejs npm || true
sudo apt autoremove -y

# Install Node.js 22
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs

node --version
npm --version
npx --version

# Clone XRF project
git clone https://github.com/Minmyatngwe/TEMPO_XRF_REPO.git

cd TEMPO_XRF_REPO
git switch new_geant4
cd ..

# Download Geant4
wget https://gitlab.cern.ch/geant4/geant4/-/archive/v11.4.2/geant4-v11.4.2.tar.gz

tar -xzf geant4-v11.4.2.tar.gz

# Patch Geant4 source
python3 ./TEMPO_XRF_REPO/python_code/script.py geant4-v11.4.2

# Build Geant4
mkdir -p geant4-v11.4.2-build
cd geant4-v11.4.2-build

cmake ../geant4-v11.4.2 \
    -DCMAKE_INSTALL_PREFIX=../geant4-install \
    -DGEANT4_INSTALL_DATA=ON \
    -DGEANT4_BUILD_MULTITHREADED=ON \
    -DGEANT4_USE_QT=ON \
    -DGEANT4_USE_QT_QT5=ON \
    -DGEANT4_USE_OPENGL_X11=ON \
    -DGEANT4_USE_VTK=OFF

cmake --build . -j$(nproc)

cmake --install .

cd ..

# Load Geant4 environment
source geant4-install/bin/geant4.sh

GEANT4_SETUP="$(realpath geant4-install/bin/geant4.sh)"

grep -qxF "source \"$GEANT4_SETUP\"" ~/.bashrc || \
    echo "source \"$GEANT4_SETUP\"" >> ~/.bashrc

geant4-config --version

# Build XRF simulation
cd TEMPO_XRF_REPO

mkdir -p build
cd build

cmake ..

cmake --build . -j$(nproc)

ls -l sim

cd ..

# Create Python virtual environment
python3 -m venv .venv

source .venv/bin/activate

python -m pip install --upgrade pip

python -m pip install -r requirement.txt

# Install Three.js and Vite
cd python_code/vis

npm install three
npm install --save-dev vite@5

npm ls three
npm ls vite

# Start Streamlit
cd ../frontend

streamlit run main.py
