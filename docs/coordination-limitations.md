# Ограничения и Edge Cases - Система координации 5etools

## Обзор

Документ описывает ограничения, edge cases и потенциальные проблемы в системе координации 5etools, включающей загрузку данных, навигацию, рендеринг и управление состоянием.

---

## 1. Ограничения загрузки данных (DataUtil)

### 1.1 GitHub Rate Limiting

**Проблема:** GitHub raw API имеет агрессивные rate limits.

```javascript
static REQUEST_LIMITER_GITHUB_RAW = new this._RequestLimiter({
  urlPrefix: "https://raw.githubusercontent.com/",
  timeoutMs: 15 * 60 * 1000, // 15 mins
});
```

**Ограничения:**
- При получении статуса 429, все запросы к GitHub raw блокируются на **15 минут**
- Timeout применяется глобально для всех запросов к одному префиксу URL
- Нет встроенного механизма exponential backoff

**Edge cases:**
- Multiple simultaneous requests могут одновременно триггерить rate limit
- После 15 минут timeout нет гарантии, что rate limit сбросился
- Пользовательский опыт: приложение "зависает" на 15 минут

**Mitigation:**
- Fallback на jsDelivr CDN при 429
- Fallback на GitHack при 429
- Использовать кэшированные данные (`DataUtil._loaded`)

### 1.2 Stack Overflow Protection

**Проблема:** Большой массив данных может переполнить стек при рендеринге.

```javascript
static _MAX_DATA_CHUNK_SIZE = 4096;

for (let i = 0; i < len; i += this.constructor._MAX_DATA_CHUNK_SIZE) {
  const chunk = data[prop].slice(i, i + this.constructor._MAX_DATA_CHUNK_SIZE);
  this._dataList.push(...chunk);
}
```

**Ограничения:**
- Чанки **4096 entities** максимум
- Добавляется в список через spread operator (`...chunk`)

**Edge cases:**
- Массивы >4096 элементов разбиваются на несколько чанков
- Если entity содержит большие вложенные объекты, всё равно возможен stack overflow
- Нет адаптивного размера чанка based на memory usage

**Mitigation:**
- Использовать чанкование по умолчанию
- Рассмотреть `requestAnimationFrame` для progressive rendering

### 1.3 Memory Leaks в кэше

**Проблема:** Кэш никогда не очищается.

```javascript
static _loading = {};  // Активные загрузки
static _loaded = {};   // Кэш загруженных данных
static _merging = {};  // Активный мерджинг
static _merged = {};   // Кэш слитых данных
```

**Ограничения:**
- Все загруженные JSON файлы остаются в памяти навсегда
- Нет LRU cache eviction
- Нет memory limit

**Edge cases:**
- Пользователь открывает 50+ различных страниц → память растёт линейно
- Homebrew с большим количеством файлов увеличивает память
- На mobile устройствах с ограниченной памятью возможен OOM crash

**Mitigation:**
- Рассмотреть `WeakMap` для temporary references
- Добавить manual cache invalidation при `window.addEventListener("beforeunload")`
- Implement LRU cache с max size

### 1.4 Concurrent Merge Conflicts

**Проблема:** Одновременный мерджинг одного и того же URL.

```javascript
const isFresh = !DataUtil._merging[ident];
DataUtil._merging[ident] ||= DataUtil._pDoMetaMerge(ident, data, options);
await DataUtil._merging[ident];
```

**Ограничения:**
- Если один URL запрошен дважды одновременно, второй запрос ждёт первый
- Нет механизма abort для stale requests

**Edge cases:**
- `DataUtil.loadJSON(url)` вызывается из двух мест одновременно
- Первый request может быть stale, но всё равно завершится
- Второй request получит устаревший результат

**Mitigation:**
- Использовать `AbortController` для cancellation
- Добавить timestamp для идентификации свежих requests

---

## 2. Ограничения навигации (Hist)

### 2.1 Unknown Hash Loop

**Проблема:** "Stuck brew" loops при удалении homebrew.

