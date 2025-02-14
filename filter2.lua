IMAGE, FORMULA, TABLE, CODE = 0, 0, 0, 0
UNNUMBERED = true
local hdlis = {
    ['АННОТАЦИЯ'] = true,
    ['ВВЕДЕНИЕ'] = true,
    ['ЗАКЛЮЧЕНИЕ'] = true,
    ['ВЫВОДЫ'] = true,
    ['СПИСОК-ИСПОЛЬЗОВАННЫХ-ИСТОЧНИКОВ'] = true
  }
  
  local section = {0, 0, 0}
  
  local function remove_trailing_punctuation(text)
    return text:gsub("[,;%.!?]+$", "")
  end
  
  local function capitalize_first_letter(text)
    local first_char = pandoc.text.sub(text, 1, 1)
    local rest = pandoc.text.sub(text, 2)
    return pandoc.text.upper(first_char) .. rest
  end
  
  local function is_unnumbered(header_text)
    return hdlis[pandoc.text.upper(header_text)] ~= nil
  end
  
  local function get_section_number(level)
    if level == 1 then
      section[1] = section[1] + 1
      section[2] = 0
      section[3] = 0
      IMAGE = 0

      return tostring(section[1])
    elseif level == 2 then
      if section[1] == 0 then
        io.stderr:write("Ошибка: Второй уровень без первого запрещен\n")
        return nil
      end
      section[2] = section[2] + 1
      section[3] = 0
      return section[1] .. "." .. section[2]
    elseif level >= 3 then
      if section[1] == 0 or section[2] == 0 then
        io.stderr:write("Ошибка: Третий уровень без первого или второго запрещен\n")
        return nil
      end
      section[3] = section[3] + 1
      return section[1] .. "." .. section[2] .. "." .. section[3]
    end
  end
  
  function Header(el)
    local cleaned_text = capitalize_first_letter(remove_trailing_punctuation(pandoc.utils.stringify(el.content)))
    local is_unnumbered_section = is_unnumbered(cleaned_text)
    UNNUMBERED = is_unnumbered_section
    local level = math.min(el.level, 3) -- Принудительно ограничиваем вложенность до 3
  
    if level > 1 and section[1] == 0 then
      io.stderr:write("Ошибка: Заголовки 2 и ниже без нумерованного заголовка 1 уровня\n")
      return el
    end
  
    if not is_unnumbered_section then
      local section_number = get_section_number(level)
      cleaned_text = section_number .. " " .. capitalize_first_letter(cleaned_text)
    elseif level > 1 then
      io.stderr:write("Ошибка: В ненумеруемом разделе не должно быть вложенных заголовков\n")
      return el
    end
  
    el.content = pandoc.Inlines(cleaned_text)
    return el
  end
  


function Figure(el)
    IMAGE = IMAGE + 1
    local str = pandoc.utils.stringify(el.caption)
    str = capitalize_first_letter(str)
    str = remove_trailing_punctuation(str)
    if UNNUMBERED then
        io.stderr:write("Ошибка: Рисунок " .. str .. " в ненумерованном разделе!")
        return el
    end
    str = "Рисунок " .. section[1] .. "." .. IMAGE .. " — " .. str

    el.caption = pandoc.Blocks(str)
    return el
end

function Table(el)
    TABLE = TABLE + 1
    local str = pandoc.utils.stringify(el.caption)
    str = capitalize_first_letter(str)
    str = remove_trailing_punctuation(str)
    if UNNUMBERED then
        io.stderr:write("Ошибка: Таблица " .. str .. " в ненумерованном разделе!")
        return el
    end
    str = "Таблица " .. section[1] .. "." .. IMAGE .. " — " .. str
    el.caption = pandoc.Blocks(str)
    return el
end

--[[ 
  Предполагается, что ранее в фильтре уже определены:
    IMAGE, FORMULA, TABLE, CODE = 0, 0, 0, 0
    UNNUMBERED, hdlis, section
    функции Header, Figure, Table (обрабатывающие подписи и прочее)
  Этот блок добавляет модификацию соседних блоков (предыдущего Para для ссылки,
  а также оборачивание следующего блока для Table и CodeBlock).
--]]

-- Функция для приведения первой буквы строки к заглавной
function capitalize_first_letter(text)
  local first = pandoc.text.sub(text, 1, 1)
  local rest = pandoc.text.sub(text, 2)
  return pandoc.text.upper(first) .. rest
end

-- Функция оборачивает блок в Div с кастомным стилем "aftertable"
function wrap_aftertable(block)
  return pandoc.Div(block, pandoc.Attr("", {}, {["custom-style"] = "aftertable"}))
end

