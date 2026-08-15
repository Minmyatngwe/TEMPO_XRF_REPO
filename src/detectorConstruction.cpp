#include "detectorConstruction.hh"
#include "G4RotationMatrix.hh"
#include "G4Region.hh"
#include "sensitiveDetector.hh"
#include "G4BOptrForceCollision.hh"
#include "G4LogicalVolumeStore.hh"
#include "G4ProductionCuts.hh"
#include "G4Tubs.hh"
#include "G4EmParameters.hh"
#include "G4Sphere.hh"
#include "G4SubtractionSolid.hh"

#include "G4VisAttributes.hh"

DetectorConstruction::DetectorConstruction(SimulationConfig& config,nlohmann::json & jsonConfig,std::string updateJsonPath):fConfig(&config),fjsonConfig{&jsonConfig},fupdateJsonPath{updateJsonPath}{}

G4VPhysicalVolume* DetectorConstruction::Construct(){

    int physplacementIndex=0;
     // Reference positions


    // World volume

    auto *nist = G4NistManager::Instance();
    auto *worldMat = nist->FindOrBuildMaterial(fConfig->worldMaterial);
    auto *worldSolid=new G4Box("worldSolid",fConfig->worldLength.x()/2,
                                            fConfig->worldLength.y()/2,
                                            fConfig->worldLength.z()/2     
                                                );


    auto *worldLogic=new G4LogicalVolume(worldSolid,worldMat,"worldLogic");
    worldLogic->SetVisAttributes(G4VisAttributes::GetInvisible());
    auto *worldPhys=new G4PVPlacement(nullptr,G4ThreeVector(),worldLogic,"worldPhys",nullptr,false,physplacementIndex++,true);
    
    // X-ray tube geometry


    // Distance from focal spot to tube collimator.

    const G4double d1=fConfig->sampleToFocalSpot-fConfig->sampleToTubeCollimatorDistance;

    if (d1<=0){
        G4Exception("Detector construction","Invalid Distance between focal spot and collimator distance",FatalException,
        "focal spot distaance must be greater than the tube collimator distance from sample");
    }
  
    if(fConfig->sourceCollimatorRadius<=0){
        G4Exception("detector construction","source Collimator radius",FatalException,"source Collimator radius must be greater than 0");
    }
    G4double d2=fConfig->sampleToTubeCollimatorDistance;

    // Beam diameter at the sample assuming geometric divergence from
    // the focal spot through the circular tube collimator.

    fConfig->sampleBeamDiameter=fConfig->sourceCollimatorRadius*2 *(d2+d1)/d1;

    //X-ray tube internal medium
    auto *tubeMat=nist->FindOrBuildMaterial(fConfig->xrayTubeInternalMedium);
    G4double tubeDistance=fConfig->sampleToFocalSpot-fConfig->sampleToTubeExitDistance-fConfig->xrayTubeWindowThickness;

    if(tubeDistance<=0){
        G4Exception("Detector construction","InvalidTubeVacuumLength",FatalException,"Sample to focal spot distance should not be equal or smaller than sample to tube exit distance");

    }
    auto *xrayTubeSolid=new G4Tubs(
        "tubesolid",
        0.0,
        fConfig->sampleBeamDiameter/2+0.1*mm,
        tubeDistance,
        0*deg,
        360*deg 
    );

    auto *xrayTubeLogic=new G4LogicalVolume(xrayTubeSolid,tubeMat,"xraytubelogic");

    G4double elevationAngle = fConfig->sourceElevationDeg;
    G4double distance=fConfig->sampleToFocalSpot;
    G4double azimuthAngle=fConfig->sourceIncidentAzimuthDeg;

    fConfig->sourcePosition=CalculatePositionFromSphericalCoordinates(distance,azimuthAngle,elevationAngle) ;
    
    FaceOrientationToSample tubeOrientation=CalculateRotationToFaceSample(fConfig->sourcePosition,fConfig->sampleReferencePoint);

    G4VPhysicalVolume*sourcePlacement=new G4PVPlacement(
        tubeOrientation.rotMatrix,
        fConfig->sourcePosition,
        xrayTubeLogic,
        "tubephys",
        worldLogic,
        false,
        physplacementIndex++,
        false
    );
    checkGeometryOrDie(sourcePlacement,"tubephys");

     //tube  window 

     auto *tubeWindowSolid=new G4Tubs("tubewindowsolid",
                                    0.0,
                                    fConfig->sampleBeamDiameter/2+0.001*mm,
                                    fConfig->xrayTubeWindowThickness/2,
                                    0.0*deg,
                                    360*deg);
    auto *tubeWindowMat=nist->FindOrBuildMaterial(fConfig->xrayTubeBeWindowMat);


     auto *tubeWindowLogic=new G4LogicalVolume(tubeWindowSolid,tubeWindowMat,"xraywindowlogic");

     G4double tubeWindowDistance=fConfig->sampleToTubeExitDistance+fConfig->xrayTubeWindowThickness/2;
     G4ThreeVector tubeWindowPosition=CalculatePositionFromSphericalCoordinates(tubeWindowDistance,azimuthAngle,elevationAngle) ;

     G4VPhysicalVolume*sourceWindowPlacement=new G4PVPlacement(
        CalculateRotationToFaceSample(tubeWindowPosition,fConfig->sampleReferencePoint).rotMatrix,
        tubeWindowPosition,
        tubeWindowLogic,
        "tubewindowphys",
        worldLogic,
        false,
        physplacementIndex++,
        false
     );
     checkGeometryOrDie(sourceWindowPlacement,"tubewindowphys");

    //tube filter 
    if(fConfig->isTubeFilterUse && fConfig-> tubeFilterEngine=="geant4"){
        auto & filterJson=(*fjsonConfig)["geometry"]["tube"]["filters"]["filters"];
        BuildComponent(fConfig->tubeFilters,worldLogic,fConfig->sampleReferencePoint,physplacementIndex,"filter",&filterJson);

    }

    //sample

    fConfig->sampleMat=BuildMaterial(fConfig->sampleMaterialType,
        fConfig->sampleMaterialName,
        fConfig->sampleMaterialDensity,
        fConfig->sampleMaterialComponents
    );

    G4cout << "\n--- Sample Material Info ---" << G4endl;
    G4cout << *(fConfig->sampleMat) << G4endl;
    G4cout << "----------------------------\n" << G4endl;    



    G4VSolid *sampleSolid=nullptr;
    G4ThreeVector samplePosition;

    if (fConfig->sampleMaterialShape=="Rectangular block"){
        sampleSolid=new G4Box("sampleSolid",fConfig->sampleWidth/2,fConfig->sampleHeight/2,fConfig->sampleThickness/2);
        samplePosition=G4ThreeVector(0,0,-fConfig->sampleThickness / 2.0);
    }
    else if (fConfig->sampleMaterialShape=="Circular cylinder")
    {
        sampleSolid=new G4Tubs(
            "sampleSolid",
            0.0,
            fConfig->sampleOuterRadius,
            fConfig->sampleThickness/2,
            0*deg,
            360*deg
        );
        samplePosition=G4ThreeVector(0,0,-fConfig->sampleThickness / 2.0);
    }
    else if (fConfig->sampleMaterialShape=="Sphere"){
        sampleSolid=new G4Sphere(
            "sampleSolid",
            0.0,
            fConfig->sampleRadius,
            0*deg,
            360*deg,
            0*deg,
            180*deg
        );
        samplePosition=G4ThreeVector(0,0,-fConfig->sampleRadius);

        
    }
    else{
        G4Exception("DetectorConstruction","InvalidSampleShape",FatalException,"Sample shape must be either Rectangular block, Circular cylinder or Sphere");
    }

    fSampleLogical=new G4LogicalVolume(sampleSolid,fConfig->sampleMat,"sampleLogic");

    // Create the sample region used for production cuts and biasing.
    auto* sampleRegion =new G4Region("SampleRegion");

    sampleRegion->AddRootLogicalVolume(
        fSampleLogical
    );    

    G4RotationMatrix *sampleRotationMatrix=new G4RotationMatrix();
    sampleRotationMatrix->rotateX(fConfig->sampleRotationX);
    sampleRotationMatrix->rotateY(fConfig->sampleRotationY);
    sampleRotationMatrix->rotateZ(fConfig->sampleRotationZ);


    auto &sampleJson=(*fjsonConfig)["geometry"]["sample"];
    storeRotationMatrix(sampleJson,*sampleRotationMatrix);
    sampleJson.erase("sample_rotation_deg");
    
    auto *samplePhys=new G4PVPlacement(sampleRotationMatrix,samplePosition,fSampleLogical,"samplePhys",worldLogic,false,physplacementIndex++,false);
    checkGeometryOrDie(samplePhys,"samplePhys");

    //detector collimator

    auto &detectorJson=(*fjsonConfig)["geometry"]["detector"];

    if (fConfig->isDetectorApertureUse  && fConfig->isDetectorCollimatorUse){
        BuildComponent(
            fConfig->detectorCollimators,
            worldLogic,
            fConfig->sampleReferencePoint,
            physplacementIndex,
            "collimator",
            &detectorJson["aperture"]["collimator"]["components"]


        );    
    }
    G4ThreeVector detectorPosition=CalculatePositionFromSphericalCoordinates(fConfig->detectorDistanceFromSample,
                                                                            fConfig->detectorazimuthAngle,
                                                                            fConfig->detectorelevationAngle);


    FaceOrientationToSample detectorLocalAxis=CalculateRotationToFaceSample(detectorPosition,fConfig->sampleReferencePoint);

    G4RotationMatrix * detectorRotation=detectorLocalAxis.rotMatrix;
    G4VSolid *detectorSolid{nullptr};

    if (fConfig->detectorActiveVolumeShape=="Rectangular detector"){
            detectorSolid=new G4Box("detectorSolid",fConfig->detectorWidth/2,fConfig->detectorHeight/2,fConfig->detectorThickness/2);
    }
    else if (fConfig->detectorActiveVolumeShape=="Circular detector"){
            detectorSolid = new G4Tubs(
                "detectorSolid",
                0.0,
                fConfig->detectorOuterRadius,
                fConfig->detectorThickness / 2.0,
                0.0,
                360.0 * deg
            );
    }

    else{
        G4Exception("DetectorConstruction","InvalidDetectorShape",FatalException,"Detector shape must be either Rectangular detector or Circular detector");
    }

    auto *detectorMat=BuildMaterial(
        fConfig->detectorMaterialType,
        fConfig->detectorMaterialName,
        fConfig->detectorDensity,
        fConfig->detectorMaterialComposition
    );
    fDetectorLV=new G4LogicalVolume(detectorSolid,detectorMat,"detectorLogic");
  

    G4LogicalVolume * cavityLogic{nullptr};


    // Detector housing
    G4double housingOuterWidth  = 0.0 * mm;
    G4double housingOuterHeight = 0.0 * mm;
    G4double housingOuterDepth  = 0.0 * mm;
    if (fConfig->isDetectorHousingUse) {

        //  Determine detector face dimensions

        G4double detectorFaceWidth  = 0.0 * mm;
        G4double detectorFaceHeight = 0.0 * mm;

        if (
            fConfig->detectorActiveVolumeShape =="Rectangular detector"
        ) {
            detectorFaceWidth  = fConfig->detectorWidth;
            detectorFaceHeight = fConfig->detectorHeight;
        }

        else if (
            fConfig->detectorActiveVolumeShape == "Circular detector"
        ) {
            detectorFaceWidth =
                2.0 * fConfig->detectorOuterRadius;

            detectorFaceHeight =
                2.0 * fConfig->detectorOuterRadius;
        }
        else {
            G4Exception(
                "DetectorConstruction::Construct",
                "InvalidDetectorShape",
                FatalException,
                "Unsupported active detector shape."
            );
        }

        // cavity dimensions
        if (
            fConfig->detectorHousingSideGap < 0.0 ||
            fConfig->detectorHousingFrontGap < 0.0 ||
            fConfig->detectorHousingBackGap < 0.0
        ) {
            G4Exception(
                "DetectorConstruction::Construct",
                "InvalidDetectorHousingGap",
                FatalException,
                "Detector housing side, front, and back gaps must be non-negative."
            );
        }

        const G4double cavityWidth =detectorFaceWidth +2.0 * fConfig->detectorHousingSideGap;

        const G4double cavityHeight =detectorFaceHeight +2.0 * fConfig->detectorHousingSideGap;

        const G4double cavityDepth =fConfig->detectorThickness +fConfig->detectorHousingFrontGap +fConfig->detectorHousingBackGap;

        //  outer housing thickness
        const G4double housingWallThickness=fConfig->detectorHousingWallThickness;

        //  cavity- wall thickness
        const G4double cavityWallThickness =fConfig->detectorHousingCavityWallThickness;

        if (
            cavityWidth <= 0.0 ||
            cavityHeight <= 0.0 ||
            cavityDepth <= 0.0
        ) {
            G4Exception(
                "DetectorConstruction::Construct",
                "InvalidDetectorCavityDimensions",
                FatalException,
                "Detector cavity dimensions must be greater than zero."
            );
        }

        if (
            housingWallThickness <= 0.0 ||
            cavityWallThickness <= 0.0
        ) {
            G4Exception(
                "DetectorConstruction::Construct",
                "InvalidDetectorHousingThickness",
                FatalException,
                "Housing and cavity-wall thicknesses must be greater than zero."
            );
        }

        // cap outer dimensions
        const G4double cavityOuterWidth =cavityWidth +2.0 * cavityWallThickness;

        const G4double cavityOuterHeight =cavityHeight +2.0 * cavityWallThickness;

        const G4double cavityOuterDepth =cavityDepth +2.0 * cavityWallThickness;

        // uter housing dimensions

        housingOuterWidth =cavityOuterWidth +2.0 * housingWallThickness;

        housingOuterHeight =cavityOuterHeight +2.0 * housingWallThickness;

        housingOuterDepth =cavityOuterDepth +2.0 * housingWallThickness;


        // Vacuum cavity
        auto* cavitySolid = new G4Box(
            "detectorCavitySolid",
            cavityWidth / 2.0,
            cavityHeight / 2.0,
            cavityDepth / 2.0
        );

        // Full outer box of the cavity-wall layer
        auto* cavityOuterSolid = new G4Box(
            "detectorCavityOuterSolid",
            cavityOuterWidth / 2.0,
            cavityOuterHeight / 2.0,
            cavityOuterDepth / 2.0
        );

        // Closed  shell before aperture cutting
        auto* cavityShellSolid = new G4SubtractionSolid(
            "detectorCavityShellSolid",
            cavityOuterSolid,
            cavitySolid
        );

        // Full outer  box
        auto* housingOuterSolid = new G4Box(
            "detectorHousingOuterSolid",
            housingOuterWidth / 2.0,
            housingOuterHeight / 2.0,
            housingOuterDepth / 2.0
        );

        auto* housingShellSolid = new G4SubtractionSolid(
            "detectorHousingShellSolid",
            housingOuterSolid,
            cavityOuterSolid
        );

        // Materials

        auto* cavityMaterial =G4NistManager::Instance()->FindOrBuildMaterial(
                                 fConfig->detectorHousingCavityInternalMaterialName
                            );

        auto* cavityWallMaterial = BuildMaterial(
                                    fConfig->detectorHousingCavityMaterialType,
                                    fConfig->detectorHousingCavityMaterialName,
                                    fConfig->detectorHousingCavityDensity,
                                    fConfig->detectorHousingCavityMaterialComposition
                                );

        auto* housingMaterial = BuildMaterial(
                                fConfig->detectorHousingMaterialType,
                                fConfig->detectorHousingMaterialName,
                                fConfig->detectorHousingDensity,
                                fConfig->detectorHousingMaterialComposition
                            );

        if (
            cavityMaterial == nullptr ||
            cavityWallMaterial == nullptr ||
            housingMaterial == nullptr
        ) {
            G4Exception(
                "DetectorConstruction::Construct",
                "InvalidDetectorHousingMaterial",
                FatalException,
                "Detector cavity, cavity-wall, or housing material could not be created."
            );
        }

        // The detector may not be centered in the cavity when frontGap != backGap.
        // Shift the cavity in world coordinates so the active detector remains
        // exactly at detectorPosition while preserving the requested front/back gaps.
        const G4double detectorZInsideCavity =
            (
                fConfig->detectorHousingBackGap -
                fConfig->detectorHousingFrontGap
            ) / 2.0;

        const G4ThreeVector detectorLocalPosition(
            0.0,
            0.0,
            detectorZInsideCavity
        );

        const G4ThreeVector worldOffset =detectorLocalAxis.localZAxis *detectorLocalPosition.z();

        const G4ThreeVector cavityPosition =detectorPosition -worldOffset;

        // Build one aperture cutter spanning the combined front thickness
        // of the inner cavity wall and outer housing wall.
        // The cutter is centered on the combined front-wall region and is
        // subtracted separately from both shell solids.

        const G4double totalFrontWallThickness =cavityWallThickness +housingWallThickness;


        const G4double frontWallCenterZ =cavityDepth / 2.0 +totalFrontWallThickness / 2.0;

        // Slightly longer to avoid coincident Boolean boundaries
        const G4double cutterTolerance =0.001 * mm;

        const G4double cutterHalfDepth =totalFrontWallThickness / 2.0 +cutterTolerance;

        G4VSolid* apertureCutter = nullptr;
        G4VSolid* windowSolid = nullptr;

        const G4double windowThickness = fConfig->detectorHousingWindowThickness;

        const G4double windowEdgeClearance  = 0.001 * mm;

        if (windowThickness <= 0.0) {
            G4Exception(
                "DetectorConstruction::Construct",
                "InvalidWindowThickness",
                FatalException,
                "Detector housing window thickness must be greater than zero."
            );
        }

        // Circular or rectangular aperture and window

        if (
            fConfig->detectorHousingApertureShape ==
            "circular"
        ) {
            const G4double apertureRadius =fConfig->detectorHousingApertureRadius;

            if (apertureRadius>cavityWidth/2 || apertureRadius>cavityHeight/2){
                G4Exception(
                    "DetectorConstruction::Construct",
                    "InvalidCircularAperture",
                    FatalException,
                    "Circular aperture radius must be smaller than the cavity outer width and height."
                );
            }


            const G4double windowRadius =apertureRadius -windowEdgeClearance ;

            if (
                apertureRadius <= 0.0 ||
                windowRadius <= 0.0
            ) {
                G4Exception(
                    "DetectorConstruction::Construct",
                    "InvalidCircularAperture",
                    FatalException,
                    "Circular aperture and window radii must be greater than zero."
                );
            }

            apertureCutter = new G4Tubs(
                "detectorHousingApertureCutter",
                0.0,
                apertureRadius,
                cutterHalfDepth,
                0.0,
                360.0 * deg
            );

            windowSolid = new G4Tubs(
                "detectorHousingWindowSolid",
                0.0,
                windowRadius,
                windowThickness / 2.0,
                0.0,
                360.0 * deg
            );
        }
        else if (
            fConfig->detectorHousingApertureShape =="rectangular"
        ) {
            const G4double apertureHalfWidth =fConfig->detectorHousingApertureWidth /2.0;

            const G4double apertureHalfHeight =fConfig->detectorHousingApertureHeight /2.0;

            const G4double windowHalfWidth =apertureHalfWidth -windowEdgeClearance ;

            const G4double windowHalfHeight =apertureHalfHeight -windowEdgeClearance ;

            if(cavityWidth/2<apertureHalfWidth || cavityHeight/2<apertureHalfHeight){
                G4Exception(
                    "DetectorConstruction::Construct",
                    "InvalidRectangularAperture",
                    FatalException,
                    "Rectangular aperture dimensions must be smaller than the cavity outer width and height."
                );
            }

            if (
                apertureHalfWidth <= 0.0 ||
                apertureHalfHeight <= 0.0 ||
                windowHalfWidth <= 0.0 ||
                windowHalfHeight <= 0.0
            ) {
                G4Exception(
                    "DetectorConstruction::Construct",
                    "InvalidRectangularAperture",
                    FatalException,
                    "Rectangular aperture and window dimensions must be greater than zero."
                );
            }

            apertureCutter = new G4Box(
                "detectorHousingApertureCutter",
                apertureHalfWidth,
                apertureHalfHeight,
                cutterHalfDepth
            );

            windowSolid = new G4Box(
                "detectorHousingWindowSolid",
                windowHalfWidth,
                windowHalfHeight,
                windowThickness / 2.0
            );
        }
        else {
            G4Exception(
                "DetectorConstruction::Construct",
                "InvalidDetectorHousingApertureShape",
                FatalException,
                "Unsupported detector housing aperture shape."
            );
        }

        // Apply the same cutter to both shells.
        // Only the intersection with each shell is removed:
        //   cavity shell  -> cuts through the inner cavity wall
        //   housing shell -> cuts through the outer housing wall
        auto* cavityShellWithApertureSolid =
            new G4SubtractionSolid(
                "detectorCavityShellWithApertureSolid",
                cavityShellSolid,
                apertureCutter,
                nullptr,
                G4ThreeVector(
                    0.0,
                    0.0,
                    frontWallCenterZ
                )
            );

        auto* housingWithApertureSolid =
            new G4SubtractionSolid(
                "detectorHousingWithApertureSolid",
                housingShellSolid,
                apertureCutter,
                nullptr,
                G4ThreeVector(
                    0.0,
                    0.0,
                    frontWallCenterZ
                )
            );

        // Window material

        auto* windowMaterial = BuildMaterial(
            fConfig->detectorHousingWindowMaterialType,
            fConfig->detectorHousingWindowMaterialName,
            fConfig->detectorHousingWindowDensity,
            fConfig->detectorHousingWindowComposition
        );

        if (windowMaterial == nullptr) {
            G4Exception(
                "DetectorConstruction::Construct",
                "InvalidDetectorWindowMaterial",
                FatalException,
                "Detector housing window material could not be created."
            );
        }

        // Logical volumes

        cavityLogic = new G4LogicalVolume(
            cavitySolid,
            cavityMaterial,
            "detectorCavityLogic"
        );

        auto* cavityShellLogic = new G4LogicalVolume(
            cavityShellWithApertureSolid,
            cavityWallMaterial,
            "detectorCavityShellLogic"
        );

        auto* housingLogic = new G4LogicalVolume(
            housingWithApertureSolid,
            housingMaterial,
            "detectorHousingLogic"
        );

        auto* windowLogic = new G4LogicalVolume(
            windowSolid,
            windowMaterial,
            "detectorHousingWindowLogic"
        );


        // The vacuum cavity, cavity wall, and outer housing are non-overlapping
        // sibling volumes placed with the same world transform.
        // The vacuum cavity also acts as the mother volume for the detector,
        // detector window, and internal detector components.

        // Place vacuum cavity in world
    

        auto *cavityPlacement=new G4PVPlacement(
            detectorRotation,
            cavityPosition,
            cavityLogic,
            "detectorCavityPhys",
            worldLogic,
            false,
            physplacementIndex++,
            false
        );
        checkGeometryOrDie(cavityPlacement,"detectorCavityPhys");



        //. Place cavity shell in world

        auto *cavityShellPhys=new G4PVPlacement(
            detectorRotation,
            cavityPosition,
            cavityShellLogic,
            "detectorCavityShellPhys",
            worldLogic,
            false,
            physplacementIndex++,
            false
        );
        checkGeometryOrDie(cavityShellPhys,"detectorCavityShellPhys");
        

        //  Place  housing in world

        auto *housingPhys=new G4PVPlacement(
            detectorRotation,
            cavityPosition,
            housingLogic,
            "detectorHousingPhys",
            worldLogic,
            false,
            physplacementIndex++,
            false
        );
        checkGeometryOrDie(housingPhys,"detectorHousingPhys");

        //. Place detector inside  cavity

        auto *detectorPhys=new G4PVPlacement(
            nullptr,
            detectorLocalPosition,
            fDetectorLV,
            "detectorPhys",
            cavityLogic,
            false,
            physplacementIndex++,
            false
        );
        checkGeometryOrDie(detectorPhys,"detectorPhys");

        //  Place window inside  cavity

        const G4double windowBoundaryClearance =
            0.001 * mm;

        const G4double windowCenterLocalZ =
            cavityDepth / 2.0 -
            windowThickness / 2.0 -
            windowBoundaryClearance;


        const G4double detectorFrontSurfaceLocalZ =
            detectorLocalPosition.z() +
            fConfig->detectorThickness / 2.0;

        const G4double windowBackSurfaceLocalZ =
            windowCenterLocalZ -
            windowThickness / 2.0;

        if (
            windowBackSurfaceLocalZ <=
            detectorFrontSurfaceLocalZ
        ) {
            G4Exception(
                "DetectorConstruction::Construct",
                "DetectorWindowOverlap",
                FatalException,
                "Detector window overlaps or touches the active detector."
            );
        }

        auto *windowPhys=new G4PVPlacement(
            nullptr,
            G4ThreeVector(
                0.0,
                0.0,
                windowCenterLocalZ
            ),
            windowLogic,
            "detectorHousingWindowPhys",
            cavityLogic,
            false,
            physplacementIndex++,
            false
        );
        checkGeometryOrDie(
            windowPhys,
            "detectorHousingWindowPhys"
        );

        const G4ThreeVector windowWorldPosition =
            cavityPosition +
            detectorLocalAxis.localZAxis *
            windowCenterLocalZ;

        // Store housing placement in JSON

        auto& housingPlacementJson =
            detectorJson["housing"]["placement"];

        auto& housingOrientationJson =
            housingPlacementJson["orientation"];

        storeRotationMatrix(
            housingOrientationJson,
            *detectorRotation
        );

        housingPlacementJson["position_mm"] = {
            cavityPosition.x() / mm,
            cavityPosition.y() / mm,
            cavityPosition.z() / mm
        };

        //  Store window placement in JSON

        auto& windowPlacementJson =
            detectorJson["housing"]["window"]["placement"];

        storeRotationMatrix(
            windowPlacementJson["orientation"],
            *detectorRotation
        );

        windowPlacementJson["position_mm"] = {
            windowWorldPosition.x() / mm,
            windowWorldPosition.y() / mm,
            windowWorldPosition.z() / mm
        };
    }

    else{
        auto *detectorPhys=new G4PVPlacement(detectorRotation,
                                            detectorPosition,
                                            fDetectorLV,
                                            "detectorPhys",
                                            worldLogic,
                                            false,
                                            physplacementIndex++,
                                            true);    

        checkGeometryOrDie(detectorPhys,"detectorPhys");

    }
    //detector filter 
      if(fConfig->isDetectorFilterUse){
        auto & detectorFilterJson=(*fjsonConfig)["geometry"]["detector"]["detector_layers"]["detector_filters"];

        BuildComponent(fConfig->detectorFilters,worldLogic,fConfig->sampleReferencePoint,physplacementIndex,"filter",&detectorFilterJson);

    }

    //detector internal mask

    if(fConfig->isDetectorApertureUse && fConfig->isDetectorInternalMaskUse){

        if(cavityLogic==nullptr){
            G4Exception("DetectorConstruction","InvalidDetectorInternalMaskPlacement",FatalException,"Detector internal mask can only be placed inside the detector housing cavity");
        }

        BuildComponent(fConfig->detectorInternalMasks,cavityLogic,fConfig->sampleReferencePoint,physplacementIndex,"internal mask",nullptr);

    }
    
    auto &activeVolumneOrientationJson=detectorJson["active_volume"]["placement"]["orientation"];
    storeRotationMatrix(activeVolumneOrientationJson,*detectorRotation);
    activeVolumneOrientationJson.erase("rotation_order");
    activeVolumneOrientationJson.erase("rotation_deg");


    auto* parameters = G4EmParameters::Instance();

    if(fConfig->isSecondarySplittingUse){
        G4cout<<"Directional bias is sued"<<G4endl;
        G4cout<<"Geant4 detector position"<<detectorPosition<<G4endl;
        G4double targetRadius = 0.0;

        if(fConfig->isDetectorHousingUse){


            targetRadius=std::sqrt(
                housingOuterWidth/2*housingOuterWidth/2+
                housingOuterHeight/2*housingOuterHeight/2+
                housingOuterDepth/2*housingOuterDepth/2

            );


        }
        else {

            if (
                    fConfig->detectorActiveVolumeShape ==
                    "Rectangular detector"
                ) {
                    const G4double halfWidth =
                        fConfig->detectorWidth / 2.0;

                    const G4double halfHeight =
                        fConfig->detectorHeight / 2.0;

                    const G4double halfThickness =
                        fConfig->detectorThickness / 2.0;

                    targetRadius = std::sqrt(
                        halfWidth * halfWidth +
                        halfHeight * halfHeight +
                        halfThickness * halfThickness
                    );
                }
                else if (
                    fConfig->detectorActiveVolumeShape ==
                    "Circular detector"
                ) {
                    const G4double halfThickness =
                        fConfig->detectorThickness / 2.0;

                    targetRadius = std::sqrt(
                        fConfig->detectorOuterRadius *
                        fConfig->detectorOuterRadius +
                        halfThickness * halfThickness
                    );
                }

        }

        parameters->SetDirectionalSplitting(true);
        parameters->SetDirectionalSplittingTarget(detectorPosition);
        parameters->SetDirectionalSplittingRadius(targetRadius);

    }


    else {
        G4EmParameters::Instance()->SetDirectionalSplitting(false);
    }

    saveJsonFile(fupdateJsonPath,*fjsonConfig);
    return worldPhys;

}

