# SYSTEM UPDATE + BASIC TOOLS

sudo apt update -y
sudo apt upgrade -y

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
    nodejs \
    npm \
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


# CLONE XRF PROJECT

git clone https://github.com/Minmyatngwe/TEMPO_XRF_REPO.git

cd TEMPO_XRF_REPO

git switch new_geant4

cd ..


# DOWNLOAD GEANT4

wget https://gitlab.cern.ch/geant4/geant4/-/archive/v11.4.2/geant4-v11.4.2.tar.gz

tar -xzf geant4-v11.4.2.tar.gz


# PATCH GEANT4 SOURCE

python3 ./TEMPO_XRF_REPO/python_code/script.py geant4-v11.4.2


# BUILD GEANT4

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


# LOAD GEANT4 ENVIRONMENT

source geant4-install/bin/geant4.sh

printf 'source "%s"\n' \
    "$(realpath geant4-install/bin/geant4.sh)" >> ~/.bashrc


# BUILD XRF SIMULATION

cd TEMPO_XRF_REPO

mkdir -p build
cd build

cmake ..

cmake --build . -j$(nproc)

cd ..


# PYTHON VIRTUAL ENVIRONMENT

python3 -m venv .venv

source .venv/bin/activate

python -m pip install --upgrade pip

python -m pip install -r requirement.txt


# THREE.JS / VITE

cd python_code/vis

npm install --save-dev vite@5


# START STREAMLIT

cd ../frontend

streamlit run main.py
