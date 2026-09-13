from pydantic import BaseModel
from .geometry import Geometry
from .material import Material
from .placement import Placement
class Internal_mask(BaseModel):
    name:str
    geometry:Geometry
    material:Material
    placement :Placement
    def model_post_init(self, context):
        if "housing" in self.geometry.shape:
            raise ValueError(
                "Internal mask geometry must be created using "
                "Geometry.circular(), Geometry.rectangular(), "
                "Geometry.rectangular_aperture(), or Geometry.circular_aperture()."
            )
        
        if self.placement.position.reference!="detector":
            raise ValueError("Internal mask placement must be created using Placement.in_front_detector()")
        