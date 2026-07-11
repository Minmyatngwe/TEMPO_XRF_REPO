#include "detectorConstruction.hh"
#include "G4RotationMatrix.hh"
#include "G4Region.hh"
#include "sensitiveDetector.hh"
#include "G4BOptrForceCollision.hh"
#include "G4LogicalVolumeStore.hh"
#include "G4ProductionCuts.hh"
#include "G4Tubs.hh"
DetectorConstruction::DetectorConstruction(SimulationConfig& config):fConfig(&config){}

G4VPhysicalVolume* DetectorConstruction::Construct(){


    auto *nist = G4NistManager::Instance();
    auto *worldMat = nist->FindOrBuildMaterial(fConfig->worldMaterial);

    G4cout<<"is sample custom"<<fConfig->sampleMaterialIsCustom<<G4endl;

    if(fConfig->sampleMaterialIsCustom){
        G4cout<<"Enter the custom material"<<G4endl;

        fConfig->sampleMat=new G4Material(
            "sampleMaterial",
            fConfig->sampleMaterialDensity,
            fConfig->sampleComposion.size()
        );

        for(const auto & item:fConfig->sampleComposion){
            G4String elementName=item.first;
            G4double fraction=item.second;
            G4Element *element=nist->FindOrBuildElement(elementName);
            fConfig->sampleMat->AddElement(element,fraction);
        }


    }
    else{
        fConfig->sampleMat = nist->FindOrBuildMaterial(fConfig->sampleMaterial);

    }

    G4cout << "\n--- Sample Material Info ---" << G4endl;
    G4cout << *(fConfig->sampleMat) << G4endl;
    G4cout << "----------------------------\n" << G4endl;


    


    auto *worldSolid=new G4Box("worldSolid",15*cm,15*cm,15*cm);

    auto *worldLogic=new G4LogicalVolume(worldSolid,worldMat,"worldLogic");
    auto *worldPhys=new G4PVPlacement(nullptr,G4ThreeVector(),worldLogic,"worldPhys",nullptr,false,0,true);

    auto *sampleSolid=new G4Box("sampleSolid",fConfig->sampleMaterialSize.x()/2,fConfig->sampleMaterialSize.y()/2,fConfig->sampleMaterialSize.z()/2);
    auto *sampleLogic=new G4LogicalVolume(sampleSolid,fConfig->sampleMat,"sampleLogic");


    G4Region* sampleRegion = new G4Region("SampleRegion");
    sampleLogic->SetRegion(sampleRegion);
    sampleRegion->AddRootLogicalVolume(sampleLogic);
    auto* sampleCuts = new G4ProductionCuts();

    sampleCuts->SetProductionCut(0.0001*mm, "gamma");
    sampleCuts->SetProductionCut(0.01*mm, "e-");
    sampleCuts->SetProductionCut(0.01*mm, "e+");
    sampleCuts->SetProductionCut(0.01*mm, "proton");

    sampleRegion->SetProductionCuts(sampleCuts);
    auto *samplePhys=new G4PVPlacement(nullptr,G4ThreeVector(0,0,0),sampleLogic,"samplePhys",worldLogic,false,1,true);


    //detector collimator
    if (fConfig->detectorCollimatorIsEnabled){
            auto * detectorCollimatorSolid=new G4Tubs("detectorCollimatorSolid",
                                                fConfig->detectorCollimatorInnerRadius, //inner radius

                                                fConfig->detectorCollimatorOuterRadius,//outer radius
                                                fConfig->detectorCollimatorThickness/2, //half length in z
                                                0*deg,
                                                360*deg);


            G4Material *detectorCollimatorMat {nullptr};
            if (fConfig->detectorCollimatorIsCustom){

            }
            else{
                
                detectorCollimatorMat=nist->FindOrBuildMaterial(fConfig->detectorCollimatorMaterial);
                
            }

            auto *detectorCollimatorLogic=new G4LogicalVolume(detectorCollimatorSolid,detectorCollimatorMat,"detectorCollimatorLogic");


            G4RotationMatrix *detectorCollimatorRotation=new G4RotationMatrix();
            detectorCollimatorRotation->rotateY(-90*deg+fConfig->detectorCollimatorAnlgeFromSample);
            G4ThreeVector detectorCollimatorPosition(fConfig->sampleToDetectorCollimatorDistance*std::cos(fConfig->detectorCollimatorAnlgeFromSample),
                                                    0,
                                                    std::sin(fConfig->detectorCollimatorAnlgeFromSample)*fConfig->sampleToDetectorCollimatorDistance);

            new G4PVPlacement(
                detectorCollimatorRotation,
                detectorCollimatorPosition,
                detectorCollimatorLogic,
                "detectorCollimatorPhys",
                worldLogic,
                false,
                3,
                true
            );
    }
    G4cout<<"Is detector collimator enabled: "<<fConfig->detectorCollimatorIsEnabled<<G4endl;
    G4cout<<"Is detector collimator custom: "<<fConfig->detectorCollimatorIsCustom<<G4endl;
    G4cout<<"Detector collimator material: "<<fConfig->detectorCollimatorMaterial<<G4endl;
    G4cout<<"Detector collimator density: "<<fConfig->detectorCollimatorDensity/(g/cm3)<<" g/cm3"<<G4endl;
    G4cout<<"Detector collimator thickness: "<<fConfig->detectorCollimatorThickness/mm<<" mm"<<G4endl;
    G4cout<<"Detector collimator outer radius: "<<fConfig->detectorCollimatorOuterRadius/mm<<" mm"<<G4endl;     
    G4cout<<"Detector collimator inner radius: "<<fConfig->detectorCollimatorInnerRadius/mm<<" mm"<<G4endl;
    G4cout<<"Detector collimator angle from sample: "<<fConfig->detectorCollimatorAnlgeFromSample/deg<<" deg"<<G4endl;
    G4cout<<"Detector collimator distance from sample: "<<fConfig->sampleToDetectorCollimatorDistance/mm<<" mm"<<G4endl;
    G4cout<<"Detector collimator position: "<<G4ThreeVector(fConfig->sampleToDetectorCollimatorDistance*std::cos(fConfig->detectorCollimatorAnlgeFromSample),
                                                    0,
                                                    std::sin(fConfig->detectorCollimatorAnlgeFromSample)*fConfig->sampleToDetectorCollimatorDistance)/mm<<" mm"<<G4endl;
    

    G4double dectorhalf = std::sqrt(fConfig->detectorArea);



    auto *detectorSolid=new G4Box("detectorSolid",dectorhalf/2,dectorhalf/2,fConfig->detectorthickness/2);

    auto *detectorMat=nist->FindOrBuildMaterial("G4_Si");
    fDetectorLV=new G4LogicalVolume(detectorSolid,detectorMat,"detectorLogic");


    G4ThreeVector detectorPosition(fConfig->detectorDistance*std::cos(fConfig->takeoffAngle),0,std::sin(fConfig->takeoffAngle)*fConfig->detectorDistance);


    G4cout<<"detectorPosition: "<<detectorPosition/mm<<" mm"<<G4endl;
    G4RotationMatrix * detectorRotation=new G4RotationMatrix();
    detectorRotation->rotateY(-90*deg+fConfig->takeoffAngle);
    auto *detectorPhys=new G4PVPlacement(detectorRotation,detectorPosition,fDetectorLV,"detectorPhys",worldLogic,false,2,true);    

    return worldPhys;
}

DetectorConstruction::~DetectorConstruction() = default;
void DetectorConstruction::ConstructSDandField(){
    auto *sd=new SensitiveDetector();
    G4SDManager::GetSDMpointer()->AddNewDetector(sd);
    fDetectorLV->SetSensitiveDetector(sd);


}
