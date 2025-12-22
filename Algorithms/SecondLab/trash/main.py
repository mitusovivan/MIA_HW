import pandas as pd
import numpy as np
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox, scrolledtext
import re
from collections import Counter
from math import log2

df_global = None
df_original = None
stats = None

COLUMNS_TO_SELECT = ['Пункт Отправления', 'Пункт Назначения', 'Время Отправления', 
                     'Время Прибытия', 'Номер Поезда', 'Вагон-Место', 'Цена', 
                     'Карта', 'Полное ФИО', 'Серия Номер'] 
LOCAL_SUPPRESSION_THRESHOLD = 0.05

def extract_gender(fio):
    if not isinstance(fio, str): return 'Неизвестно'
    parts = fio.split()
    if not parts: return 'Неизвестно'
    if len(parts) >= 3:
        patronymic = parts[2].lower()
        if patronymic.endswith(('вна', 'ична', 'ловна', 'рьевна')): return 'Женский'
        if patronymic.endswith(('вич', 'ич', 'лович', 'рьевич')): return 'Мужской'
    family_name = parts[0].lower()
    if family_name.endswith('а'): return 'Женский'
    return 'Мужской'
    
def generalize_time(time_str):
    if pd.isna(time_str): return 'NaN'
    if isinstance(time_str, str) and 'T' in time_str:
        return '****.**.**T**:**'
    return 'Общее время'

def generalize_price(price):
    if pd.isna(price): return 'NaN'
    try:
        price = int(price)
        if price < 500: return 'до 500'
        if price < 1500: return '500-1500'
        if price < 3000: return '1500-3000'
        return '3000+'
    except:
        return 'Общая цена'

def generalize_card(card_number):
    if pd.isna(card_number) or not isinstance(card_number, str): return 'XXXX'
    card_number = card_number.replace('_', '')
    if len(card_number) >= 4:
        return card_number[:4] + 'XXXXXXXXXXXX'
    return 'XXXX'

def generalize_wagon_place(wagon_place):
    if pd.isna(wagon_place) or not isinstance(wagon_place, str): return 'NaN'
    parts = wagon_place.split('_')
    if len(parts) == 2:
        return 'WAGON_XX' 
    return 'XX_XX'

def mask_passport_number(series_number):
    if pd.isna(series_number) or not isinstance(series_number, str):
        return 'NaN'
    return '****_******'

def add_or_update_k_anonymity_column(df, quasi_identifiers):
    if not quasi_identifiers:
        df['k-anonymity'] = len(df)
        return df

    grouped = df.groupby(quasi_identifiers).size().reset_index(name='k-anonymity')
    
    if 'k-anonymity' in df.columns:
        df = df.drop(columns=['k-anonymity']).merge(grouped, on=quasi_identifiers, how='left')
    else:
        df = df.merge(grouped, on=quasi_identifiers, how='left')
        
    return df.sort_values(by='k-anonymity').reset_index(drop=True)

def remove_worst_k_anonymity_rows(df, max_percent):
    if 'k-anonymity' not in df.columns: return df 

    n_rows_to_remove = int(len(df) * max_percent)
    if n_rows_to_remove == 0: return df
        
    df_sorted = df.sort_values(by='k-anonymity')
    df_trimmed = df_sorted.iloc[n_rows_to_remove:].reset_index(drop=True)
    
    return df_trimmed

def calculate_k_anonymity(dataframe, quasi_identifiers):
    if not quasi_identifiers:
        total_rows = len(dataframe)
        return {'min_k': total_rows, 'max_k': total_rows, 'avg_k': float(total_rows), 'bad_k_count': 0, 'bad_k_percent': 0.0, 'bad_k_list': []}

    try:
        groups = dataframe[quasi_identifiers].value_counts()
    except Exception as e:
        messagebox.showerror("Ошибка расчета K", f"Не удалось рассчитать K-анонимность: {e}")
        return None

    if groups.empty:
        return {'min_k': 0, 'max_k': 0, 'avg_k': 0.0, 'bad_k_count': len(dataframe), 'bad_k_percent': 100.0, 'bad_k_list': []}

    total_rows = len(dataframe)
    min_k = groups.min() 
    max_k = groups.max() 
    avg_k = groups.mean() 
    
    bad_groups = groups[groups == min_k] 
    bad_k_count = bad_groups.sum()
    bad_k_percent = (bad_k_count / total_rows) * 100 if total_rows > 0 else 0.0
    
    bad_k_list = []
    for i, (index, count) in enumerate(bad_groups.head(5).items()):
        qi_values = {qi: val for qi, val in zip(quasi_identifiers, index)}
        bad_k_list.append((int(count), qi_values))

    stats_result = {
        'min_k': int(min_k) if pd.notna(min_k) else 0,
        'max_k': int(max_k) if pd.notna(max_k) else 0,
        'avg_k': avg_k,
        'bad_k_count': int(bad_k_count),
        'bad_k_percent': bad_k_percent,
        'bad_k_list': bad_k_list
    }
    return stats_result

