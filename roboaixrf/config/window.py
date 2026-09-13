from pydantic import BaseModel
from .geometry import Geometry
from .material import Material
class TubeWindow(BaseModel):
    name:str
    material:Material
    thickness_mm:float