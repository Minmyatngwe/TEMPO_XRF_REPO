#ifndef SIMULATIONCONFIG_HH
#define SIMULATIONCONFIG_HH

#include <string>
#include <vector>
#include "globals.hh"
#include "G4SystemOfUnits.hh"
#include "G4ThreeVector.hh"
#include <utility>
#include "G4Material.hh"
#include <nlohmann/json.hpp>
#include <filesystem>


using json = nlohmann::json;

class MaterialComponent{

    public:
        G4String elementName;
        G4double fraction;
        MaterialComponent(const G4String  &elementName, G4double fraction): elementName(elementName), fraction(fraction){};
};
class ComponentConfig{

    public:
        G4String name;
        G4String shape;
        G4double width=0*mm;
        G4double height=0*mm;
        G4double thickness=0*mm;


        G4double outerRadius=0*mm;
        G4double innerRadius=0*mm;
        G4double apertureRadius=0*mm;
        G4double length=0*mm;
        G4double outerWidth=0*mm;
        G4double outerHeight=0*mm;
        G4double apertureWidth=0*mm;
        G4double apertureHeight=0*mm;


        G4double radius=0*mm; 

        G4String materialType;
        G4String materialName;
        G4double density=0*g/cm3;
        std::vector<MaterialComponent> material;

        G4double distanceFromSample=0*mm;
        
        G4double elevationAngle=0*deg;
        G4double azimuthAngle=0*deg;

        G4String orientationType;
        G4double xRotation=0*deg;
        G4double yRotation=0*deg;
        G4double zRotation=0*deg; 

};


struct detectorShieldConfig
{
    G4int index = 0;

    G4String materialType;
    G4String materialName;

    G4double density = 0.0 * g / cm3;

    std::vector<MaterialComponent> materialComposition;

    G4double gapBetween = 0.0 * mm;
    G4double thickness = 0.0 * mm;
};

class SimulationConfig{


    public:

        //xray tube and tube filters
        G4double focalspotdiameter = 0.0 * mm;

        G4bool isTubeFilterUse;
        G4String tubeFilterEngine;

        std::vector<ComponentConfig>tubeFilters;
        G4double sampleToFocalSpot=0*mm;

        G4String xrayTubeInternalMedium="G4_Glactic";

        G4ThreeVector sourcePosition;

        G4String xrayTubeBeWindowMat="G4_Be";
        G4double xrayTubeWindowThickness=0.01*mm;





        //sample
        G4String sampleMaterialShape;
        G4double sampleWidth=0*mm;
        G4double sampleHeight=0*mm;
        G4double sampleThickness=0*mm;
        G4double sampleInnerRadius=0*mm;
        G4double sampleOuterRadius=0*mm;
        G4double sampleRadius=0*mm;


        G4String sampleMaterialType;
        G4String sampleMaterialName;
        G4double sampleMaterialDensity = 0.0*g/cm3;
        std::vector<MaterialComponent> sampleMaterialComponents;
        G4Material* sampleMat{nullptr};


        G4double sampleRotationX=0*deg;
        G4double sampleRotationY=0*deg;
        G4double sampleRotationZ=0*deg;

        //source collimator
        G4double sampleToTubeExitDistance=0*mm;
        G4double sourceIncidentAzimuthDeg=0*deg; 
        G4double sourceElevationDeg=0*deg ;
        G4double sampleToTubeCollimatorDistance=0*mm;
        G4double sourceCollimatorRadius=0*mm;
        G4double sampleBeamDiameter = 0.0 * mm;

        //detector active volumne
        G4String detectorActiveVolumeShape;
        G4double detectorWidth;
        G4double detectorHeight;
        G4double detectorThickness;
        G4double detectorInnerRadius;
        G4double detectorOuterRadius;
        G4double detectorRadius;

        G4String detectorMaterialType;
        G4String detectorMaterialName;
        G4double detectorDensity;
        std::vector<MaterialComponent> detectorMaterialComposition;

        G4double detectorDistanceFromSample=0*mm;
        G4double detectorelevationAngle=0*deg;
        G4double detectorazimuthAngle=0*deg;
        G4String detectorOrientationType;

        G4double detectorXRotation=0*deg;
        G4double detectorYRotation=0*deg;
        G4double detectorZRotation=0*deg;


        //detector apeture
        G4bool isDetectorApertureUse;

        //detector collimator 

        G4bool isDetectorCollimatorUse=false;

        std::vector<ComponentConfig> detectorCollimators;


        //detector internal mask
        G4bool isDetectorInternalMaskUse=false;
        std::vector<ComponentConfig> detectorInternalMasks;


        //detector filter 
        G4bool isDetectorFilterUse;
        std::vector<ComponentConfig>detectorFilters;

        //detector housing
        G4bool isDetectorHousingUse = false;

        G4String detectorHousingShape = "Rectangular housing";

        G4double detectorHousingSideGap = 0.0 * mm;
        G4double detectorHousingFrontGap = 0.0 * mm;
        G4double detectorHousingBackGap = 0.0 * mm;
        G4double detectorHousingWallThickness = 0.0 * mm;

        G4String detectorHousingApertureShape;

        G4double detectorHousingApertureRadius = 0.0 * mm;
        G4double detectorHousingApertureWidth = 0.0 * mm;
        G4double detectorHousingApertureHeight = 0.0 * mm;


        // Housing material
        G4String detectorHousingMaterialType;
        G4String detectorHousingMaterialName;
        G4double detectorHousingDensity = 0.0 * g / cm3;

        std::vector<MaterialComponent>
            detectorHousingMaterialComposition;


        // Internal cavity
        G4String detectorHousingCavityMaterialName;
        G4String detectorHousingCavityMaterialType;
        G4String detectorHousingCavityInternalMaterialName="G4_Galactic";
        G4double detectorHousingCavityDensity=0.0*g/cm3;
        std::vector<MaterialComponent>detectorHousingCavityMaterialComposition;
        G4double detectorHousingCavityWallThickness=0*mm;




        // Entrance window
        G4String detectorHousingWindowMaterialType;
        G4String detectorHousingWindowMaterialName;
        G4double detectorHousingWindowDensity =0.0 * g / cm3;

        std::vector<MaterialComponent>
            detectorHousingWindowComposition;

        G4double detectorHousingWindowThickness = 0.0 * mm;

        //extra
        G4String worldMaterial = "G4_AIR";
        G4ThreeVector worldLength;

        G4String outputFileName = "output.root";

        G4double numberOfSecondarySplitting=0;
        G4ThreeVector sampleReferencePoint=G4ThreeVector(0,0,0);


        //physics
        G4bool isFluorescenceUse=true;
        G4bool isAugerUse=false;
        G4bool isPixeUse=false;
        G4bool isIgnoreCutUse=true;

        G4bool isSecondarySplittingUse=true;
        G4double photoelectricFactor=100;
        G4double comptFactor=100;
        G4double rayleighFactor=100;
        G4double maximumEnergy=1000*keV;

        G4bool isInteractionBiasingUse=true;

        G4double gammaCut=0.001*mm;
        G4double electronCut=0.01*mm;
        G4double positronCut=0.01*mm;
        G4double protonCut=0.01*mm;
        G4String fluDatasetName="ANSTO";
        std::filesystem::path parentFilePath;

        G4bool debug=false;

    
    
        void LoadFromJson(
        const nlohmann::json& jsonConfig
        );
        void Print() const;

        void ParseComponentConfig(
            const nlohmann::json& componentJson,
            std::vector<ComponentConfig>& componentVector,
            G4String componentType="COMPONENT"
        );

        

};      

#endif