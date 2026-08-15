#include "actionInitialization.hh"

#include "primaryGenerator.hh"
#include "runAction.hh"
#include "steppingAction.hh"

ActionInitialization::~ActionInitialization(){}

void ActionInitialization::Build() const{

    SetUserAction(new PrimaryGenerator(*fConfig));
    // SetUserAction(new RunAction(*fConfig));
    auto* runAction = new RunAction(*fConfig);

SetUserAction(runAction);

SetUserAction(
    new SteppingAction(*fConfig, runAction)
);
}
void ActionInitialization::BuildForMaster() const{

    SetUserAction(new RunAction(*fConfig));

}