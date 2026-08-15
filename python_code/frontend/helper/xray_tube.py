import spekpy as sp 
from typing import List
import numpy as np
import matplotlib.pyplot as plt 
import pandas as pd
from typing import List,Dict
def get_flu(
    current:float,#mas
    voltage:float,
    exposure_time:float,
    anode_degree:float,
    anode_target_material:str,
    filter_engine:str,
    filters:List[Dict],
    source_to_sample:float,
            )->tuple[np.ndarray,np.ndarray]:
    
    mas=current*exposure_time
    s=sp.Spek(kvp=voltage,th=anode_degree,targ=anode_target_material[0],physics="kqp")
    if filter_engine.lower()=="spekpy":
        for i in filters:
            s.filter(i['material'],i['thickness_mm'])
    
    energy_bin,fluence_list=s.get_spectrum(z=source_to_sample/10,diff=False)
    flu_number=s.get_flu(z=source_to_sample/10,mas=mas)
    print("get flu",flu_number)
    return energy_bin,fluence_list,flu_number

if __name__=="__main__":
    energy,hist,flu_number=get_flu(0.5,50,30,12,"W",pd.DataFrame({"filter":["Al"],"thickness (mm)":[0.05]}),140)
    # # data = np.column_stack((energy, hist))
    print(flu_number*0.1144993686143057/10)
    plt.plot(energy,hist)
    plt.show()