def calculate_kld(df_original, df_anonymized, quasi_identifiers):
    if not quasi_identifiers: return 0.0
    try:
        orig_groups = df_original[quasi_identifiers].apply(lambda x: '_'.join(x.astype(str)), axis=1).value_counts(normalize=True).sort_index()
        anon_groups = df_anonymized[quasi_identifiers].apply(lambda x: '_'.join(x.astype(str)), axis=1).value_counts(normalize=True).sort_index()
        all_keys = orig_groups.index.union(anon_groups.index)
        P_orig = orig_groups.reindex(all_keys, fill_value=0)
        Q_anon = anon_groups.reindex(all_keys, fill_value=0)
        epsilon = 1e-10
        Q_anon = Q_anon.replace(0, epsilon) 
        P_orig = P_orig.replace(0, epsilon)
        kld = (P_orig * np.log2(P_orig / Q_anon)).sum()
        return float(kld)
    except Exception as e:
        print(f"Ошибка при расчете KLD: {e}")
        return -1.0

def apply_anonymization(df_to_anonymize, quasi_identifiers):
    df_anonymized = df_to_anonymize.copy()
    
    if 'Серия Номер' in df_anonymized.columns and 'Серия Номер' in quasi_identifiers:
        df_anonymized['Серия Номер'] = df_anonymized['Серия Номер'].apply(mask_passport_number)

    for qi in quasi_identifiers:
        if qi == 'Время Отправления' or qi == 'Время Прибытия':
            df_anonymized[qi] = df_anonymized[qi].apply(generalize_time)
        elif qi == 'Цена': 
            df_anonymized[qi] = df_anonymized[qi].apply(generalize_price)
        elif qi == 'Карта':
            df_anonymized[qi] = df_anonymized[qi].apply(generalize_card)
        elif qi == 'Вагон-Место':
            df_anonymized[qi] = df_anonymized[qi].apply(generalize_wagon_place) 
        elif qi in ['Пункт Отправления', 'Пункт Назначения', 'Номер Поезда']:
            df_anonymized[qi] = df_anonymized[qi].apply(lambda x: 'Город/Поезд') 
            
    return df_anonymized

def prepare_data_for_anonymization(df_to_prepare):
    if 'Пол' not in df_to_prepare.columns and 'Полное ФИО' in df_to_prepare.columns:
        df_to_prepare['Пол'] = df_to_prepare['Полное ФИО'].apply(extract_gender)
    
    return df_to_prepare.drop(columns=['Полное ФИО'], errors='ignore')

def get_target_k(data_size):
    if data_size <= 51000:
        return 10
    elif data_size <= 105000:
        return 7
    elif data_size <= 260000:
        return 5
    else:
        return 5 

def process_data(attribute_vars):
    global df_global, df_original, stats
    if df_original is None:
        messagebox.showerror("Ошибка", "Сначала загрузите CSV файл.")
        return 
        
    df_original_clean = prepare_data_for_anonymization(df_original.copy())

    selected_qi_raw = [col for col, var in attribute_vars.items() if var.get() == 1]
    
    selected_qi_anon = [qi for qi in selected_qi_raw]
    
    if 'Полное ФИО' in selected_qi_anon:
        selected_qi_anon.remove('Полное ФИО')
        if 'Пол' in df_original_clean.columns:
            selected_qi_anon.append('Пол')
    selected_qi_anon = [qi for qi in selected_qi_anon if qi in df_original_clean.columns]
    
    # K-анонимность рассчитывается по ВСЕМ столбцам, кроме 'k-anonymity', 'Полное ФИО'
    qi_for_k = [col for col in df_original_clean.columns if col != 'k-anonymity' and col != 'Полное ФИО']
    
    if not qi_for_k:
        messagebox.showerror("Ошибка", "Нет столбцов для анализа QI. Загрузите файл с корректными данными.")
        return

    df_anonymized = apply_anonymization(df_original_clean.copy(), selected_qi_anon)
    
    df_with_k = add_or_update_k_anonymity_column(df_anonymized.copy(), qi_for_k)
    
    df_suppressed = remove_worst_k_anonymity_rows(df_with_k, max_percent=LOCAL_SUPPRESSION_THRESHOLD)
    
    suppressed_count = len(df_anonymized) - len(df_suppressed)
    
    df_global = df_suppressed 
    
    stats = calculate_k_anonymity(df_global, qi_for_k)
    if stats is None: return
        
    kld = calculate_kld(df_original_clean, df_global, qi_for_k)
    
    target_k_display = get_target_k(len(df_original))
    
    display_results(stats, qi_for_k, suppressed_count, target_k_display, kld)

