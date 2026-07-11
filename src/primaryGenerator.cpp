#include "primaryGenerator.hh"
#include "G4ThreeVector.hh"

PrimaryGenerator::PrimaryGenerator(SimulationConfig& config):fConfig(&config){
    CalulateSourcePositionAndDirection();
    fgun=new G4GeneralParticleSource();
    auto* source = fgun->GetCurrentSource();
    source->GetPosDist()->SetCentreCoords(SourcePosition);
    source->GetPosDist()->SetPosDisType("Plane");
    source->GetPosDist()->SetPosDisShape("Circle");
    source->GetPosDist()->SetRadius(fConfig->focalspotdiameter/2);
    G4double d2=fConfig->sampleToCollimatorDistance ;   
    G4double d1=fConfig->sourceDistance-d2;
 
    fConfig->sampleBeamdiameter=fConfig->sourceCollimatoryDiameter *(d2+d1)/d1;

}

PrimaryGenerator::~PrimaryGenerator(){
    delete fgun;
}

void PrimaryGenerator::CalulateSourcePositionAndDirection(){
    G4double theta = fConfig->incidentAngle;
    G4double distance=fConfig->sourceDistance;

    SourcePosition=G4ThreeVector(-distance*std::cos(theta),
                                     0,
                        distance*std::sin(theta)) ;

    

}

void PrimaryGenerator::GeneratePrimaries(G4Event *event)
{

    G4double randomNumber=fConfig->sampleBeamdiameter/2*std::sqrt(G4UniformRand());
    G4double randomAngle=2*M_PI*G4UniformRand();
    

     G4ThreeVector randomBeamPointOnSample(
        randomNumber*std::sin(randomAngle),
        randomNumber*std::cos(randomAngle), fConfig->sampleMaterialSize.z()/2);

    // G4cout<<"Random Beam Point on Sample: "<<randomBeamPointOnSample/mm<<" mm"<<G4endl;

    fgun->GeneratePrimaryVertex(event);
    G4PrimaryVertex* vertex = event->GetPrimaryVertex(0);
    G4PrimaryParticle* particle = vertex->GetPrimary(0);
    SourcePosition = vertex->GetPosition();
    SourceDirection=randomBeamPointOnSample-SourcePosition;
    // G4cout<<"Source direction before unit "<<SourceDirection<<G4endl;



    // G4cout << "SourcePosition: " << SourcePosition/mm << " mm" << G4endl;
    // G4cout << "SourceDirection: " << SourceDirection << G4endl;
    // G4cout << "SourceDirection magnitude: " << SourceDirection.mag() << G4endl;
    // G4cout << "Random Beam Point on Sample: " <<randomBeamPointOnSample/mm << " mm" << G4endl;


    particle->SetMomentumDirection(SourceDirection.unit());


    // event->GetPrimaryVertex(0)->SetWeight(0.01);
    
}
