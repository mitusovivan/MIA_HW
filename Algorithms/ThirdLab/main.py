import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import csv
from functools import reduce
import hashlib
import random
import os
import subprocess
import tempfile

CSV_DELIMITER = ';'
ENCODING = 'cp1251'
HASHCAT_DIR = 'hashcat-7.1.2'
HASHCAT_EXE = 'hashcat.exe'

class App:
    def __init__(self, master):
        self.master = master
        master.title("Инструмент анализа и деобезличивания")

        self.all_hashes = []
        self.known_pairs = {}
        self.all_data_rows = [] 
        
        self.input_file_path = tk.StringVar()
        self.encryption_input_path = tk.StringVar()
        self.salt_result_var = tk.StringVar()
        self.salt_result_var.set("Соль: не определена")
        
        self._temp_hash_file_path = None
        self._temp_output_file_path = None

        self.notebook = ttk.Notebook(master)
        self.notebook.pack(pady=10, padx=10, expand=True, fill='both')

        self.decryption_tab = ttk.Frame(self.notebook)
        self.encryption_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.decryption_tab, text='Деобезличивание и анализ')
        self.notebook.add(self.encryption_tab, text='Шифрование (Анонимизация)')

        self._setup_decryption()
        self._setup_encryption()

    def log(self, message, field='decryption'):
        if field == 'decryption':
            text_widget = self.status_text
        else:
            text_widget = self.encryption_text
            
        text_widget.config(state=tk.NORMAL)
        text_widget.insert(tk.END, message + "\n")
        text_widget.config(state=tk.DISABLED)
        text_widget.see(tk.END)

    def select_file(self, var):
        filename = filedialog.askopenfilename(
            title="Выберите файл",
            filetypes=(("CSV файлы", "*.csv"), ("Все файлы", "*.*"))
        )
        if filename:
            var.set(filename)

    def _setup_decryption(self):
        frame = ttk.Frame(self.decryption_tab, padding="10")
        frame.pack(expand=True, fill='both')

        ttk.Label(frame, text="1. Исходный файл (data_var. 9.csv):").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        ttk.Entry(frame, textvariable=self.input_file_path, width=40).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(frame, text="Обзор", command=lambda: self.select_file(self.input_file_path)).grid(row=0, column=2, padx=5, pady=5)

        ttk.Label(frame, textvariable=self.salt_result_var, font=('Arial', 10, 'bold')).grid(row=1, column=0, columnspan=3, pady=10)

        ttk.Button(frame, text="Запустить деобезличивание", command=self.run_full_decryption_process).grid(row=2, column=0, columnspan=3, pady=15)
        
        ttk.Label(frame, text="Статус и результаты анализа:").grid(row=3, column=0, padx=5, pady=5, sticky='w')
        self.status_text = tk.Text(frame, height=10, width=65, state=tk.DISABLED)
        self.status_text.grid(row=4, column=0, columnspan=3, padx=5, pady=5)

    def read_data(self, file_path):
        self.all_hashes = []
        self.known_pairs = {}
        self.all_data_rows = []
        
        if not file_path:
            return False

        try:
            with open(file_path, 'r', encoding=ENCODING) as f:
                reader = csv.reader(f, delimiter=CSV_DELIMITER)
                all_rows = list(reader)
                
                if not all_rows:
                    raise ValueError("Файл пуст.")

                self.all_data_rows = all_rows
                
                for row in all_rows[1:]:
                    hash_val = row[0].strip() if len(row) > 0 else ''
                    num_str = row[2].strip() if len(row) > 2 else ''
                    
                    if len(hash_val) == 32: 
                        self.all_hashes.append(hash_val)
                        
                        if num_str.isdigit():
                            # Хеш может повторяться, но в known_pairs он будет уникален,
                            # что корректно для дедупликации известных пар.
                            self.known_pairs[hash_val] = int(num_str)
                        
            if not self.all_hashes:
                raise ValueError("В файле не найдено хешей.")

            self.log(f"Исходный файл прочитан. Найдено хешей: {len(self.all_hashes)}, известных пар: {len(self.known_pairs)}.")
            return True

        except Exception as e:
            self.log(f"Ошибка чтения исходного файла: {e}")
            messagebox.showerror("Ошибка", f"Ошибка чтения исходного файла: {e}")
            return False

    def run_hashcat(self):
        project_root = os.getcwd() 
        hashcat_exe_path = os.path.join(project_root, HASHCAT_DIR, HASHCAT_EXE)
        hashcat_cwd_path = os.path.join(project_root, HASHCAT_DIR)

        unique_hashes = set(self.all_hashes)
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_hash_file:
                for hash_val in unique_hashes:
                    temp_hash_file.write(f"{hash_val}\n")
                self._temp_hash_file_path = temp_hash_file.name
            
            with tempfile.NamedTemporaryFile(mode='r+', delete=False) as temp_output_file:
                self._temp_output_file_path = temp_output_file.name

            self.log(f"Созданы временные файлы.")
            
        except Exception as e:
            self.log(f"Ошибка подготовки временных файлов: {e}")
            return False

        mask = "?d" * 11

        command = [
            hashcat_exe_path, 
            "--potfile-disable", 
            '-a', '3', 
            '-m', '0', 
            '-o', self._temp_output_file_path, 
            self._temp_hash_file_path,
            mask
        ]
        
        self.log("\n--- Запуск Hashcat ---")
        self.log(f"Команда: {os.path.join(HASHCAT_DIR, HASHCAT_EXE)} [абс_путь_in] ... [абс_путь_out]")
        self.log(f"Рабочая директория (CWD): {hashcat_cwd_path}")
        self.salt_result_var.set("Выполняется Hashcat...")
        
        success = False
        try:
            process = subprocess.run(
                command, 
                check=False,
                capture_output=True, 
                text=True,
                cwd=hashcat_cwd_path
            )
            
            if process.returncode == 0:
                self.log("Успешное завершение Hashcat.")
                success = True
            elif 'No devices found/left' in process.stderr:
                self.log("КРИТИЧЕСКАЯ ОШИБКА: Hashcat не смог найти ни одного устройства (ни CPU, ни GPU).")
                self.log("Это проблема вашей системы/драйверов OpenCL/CUDA, а не кода Python.")
                self.log(f"Детали: {process.stderr}")
                messagebox.showerror("Ошибка Hashcat", "No devices found/left. Проверьте драйверы OpenCL/CUDA.")
            else:
                self.log(f"Ошибка выполнения Hashcat (код {process.returncode}).")
                self.log(f"Детали: {process.stderr}")
                messagebox.showerror("Ошибка Hashcat", f"Hashcat завершился с ошибкой:\n{process.stderr}")
                
        except FileNotFoundError:
            self.log(f"Ошибка: Исполняемый файл '{hashcat_exe_path}' не найден. Проверьте путь.")
            messagebox.showerror("Ошибка", f"Исполняемый файл '{hashcat_exe_path}' не найден. Проверьте путь.")
        except Exception as e:
            self.log(f"Непредвиденная ошибка при запуске Hashcat: {e}")
            
        return success

    def read_cracked_numbers(self):
        cracked_numbers = {}
        file_path = self._temp_output_file_path 
        
        if not file_path or not os.path.exists(file_path):
            self.log("Файл результатов Hashcat не найден или не был создан.")
            return None
            
        try:
            # Чтение файла результатов Hashcat
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.read().splitlines()
                for line in lines:
                    parts = line.split(':')
                    if len(parts) >= 2 and parts[1].strip().isdigit():
                        hash_val = parts[0].strip()
                        number = int(parts[1].strip())
                        cracked_numbers[hash_val] = number
            return cracked_numbers
        except Exception as e:
            self.log(f"Ошибка чтения файла результатов Hashcat: {e}")
            return None

    def run_full_decryption_process(self):
        self.log("--- Начало процесса деобезличивания ---")
        input_path = self.input_file_path.get()
        
        if not self.read_data(input_path):
            return

        if not self.run_hashcat():
            self.salt_result_var.set("Ошибка Hashcat!")
            self._cleanup_temp_files()
            return

        cracked_numbers_by_hash = self.read_cracked_numbers()
        self._cleanup_temp_files()
        
        if not cracked_numbers_by_hash:
            self.salt_result_var.set("Результаты Hashcat пусты.")
            return

        # Обновленный вызов для получения соли и минимального числа пар
        final_salt, min_pairs = self.find_salt_and_analyze(cracked_numbers_by_hash)

        if final_salt is None:
            self.salt_result_var.set("Соль не найдена!")
            return

        self.salt_result_var.set(f"Соль найдена: {final_salt} (Мин. пар: {min_pairs})")
        
        decrypted_numbers = []
        
        # Дешифровка номеров
        for hash_val in self.all_hashes:
            if hash_val in cracked_numbers_by_hash:
                salted_num = cracked_numbers_by_hash[hash_val]
                original = salted_num - final_salt
                decrypted_numbers.append(original)
            
        self.save_result(decrypted_numbers)

    def _cleanup_temp_files(self):
        if self._temp_hash_file_path and os.path.exists(self._temp_hash_file_path):
            try:
                os.remove(self._temp_hash_file_path)
            except Exception as e:
                self.log(f"Ошибка при удалении входного временного файла: {e}", field='decryption')
        if self._temp_output_file_path and os.path.exists(self._temp_output_file_path):
            try:
                os.remove(self._temp_output_file_path)
            except Exception as e:
                self.log(f"Ошибка при удалении выходного временного файла: {e}", field='decryption')
        self.log("Временные файлы Hashcat удалены.", field='decryption')

    def find_salt_and_analyze(self, cracked_numbers_by_hash):
        # 1. Подготовка данных
        
        # Все известные оригинальные номера P_i
        unique_original_numbers = list(set(self.known_pairs.values()))
        
        # Все взломанные числа C из результатов Hashcat
        # Используем dict.values() для получения только чисел
        all_cracked_numbers_set = set(cracked_numbers_by_hash.values())
        
        set_of_shifts = []
        
        if not unique_original_numbers or not all_cracked_numbers_set:
            self.log("Недостаточно данных для анализа сдвига.", field='decryption')
            return None, 0

        # 2. Генерация наборов сдвигов S_i = {C - P_i}
        # Использование всего набора C для каждого P_i делает поиск соли надежным.
        for i, original_num in enumerate(unique_original_numbers):
            shifts = set()
            for cracked_num in all_cracked_numbers_set:
                shift = cracked_num - original_num
                shifts.add(shift)
            
            if shifts:
                set_of_shifts.append(shifts)
        
        if not set_of_shifts:
            self.log("Не удалось создать наборы сдвигов.", field='decryption')
            return None, 0
        
        self.log("\n--- Анализ минимального числа пар для определения соли ---", field='decryption')
        
        final_salt = None
        min_pairs = len(set_of_shifts)

        # 3. Нахождение пересечения и минимального числа пар (k)
        current_intersection = set_of_shifts[0]
        
        for num_pairs in range(1, len(set_of_shifts) + 1):
            if num_pairs > 1:
                # Пересечение с предыдущим результатом
                current_intersection = current_intersection.intersection(set_of_shifts[num_pairs-1])
            
            intersection_size = len(current_intersection)
            self.log(f"Пересечение {num_pairs} пар: Размер = {intersection_size}", field='decryption')

            if intersection_size == 1:
                final_salt = current_intersection.pop()
                min_pairs = num_pairs
                break
                
        if final_salt is not None:
            self.log(f"\nМинимальное количество пар для дешифровки: {min_pairs} пары(пар).", field='decryption')
            return final_salt, min_pairs
        else:
            self.log("Ошибка: Общая соль не найдена.", field='decryption')
            # Возвращаем общее количество пар, если соль не найдена
            return None, len(unique_original_numbers) 

    def save_result(self, decrypted_numbers):
        
        output_rows = []
        
        output_rows.append(self.all_data_rows[0])
        
        data_rows = self.all_data_rows[1:]
        
        for i, data_row in enumerate(data_rows):
            new_row = list(data_row)
            
            if i < len(decrypted_numbers):
                original_num = decrypted_numbers[i]
                formatted_num = f"{original_num:011d}"
                
                if len(new_row) > 2:
                    new_row[2] = formatted_num
                else:
                    new_row.extend([''] * (3 - len(new_row)))
                    new_row[2] = formatted_num
                    
                output_rows.append(new_row)

        output_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            initialfile="decrypted_phone_numbers_final.csv",
            title="Сохранить расшифрованные номера"
        )

        if output_path:
            try:
                with open(output_path, 'w', newline='', encoding=ENCODING) as f:
                    writer = csv.writer(f, delimiter=CSV_DELIMITER)
                    writer.writerows(output_rows)
                self.log(f"\nРасшифровка завершена! Номера сохранены в: {output_path}")
                messagebox.showinfo("Готово", f"Расшифровка завершена! Номера сохранены в: {output_path}")
            except Exception as e:
                self.log(f"Ошибка сохранения файла: {e}")
                messagebox.showerror("Ошибка", f"Ошибка сохранения файла: {e}")

    def _setup_encryption(self):
        frame = ttk.Frame(self.encryption_tab, padding="10")
        frame.pack(expand=True, fill='both')

        ttk.Label(frame, text="Файл с исходными (дешифрованными) номерами:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        ttk.Entry(frame, textvariable=self.encryption_input_path, width=40).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(frame, text="Обзор", command=lambda: self.select_file(self.encryption_input_path)).grid(row=0, column=2, padx=5, pady=5)
        
        ttk.Button(frame, text="Зашифровать 3 методами", command=self.run_encryption).grid(row=1, column=0, columnspan=3, pady=15)
        
        self.encryption_text = tk.Text(frame, height=10, width=65, state=tk.DISABLED)
        self.encryption_text.grid(row=2, column=0, columnspan=3, padx=5, pady=5)

    def run_encryption(self):
        self.log("--- Начало процесса шифрования ---", 'encryption')
        input_path = self.encryption_input_path.get()
        
        try:
            with open(input_path, 'r', encoding=ENCODING) as f:
                reader = csv.reader(f, delimiter=CSV_DELIMITER)
                all_rows = list(reader)
                
                if not all_rows:
                     messagebox.showerror("Ошибка", "Файл пуст.")
                     return
                     
                # Считываем старый заголовок
                # header = all_rows[0]
                
                # ИСПРАВЛЕНИЕ: Принудительная установка корректного заголовка
                # Структура CSV: [Хэш, Пусто, Номер телефона]
                correct_header = ['Хэш', '', 'Номер телефона'] 

                data_rows = all_rows[1:]
                
                original_numbers = []
                for row in data_rows:
                    num_str = row[2].strip() if len(row) > 2 else ''
                    if num_str.isdigit() and len(num_str) == 11:
                        original_numbers.append(num_str)
                    else:
                        original_numbers.append('')

        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка чтения исходного файла: {e}")
            return
            
        if not original_numbers or len(original_numbers) != len(data_rows):
            messagebox.showerror("Ошибка", "Проблема с чтением номеров из файла.")
            return

        save_directory = filedialog.askdirectory(title="Выберите папку для сохранения зашифрованных файлов")
        if not save_directory:
            return

        def method_a(num):
            SALT = "MIA_HW_LAB_3"
            return hashlib.md5(f"{num}{SALT}".encode()).hexdigest()

        def method_b(num):
            return hashlib.sha256(num.encode()).hexdigest()
            
        random_salt = random.randint(1000000000, 9999999999) 
        def method_c(num_str):
            try:
                num_int = int(num_str)
                return f"{num_int + random_salt:011d}"
            except ValueError:
                return ""
        
        base_filename = os.path.basename(input_path).replace('.csv', '')

        methods = {
            f"1_MD5_Salted_{base_filename}.csv": (method_a, "MD5 + Строковая Соль"),
            f"2_SHA256_{base_filename}.csv": (method_b, "SHA-256"),
            f"3_NumericShift_Hashcat_{base_filename}.csv": (method_c, f"Числовой Сдвиг (+{random_salt}) (Взламывается Hashcat)"),
        }

        self.log(f"Начало шифрования {len(data_rows)} номеров...", 'encryption')

        for filename, (func, description) in methods.items():
            try:
                # Использование исправленного заголовка
                output_rows = [correct_header]
                
                for i, data_row in enumerate(data_rows):
                    current_num_str = original_numbers[i]
                    
                    if not current_num_str:
                        new_row = list(data_row)
                        output_rows.append(new_row)
                        continue

                    new_encrypted_val = func(current_num_str)
                    
                    new_row = list(data_row)
                    
                    while len(new_row) < 3:
                        new_row.append('')
                        
                    new_row[0] = new_encrypted_val
                    
                    if i < 5:
                        new_row[2] = current_num_str 
                    else:
                        new_row[2] = '' 
                        
                    output_rows.append(new_row)
                
                output_path = os.path.join(save_directory, filename)
                with open(output_path, 'w', newline='', encoding=ENCODING) as f:
                    writer = csv.writer(f, delimiter=CSV_DELIMITER)
                    writer.writerows(output_rows)
                
                self.log(f"Успешно создан: {filename} ({description})", 'encryption')
            except Exception as e:
                self.log(f"Ошибка при шифровании методом {description}: {e}", 'encryption')

        messagebox.showinfo("Готово", "Все 3 зашифрованных файла сохранены.")


if __name__ == '__main__':
    root = tk.Tk()
    app = App(root)
    root.mainloop()
