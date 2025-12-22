#include "generator.hpp"
#include "train.hpp"

#include <algorithm> 
#include <cstdlib> 
#include <iomanip>     
#include <iostream>
#include <iomanip>   
#include <fstream>
#include <sstream>
#include <stdexcept> 
#include <windows.h>

struct WagonClass {
    std::string code;
    int minWagon;
    int maxWagon;
    int maxSeat;
};

static const std::vector<WagonClass> allWagonClasses = {
    // a) Поезда «Сапсан»
    {"1P_S", 1, 1, 4},   
    {"1V_S", 1, 1, 48},  
    {"1C_S", 2, 4, 64},  
    {"2C_S", 5, 9, 80}, 
    {"2V_S", 9, 9, 80}, 
    {"2E_S", 10, 10, 32}, 
    // b) Поезда «Стриж»
    {"1E_St", 1, 3, 16}, 
    {"1P_St", 3, 6, 64}, 
    {"2C_St", 6, 12, 80},
    // c) Сидячий вагон (Общие)
    {"1C_G", 1, 2, 64}, 
    {"1P_G", 1, 2, 16}, 
    {"1V_G", 3, 3, 1},  
    {"2P_G", 3, 4, 64}, 
    {"2E_G", 4, 10, 80},
    // d) Плацкартные вагоны
    {"3E_G", 1, 8, 54}, 
    // e) Купе
    {"2E_K", 8, 15, 36},
    // f) Люкс (СВ)
    {"1B_L", 15, 16, 18},  
    {"1L_L", 16, 17, 18},  
    // g) Мягкий вагон
    {"1A_M", 17, 18, 8},   
    {"1I_M", 18, 19, 8}    
};


