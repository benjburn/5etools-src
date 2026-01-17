# Модуль обработки Image References

## Обзор

Система image references в 5etools обеспечивает работу с изображениями всех типов: обложки книг, изображения в контенте (entries), токены существ, и многое другое. Изображения хранятся в директории `img/` и ссылаются через JSON данные.

## Основные концепции

### 1. Типы изображений

**Категории изображений в `img/`:**
- `covers/` - Обложки книг (132 файла)
- `bestiary/` - Изображения существ (91 source, 7438 файла)
- `items/` - Изображения предметов (43 source, 774 файла)
- `adventure/` - Изображения из приключений (82 source, 5052 файла)
- `backgrounds/` - Изображения предысторий (19 source, 81 файл)
- `races/` - Изображения рас (29 source, 182 файла)
- `classes/` - Изображения классов (14 source, 174 файла)
- `spells/` - Изображения заклинаний (9 source, 88 файлов)
- `tokens/` - Токены существ
- `decks/` - Карты (15 source, 609 файлов)
- И 20+ других категорий

### 2. Структура JSON ссылки на изображение

**Entry с типом image:**
```javascript
{
  type: "image",
  href: {
    type: "internal",
    path: "adventure/CRCotN/000-00-001.ruidus-moon.webp"
  },
  title: "Ruidus Moon",
  credit: "{@artist Artist Name}",
  imageType: "map",           // "map" | "mapPlayer" | undefined
  width: 1000,
  height: 800,
  mapRegions: [...],          // Опционально: регионы карты
  expectsLightBackground: true,  // Опционально
  expectsDarkBackground: false   // Опционально
}
```

**Cover изображения:**
```javascript
// В books.json
{
  id: "PHB",
  name: "Player's Handbook (2014)",
  source: "PHB",
  cover: {
    type: "internal",
    path: "covers/PHB.webp"
  }
}
```

**Token ссылки:**
```javascript
// В bestiary данных
{
  name: "Goblin",
  source: "MM",
  token: {
    name: "Goblin",
    source: "MM"
  }
}

// Или через tokenHref:
{
  name: "Goblin",
  source: "MM",
  tokenHref: {
    type: "internal",
    path: "bestiary/tokens/MM/Goblin.webp"
  }
}
```

### 3. Renderer.getMediaUrl() - базовая функция (render.js:112)

```javascript
this.getMediaUrl = function (mediaDir, path) {
  // mediaDir: "img", "fonts", etc.
  // path: "covers/PHB.webp", "bestiary/MM/Goblin.webp", etc.
  return `${baseUrl}${mediaDir}/${path}`;
};
```

**Примеры:**
```javascript
getMediaUrl("img", "covers/PHB.webp")
  → "https://example.com/img/covers/PHB.webp"

getMediaUrl("img", "bestiary/tokens/MM/Goblin.webp")
  → "https://example.com/img/bestiary/tokens/MM/Goblin.webp"
```

### 4. getEntryMediaUrl() - универсальная функция (render.js:4440-4453)

```javascript
static getEntryMediaUrl (entry, prop, mediaDir, {isUrlEncode = false} = {}) {
  if (!entry[prop]) return "";

  let href = "";
  if (entry[prop].type === "internal") {
    // Внутренняя ссылка: path относительно img/
    href = UrlUtil.link(Renderer.get().getMediaUrl(
      mediaDir,
      isUrlEncode ? encodeURI(entry[prop].path) : entry[prop].path
    ));
  } else if (entry[prop].type === "external") {
    // Внешняя ссылка: полный URL
    const isPreEncoded = decodeURI(entry[prop].url) !== entry[prop].url;
    href = (isPreEncoded || !isUrlEncode)
      ? entry[prop].url
      : encodeURI(entry[prop].url);
  }
  return href;
}
```

**Использование:**
```javascript
// Для href изображения
const url = Renderer.utils.getEntryMediaUrl(entry, "href", "img");

// Для thumbnail
const thumbUrl = Renderer.utils.getEntryMediaUrl(entry, "hrefThumbnail", "img");

// Для cover
const coverUrl = Renderer.utils.getEntryMediaUrl(bookData, "cover", "img");

// Для token
const tokenUrl = Renderer.utils.getEntryMediaUrl(creature, "tokenHref", "img");
```