DetectorConstruction::~DetectorConstruction() = default;

// Create and attach the sensitive detector and optional
// interaction-biasing operator after the geometry has been constructed.

void DetectorConstruction::ConstructSDandField(){


    auto *sd=new SensitiveDetector();
    G4SDManager::GetSDMpointer()->AddNewDetector(sd);
    fDetectorLV->SetSensitiveDetector(sd);

    if(fConfig->isInteractionBiasingUse){
        auto *forceCollision=new G4BOptrForceCollision("gamma","ForceGammaCollisionInSample");
        forceCollision->AttachTo(
            fSampleLogical
        );


    }
}
// Convert distance, azimuth, and elevation into a world-coordinate position.
// Angles are expected to already be in Geant4 angular units.

G4ThreeVector DetectorConstruction::CalculatePositionFromSphericalCoordinates(G4double distance, G4double azimuthalAngle, G4double elevationAngle){

    G4double x=distance*std::sin(elevationAngle)*std::cos(azimuthalAngle);
    G4double y=distance*std::cos(elevationAngle);
    G4double z=distance*std::sin(elevationAngle)*std::sin(azimuthalAngle);
    return G4ThreeVector(x,y,z);
}
// Construct a local coordinate system whose +Z axis points from
// the component position toward the sample reference point.
// Returns both the local axes and the Geant4 placement rotation matrix.

