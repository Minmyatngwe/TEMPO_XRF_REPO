#include <iostream>
#include "G4RunManager.hh"
#include "G4MTRunManager.hh"
#include "G4UImanager.hh"
#include "G4VisExecutive.hh"
#include "G4UIExecutive.hh"

#include "physicsList.hh"
#include "simulationConfig.hh"
#include "simulationMessenger.hh"
#include "detectorConstruction.hh"
#include "actionInitialization.hh"
#include "G4NistManager.hh"
#include "G4UImessenger.hh"
#include "G4UIcommand.hh"
#include "G4GenericMessenger.hh"
#include <filesystem>

#include "G4GenericBiasingPhysics.hh"
#include <fstream>
#include <nlohmann/json.hpp>

using json = nlohmann::json;

int main(int argc,char **argv){

    G4UIExecutive *ui{nullptr};
    if (argc == 2) {
        G4cout << "Creating Qt UI..." << G4endl;

        ui = new G4UIExecutive(argc, argv,"OGLSQt");

        G4cout << "Qt UI object created." << G4endl;
        G4cout << "ui->IsGUI() = " << ui->IsGUI() << G4endl;
    }

    std::string configJsonPath=argv[1];
    std::filesystem::path filePath=argv[1];
    std::filesystem::path updatedJson =filePath.parent_path()/"updated_config.json";

    std::string updatedJsonPath=updatedJson.string();
    std::ifstream configStream(configJsonPath);

    if (!configStream.is_open())
    {
        std::cerr << "Cannot open: " << configJsonPath << "\n";
        return 1;
    }
    json jsonConfig;
    
    configStream>>jsonConfig;



    #ifdef G4MULTITHREADED
        G4MTRunManager *manager=new G4MTRunManager;
    #else
        G4RunManager *manager=new G4RunManager;
    #endif
    
    SimulationConfig config;
    config.LoadFromJson(jsonConfig);
    config.parentFilePath=filePath.parent_path();
    config.Print();



    SimulationMessenger messenger(config);
    manager->SetUserInitialization(new DetectorConstruction(config,jsonConfig,updatedJsonPath));


    manager->SetUserInitialization(new PhysicsList(config));


    manager->SetUserInitialization(new ActionInitialization(config));
    // manager->Initialize();
    G4VisManager *vismanger=new G4VisExecutive();
    vismanger->Initialize();
    G4UImanager *uimanager=G4UImanager::GetUIpointer();

    if (ui){
        config.debug=true;
        G4cout << "UI session starts..." << G4endl;
        G4cout << "UI session starts..." << G4endl;
        G4int result=uimanager->ApplyCommand("/control/execute vis.mac");
        // G4cout << "Result = " << result << G4endl;
        // ui->SessionStart();
    }

    else {
        config.debug=false
        G4String command = "/control/execute ";
        G4String fileName = argv[2];
        uimanager->ApplyCommand(command + fileName);
    }


    return 0;



}

