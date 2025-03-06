global sRuM, sRuW, sEnM, sEnW, total
sRuM = "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"
sRuW = "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"
sEnM = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
sEnW = "abcdefghijklmnopqrstuvwxyz"
total = sRuM + sRuW + sEnM + sEnW

def code():
    s = input('Кодируемое сообщение: ')
    key = input('Ключ: ')
    q = input('Сдвиг кодировки Винжера: ')
    step = int(q) if q.isdigit() else 0
    sw = []
    for i in s:
        if total.find(i) == -1: sw.append((i, 0))
        else: 
            g = max(1 * (sRuM.find(i) + 1), 2 * (sRuW.find(i) + 1), 3 * (sEnM.find(i) + 1), 4 * (sEnW.find(i) + 1))
            sw.append((max(sRuM.find(i), sRuW.find(i), sEnW.find(i), sEnM.find(i)), g // (max(sRuM.find(i), sRuW.find(i), sEnW.find(i), sEnM.find(i)) + 1)))
    #print(sw)
    kw = []
    for i in key:
        if total.find(i) == -1: sw.append(0)
        else: kw.append(max(sRuM.find(i), sRuW.find(i), sEnW.find(i), sEnM.find(i)) + step)
    #print(kw)
    if kw == []: return s
    result = ''
    delta = 0
    for i in range(len(sw)):
        a, b = sw[i]
        if b == 0:
            result += a
            delta += 1
        elif b == 1:result += sRuM[(int(kw[(i - delta) % len(kw)]) + int(a)) % 33]
        elif b == 3: result += sEnM[(int(kw[(i - delta) % len(kw)]) + int(a)) % 26]
        elif b == 2: result += sRuW[(int(kw[(i - delta) % len(kw)]) + int(a)) % 33]
        elif b == 4: result += sEnW[(int(kw[(i - delta) % len(kw)]) + int(a)) % 26]
    return result

def decode():
    s = input('Декодируемое сообщение: ')
    key = input('Ключ: ')
    q = input('Сдвиг кодировки Винжера: ')
    step = int(q) if q.isdigit() else 0
    sw = []
    for i in s:
        if total.find(i) == -1: sw.append((i, 0))
        else: 
            g = max(1 * (sRuM.find(i) + 1), 2 * (sRuW.find(i) + 1), 3 * (sEnM.find(i) + 1), 4 * (sEnW.find(i) + 1))
            sw.append((max(sRuM.find(i), sRuW.find(i), sEnW.find(i), sEnM.find(i)), g // (max(sRuM.find(i), sRuW.find(i), sEnW.find(i), sEnM.find(i)) + 1)))
    #print(sw)
    kw = []
    for i in key:
        if total.find(i) == -1: sw.append(0)
        else: kw.append(max(sRuM.find(i), sRuW.find(i), sEnW.find(i), sEnM.find(i)) + step)
    #print(kw)
    result = ''
    delta = 0

    if kw == []: return s
    for i in range(len(sw)):
        a, b = sw[i]
        if b == 0:
            result += a
            delta += 1
        elif b == 1:
            result += sRuM[(int(a) - int(kw[(i - delta) % len(kw)])) if (int(a) - int(kw[(i - delta) % len(kw)]) >= 0) else 33 + (int(a) - int(kw[(i - delta) % len(kw)]))]
        elif b == 3:
            result += sEnM[(int(a) - int(kw[(i - delta) % len(kw)])) if (int(a) - int(kw[(i - delta) % len(kw)]) >= 0) else 26 + (int(a) - int(kw[(i - delta) % len(kw)]))]
        elif b == 2:
            result += sRuW[(int(a) - int(kw[(i - delta) % len(kw)])) if (int(a) - int(kw[(i - delta) % len(kw)]) >= 0) else 33 + (int(a) - int(kw[(i - delta) % len(kw)]))]
        elif b == 4:
            result += sEnW[(int(a) - int(kw[(i - delta) % len(kw)])) if (int(a) - int(kw[(i - delta) % len(kw)]) >= 0) else 26 + (int(a) - int(kw[(i - delta) % len(kw)]))]
    return result


while True:
    n = input("Введите тип операции: 1 - кодирование, 2 - декодирование: ")
    if n.isdigit():
        if n.count('1') > 0: print(code())
        if n.count('2') > 0: print(decode())




