FaceOrientationToSample DetectorConstruction::CalculateRotationToFaceSample(
   const G4ThreeVector &detectorPosition, 
   const G4ThreeVector &sampleReferencePoint) 
{
    FaceOrientationToSample rotation;
    G4ThreeVector zAxis = (sampleReferencePoint - detectorPosition).unit();
    
    G4ThreeVector upVector(0., 1., 0.);
    
    G4ThreeVector xAxis = upVector.cross(zAxis);
    
    if (xAxis.mag2() < 1e-6) {
        xAxis = G4ThreeVector(1., 0., 0.); 
    } else {
        xAxis = xAxis.unit();
    }
    
    G4ThreeVector yAxis = zAxis.cross(xAxis).unit();
    
    G4RotationMatrix* rotMatrix = new G4RotationMatrix(xAxis, yAxis, zAxis);
    
    rotMatrix->invert();
    rotation.localXAxis=xAxis;
    rotation.localYAxis=yAxis;
    rotation.localZAxis=zAxis;
    rotation.rotMatrix=rotMatrix;

    return rotation;
}
// Build either a custom material from elemental mass fractions
// or retrieve an existing material from the Geant4 NIST database.

G4Material*DetectorConstruction:: BuildMaterial(
    const G4String& materialType,
    const G4String& materialName,
    G4double density,
    const std::vector<MaterialComponent>& components
)
{
    auto* nist = G4NistManager::Instance();

    if (materialType == "custom") {
        if (density <= 0.0) {
            G4Exception(
                "BuildMaterial",
                "InvalidDensity",
                FatalException,
                "Custom material density must be greater than zero."
            );
        }

        if (components.empty()) {
            G4Exception(
                "BuildMaterial",
                "EmptyComposition",
                FatalException,
                "Custom material must contain at least one element."
            );
        }

        auto* material = new G4Material(
            materialName,
            density,
            static_cast<G4int>(components.size())
        );

        for (const auto& item : components) {
            auto* element =
                nist->FindOrBuildElement(item.elementName);

            if (element == nullptr) {
                G4Exception(
                    "BuildMaterial",
                    "InvalidElement",
                    FatalException,
                    "Could not build one of the requested elements."
                );
            }

            material->AddElement(element, item.fraction);
        }

        return material;
    }

    auto* material =
        nist->FindOrBuildMaterial(materialName);

    if (material == nullptr) {
        G4Exception(
            "BuildMaterial",
            "InvalidMaterial",
            FatalException,
            "Could not find or build the requested Geant4 material."
        );
    }

    return material;
}

