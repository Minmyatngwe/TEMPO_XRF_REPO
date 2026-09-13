from pathlib import Path
import xraylib
BEARDEN_DIR = Path(r"/home/minmyatngwe/geant_4_xrf/geant4-v11.4.2-install/share/Geant4/data/G4EMLOW8.8/fluor_Bearden")
ANSTO_DIR = Path(r"/home/minmyatngwe/geant_4_xrf/geant4-v11.4.2-install/share/Geant4/data/G4EMLOW8.8/fluor_ANSTO")
OUTPUT_DIR = Path(r"/home/minmyatngwe/geant_4_xrf/geant4-v11.4.2-install/share/Geant4/data/G4EMLOW8.8/flu_combined")

OUTPUT_DIR.mkdir(exist_ok=True)

shell_map = {
    1: "K",
    
    3: "L1",
    5: "L2",
    6: "L3",

    8: "M1",
    10: "M2",
    11: "M3",
    13: "M4",
    14: "M5",

    16: "N1",
    18: "N2",
    19: "N3",
    21: "N4",
    22: "N5",
    24: "N6",
    25: "N7",

    27: "O1",
    29: "O2",
    30: "O3",
    32: "O4",
    33: "O5",
    35: "O6",
    36: "O7",
    38: "O8",
    39: "O9",

    41: "P1",
    43: "P2",
    44: "P3",
    46: "P4",
    47: "P5",
    49: "P6",
    50: "P7",
    52: "P8",
    53: "P9",
    55: "P10",
    56: "P11",

    58: "Q1",
    60: "Q2",
    61: "Q3",
}
def read_transitions(file_path):
    transitions = {}
    current_vacancy = None

    with open(file_path, "r") as file:
        for line in file:
            values = line.split()

            if not values:
                continue
            if values[0] == "-1":
                current_vacancy = None
            elif values[0] == "-2":
                break

            elif values[0] == values[1] == values[2]:
                current_vacancy = int(values[0])
                print(current_vacancy)
            else:

                origin = int(values[0])
                probability = float(values[1])
                energy = float(values[2])
                key = (current_vacancy, origin)

                transitions[key] = (probability,energy)
    return transitions
def get_xraylib_energy(Z, vacancy, origin):
    vacancy_name = shell_map.get(vacancy)
    origin_name = shell_map.get(origin)

    if vacancy_name is None or origin_name is None:
        return None
    line_name = vacancy_name + origin_name + "_LINE"
    line_id = getattr(xraylib, line_name, None)

    if line_id is None:
        return None

    try:
        energy_keV = xraylib.LineEnergy(Z, line_id)
        return energy_keV / 1000.0

    except ValueError:
        return None
def process_element(bearden_file):
    Z = int(bearden_file.stem.split("-")[-1])

    ansto_file = ANSTO_DIR / bearden_file.name
    output_file = OUTPUT_DIR / bearden_file.name
    bearden = read_transitions(bearden_file)


    if ansto_file.exists():
        ansto = read_transitions(ansto_file)
    else:
        ansto = {}
    final_transitions = {}
    for key, bearden_values in bearden.items():
        vacancy, origin = key

        bearden_probability = bearden_values[0]
        bearden_energy = bearden_values[1]
        #fusion of data
        if key in ansto:
            final_probability = ansto[key][0]
        else:
            final_probability = bearden_probability

        xraylib_energy = get_xraylib_energy(Z,vacancy,origin)

        if xraylib_energy is not None:
            final_energy = xraylib_energy
        else:
            final_energy = bearden_energy

        final_transitions[key] = (final_probability,final_energy)

    current_vacancy = None

    with open(bearden_file, "r") as source, \
         open(output_file, "w") as output:

        for line in source:

            values = line.split()

            if not values:
                output.write(line)
                continue
            if values[0] == "-1" or values[0] == "-2":

                output.write(line)
            elif values[0] == values[1] == values[2]:

                current_vacancy = int(values[0])
                output.write(line)
            else:

                origin = int(values[0])
                key = (current_vacancy,origin)
                probability, energy = final_transitions[key]
                output.write(f"{origin:<12}" f"{probability:<15.9g}" f"{energy:<15.9g}\n")
    print(f"Z={Z}: {output_file.name}")

bearden_files = [path for path in BEARDEN_DIR.glob("fl-tr-pr-*.dat") if ".commented." not in path.name]
bearden_files = sorted(bearden_files, key=lambda path: int(path.stem.split("-")[-1]))

for bearden_file in bearden_files:
    process_element(bearden_file)

