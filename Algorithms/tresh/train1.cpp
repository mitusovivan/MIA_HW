#include "train.hpp"
#include <iostream>
#include <fstream>
#include <sstream>
#include <algorithm>
#include <cstdlib>
#include <ctime>
#include <chrono>
#include <cmath>

using namespace std::chrono;

namespace mia {

// Начальное время для симуляции (01.01.2025 00:00:00 UTC)
const long long START_TIME_BASE = 1735689600LL; 
const int DAY_IN_SECONDS = 86400; // 24 * 60 * 60

/**
 * @brief Вспомогательная функция для инициализации rand()
 */
static void ensureSeeded() {
    static bool seeded = false;
    if (!seeded) {
        std::srand(static_cast<unsigned int>(std::time(0)));
        seeded = true;
    }
}


// --- 1. ЛОГИКА ЗАГРУЗКИ МАРШРУТОВ ИЗ CSV ---
RouteMap loadTrainRoutes(const std::string& filename) {
    RouteMap routes;
    std::ifstream file(filename);

    if (!file.is_open()) {
        std::cerr << "Критическая ошибка: Не удалось открыть файл с поездами: " 
                  << filename << std::endl;
        return routes;
    }

    std::string line;
    // Пропускаем заголовок
    std::getline(file, line); 

    while (std::getline(file, line)) {
        std::stringstream ss(line);
        std::string segment;
        std::vector<std::string> fields;
        
        // Разделяем строку по ';'
        while(std::getline(ss, segment, ',')) {
            fields.push_back(segment);
        }

        if (fields.size() < 6) {
            std::cerr << "Предупреждение: Некорректный формат строки в файле поездов: " 
                      << line << std::endl;
            continue;
        }

        TrainRoute route;
        route.routeNumber = fields[0];
        route.startStation = fields[1];
        route.endStation = fields[3];
        
        // Время в пути, в днях (поля fields[4] и fields[5] соединены в CSV-таблице)
        int travelDays = std::stoi(fields[4]); 
        int travelHours = std::stoi(fields[5]); 
        
        // Переводим в минуты:
        route.travelTimeMinutes = travelDays * 24 * 60 + travelHours * 60; 

        // Парсим промежуточные пункты (field[6] и далее)
        for (size_t i = 6; i < fields.size(); ++i) {
            if (!fields[i].empty()) {
                route.intermediateStations.push_back(fields[i]);
            }
        }
        
        // Формируем список всех остановок
        route.allStops.push_back(route.startStation);
        route.allStops.insert(route.allStops.end(), 
                              route.intermediateStations.begin(), 
                              route.intermediateStations.end());
        route.allStops.push_back(route.endStation);

        // Изначально поезд свободен с базового времени
        route.nextAvailableTime = START_TIME_BASE; 

        routes[route.routeNumber] = route;
    }

    return routes;
}


// --- 2. ЛОГИКА ВЫБОРА РЕЙСА ДЛЯ ПАССАЖИРА ---
long long assignAndGetStartTime(
    RouteMap& routes, 
    TrainRoute& passengerRoute, 
    std::string& outStartStation, 
    long long& outEndTime) 
{
    ensureSeeded();

    // 1. Выбираем случайный поезд (нужно, чтобы Map был непустым)
    if (routes.empty()) {
        throw std::runtime_error("Нет загруженных маршрутов поездов.");
    }
    
    // Получаем случайный итератор
    auto it = routes.begin();
    std::advance(it, std::rand() % routes.size());
    
    // Получаем выбранный маршрут (важно использовать ссылку!)
    passengerRoute = it->second;

    // 2. Выбираем случайный сегмент для пассажира
    
    // Маршрут должен состоять минимум из 2 станций (Начало + Конец)
    if (passengerRoute.allStops.size() < 2) {
        // Такое не должно случиться, если данные корректны, но на всякий случай
        outStartStation = passengerRoute.startStation; 
        long long currentTime = passengerRoute.nextAvailableTime;
        passengerRoute.nextAvailableTime = currentTime + 1; // Занимаем поезд на 1 сек
        outEndTime = passengerRoute.nextAvailableTime;
        return currentTime;
    }
    
    // Выбираем случайную станцию отправления (от 0 до penultimate, не конечная)
    int startIndex = std::rand() % (passengerRoute.allStops.size() - 1);
    
    // Выбираем случайную станцию прибытия (после станции отправления)
    // От startIndex + 1 до последней (index < allStops.size())
    int endIndex = startIndex + 1 + (std::rand() % (passengerRoute.allStops.size() - 1 - startIndex));
    
    outStartStation = passengerRoute.allStops[startIndex];
    std::string endStation = passengerRoute.allStops[endIndex]; // Используем как outEndStation

    // 3. Расчет времени (Ограничение: Промежуточные пункты равномерно делят время)
    
    // Общее количество сегментов пути (Start->End)
    int totalSegments = passengerRoute.allStops.size() - 1; 
    
    // Время на один сегмент (в минутах)
    double timePerSegmentMinutes = (double)passengerRoute.travelTimeMinutes / totalSegments; 
    
    // Количество сегментов, которые проедет пассажир
    int passengerSegments = endIndex - startIndex;
    
    // Время в пути пассажира (в секундах, округляем)
    long long passengerTravelTimeSeconds = (long long)std::round(passengerSegments * timePerSegmentMinutes * 60.0);

    // 4. Определение времени отправления
    // Поезд не может отправиться раньше, чем освободится
    long long departureTime = passengerRoute.nextAvailableTime;
    
    // Можно добавить небольшой случайный сдвиг к departureTime, чтобы рейсы не 
    // отправлялись точно в момент прибытия, но для простоты симуляции пропустим.
    
    // 5. Расчет времени прибытия и обновление nextAvailableTime
    outEndTime = departureTime + passengerTravelTimeSeconds;

    // ОБНОВЛЕНИЕ КЛЮЧЕВОГО ОГРАНИЧЕНИЯ:
    // Поезд будет занят до момента, когда он прибудет на конечную станцию (endStation).
    // То есть, до времени, когда закончится полный маршрут (из startStation в endStation).
    
    // Считаем время полного маршрута в секундах
    long long fullTravelTimeSeconds = (long long)std::round((double)passengerRoute.travelTimeMinutes * 60.0);
    
    // Следующий рейс может начаться только после полного прибытия
    routes[passengerRoute.routeNumber].nextAvailableTime = departureTime + fullTravelTimeSeconds;

    return departureTime;
}

} // namespace mia