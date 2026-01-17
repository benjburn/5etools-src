# Модуль обработки cross-source references

## Обзор

Система cross-source references в 5etools обеспечивает работу ссылок между разными версиями D&D 5e (2014 vs 2024) и различными source books. Основная проблема: одни и те же сущности могут существовать в разных источниках с разными правилами.

## Основные концепции

### 1. Source версии (2014 vs 2024)

**Константы источников (parser.js:3088-3192):**
```javascript
Parser.SRC_PHB = "PHB";   // Player's Handbook 2014
Parser.SRC_XPHB = "XPHB";  // Player's Handbook 2024
Parser.SRC_DMG = "DMG";    // Dungeon Master's Guide 2014
Parser.SRC_XDMG = "XDMG";  // Dungeon Master's Guide 2024
Parser.SRC_MM = "MM";      // Monster Manual 2014
```

**Style hints (consts.js):**
```javascript
SITE_STYLE__CLASSIC = "classic";  // 2014 edition
SITE_STYLE__ONE = "one";          // 2024 edition
```

### 2. Определение типа source (utils.js:617-623)

**SourceUtil.isClassicSource():**
```javascript
static isClassicSource(source) {
  // Сравнивает дату source с датой XPHB (2024-09-17)
  this._CLASSIC_THRESHOLD_TIMESTAMP ||=
    new Date(Parser.sourceJsonToDate(Parser.SRC_XPHB));
  return new Date(Parser.sourceJsonToDate(source))
    < this._CLASSIC_THRESHOLD_TIMESTAMP;
}
```

- Если source старее XPHB → classic (2014)
- Если source новее или равен XPHB → modern (2024)
- Работает для prerelease и homebrew

### 3. Default sources для тегов (render.js:5201-5996)

**Renderer.tag классы имеют `defaultSource`:**
```javascript
static TagSpell = class extends this._TagBaseAt {
  tagName = "spell";
  defaultSource = Parser.SRC_PHB;  // или XPHB в зависимости от style
};

static TagItem = class extends this._TagBaseAt {
  tagName = "item";
  defaultSource = Parser.SRC_PHB;
};

static TagCreature = class extends this._TagBaseAt {
  tagName = "creature";
  defaultSource = Parser.SRC_MM;
};
```

**Parser.getTagSource() (parser.js:4301-4310):**
```javascript
Parser.getTagSource = function(tag, source) {
  if (source && source.trim()) return source;  // Explicit source

  tag = tag.trim();
  const tagMeta = Renderer.tag.TAG_LOOKUP[tag];
  if (!tagMeta) throw new Error(`Unhandled tag "${tag}"`);
  return tagMeta.defaultSource;  // Default from tag class
}
```

## Теги и источники

### Формат тегов

**Полный формат:**
```
{@tagName name|source|displayText|...others}
```

**Примеры:**
```javascript
// Explicit source
"{@spell fireball|XPHB}" → 2024 Fireball
"{@item longsword|PHB}" → 2014 Longsword

// No source (ambiguous)
"{@spell fireball}" → uses defaultSource (PHB or XPHB based on style)
"{@condition Blinded}" → uses defaultSource

// With display text
"{@item longsword|XPHB|Magic Sword}" → display "Magic Sword", link to XPHB longsword
```

### unpackUid() - парсинг UID (utils.js:5216-5234)

```javascript
static unpackUid(uid, tag, opts) {
  // "{@spell fireball|XPHB|Display Text}"
  let [name, source, displayText, ...others] =
    uid.split("|").map(Function.prototype.call.bind(String.prototype.trim));

  // Если source не указан → ambiguous reference
  const isAllowRedirect = !source;

  // Получить default source для тега
  source = source || Parser.getTagSource(tag, source);

  return {
    name,           // "fireball"
    source,         // "XPHB"
    displayText,    // "Display Text"
    others,         // [...]
    isAllowRedirect // true если source не был указан
  };
}
```

## Система редиректов

### Renderer.redirect class (render.js:15230-15278)

**Инициализация:**
```javascript
static async pInit() {
  this._P_LOADING_VERSION_REDIRECT_LOOKUP ||=
    DataUtil.loadJSON("data/generated/gendata-tag-redirects.json");
  const lookup = await this._P_LOADING_VERSION_REDIRECT_LOOKUP;
  this._VERSION_REDIRECT_LOOKUP ||= lookup;
}
```