namespace TrainData {




std::string generateRandomWagonNumber(int trainNumber) {
    std::stringstream ss;
    if (trainNumber >= 751) {
        const WagonClass& selectedClass = allWagonClasses[std::rand() % 6];
        int wagonNum = mia::generateInt(selectedClass.minWagon, selectedClass.maxWagon);
        int seatNum = mia::generateInt(1, selectedClass.maxSeat);

        ss << selectedClass.code << "-" << wagonNum << "_" << seatNum;

    } else if (trainNumber <= 750 && trainNumber >= 710) {
        const WagonClass& selectedClass = allWagonClasses[6 + std::rand() % 3];
        int wagonNum = mia::generateInt(selectedClass.minWagon, selectedClass.maxWagon);
        int seatNum = mia::generateInt(1, selectedClass.maxSeat);

        ss << selectedClass.code << "-" << wagonNum << "_" << seatNum;

        
    }else if (trainNumber <= 710 && trainNumber >= 701){
        const WagonClass& selectedClass = allWagonClasses[6 + std::rand() % 3];
        int wagonNum = mia::generateInt(selectedClass.minWagon, selectedClass.maxWagon);
        int seatNum = mia::generateInt(1, selectedClass.maxSeat);

        ss << selectedClass.code << "-" << wagonNum << "_" << seatNum;
    }else{
        const WagonClass& selectedClass = allWagonClasses[9 + std::rand() % 11];
        int wagonNum = mia::generateInt(selectedClass.minWagon, selectedClass.maxWagon);
        int seatNum = mia::generateInt(1, selectedClass.maxSeat);

        ss << selectedClass.code << "-" << wagonNum << "_" << seatNum;
    }
    return ss.str();
    }

long timeToMinutes(const std::string& travelTimeStr) {
    long totalMinutes = 0;
    size_t d_pos = travelTimeStr.find(" "); 
    if (d_pos != std::string::npos) {

        std::string days_str = travelTimeStr.substr(0, d_pos);
        std::string hour_str = travelTimeStr.substr(d_pos, d_pos + 2);
        std::string minute_str = travelTimeStr.substr(d_pos + 2, d_pos + 4);

        if (!days_str.empty()) {
            int days = std::stoi(days_str);
            totalMinutes += days * 24 * 60 + 
            std::stoi(hour_str) * 60 + std::stoi(minute_str);
        }

    }
    
    return totalMinutes;
}

std::string minutesToTime(long totalMinutes) {
    if (totalMinutes < 0) totalMinutes = 0;

    long minutes = totalMinutes % 60;
    long totalHours = totalMinutes / 60;
    long hours = totalHours % 24;
    long days = totalHours / 24;
    
    std::stringstream ss;
    ss << days << "д " 
       << std::setw(2) << std::setfill('0') << hours << ":"
       << std::setw(2) << std::setfill('0') << minutes;
    
    return ss.str();
}


std::string ansi_to_utf8(const std::string& ansi_str) {
    if (ansi_str.empty()) return {};

    int wlen = MultiByteToWideChar(CP_ACP, 0, ansi_str.c_str(), -1, nullptr, 0);
    if (wlen == 0) return {};
    std::vector<wchar_t> wbuf(wlen);
    MultiByteToWideChar(CP_ACP, 0, ansi_str.c_str(), -1, wbuf.data(), wlen);

    int utf8len = WideCharToMultiByte(CP_UTF8, 0, wbuf.data(), -1, nullptr, 0, nullptr, nullptr);
    if (utf8len == 0) return {};
    std::vector<char> utf8buf(utf8len);
    WideCharToMultiByte(CP_UTF8, 0, wbuf.data(), -1, utf8buf.data(), utf8len, nullptr, nullptr);

    return std::string(utf8buf.data());
}


std::vector<std::string> splitAndTrim(const std::string& str, char delimiter) {
    std::vector<std::string> parts;
    std::stringstream ss(str);
    std::string item;
    while (std::getline(ss, item, delimiter)) {
        item.erase(0, item.find_first_not_of(" \t\r"));
        item.erase(item.find_last_not_of(" \t\r") + 1);
        if (!item.empty()) {
            parts.push_back(item);
        }
    }
    return parts;
}


long timeHHMMToMinutes(const std::string& timeStr) {
    size_t colon_pos = timeStr.find(':');
    if (colon_pos == std::string::npos) return 0;
    
    try {
        std::string cleanStr = timeStr;
        cleanStr.erase(0, cleanStr.find_first_not_of(" \t\r\n"));
        
        int hours = std::stoi(cleanStr.substr(0, colon_pos));
        int minutes = std::stoi(cleanStr.substr(colon_pos + 1));
        return hours * 60 + minutes;
    } catch (...) {
        return 0; 
    }
}

TrainData::AllRoutesMap loadAllTrainRoutes(const std::string& filename) {
    TrainData::AllRoutesMap allRoutes;
    TrainData::AllRoutesMap result;

    std::ifstream file(filename);
    if (!file.is_open()) {
        std::cerr << "Не удалось открыть файл: " << filename << std::endl;
        return result;
    }

    char bom[3];
    if (file.peek() == 0xEF){
        file.read(bom, 3);
    }
    
    std::string header;
    std::getline(file, header);

    std::string line;
    while (std::getline(file, line)) {
        
        if (line.empty() || line.find_first_not_of(" \t\n\r") == std::string::npos) {
            continue; 
        }
        
        std::stringstream ss(line);
        std::string segment;
        
        int trainNumber = -1;
        if (std::getline(ss, segment, ';')) {
            segment.erase(std::remove(segment.begin(), segment.end(), '\r'), segment.end());
            try {
                trainNumber = std::stoi(segment);
            } catch (...) { continue; }
        } else continue;
        
        ParsedRoute route;
        
        std::string departureCity;
        if (!std::getline(ss, departureCity, ';')) continue;
        departureCity.erase(0, departureCity.find_first_not_of(" \t")); 
        departureCity.erase(std::remove(departureCity.begin(), departureCity.end(), '\r'), departureCity.end());
        departureCity = ansi_to_utf8(departureCity);

        std::string initialDepartureTimeStr;
        if (!std::getline(ss, initialDepartureTimeStr, ';')) continue;
        initialDepartureTimeStr.erase(std::remove(initialDepartureTimeStr.begin(), initialDepartureTimeStr.end(), '\r'), initialDepartureTimeStr.end());   
        route.initialDepartureMinutes = timeHHMMToMinutes(initialDepartureTimeStr); 
        
        std::string arrivalCity;
        if (!std::getline(ss, arrivalCity, ';')) continue;
        arrivalCity.erase(0, arrivalCity.find_first_not_of(" \t")); 
        arrivalCity.erase(std::remove(arrivalCity.begin(), arrivalCity.end(), '\r'), arrivalCity.end());
        arrivalCity = ansi_to_utf8(arrivalCity);

        std::string travelTimeStr;
        if (!std::getline(ss, travelTimeStr, ';')) continue;
        route.totalMinutes = timeToMinutes(travelTimeStr);
        if (route.totalMinutes == 0) continue; 

        std::string intermediateStops;
        if (!std::getline(ss, intermediateStops)) continue;
        intermediateStops.erase(std::remove(intermediateStops.begin(), intermediateStops.end(), '\r'), intermediateStops.end()); 
        intermediateStops = ansi_to_utf8(intermediateStops); 

        route.allStops.push_back(departureCity);
        
        std::vector<std::string> intermediateList = splitAndTrim(intermediateStops, ',');
        route.allStops.insert(route.allStops.end(), intermediateList.begin(), intermediateList.end());
        
        route.allStops.push_back(arrivalCity);

        if (route.allStops.size() < 2) continue; 
        
        allRoutes[trainNumber] = route;
    }

    return allRoutes;
}


TrainData::TripSegment generateRandomTrip(const TrainData::AllRoutesMap& allRoutes, int trainNumber) {
    TripSegment result = {trainNumber, "", "", "0д 00:00", "0д 00:00", 0, ""}; 

    auto it = allRoutes.find(trainNumber);
    if (it == allRoutes.end()) {
        std::cerr << "Предупреждение: Маршрут для поезда №" << trainNumber << " не найден." << std::endl;
        return result;
    }

    const ParsedRoute& route = it->second;
    const size_t numStops = route.allStops.size();

    if (numStops < 2) return result; 
    
    int i_start = std::rand() % (numStops - 1);
    int range_size = numStops - 1 - i_start; 
    int i_end = (i_start + 1) + (std::rand() % range_size);

    result.startCity = route.allStops[i_start];
    result.endCity = route.allStops[i_end];

    long N_segments = numStops - 1;
    long totalMinutes = route.totalMinutes;
    result.total_time = totalMinutes;
    long T_segment = totalMinutes / N_segments; 

    long T_absolute_dep = route.initialDepartureMinutes + (long)i_start * T_segment;
    
    long T_absolute_arr = route.initialDepartureMinutes + (long)i_end * T_segment;

    result.curent_time = T_absolute_arr - T_absolute_dep;
    
    result.departureTime = minutesToTime(T_absolute_dep);
    result.arrivalTime = minutesToTime(T_absolute_arr);


    std::string wagon = generateRandomWagonNumber(trainNumber);
    size_t pos = wagon.find("-");
    result.wagonNumber = wagon.substr(pos + 1); 
    result.wagonCode =  wagon.substr(0, pos);  
    
    return result;
}

} 