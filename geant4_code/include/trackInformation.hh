#ifndef TRACKINFORMATION_HH
#define TRACKINFORMATION_HH


#include "G4VUserTrackInformation.hh"
#include "globals.hh"

class TrackInformation:public G4VUserTrackInformation{
    public:
        TrackInformation(G4int rootId):fRootId(rootId){}
        ~TrackInformation()override{}
        G4int GetRootId()const {
            return fRootId;
        }
        void SetRootId(G4int rootId){
            fRootId=rootId;
        }
    private:

        G4int fRootId{-1};
};

#endif 