def display_results(stats, selected_qi, suppressed_count, target_k, kld_value):
    results_window = tk.Toplevel()
    results_window.title("Результаты K-анонимности и оценки")
    results_window.geometry("700x550")
    results_window.configure(bg="#f4f4f9")

    header_font = ("Arial", 14, "bold")
    text_font = ("Arial", 12)

    tk.Label(results_window, text="Статистика K-анонимности и Обезличивания", font=header_font, bg="#f4f4f9").pack(pady=10)
    
    stats_frame = tk.Frame(results_window, bg="#ffffff", padx=10, pady=10, relief=tk.RIDGE, borderwidth=1)
    stats_frame.pack(pady=5, padx=20, fill='x')

    tk.Label(stats_frame, text=f"Целевое минимальное K (по ТЗ): {target_k}", font=("Arial", 12, "bold"), fg="#005792", bg="#ffffff").pack(anchor=tk.W)

    qi_display_names = [qi if qi != 'Пол' else 'Пол (вместо ФИО)' for qi in selected_qi]
    
    tk.Label(stats_frame, text=f"Квази-идентификаторы (для расчета K): {', '.join(qi_display_names)}", font=text_font, bg="#ffffff").pack(anchor=tk.W)

    tk.Label(stats_frame, text=f"Минимальное K (K-анонимность): {stats['min_k']}", font=text_font, bg="#ffffff").pack(anchor=tk.W)
    tk.Label(stats_frame, text=f"Максимальное K: {stats['max_k']}", font=text_font, bg="#ffffff").pack(anchor=tk.W)
    tk.Label(stats_frame, text=f"Средний размер группы (K): {stats['avg_k']:.2f}", font=text_font, bg="#ffffff").pack(anchor=tk.W)
    tk.Label(stats_frame, text=f"Удалено строк (Local Suppression): {suppressed_count}", font=text_font, fg="#990000", bg="#ffffff").pack(anchor=tk.W)

    tk.Label(results_window, text="Анализ 'Плохих' Групп (K = min_k)", font=header_font, bg="#f4f4f9").pack(pady=10)
    
    bad_frame = tk.Frame(results_window, bg="#ffffff", padx=10, pady=10, relief=tk.RIDGE, borderwidth=1)
    bad_frame.pack(pady=5, padx=20, fill='x')

    tk.Label(bad_frame, text=f"Общее число 'плохих' строк (K={stats['min_k']}): {stats['bad_k_count']}", font=text_font, bg="#ffffff").pack(anchor=tk.W)
    tk.Label(bad_frame, text=f"Процент 'плохих' строк: {stats['bad_k_percent']:.2f}%", font=text_font, bg="#ffffff").pack(anchor=tk.W)

    tk.Label(bad_frame, text="\nТоп-5 Примеров 'Плохих' Групп:", font=("Arial", 11, "italic"), bg="#ffffff").pack(anchor=tk.W)
    if stats['bad_k_list']:
        st = scrolledtext.ScrolledText(bad_frame, wrap=tk.WORD, width=80, height=8, font=("Courier New", 10))
        st.pack(pady=5)
        for count, qi_values in stats['bad_k_list']:
            st.insert(tk.END, f"K={count}: {qi_values}\n")
        st.configure(state='disabled')
    else:
        tk.Label(bad_frame, text="Нет групп с минимальным K.", font=text_font, bg="#ffffff").pack(anchor=tk.W)

    kld_frame = tk.Frame(results_window, bg="#ffffff", padx=10, pady=10, relief=tk.RIDGE, borderwidth=1)
    kld_frame.pack(pady=10, padx=20, fill='x')
    tk.Label(kld_frame, text="Оценка Полезности Данных (KLD)", font=header_font, bg="#ffffff").pack(pady=5)
    
    if kld_value >= 0:
        tk.Label(kld_frame, text=f"Дивергенция Кульбака-Лейблера (KLD): {kld_value:.4f}", font=text_font, bg="#ffffff").pack(anchor=tk.W)
        tk.Label(kld_frame, text="Чем ближе KLD к 0, тем выше полезность данных.", font=("Arial", 10, "italic"), bg="#ffffff").pack(anchor=tk.W)
    else:
        tk.Label(kld_frame, text="Не удалось рассчитать KLD.", font=text_font, fg="#990000", bg="#ffffff").pack(anchor=tk.W)

