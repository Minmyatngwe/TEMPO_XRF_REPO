#include "buildinghelper.hh"
#include "G4Tubs.hh"
#include "G4EmParameters.hh"
#include "G4Sphere.hh"
#include "G4NistManager.hh"
#include "G4Box.hh"
#include "G4SubtractionSolid.hh"

G4LogicalVolume * BuildHelper::BuildGeometry( ComponentConfig & component){


    auto *material=BuildMaterial(component.material);
    G4VSolid * componentSolid{nullptr};
    if (component.shape=="rectangular"){
        componentSolid=new G4Box(component.name+"_solid",
                                       component.width/2,
                                       component.height/2,
                                       component.thickness/2
                            );
    }

    else if (component.shape=="circular"){
        componentSolid=new G4Tubs(
            component.name+"+_solid",
            0.0,
            component.radius,
            component.thickness/2,
            0*deg,
            360*deg


        );

    }
    else if(component.shape.find("aperture")!= G4String::npos){

        if(component.apertureShape=="rectangular"){
            auto * outerSolid=new G4Box(
                component.name+"outerSolid",
                component.outerWidth/2,
                component.outerHeight/2,
                component.length/2
            );
            auto *innerSolid=new G4Box(
                component.name+"InnerSolid",
                component.apertureWidth/2,
                component.apertureHeight/2,
                component.length/2+0.001*mm
            );
            componentSolid=new G4SubtractionSolid(
                component.name+"_solid",
                outerSolid,
                innerSolid
            );

        }
        else if(component.apertureShape=="circular"){
            componentSolid=new G4Tubs(
                component.name+"_solid",
                component.apertureRadius,
                component.outerRadius,
                component.length/2,
                0*deg,
                360*deg
            );

        }
        else{
            G4Exception(
                "BuildingHelper::BuildGeometry",
                "UnknownComponentShape",
                FatalException,
                ("Unknown component shape: " + component.apertureShape).c_str()
            );

        }


    }



    auto * componentLogical=new G4LogicalVolume(componentSolid,material,component.name+"_logical");

    return componentLogical;



}

G4Material * BuildHelper::BuildMaterial(const MaterialConfig & matConfig){
    auto *nist = G4NistManager::Instance();

    G4Material *mat{nullptr};

    if (matConfig.type=="geant4"){
        mat=nist->FindOrBuildMaterial(matConfig.name);

    }
    else if(matConfig.type=="custom"){

        if(matConfig.density<=0.0){
             G4Exception(
                "BuildMaterial",
                "InvalidDensity",
                FatalException,
                "Custom material density must be greater than zero."
            );

        }
        if(matConfig.compositions.empty()){
            G4Exception(
                "BuildMaterial",
                "EmptyComposition",
                FatalException,
                "Custom material must contain at least one element."
            );

        }

        mat=new G4Material(
            matConfig.name,
            matConfig.density,
            static_cast<G4int>(matConfig.compositions.size())
        );

        for(const auto &item:matConfig.compositions){
            auto *element=nist->FindOrBuildElement(item.elementName);
            if (element == nullptr) {
                G4Exception(
                    "BuildMaterial",
                    "InvalidElement",
                    FatalException,
                    "Could not build one of the requested elements."
                );
            }
            mat->AddElement(element, item.fraction);

        }

    }

    else{
            G4String errorMsg =
                "The material type should be 'geant4' or 'custom', but got: " +
                matConfig.type;

            G4Exception(
                "BuildHelper::BuildMaterial",
                "InvalidType",
                FatalException,
                errorMsg.c_str()
            );
    }

    return mat;
}



