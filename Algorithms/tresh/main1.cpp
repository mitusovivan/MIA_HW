#include "generator.hpp" 
#include "train.hpp" 
#include <iostream>
#include <fstream>      
#include <string>
#include <set>          
#include <iomanip> 
#include <algorithm>

// Коды BOM для UTF-8 (для Excel): 0xEF, 0xBB, 0xBF
const char UTF8_BOM[] = "\xEF\xBB\xBF";

// Функция для преобразования Unix time в читаемый формат
std::string timeToReadable(long long unixTime) {
    // ВНИМАНИЕ: std::put_time работает с локальным временем, 
    // для точности UTC нужно использовать gmtime_r (на *nix) или gmtime_s (на Windows).
    // Для простоты симуляции пока используем time_t и localtime.
    std::time_t t = unixTime;
    std::tm* tm_local = std::localtime(&t);
    
    // Формат: ГГГГ-ММ-ДД ЧЧ:ММ:СС
    std::stringstream ss;
    ss << std::put_time(tm_local, "%Y-%m-%d %H:%M:%S");
    return ss.str();
}


int main() {
    const std::string output_file = "FIO_Passport_Train_List.csv"; // Изменено имя
    const std::string train_file = "trains.csv"; // Имя файла с поездами
    const int number_to_generate = 50000; 

    // Загружаем данные о маршрутах
    mia::RouteMap trainRoutes = mia::loadTrainRoutes(train_file);
    if (trainRoutes.empty()) {
        std::cerr << "Критическая ошибка: Не удалось загрузить данные о поездах. Выход." << std::endl;
        return 1;
    }
    
    // Локальное множество для хранения уже сгенерированных УНИКАЛЬНЫХ номеров
    std::set<std::string> generated_passports; 

    std::ofstream outfile(output_file, std::ios::trunc); 

    if (!outfile.is_open()) {
        std::cerr << "Критическая ошибка: Не удалось открыть файл для записи: " 
                  << output_file << std::endl;
        return 1;
    }
    
    // 1. Записываем BOM для корректной кодировки
    outfile << UTF8_BOM;

    // 2. Записываем заголовок
    outfile << "Полное ФИО;Серия Номер;Номер Поезда;Пункт Отправления;Время Отправления;Пункт Прибытия;Время Прибытия\n"; // <-- ЗАГОЛОВОК ИЗМЕНЕН

    std::cout << "Начинаем генерацию и запись " << number_to_generate 
              << " записей в файл " << output_file << "..." << std::endl;

    for (int i = 0; i < number_to_generate; ++i) {
        
        // --- ПАСПОРТНЫЕ ДАННЫЕ (УНИКАЛЬНОСТЬ СОХРАНЕНА) ---
        std::string fullName = mia::generateFullName();
        std::string fullPassportData;
        
        bool inserted = false;
        do {
            fullPassportData = mia::generatePassportData(); 
            inserted = generated_passports.insert(fullPassportData).second;
        } while (!inserted); 
        
        std::string series = fullPassportData.substr(0, 4);   
        std::string number = fullPassportData.substr(4, 6);   
        // ----------------------------------------------------

        // --- ДАННЫЕ О ПОЕЗДКЕ ---
        mia::TrainRoute selectedRoute;
        std::string departureStation;
        long long arrivalTimeSeconds; // Время прибытия в секундах
        
        // ВАЖНО: trainRoutes передается по ссылке и будет обновляться!
        long long departureTimeSeconds = mia::assignAndGetStartTime(
            trainRoutes, 
            selectedRoute, 
            departureStation, 
            arrivalTimeSeconds);
        
        std::string arrivalStation = selectedRoute.allStops.back(); // Конечный пункт в этой логике - конечный пункт маршрута, 
                                                                    // но функция assignAndGetStartTime должна была бы
                                                                    // вернуть пункт прибытия пассажира.
        // FIX: Функция assignAndGetStartTime не возвращает пункт прибытия пассажира, 
        // но он по логике - следующий после departureStation в allStops.
        // Для упрощения, пока оставим так:
        std::string passengerArrivalStation;
        
        // Находим индекс отправления
        auto it_dep = std::find(selectedRoute.allStops.begin(), selectedRoute.allStops.end(), departureStation);
        // Если станция не последняя, берем следующую как пункт прибытия
        if (it_dep != selectedRoute.allStops.end() && (it_dep + 1) != selectedRoute.allStops.end()) {
             passengerArrivalStation = *(it_dep + 1);
        } else {
             passengerArrivalStation = selectedRoute.endStation; 
        }
        
        // Форматируем время
        std::string departureTimeStr = timeToReadable(departureTimeSeconds);
        std::string arrivalTimeStr = timeToReadable(arrivalTimeSeconds);
        
        // 4. Запись в CSV (ФИО;Серия_Номер;Номер Поезда;Откуда;Время Отпр;Куда;Время Приб)
        outfile << fullName << ";" 
                << series << "_" << number << ";"
                << selectedRoute.routeNumber << ";"
                << departureStation << ";"
                << departureTimeStr << ";"
                << passengerArrivalStation << ";"
                << arrivalTimeStr << "\n";
    }

    std::cout << "Завершено. Проверьте файл " << output_file << std::endl;
    
    return 0;
}