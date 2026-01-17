# Модуль обработки тегов

## Обзор

Система тегов 5etools - это мощный механизм для создания интерактивных cross-references и форматирования текста в JSON данных. Теги имеют синтаксис `{@tagName ...}` и преобразуются в HTML через Renderer.

## Основные компоненты

### 1. Парсинг тегов (render.js:2709-2825)

**splitByTags()** - разделяет строку на части (обычный текст + теги):
- Ищет `{@` и `{=` как начало тега
- Отслеживает вложенность через `tagDepth`
- Возвращает массив частей: `["plain text", "{@tag ...}", "more text"]`

**splitFirstSpace()** - разделяет тег на имя и содержимое:
```javascript
// {@spell fireball|PHB} → ["@spell", "spell fireball|PHB"]
{@tag} → ["@tag", ""]
```

**splitTagByPipe()** - умное разделение по `|` (учитывает вложенные теги):
```javascript
// "{@spell fireball|PHB}" → ["fireball", "PHB"]
// "{@class Fighter|PHB|Eldritch Knight|PHB|2-0}" → ["Fighter", "PHB", "Eldritch Knight", "PHB", "2-0"]
```
- Экранированный `\|` НЕ split-ится
- `|` внутри вложенных `{@...}` НЕ split-ится
- Использует `tagDepth` для отслеживания вложенности

### 2. Рендеринг тегов (render.js:1993-2442)

**_renderString_renderTag()** - главный диспетчер (500+ строк switch statement):

**Стили текста:**
- `@b/@bold` → `<b>...</b>`
- `@i/@italic` → `<i>...</i>`
- `@s/@strike` → `<s>...</s>`
- `@u/@underline` → `<u>...</u>`
- `@sup` → `<sup>...</sup>`
- `@sub` → `<sub>...</sub>`
- `@code` → `<span class="code">...</span>`
- `@style` → `<span class="custom-styles">...</span>` (semicolon-separated styles)
- `@font` → `<span style="font-family: '...'">...</span>` (supports custom fonts)

**Dice теги (через getTagEntry()):**
- `@dice 2d6 + 3` → rollable dice
- `@damage 1d6|fire` → damage roll with type
- `@hit +5` → d20 hit roll
- `@d20` → generic d20 roll
- `@recharge 5` → recharge dice (1d6, success on 5-6)
- `@ability str 16` → ability check
- `@savingThrow dex 4` → saving throw
- `@skillCheck animal_handling 5` → skill check
- `@chance 25` → percentile dice
- `@coinflip` → 1d2 coin flip

**Cross-reference теги (через getTagMeta()):**
- `@spell fireball` → ссылка на заклинание
- `@item longsword` → ссылка на предмет
- `@creature goblin` → ссылка на существо
- `@condition Blinded` → ссылка на состояние
- `@background Acolyte` → ссылка на предысторию
- `@race Elf` → ссылка на расу
- `@class Fighter` → ссылка на класс
- `@feat Sentinel` → ссылка на feat
- И многие другие...

**Специальные теги:**
- `@filter Warlock Spells|spells|level=1;2|class=Warlock` → filtered search link
- `@link Display Text|https://example.com` → external link
- `@5etools Bestiary|bestiary.html` → internal page link
- `@5etoolsImg Character Sheet|pdf/DoSI/Char.pdf` → PDF link
- `@footnote Click|Hover text|Title` → hover tooltip
- `@homebrew NewText|OldText` → homebrew modification marker
- `@area AreaName` → book area reference
- `@loader BrewName|path/to/brew.json|homebrew` → installable homebrew

**Комиксы:**
- `@comic`, `@comicH1`-`@comicH4`, `@comicNote` → comic-style text

**Action tags:**
- `@actSave` → "Strength Saving Throw:"
- `@actSaveSuccess` → "Success:"
- `@actSaveFail` → "Failure:"
- `@actSaveFailBy 5` → "Failure by 5 or More:"
- `@actTrigger` → "Trigger:"
- `@actResponse` → "Response:"

### 3. Meta-система (render.js:5201-6157)

**Renderer.tag классы:**
- Базовый класс: `_TagBase`
- `_TagBaseAt` → `@tagName` format
- `_TagBaseHash` → `#tagName` format
- Каждый тег имеет `tagName`, `defaultSource`, `page`

**TAGS массив (render.js:6000-6137):**
```javascript
static TAGS = [
  new TagBoldShort(),      // @b
  new TagBoldLong(),       // @bold
  new TagSpell(),          // @spell
  new TagItem(),           // @item
  new TagCreature(),       // @creature
  // ... 70+ tag classes
];
```

