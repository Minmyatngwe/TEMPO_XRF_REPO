
from pydantic import BaseModel

class Physics(BaseModel):
    interaction_bias_use:bool=True
    secondary_splitting_use:bool=True
    
    flu_use:bool=True
    auger_use:bool=True
    pixe_use:bool=False
    ignore_cut_use:bool=True
    flu_dataset_name:str="ANSTO"
    
    maximum_energy:float=1000
    
    phot_factor:int=100
    compt_factor:int=100
    rayl_factor:int=100
    
    electron_cut:float=0.01
    gamma_cut:float=0.01
    positron_cut:float=0.01
    proton_cut:float=0.01 
    