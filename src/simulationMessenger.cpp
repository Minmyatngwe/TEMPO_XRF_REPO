#include "simulationMessenger.hh"

SimulationMessenger::SimulationMessenger(SimulationConfig& config):fconfig(&config){

    fAddShieldLayerCmd = new G4UIcommand("/xrf/addShieldLayer", this);
    fAddShieldLayerCmd->SetGuidance("Add shield layer: material thickness unit gapbefore unit");

    fMessenger=new G4GenericMessenger(this,"/xrf/","Simulation control commands");
    fMessenger->DeclareProperty("fileName",fconfig->outputFileName,"Set the output file name");
    fMessenger->DeclareProperty("worldmat",fconfig->worldMaterial,"Set Material for world");

};

SimulationMessenger::~SimulationMessenger(){
    delete fAddShieldLayerCmd;
    delete fMessenger;
}   