**getRedirectByHash():**
```javascript
static getRedirectByHash(page, hash) {
  // Ищет редирект в lookup таблице
  const fromLookup = MiscUtil.get(this._VERSION_REDIRECT_LOOKUP, page, hash);
  if (!fromLookup) return null;

  // Может быть строкой (new hash) или объектом ({page, hash})
  const hashNxt = fromLookup.hash || fromLookup;
  const pageNxt = fromLookup.page || page;
  const decodedNxt = UrlUtil.autoDecodeHash(hashNxt, {page: pageNxt});

  // Проверить исключения
  if (ExcludeUtil.isExcluded(hashNxt, prop, decodedNxt.source))
    return null;

  return {
    page: pageNxt,
    hash: hashNxt,
    source: decodedNxt.source,
    name: decodedNxt.name
  };
}
```

### gendata-tag-redirects.json (114KB)

**Структура:**
```json
{
  "actions.html": {
    "attack_phb": "attack_xphb",
    "dash_phb": "dash_xphb",
    "grapple_phb": {
      "hash": "unarmed%20strike_xphb",
      "page": "variantrules.html"
    }
  },
  "bestiary.html": {
    "aarakocra_mm": "aarakocra%20skirmisher_xmm",
    "aboleth_mm": "aboleth_xmm"
  },
  "spells.html": {
    "fireball_phb": "fireball_xphb",
    "magic%20missile_phb": "magic%20missile_xphb"
  }
}
```

**Формат редиректа:**
- `{page: {hash_old: hash_new}}`
- `hash_new` может быть:
  - Строка: новый hash на той же странице
  - Объект: `{hash: "...", page: "..."}` для cross-page redirect

### Hover обработка с редиректами (render.js:15569-15574)

```javascript
static async _pHandleLinkMouseOver_pGetVersionRedirectMeta(
  {page, source, hash, preloadId, customHashId, isAllowRedirect}
) {
  // Не редиректим если:
  if (!isAllowRedirect || preloadId || customHashId) return null;

  // В classic стиле не редиректим
  if (VetoolsConfig.get("styleSwitcher", "style") === "classic")
    return null;

  // Ищем редирект
  return Renderer.redirect.pGetRedirectByHash(page, hash);
}
```

**Поток при hover:**
1. Пользователь наводит на ссылку `{@spell fireball}`
2. isAllowRedirect = true (source не был указан)
3. Если style ≠ "classic", ищем редирект
4. Если нашли редирект → загружаем данные из нового source
5. Показываем tooltip с правильной версией

## Примеры из данных

### Explicit cross-source ссылки (data/actions.json)

```javascript
// Ссылка на 2024 версию правила
"{@variantrule Unarmed Strike|XPHB}"
"{@variantrule Speed|XPHB}"
"{@variantrule Fly Speed|XPHB}"
"{@variantrule Swim Speed|XPHB}"

// Классические ссылки (2014)
"{@book Making an Attack|phb|9|making an attack}"
```

### Ambiguous ссылки (без source)

```javascript
// Используют defaultSource в зависимости от style
"{@action Use an Object}"
"{@skill Athletics}"
"{@skill Acrobatics}"
"{@status concentration}"
```

### Items с явным source (data/items.json)

```javascript
// Всегда используют PHB версию
"{@item drum|PHB}"
"{@item artisan's tools|PHB}"
"{@item smith's tools|PHB}"
```

## Tag rendering с cross-source (render.js:2408-2440)

```javascript
// _renderString_renderTag() - default case
const {
  name, source, displayText, others,
  page, hash, hashPreEncoded,
  pageHover, sourceHover, hashHover, hashPreEncodedHover,
  preloadId, linkText, subhashes, subhashesHover,
  isFauxPage, isAllowRedirect
} = Renderer.utils.getTagMeta(tag, text);

const fauxEntry = {
  type: "link",
  href: {
    type: "internal",
    path: page,
    hash,
    hover: {
      page,
      isFauxPage,
      source,
    },
  },
  text: (displayText || name),
};

// Добавляем redirect metadata
if (isAllowRedirect)
  fauxEntry.href.hover.isAllowRedirect = isAllowRedirect;

this._recursiveRender(fauxEntry, textStack, meta);
```

## Style-aware генерация (converter/makebrew)

### Style hint propagation

```javascript
// Пример из makebrew-spell.js
source: styleHint === SITE_STYLE__CLASSIC
  ? Parser.SRC_PHB
  : Parser.SRC_XPHB

// Converter example
if (styleHint === SITE_STYLE_ONE && it.edition === src)
  return false;
if (styleHint === SITE_STYLE__CLASSIC &&
    !SourceUtil.isClassicSource(src))
  return false;
```