def load_file(file_label, attribute_vars, process_save_frame):
    global df_original, df_global, COLUMNS_TO_SELECT
    filepath = filedialog.askopenfilename(
        defaultextension=".csv",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
    )
    if not filepath: return
    
    try:
        # 1. Попытка загрузки в UTF-8
        df = pd.read_csv(filepath, sep=';', encoding='utf-8')
    except UnicodeDecodeError:
        try:
            # 2. Попытка загрузки в cp1251 (ANSI) - для поддержки кириллицы
            df = pd.read_csv(filepath, sep=';', encoding='cp1251')
        except Exception as e:
            messagebox.showerror("Ошибка загрузки", f"Не удалось загрузить файл или обработать его (ошибка кодировки или формата): {e}")
            df_original = None
            df_global = None
            return
    except Exception as e:
        messagebox.showerror("Ошибка загрузки", f"Не удалось загрузить файл: {e}")
        df_original = None
        df_global = None
        return

    # Если загрузка прошла успешно
    df_original = df.copy()
    
    df_clean = prepare_data_for_anonymization(df.copy())
    df_global = df_clean.copy()
    
    file_label.config(text=f"Загружен файл: {filepath.split('/')[-1]} ({len(df_original)} строк)", fg="#005792")
    messagebox.showinfo("Успех", "Файл успешно загружен. Выберите квази-идентификаторы.")
    
    # Показываем кнопки обработки и сохранения
    process_save_frame.pack(pady=10, padx=20, fill='x')

def save_file():
    global df_global
    if df_global is None:
        messagebox.showerror("Ошибка", "Нет обезличенных данных для сохранения.")
        return

    filepath = filedialog.asksaveasfilename(
        defaultextension=".csv",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        initialfile="anonymized_data_output.csv"
    )
    
    if filepath:
        try:
            df_to_save = df_global.copy()
            if 'k-anonymity' in df_to_save.columns:
                df_to_save = df_to_save.drop(columns=['k-anonymity'])

            df_to_save.to_csv(filepath, sep=';', index=False, encoding='cp1251')
            
            messagebox.showinfo("Успех", f"Обезличенный датасет сохранен в {filepath}.")
        except Exception as e:
            messagebox.showerror("Ошибка сохранения", f"Не удалось сохранить файл: {e}")

def interface():
    root = tk.Tk()
    root.title("Обезличивание данных и K-анонимность")
    root.geometry("600x650")
    root.configure(bg="#f4f4f9")

    button_style = {'font': ("Arial", 12, "bold"), 'relief': tk.RAISED, 'bd': 2, 'padx': 10, 'pady': 5}
    frame_style = {'bg': "#ffffff", 'relief': tk.GROOVE, 'bd': 2, 'padx': 15, 'pady': 15}

    tk.Label(root, text="Лабораторная работа №2: Обезличивание данных", font=("Arial", 16, "bold"), bg="#f4f4f9").pack(pady=10)

    load_frame = tk.Frame(root, **frame_style)
    load_frame.pack(pady=10, padx=20, fill='x')
    tk.Label(load_frame, text="1. Загрузка данных", font=("Arial", 14, "bold"), bg="#ffffff").pack(anchor=tk.W)
    file_label = tk.Label(load_frame, text="Файл не загружен.", font=("Arial", 12), bg="#ffffff", fg="#990000")
    file_label.pack(pady=10)

    attribute_vars = {} 
    
    process_save_frame = tk.Frame(root, **frame_style) 
    
    load_button = tk.Button(load_frame, text="Загрузить CSV файл (разделитель ';')", 
                            command=lambda: load_file(file_label, attribute_vars, process_save_frame), 
                            **button_style, bg='#007acc', fg="#ffffff")
    load_button.pack(pady=5)
    
    qi_frame = tk.Frame(root, **frame_style)
    qi_frame.pack(pady=10, padx=20, fill='x')
    tk.Label(qi_frame, text="2. Выберите поля для ОБОБЩЕНИЯ:", font=("Arial", 14, "bold"), bg="#ffffff").pack(anchor=tk.W)
    
    columns_to_display = COLUMNS_TO_SELECT 
    
    for attribute in columns_to_display:
        var = tk.IntVar(value=0)
        attribute_vars[attribute] = var
        checkbox = tk.Checkbutton(qi_frame, text=attribute, variable=var, font=("Arial", 12), bg="#ffffff")
        checkbox.pack(anchor=tk.W, padx=10, pady=2)
    
    tk.Label(process_save_frame, text="3. Обработка и Результаты", font=("Arial", 14, "bold"), bg="#ffffff").pack(anchor=tk.W)

    process_button = tk.Button(process_save_frame, text="Обезличить, Подавить и Рассчитать K/KLD", 
                               command=lambda: process_data(attribute_vars), 
                               **button_style, bg='#4CAF50', fg="#ffffff")
    process_button.pack(pady=10)

    save_button = tk.Button(process_save_frame, text="Сохранить Обезличенный Датасет", 
                            command=save_file, 
                            **button_style, bg='#f44336', fg="#ffffff")
    save_button.pack(pady=5)

    root.mainloop()

if __name__ == "__main__":
    interface()