std::pair<G4ThreeVector,ComponentRotation> BuildHelper::BuildPlacement(ComponentConfig & component,const SimulationConfig & fConfig, ComponentConfig * parentComponent){
    if(!component.isInherited){
        component.position=CalculatePositionFromSphericalCoordinates(component.distance,component.azimuthAngle,component.elevationAngle);
        component.rotation=CalculateRotation(component.orientationType,component.position,fConfig.sampleReferencePoint,component.xRotation,component.yRotation,component.zRotation);
        


    }
    else{
        if (parentComponent == nullptr) {

            G4String errorMsg =
                "Component '" +
                component.name +
                "' uses inherited placement, but no parent/reference "
                "component was provided.";

            G4Exception(
                "BuildHelper::BuildPlacement",
                "MissingParentComponent",
                FatalException,
                errorMsg.c_str()
            );
        }


        G4double distance=parentComponent->distance-GetComponentAxialThickness(*parentComponent)/2-component.distanceFromReferenceSurface-GetComponentAxialThickness(component)/2;

        component.position=CalculatePositionFromSphericalCoordinates(distance,parentComponent->azimuthAngle,parentComponent->elevationAngle);
        
        if (parentComponent->rotation.rotMatrix == nullptr) {

            G4String errorMsg =
                "Cannot inherit placement for component '" +
                component.name +
                "'. Parent component '" +
                parentComponent->name +
                "' does not have a valid rotation. "
                "The parent component must be placed before an inherited component.";

            G4Exception(
                "BuildHelper::BuildPlacement",
                "InvalidParentRotation",
                FatalException,
                errorMsg.c_str()
            );
        }
        component.azimuthAngle =parentComponent->azimuthAngle;

        component.elevationAngle =parentComponent->elevationAngle;

        component.rotation =parentComponent->rotation;


    }
    return {component.position,component.rotation};

        
}
G4PVPlacement * BuildHelper::BuildComponent( ComponentConfig & component,SimulationConfig & config,
                                    G4LogicalVolume * mother,int & counter,ComponentConfig * parentComponent){

    auto *logicalVolume=BuildGeometry(component);
    auto [position,rotation]=BuildPlacement(component,config,parentComponent);

    return new G4PVPlacement(
        rotation.rotMatrix,
        position,
        logicalVolume,
        component.name+"_placement",
        mother,
        false,
        counter++,
        true 
    );
    
}
G4ThreeVector BuildHelper::CalculatePositionFromSphericalCoordinates(G4double distance, G4double azimuthalAngle, G4double elevationAngle){

    G4double x=distance*std::sin(elevationAngle)*std::cos(azimuthalAngle);
    G4double y=distance*std::cos(elevationAngle);
    G4double z=distance*std::sin(elevationAngle)*std::sin(azimuthalAngle);
    return G4ThreeVector(x,y,z);
}

ComponentRotation BuildHelper::CalculateRotation(G4String orientationType,
    const G4ThreeVector & componentPosition,
    const G4ThreeVector & samplePosition,
    G4double xRotation,G4double yRotation,G4double zRotation){
    ComponentRotation rotation;

    if(orientationType=="face_sample"){
        G4ThreeVector zAxis=(samplePosition-componentPosition).unit();

        G4ThreeVector upVector (0,1,0);
        G4ThreeVector xAxis=upVector.cross(zAxis);

        if(xAxis.mag2()<1e-6){
            xAxis=G4ThreeVector(1,0,0);
        }
        else{
            xAxis=xAxis.unit();
        }
        G4ThreeVector yAxis=zAxis.cross(xAxis).unit();
        G4RotationMatrix * rotMatrix=new G4RotationMatrix(xAxis,yAxis,zAxis);

        rotMatrix->invert();

        rotation.localXAxis=xAxis;
        rotation.localYAxis=yAxis;
        rotation.localZAxis=zAxis;
        rotation.rotMatrix=rotMatrix;
    }
    else if(orientationType=="manual"){
        G4RotationMatrix *rotMatrix=new G4RotationMatrix();
        rotMatrix->rotateX(xRotation);
        rotMatrix->rotateY(yRotation);
        rotMatrix->rotateZ(zRotation);
        rotation.rotMatrix=rotMatrix;

    }
    else {
        G4ExceptionDescription msg;
        msg << "Invalid orientation type: \"" << orientationType << "\"\n"
            << "Supported orientation types are:\n"
            << "  - face_sample\n"
            << "  - manual";

        G4Exception(
            "BuildHelper::CalculateRotation",
            "InvalidOrientationType",
            FatalException,
            msg
        );
    }
    return rotation;

}

