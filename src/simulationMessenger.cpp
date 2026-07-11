#include "simulationMessenger.hh"

SimulationMessenger::SimulationMessenger(SimulationConfig& config):fconfig(&config){

    fAddShieldLayerCmd = new G4UIcommand("/xrf/addShieldLayer", this);
    fAddShieldLayerCmd->SetGuidance("Add shield layer: material thickness unit gapbefore unit");

    fMessenger=new G4GenericMessenger(this,"/xrf/","Simulation control commands");
    fMessenger->DeclareProperty("sampleMaterial",fconfig->sampleMaterial,"Set sample material");
    fMessenger->DeclareProperty("sampleMaterialIsCustom",fconfig->sampleMaterialIsCustom,"Set if the sample material is custom defined");
    fMessenger->DeclarePropertyWithUnit("sampleMaterialDensity",
                                        "g/cm3",
                                        fconfig->sampleMaterialDensity,
                                        "Set the density of the custom sample material");
    fMessenger->DeclarePropertyWithUnit("incidentAngle",
                                        "deg",
                                        fconfig->incidentAngle,
                                        "Set the incident angle of the primary particles");
    fMessenger->DeclarePropertyWithUnit("sourceDistance",
                                        "mm",
                                        fconfig->sourceDistance,
                                        "Set the distance between the source and the sample");
    fMessenger->DeclarePropertyWithUnit("detectorDistance",
                                        "mm",
                                        fconfig->detectorDistance,
                                        "Set the distance between the sample and the detector");
    fMessenger->DeclarePropertyWithUnit("takeoffAngle",
                                        "deg",
                                        fconfig->takeoffAngle,
                                        "Set the takeoff angle of the detector");
    fMessenger->DeclarePropertyWithUnit("detectorBewindowThickness",
                                        "mm",
                                        fconfig->detectorBewindowThickness,
                                        "Set the thickness of the detector bewindow");
    fMessenger->DeclarePropertyWithUnit("detectorthickness",
                                        "mm",
                                        fconfig->detectorthickness,
                                        "Set the thickness of the detector in mm");
    fMessenger->DeclarePropertyWithUnit("detectorArea",
                                        "mm2",
                                        fconfig->detectorArea,
                                    "Set the area of the detector in mm^2");
    fMessenger->DeclarePropertyWithUnit("sampleSize",
                                    "mm",
                                    fconfig->sampleMaterialSize,
                                    "Set the sample size");
    fMessenger->DeclareProperty("fileName",fconfig->outputFileName,"Set the output file name");
    fMessenger->DeclareProperty("worldmat",fconfig->worldMaterial,"Set Material for world");
    fMessenger->DeclarePropertyWithUnit("focalspotdiameter",
                                        "mm",
                                        fconfig->focalspotdiameter,
                                        "Set the diameter of the focal spot in mm");
                                        
    
    
    fMessenger->DeclarePropertyWithUnit("sampleToCollimatorDistance",
                                        "mm",
                                        fconfig->sampleToCollimatorDistance ,
                                        "Set the distance between the source and the collimatory in mm");

    fMessenger->DeclarePropertyWithUnit("sourceCollimatoryDiameter",
                                        "mm",
                                        fconfig->sourceCollimatoryDiameter,
                                        "Set the diameter of the source collimatory in mm");


    
    
    addSampleElementCmd=new G4UIcmdWithAString("/xrf/addSampleElement",this);


    //detector collimator configuration
    fMessenger->DeclareProperty("detectorCollimatorIsEnabled",fconfig->detectorCollimatorIsEnabled,"Set if the detector collimator is enabled");
    fMessenger->DeclareProperty("detectorCollimatorIsCustom",fconfig->detectorCollimatorIsCustom,"Set if the detector collimator is custom defined");
    fMessenger->DeclareProperty("detectorCollimatorMaterial",fconfig->detectorCollimatorMaterial,"Set the material of the detector collimator");
    
    fMessenger->DeclarePropertyWithUnit("sampleToDetectorCollimatorDistance",
                                        "mm",
                                        fconfig->sampleToDetectorCollimatorDistance,
                                        "Set the distance between the sample and the detector collimator in mm");
    fMessenger->DeclarePropertyWithUnit("detectorCollimatoryAngleFromSample",
                                        "deg",
                                        fconfig->detectorCollimatorAnlgeFromSample,
                                        "Set the angle of the detector collimator from the sample in deg");

    
    fMessenger->DeclarePropertyWithUnit("detectorCollimatorDensity",
                                        "g/cm3",
                                        fconfig->detectorCollimatorDensity,
                                        "Set the density of the detector collimator in g/cm3");                                  


    fMessenger->DeclarePropertyWithUnit("detectorCollimatorThickness",
                                        "mm",
                                        fconfig->detectorCollimatorThickness,
                                        "Set the thickness of the detector collimator in mm");

                                        
    fMessenger->DeclarePropertyWithUnit("detectorCollimatorOuterRadius",
                                        "mm",
                                        fconfig->detectorCollimatorOuterRadius,
                                        "Set the outer radius of the detector collimator in mm");
    fMessenger->DeclarePropertyWithUnit("detectorCollimatorInnerRadius",
                                        "mm",
                                        fconfig->detectorCollimatorInnerRadius,
                                        "Set the inner radius of the detector collimator in mm");   

    


        
    };







void SimulationMessenger::SetNewValue(G4UIcommand*,G4String newvalue){

    std::istringstream iss(newvalue);
    G4String elementName;
    G4double fraction;
    iss>>elementName>>fraction;

    fconfig->sampleComposion.push_back({elementName,fraction});

}

SimulationMessenger::~SimulationMessenger(){
    delete fAddShieldLayerCmd;
    delete fMessenger;
}   