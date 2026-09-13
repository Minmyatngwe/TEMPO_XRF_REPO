from .geometry import Geometry
from .material import Material
from .placement import Placement

from pydantic import BaseModel
class Filter(BaseModel):
    
    name:str
    geometry:Geometry
    material:Material
    placement:Placement
    
class SpekpyFilter(BaseModel):
    element:str
    thickness_mm:float