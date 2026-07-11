import numpy as np 

print(np.linalg.norm([7.5,13]))

print(np.rad2deg(np.arcsin(13/15)))

angle=np.deg2rad(45)
distance=10

adj=np.cos(angle)*distance
print(adj)