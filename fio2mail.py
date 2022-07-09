#!/usr/bin/env python3
# +++++++++++++++++++++++++++++++++++++++++++
#               fio2mail v1.1
# +++++++++++++++++++++++++++++++++++++++++++
# by vinzekatze
# 
# Для запуска сего скромного микротулза не
# забудьте установить библиотеку "iuliia":
#
#   $ pip3 install iuliia
#
# ... или типо того.

from base64 import encode
from collections import OrderedDict
import fileinput
import re
import iuliia
import argparse

schemes = [iuliia.ALA_LC_ALT, iuliia.BS_2979_ALT, iuliia.GOST_52290, iuliia.GOST_7034, iuliia.ICAO_DOC_9303, iuliia.GOST_779_ALT, iuliia.MOSMETRO, iuliia.TELEGRAM, iuliia.WIKIPEDIA, iuliia.YANDEX_MAPS, iuliia.YANDEX_MONEY, iuliia.GOST_16876_ALT, iuliia.GOST_52535, iuliia.MVD_310, iuliia.MVD_310_FR, iuliia.MVD_782]
defworldlsit = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'r', 's', 't', 'u', 'v', 'y', 'z']
alldicts = [' ',' ',' ',' ']

# описание
mydescription = '''
Скрипт транслитерирует ФИО 16-ю разными стандартами и преобразует в строку по паттерну, задаваемому флагом -p. 
Например, паттерн \'{3}_{1:.1}{2:.1}@example.ru\' преобразует \'Иван Николаевич Городецкий\' в 
    gorodeckii_in@example.ru
    gorodeckij_in@example.ru
    gorodeckijj_in@example.ru
    ...

{1}, {2} и {3} означают номера слов в строке. {1:.1} - только первый символ первого слова.
Если в данных отсутствуют какие-либо составляющие ФИО и не установлен флаг -ng, скрипт будет генерировать все возможные варианты, добавляя одну латинскую букву вместо недостающего слова, либо подставляя значения из соответствующих словарей (-f1, -f2 и -f3), если последние указаны.
'''
# Эпилог
myepilog = '''
Формат входных данных:
Принимает кирилицу и латиницу в перемешку. Транслитерирована будет только кирилица, строки по паттерну будут сгенерированы для всего. Рекомендуется соблюдать последовательность Ф-И-О, так как в большинстве случаев неизвестна и требует подбора именно первая буква отчества. Например:
    Иванов Сергей Николаевич
    Сергеенко Николай
    Matrosov Anton

Можно поставить символ '?' вместо неизвестного слова - скрипт будет его подбирать. Например:
    Александр Сергеевич Пушкин 
    Антон ? Городецкий



Примеры запусков:
    echo 'Сергей Николаевич Иванов\\nАнтон ? Городецкий' | fio2mail.py -p '{3}_{1:.1}{2:.1}@example.ru'
    echo 'Иван Николаевич Городецкий' | fio2mail.py -t
    fio2mail.py -p '{2}.{1}@random.mail' -f names.txt

'''
# Ошибка  
def erroremsg(text):
    print('*** ERROR: ', text)
    quit(1)

# Чтение файла
def readfile(path):
    output = []
    try:
        for line in fileinput.input(path, openhook=fileinput.hook_encoded("utf-8")):
            output.append(line.rstrip())
        output = list(filter(None, output))
    except FileNotFoundError:
        erroremsg(f'Файл {path} не найден')
    except PermissionError:
        erroremsg(f'Нет доступа к {path}')
    except IsADirectoryError:
        erroremsg(f'{path} это директория')
    return output

# Анализ mailsheme
def shemeanalis(mailsheme):
    args = re.findall('{([\d]+?)[\D]',mailsheme)
    args = list(OrderedDict.fromkeys(args))
    args.sort()
    if args == [] or int(max(args)) > 3 or int(min(args)) < 1: erroremsg('Ошибка в паттерне')
    return args

# Отчистка от пустот, добавление вопросиков, приведение ФИО списку
def lineformat(line, maxargs, arglen):
    line.rstrip()
    formatedline = line.split()
    [formatedline.append('?') for j in range(maxargs-len(formatedline))]
    if formatedline.count('?') == arglen: formatedline = ['','','']
    formatedline.insert(0,'')
    return formatedline

