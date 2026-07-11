#ifndef SIMULATIONCONFIG_HH
#define SIMULATIONCONFIG_HH

#include <string>
#include <vector>
#include "globals.hh"
#include "G4SystemOfUnits.hh"
#include "G4ThreeVector.hh"
#include <utility>
#include "G4Material.hh"

class MaterialComponent{

    public:
        G4String elementName;
        G4double fraction;
        MaterialComponent(const std::string &elementName, G4double fraction): elementName(elementName), fraction(fraction){};
};

class ShieldLayerConfig{
    public:
        G4String materialName;
        G4double thickness;
        ShieldLayerConfig(const std::string &materialName, G4double thickness): materialName(materialName), thickness(thickness){};
        
};


class ShieldConfig{
    public:
        G4bool enable;
        G4double detectorAndFirstLayerGap;
        std::vector<ShieldLayerConfig> layers;

        ShieldConfig(): enable(false), detectorAndFirstLayerGap(0.0){};
};

class SimulationConfig{


    public:
        G4String sampleMaterial;

        G4bool sampleMaterialIsCustom = false;

        G4double sampleMaterialDensity = 0.0*g/cm3;

        std::vector<MaterialComponent> sampleMaterialComponents;

        G4ThreeVector sampleMaterialSize = G4ThreeVector(0,0,0);

        G4double incidentAngle = 0.0*deg;

        G4double sourceDistance = 0.0 * mm;

        G4double detectorDistance = 0.0 * mm;

        G4double takeoffAngle = 0.0*deg;

        G4double sampleToCollimatorDistance  = 0.0 * mm;

        G4double sourceCollimatoryDiameter = 0.0 * mm;

        G4double detectorCollimatoryDiameter = 0.0 * mm;

        G4double detectorBewindowThickness = 0.0 * mm;

        G4double detectorArea = 0.0 * mm * mm;

        G4double focalspotdiameter = 0.0 * mm;

        G4double detectorthickness = 0.0 * mm;

        long long totalEvents = 0;

        G4String worldMaterial = "G4_Galactic";
        G4double explambda = 0.0;
        ShieldConfig shieldConfig;
        G4String outputFileName = "output.root";

        std::vector<std::pair<G4String,G4double>> sampleComposion;

        G4Material* sampleMat{nullptr};
        G4double sampleBeamdiameter = 0.0 * mm;


        //detector collimator configuration

        G4String detectorCollimatorMaterial = "G4_Pb";
        G4bool detectorCollimatorIsCustom = false;
        G4bool detectorCollimatorIsEnabled = false;
        G4double sampleToDetectorCollimatorDistance = 0.0 * mm;
        G4double detectorCollimatorAnlgeFromSample = 0.0 * deg;

        //std::vector<std::pair<G4String,G4double>> detectorCollimatorComposition;
        G4double detectorCollimatorDensity = 0.0 * g/cm3;
        G4double detectorCollimatorThickness = 0.0 * mm;
        G4double detectorCollimatorOuterRadius = 0.0 * mm;
        G4double detectorCollimatorInnerRadius = 0.0 * mm;


};      

#endif