#pragma once
#include <map>
#include <string>
#include <vector>

namespace TrainData {
    
    struct TripSegment {
        int trainNumber;
        std::string startCity;
        std::string endCity;
        std::string departureTime;
        std::string arrivalTime;  
        long total_time;
        std::string wagonNumber; 
        std::string wagonCode;
        long curent_time;
    };

    std::string generateRandomWagonNumber(int trainNumber); 

    struct ParsedRoute {
        std::vector<std::string> allStops; 
        long totalMinutes; 
        long initialDepartureMinutes;   
    };

    using AllRoutesMap = std::map<int, ParsedRoute>;

    AllRoutesMap loadAllTrainRoutes(const std::string& filename); 
    
    TripSegment generateRandomTrip(const AllRoutesMap& allRoutes, int trainNumber);

}