// Store a Geant4 rotation matrix in the configuration JSON
// as a 3x3 numeric matrix.

void DetectorConstruction::storeRotationMatrix(json & orientationJson,const G4RotationMatrix &rotation){

    orientationJson["rotation_matrix"] = {
        {
            rotation.xx(),
            rotation.xy(),
            rotation.xz()
        },
        {
            rotation.yx(),
            rotation.yy(),
            rotation.yz()
        },
        {
            rotation.zx(),
            rotation.zy(),
            rotation.zz()
        }
    };
}
// Build the solid geometry for a detector/tube filter.
// Supported shapes: rectangular plate, circular disk, and ring.

G4VSolid * DetectorConstruction::BuildFilterSolid(const ComponentConfig & filter){
    G4VSolid *filterSolid=nullptr;

    if (filter.shape=="Rectangular plate"){

        filterSolid=new G4Box(
            filter.name+"Solid",
            filter.width/2.0,
            filter.height/2.0,
            filter.thickness/2.0
            
        );
    }
    else if(filter.shape=="Circular disk"){
        filterSolid=new G4Tubs(
            filter.name+"Solid",
            0.0,
            filter.outerRadius,
            filter.thickness/2.0,
            0.0,
            360.0*deg
        );
    }
    else if(filter.shape=="Ring"){
        filterSolid=new G4Tubs(
            filter.name+"Solid",
            filter.innerRadius,
            filter.outerRadius,
            filter.thickness/2.0,
            0.0,
            360.0*deg
        );
    }
    else{
        G4Exception(
            "DetectorConstruction::BuildFilterSolid",
            "UnknownFilterShape",
            FatalException,
            ("Unknown filter shape: " + filter.shape).c_str()
        );
    }
    return filterSolid;
}
// Build a collimator or internal-mask solid containing either
// a circular or rectangular aperture.

