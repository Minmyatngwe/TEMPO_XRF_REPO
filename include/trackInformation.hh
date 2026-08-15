#ifndef TRACKINFORMATION_HH
#define TRACKINFORMATION_HH

#include "G4VUserTrackInformation.hh"
#include "globals.hh"

class TrackInformation : public G4VUserTrackInformation {
    public:
        TrackInformation(G4int rootId) : fRootId(rootId) {}
        
        ~TrackInformation() override {} 
        
        virtual void Print() const override {}
        
        G4int GetRootID() const { return fRootId; } 
        
        void SetRootId(G4int rootID){
                fRootId=rootID;
        }
    
    private:
        G4int fRootId{-1};
};

#endif