#pragma once

#include "globals.hh"
#include "G4ThreeVector.hh"

#include <map>
#include <string>
#include <vector>

class G4Track;

class BrowserTrackExporter
{
    public:
        struct TrackKey
        {
            G4int eventId;
            G4int trackId;

            bool operator<(const TrackKey& other) const
            {
                if (eventId != other.eventId) {
                    return eventId < other.eventId;
                }

                return trackId < other.trackId;
            }
        };

        struct TrackData
        {
            G4int eventId  = -1;
            G4int trackId  = -1;
            G4int parentId = -1;

            G4String particle;

            std::vector<G4ThreeVector> points;
        };

        static BrowserTrackExporter& Instance();

        void Clear();

        void SetMaxEvents(G4int value);

        void RecordStep(
            G4int eventId,
            const G4Track* track,
            const G4ThreeVector& prePosition,
            const G4ThreeVector& postPosition
        );

        void Write(const std::string& filename);

    private:
        BrowserTrackExporter() = default;

        BrowserTrackExporter(
            const BrowserTrackExporter&
        ) = delete;

        BrowserTrackExporter& operator=(
            const BrowserTrackExporter&
        ) = delete;

        std::map<TrackKey, TrackData> tracks;

        // Only export trajectories for the first few events.
        G4int maxEvents = 10;
};