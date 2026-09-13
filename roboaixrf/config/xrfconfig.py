from  pydantic import BaseModel
from .detectorConfig import Detector
from .sampleConfig import Sample 
from .xray_tube import XRayTube
from .physics_engine import Physics
from .material import Material

class XRFConfigure(BaseModel):
    
    """
        Main configuration model for an XRF simulation.

        This class stores the global simulation settings together with the
        detector, sample, X-ray tube, physics configuration, and reference
        information.

        Components such as the detector, sample, and X-ray tube can be added
        using the `add()` method. Before running a simulation,
        `validate_complete()` should be called to ensure that all required
        components have been configured.
    """

    world_material:Material 
    
    world_size_x_mm: float
    world_size_y_mm: float
    world_size_z_mm: float    
    
    detector:Detector|None=None
    sample:Sample|None=None
    xray_tube:XRayTube|None=None
    
    
    
    #physics
    physics:Physics=Physics()    
    
    def add(self,obj):
        
        """
        Add a simulation component to the configuration.

        The object type determines where it is stored:

        - `Detector` is assigned to `self.detector`.
        - `Sample` is assigned to `self.sample`.
        - `XRayTube` is assigned to `self.xray_tube`.

        Parameters
        ----------
        obj
            Simulation component to add. Supported types are
            `Detector`, `Sample`, and `XRayTube`.
        """

        if isinstance(obj,Detector):
            self.detector=obj
        
        elif isinstance(obj,Sample):
            self.sample=obj 
        elif isinstance(obj,XRayTube):
            self.xray_tube=obj
            
    
    def validate_complete(self):
        """
        Validate that all required XRF simulation components are present.

        The simulation requires a detector, sample, and X-ray tube.

        Raises
        ------
        ValueError
            If the detector, sample, or X-ray tube has not been configured.
        """

        
        if self.detector is None:
            raise ValueError("Detector is missing")
        if self.sample is None:
            raise ValueError("Sample is missing")

        if self.xray_tube is None:
            raise ValueError("Tube is missing")
            
    
