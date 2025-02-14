# import json
# import sys
# import re

# body = json.loads(input())
# blocks = body['blocks']

# def eprint(*args, **kwargs):
#     print(*args, file=sys.stderr, **kwargs)

# def str2pd(str_to_pandoc):
#     def intersperse(lst, item):
#         result = [item] * (len(lst) * 2 - 1)
#         result[0::2] = lst
#         return result
#     return intersperse(list(map(
#         lambda x: {'t': 'Str', 'c': x},
#         list(filter(lambda x: x != '', re.split('[\t\n\r ]', str_to_pandoc))))),
#                        {'t': 'Space'})


# def upper_first_token(tokens):
#     for token in tokens:
#         if token['t'] == 'Str':
#             token['c'] = token['c'][0].upper() + token['c'][1:]
#             break
#     return tokens

# def append_reference (mb_text_block, name, section0, num):
#     if mb_text_block['t'] == 'Div':
#         mb_text_block = mb_text_block['c'][-1][0]
#     if mb_text_block['t'] == 'Para':
#         for token in mb_text_block['c'][::-1]:
#             if token['t'] == 'Str':
#                 token['c'] = token['c'].rstrip('.?!…\t ')
#                 break

#         mb_text_block['c'] += [{'t' : 'Space'}] # a space after a paragraph and...
#         + upper_first_token(str2pd(f'({name} {section0}.{num}):'))
#         return True
#     return False



# #for i, b in enumerate(blocks):
# i = 0
# image, formula, table, code, section = 0, 0, 0, 0, [0, 0, 0]
# E, W = "ОШИБКА: ", "ПРЕДУПРЕЖДЕНИЕ: "
# while i < len(blocks):
#     b = blocks[i]
#     btype = b['t']

#     if btype == 'Table':
#         if not append_reference(blocks[i-1], 'Таблица', section[0], table):
#             eprint(E+"перед таблицей", b['c'],"нет абзаца, в который можно встроить ссылку на таблицу!")

#         blocks[i+1] = {'t':'Div', 'c': [["",[],[['custom-style', 'aftertable']]], [blocks[i+1]]]}

#     if btype == 'Figure':
#         if not append_reference(blocks[i-1], 'Рисунок', section[0], image):
#             eprint(E+"перед рисунком", b['c'], "нет абзаца, в который можно встроить ссылку на рисунок!")

#     if btype == 'CodeBlock':
#         if len(b['c'][0][2]) == 0:
#             eprint(E+"нет подписи у листинга:\n", b['c'][1], "\nЧТОБЫ ДОБАВИТЬ ПОДПИСЬ, используйте ключ caption:\n~~~{.lang caption=\"Hello world\"}")

#         if not('caption' in dict(b['c'][0][2])):
#             eprint(E+"нет подписи у листинга:\n", b['c'][1], "\nЧТОБЫ ДОБАВИТЬ ПОДПИСЬ, используйте ключ caption:\n~~~{.lang caption=\"Hello world\"}")

#         code += 1
#         caption = f'Листинг {section[0]}.{code} — ' + dict(b['c'][0][2])['caption']
#         if not append_reference(blocks[i-1], 'Листинг', section[0], code):
#             eprint(E+"перед листингом", b['c'], "нет абзаца, в который можно встроить ссылку на листинг!")

#         blocks.insert(i, {"t":"Div","c":[["",[],[["custom-style","Code Caption"]]], [{"t":"Para","c":str2pd(caption)}]]})
#         i += 1
#         blocks[i+1] = {'t':'Div', 'c': [["",[],[['custom-style', 'aftertable']]], [blocks[i+1]]]}

#     i += 1

# body['blocks'] = blocks
# print(json.dumps(body))
