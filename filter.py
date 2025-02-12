#!/usr/bin/env python3

import json
import sys
import re

sys.stdin.reconfigure(encoding='utf-8') # for windows 

image, formula, table, code, section = 0, 0, 0, 0, [0, 0, 0]
E, W = "ОШИБКА: ", "ПРЕДУПРЕЖДЕНИЕ: "
SP = [{'t' : 'Space'}]

unnumbered = True
HEADERSEP = ' '

hdlis = [ 'АННОТАЦИЯ', 'ВВЕДЕНИЕ', 'ЗАКЛЮЧЕНИЕ', 'ВЫВОДЫ', 'СПИСОК-ИСПОЛЬЗОВАННЫХ-ИСТОЧНИКОВ' ]

body = json.loads(input())
blocks = body['blocks']

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def str2pd(str_to_pandoc):
    def intersperse(lst, item):
        result = [item] * (len(lst) * 2 - 1)
        result[0::2] = lst
        return result
    return intersperse(list(map(
        lambda x: {'t': 'Str', 'c': x},
        list(filter(lambda x: x != '', re.split('[\t\n\r ]', str_to_pandoc))))),
                       {'t': 'Space'})

def section_inc (index):
    if index <= 1:
        global image, formula, table, code
        image, formula, table, code = 0, 0, 0, 0
    global section
    section[index-1] += 1
    section[index:] = [0]*len(section[index:])

def section_str (index):
    return str(section[0]) if index <= 1 else section_str(index-1)+"."+str(section[index-1])

def phrase_list (phrase, listtype, islast):
    if listtype == 'OrderedList':
        inl, start = 'в нумерованном списке ', 'большой (заглавной) '
    else:
        inl, start = 'в маркированном списке ', 'маленькой (строчной) '
    endswith = "пункт заканчивается знаком "

    ender, subender = '.', ';'
    if not islast and listtype != 'OrderedList':
        ender, subender = subender, ender

    if phrase[0]['t'] == 'Plain':
        if phrase[0]['c'][0]['c'][0].islower() and (listtype == 'OrderedList'):
            phrase[0]['c'][0]['c'] = phrase[0]['c'][0]['c'][0].upper() + phrase[0]['c'][0]['c'][1:]
        if phrase[0]['c'][0]['c'][0].isupper() != (listtype == 'OrderedList'):
            eprint(W+inl+'текст должен начинаться с ' + start + 'буквы')

        if phrase[0]['c'][-1]['c'][-1] == subender:
            if islast:
                eprint(W + inl + "последний " + endswith + ender,
                       ", хотя остальных пунктах используется ", subender)
            else:
                eprint(W+inl+"каждый" + endswith + ender,
                       " , а не знаком ", subender)
        elif phrase[0]['c'][-1]['c'][-1] != ender:
            phrase[0]['c'][-1]['c'] += ender
    return phrase

def text_ref (prev, caption, section, figure):
    return str2pd(f'{caption} {section}.{figure} —') + SP + prev

def delete_end_marks (tokens, chars='.?!…\t '):
    for token in tokens[::-1]:
        if token['t'] == 'Str':
            token['c'] = token['c'].rstrip(chars)
            break
    return tokens

def upper_first_token(tokens):
    for token in tokens:
        if token['t'] == 'Str':
            token['c'] = token['c'][0].upper() + token['c'][1:]
            break
    return tokens

def append_reference (mb_text_block, name, section0, num):
    if mb_text_block['t'] == 'Div':
        mb_text_block = mb_text_block['c'][-1][0]
    if mb_text_block['t'] == 'Para':
        delete_end_marks(mb_text_block['c'])
        mb_text_block['c'] += SP + upper_first_token(str2pd(f'({name} {section0}.{num}):'))
        return True
    return False



#for i, b in enumerate(blocks):
i = 0
while i < len(blocks):
    b = blocks[i]

    btype = b['t']
    if btype == 'Header':
        order = b['c'][0]
        refname = b['c'][1][0]
        headerTokens = b['c'][2]
        
        delete_end_marks(headerTokens)

    if btype == 'Header' and order == 1:
        unnumbered = (refname.strip()).upper() in hdlis
        if not unnumbered:
            section_inc(order)
            headerTokens.insert(0, {'t': 'Str', 'c': str(section_str(order)+HEADERSEP)})

        for token in headerTokens:
            if token['t'] == 'Str':
                token['c'] = token['c'].upper()

    if btype == 'Header' and order != 1:
        if unnumbered:
            eprint(E+
                   "Используется заголовок 2 и ниже уровней",
                   b['c'][1],
                   "в ненумерованном разделе (или вовсе вне разделов). \
                           Проверьте структуру разделов.")
            sys.exit(1)

        upper_first_token(headerTokens)

        section_inc(order)
        headerTokens.insert(0, {'t': 'Str', 'c': str(section_str(order)+HEADERSEP)})

    if btype == 'Para':
