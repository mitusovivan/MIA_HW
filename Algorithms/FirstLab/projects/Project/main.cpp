#include "generator.hpp" 
#include "train.hpp"     


#include <algorithm>
#include <cctype>   
#include <cstdlib>      
#include <ctime>  
#include <iostream>
#include <fstream>
#include <set>   
#include <sstream>       
#include <string>    
#include <tuple>   
#include <vector>       

   

const char UTF8_BOM[] = "\xEF\xBB\xBF";

static const std::map<std::string, int> allWagonPricesMap = {
    {"1P_S", 100},   // Купе-переговорная (1.00 руб/мин)
    {"1V_S", 90},    // 1 класс (0.90 руб/мин)
    {"1C_S", 80},    // Бизнес-класс (0.80 руб/мин)
    {"2C_S", 65},    // Эконом-класс (0.65 руб/мин)
    {"2V_S", 60},    // Экономический+ (0.60 руб/мин)
    {"2E_S", 60},    // Бистро/Бар 

    {"1E_St", 55},   // Люкс СВ (0.55 руб/мин)
    {"1P_St", 45},   // Купе (0.45 руб/мин)
    {"2C_St", 30},   // Сидячий (0.30 руб/мин)

    {"1C_G", 25},    // Бизнес-класс (0.25 руб/мин)
    {"1P_G", 3},    // Купе (0.20 руб/мин)
    {"1V_G", (6 * 64)},    
    {"2P_G", 5},    
    {"2E_G", 6},    // Эконом сидячий (0.10 руб/мин)

    {"3E_G", 7},     // Плацкарт (0.07 руб/мин)
    {"2E_K", 18},    // Купе (0.18 руб/мин)

    {"1B_L", 50},    // Люкс (СВ)
    {"1L_L", 48},    // Люкс (СВ)

    {"1A_M", 55},    // Мягкий
    {"1I_M", 52}     // Мягкий
};
int getWagonPricePerMinute(const std::string& wagonCode);


