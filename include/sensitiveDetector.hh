#ifndef SENSITIVEDETECTOR_HH
#define SENSITIVEDETECTOR_HH


#include "G4VSensitiveDetector.hh"
#include "G4SystemOfUnits.hh"
#include "G4UnitsTable.hh"
#include "G4RunManager.hh"
#include <map>
#include "G4AnalysisManager.hh"
#include "simulationConfig.hh"
#include <vector>
#include <algorithm>


class SensitiveDetector:public G4VSensitiveDetector{

    public:
        SensitiveDetector();
        ~SensitiveDetector();
    private:
        G4double fTotalEnergyDeposited;
        G4double energyWeight=1.0;
        virtual void Initialize (G4HCofThisEvent *)override;
        virtual void EndOfEvent(G4HCofThisEvent*)override;
        virtual G4bool ProcessHits(G4Step*,G4TouchableHistory*);    
        std::map<G4int,G4double>energyDepositTrackEnergy;
        std::map<G4int,G4double>energyDepositTrackWeight;
        
};

#endif