### 5. _renderImage() - рендеринг изображений (render.js:570-610)

**Основной flow:**

```javascript
this._renderImage = function (entry, textStack, meta, options) {
  // 1. Track title для index
  if (entry.title) this._handleTrackTitles(entry.title, {isImage: true});

  // 2. Map wrapper
  if (entry.imageType === "map" || entry.imageType === "mapPlayer")
    textStack[0] += `<div class="rd__wrp-map">`;

  // 3. Gallery wrapper
  textStack[0] += `<div class="${
    meta._typeStack.includes("gallery") ? "rd__wrp-gallery-image" : ""
  }">`;

  // 4. Get URL
  const href = this._renderImage_getUrl(entry);

  // 5. Get tooltip (title + credit)
  const ptTitleCreditTooltip = this._renderImage_getTitleCreditTooltipText(entry);
  const ptTitle = ptTitleCreditTooltip ? `title="${ptTitleCreditTooltip}"` : "";

  // 6. Check plugin overrides
  const pluginDataIsNoLink = this._applyPlugins_useFirst(
    "image_isNoLink", {textStack, meta, options}, {input: entry}
  );

  // 7. Get map region labels
  const ptLabels = this._renderImage_geLabels(entry);

  // 8. Render wrapper
  textStack[0] += `<div class="${
    this._renderImage_getWrapperClasses(entry, meta)
  }" ${entry.title && this._isHeaderIndexIncludeImageTitles
      ? `data-title-index="${this._headerIndex++}"`
      : ""}>
    <div class="w-100 h-100 relative">
      ${pluginDataIsNoLink ? "" : `<a class="relative" href="${href}"
        target="_blank" rel="noopener noreferrer" ${ptTitle}>`}
        ${this._renderImage_getImg({entry, meta, href, pluginDataIsNoLink, ptTitle})}
      ${pluginDataIsNoLink ? "" : `</a>`}
      ${ptLabels}
    </div>
  </div>`;

  // 9. Render title/credit/map regions
  if (!this._renderImage_isComicStyling(entry) &&
      (entry.title || entry.credit || entry.mapRegions)) {

    textStack[0] += `<div class="rd__image-title">`;

    const isDynamicViewer = entry.mapRegions && !globalThis.IS_VTT;

    if (entry.title && !isDynamicViewer)
      textStack[0] += `<div class="rd__image-title-inner">${
        this.render(entry.title)
      }</div>`;

    if (isDynamicViewer) {
      textStack[0] += `<button class="ve-btn ve-btn-xs ve-btn-default
        rd__image-btn-viewer" onclick="RenderMap.pShowViewer(event, this)"
        data-rd-packed-map="${this._renderImage_getMapRegionData(entry)}"
        title="Open Dynamic Viewer (SHIFT to Open in New Window)">
        <span class="glyphicon glyphicon-picture"></span>
        ${Renderer.stripTags(entry.title) || "Dynamic Viewer"}
      </button>`;
    }

    if (entry.credit)
      textStack[0] += `<div class="rd__image-credit ve-muted">
        <span class="glyphicon glyphicon-pencil" title="Art Credit"></span>
        ${this.render(entry.credit)}
      </div>`;

    textStack[0] += `</div>`;
  }

  // 10. Close map wrapper
  if (entry.imageType === "map" || entry.imageType === "mapPlayer")
    textStack[0] += `</div>`;
};
```

**_renderImage_getUrl() (render.js:776-780):**
```javascript
this._renderImage_getUrl = function (entry) {
  let url = Renderer.utils.getEntryMediaUrl(entry, "href", "img");
  url = this._applyPlugins_useAll("image_urlPostProcess", null, {input: url}) ?? url;
  return url;
};
```

**_renderImage_getImg() - рендеринг <img> тега (render.js:620-674):**
```javascript
this._renderImage_getImg = function ({entry, meta, href, pluginDataIsNoLink, ptTitle}) {
  const hasWidthHeight = entry.width != null && entry.height != null;
  const isLazy = this._lazyImages && hasWidthHeight;
  const isMinimizeLayoutShift = this._isMinimizeLayoutShift && hasWidthHeight;

  // Lazy loading placeholder
  const svg = isLazy || isMinimizeLayoutShift
    ? Renderer.utils.lazy.getPlaceholderImgHtml({width: entry.width, height: entry.height})
    : null;

  const imgUrl = this._renderImage_getUrlThumbnail(entry);

  const srcPart = svg
    ? `src="${svg}" data-src="${href}"`
    : `src="${href}"`;

  const srcsetPart = imgUrl
    ? `srcset="${imgUrl} 1x, ${href} 2x"`
    : ``;

  const loadingPart = svg || isLazy
    ? `loading="lazy"`
    : ``;

  const classes = [
    "rd__image",
    entry.style === "full-width" ? "w-100" : ""
  ].filter(Boolean).join(" ");

  return `<img
    class="${classes}"
    ${srcPart}
    ${srcsetPart}
    alt="${entry.title ? Renderer.stripTags(entry.title) : ""}"
    ${entry.width != null ? `width="${entry.width}"` : ""}
    ${entry.height != null ? `height="${entry.height}"` : ""}
    ${loadingPart}
    ${ptTitle}
  >`;
};
```

### 6. _renderGallery() - рендеринг галерей (render.js:1842-1859)

```javascript
this._renderGallery = function (entry, textStack, meta, options) {
  if (entry.name)
    textStack[0] += `<h5 class="rd__gallery-name">${entry.name}</h5>`;

  textStack[0] += `<div class="rd__wrp-gallery">`;

  const len = entry.images.length;
  const anyNamed = entry.images.some(it => it.title);
  const isAnyCredited = entry.images.some(it => it.credit);

  for (let i = 0; i < len; ++i) {
    const img = MiscUtil.copyFast(entry.images[i]);

    // Padding для согласования размеров
    if (anyNamed && !img.title) img._galleryTitlePad = true;
    if (isAnyCredited && !img.credit) img._galleryCreditPad = true;

    delete img.imageType;
    this._recursiveRender(img, textStack, meta, options);
  }

  textStack[0] += `</div>`;
};
```

**Gallery структура:**
```javascript
{
  type: "gallery",
  name: "Gallery Name",
  images: [
    {
      type: "image",
      href: {type: "internal", path: "..."},
      title: "Image 1",
      credit: "{@artist Artist}"
    },
    {
      type: "image",
      href: {type: "internal", path: "..."},
      // Без title - будет padding
      credit: "{@artist Artist}"
    }
  ]
}
```

### 7. Cover изображения (render.js:14135-14148)

```javascript
static _isAltMissingCoverUsed = false;