## Валидация cross-source ссылок

### test-tags.js

```javascript
static _RE = RegExp(
  `{@(tag1|tag2|...) ([^}]*?)}`, "g"
);

_checkTagText({original, tag, text, filePath}) {
  const tagMeta = Renderer.utils.getTagMeta(`@${tag}`, text);
  const encoded = tagMeta.hashHover || tagMeta.hash;
  const url = `${tagMeta.page}#${encoded}`.toLowerCase().trim();

  // Проверка существования URL
  if (!tagTestUrlLookup.hasUrl(url)) {
    this._addMessage(`Missing link: ${original} → "${url}"`);
  }
}
```

## GetUidPacked() - упаковка UID (utils.js:5236-5249)

```javascript
static getUidPacked(ent, tag, opts = {}) {
  const {name} = ent;
  const source = SourceUtil.getEntitySource(ent);

  // Получаем default source для тега
  const sourceDefault = Parser.getTagSource(tag);

  // Если source совпадает с default → опускаем его
  const out = [
    ent.name,
    source.toLowerCase() === sourceDefault.toLowerCase()
      ? ""
      : source,
  ].join("|").replace(/\|+$/, ""); // Trim trailing pipes

  return opts.isMaintainCase ? out : out.toLowerCase();
}
```

**Примеры:**
```javascript
// Для style=classic (default PHB)
{name: "Fireball", source: "PHB"} → "fireball"
{name: "Fireball", source: "XPHB"} → "fireball|xphb"

// Для style=one (default XPHB)
{name: "Fireball", source: "XPHB"} → "fireball"
{name: "Fireball", source: "PHB"} → "fireball|phb"
```

## Ключевые файлы

- `js/parser.js:3088-3192` - Source constants (PHB, XPHB, DMG, XDMG)
- `js/parser.js:4301-4310` - getTagSource()
- `js/consts.js:1-8` - Style constants (classic/one)
- `js/utils.js:617-623` - isClassicSource()
- `js/utils.js:5216-5234` - unpackUid()
- `js/utils.js:5236-5249` - getUidPacked()
- `js/render.js:5201-5996` - Renderer.tag классы с defaultSource
- `js/render.js:4648-4920` - getTagMeta() cross-reference resolution
- `js/render.js:15230-15278` - Renderer.redirect class
- `data/generated/gendata-tag-redirects.json` - Version mapping (114KB)
- `test/test-tags.js` - Tag validation

## Архитектурные паттерны

1. **Dual-version support** - Одна codebase поддерживает 2014 и 2024
2. **Style hints** - Глобальная настройка определяет default sources
3. **Ambiguous references** - Теги без source используют default
4. **Redirect lookup** - Автоматический редирект между версиями
5. **Optimized storage** - Source опускается если=default
6. **Date-based classification** - Classic vs modern по дате source
7. **Hover-time resolution** - Редиректы применяются при hover
8. **Explicit overrides** - Явный source всегда имеет приоритет
9. **Tag metadata** - Каждый тег знает свой default source
10. **Centralized mappings** - gendata-tag-redirects.json для всех редиректов

## Статистика

- **~50 source constants** (PHB, XPHB, DMG, XDMG, MM, XMM, и др.)
- **2 стиля:** classic (2014), one (2024)
- **70+ тегов** с defaultSource
- **114KB** redirect lookup table
- **3 формата** редиректа: simple hash, cross-page, null
- **~5000+** mappings в gendata-tag-redirects.json
- **Date threshold:** 2024-09-17 (XPHB release date)

## Типичные use cases

### 1. Ссылка на конкретную версию
```javascript
"{@spell fireball|XPHB}" → всегда 2024 Fireball
```

### 2. Ambiguous ссылка (auto-version)
```javascript
"{@spell fireball}" →
  - classic style → PHB 2014
  - one style → XPHB 2024
```

### 3. Redirect при hover
```javascript
// Data имеет PHB версию
{name: "Fireball", source: "PHB"}

// User в one стиле наводит на ссылку
// → Автоматический redirect на XPHB версию в tooltip
```

### 4. Cross-page redirect
```javascript
// Grapple действие в PHB → Unarmed Strike правило в XPHB
"grapple_phb" → {
  hash: "unarmed%20strike_xphb",
  page: "variantrules.html"
}
```

### 5. Excluded entities
```javascript
// Если entity исключена через blocklist
// → Redirect не применяется
if (ExcludeUtil.isExcluded(hashNxt, prop, source))
  return null;
```
