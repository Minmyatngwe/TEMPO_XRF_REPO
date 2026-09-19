from pydantic import BaseModel,ConfigDict,validate_call
from .placement import Placement
from .material import Material
from .filter import Filter,SpekpyFilter
from .window import TubeWindow
from pathlib import Path
import pandas as pd 
class TubePlacement(BaseModel):
    """
    Defines the geometric placement parameters of an X-ray tube
    relative to the sample.

    Parameters
    ----------
    focal_spot_to_sample_distance_mm : float
        Distance from the X-ray tube focal spot to the sample in millimeters.

    tube_window_to_sample_distance_mm : float
        Distance from the tube window to the sample in millimeters.

    elevation_deg : float
        Elevation angle of the X-ray tube relative to the sample in degrees.

    azimuth_deg : float
        Azimuth angle of the X-ray tube around the sample in degrees.
    """

    focal_spot_to_sample_distance_mm: float
    tube_window_to_sample_distance_mm:float
    elevation_deg: float
    azimuth_deg: float
    
    def __str__(self):
        return f"TubePlacement({super().__str__()})"
class XRayTube(BaseModel):
    
    """
    Configuration model for an X-ray tube used in an XRF simulation.

    The model contains the physical operating parameters of the tube,
    its placement relative to the sample, the virtual collimator geometry,
    tube window, and optional filters.

    XRayTube objects must be created using the `create()` class method.
    The tube window and filters can be added afterwards using the
    corresponding setter methods.

    Parameters
    ----------
    name : str
        Name used to identify the X-ray tube.

    current_ma : float
        Tube current in milliamperes.

    voltage_kv : float
        Tube operating voltage in kilovolts.

    anode_angle_deg : float
        Anode angle in degrees.

    anode_symbol : str
        Chemical symbol of the anode target material.

    focal_spot_diameter_mm : float
        Diameter of the X-ray tube focal spot in millimeters.

    tube_collimator_radius_mm : float
        Radius of the virtual tube collimator in millimeters.

    tube_window_to_virtual_collimator_distance_mm : float
        Distance from the tube window to the virtual collimator
        in millimeters.

    tube_window_to_sample_distance_mm : float
        Distance from the tube window to the sample in millimeters.

    placement : Placement
        Placement configuration defining the tube position and orientation.
    """

    model_config = ConfigDict(validate_assignment=True)
    tube_window:TubeWindow|None=None
    name:str 
    tube_filters_geant4:list[Filter]|None=[]
    tube_filter_spekpy:list[SpekpyFilter]|None=[]
    tube_type:str|None="reflection"
    target_thickness_um:float|None=0
    
    
    placement:Placement
    current_ma:float|None=None
    voltage_kv:float|None=None
    anode_angle_deg:float|None=None
    anode_symbol:str |None=None
    focal_spot_diameter_mm:float|None
    tube_window_to_virtual_collimator_distance_mm:float
    tube_collimator_radius_mm:float
    tube_window_to_sample_distance_mm:float
    spectrum_file_path:str|None=None
    is_spekpy_tube:bool

    def __init__(self,*,_token=None,**data):
        if _token is None:
            raise ValueError("Create XRayTube using XRayTube.create() or XRayTube.read_spectrum() ")
        
        super().__init__(**data)
    def validate_complete(self):
        
        if self.tube_window is None:
            raise ValueError(
                "Tube window is missing. "
                "Create a TubeWindow and add it to the tube."
            )
        
        
        return self 

    def model_post_init(self, __context):
        """
        Perform additional validation after Pydantic initialization.

        This validates the virtual collimator radius and ensures that
        the selected anode material is supported by SpekPy.

        Raises
        ------
        ValueError
            If the virtual collimator radius is not greater than zero.

        ValueError
            If the selected anode material is not supported by SpekPy.
        """

        if self.is_spekpy_tube:
            spekpy_target_mat = ["Cr", "Cu", "Mo", "Rh", "Ag", "W", "Au"]
            if self.tube_collimator_radius_mm<=0:
                raise ValueError("Virtual tube collimator radius must be greater than 0")
            if self.anode_symbol not in spekpy_target_mat:
                raise ValueError(
                    f"Unsupported SpekPy anode target: '{self.anode_symbol}'. "
                    f"Supported targets are: {', '.join(spekpy_target_mat)}. "
                    "Check the SpekPy documentation/website for the currently supported target materials."
                    )
    @classmethod
    @validate_call

    def create(cls,name:str,current_ma:float,voltage_kv:float,anode_angle_deg:float,anode_symbol:str,focal_spot_diameter_mm:float,tube_collimator_radius_mm:float,
               tube_window_to_virtual_collimator_distance_mm:float,
                tube_placement:TubePlacement):
        
        """
        Create and configure an X-ray tube.

        The tube position is defined relative to the sample using the
        supplied `TubePlacement`. The resulting placement is configured
        so that the X-ray tube faces the sample.

        Parameters
        ----------
        name : str
            Name of the X-ray tube.

        current_ma : float
            Tube current in milliamperes.

        voltage_kv : float
            Tube voltage in kilovolts.

        anode_angle_deg : float
            X-ray tube anode angle in degrees.

        anode_symbol : str
            Chemical symbol of the anode target material.

        focal_spot_diameter_mm : float
            Diameter of the tube focal spot in millimeters.

        tube_collimator_radius_mm : float
            Radius of the virtual tube collimator in millimeters.

        tube_window_to_virtual_collimator_distance_mm : float
            Distance from the tube window to the virtual collimator
            in millimeters.

        tube_placement : TubePlacement
            Tube placement parameters relative to the sample.

        Returns
        -------
        XRayTube
            Configured X-ray tube instance.

        Raises
        ------
        ValueError
            If the configured collimator distance is incompatible with
            the focal-spot-to-sample distance.
        """

        
        placement=Placement.face_sample(distance_mm=tube_placement.focal_spot_to_sample_distance_mm,elevation_deg=tube_placement.elevation_deg,azimuth_deg=tube_placement.azimuth_deg)
        
        if(tube_placement.focal_spot_to_sample_distance_mm<tube_window_to_virtual_collimator_distance_mm):
            raise ValueError("Collimator distance from sample should not be greater than focal spot to sample")
        return cls(
            _token=True,
            name=name,
            current_ma=current_ma,
            voltage_kv=voltage_kv,
            anode_angle_deg=anode_angle_deg,
            anode_symbol=anode_symbol,
            focal_spot_diameter_mm=focal_spot_diameter_mm,
            tube_collimator_radius_mm=tube_collimator_radius_mm,
            tube_window_to_sample_distance_mm=tube_placement.tube_window_to_sample_distance_mm,
            placement=placement,
            tube_window_to_virtual_collimator_distance_mm=tube_window_to_virtual_collimator_distance_mm,
            is_spekpy_tube=True


        )       
    @classmethod
    @validate_call
    def read_spectrum( cls,spectrum_file_path:str|Path,name:str,focal_spot_diameter_mm:float,tube_collimator_radius_mm:float,
               tube_window_to_virtual_collimator_distance_mm:float,tube_placement:TubePlacement): 
        
        """
        Create an X-ray tube source from a user-provided continuous spectrum.

        The spectrum file must contain exactly two columns:

            Column 1: photon energy [keV]
            Column 2: total spectral intensity [photons/s/keV]

        Example:

            3.0    1.25e6
            3.5    1.80e6
            4.0    2.10e6

        The second column represents the total photon-rate density at each
        energy point.

        This format is compatible with the two-column continuous spectrum
        representation used for XMI-MSIM input.
        """
        placement=Placement.face_sample(distance_mm=tube_placement.focal_spot_to_sample_distance_mm,elevation_deg=tube_placement.elevation_deg,azimuth_deg=tube_placement.azimuth_deg)

        return cls(
            _token=True,
            name=name,
            spectrum_file_path=spectrum_file_path,
            focal_spot_diameter_mm=focal_spot_diameter_mm,
            tube_collimator_radius_mm=tube_collimator_radius_mm,
            tube_window_to_virtual_collimator_distance_mm=tube_window_to_virtual_collimator_distance_mm,
            placement=placement,
            tube_window_to_sample_distance_mm=tube_placement.tube_window_to_sample_distance_mm,

            is_spekpy_tube=False
        )
        
        
    @validate_call
    def set_window(self,value:TubeWindow):
        """
        Attach a tube window to the X-ray tube.

        Parameters
        ----------
        value : TubeWindow
            Tube window configuration to assign to the tube.
        """

        self.tube_window=value
    @validate_call
    def add_filter_geant4(self,filter:Filter):
        """
        Add a physical Geant4 filter in front of the X-ray tube window.

        The filter placement must reference `tube_window`, ensuring that
        the filter is positioned relative to the tube window.

        Parameters
        ----------
        filter : Filter
            Geant4 filter to add.

        Raises
        ------
        ValueError
            If the filter was not configured using a placement referenced
            to the tube window.
        """


        if filter.placement.position.reference!="tube_window":
            raise ValueError("tube filter placement must be created using Placement.in_front_of_tube_window")
        self.tube_filters_geant4.append(filter)
    @validate_call
    def add_filter_spekpy(self,value:dict):
        """
        Add a SpekPy filter to the X-ray tube spectrum.

        Parameters
        ----------
        value : dict
            Filter configuration containing:

            - `element`: chemical symbol of the filter material.
            - `thickness_mm`: filter thickness in millimeters.
        """

        obj=SpekpyFilter(element=value["element"],thickness_mm=value["thickness_mm"])
        self.tube_filter_spekpy.append(obj)
        
    
    def to_dict(self):
        return self.model_dump(exclude_none=True)
    
    def __str__(self):
        return f"XrfTube({super().__str__()})"
    
    def _read(self,file_path:str|Path):
        
        file_path=Path(file_path).resolve()
        
        if not  file_path.exists():
            raise ValueError(f"File path does not exit for reading spectrum {file_path}")
        
        if file_path.suffix.lower()==".csv":
            df=pd.read_csv(file_path)
        
        elif file_path.suffix.lower() in [".txt",".dat"]:
            df=pd.read_csv(file_path,sep=None,engine="python",header=None,comment="#")
            
        else:
            raise ValueError("Unsupported file format got"
                             "Excepted .csv,.txt or .dat")
        print(df)
        energy=df.iloc[:,0]
        intensity=df.iloc[:,1]
        
        return energy,intensity,""
            
    
    
