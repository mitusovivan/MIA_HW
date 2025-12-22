#include "generator.hpp" 
#include <cstdlib> 
#include <ctime>
#include <iomanip>
#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>

 
static const int daysInMonth[] = {0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31};
const int FILE_SIZE = 100;

const int month_year[] = {0, 31, 59, 90, 120, 151, 181, 212, 242, 272, 303, 333, 364, 400}; 

static const std::vector<std::string> russianBins = {
    // МИР (220)
    "2200", "2202", "2204",
    // Visa (4)
    "4000", "4100", "4300", "4567", "4276", "4817", 
    // Mastercard (5)
    "5100", "5200", "5400", "5500",
    // Сбербанк/другие крупные (рандомные)
    "5334", "5469", "5486", "2207", "4279" 
};

int mia::findUseBin(int day){
    
     int low = 0;
    int high = 12;
    int result_index = 0;

    while (low <= high) {
        int mid = low + (high - low) / 2; 

        if (month_year[mid] < day) {
            result_index = mid; 
            low = mid + 1;
        } else {
            high = mid - 1; 
        }
    }
    return result_index + 1;
}

std::string mia::generateBankCardNumber(int V, int M, int W) {
    std::stringstream ss;
    int binIndex;
    std::string selectedBin;
    int res = generateInt(0, (V + M + W)); 

    /*if (res < V) {
        binIndex = generateInt(0, 3);
    } else if (res < V + M) { 
        binIndex = generateInt(3, 6);
    } else { 
        binIndex = generateInt(9, 9); 
    }
    selectedBin = russianBins[binIndex];
    ss << selectedBin;
    */
    binIndex = generateInt(0, russianBins.size() - 1);
    selectedBin = russianBins[binIndex];
    
    ss << selectedBin;
    
    const int remainingDigits = 16 - (int)selectedBin.length(); 
    for (int i = 0; i < remainingDigits; ++i) {
        ss << generateInt(0, 9);
    }
    
    return ss.str();
}

std::string mia::generateDate(int minYear, int maxYear, int train_number, int total_time) {
    std::stringstream ss;
    
    int year = minYear + std::rand() % (maxYear - minYear);
    int month;
    int day;

    if ((train_number < 151) || (298 < train_number < 451) || (598 < train_number)) {
        long iterration = 1 + abs(std::rand() % (365 * (maxYear - minYear)));
        long it_days = (total_time * iterration) / 60 / 24;
        long it_years = it_days / 365;
        
        year = minYear + it_years;
        it_days = it_days % 365;  

        month = mia::findUseBin(it_days);
        day = it_days - month_year[month - 1];

        
    }else if ((180 < train_number < 183) || (138 < train_number < 141)){
        int iterration = 1 + std::rand() % 92;
        while ((total_time * iterration) > (91*24*60)) iterration = 1 + std::rand() % 92;
        
        int it_days = (total_time * iterration) / 60 / 24 - 31;
        if (it_days < 0) it_days += 365;

        month = mia::findUseBin(it_days);

        day = it_days - month_year[month - 1];
    }else{
        int iterration = 1 + std::rand() % 92;
        while ((total_time * iterration) > (91*24*60)) iterration = 1 + std::rand() % 92;

        int it_days = (total_time * iterration) / 60 / 24 + 151;
        month = mia::findUseBin(it_days);
        
        day = it_days - month_year[month - 1];
    }
    
    
    ss << year << "-"
       << std::setw(2) << std::setfill('0') << month << "-"
       << std::setw(2) << std::setfill('0') << day;

    return ss.str();
}



int mia::generateInt(const int a, const int b){
    int result = a + std::rand() % b;
    return result; 
}

std::string mia::generateFullName() {
    
    static bool seeded = false;
    if (!seeded) {
        std::srand(static_cast<unsigned int>(std::time(0)));
        seeded = true;
    }

    int gender = std::rand() % 2; 

    std::string names_file, surnames_file, patronymics_file;

    if (gender == 0) {
         names_file = "men_Names.txt";
        surnames_file = "men_Fam.txt";
        patronymics_file = "men_fNames.txt";
    } else {
        names_file = "wmen_Names.txt";
        surnames_file = "wmen_Fam.txt";
         patronymics_file = "wmen_fNames.txt";
    }

    std::string name = getRandomLineFromFile(names_file);
    std::string surname = getRandomLineFromFile(surnames_file);
    std::string patronymic = getRandomLineFromFile(patronymics_file);

    std::stringstream ss;
    ss << surname << " " << name << " " << patronymic;

    return ss.str();
}


std::string mia::getRandomLineFromFile(const std::string& filename) {
    std::ifstream file(filename);
    
    if (!file.is_open()) {
        std::cerr << "Warning: Не удалось открыть файл: " << filename << std::endl;
        return ""; 
    }

    std::vector<std::string> raw_lines;
    std::string line_buffer;
    while (std::getline(file, line_buffer)) {
        if (!line_buffer.empty()) {
            raw_lines.push_back(line_buffer);
        }
    }
    
    if (raw_lines.empty()) {
        std::cerr << "Warning: Файл пуст: " << filename << std::endl;
        return "";
    }

    int randomIndex = std::rand() % raw_lines.size();
    std::string raw_line = raw_lines[randomIndex];
    
    std::stringstream ss(raw_line);
    
    int dummy_number;
    std::string result;

    if (!(ss >> dummy_number)) {
        std::cerr << "Warning: Ошибка формата строки (нет номера) в файле: " << filename << std::endl;
        return "";
    }

   std::string remaining_line;
    if (std::getline(ss >> std::ws, remaining_line)) { 
        return remaining_line;
    }

    return "";
}



std::string mia::generatePassportData() {
    std::stringstream ss;
    
    int region_code = (std::rand() % 99) + 1; 
    
    int issue_year = std::rand() % 100;
    
    ss << std::setw(2) << std::setfill('0') << region_code
       << std::setw(2) << std::setfill('0') << issue_year;
    
    for (int i = 0; i < 6; ++i) {
        ss << (std::rand() % 10);
    }
    
    return ss.str();
}


std::string mia::returnDate(const std::string& dateStr, long daysToAdd, std::string time) {

    if (daysToAdd == 0) return dateStr;

    int year = std::stoi(dateStr.substr(0, 4));
    int month = std::stoi(dateStr.substr(5, 2));
    int day = std::stoi(dateStr.substr(8, 2));

    day += daysToAdd;

    while (day > daysInMonth[month]) {
        day -= daysInMonth[month];
        month++;
        if (month > 12) {
            month = 1;
            year++;
        }
    }

    std::stringstream ss;
    ss << year << "-"
       << std::setw(2) << std::setfill('0') << month << "-"
       << std::setw(2) << std::setfill('0') << day;

    return ss.str();
}