G4double BuildHelper::GetComponentAxialThickness(
    const ComponentConfig& component)
{
    if (
        component.shape == "circular" ||
        component.shape == "rectangular"
    ) {
        return component.thickness;
    }

    if (
        component.shape == "circular aperture" ||
        component.shape == "rectangular aperture"
    ) {
        return component.length;
    }

    G4Exception(
        "BuildHelper::GetComponentAxialThickness",
        "InvalidGeometry",
        FatalException,
        (
            "Cannot determine axial thickness for: "
            + component.name
        ).c_str()
    );

    return 0.0;
}
void BuildHelper::BuildHousing(SimulationConfig& fConfig,G4LogicalVolume* detectorLogicalVolume,
    G4LogicalVolume*& cavityLogic,G4LogicalVolume* worldLogic,G4int& physplacementIndex){

    
    auto& housing = fConfig.housingConfig;

    // Detector dimensions

    G4double detectorWidth = 0.0;
    G4double detectorHeight = 0.0;
    G4double detectorThickness = 0.0;

    auto* detectorSolid = detectorLogicalVolume->GetSolid();

    if (auto* tubs = dynamic_cast<G4Tubs*>(detectorSolid)) {

        detectorWidth =2.0 * tubs->GetOuterRadius();

        detectorHeight =2.0 * tubs->GetOuterRadius();

        detectorThickness =2.0 * tubs->GetZHalfLength();
    }

    else if (auto* box = dynamic_cast<G4Box*>(detectorSolid)) {

        detectorWidth = 2.0 * box->GetXHalfLength();

        detectorHeight =2.0 * box->GetYHalfLength();

        detectorThickness =2.0 * box->GetZHalfLength();
    }

    else {

        G4Exception(
            "BuildHelper::BuildHousing",
            "UnsupportedDetectorGeometry",
            FatalException,
            "BuildHousing supports only G4Tubs and G4Box detectors."
        );
    }


    const G4double clearance =housing.detectorClearance;

    const G4double cavityWallThickness =housing.housingCavityWallThickness;

    const G4double housingWallThickness =housing.housingWallThickness;

    const G4double windowThickness =housing.window_thickness_mm;


    if (
        clearance < 0.0 ||
        cavityWallThickness <= 0.0 ||
        housingWallThickness <= 0.0 ||
        windowThickness <= 0.0)
    {
        G4Exception(
            "BuildHelper::BuildHousing",
            "InvalidHousingDimensions",
            FatalException,
            "Housing clearance and wall/window thickness values are invalid."
        );
    }


    // Inner empty cavity
    const G4double cavityWidth =detectorWidth + 2.0 * clearance;

    const G4double cavityHeight = detectorHeight + 2.0 * clearance;

    const G4double cavityThickness =detectorThickness + 2.0 * clearance;


    // Outer dimensions of cavity-wall layer
    const G4double cavityOuterWidth =cavityWidth + 2.0 * cavityWallThickness;

    const G4double cavityOuterHeight =cavityHeight + 2.0 * cavityWallThickness;

    const G4double cavityOuterThickness =cavityThickness + 2.0 * cavityWallThickness;


    // Entire detector housing
    const G4double housingOuterWidth =cavityOuterWidth + 2.0 * housingWallThickness;

    const G4double housingOuterHeight =cavityOuterHeight + 2.0 * housingWallThickness;

    const G4double housingOuterThickness =cavityOuterThickness + 2.0 * housingWallThickness;

    housing.width=housingOuterWidth;
    housing.height=housingOuterHeight;
    housing.thickness=housingOuterThickness;
    

    // Main solids

    auto* cavitySolid = new G4Box(
        "detectorCavitySolid",
        cavityWidth / 2.0,
        cavityHeight / 2.0,
        cavityThickness / 2.0
    );


    auto* cavityOuterSolid = new G4Box(
        "detectorCavityOuterSolid",
        cavityOuterWidth / 2.0,
        cavityOuterHeight / 2.0,
        cavityOuterThickness / 2.0
    );


    auto* cavityShellSolid = new G4SubtractionSolid(
        "detectorCavityShellSolid",
        cavityOuterSolid,
        cavitySolid
    );


    auto* housingOuterSolid = new G4Box(
        "detectorHousingOuterSolid",
        housingOuterWidth / 2.0,
        housingOuterHeight / 2.0,
        housingOuterThickness / 2.0
    );


    auto* housingShellSolid = new G4SubtractionSolid(
        "detectorHousingShellSolid",
        housingOuterSolid,
        cavityOuterSolid
    );

    // Materials
    auto* cavityMediumMaterial =BuildMaterial(
                                housing.innerCavityMediumMaterial
                            );

    auto* cavityWallMaterial =BuildMaterial(
                                housing.cavityWallMaterial
                            );

    auto* housingMaterial =BuildMaterial(
                                housing.housingWallMaterial
                            );

    auto* windowMaterial =BuildMaterial(
                                housing.detectorWindowMaterial
                            );


    const G4double totalFrontWallThickness =cavityWallThickness+ housingWallThickness;


    const G4double frontWallCenterZ =cavityThickness / 2.0+ totalFrontWallThickness / 2.0;


    // Make cutter slightly longer so Boolean surfaces
    // are not exactly coincident.
    const G4double tolerance =0.001 * mm;


    const G4double cutterHalfDepth =totalFrontWallThickness / 2.0+ tolerance;


    G4VSolid* apertureCutter = nullptr;
    G4VSolid* apertureChannelSolid = nullptr;
    G4VSolid* windowSolid = nullptr;


    // Circular aperture/window

    if (housing.apertureShape == "circular") {

        const G4double radius =housing.apertureRadius;


        if (
            radius <= 0.0 ||
            radius > cavityWidth / 2.0 ||
            radius > cavityHeight / 2.0)
        {
            G4Exception(
                "BuildHelper::BuildHousing",
                "InvalidCircularAperture",
                FatalException,
                "Circular housing aperture radius is invalid."
            );
        }


        apertureCutter = new G4Tubs(
            "detectorHousingApertureCutter",
            0.0,
            radius,
            cutterHalfDepth,
            0.0,
            360.0 * deg
        );


        apertureChannelSolid = new G4Tubs(
            "detectorHousingApertureChannelSolid",
            0.0,
            radius,
            totalFrontWallThickness / 2.0,
            0.0,
            360.0 * deg
        );


        windowSolid = new G4Tubs(
            "detectorHousingWindowSolid",
            0.0,
            radius,
            windowThickness / 2.0,
            0.0,
            360.0 * deg
        );
    }



    // Rectangular aperture/window

    else if (housing.apertureShape == "rectangular") {

        const G4double halfWidth =housing.apertureWidth / 2.0;

        const G4double halfHeight =housing.apertureHeight / 2.0;


        if (
            halfWidth <= 0.0 ||
            halfHeight <= 0.0 ||
            halfWidth > cavityWidth / 2.0 ||
            halfHeight > cavityHeight / 2.0)
        {
            G4Exception(
                "BuildHelper::BuildHousing",
                "InvalidRectangularAperture",
                FatalException,
                "Rectangular housing aperture dimensions are invalid."
            );
        }


        apertureCutter = new G4Box(
            "detectorHousingApertureCutter",
            halfWidth,
            halfHeight,
            cutterHalfDepth
        );


        apertureChannelSolid = new G4Box(
            "detectorHousingApertureChannelSolid",
            halfWidth,
            halfHeight,
            totalFrontWallThickness / 2.0
        );


        windowSolid = new G4Box(
            "detectorHousingWindowSolid",
            halfWidth,
            halfHeight,
            windowThickness / 2.0
        );
    }


    else {

        G4ExceptionDescription msg;

        msg << "Unsupported housing aperture shape: "
            << housing.apertureShape << "\n"
            << "Supported shapes:\n"
            << "  - circular\n"
            << "  - rectangular";

        G4Exception(
            "BuildHelper::BuildHousing",
            "InvalidHousingApertureShape",
            FatalException,
            msg
        );
    }



    auto* cavityShellWithAperture =
        new G4SubtractionSolid(
            "detectorCavityShellWithAperture",
            cavityShellSolid,
            apertureCutter,
            nullptr,
            G4ThreeVector(
                0.0,
                0.0,
                frontWallCenterZ
            )
        );



    auto* housingShellWithAperture =
        new G4SubtractionSolid(
            "detectorHousingShellWithAperture",
            housingShellSolid,
            apertureCutter,
            nullptr,
            G4ThreeVector(
                0.0,
                0.0,
                frontWallCenterZ
            )
        );



    // Logical volumes

    cavityLogic = new G4LogicalVolume(
        cavitySolid,
        cavityMediumMaterial,
        "detectorCavityLogic"
    );


    auto* cavityShellLogic =
        new G4LogicalVolume(
            cavityShellWithAperture,
            cavityWallMaterial,
            "detectorCavityShellLogic"
        );


    auto* housingLogic =
        new G4LogicalVolume(
            housingShellWithAperture,
            housingMaterial,
            "detectorHousingLogic"
        );


    auto* apertureChannelLogic =
        new G4LogicalVolume(
            apertureChannelSolid,
            cavityMediumMaterial,
            "detectorHousingApertureChannelLogic"
        );


    auto* windowLogic =
        new G4LogicalVolume(
            windowSolid,
            windowMaterial,
            "detectorHousingWindowLogic"
        );


    // Housing follows detector placement

    housing.position = fConfig.detectorConfig.position;

    housing.rotation =fConfig.detectorConfig.rotation;


    const G4ThreeVector housingPosition =housing.position;

    const auto& housingRotation =housing.rotation;



    new G4PVPlacement(
        housingRotation.rotMatrix,
        housingPosition,
        cavityLogic,
        "detectorCavityPhys",
        worldLogic,
        false,
        physplacementIndex++,
        true
    );



    new G4PVPlacement(
        housingRotation.rotMatrix,
        housingPosition,
        cavityShellLogic,
        "detectorCavityShellPhys",
        worldLogic,
        false,
        physplacementIndex++,
        true
    );



    new G4PVPlacement(
        housingRotation.rotMatrix,
        housingPosition,
        housingLogic,
        "detectorHousingPhys",
        worldLogic,
        false,
        physplacementIndex++,
        true
    );


    // Aperture channel

    const G4ThreeVector apertureChannelPosition =housingPosition+ housingRotation.localZAxis* frontWallCenterZ;


    new G4PVPlacement(
        housingRotation.rotMatrix,
        apertureChannelPosition,
        apertureChannelLogic,
        "detectorHousingApertureChannelPhys",
        worldLogic,
        false,
        physplacementIndex++,
        true
    );



    // Window sits directly outside the front housing surface.
    const G4double windowCenterZ =cavityThickness / 2.0+ totalFrontWallThickness+ windowThickness / 2.0;


    const G4ThreeVector windowPosition =housingPosition+ housingRotation.localZAxis* windowCenterZ;


    fConfig.detectorWindowConfig.position =windowPosition;

    fConfig.detectorWindowConfig.rotation =housingRotation;

    fConfig.detectorWindowConfig.thickness =windowThickness;


    new G4PVPlacement(
        housingRotation.rotMatrix,
        windowPosition,
        windowLogic,
        "detectorHousingWindowPhys",
        worldLogic,
        false,
        physplacementIndex++,
        true
    );

    // Detector inside cavity

    new G4PVPlacement(
        nullptr,
        G4ThreeVector(),
        detectorLogicalVolume,
        fConfig.detectorConfig.name+"_placement",
        cavityLogic,
        false,
        physplacementIndex++,
        true
    );
}