#        if unnumbered:
#            eprint(E+"Текст или картинка вне раздела \
#                    или в ненумерованном разделе",
#                   b['c'][1],
#                   ". Проверьте структуру разделов.")
#            sys.exit(1)

        for bb in b['c']:
            bbtype = bb['t']
            if bbtype == 'Image':
                image += 1
                b['c'][0]['c'][1] = text_ref(b['c'][0]['c'][1], 'Рисунок', section[0], image) # TODO error if fail
                delete_end_marks(blocks[i-1]['c'])
                blocks[i-1]['c'] += SP + str2pd(f'(Рисунок {section[0]}.{image}):') 

    if btype == 'Table':
        if unnumbered:
            eprint(E+"Таблица вне раздела или в ненумерованном разделе:\n", b['c'], "\nПровертье структуру разделов.")
            sys.exit(1)
        table += 1
        b['c'][1][1][0]['c'] = str2pd(f'Таблица {section[0]}.{table} —') + SP + b['c'][1][1][0]['c']
        if not append_reference(blocks[i-1], 'Таблица', section[0], table):
            eprint(E+"перед таблицей", b['c'],"нет абзаца, в который можно встроить ссылку на таблицу!")
            sys.exit(1)

        blocks[i+1] = {'t':'Div', 'c': [["",[],[['custom-style', 'aftertable']]], [blocks[i+1]]]}

    if btype == 'Figure':
        if unnumbered:
            eprint(E+"Рисунок вне раздела или в ненумерованном разделе:\n", b['c'], "\nПровертье структуру разделов.")
            sys.exit(1)
        image += 1
        b['c'][1][1][0]['c'] = str2pd(f'Рисунок {section[0]}.{image} —') + SP + b['c'][1][1][0]['c']
        
        if not append_reference(blocks[i-1], 'Рисунок', section[0], image):
            eprint(E+"перед рисунком", b['c'], "нет абзаца, в который можно встроить ссылку на рисунок!")
            sys.exit(1)

    if btype == 'CodeBlock':
        if unnumbered:
            eprint(E+"Листинг вне раздела или в ненумерованном разделе:\n", b['c'], "\nПровертье структуру разделов.")
            sys.exit(1)
        if len(b['c'][0][2]) == 0:
            eprint(E+"нет подписи у листинга:\n", b['c'][1], "\nЧТОБЫ ДОБАВИТЬ ПОДПИСЬ, используйте ключ caption:\n~~~{.lang caption=\"Hello world\"}")
            sys.exit(1)

        if not('caption' in dict(b['c'][0][2])):
            eprint(E+"нет подписи у листинга:\n", b['c'][1], "\nЧТОБЫ ДОБАВИТЬ ПОДПИСЬ, используйте ключ caption:\n~~~{.lang caption=\"Hello world\"}")
            sys.exit(1)

        code += 1
        caption = f'Листинг {section[0]}.{code} — ' + dict(b['c'][0][2])['caption']
        if not append_reference(blocks[i-1], 'Листинг', section[0], code):
            eprint(E+"перед листингом", b['c'], "нет абзаца, в который можно встроить ссылку на листинг!")
            sys.exit(1)

        blocks.insert(i, {"t":"Div","c":[["",[],[["custom-style","Code Caption"]]], [{"t":"Para","c":str2pd(caption)}]]})
        i += 1
        blocks[i+1] = {'t':'Div', 'c': [["",[],[['custom-style', 'aftertable']]], [blocks[i+1]]]}
    #   eprint(blocks[i+1])
       # .insert(i, {"t":"Div","c":[["",[],[["custom-style","Code Caption"]]], [{"t":"Para","c":str2pd(caption)}]]})

    if btype == 'BulletList':
        for j, phrase in enumerate(b['c']):
            phrase = phrase_list(phrase, btype, j == (len(b['c']) - 1))

    if btype == 'OrderedList':
        for phrase in b['c'][1]:
            phrase = phrase_list(phrase, btype, False)

    i += 1

body['blocks'] = blocks
print(json.dumps(body))
