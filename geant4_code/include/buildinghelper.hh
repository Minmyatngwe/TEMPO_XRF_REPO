#ifndef BUILDINGHELPER_HH
#define BUILDINGHELPER_HH
#include <nlohmann/json.hpp>
#include "G4LogicalVolume.hh"
#include "parseHelper.hh"
#include <iostream>
#include <utility>
#include "simulationConfig.hh"
#include "G4PVPlacement.hh"
#include "G4EmParameters.hh"

using namespace ParseHelper;
namespace BuildHelper{

    G4LogicalVolume * BuildGeometry( ComponentConfig & component);

    G4Material * BuildMaterial(const MaterialConfig & matConfig);

    std::pair<G4ThreeVector,ComponentRotation>  BuildPlacement( ComponentConfig & component,const SimulationConfig & config,ComponentConfig* parentComponent = nullptr);
    G4PVPlacement* BuildComponent(
        ComponentConfig& component,
        SimulationConfig& config,
        G4LogicalVolume* mother,
        int& counter,
        ComponentConfig* parentComponent = nullptr);
    G4ThreeVector CalculatePositionFromSphericalCoordinates(G4double distance, G4double azimuthalAngle, G4double elevationAngle);
    ComponentRotation CalculateRotation(G4String orientationType,    const G4ThreeVector & componentPosition,const G4ThreeVector & samplePosition,G4double xRotation=0,G4double yRotation=0,G4double zRotation=0);
    G4double GetComponentAxialThickness(const ComponentConfig & component);

    void BuildHousing(
        SimulationConfig& fConfig,
        G4LogicalVolume* detectorLogicalVolume,
        G4LogicalVolume*& cavityLogic,
        G4LogicalVolume* worldLogic,
        G4int& physplacementIndex
    );
};
#endif