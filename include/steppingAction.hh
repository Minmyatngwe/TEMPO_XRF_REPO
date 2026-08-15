#ifndef STEPPINGACTION_HH
#define STEPPINGACTION_HH


#include "G4UserSteppingAction.hh"
#include "G4Step.hh"
#include "simulationConfig.hh"
class RunAction;

class SteppingAction : public G4UserSteppingAction {
public:
SteppingAction(
    SimulationConfig& config,
    RunAction* runAction
);
    virtual ~SteppingAction();

    virtual void UserSteppingAction(const G4Step* step) override;

    G4double GetCrossSectionPerVolume(G4double energy,G4String processName);

    G4double CalculateDistancePhotonNeedToTravelInSample(G4Track* track);
    private:
    SimulationConfig * fConfig;
    std::map<G4int, G4double> detectorEntryEnergy;
    RunAction* fRunAction = nullptr;
};

#endif 