```javascript
// Avoid "stuck brew" loops:
// - user is viewing a homebrew statblock; hash has homebrew source
// - user deletes that homebrew; page reloads
// - "unknown hash" flow triggers; deleted homebrew is re-loaded; page reloads
// - user is presented with the same statblock
```

**Ограничения:**
- Удалённый homebrew может быть автоматически перезагружен
- Пользователь не может удалить brew, если он открыт в hash

**Edge cases:**
- `Hist.doPreLocationReload()` пытается предотвратить это
- Но если source не распознан, loop всё равно возможен
- Особенно критично для prerelease контента

**Mitigation:**
- `doPreLocationReload()` очищает sources из hash перед перезагрузкой
- Пользователь должен вручную очистить hash перед удалением brew

### 2.2 Hash Format Assumptions

**Проблема:** Hash format зависит от типа entity.

```javascript
// Deities: name, pantheon, source
[name, pantheon, source] = parts;

// Class features: name, className, classSource, level, source
[name, className, classSource, levelRaw, source] = parts;

// Default: name, source
[name, source] = parts;
```

**Ограничения:**
- Количество компонентов хеша варьируется от 2 до 5
- Если entity меняет формат, старые хеши становятся невалидными
- Нет автоматической миграции хешей

**Edge cases:**
- Bookmarks с старым форматом хеша не работают
- Homebrew entities должны следовать формату official content
- `autoDecodeHash` throws error если encoder не найден

**Mitigation:**
- Использовать `autoEncodeHash` для генерации хешей
- Никогда не кодировать хеши вручную
- Consider URL-safe base64 encoding для future-proofing

### 2.3 Race Conditions в Hash Navigation

**Проблема:** Асинхронная обработка unknown hash.

```javascript
if (typeof this._pHandleUnknownHash === "function" && window.location.hash.length && this._lastUnknownLink !== link) {
  this._lastUnknownLink = link;
  this._pLoadingUnknownHash = this._pHandleUnknownHash(link, sub);
  return;  // Early return!
}
```

**Ограничения:**
- `_pLoadingUnknownHash` может быть pending во время следующего hash change
- `Hist._freshLoad()` ждёт завершения, но только через `setTimeout(..., 1)`

**Edge cases:**
- Быстрая навигация по нескольким unknown hash → race condition
- Пользователь может нажать "back" во время loading → stale promise
- Multiple tabs с одним и тем же hash → duplicate requests

**Mitigation:**
- `_lastUnknownLink` предотвращает повторные запросы для одного hash
- `_freshLoad` ждёт `_pLoadingUnknownHash` через promise chain

---

## 3. Ограничения URL Encoding (UrlUtil)

### 3.1 Limited Separator Characters

**Проблема:** Фиксированный набор разделителей.

```javascript
HASH_PART_SEP = ",";        // Между primary hash и subhash
HASH_LIST_SEP = "|";        // Между элементами списка
HASH_SUB_LIST_SEP = "~";    // Между значениями в subhash
HASH_SUB_KV_SEP = ":";      // Между key и value в subhash
```

**Ограничения:**
- Если entity name содержит эти символы, они будут URL-encoded
- Но URL encoding использует `%`, который также используется в hash encoding
- Двойное encoding возможно при неправильном использовании

**Edge cases:**
- Entity name `Fire: Storm` → `fire%3A%20storm` → broken subhash parsing
- Entity name `Ogre|Chief` → `ogre%7Cchief` → broken list parsing
- Unicode characters → percent encoding → readability issues

**Mitigation:**
- Использовать `toUrlified()` для encoding (заменяет пробелы на `-`)
- Избегать использования разделителей в entity names
- Consider base64url encoding для future-proofing

### 3.2 Missing Encoder Error

**Проблема:** Нет гарантированного encoder для всех страниц.

```javascript
autoEncodeHash (obj) {
  const curPage = UrlUtil.getCurrentPage();
  const encoder = UrlUtil.URL_TO_HASH_BUILDER[curPage];
  if (!encoder) throw new Error(`No encoder found for page ${curPage}`);
  return encoder(obj);
}
```

