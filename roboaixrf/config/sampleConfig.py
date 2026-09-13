from pydantic import BaseModel,model_validator
from .geometry import Geometry
from .placement import Placement
from .material import Material
class SampleRotation(BaseModel):
    x:float=0
    y:float=0
    z:float=0

class Sample(BaseModel):
    name:str
    material:Material
    geometry:Geometry
    sample_rotation_deg:SampleRotation|None=None
    
    @model_validator(mode="after")
    def check_shape(self):
        allowed_shape=["Rectangular","Circular"]
        
        if self.geometry.shape not in allowed_shape:
            raise ValueError(f"{self.geometry.shape} is not allowed shape for sample")
        return self 
    
    
    def to_dict(self):
        return self.model_dump(exclude_none=True)

    

    
    
    
    
    