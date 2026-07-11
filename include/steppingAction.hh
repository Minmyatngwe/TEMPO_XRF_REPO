#ifndef STEPPINGACTION_HH
#define STEPPINGACTION_HH


#include "G4UserSteppingAction.hh"
#include "G4Step.hh"
#include "simulationConfig.hh"

class SteppingAction : public G4UserSteppingAction {
public:
    SteppingAction(SimulationConfig &config);
    virtual ~SteppingAction();

    virtual void UserSteppingAction(const G4Step* step) override;

    G4double GetCrossSectionPerVolume(G4double energy,G4String processName);

    G4double CalculateDistancePhotonNeedToTravelInSample(G4Track* track);
    private:
    SimulationConfig * fConfig;

};

#endif 