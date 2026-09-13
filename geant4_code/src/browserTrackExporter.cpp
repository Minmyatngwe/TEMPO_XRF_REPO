#include "browserTrackExporter.hh"

#include "G4AutoLock.hh"
#include "G4ParticleDefinition.hh"
#include "G4SystemOfUnits.hh"
#include "G4Track.hh"

#include <nlohmann/json.hpp>

#include <fstream>

namespace
{
    G4Mutex browserTrackMutex = G4MUTEX_INITIALIZER;
}


// SINGLETON

BrowserTrackExporter&
BrowserTrackExporter::Instance()
{
    static BrowserTrackExporter instance;
    return instance;
}


void BrowserTrackExporter::Clear()
{
    G4AutoLock lock(&browserTrackMutex);

    tracks.clear();
}

void BrowserTrackExporter::SetMaxEvents(G4int value)
{
    G4AutoLock lock(&browserTrackMutex);

    maxEvents = value;
}

void BrowserTrackExporter::RecordStep(
    G4int eventId,
    const G4Track* track,
    const G4ThreeVector& prePosition,
    const G4ThreeVector& postPosition
)
{
    if (track == nullptr) {
        return;
    }

    G4AutoLock lock(&browserTrackMutex);

    // Do not store trajectories for millions of events.
    if (eventId < 0 || eventId >= maxEvents) {
        return;
    }

    const TrackKey key{
        eventId,
        track->GetTrackID()
    };

    auto& data = tracks[key];

    // First step recorded for this track.
    if (data.points.empty()) {

        data.eventId  = eventId;
        data.trackId  = track->GetTrackID();
        data.parentId = track->GetParentID();

        data.particle =
            track
                ->GetParticleDefinition()
                ->GetParticleName();

        data.points.push_back(prePosition);
    }

    // Avoid storing the same position twice.
    constexpr G4double tolerance2 =
        1e-18 * mm * mm;

    if (
        (data.points.back() - postPosition).mag2()
        > tolerance2
    )
    {
        data.points.push_back(postPosition);
    }
}


// WRITE JSON

void BrowserTrackExporter::Write(
    const std::string& filename
)
{
    G4AutoLock lock(&browserTrackMutex);

    nlohmann::json output;

    output["format"] = "geant4-browser-tracks";
    output["units"]  = "mm";
    output["tracks"] = nlohmann::json::array();

    for (const auto& [key, data] : tracks) {

        if (data.points.size() < 2) {
            continue;
        }

        nlohmann::json trackJson;

        trackJson["eventId"]  = data.eventId;
        trackJson["trackId"]  = data.trackId;
        trackJson["parentId"] = data.parentId;
        trackJson["particle"] = data.particle;
        trackJson["points"]   = nlohmann::json::array();

        for (const auto& point : data.points) {

            trackJson["points"].push_back({
                point.x() / mm,
                point.y() / mm,
                point.z() / mm
            });
        }

        output["tracks"].push_back(
            std::move(trackJson)
        );
    }

    std::ofstream file(filename);

    if (!file) {
        G4cerr
            << "Failed to open browser track file: "
            << filename
            << G4endl;

        return;
    }

    file << output.dump(2);

    G4cout
        << "Browser trajectories exported to: "
        << filename
        << G4endl;
}