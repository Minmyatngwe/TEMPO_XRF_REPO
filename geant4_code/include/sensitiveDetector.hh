#ifndef SENSITIVEDETECTOR_HH
#define SENSITIVEDETECTOR_HH
#include "G4VSensitiveDetector.hh"
#include <map>
class SensitiveDetector:public G4VSensitiveDetector{
    public:
        SensitiveDetector();
        ~SensitiveDetector();

    private:
        virtual void Initialize(G4HCofThisEvent *) override;
        virtual void EndOfEvent(G4HCofThisEvent *) override;
        virtual G4bool ProcessHits(G4Step *,G4TouchableHistory*);

        std::map<G4int,G4double>energyDepositTrackWeight;
        std::map<G4int,G4double>energyDepositTrackEnergy;
};

#endif 
