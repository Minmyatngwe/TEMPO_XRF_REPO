from pydantic import BaseModel,model_validator,ValidationInfo

class Geometry(BaseModel):
    #common 
    shape:str
    
    @model_validator(mode="before")
    @classmethod
    def  only_allowed_factory(cls,data,info:ValidationInfo):
        
        if not info.context or not info.context.get("factory"):
            raise ValueError(
                "Create Geometry using Geometry.circular(), "
                "Geometry.rectangular(), etc."
            )
        return data

    
    thickness_mm:float|None=None

    # Circular / cylindrical geometry
    
    inner_radius_mm:float|None=None
    outer_radius_mm:float|None=None
    radius_mm:float|None=None
    
    @classmethod
    def circular(cls,radius_mm:float,thickness_mm:float):
        
        return cls.model_validate(
            {
                "shape":"Circular",
                "radius_mm":radius_mm,
                "thickness_mm":thickness_mm
                
                
            },
            context={"factory":True}
        )
    
    #Rectangular geometry
    width_mm:float|None=None
    height_mm:float|None=None
    
    @classmethod
    def rectangular(cls,width_mm:float,height_mm:float,thickness_mm:float):
        
        return cls.model_validate(
            {
                "shape":"Rectangular",
                "width_mm":width_mm,
                "height_mm":height_mm,
                "thickness_mm":thickness_mm
            },
            context={"factory":True}
        )
    

    
    #Aperture information
    aperture_shape: str | None = None    

    aperture_radius_mm:float|None=None
    aperture_width_mm:float|None=None
    aperture_height_mm:float|None=None
    
    
    #Rectangular collimator outer dimensions
    outer_width_mm:float|None=None
    outer_height_mm:float|None=None
    length_mm:float|None=None
    @classmethod
    def rectangular_aperture(cls,aperture_width_mm:float,aperture_height_mm:float,
                                          outer_width_mm:float,outer_height_mm:float,
                                          length_mm:float):
        
        if aperture_height_mm>=outer_height_mm or aperture_width_mm>=outer_width_mm:
            measure="height" if aperture_height_mm>=outer_height_mm else "width"
            raise   ValueError(f"Aperture {measure} canot be greater than or equal outer {measure} ")
        return cls.model_validate(
            {    "shape": "Rectangular aperture",
                "aperture_shape":"Rectangular",
                "aperture_width_mm":aperture_width_mm,
                "aperture_height_mm":aperture_height_mm,
                "outer_width_mm":outer_width_mm,
                "outer_height_mm":outer_height_mm,
                "length_mm":length_mm
            },
            context={"factory":True}
        )
        
    @classmethod
    def circular_aperture(cls,aperture_radius_mm:float,outer_radius_mm:float,length_mm:float):
        
        if aperture_radius_mm>=outer_radius_mm:
            raise ValueError(f"Aperture radius cannot be greater than equal outer radius of aperture")
        return cls.model_validate(
            {
                "shape": "Circular aperture",

                "aperture_shape":"Circular",
                "aperture_radius_mm":aperture_radius_mm,
                "outer_radius_mm":outer_radius_mm,
                "length_mm":length_mm
            },
            context={"factory":True}
        )

    # Detector housing gaps and wall
    detector_clearance_mm:float|None=None
    housing_wall_thickness_mm:float|None=None
    cavity_wall_thickness_mm:float|None=None
    
    @classmethod
    def detector_housing_circular_aperture(
        cls,
        aperture_radius_mm:float,
        detector_clearance_mm:float,
        housing_wall_thickness_mm:float,
        cavity_wall_thickness_mm:float
    ):
        return cls.model_validate(
            
            {   
                "shape": "Detector housing",
                "aperture_shape":"Circular",
                "aperture_radius_mm":aperture_radius_mm,
                "detector_clearance_mm":detector_clearance_mm,
                "housing_wall_thickness_mm":housing_wall_thickness_mm,
                "cavity_wall_thickness_mm":cavity_wall_thickness_mm
                
            },
            context={"factory":True}
        )
        
    @classmethod
    def detector_housing_rectangular_aperture(
        cls,
        aperture_width_mm: float,
        aperture_height_mm: float,
        detector_clearance_mm:float,
        housing_wall_thickness_mm: float,
        cavity_wall_thickness_mm:float
    ):
        return cls.model_validate(
            {
    
                "shape": "Detector housing",
                "aperture_shape": "Rectangular",
                "aperture_width_mm": aperture_width_mm,
                "aperture_height_mm": aperture_height_mm,
                "detector_clearance_mm":detector_clearance_mm,
                "housing_wall_thickness_mm":housing_wall_thickness_mm,

                "cavity_wall_thickness_mm":cavity_wall_thickness_mm
            },
            context={"factory": True},
        )
    def __str__(self):

        shape = self.shape.lower()

        # Rectangular normal geometry
        if shape == "rectangular":
            return (
                f"Geometry("
                f"shape=Rectangular, "
                f"width_mm={self.width_mm}, "
                f"height_mm={self.height_mm}, "
                f"thickness_mm={self.thickness_mm}"
                f")"
            )

        # Circular normal geometry
        elif shape == "circular":
            return (
                f"Geometry("
                f"shape=Circular, "
                f"radius_mm={self.outer_radius_mm}, "
                f"thickness_mm={self.thickness_mm}"
                f")"
            )

        # Circular aperture
        elif shape == "circular aperture":
            return (
                f"Geometry("
                f"shape=Circular aperture, "
                f"aperture_radius_mm={self.aperture_radius_mm}, "
                f"outer_radius_mm={self.outer_radius_mm}, "
                f"length_mm={self.length_mm}"
                f")"
            )

        # Rectangular aperture
        elif shape == "rectangular aperture":
            return (
                f"Geometry("
                f"shape=Rectangular aperture, "
                f"aperture_width_mm={self.aperture_width_mm}, "
                f"aperture_height_mm={self.aperture_height_mm}, "
                f"outer_width_mm={self.outer_width_mm}, "
                f"outer_height_mm={self.outer_height_mm}, "
                f"length_mm={self.length_mm}"
                f")"
            )

        # Detector housing
        elif shape == "detector housing":

            if self.aperture_shape == "Circular":
                return (
                    f"Geometry("
                    f"shape=Detector housing, "
                    f"aperture_shape=Circular, "
                    f"aperture_radius_mm={self.aperture_radius_mm}, "
                    f"side_gap_mm={self.side_gap_mm}, "
                    f"front_gap_mm={self.front_gap_mm}, "
                    f"back_gap_mm={self.back_gap_mm}, "
                    f"wall_thickness_mm={self.wall_thickness_mm}"
                    f"cavity_wall_thickness_mm={self.cavity_wall_thickness_mm}"

                    f")"
                )

            elif self.aperture_shape == "Rectangular":
                return (
                    f"Geometry("
                    f"shape=Detector housing, "
                    f"aperture_shape=Rectangular, "
                    f"aperture_width_mm={self.aperture_width_mm}, "
                    f"aperture_height_mm={self.aperture_height_mm}, "
                    f"side_gap_mm={self.side_gap_mm}, "
                    f"front_gap_mm={self.front_gap_mm}, "
                    f"back_gap_mm={self.back_gap_mm}, "
                    f"wall_thickness_mm={self.wall_thickness_mm}"
                    f"cavity_wall_thickness_mm={self.cavity_wall_thickness_mm}"
                    f")"
                )

        return f"Geometry(shape={self.shape})"
    
    
    
    
    def to_dict(self):
        
        return self.model_dump(
            exclude_none=True
        )
    