**Ограничения:**
- Если страница не в `URL_TO_HASH_BUILDER`, throw error
- Нет graceful fallback

**Edge cases:**
- Новая страница без encoder → crash
- Custom HTML pages не в репозитории → crash
- Typos в page name → crash

**Mitigation:**
- Добавить все страницы в `URL_TO_HASH_BUILDER`
- Implement default encoder based на `name` и `source`

---

## 4. Ограничения Homebrew/Prerelease (BrewUtil2)

### 4.1 Drag & Drop Limitations

**Проблема:** Shared drag & drop для brew и prerelease.

```javascript
document.body.addEventListener("drop", async evt => {
  const [prereleaseFileMetas, brewFileMetas] = fileMetas.segregate(fileMeta => this._isPrereleaseDroppedJson(fileMeta.json));

  if (prereleaseFileMetas.length) await PrereleaseUtil.pAddBrewsFromFiles(prereleaseFileMetas);
  if (brewFileMetas.length) await BrewUtil2.pAddBrewsFromFiles(brewFileMetas);

  this?.doLocationReload();
});
```

**Ограничения:**
- Все файлы обрабатываются последовательно
- Нет progress indicator
- Нет validation до добавления
- Нет undo для不小心 dropped files

**Edge cases:**
- Drop 50 JSON files → browser freeze
- Drop corrupted JSON → silent failure
- Drop non-JSON files → silently ignored
- Drop duplicate files → дублирование в storage

**Mitigation:**
- Валидировать JSON до добавления
- Показать confirmation dialog перед reload
- Implement file deduplication

### 4.2 Storage Quota

**Проблема:** localStorage имеет ограничения (обычно 5-10MB).

```javascript
_STORAGE_KEY = "BREW_STORAGE";
StorageUtil.syncSet(this._STORAGE_KEY, JSON.stringify(this._cache_brews));
```

**Ограничения:**
- Large homebrew collections могут превысить quota
- `JSON.stringify` может fail с `QuotaExceededError`
- No cleanup mechanism для old brew

**Edge cases:**
- Homebrew с images → быстро fills storage
- Multiple prerelease sources → storage full
- Safari private mode → localStorage disabled

**Mitigation:**
- Compress JSON перед storage (но browser support varies)
- Implement manual cleanup в manage-brew page
- Fallback на IndexedDB для large storage (но не реализовано)

### 4.3 Font Loading Race Conditions

**Проблема:** Custom fonts из brew загружаются асинхронно.

```javascript
this._pInit_pDoLoadFonts().then(null);  // Fire and forget
```

**Ограничения:**
- Fonts могут загружаться после initial render
- Text reflow possible при font load
- No error handling если font URL invalid

**Edge cases:**
- Homebrew с custom font → текст "прыгает" при загрузке
- Invalid font URL → silent failure
- Network timeout → fonts never load

**Mitigation:**
- Use `font-display: swap` CSS
- Implement font loading timeout
- Fallback на system fonts

---

## 5. Ограничения Meta Merge (Copy Resolution)

### 5.1 Unresolved _Copy Detection

**Проблема:** Проверка на unresolved `_copy` references.

```javascript
_verifyMerged (data) {
  for (const it of data[k]) {
    if (it._copy) {
      setTimeout(() => { throw new Error(`Unresolved "_copy" in entity: ${JSON.stringify(it)}`); });
    }
  }
}
```

**Ограничения:**
- Error throwed через `setTimeout` → может быть пропущен в try/catch
- Нет graceful recovery
- Останавливает только после завершения мерджинга

**Edge cases:**
- Circular `_copy` references → infinite loop (но должен быть detected)
- Missing source entity → crash
- Homebrew с `_copy` на несуществующий entity → crash

**Mitigation:**
- Validate `_copy` targets до merge
- Implement circular reference detection
- Provide user-friendly error message

