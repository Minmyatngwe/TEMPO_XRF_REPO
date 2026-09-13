
#ifndef UTILITY_HH
#define UTILITY_HH
#include "G4SystemOfUnits.hh"
#include "G4ThreeVector.hh"

inline G4String toLower(G4String str)
{
    std::transform(str.begin(), str.end(), str.begin(), [](unsigned char c) { return std::tolower(c); });
    return str;
}
#endif 