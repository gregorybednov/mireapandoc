1. Требуется установить Pandoc

Pandoc - универсальный конвертер документов между различными форматами и разметками.

2. Для того чтобы воспользоваться скриптом, скачайте репозиторий и введите команду:

```
 pandoc --lua-filter=filter2.lua --from markdown --to docx --reference-doc=custom-reference3.docx < отчёт.md > отчёт.docx
 ```

 *Уточнение*. Установка Lua не требуется, так как интерпретатор этого языка программирования "зашит" внутрь Pandoc, хотя сам Pandoc написан на Haskell.

 Программа должна работать в Linux, macOS. По идее, она будет работать и в Windows, но важно сохранить файл .md в кодировке UTF-8.

 3. Есть файл "правила оформления", он частично видоизменен, он неполный, там больший упор на то чего НЕ удалось реализовать в скрипте в автоматическом виде, но на что нужно обратить внимание (odg был создан в libreoffice draw, спокойно конвертируется в PDF).

__ОТКАЗ ОТ ОТВЕТСТВЕННОСТИ__. Программа является всего лишь ИНСТРУМЕНТОМ, и не заменяет голову на плечах, она предоставляется в том виде, в котором она была создана, она гарантированно многого все ещё *не* умеет (например, пока не придумал способ уместить в pandoc создание титульников)

Часть первоначальной версии программы доступна в прошлых ревизиях Git и написана на Python. Текущая версия не требует установки Python в систему (и вообще никаких программ, кроме Pandoc), но была переписана на Lua, возможны регрессии функциональности.