# Транслитерация
def tranleterate(datalist):
    translits = []
    for line in datalist :
        for scheme in schemes :
            translits.append(list([re.sub("[^A-Za-z\?\-\_\.\@]", "", iuliia.translate(word, schema=scheme)).lower() for word in line]))
    outdata = []
    for line in translits :
        if line not in outdata :
            outdata.append(line)
    return outdata

# Добавление недостающего имени в столбец agr
def addnames(datalist, arg, wordlist):   
    fios = []
    for line in datalist:
        if line[arg] == '?':
            for name in wordlist:
                line[arg] = name
                fios.append(list(line))
        else:
            fios.append(list(line))
    return fios

# Добавление всех недостоющих имен
def addallnames(formatedline, shemeargs, wordlists) :
    
    newnamelist = [formatedline]
    for arg in shemeargs:
        tempnamelist = []
        tempnamelist.extend(addnames(newnamelist,int(arg),wordlists[int(arg)]))
        newnamelist = tempnamelist
    return newnamelist

# Генерация строк по шаблону
def mailgen(datalist, mailsheme):
    mails = []
    try:
        for line in datalist :
            mails.append(mailsheme.format(*line))
        outdata = list(OrderedDict.fromkeys(mails))
    except Exception:
        erroremsg('Ошибка в паттерне')
    return outdata

# Парсер аргументов командной строки
parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,description=mydescription,epilog=myepilog)
t_or_p = parser.add_mutually_exclusive_group(required=True)
t_or_p.add_argument("-p", metavar='pattern', type=str, help="Паттерн генерации строки. Подается напрямую в функцию format, так что аккуратнее")
t_or_p.add_argument("-t", action="store_true", help="Траслитерация любого текста напрямую без иных преобразований")
parser.add_argument("-f", metavar='FILE', type=str, default='-', help="Читать ФИО из файла. Если не задан, читает stdin, в том числе интерактивно. Но это скорее баг, чем фитча xD")
parser.add_argument("-f1", metavar='FILE', type=str, default='', help="Cписок вариантов для первого слова")
parser.add_argument("-f2", metavar='FILE', type=str, default='', help="Cписок вариантов для второго слова")
parser.add_argument("-f3", metavar='FILE', type=str, default='', help="Cписок вариантов для третьего слова")
parser.add_argument("-o", metavar='FILE', type=str, default='', help="Записать результаты в файл")
parser.add_argument("-ng", action="store_false", help="Не подставлять недостающие имена и инициалы")
args = parser.parse_args()

try:    
    if args.o != '': outfile = open(args.o, 'w', encoding="utf-8")
    if args.t:
        for line in fileinput.input(args.f, openhook=fileinput.hook_encoded("utf-8")):
            if line.rstrip() != '':
                translits = []
                for scheme in schemes:
                        translits.append(iuliia.translate(line, schema=scheme))
                translits = list(OrderedDict.fromkeys(translits))
                for output in translits:
                    output = output.rstrip()
                    print(output)
                    if args.o != '': outfile.write(output + '\n')
    else:
        shemeargs = shemeanalis(args.p)
        maxargs = int(max(shemeargs))
        argslen = len(shemeargs)
        n = 1
        for i in [args.f1, args.f2, args.f3]:  
            if i == '' and args.ng: 
                alldicts[n] = defworldlsit
            elif args.ng:
                alldicts[n] = readfile(i)
            n += 1

        for line in fileinput.input(args.f, openhook=fileinput.hook_encoded("utf-8")):
            if line.rstrip() != '': 
                formatedline = lineformat(line,maxargs,argslen)
                newnamelist = addallnames(formatedline, shemeargs, alldicts)
                transdata = tranleterate(newnamelist)
                mails = mailgen(transdata, args.p)
                mails.sort()
                for output in mails:
                    print(output)
                    if args.o != '': outfile.write(output + '\n')
except KeyboardInterrupt:
    quit(0)
except FileNotFoundError:
    erroremsg(f'Файл {args.f} не найден')
except PermissionError:
    erroremsg(f'Нет доступа к {args.f}')
except IsADirectoryError:
    erroremsg(f'{args.f} это директория')
finally:
    if args.o != '': outfile.close()
