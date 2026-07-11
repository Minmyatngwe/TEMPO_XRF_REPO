#ifndef SIMULATIONMESSAGENGER_HH
#define SIMULATIONMESSAGENGER_HH


#include "G4UImessenger.hh"
#include "G4UIcmdWithADoubleAndUnit.hh"
#include "G4UIcmdWith3VectorAndUnit.hh"
#include "G4UIcmdWithAString.hh"
#include "G4UIcmdWithABool.hh"
#include "simulationConfig.hh"
#include "G4GenericMessenger.hh"
#include "G4UnitsTable.hh"
#include "G4UImessenger.hh"
#include "G4UIcommand.hh"
#include "simulationConfig.hh"


class SimulationMessenger:public G4UImessenger{

    public:
     SimulationMessenger(SimulationConfig& config);;
    ~SimulationMessenger();

    
    private:
        SimulationConfig * fconfig{nullptr};
        G4GenericMessenger *fMessenger{nullptr};
        G4UIcommand* fAddShieldLayerCmd  {nullptr};
        G4UIcmdWithAString *addSampleElementCmd;


        void SetNewValue(G4UIcommand*, G4String) override;
};

#endif