-- Функция, которая ищет в списке блоков блок по индексу index и, если это Para (или вложенный Para в Div),
-- удаляет завершающую пунктуацию у последнего текстового элемента и дописывает ссылку в виде: 
-- " (Тип section.num):"
function append_reference_to_block(blocks, index, ref_name, section_num, num)
  if index < 1 or index > #blocks then
    return false
  end
  local blk = blocks[index]
  -- Если блок – Div, пробуем взять последний вложенный блок из его содержимого
  if blk.t == "Div" then
    if blk.c and #blk.c >= 2 and type(blk.c[2]) == "table" and #blk.c[2] > 0 then
      blk = blk.c[2][#blk.c[2]]
    else
      return false
    end
  end
  if blk.t ~= "Para" then
    return false
  end
  -- Удаляем завершающую пунктуацию у последнего Str
  local inlines = blk.c
  for j = #inlines, 1, -1 do
    if inlines[j].t == "Str" then
      inlines[j].text = inlines[j].text:gsub("[%.?!…%s]+$", "")
      break
    end
  end
  -- Формируем текст ссылки, например: "(Рисунок 1.2):"
  local ref_text = "(" .. ref_name .. " " .. section_num .. "." .. num .. "):"
  ref_text = capitalize_first_letter(ref_text)
  table.insert(inlines, pandoc.Space())
  table.insert(inlines, pandoc.Str(ref_text))
  return true
end

-- Главная функция фильтра, которая проходит по всем блокам документа и в нужных местах
-- модифицирует соседние блоки.
function Pandoc(doc)
  local blocks = doc.blocks
  local i = 1
  while i <= #blocks do
    local blk = blocks[i]
    if blk.t == "Table" then
      -- Для таблиц: добавляем ссылку в предыдущий абзац и оборачиваем следующий блок
      if not append_reference_to_block(blocks, i - 1, "Таблица", section[1], TABLE) then
        io.stderr:write("ОШИБКА: перед таблицей нет абзаца для ссылки\n")
      end
      if i + 1 <= #blocks then
        blocks[i + 1] = wrap_aftertable(blocks[i + 1])
      end
    elseif blk.t == "Figure" then
      -- Для рисунков: добавляем ссылку в предыдущий абзац
      if not append_reference_to_block(blocks, i - 1, "Рисунок", section[1], IMAGE) then
        io.stderr:write("ОШИБКА: перед рисунком нет абзаца для ссылки\n")
      end
    elseif blk.t == "CodeBlock" then
      -- Для листингов: проверяем наличие подписи (caption) в атрибутах
      local attr = blk.attr or {"", {}, {}}
      local attributes = attr[3] or {}
      local caption = attributes.caption
      if not caption then
        io.stderr:write("ОШИБКА: Листинг без подписи!\nИспользуйте ключ caption в CodeBlock\n")
      else
        CODE = CODE + 1
        local ref_text = "Листинг " .. section[1] .. "." .. CODE .. " — " .. caption
        if not append_reference_to_block(blocks, i - 1, "Листинг", section[1], CODE) then
          io.stderr:write("ОШИБКА: перед листингом нет абзаца для ссылки\n")
        end
        -- Вставляем блок с подписью перед текущим CodeBlock.
        local caption_block = pandoc.Div(
          pandoc.Para({ pandoc.Str(capitalize_first_letter(ref_text)) }),
          pandoc.Attr("", {}, {["custom-style"] = "Code Caption"})
        )
        table.insert(blocks, i, caption_block)
        i = i + 1  -- пропускаем вставленный блок
        if i + 1 <= #blocks then
          blocks[i + 1] = wrap_aftertable(blocks[i + 1])
        end
      end
    end
    i = i + 1
  end
  return pandoc.Pandoc(blocks, doc.meta)
end

function Meta(m)
  if m.date == nil then 
    m.date = os.date("%e «%m» %Y")
  end
  return m
end

local function remove_trailing_punctuation_li (li)
  return pandoc.Blocks(remove_trailing_punctuation(pandoc.utils.stringify(li)))
end

local function add_trailing_semicolon_li (li)
  return pandoc.Blocks(pandoc.utils.stringify(li) .. ";")
end

local function add_trailing_stop_li (li)
  return pandoc.Blocks(pandoc.utils.stringify(li) .. ".")
end

local function capitalize_first_letter_li (li)
  return pandoc.Blocks(capitalize_first_letter(pandoc.utils.stringify(li)))
end

local function warnCapitalizedStart (li)
  local str = pandoc.utils.stringify(li)
  local capitalized = capitalize_first_letter(str)
  if str == capitalized
  then
    io.stderr:write("Предупреждение: необходимо исправить вручную. В маркированном списке предложение должно начинаться со строчной (маленькой) буквы. Если текст пункта стартует с аббревиатуры, проигнорируйте данное предупреждение, иначе - исправьте вручную. Текст пункта:\n" .. str)
  end
  
  return li
end

function BulletList(el)
  local li = el.content
  li = pandoc.List.map(li, remove_trailing_punctuation_li)
  li = pandoc.List.map(li, add_trailing_semicolon_li)
  local ending = pandoc.List.at(el.content, -1)
  pandoc.List.remove(li)
  ending = add_trailing_stop_li(remove_trailing_punctuation_li(ending))
  pandoc.List.insert(li, ending)
  li = pandoc.List.map(li, warnCapitalizedStart);
  el.content = li
  return el
end

function OrderedList(el)
  local li = el.content
  li = pandoc.List.map(li, remove_trailing_punctuation_li)
  li = pandoc.List.map(li, add_trailing_stop_li)
  li = pandoc.List.map(li, capitalize_first_letter_li)
  el.content = li
  return el
end