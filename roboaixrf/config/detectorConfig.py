from pydantic import BaseModel,model_validator,ConfigDict,validate_call
from .geometry import Geometry
from .placement import Placement
from .material import Material
from .filter import Filter
from .collimator import Collimator
from .housing import Housing
from .internal_mask import Internal_mask

class Detector(BaseModel):
    """
    Configuration model for an XRF detector.

    The detector contains its geometry, material, placement, and optional
    components such as filters, housing, internal masks, and collimators.

    Parameters
    ----------
    name : str
        Name used to identify the detector.

    geometry : Geometry
        Geometry configuration of the detector.

    placement : Placement
        Position and orientation of the detector relative to the sample.

    material : Material
        Material used for the active detector volume.

    detector_filters : list[Filter] | None
        Optional filters positioned in front of the detector.

    housing : Housing | None
        Optional detector housing.

    internal_masks : list[Internal_mask] | None
        Optional masks located inside the detector housing.

    detector_collimators : list[Collimator] | None
        Optional collimators positioned in front of the detector.
    """

    name:str
    geometry:Geometry
    placement:Placement
    material:Material
    detector_filters:list[Filter]|None=[]
    housing:Housing|None=None
    internal_masks:list[Internal_mask]|None=[]
    
    detector_collimators:list[Collimator]|None=[]
    model_config = ConfigDict(validate_assignment=True)

    @model_validator(mode="after")
    def check_geometry(self):
        allowed_shape={
            "Circular",
            "Rectangular"
        }
        
        if self.geometry.shape  not in allowed_shape:
            raise ValueError(
                    f"{self.geometry.shape} shape is not allowed for Detector"
                )

        return self    
    @validate_call
    def add_filter(self,filter:Filter ):
        if filter.placement.position.reference!="detector":
            raise ValueError(
                "Detector filter placement must be created using Placement.in_front_of_detector()"
            )
        self.detector_filters.append(filter)
    @validate_call
    def add_collimator(self,collimator:Collimator):
        if collimator.placement.position.reference!="detector":
            raise ValueError(
                "Detector collimator placement must be created using Placement.in_front_of_detector()"
            )

        self.detector_collimators.append(collimator)
    @validate_call
    def add_internal_mask(self,internal_mask:Internal_mask):
        
        if self.housing is None:
            raise ValueError("Internal mask canot be used without using housing")
        
        self.internal_masks.append(internal_mask)
        
    @validate_call
    def add_housing(self,housing:Housing):
        self.housing=housing
    @validate_call
    def to_dict(self):
        
        return self.model_dump(
            exclude_none=True
        )
        
