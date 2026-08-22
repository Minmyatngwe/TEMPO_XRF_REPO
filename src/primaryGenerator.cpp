#include "primaryGenerator.hh"
#include "G4ThreeVector.hh"
#include "G4AnalysisManager.hh"

PrimaryGenerator::PrimaryGenerator(SimulationConfig& config):fConfig(&config){
    // CalulateSourcePositionAndDirection();
    fgun=new G4GeneralParticleSource();
    auto* source = fgun->GetCurrentSource();
    auto* posDist = source->GetPosDist();

    // Create a circular focal-spot source centered at the
    // calculated X-ray focal-spot position.

    posDist->SetCentreCoords(fConfig->sourcePosition);
    posDist->SetPosDisType("Plane");
    posDist->SetPosDisShape("Circle");


    source->GetPosDist()->SetRadius(fConfig->focalspotdiameter/2);
    // Direction normal to the focal-spot plane:
    // from the X-ray focal spot toward the sample reference point.

    G4ThreeVector normal =(fConfig->sampleReferencePoint - fConfig->sourcePosition).unit();    G4ThreeVector helperVector(0,1,0);
    if(std::abs(normal.dot(helperVector))>0.99){
        helperVector=G4ThreeVector(1,0,0);
    }
    // Choose a helper vector that is not parallel to the normal.
    // This lets us construct two perpendicular axes lying
    // in the focal-spot plane.

    G4ThreeVector xAxis=helperVector.cross(normal).unit();
    G4ThreeVector yAxis=normal.cross(xAxis).unit();
    posDist->SetPosRot1(xAxis);
    posDist->SetPosRot2(yAxis);

    // Geometrical beam diameter at the sample based on
    // focal-spot-to-collimator and collimator-to-sample distances.
    G4double d1= fConfig->sampleToFocalSpot-fConfig->sampleToTubeCollimatorDistance ;
    G4double d2=fConfig->sampleToTubeCollimatorDistance; 
 
    fConfig->sampleBeamDiameter=fConfig->sourceCollimatorRadius*2 *(d2+d1)/d1;
}

PrimaryGenerator::~PrimaryGenerator(){
    delete fgun;
}

void PrimaryGenerator::GeneratePrimaries(G4Event *event)
{
    // Randomly choose a target point inside the calculated beam footprint
    // on the sample reference plane (world XY plane at Z = 0).
    // The primary photon direction is then set from its randomly sampled
    // focal-spot position toward this target point.


    G4double randomNumber=fConfig->sampleBeamDiameter/2*std::sqrt(G4UniformRand());
    G4double randomAngle=2*M_PI*G4UniformRand();
    

     G4ThreeVector randomBeamPointOnSample(
        randomNumber*std::sin(randomAngle),
        randomNumber*std::cos(randomAngle),0);


    fgun->GeneratePrimaryVertex(event);
    G4PrimaryVertex* vertex = event->GetPrimaryVertex(0);
    G4PrimaryParticle* particle = vertex->GetPrimary(0);
    SourcePosition = vertex->GetPosition();
    SourceDirection=randomBeamPointOnSample-SourcePosition;

    if (fConfig->debug)
    {
        G4cout << G4endl;
        G4cout << "========================================" << G4endl;
        G4cout << "[DEBUG][PRIMARY SOURCE]" << G4endl;
        G4cout << "========================================" << G4endl;

        G4cout
            << "Random point on sample : ("
            << randomBeamPointOnSample.x() / mm << ", "
            << randomBeamPointOnSample.y() / mm << ", "
            << randomBeamPointOnSample.z() / mm
            << ") mm"
            << G4endl;

        G4cout
            << "Source position        : ("
            << SourcePosition.x() / mm << ", "
            << SourcePosition.y() / mm << ", "
            << SourcePosition.z() / mm
            << ") mm"
            << G4endl;

        G4cout
            << "Source direction raw   : ("
            << SourceDirection.x() / mm << ", "
            << SourceDirection.y() / mm << ", "
            << SourceDirection.z() / mm
            << ") mm"
            << G4endl;

        const G4ThreeVector unitDirection =
            SourceDirection.unit();

        G4cout
            << "Momentum direction     : ("
            << unitDirection.x() << ", "
            << unitDirection.y() << ", "
            << unitDirection.z()
            << ")"
            << G4endl;

        G4cout << "========================================" << G4endl;
    }
    particle->SetMomentumDirection(SourceDirection.unit());


    
}