**TAG_LOOKUP registry:**
```javascript
TAG_LOOKUP["@spell"] = TagSpell instance
TAG_LOOKUP["spell"] = TagSpell instance
```

### 4. Cross-reference resolution (render.js:4648-4920)

**getTagMeta(tag, text)** - возвращает метаданные для ссылки:

**Generic handler (_getTagMeta_generic):**
```javascript
// {@spell fireball|PHB|Display Text}
{
  name: "fireball",
  source: "PHB",
  displayText: "Display Text",
  page: "spells.html",
  hash: "fireball%PHB",
  hashPreEncoded: true
}
```

**Page mappings:**
- `@spell` → `UrlUtil.PG_SPELLS`
- `@item` → `UrlUtil.PG_ITEMS`
- `@creature` → `UrlUtil.PG_BESTIARY`
- `@class` → `UrlUtil.PG_CLASSES`
- `@condition` → `UrlUtil.PG_CONDITIONS_DISEASES`
- И 40+ других...

**Special handling:**

**Creature scaling (render.js:4818-4860):**
```javascript
// {@creature goblin|PHB|scaled=1/8}
// {@creature wolf|PHB|scaledsummon=3}
// {@creature demon|MM|scaledclass=5}
{
  subhashes: [{key: "scaled", value: 0.125}],
  preloadId: "...",
  linkText: "goblin (CR 1/8)"
}
```

**Class features (render.js:4862-4920):**
```javascript
// {@class Fighter|PHB|Eldritch Knight|XPHB|2-0}
{
  hash: "fighter%PHB...",
  subhashes: [{key: "state", value: "..."}],
  subhashesHover: [{key: "state", value: "..."}],
  sourceHover: "XPHB"
}
```

**Deities (render.js:4650-4667):**
```javascript
// {@deity Tempora|Forgotten Realms|PHB}
{
  name: "Tempora",
  pantheon: "Forgotten Realms",
  source: "PHB",
  hash: "tempora%forgotten%20realms%PHB"
}
```

**Cards (render.js:4669-4684):**
```javascript
// {@card card_id|set|source}
{
  name: "card_id",
  source: "source",
  hash: "card_id%set%source",
  isFauxPage: true,
  page: "card"
}
```

### 5. Валидация тегов (test/test-tags.js)

**LinkCheck класс:**
```javascript
static _RE = RegExp({@(tag1|tag2|...)} ([^}]*?)}, "g");
```

**Process:**
1. Сканирует все JSON файлы
2. Находит все теги с defaultSource
3. Вызывает `getTagMeta()` для каждого
4. Проверяет что URL существует в TagTestUrlLookup
5. Reports broken links

**Example:**
```
{@spell nonexistentspell|PHB} → Missing link: spell.html#nonexistentspell%PHB
```

## Поток обработки

**Input → Output:**

```
{@spell fireball|PHB}
↓
splitByTags() → ["{@spell fireball|PHB}"]
↓
splitFirstSpace() → ["@spell", "spell fireball|PHB"]
↓
_renderString_renderTag("@spell", "spell fireball|PHB")
↓
getTagMeta("@spell", "spell fireball|PHB")
↓
{
  name: "fireball",
  source: "PHB",
  page: "spells.html",
  hash: "fireball%PHB"
}
↓
_recursiveRender({type: "link", href: {...}, text: "fireball"})
↓
_renderLink()
↓
<a href="spells.html#fireball%PHB">fireball</a>
```

## Ключевые файлы

- `js/render.js:1970-2825` - Tag parsing and rendering
- `js/render.js:4648-4920` - Cross-reference resolution (getTagMeta)
- `js/render.js:5201-6157` - Renderer.tag class definitions
- `js/render.js:4455-4646` - Dice tag handlers (getTagEntry)
- `test/test-tags.js` - Tag validation

## Статистика

- **~70 тегов** в системе
- **500+ строк** switch statement для рендеринга
- **~600 строк** классов тегов
- **40+ страниц** для cross-references
- **3 формата** dice: простые, modifiers, prompts
- **3 типа** creature scaling: CR, spell summon, class summon

## Архитектурные паттерны

1. **Plugin system** - теги могут быть переопределены плагинами
2. **Recursive rendering** - содержимое тегов рекурсивно рендерится
3. **Faux entries** - теги создают временные объекты для рендеринга
4. **String-based DSL** - все теги - строки в JSON
5. **Central registry** - TAG_LOOKUP для всех тегов
6. **Switch statement** - dispatch pattern для обработки
7. **Pipe syntax** - параметры разделены | (как UNIX pipes)
8. **Hash encoding** - URL хеши прекомпилированы
9. **Subhashes** - составное состояние страницы
10. **Hover tooltips** - разделение page/hover page/hash
