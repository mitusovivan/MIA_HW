import csv
import sys
from functools import reduce

# --- 1. Исходные данные и конфигурация ---

# 5 известных оригинальных номеров (P_i)
# Это те номера, которые вы предлагаете вычитать из взломанных чисел.
KNOWN_ORIGINAL_NUMBERS = [
    89686432819,
    89057739877,
    89581185764,
    89197414421,
    89689031836
]

INPUT_FILE = 'cracked_numbers_with_offset_full.txt'

# --- 2. Чтение взломанных чисел (Cracked Numbers, C) ---

cracked_numbers = []

print(f"Чтение взломанных чисел из {INPUT_FILE}...")
try:
    with open(INPUT_FILE, 'r') as f:
        reader = csv.reader(f, delimiter=':')
        for row in reader:
            if len(row) < 2:
                continue
            
            # Извлекаем только взломанное число (второй элемент)
            p_str = row[1].strip()
            
            try:
                p = int(p_str)
                cracked_numbers.append(p)
            except ValueError:
                continue
            
except FileNotFoundError:
    print(f"❌ Ошибка: Файл {INPUT_FILE} не найден. Убедитесь, что Hashcat завершил работу.")
    sys.exit()

print(f"✅ Успешно прочитано {len(cracked_numbers)} взломанных чисел.")
if not cracked_numbers:
    sys.exit()

# --- 3. Вычисление 5 Наборов Сдвигов (S_i) ---

# S_i = { c - P_i | для всех c в Cracked_Numbers }
sets_of_diffs = []

print("\n🔍 Вычисление 5 наборов возможных сдвигов (S_i = C - P_i):")
print("-" * 50)

for i, p_original in enumerate(KNOWN_ORIGINAL_NUMBERS):
    # Создаем "копию" данных в виде нового набора сдвигов
    current_diff_set = set()
    for cracked_num in cracked_numbers:
        diff = cracked_num - p_original
        current_diff_set.add(diff)
    
    sets_of_diffs.append(current_diff_set)
    print(f"   > Набор S{i+1} (вычтено {p_original}): {len(current_diff_set)} уникальных сдвигов.")

# --- 4. Нахождение Пересечения ---

# Используем функцию reduce с оператором пересечения (&) для поиска общего элемента
# S_final = S_1 ∩ S_2 ∩ S_3 ∩ S_4 ∩ S_5
print("\n🔍 Вычисление общего пересечения (S_1 ∩ S_2 ∩ S_3 ∩ S_4 ∩ S_5)...")
final_intersection = reduce(set.intersection, sets_of_diffs)

# --- 5. Вывод Результата ---

print("-" * 50)
if len(final_intersection) == 1:
    final_salt = final_intersection.pop()
    print(f"🎉 **Общий Числовой Сдвиг (Соль) найден:** {final_salt}")
    print("Теперь вы можете вычесть эту соль из всех взломанных чисел для получения финальных номеров.")

elif len(final_intersection) > 1:
    print(f"⚠️ **Найдено несколько общих сдвигов ({len(final_intersection)}):**")
    print(final_intersection)
    print("Необходимо дополнительно проверить, какой из них является верным.")

else:
    print("❌ **Общий Числовой Сдвиг (Соль) НЕ НАЙДЕН.**")
    print("Пересечение всех 5 наборов пусто.")
    print("\n   --- Диагностика ---")
    print("   Этот результат подтверждает, что хэш был создан не с помощью 'числового сдвига', а с помощью 'строковой соли', которая приводит к MD5-коллизиям. Необходимо вернуться к поиску строковой соли.")