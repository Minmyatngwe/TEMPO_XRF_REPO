#include "G4MTRunManager.hh"
#include "G4RunManager.hh"
#include "physicsList.hh"
#include "simulationConfig.hh"
#include <nlohmann/json.hpp>
#include "detectorConstruction.hh"
#include "actionInitialization.hh"
#include "G4UImanager.hh"

#include <iostream>
#include <fstream>
#include <filesystem>
int main(int argc,char **argv){

    #ifdef G4MULTITHREADED
        G4MTRunManager *manager=new G4MTRunManager();
    
    #else
        G4RunManager *manager=new G4RunManager();
    
    #endif 





    std::string configJsonPath=argv[1];
    std::filesystem::path filePath=argv[1];

    std::filesystem::path updateJsonFilepath=filePath.parent_path()/"updated_config.json";


    std::ifstream configStream(configJsonPath);
    if (!configStream.is_open())
    {
        std::cerr << "Cannot open: " << configJsonPath << "\n";
        return 1;
    }

    nlohmann::json jsonConfig;
    configStream>>jsonConfig;

    SimulationConfig config;
    config.LoadFromJson(jsonConfig);
    config.parentFilePath=filePath.parent_path();
    config.Print();
    manager->SetUserInitialization(new DetectorConstruction(config,jsonConfig,updateJsonFilepath));

    manager->SetUserInitialization(new PhysicsList(config));
    manager->SetUserInitialization(new ActionInitialization(&config));
    G4cout << "BEFORE INITIALIZE" << G4endl;


    G4cout << "AFTER INITIALIZE" << G4endl;
    G4cout << "PROGRAM END - NO BEAMON CALLED" << G4endl;    
    G4UImanager * uiManager=G4UImanager::GetUIpointer();

    if(argc==3){
    
        G4String command="/control/execute ";
        uiManager->ApplyCommand(command+argv[2]);

    }
    else if(argc==2){
            manager->Initialize();
            manager->BeamOn(1000);

    }

    delete manager;

    return 0;


}