### 5.2 Deep Copy Performance

**Проблема:** Глубокое копирование больших объектов.

```javascript
_generic_pMergeCopy_copy (target, source) {
  return MiscUtil.copyFast(source);
}
```

**Ограничения:**
- `copyFast` использует structured clone algorithm
- Large objects (bestiary entities с spellcasting) могут быть медленными
- No memoization для repeated copies

**Edge cases:**
- Creature с 50 spells → slow copy
- Multiple entities с одинаковым source → redundant copies
- Nested `_copy` references → exponential time

**Mitigation:**
- Consider shallow copy где возможно
- Implement copy-on-write semantics
- Cache copied entities

---

## 6. Ограничения Initialisation

### 6.1 Hard-coded Init Order

**Проблема:** Жёсткий порядок инициализации.

```javascript
await Promise.all([
  PrereleaseUtil.pInit(),
  BrewUtil2.pInit(),
]);
ExcludeUtil.pInitialise().then(null);
```

**Ограничения:**
- Prerelease и Brew загружаются параллельно
- ExcludeUtil запускается после, но не awaited
- Нет зависимости между ними

**Edge cases:**
- Если BrewUtil2.pInit() hangs, всё приложение hangs
- Если PrereleaseUtil.pInit() throws, исключение не поймано
- ExcludeUtil может инициализироваться после первого render

**Mitigation:**
- Add timeout для init operations
- Implement graceful degradation при failures
- Consider lazy loading для non-critical modules

### 6.2 Multiple ToolsLoaded Events

**Проблема:** "toolsLoaded" event dispatch multiple times.

```javascript
// IndexPage.pOnLoad()
window.dispatchEvent(new Event("toolsLoaded"));

// ListPage.pOnLoad()
window.dispatchEvent(new Event("toolsLoaded"));
```

**Ограничения:**
- Нет указания, какой toolsLoaded (index vs list page)
- Нет способа различить тип страницы
- Multiple listeners могут быть triggered multiple times

**Edge cases:**
- Script listens to toolsLoaded → executes twice
- Race conditions если two pages load simultaneously
- No cleanup mechanism для old listeners

**Mitigation:**
- Use custom event с detail `{page: "spells"}`
- Implement event namespaces
- Consider `CustomEvent` вместо generic Event

---

## 7. Ограничения Cross-Browser Compatibility

### 7.1 XMLHttpRequest vs Fetch

**Проблема:** Предпочтение XHR над fetch.

```javascript
// Testing shows XMLHttpRequest to be faster than fetch on Chrome and Firefox
const request = new XMLHttpRequest();
```

**Ограничения:**
- XHR не поддерживает streaming responses
- XHR callback hell vs fetch async/await
- CORS limitations специфичны для XHR

**Edge cases:**
- Large JSON files → no progress indication
- Request cancellation требует `abort()`
- Modern features (RequestPriority) недоступны

**Mitigation:**
- Consider fetch для future browsers
- Implement wrapper для unified API
- Polyfill для old browsers

### 7.2 Service Worker Cache

**Проблема:** Service worker кэширует файлы агрессивно.

**Ограничения:**
- Development changes не видны без hard reload
- No automatic cache invalidation
- Service worker не в репозитории (built locally)

**Edge cases:**
- Developer меняет JSON → не видит changes
- User видит stale content после deployment
- Cache poisoning possibility (malicious SW)

**Mitigation:**
- Disable SW в development mode
- Implement cache versioning
- Provide "Clear Cache" button для users

---

## 8. Рекомендации для Future Development

### 8.1 Priority 1 (Critical)
1. **Implement LRU cache** для `DataUtil._loaded` to prevent memory leaks
2. **Add timeout handling** для all async operations (init, loading, merging)
3. **Improve error messages** для unknown hash situations

### 8.2 Priority 2 (Important)
4. **Consider IndexedDB** вместо localStorage для brew storage
5. **Implement request cancellation** с AbortController
6. **Add progress indicators** для large data operations