int main() {
    
    std::cout << "Введите количество строк, которые необходимо создать:";
    int input;
    std::cin >> input;
    const int number_to_generate = input; 

    std::cout << "Введите вероятность платёжной системы в формате Visa MasterCard Mir:";
    int inputV, inputM, inputW;
    std::cin >> inputV >> inputM >> inputW;
    

    const std::string output_file = "FIO_Passport_Trip_List.csv"; 
    TrainData::AllRoutesMap allTrainRoutes = TrainData::loadAllTrainRoutes("trains.csv");
    std::set<std::string> generated_passports; 
    std::set<std::string> generated_cards; 
    std::ofstream outfile(output_file, std::ios::trunc); 

    std::srand(static_cast<unsigned int>(std::time(0))); 

    std::vector<int> availableTrainNumbers;
    for (const auto& pair : allTrainRoutes) {
        availableTrainNumbers.push_back(pair.first);
    }


    if (!outfile.is_open()) {
        std::cerr << "Критическая ошибка: Не удалось открыть файл для записи: " 
                  << output_file << ". Возможно он уже используется" << std::endl;
        return 1;
    }
    


    using PlaceKey = std::tuple<int, std::string, std::string>;
    std::set<PlaceKey> occupied_places; 

    outfile << UTF8_BOM 
    << "Полное ФИО;Серия Номер;Пункт Отправления;"
    << "Пункт Назначения;Время Отправления;" << 
    "Время Прибытия;Номер Поезда;Вагон-Место;Цена;Карта\n";

    std::cout << "Начинаем генерацию и запись " << number_to_generate 
              << " записей в файл " << output_file << "..." << std::endl;

    for (int i = 0; i < number_to_generate; ++i) {
        
        std::string fullName = mia::generateFullName();

        std::string fullPassportData;
        bool inserted = false;
        do {
            fullPassportData = mia::generatePassportData(); 
            inserted = generated_passports.insert(fullPassportData).second;
        } while (!inserted); 
        std::string series = fullPassportData.substr(0, 4); 
        std::string number = fullPassportData.substr(4, 6); 
        
        int randomTrainIndex = std::rand() % availableTrainNumbers.size();
        int trainNumber = availableTrainNumbers[randomTrainIndex];

                 
        TrainData::TripSegment trip = TrainData::generateRandomTrip(allTrainRoutes, trainNumber);

        inserted = false;
        
        std::string finalDeparture; 
        std::string finalArrival;
        do {
            std::string baseDate = mia::generateDate(2013, 2035, trainNumber, trip.total_time);


            long dep_days = 0;
            std::string dep_time_only = "00:00";
            
            size_t dep_d_pos = trip.departureTime.find("д"); 
            if (dep_d_pos != std::string::npos) {
                std::string days_str = trip.departureTime.substr(0, dep_d_pos);
                try {
                    days_str.erase(std::remove_if(days_str.begin(), days_str.end(), ::isspace), days_str.end());
                    if (!days_str.empty()) {
                        dep_days = std::stol(days_str);
                    }
                } catch (...) { }

                size_t dep_space_pos = trip.departureTime.find(' ', dep_d_pos);
                if (dep_space_pos != std::string::npos) {
                    dep_time_only = trip.departureTime.substr(dep_space_pos + 1, 5); 
                }
            } else {
                dep_time_only = trip.departureTime;
            }


            long arr_days = 0;
            std::string arr_time_only = "00:00";
            
            size_t arr_d_pos = trip.arrivalTime.find("д"); 
            if (arr_d_pos != std::string::npos) {
                std::string days_str = trip.arrivalTime.substr(0, arr_d_pos);
                try {
                    days_str.erase(std::remove_if(days_str.begin(), days_str.end(), ::isspace), days_str.end());
                    if (!days_str.empty()) {
                        arr_days = std::stol(days_str);
                    }
                } catch (...) {  }

                size_t arr_space_pos = trip.arrivalTime.find(' ', arr_d_pos);
                if (arr_space_pos != std::string::npos) {
                    arr_time_only = trip.arrivalTime.substr(arr_space_pos + 1, 5);
                }
            } else {
                arr_time_only = trip.arrivalTime;
            }
            
            std::string finalDepartureDate = mia::returnDate(baseDate, dep_days, dep_time_only);
            std::string finalArrivalDate = mia::returnDate(baseDate, arr_days, arr_time_only);
            
            finalDeparture = finalDepartureDate + "T" + dep_time_only;
            finalArrival = finalArrivalDate + "T" + arr_time_only;

            std::string placeAndWagon;
            PlaceKey currentPlaceKey;

                placeAndWagon = trip.wagonNumber;
                currentPlaceKey = std::make_tuple(trainNumber, baseDate, placeAndWagon);
                
                inserted = occupied_places.insert(currentPlaceKey).second;
            
        } while (!inserted);

        int priceKopecksPerMin = getWagonPricePerMinute(trip.wagonCode);


        long long travelCostKopecks = (long long)priceKopecksPerMin * trip.curent_time;


        long long baseFeeKopecks = 50000; 

        long long finalCostKopecks = travelCostKopecks + baseFeeKopecks;

        int cost = (int)(finalCostKopecks / 100); 
        if (trip.wagonCode == "2E_S") cost += 2000;

        std::string card;

        inserted = false;
        do {
            card = mia::generateBankCardNumber(inputV, inputM, inputW); 
            inserted = generated_cards.insert(card).second;
        } while (!inserted); 

        std::string cardNumber = card + '_';

        outfile << fullName << ";" 
                << series << "_" << number << ";"
                << trip.startCity << ";"           
                << trip.endCity << ";"             
                << finalDeparture << ";"           
                << finalArrival << ";"             
                << trip.trainNumber << ";"          
                << trip.wagonNumber << ";"
                << cost << ";" 
                << cardNumber <<"\n";
            
            if (i % (number_to_generate / 100) == 0) std::cout << (i / (number_to_generate / 100))  << "%" << '\n';
        
        }
    std::cout << "Завершено. Файл " << output_file << " создан." << std::endl;

    return 0;
}


int getWagonPricePerMinute(const std::string& wagonCode) {
    auto it = allWagonPricesMap.find(wagonCode);
    if (it != allWagonPricesMap.end()) {
        return it->second; 
    }
    
    return 5; 
}