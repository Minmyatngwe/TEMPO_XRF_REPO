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

#include "G4GenericBiasingPhysics.hh"


int main(int argc,char **argv){

    G4UIExecutive *ui{nullptr};
    if (argc == 1) {
        G4cout << "Creating Qt UI..." << G4endl;

        ui = new G4UIExecutive(argc, argv,"OGLSQt");

        G4cout << "Qt UI object created." << G4endl;
        G4cout << "ui->IsGUI() = " << ui->IsGUI() << G4endl;
    }


    #ifdef G4MULTITHREADED
        G4MTRunManager *manager=new G4MTRunManager;
    #else
        G4RunManager *manager=new G4RunManager;
    #endif


    manager->SetUserInitialization(new PhysicsList());

    SimulationConfig config;
    SimulationMessenger messenger(config);

    manager->SetUserInitialization(new DetectorConstruction(config));
    manager->SetUserInitialization(new ActionInitialization(config));

    G4VisManager *vismanger=new G4VisExecutive();
    vismanger->Initialize();
    G4UImanager *uimanager=G4UImanager::GetUIpointer();

    if (ui){
        G4cout << "UI session starts..." << G4endl;
        uimanager->ApplyCommand("/det/useFilter true");
        G4cout << "UI session starts..." << G4endl;
        G4int result=uimanager->ApplyCommand("/control/execute vis.mac");
        G4cout << "Result = " << result << G4endl;
        ui->SessionStart();
    }

    else {
        G4String command = "/control/execute ";
        G4String fileName = argv[1];
        uimanager->ApplyCommand(command + fileName);
    }


    return 0;



}

