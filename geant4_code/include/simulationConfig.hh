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
#include "parseHelper.hh"

using namespace ParseHelper;

class SimulationConfig{


    public: 
    
    //world 
    MaterialConfig worldMaterial;
    G4double worldXSize=0*mm;
    G4double worldYSize=0*mm;
    G4double worldZSize=0*mm;

    //xray tube

    ComponentConfig tubeConfig;
    G4double focalSpotDiameter=0*mm;
    G4double tubeWindowToSampleDistance=0*mm; 
    G4double tubeCollimatorRadius=0*mm;
    G4double tubeWindowToVirtualCollimator=0*mm;
    G4double virtualTubeCollimatorArea;
    //window 

    ComponentConfig tubeWindowConfig;
    //filter
    std::vector<ComponentConfig> tubeFilterComponents;
    //sample
    ComponentConfig sampleConfig;
    //detector
    ComponentConfig detectorConfig;
    
    std::vector<ComponentConfig> detectorFilterConfig;
    std::vector<ComponentConfig> detectorCollimatorConfig;
    std::vector<ComponentConfig> detectorInternalMaskConfig;

    //housing 
    G4bool isHousingUse=false;
    ComponentConfig housingConfig;
    //housingwindow 
    ComponentConfig detectorWindowConfig;
    
    //physics
    G4bool isInteractionBiasingUse=true;
    G4bool isFluorescenceUse=true ;
    G4bool isAugerUse=false; 
    G4bool isPixeUse=false;
    G4bool isIgnoreCutUse=true ;
    G4String fluDatasetName;
    G4bool isSecondarySplittingUse=true; 
    G4double maximumEnergy=1000;
    G4int photoelectricFactor=100;
    G4int comptFactor=100;
    G4int rayleighFactor=100;

    G4double gammaCut=0.01;
    G4double electronCut=0.01;
    G4double positronCut=0.01;
    G4double protonCut=0.01;

    //other
    G4ThreeVector sourcePosition;
    G4ThreeVector virtualTubeCollimatorPosition;
    G4ThreeVector sampleReferencePoint;

    //file parent path
    G4String parentFilePath;




    //function

    void LoadFromJson(const nlohmann::json &jsonConfig);


    void ParseFilterConfig(const nlohmann::json & filterConfig,std::vector<ComponentConfig> &filterComponents);
    void printComponentConfig(const ComponentConfig &componentConfig); 

    void parseComponentConfig(const nlohmann::json & componentConfigJson,ComponentConfig & componentConfig,G4bool isInternalMask=false);

    void parsePhysicsConfig(const nlohmann::json & physicsConfigJson);

    void parseHousingConfig(const nlohmann::json & detectorJson,ComponentConfig & housingConfig);
    void Print();
};
#endif  