static getCoverUrl (contents) {
  // 1. Explicit cover object
  if (contents.cover) {
    return UrlUtil.link(Renderer.utils.getEntryMediaUrl(contents, "cover", "img"));
  }

  // 2. Legacy coverUrl string (deprecated)
  if (contents.coverUrl) {
    if (/^https?:\/\//.test(contents.coverUrl))
      return contents.coverUrl;
    return UrlUtil.link(Renderer.get().getMediaUrl(
      "img", contents.coverUrl.replace(/^img\//, "")
    ));
  }

  // 3. Default blank cover
  return UrlUtil.link(Renderer.get().getMediaUrl("img",
    `covers/blank${Math.random() <= 0.05 &&
      !Renderer.adventureBook._isAltMissingCoverUsed &&
      (Renderer.adventureBook._isAltMissingCoverUsed = true)
      ? "-alt" : ""}.webp`
  ));
}
```

**Blank cover варианты:**
- `covers/blank.webp` (95% случаев)
- `covers/blank-alt.webp` (5% случаев - рандомизация)

### 8. Token изображения (render.js:15221-15227)

```javascript
static getTokenUrl (ent, mediaDir, {isIgnoreImplicit = false, isUrlEncode = false} = {}) {
  // 1. Legacy tokenUrl (deprecated)
  if (ent.tokenUrl) return ent.tokenUrl;

  // 2. Explicit token object
  if (ent.token)
    return Renderer.get().getMediaUrl("img",
      `${mediaDir}/${ent.token.source}/${
        Parser.nameToTokenName(ent.token.name, {isUrlEncode})
      }.webp`
    );

  // 3. tokenHref (с type/internal или external)
  if (ent.tokenHref)
    return Renderer.utils.getEntryMediaUrl(ent, "tokenHref", "img", {isUrlEncode});

  // 4. Implicit token (по умолчанию)
  if (isIgnoreImplicit) return null;
  return Renderer.get().getMediaUrl("img",
    `${mediaDir}/${ent.source}/${
      Parser.nameToTokenName(ent.name, {isUrlEncode})
    }.webp`
  );
}
```

**Parser.nameToTokenName() (parser.js:2848-2854):**
```javascript
Parser.nameToTokenName = function (name, {isUrlEncode = false} = {}) {
  const out = name
    .toAscii()  // Удаляет non-ASCII символы
    .replace(/"/g, "");  // Удаляет кавычки

  if (!isUrlEncode) return out;
  return encodeURIComponent(out);
};
```

**Примеры:**
```javascript
// "Goblin" → "Goblin"
nameToTokenName("Goblin")
  → "Goblin"

// "Ancient Red Dragon" → "Ancient Red Dragon"
nameToTokenName("Ancient Red Dragon")
  → "Ancient Red Dragon"

// "Tarrasque" → "Tarrasque" (URL encoded)
nameToTokenName("Tarrasque", {isUrlEncode: true})
  → "Tarrasque"

// Implicit token path
getTokenUrl({name: "Goblin", source: "MM"}, "bestiary/tokens")
  → "img/bestiary/tokens/MM/Goblin.webp"

// Explicit token
getTokenUrl({
  name: "Goblin",
  source: "MM",
  token: {name: "Goblin Boss", source: "MM"}
}, "bestiary/tokens")
  → "img/bestiary/tokens/MM/Goblin Boss.webp"
```

### 9. Map Regions - интерактивные карты

**Структура mapRegions:**
```javascript
{
  type: "image",
  href: {type: "internal", path: "adventure/CRCotN/map.webp"},
  imageType: "map",  // или "mapPlayer"
  width: 2000,
  height: 1500,
  title: "Dungeon Map",
  mapRegions: [
    {
      x: 100,
      y: 100,
      w: 200,
      h: 150,
      area: "room_1"
    },
    {
      x: 400,
      y: 300,
      w: 250,
      h: 200,
      area: "corridor_a"
    }
  ]
}
```

**_renderImage_getMapRegionData()** - упаковка регионов:
```javascript
this._renderImage_getMapRegionData = function (entry) {
  return JSON.stringify({
    u: entry.href.path,
    w: entry.width,
    h: entry.height,
    r: entry.mapRegions
  }).toBase64();
};
```

**_renderImage_geLabels() - рендеринг меток регионов:**
```javascript
this._renderImage_geLabels = function (entry) {
  if (
    !entry.labelMapRegions
    || !globalThis.BookUtil?.curRender?.headerMap
    || !globalThis.polylabel
    || !entry.width
    || !entry.height
    || !entry.mapRegions?.length
  ) return "";

  const tagInfo = Renderer.tag.TAG_LOOKUP.area;

  return entry.mapRegions
    .map(region => {
      const area = globalThis.BookUtil.curRender.headerMap[region.area];
      if (!area) return "";

      // Использует polylabel для нахождения оптимальной позиции label
      const center = globalThis.polylabel([region], 1.0);

      return `<div style="
        position: absolute;
        left: ${center.x / entry.width * 100}%;
        top: ${center.y / entry.height * 100}%;
      ">
        ${area}
      </div>`;
    })
    .join("");
};
```

### 10. Стили изображений

**_renderImage_getWrapperClasses() (render.js:753-764):**
```javascript
this._renderImage_getWrapperClasses = function (entry) {
  const out = ["rd__wrp-image", "relative"];

  // Фон
  if (entry.expectsLightBackground)
    out.push("rd__wrp-image--bg", "rd__wrp-image--bg-light");
  else if (entry.expectsDarkBackground)
    out.push("rd__wrp-image--bg", "rd__wrp-image--bg-dark");

  // Comic стиль
  if (entry.style) {
    switch (entry.style) {
      case "comic-speaker-left":
        out.push("rd__comic-img-speaker", "rd__comic-img-speaker--left");
        break;
      case "comic-speaker-right":
        out.push("rd__comic-img-speaker", "rd__comic-img-speaker--right");
        break;
    }
  }

  return out.join(" ");
};
```

**_renderImage_getImageClasses() (render.js:766-774):**
```javascript
this._renderImage_getImageClasses = function (entry) {
  const out = ["rd__image"];

  if (entry.style) {
    switch (entry.style) {
      case "full-width": out.push("w-100"); break;
      case "comic-speaker-left": out.push("rd__comic-img"); break;
      case "comic-speaker-right": out.push("rd__comic-img"); break;
    }
  }

  return out.join(" ");
};
```

## Примеры из данных

### Adventure изображения (adventure-crcotn.json)

```javascript
{
  type: "image",
  href: {
    type: "internal",
    path: "adventure/CRCotN/000-00-001.ruidus-moon.webp"
  },
  title: "Ruidus Moon",
  credit: "{@artist Artist Name}"
}
```

### Book covers (books.json)

```javascript
{
  id: "PHB",
  name: "Player's Handbook (2014)",
  source: "PHB",
  cover: {
    type: "internal",
    path: "covers/PHB.webp"
  }
}
```

### Bestiary tokens

```javascript
{
  name: "Goblin",
  source: "MM",
  token: {
    name: "Goblin",
    source: "MM"
  }
}
// → img/bestiary/tokens/MM/Goblin.webp
```

### Gallery пример

```javascript
{
  type: "gallery",
  name: "NPC Portraits",
  images: [
    {
      type: "image",
      href: {type: "internal", path: "adventure/CRCotN/001-00-002.alyxian.webp"},
      title: "Alyxian",
      credit: "{@artist Artist}"
    },
    {
      type: "image",
      href: {type: "internal", path: "adventure/CRCotN/002-00-003.ayo-jabe.webp"},
      title: "Ayo Jabe",
      credit: "{@artist Artist}"
    }
  ]
}
```

## Lazy Loading и Layout Shift Prevention

**Placeholder SVG (render.js:629-634):**
```javascript
const svg = isLazy || isMinimizeLayoutShift
  ? Renderer.utils.lazy.getPlaceholderImgHtml({width: entry.width, height: entry.height})
  : null;
```

**HTML вывод:**
```html
<!-- С placeholder -->
<img src="data:image/svg+xml;..." data-src="img/adventure/map.webp"
     width="1000" height="800" loading="lazy">

<!-- Без placeholder -->
<img src="img/adventure/map.webp"
     width="1000" height="800">
```

## Ключевые файлы

- `js/render.js:112` - getMediaUrl()
- `js/render.js:570-610` - _renderImage()
- `js/render.js:620-674` - _renderImage_getImg()
- `js/render.js:776-780` - _renderImage_getUrl()
- `js/render.js:782-786` - _renderImage_getUrlThumbnail()
- `js/render.js:753-764` - _renderImage_getWrapperClasses()
- `js/render.js:766-774` - _renderImage_getImageClasses()
- `js/render.js:675-716` - _renderImage_geLabels() (map regions)
- `js/render.js:1842-1859` - _renderGallery()
- `js/render.js:4440-4453` - getEntryMediaUrl()
- `js/render.js:14135-14148` - getCoverUrl()
- `js/render.js:15221-15227` - getTokenUrl()
- `js/parser.js:2848-2854` - nameToTokenName()
- `img/` - Директория с изображениями (28 категорий)
- `data/books.json` - Cover metadata
- `data/adventure/` - Adventure изображения
- `data/bestiary/` - Creature tokens

## Архитектурные паттерны

1. **Type-based dispatch** - `type: "image"` обрабатывается через _renderImage()
2. **Internal vs External** - Разделение на внутренние (path) и внешние (url) изображения
3. **Media URL abstraction** - getMediaUrl() для унификации путей
4. **Entry-based references** - href объекты с type/path или type/url
5. **Lazy loading** - Placeholder SVG + data-src для производительности
6. **Layout shift prevention** - Explicit width/height в данных
7. **Source-based organization** - img/{category}/{source}/{name}.webp
8. **Token name normalization** - ASCII-only filenames
9. **Map regions** - Интерактивные карты с polygon labels
10. **Plugin system** - image_isNoLink, image_urlPostProcess hooks
11. **Gallery support** - Множественные изображения с title/credit
12. **Multi-resolution** - hrefThumbnail + href для retina displays
13. **Fallback covers** - blank.webp для книг без обложки
14. **Explicit token override** - token объект для переопределения implicit
15. **Dynamic viewer** - RenderMap для интерактивных карт

## Статистика

- **28 категорий** изображений в `img/`
- **~17,000+ файлов** изображений
- **132 cover** изображений
- **7,438 bestiary** изображений
- **5,052 adventure** изображений
- **3 формата** ссылок: internal, external, legacy string
- **2 типа** карт: map, mapPlayer
- **3 стиля** изображений: full-width, comic-speaker-left, comic-speaker-right
- **2 варианта** background: light, dark
- **WebP формат** для всех изображений

## Типичные use cases

### 1. Простое изображение
```javascript
{
  type: "image",
  href: {type: "internal", path: "adventure/CRCotN/map.webp"},
  title: "Dungeon Map"
}
```

### 2. Изображение с credit
```javascript
{
  type: "image",
  href: {type: "internal", path: "adventure/CRCotN/portrait.webp"},
  title: "NPC Portrait",
  credit: "{@artist Artist Name|XPHB}"
}
```

### 3. Интерактивная карта
```javascript
{
  type: "image",
  href: {type: "internal", path: "adventure/CRCotN/dungeon.webp"},
  imageType: "map",
  width: 2000,
  height: 1500,
  title: "Dungeon Level 1",
  mapRegions: [
    {x: 100, y: 100, w: 200, h: 150, area: "room_1"},
    {x: 400, y: 300, w: 250, h: 200, area: "corridor_a"}
  ],
  labelMapRegions: true
}
```

### 4. Gallery
```javascript
{
  type: "gallery",
  name: "Party Portraits",
  images: [
    {type: "image", href: {...}, title: "Character 1"},
    {type: "image", href: {...}, title: "Character 2"}
  ]
}
```

### 5. Creature token (implicit)
```javascript
{
  name: "Goblin",
  source: "MM"
}
// → img/bestiary/tokens/MM/Goblin.webp
```

### 6. Creature token (explicit)
```javascript
{
  name: "Goblin Boss",
  source: "MM",
  token: {
    name: "Goblin",
    source: "MM"  // Использует обычный Goblin token
  }
}
// → img/bestiary/tokens/MM/Goblin.webp
```

### 7. Book cover
```javascript
{
  id: "PHB",
  source: "PHB",
  cover: {
    type: "internal",
    path: "covers/PHB.webp"
  }
}
```

### 8. Lazy-loaded изображение
```javascript
{
  type: "image",
  href: {type: "internal", path: "adventure/large-map.webp"},
  width: 3000,
  height: 2000  // Нужен для placeholder
}
```

### 9. Внешнее изображение
```javascript
{
  type: "image",
  href: {
    type: "external",
    url: "https://example.com/image.jpg"
  },
  title: "External Image"
}
```

### 10. Изображение с thumbnail
```javascript
{
  type: "image",
  href: {type: "internal", path: "adventure/map-hd.webp"},
  hrefThumbnail: {type: "internal", path: "adventure/map.webp"},
  width: 2000,
  height: 1500
}
// srcset="adventure/map.webp 1x, adventure/map-hd.webp 2x"
```
