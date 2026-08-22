from pathlib import Path
import sys


if len(sys.argv) != 2:
    print("Usage: python3 patch_geant4.py <geant4-source-folder>")
    sys.exit(1)


geant4_source = Path(sys.argv[1])

files = list(
    geant4_source.rglob("G4EmBiasingManager.cc")
)

if not files:
    print("ERROR: G4EmBiasingManager.cc not found")
    sys.exit(1)

if len(files) > 1:
    print("ERROR: Multiple G4EmBiasingManager.cc files found:")
    for file in files:
        print(file)
    sys.exit(1)


file_path = files[0]

print("Found:")
print(file_path)


text = file_path.read_text()


function_name = (
    "G4EmBiasingManager::ApplyDirectionalSplitting"
)

function_position = text.find(function_name)

if function_position == -1:
    print(
        "ERROR: ApplyDirectionalSplitting function not found"
    )
    sys.exit(1)


target = (
    "if (tmpSecondaries[kk]->GetParticleDefinition() "
    "== theGamma)"
)


target_position = text.find(
    target,
    function_position
)

if target_position == -1:
    print(
        "ERROR: Could not find tmpSecondaries gamma check"
    )
    sys.exit(1)


# ---------------------------------------------------------
# Check whether patch already exists
# ---------------------------------------------------------

before_target = text[
    max(function_position, target_position - 300):
    target_position
]

if "tmpSecondaries[kk] == nullptr" in before_target:
    print("Geant4 is already patched.")
    sys.exit(0)


# ---------------------------------------------------------
# Find indentation of target line
# ---------------------------------------------------------

line_start = text.rfind(
    "\n",
    0,
    target_position
) + 1

indent = text[
    line_start:
    target_position
]


patch = (
    f"{indent}if (tmpSecondaries[kk] == nullptr) {{\n"
    f"{indent}  continue;\n"
    f"{indent}}}\n\n"
)


# ---------------------------------------------------------
# Backup original file
# ---------------------------------------------------------

backup = file_path.with_suffix(
    file_path.suffix + ".bak"
)

backup.write_text(text)

print("Backup created:")
print(backup)


# ---------------------------------------------------------
# Insert patch
# ---------------------------------------------------------

new_text = (
    text[:line_start]
    + patch
    + text[line_start:]
)

file_path.write_text(new_text)


print()
print("Geant4 patch successfully applied.")
print()
print("Inserted:")
print()
print(
    "if (tmpSecondaries[kk] == nullptr) {\n"
    "  continue;\n"
    "}"
)
