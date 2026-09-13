#ifndef STEPTTINGACTION_HH
#define STEPPINGACTION_HH

#include "G4UserSteppingAction.hh"
#include "G4Step.hh"
#include "simulationConfig.hh"
#include "simulationConfig.hh"
#include <map>
#include "runAction.hh"

class SteppingAction:public G4UserSteppingAction{
    public:
        SteppingAction(SimulationConfig & config);

        virtual ~SteppingAction();
        virtual void UserSteppingAction(const G4Step *step) override;

    private:
        SimulationConfig *fConfig;
        std::map<G4int,G4double>detectorEntryEnergy;

};




#endif 