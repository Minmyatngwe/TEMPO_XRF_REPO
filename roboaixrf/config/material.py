from pydantic import BaseModel,model_validator,ValidationInfo

class Composition(BaseModel):
    element:str 
    mass_fraction:float 


class Material(BaseModel):
    material_type:str 
    material_name:str 
    
    density_g_cm3: float | None = None
    compositions: list[Composition] | None = None
    
    
    
    @model_validator(mode="before")
    @classmethod
    def  only_allowed_factory(cls,data,info:ValidationInfo):
        
        if not info.context or not info.context.get("factory"):
            raise ValueError(
                "Create Material using Geometry.geant4(), "
                "Geometry.custom_mat(), etc."
            )
        return data


    
    @classmethod
    def geant4(cls,material_name:str):
        return cls.model_validate(
            {
                "material_type":"geant4",
                "material_name":material_name
            },
            context={"factory":True}
        )
    @classmethod
    def custom_mat(cls,density_g_cm3:float,compositions:list[Composition],material_name):
        
        obj= cls.model_validate(
            {
                "material_type":"custom",
                "material_name":material_name,
                "density_g_cm3":density_g_cm3,
                "compositions":compositions
                
            },
            context={"factory":True}
        )
        obj.check_composition()
        
        return obj 
    
    def check_composition(self):
        
        total=sum([i.mass_fraction for i in self.compositions])
        
        if total != 1.0:
            raise ValueError(
                f"Mass fractions must add up to 1.0, got {total}"
            )

    def __str__(self):
        text = (
            f"Material\n"
            f"  Type    : {self.material_type}\n"
            f"  Name    : {self.material_name}\n"
        )

        if self.compositions is not None:
            text += f"  Density : {self.density_g_cm3} g/cm³\n"
            text += "  Composition:\n"

            for item in self.compositions:
                text += (
                    f"    {item.element}: "
                    f"{item.mass_fraction}\n"
                )

        return text
    
    def to_dict(self):
        return self.model_dump(
            exclude_none=True
        )