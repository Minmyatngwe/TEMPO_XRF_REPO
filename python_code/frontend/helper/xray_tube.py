import spekpy as sp 
from typing import List
import numpy as np
import pandas as pd
def get_flu(
    current:float,
    voltage:float,
    exposure_time:float,
    anode_degree:float,
    anode_target_material:str,
    filter:pd.DataFrame,
    source_to_tube_collimatory:float,
            )->tuple[np.ndarray,np.ndarray]:
    
    mas=current*exposure_time
    s=sp.Spek(kvp=voltage,th=anode_degree,targ=anode_target_material[0],mas=mas)
    
    for row in filter.to_dict("records"):
        material_name=row['filter']
        thickness=row['thickness (mm)']
        s.filter(material_name,thickness)
    
    energy_bin,fluence_list=s.get_spectrum(z=source_to_tube_collimatory)
    return energy_bin,fluence_list