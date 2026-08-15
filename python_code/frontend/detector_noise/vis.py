import numpy as np
import matplotlib.pyplot as plt
import uproot

# Load your data
tree = uproot.open("/home/minmyatngwe/geant_4_xrf/XRF_ONLY/python_code/root_output_file/Inconel 718.root:MyTree")
df = tree.arrays(library="pd")

# 1. Let NumPy calculate the weighted counts and the bin edges
# (This does the math without drawing anything yet)
counts, bin_edges = np.histogram(df['Energy'], bins=100, weights=df['Weight'])

# 2. Calculate the exact center point of each bin
# (We add the left edge and right edge of each bin and divide by 2)
bin_centers = 0.5 * (bin_edges[1:] + bin_edges[:-1])

# 3. Plot it as a standard continuous line!
plt.figure(figsize=(8, 5))
plt.plot(bin_centers, counts, color='green', linestyle='-', linewidth=2, label='Inconel 718 Spectrum')

# 4. Make it look professional
plt.title("XRF Energy Spectrum (Line Plot)")
plt.xlabel("Energy (keV)")
plt.ylabel("Weighted Counts")
plt.legend()
plt.grid(True, alpha=0.3)
plt.show()