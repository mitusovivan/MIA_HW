#pragma once
#include <string>
#include <vector>
#include <map>

namespace mia {

/**
 * @brief Структура для хранения данных об одном маршруте поезда.
 */
struct TrainRoute {
    std::string routeNumber;    // Номер маршрута (например, "001")
    std::string startStation;   // Начальный пункт
    std::string endStation;     // Конечный пункт
    int travelTimeMinutes;      // Время в пути, в минутах
    std::vector<std::string> intermediateStations; // Промежуточные пункты
    
    // Поле для отслеживания времени, когда поезд СТАНЕТ СВОБОДЕН для следующего рейса.
    // Это ключевое поле для соблюдения ограничения:
    // "поезд не может отправиться, пока не прибудет на конечную".
    long long nextAvailableTime; 

    // Дополнительно: список всех возможных остановок (Start + Intermediate + End)
    std::vector<std::string> allStops;
};


// Тип для хранения всех маршрутов, ключ - номер маршрута.
using RouteMap = std::map<std::string, TrainRoute>;


/**
 * @brief Загружает данные о поездах из CSV-файла.
 * @param filename Имя файла с данными о поездах.
 * @return Карта TrainRoute, где ключ - номер маршрута.
 */
RouteMap loadTrainRoutes(const std::string& filename);


/**
 * @brief Выбирает случайный сегмент пути для пассажира и обновляет доступность поезда.
 * @param routes Карта всех маршрутов.
 * @param passengerRoute Ссылка на выбранный маршрут (для обновления nextAvailableTime).
 * @param outStartStation Ссылка для записи пункта отправления пассажира.
 * @param outEndTime Ссылка для записи времени прибытия пассажира (Unix time, секунды).
 * @return Время отправления пассажира (Unix time, секунды).
 */
long long assignAndGetStartTime(
    RouteMap& routes, 
    TrainRoute& passengerRoute, 
    std::string& outStartStation, 
    long long& outEndTime);

} // namespace mia