### 8.3 Priority 3 (Nice to Have)
7. **Migrate to fetch API** для better streaming support
8. **Implement hash versioning** для backward compatibility
9. **Add telemetry** для monitoring performance issues

---

## 9. Testing Checklist

Для тестирования edge cases:

- [ ] Load 50+ different pages and monitor memory usage
- [ ] Delete homebrew while viewing it in hash
- [ ] Rapid navigation between unknown hashes
- [ ] Drag and drop 50 JSON files simultaneously
- [ ] Fill localStorage to quota limit
- [ ] Trigger GitHub rate limit intentionally
- [ ] Load page with entity name containing separator characters
- [ ] Navigate to bookmark with old hash format
- [ ] Open multiple tabs with same hash
- [ ] Test on mobile device with limited memory

---

## 10. Ограничения PDF Files (Image References)

### 10.1 Broken PDF Files in XDMG

**Проблема:** Некоторые PDF файлы в `img/pdf/XDMG/` повреждены.

**Файлы с ошибками:**
- `XDMG/001-travel-planner.pdf`
- `XDMG/002-npc-tracker-sheet.pdf`
- `XDMG/003-settlement-tracker.pdf`
- `XDMG/004-campaign-journal-sheet.pdf`
- `XDMG/005-character-tracker.pdf`
- `XDMG/006-campaign-conflict-sheet.pdf`

**Описание проблемы:**
Файлы 001-006 содержат HTML error pages (404 Not Found от D&D Beyond) вместо PDF контента. Корректные PDF файлы существуют под номерами 010-015.

**Диагностика:**
```bash
# Проверка заголовка файла
head -c 4 img/pdf/XDMG/001-travel-planner.pdf
# Вывод: <!DO (вместо %PDF)

# Корректный PDF
head -c 4 img/pdf/XDMG/010-travel-planner.pdf
# Вывод: %PDF
```

**Неправильные ссылки в данных:**
```json
// data/book/book-xdmg.json:3232
"title": "{@5etoolsImg Download PDF|pdf/XDMG/001-travel-planner.pdf}"
// Должно быть:
"title": "{@5etoolsImg Download PDF|pdf/XDMG/010-travel-planner.pdf}"
```

**Impact:**
- Пользователи видят 404 error при попытке скачать PDF
- 6 ссылок в `book-xdmg.json` указывают на битые файлы
- Обнаружено валидатором `scripts/validation/check_pdf.py`

**Mitigation:**
1. Заменить файлы 001-006 на корректные PDF (скачать с источника)
2. Или обновить ссылки в JSON на 010-015
3. Удалить битые файлы и обновить ссылки

### 10.2 Unreferenced PDF Files

**Проблема:** 19 PDF файлов не referenced в JSON данных.

**Файлы без ссылок:**
- `AZfyT/*.pdf` (10 файлов) - Character sheets из AZfyT adventure
- `LRDT/*.pdf` (4 файла) - Character sheets из Lost Mine of Phandelver
- `MGELFT/Character Sheet.pdf` - Character sheet из MGELFT
- `RMBRE/*.pdf` (4 файла) - Character sheets из RMBRE adventure

**Возможные причины:**
- PDF загружены вручную, но не интегрированы в данные
- JSON данные не обновлены после загрузки PDF
- Преднамеренно не включены в UI (backup/reserve)

**Recommendation:**
- Проверить, должны ли эти файлы быть доступны в UI
- Добавить ссылки в соответствующие JSON файлы или удалить файлы

---

## 11. Related Documentation

- [docs/coordination.md](coordination.md) - Архитектура координации
- [docs/data-validation.md](data-validation.md) - Валидация данных
- [docs/images.md](images.md) - Система изображений
- [scripts/validation/README.md](../scripts/validation/README.md) - Валидационные скрипты
- [js/utils.js:4560+](../js/utils.js) - DataUtil implementation
- [js/hist.js](../js/hist.js) - Hist implementation
- [js/listpage.js:1328+](../js/listpage.js) - ListPage implementation
