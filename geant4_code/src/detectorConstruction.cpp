#include "detectorConstruction.hh"
#include "geometryExporter.hh"
#include "buildinghelper.hh"
#include "G4Region.hh"
#include "sensitiveDetector.hh"
#include "G4BOptrForceCollision.hh"
#include "G4VisAttributes.hh"
#include "G4Colour.hh"
using namespace BuildHelper;

DetectorConstruction::DetectorConstruction(SimulationConfig& config,nlohmann::json & jsonConfig,std::string updateJsonPath):fConfig(&config),fJsonConfig{&jsonConfig},fupdateJsonPath{updateJsonPath}{}



DetectorConstruction::~DetectorConstruction() {

};
G4VPhysicalVolume * DetectorConstruction::Construct () {
    G4int physplacementIndex=0;
    fConfig->sampleReferencePoint=G4ThreeVector(0,0,0);
    G4ThreeVector samplePosition;

    //world

    auto *nist=G4NistManager::Instance();
    auto *worldMat=BuildMaterial(fConfig->worldMaterial);


    auto *worldSolid=new G4Box("worldSolid",fConfig->worldXSize/2,
                                fConfig->worldYSize/2,
                                fConfig->worldZSize/2
                                );

    auto *worldLogic=new G4LogicalVolume(worldSolid,worldMat,"worldLogic");
    worldLogic->SetVisAttributes(G4VisAttributes::GetInvisible());

    auto *worldPhys=new G4PVPlacement(nullptr,G4ThreeVector(),worldLogic,"worldPhys",nullptr,false,physplacementIndex++,true);

    //sample

    fSampleLogic=BuildGeometry(fConfig->sampleConfig);
    samplePosition=G4ThreeVector(0,0,-fConfig->sampleConfig.thickness/2);
    G4cout<<"Sample position"<<samplePosition<<G4endl;
    auto *sampleRegion=new G4Region("SampleRegion");
    sampleRegion->AddRootLogicalVolume(fSampleLogic);

    new G4PVPlacement(
        nullptr,                                
        samplePosition,               
        fSampleLogic,                        
        fConfig->sampleConfig.name + "_placement",
        worldLogic,                        
        physplacementIndex++,
        true
    );


    G4double distanceFromTubeToCollimator=fConfig->tubeWindowToSampleDistance-fConfig->tubeWindowToVirtualCollimator;
    if (distanceFromTubeToCollimator <= 0)
    {
        G4String errorMsg =
            "Invalid virtual collimator position. "
            "Calculated distance from the X-ray source to the virtual collimator is "
            + std::to_string(distanceFromTubeToCollimator / mm)
            + " mm. Check 'tube_window_to_sample_distance_mm' and "
            "'tube_window_to_virtual_collimator_distance_mm'. "
            "The resulting source-to-collimator distance must be greater than 0 mm.";

        G4Exception(
            "PrimaryGenerator::PrimaryGenerator",
            "InvalidTubeCollimatorDistance",
            FatalException,
            errorMsg.c_str()
        );
    }
    fConfig->virtualTubeCollimatorPosition=CalculatePositionFromSphericalCoordinates(distanceFromTubeToCollimator,fConfig->tubeConfig.azimuthAngle,fConfig->tubeConfig.elevationAngle);
    
    //detector 
    auto& detectorConfig=fConfig->detectorConfig;

    fDetectorLogic=BuildGeometry(detectorConfig);

    auto [detectorPosition, detectorRotation]=BuildPlacement(detectorConfig,*fConfig);

    detectorConfig.position = detectorPosition;
    detectorConfig.rotation = detectorRotation;
    //housing
    G4LogicalVolume * cavitylogic{nullptr};
    if(fConfig->isHousingUse){
        BuildHousing(*fConfig,fDetectorLogic,cavitylogic,worldLogic,physplacementIndex);

    }
    else{
        new G4PVPlacement(
            detectorConfig.rotation.rotMatrix,
            detectorConfig.position,
            fDetectorLogic,
            detectorConfig.name+"_placement",
            worldLogic,             
            false,           
            physplacementIndex++,
            true

        );

    }
    //internal mask 
    if(fConfig->isHousingUse && cavitylogic!=nullptr){


            for (auto& mask : fConfig->detectorInternalMaskConfig)
            {
                auto* maskLogic = BuildGeometry(mask);

                const G4double detectorHalfThickness =
                    GetComponentAxialThickness(fConfig->detectorConfig) / 2.0;

                const G4double maskHalfThickness =
                    GetComponentAxialThickness(mask) / 2.0;

                const G4double localZ =
                    detectorHalfThickness
                    + mask.distanceFromReferenceSurface
                    + maskHalfThickness;

                G4ThreeVector localPosition(
                    0.0,
                    0.0,
                    localZ
                );

                new G4PVPlacement(
                    nullptr,                    // same local orientation as detector
                    localPosition,
                    maskLogic,
                    mask.name + "_placement",
                    cavitylogic,
                    false,
                    physplacementIndex++,
                    true
                );
            }
    }

    //xray tube 
    G4double tubeLength=fConfig->tubeConfig.distance-fConfig->tubeWindowToSampleDistance-fConfig->tubeWindowConfig.thickness;

    if(tubeLength<=0){
            G4ExceptionDescription msg;

            msg << "Invalid X-ray tube geometry.\n"
                << "Calculated tube length must be greater than zero.\n"
                << "tubeConfig.distance = "
                << fConfig->tubeConfig.distance / mm << " mm\n"
                << "tubeWindowToSampleDistance = "
                << fConfig->tubeWindowToSampleDistance / mm << " mm\n"
                << "Calculated tubeLength = "
                << tubeLength / mm << " mm";

            G4Exception(
                "DetectorConstruction::Construct",
                "InvalidTubeLength",
                FatalException,
                msg
            );

    }

    auto * xrayTubeSolid=new G4Tubs(fConfig->tubeConfig.name,
                                    0.0,
                                    fConfig->tubeCollimatorRadius+0.1*mm,
                                    tubeLength,
                                    0*deg ,
                                    360*deg);

    auto * tubeMat=nist->FindOrBuildMaterial("G4_Galactic");
    auto * xrayTubeLogic=new G4LogicalVolume(xrayTubeSolid,tubeMat,fConfig->tubeConfig.name+"_logic");


    auto [sourcePosition,sourceRotation]=BuildPlacement(fConfig->tubeConfig,*fConfig);
    fConfig->sourcePosition=sourcePosition;


    new G4PVPlacement(
        sourceRotation.rotMatrix,
        sourcePosition,
        xrayTubeLogic,
        fConfig->tubeConfig.name+"_placement",
        worldLogic,
        false,
        physplacementIndex++,
        true

    );

    //xray tube window
    auto& tubeWindowConfig = fConfig->tubeWindowConfig;
    tubeWindowConfig.shape = "circular";
    tubeWindowConfig.distance =fConfig->tubeWindowToSampleDistance+ tubeWindowConfig.thickness / 2.0;

    tubeWindowConfig.azimuthAngle =fConfig->tubeConfig.azimuthAngle;

    tubeWindowConfig.elevationAngle =fConfig->tubeConfig.elevationAngle;

    tubeWindowConfig.position =
        CalculatePositionFromSphericalCoordinates(
            tubeWindowConfig.distance,
            tubeWindowConfig.azimuthAngle,
            tubeWindowConfig.elevationAngle
        );

    // Same axis/orientation as tube
    tubeWindowConfig.rotation =fConfig->tubeConfig.rotation;
    auto * tubeWindowMat=BuildMaterial(tubeWindowConfig.material);
    auto *tubeWindowSolid=new G4Tubs(tubeWindowConfig.name+"_solid",
                                    0,
                                    fConfig->tubeCollimatorRadius+0.01*mm,
                                    tubeWindowConfig.thickness/2,
                                    0*deg,
                                    360*deg);
    auto * tubeWindowLogic=new G4LogicalVolume(tubeWindowSolid,tubeWindowMat,fConfig->tubeWindowConfig.name+"_logic");

    G4VisAttributes vis(G4Colour(0,1,0,1));
    vis.SetForceSolid(true);
    tubeWindowLogic->SetVisAttributes(vis);



    new G4PVPlacement(
        tubeWindowConfig.rotation.rotMatrix,
        tubeWindowConfig.position,
        tubeWindowLogic,
        tubeWindowConfig.name+"_placement",
        worldLogic,
        false,
        physplacementIndex++,
        true
    );

    // //tube filter
    for( auto & component:fConfig->tubeFilterComponents){
        BuildComponent(component,*fConfig,worldLogic,physplacementIndex,&tubeWindowConfig);
    }

    //detector filter

    for(auto & component:fConfig->detectorFilterConfig){
        BuildComponent(component,*fConfig,worldLogic,physplacementIndex,&detectorConfig);

    }
    //detector collimator
    for(auto& collimator:fConfig->detectorCollimatorConfig){
        BuildComponent(collimator,*fConfig,worldLogic,physplacementIndex,&detectorConfig);


    }


    if(fConfig->isSecondarySplittingUse){
        G4cout<<"Directional splitting is enabled"<<G4endl;
        G4cout<<"Geant4 detector position"<<detectorPosition<<G4endl;

        G4double targetRadius=0;


        if(fConfig->isHousingUse){
            auto & housingConfig=fConfig->housingConfig;

            targetRadius=std::sqrt(
                housingConfig.width/2*housingConfig.width/2+
                housingConfig.height/2*housingConfig.height/2+
                housingConfig.thickness/2*housingConfig.thickness/2
            );
        }
        else{
            if (detectorConfig.shape=="rectangular"){
                targetRadius=std::sqrt(
                    detectorConfig.width/2*detectorConfig.width/2+
                    detectorConfig.height/2*detectorConfig.height/2+
                    detectorConfig.thickness/2*detectorConfig.thickness/2
                    
                );
            }
            else if(detectorConfig.shape=="circular"){
                targetRadius=std::sqrt(
                    detectorConfig.radius*detectorConfig.radius+detectorConfig.thickness/2*detectorConfig.thickness/2
                );
            }
            else {
                G4ExceptionDescription msg;

                msg << "Cannot calculate directional-splitting target radius. "
                    << "Unsupported detector geometry shape: '"
                    << detectorConfig.shape
                    << "'. Supported detector shapes are 'rectangular' and 'circular'.";

                G4Exception(
                    "DetectorConstruction::Construct()",
                    "XRF.GEOM.001",
                    FatalException,
                    msg
                );
            }
        }
        auto* parameters = G4EmParameters::Instance();

        parameters->SetDirectionalSplitting(true);
        parameters->SetDirectionalSplittingTarget(detectorPosition);
        parameters->SetDirectionalSplittingRadius(targetRadius);
        G4cout<<"Target radius"<<targetRadius<<G4endl;


    }

    ExportGeometryForBrowser(
        worldPhys,
        "../../roboaixrf/vis/public/xrf_geometry_vis.json",
        48
    );
    return worldPhys;
};



void DetectorConstruction::ConstructSDandField() {
    auto *sd=new SensitiveDetector();
    G4SDManager::GetSDMpointer()->AddNewDetector(sd);
    fDetectorLogic->SetSensitiveDetector(sd);

    if(fConfig->isInteractionBiasingUse){

        auto * forceCollision=new G4BOptrForceCollision("gamma","ForceGammaCollisionInSample");
        forceCollision->AttachTo(
            fSampleLogic
        );
    }


}

