
from pydantic import validate_call
from .xrfconfig import XRFConfigure
import json
from pathlib import Path
@validate_call
def write_json(config:XRFConfigure,path:str|Path):
    
    data={
        "world":{
            "world_material":config.world_material.to_dict(),
            "world_size_x_mm":config.world_size_x_mm,
            "world_size_y_mm":config.world_size_y_mm,
            "world_size_z_mm":config.world_size_z_mm
            
        },
        

        "xray_tube":config.xray_tube.to_dict(),
        "sample":config.sample.to_dict(),
        "detector":config.detector.to_dict(),
        "physics":config.physics.model_dump()
    }
    with open(path,"w") as file:
        json.dump(data,file,indent=2)
        
    print("done")
    
    
    
        
    