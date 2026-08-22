sudo apt update -y
sudo apt upgrade -y
sudo apt install -y git curl 
wget https://gitlab.cern.ch/geant4/geant4/-/archive/v11.4.2/geant4-v11.4.2.tar.gz
tar -xzf geant4-v11.4.2.tar.gz
python3 ./TEMPO_XRF_REPO/python_code/script.py geant4-v11.4.2
mkdir geant4-v11.4.2-build
cd geant4-v11.4.2-build
sudo apt install -y build-essential cmake
sudo apt update

sudo apt install -y \
    build-essential \
    cmake \
    wget \
    libx11-dev \
    libxmu-dev \
    libxi-dev \
    libgl1-mesa-dev \
    libglu1-mesa-dev \
    freeglut3-dev \
    mesa-common-dev \
    qtbase5-dev \
    libqt5opengl5-dev \
    libvtk9-dev \
    libvtk9-qt-dev
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
printf 'source "%s"\n' "$(realpath ../geant4-install/bin/geant4.sh)" >> ~/.bashrc
source ~/.bashrc

cd ..

cd TEMPO_XRF_REPO
mkdir build
cd build
sudo apt install -y nlohmann-json3-dev
cmake ..
cd .. 

python3 -m venv .venv
pip install --upgrade pip
source .venv/bin/activate
sudo apt update

sudo apt install -y \
    pkg-config \
    libcairo2-dev \
    libpango1.0-dev
sudo apt install -y \
    ffmpeg \
    build-essential \
    python3-dev
pip install -r requirement.txt

git switch new_geant4

cd python_code/
cd vis

rm -rf node_modules
rm -f package.json
rm -f package-lock.json
npm install --save-dev vite@5
npm ci
cd ..
cd frontend
streamlit run main.py