G4VSolid * DetectorConstruction::BuildCollimatorOrInternalMaskSolid(const ComponentConfig & component){
    
    G4VSolid *componentSolid=nullptr;
    if(component.shape=="Circular aperture"){

        componentSolid=new G4Tubs(
            component.name+"Solid",
            component.apertureRadius,
            component.outerRadius,
            component.length/2.0,
            0.0,
            360.0*deg
        );

    }
    else if(component.shape=="Rectangular aperture"){

        auto * outerSolid=new G4Box(
            component.name+"OuterSolid",
            component.outerWidth/2.0,
            component.outerHeight/2.0,
            component.length/2.0
        );
        auto * innerSolid=new G4Box(
            component.name+"InnerSolid",
            component.apertureWidth/2.0,
            component.apertureHeight/2.0,
            component.length/2+0.001*mm
        );
        componentSolid=new G4SubtractionSolid(
            component.name+"Solid",
            outerSolid,
            innerSolid
        );
    }
    else{
        G4Exception(
            "DetectorConstruction::BuildCollimatorOrInternalMaskSolid",
            "UnknownComponentShape",
            FatalException,
            ("Unknown component shape: " + component.shape).c_str()
        );
    }
    return componentSolid;
}
// Build and place a list of reusable geometry components.
//
// filter/collimator:
//   Positioned in world coordinates relative to the sample and
//   optionally oriented to face the sample.
//
// internal mask:
//   Positioned in the detector cavity's local coordinate system.
//
// componentJson:
//   Optional pointer used to store the resulting placement rotation.

