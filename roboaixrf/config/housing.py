from pydantic import BaseModel,validate_call
from .geometry import Geometry
from .material import Material
from .filter import Filter
class Housing(BaseModel):
    name:str
    geometry:Geometry
    cavity_wall_material:Material
    housing_material:Material
    inner_cavity_medium_material:Material
    window_material:Material
    window_thickness_mm:float
    
        
    def __init__(self,*,_token=None,**data):
        if _token is None:
            raise ValueError("Create Housing using Housing.create()")
        
        super().__init__(**data)
        
    
    def model_post_init(self, _context):
        
        allowed_shapes={
            "Circular",
            "Rectangular"
        }
        
        if self.geometry.aperture_shape is None or self.geometry.aperture_shape not in allowed_shapes:
            raise ValueError(f"For housing aperture {self.name} geometry obj must be created by using ",
                             "Geometry.detector_housing_circular_aperture() or Geometry.detector_housing_rectangular_aperture()")
            

        geo=self.geometry
        if (
            geo.detector_clearance_mm is None
            or geo.housing_wall_thickness_mm is None
            or geo.cavity_wall_thickness_mm is None):
            raise ValueError(
                f"Housing '{self.name}' requires detector_clearance_mm, housing_wall_thickness_mm, "
                "cavity_wall_thickness_mm"
                "Create the geometry using "
                "Geometry.detector_housing_circular_aperture() or "
                "Geometry.detector_housing_rectangular_aperture()."
            )
    @classmethod
    @validate_call
    def create(cls,name:str,
               geometry:Geometry,
               housing_material:Material,
               cavity_material:Material,inner_cavity_medium_material:Material,
               window_material:Material,
               window_thickness_mm:float):
        
        
        return cls(
            _token=True,
            name=name,
            geometry=geometry,
            housing_material=housing_material,
            cavity_wall_material=cavity_material,
            inner_cavity_medium_material=inner_cavity_medium_material,
            window_material=window_material,
            window_thickness_mm=window_thickness_mm
        )        
        
    
    