from pydantic import BaseModel
from .geometry import Geometry
from .material import Material
from .placement import Placement


class Collimator(BaseModel):
    name:str 
    material:Material
    placement:Placement
    geometry:Geometry
    
    def validate_collimator_geometry(self):
        if self.geometry.aperture_shape is None  or self.geometry.aperture_shape not in ["Rectangular","Circular"]:
            raise ValueError(f"For collimator {self.name} geometry obj must be created by using ",
                             "Geometry.rectangular_aperture() or Geometry.circular_aperture()")
            
    