void DetectorConstruction::BuildComponent(
    const std::vector<ComponentConfig>& components,
    G4LogicalVolume* motherLogic,
    const G4ThreeVector& sampleReferencePoint,
    G4int & physplacementIndex,
    G4String type,
    nlohmann::json *componentJson
)
{
    if(motherLogic==nullptr){
        G4Exception(
            "DetectorConstruction::BuildComponent",
            "InvalidMotherVolume",
            FatalException,
            "Mother logical volume is null. for filter or internal mask placement, a valid mother volume must be provided."
        );
    }
    int counter=0;
    for (const auto& component : components) {
        

        G4VSolid* componentSolid = {nullptr};
        if(type=="filter"){
            componentSolid=BuildFilterSolid(component);
        }
        else if(type=="internal mask" || type=="collimator"){
            componentSolid=BuildCollimatorOrInternalMaskSolid(component);
        }
        else{
            G4Exception(
                "DetectorConstruction::BuildComponent",
                "InvalidType",
                FatalException,
                ("Invalid type: " + type + ". Must be 'filter', 'internal mask', or 'collimator'.").c_str()
                        );
        
            }

        G4String physicalName = component.name + "_" + std::to_string(counter);

        G4Material* material = BuildMaterial(
            component.materialType,
            component.materialName,
            component.density,
            component.material
        );

        auto* componentLogic = new G4LogicalVolume(
            componentSolid,
            material,
            physicalName + "Logic"
        );

        G4ThreeVector componentPosition;
        G4RotationMatrix* componentRotation = nullptr;

        if(type=="filter" || type=="collimator") {
            componentPosition=CalculatePositionFromSphericalCoordinates(
                component.distanceFromSample,
                component.azimuthAngle,
                component.elevationAngle
            );

            if (component.orientationType == "face_sample") {
                componentRotation = CalculateRotationToFaceSample(
                    componentPosition,
                    sampleReferencePoint
                ).rotMatrix;
            }
            else {
                componentRotation = new G4RotationMatrix();

                componentRotation->rotateX(component.xRotation);
                componentRotation->rotateY(component.yRotation);
                componentRotation->rotateZ(component.zRotation);
            }

        }
        else if(type=="internal mask"){
            const G4double detectorZInsideCavity =(
                                                    fConfig->detectorHousingBackGap -
                                                    fConfig->detectorHousingFrontGap
                                                    ) / 2.0;

            componentPosition = G4ThreeVector(
                0.0,
                0.0,
                detectorZInsideCavity
                + fConfig->detectorThickness / 2.0
                + component.distanceFromSample
            );
        }


        else{
            G4Exception(
                "DetectorConstruction::BuildComponent",
                "InvalidType",
                FatalException,
                ("Invalid type: " + type + ". Must be 'filter' or 'internal mask' or 'collimator'.").c_str()
            );
        }
        G4cout
            << "\nINTERNAL MASK DEBUG\n"
            << "name             = " << component.name << G4endl
            << "distance         = " << component.distanceFromSample / mm << " mm" << G4endl
            << "length           = " << component.length / mm << " mm" << G4endl
            << "position Z       = " << componentPosition.z() / mm << " mm" << G4endl;

        auto* componentPhys=new G4PVPlacement(
            componentRotation,
            componentPosition,
            componentLogic,
            physicalName + "Phys",
            motherLogic,
            false,
            physplacementIndex,
            false
        );
        checkGeometryOrDie(componentPhys, physicalName + "Phys");

        if(componentJson!=nullptr){
            auto& orientationJson=(*componentJson)[counter]["placement"]["orientation"];
            if(componentRotation!=nullptr){
                storeRotationMatrix(
                    orientationJson,
                    *componentRotation
                );

            }
            orientationJson.erase("rotation_order");
            orientationJson.erase("rotation_deg");

        }
        counter++;
        physplacementIndex++;
    }
    
}
// Write the updated simulation configuration to disk.

void DetectorConstruction::saveJsonFile(
    const std::string&filePath,
    const nlohmann::json &configJson
){
    std::ofstream outputFile(filePath);
    if (!outputFile.is_open()) {
        throw std::runtime_error(
            "Could not open JSON file: " + filePath
        );
    }
    outputFile << configJson.dump(4);

}

// Check a placed physical volume for geometry overlaps.
// Abort the simulation immediately if an overlap is detected.

void DetectorConstruction::checkGeometryOrDie(G4VPhysicalVolume* volume,const G4String &name){


        if(volume!=nullptr && volume->CheckOverlaps(10000,0,true,1)){
            G4Exception(
                "DetectorConstruction::checkGeometryOrDie",
                "GeometryOverlapError",
                FatalException,
                ("Geometry overlaps detected in volume: " + name).c_str()
            );
        }
        else{
            G4cout<<"No geometry overlaps detected in volume: "<<name<<G4endl;
        }
}
