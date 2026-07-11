#include "actionInitialization.hh"

#include "primaryGenerator.hh"
#include "runAction.hh"
#include "steppingAction.hh"

ActionInitialization::~ActionInitialization(){}

void ActionInitialization::Build() const{

    SetUserAction(new PrimaryGenerator(*fConfig));
    SetUserAction(new RunAction(*fConfig));
    SetUserAction(new SteppingAction(*fConfig));
    // SetUserAction(new TrackAction());
    // SetUserAction(new EventAction());

}
void ActionInitialization::BuildForMaster() const{

    SetUserAction(new RunAction(*fConfig));

}