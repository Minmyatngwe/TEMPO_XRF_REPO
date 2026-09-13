from pydantic import BaseModel, model_validator, ValidationInfo


class Position(BaseModel):
    """
    Defines the position of a component relative to a reference object.

    Parameters
    ----------
    reference : str
        Name of the reference object used for positioning.

    distance_mm : float
        Distance from the reference object in millimeters.

    elevation_deg : float | None
        Elevation angle in degrees.

    azimuth_deg : float | None
        Azimuth angle in degrees.
    """

    reference: str
    distance_mm: float
    elevation_deg: float | None = None
    azimuth_deg: float | None = None


class Orientation(BaseModel):
    """
    Defines the orientation of a component.

    Parameters
    ----------
    mode : str
        Orientation mode.

        Examples include:
        - ``face_sample``
        - ``manual``
        - ``inherient``

    x : float | None
        X component of a manually specified orientation vector.

    y : float | None
        Y component of a manually specified orientation vector.

    z : float | None
        Z component of a manually specified orientation vector.
    """

    mode: str
    x: float = None
    y: float = None
    z: float = None


class Placement(BaseModel):
    """
    Defines the position and orientation of a simulation component.

    Placement objects cannot be created directly. They must be created
    using one of the provided factory methods so that valid reference
    and orientation settings are used.

    Available factory methods
    -------------------------
    face_sample()
        Place a component relative to the sample and orient it so that
        it faces the sample.

    manual()
        Place a component relative to the sample and manually specify
        its orientation vector.

    in_front_detector()
        Place a component in front of the detector and inherit the
        detector orientation.

    in_front_of_tube_window()
        Place a component in front of the X-ray tube window and inherit
        the tube-window orientation.
    """


    position: Position
    orientation: Orientation | None = None

    @model_validator(mode="before")
    @classmethod
    def only_allowed_factory(
        cls,
        data,
        info: ValidationInfo
    ):
        if not info.context or not info.context.get("factory"):
            raise ValueError(
                "Create Placement using "
                "Placement.face_sample(), "
                "Placement.manual(), or "
                "Placement.in_front_detector() or"
                "Placement.in_front_of_tube_window()"
            )

        return data

    @classmethod
    def face_sample(
        cls,
        distance_mm: float,
        elevation_deg: float,
        azimuth_deg: float,
    ):
        return cls.model_validate(
            {   
                "position": Position(
                    reference="sample",
                    distance_mm=distance_mm,
                    elevation_deg=elevation_deg,
                    azimuth_deg=azimuth_deg,
                ),
                "orientation": Orientation(
                    mode="face_sample"
                ),
            },
            context={"factory": True},
        )

    @classmethod
    def manual(
        cls,
        distance_mm: float,
        elevation_deg: float,
        azimuth_deg: float,
        x: float,
        y: float,
        z: float,
    ):
        return cls.model_validate(
            {
                "position": Position(
                    reference="sample",
                    distance_mm=distance_mm,
                    elevation_deg=elevation_deg,
                    azimuth_deg=azimuth_deg,
                ),
                "orientation": Orientation(
                    mode="manual",
                    x=x,
                    y=y,
                    z=z,
                ),
            },
            context={"factory": True},
        )
        
    @classmethod
    def in_front_detector(cls,distance_mm:float):
        
        return cls.model_validate(
            {
                "position":Position(
                    reference="detector",
                    distance_mm=distance_mm
                ),
                "orientation":Orientation(
                    mode="inherient"
                )
            },
            context={"factory":True}
        )
    
    @classmethod
    def in_front_of_tube_window(cls,distance_mm:float):
        return cls.model_validate(
            {
                "position":Position(
                    reference="tube_window",
                    distance_mm=distance_mm
                    
                ),
                "Orientation":Orientation(
                    mode="inherient"
                )
            },
            context={"factory":True}
        )
