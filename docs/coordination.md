# Главный модуль координации

## Обзор

Система координации 5etools управляет загрузкой данных, инициализацией страниц, навигацией и взаимодействием между всеми модулями. Это "клей" который связывает:

- Загрузку данных (DataUtil, DataLoader)
- Рендеринг контента (Renderer)
- Управление состоянием (Hist, UrlUtil)
- Фильтрацию (PageFilter)
- Homebrew/Prerelease контент (BrewUtil2, PrereleaseUtil)
- Исключения (ExcludeUtil)

## Архитектура

### 1. Страница приложения (index.html)

**Главная страница** (index.html):
- Навигационное меню: `<nav id="navigation">`
- Контент: `<div id="pagecontent">`
- Табы: `<div id="stat-tabs">`
- Список: `<div id="list">`
- Фильтры: `<div id="filter-search-group">`

**Скрипты:**
```html
<script blocking="render" type="module" src="js/styleswitch.js"></script>
<script type="text/javascript" src="js/navigation.js"></script>
<script type="module" src="js/browsercheck.js"></script>
```

### 2. IndexPage (js/index.js)

**Главная страница координации:**

```javascript
class IndexPage {
  static async _pOnLoad_pInitGeneric () {
    await Promise.all([
      PrereleaseUtil.pInit(),
      BrewUtil2.pInit(),
    ]);
    ExcludeUtil.pInitialise().then(null);
  }

  static async pOnLoad () {
    await this._pOnLoad_pInitGeneric();
    this._pOnLoad_initElements();
    await this._pOnLoad_pAddHashChangeListener();

    window.dispatchEvent(new Event("toolsLoaded"));
  }

  static async _pOnHashChange () {
    await ManageExternalUtils.pAddSourcesFromHash();
  }
}
```

**Инициализация при загрузке:**
1. Инициализация PrereleaseUtil и BrewUtil2 (параллельно)
2. Инициализация ExcludeUtil
3. Настройка элементов UI
4. Добавление обработчика hashchange
5. Dispatch события "toolsLoaded"

## 3. ListPage (js/listpage.js)

**Базовый класс для всех страниц-списков** (spells, items, bestiary и т.д.):

```javascript
class ListPage {
  constructor (opts) {
    this._styleHint = VetoolsConfig.get("styleSwitcher", "style");
    this._dataSource = opts.dataSource;
    this._prereleaseDataSource = opts.prereleaseDataSource;
    this._brewDataSource = opts.brewDataSource;
    this._pFnGetFluff = opts.pFnGetFluff;
    this._pageFilter = opts.pageFilter;
    this._dataProps = opts.dataProps;
  }

  async pOnLoad () {
    Hist.setListPage(this);

    this._pOnLoad_findPageElements();

    // 1. Инициализация brew/prerelease
    await Promise.all([
      PrereleaseUtil.pInit(),
      BrewUtil2.pInit(),
    ]);
    await ExcludeUtil.pInitialise();

    // 2. Настройка настроек
    await this._pOnLoad_pInitSettingsManager();

    // 3. Загрузка данных (до фильтров)
    let data;
    if (!this._isLoadDataAfterFilterInit) {
      await this._pOnLoad_pPreDataLoad();
      data = await this._pOnLoad_pGetData();
    }

    // 4. Инициализация списков и фильтров
    await this._pOnLoad_pInitPrimaryLists();

    // 5. Загрузка данных (после фильтров)
    if (this._isLoadDataAfterFilterInit) {
      await this._pOnLoad_pPreDataLoad();
      data = await this._pOnLoad_pGetData();
    }

    // 6. Инициализация UI
    this._pOnLoad_initVisibleItemsDisplay();

    if (this._sublistManager) {
      await this._sublistManager.pCreateSublist();
    }

    await this._pOnLoad_pPreDataAdd();
    this._addData(data);

    if (this._pageFilter) this._pageFilter.trimState();

    await this._pOnLoad_pLoadListState();
    this._pOnLoad_bindMiscButtons();
    this._pOnLoad_pBookView().then(null);
    this._pOnLoad_tableView();

    // 7. Настройка истории
    Hist.setFnLoadHash(this.pDoLoadHash.bind(this));
    Hist.setFnLoadSubHash(this.pDoLoadSubHash.bind(this));
    Hist.setFnHandleUnknownHash(this.pHandleUnknownHash.bind(this));

    this.primaryLists.forEach(list => list.init({...}));
    if (this._sublistManager) this._sublistManager.init();

    Hist.init(true);

    ListPage._checkShowAllExcluded(this._dataList, this._pgContent);

    if (this._filterBox) this._filterBox.on(FILTER_BOX_EVNT_VALCHANGE, this.handleFilterChange.bind(this));
    this.handleFilterChange();

    await this._pOnLoad_pPostLoad();

    window.dispatchEvent(new Event("toolsLoaded"));
  }
}
```

**Поток загрузки данных:**

```javascript
async _pOnLoad_pGetData () {
  // 1. Загрузка основного JSON
  const data = await (typeof this._dataSource === "string"
    ? DataUtil.loadJSON(this._dataSource)
    : this._dataSource());

  // 2. Загрузка prerelease
  const prerelease = await (this._prereleaseDataSource
    ? this._prereleaseDataSource()
    : PrereleaseUtil.pGetBrewProcessed());

  // 3. Загрузка homebrew
  const homebrew = await (this._brewDataSource
    ? this._brewDataSource()
    : BrewUtil2.pGetBrewProcessed());

  // 4. Мерджинг всех данных
  return BrewUtil2.getMergedData(
    PrereleaseUtil.getMergedData(data, prerelease),
    homebrew
  );
}
```

**Добавление данных в список:**

```javascript
_addData (data) {
  if (!this._dataProps.some(prop => data[prop] && data[prop].length)) return;

  // Чанкование для избежания переполнения стека
  for (const prop of this._dataProps) {
    const len = data[prop]?.length || 0;
    if (!len) continue;

    for (let i = 0; i < len; i += this.constructor._MAX_DATA_CHUNK_SIZE) {
      const chunk = data[prop].slice(i, i + this.constructor._MAX_DATA_CHUNK_SIZE);
      this._dataList.push(...chunk);
    }
  }

  // Создание list items
  const len = this._dataList.length;
  for (; this._ixData < len; this._ixData++) {
    const it = this._dataList[this._ixData];
    const isExcluded = ExcludeUtil.isExcluded(
      UrlUtil.autoEncodeHash(it),
      it.__prop,
      it.source
    );
    const listItem = this.getListItem(it, this._ixData, isExcluded);
    if (!listItem) continue;
    if (this._isPreviewable) this._doBindPreview(listItem);
    this._addListItem(listItem);
  }

  this.primaryLists.forEach(list => list.update());
}
```

## 4. DataUtil (js/utils.js:4560+)

**Главный модуль работы с данными:**

```javascript
globalThis.DataUtil = class {
  static _loading = {};  // Активные загрузки
  static _loaded = {};   // Кэш загруженных данных
  static _merging = {};  // Активный мерджинг
  static _merged = {};   // Кэс слитых данных

  // Rate limiting
  static REQUEST_LIMITER_GITHUB_RAW = new this._RequestLimiter({
    urlPrefix: "https://raw.githubusercontent.com/",
    timeoutMs: 15 * 60 * 1000, // 15 mins
  });

  // Основной метод загрузки JSON
  static async loadJSON (url) {
    return DataUtil._loadJson(url, {isDoDataMerge: true});
  }

  // Сырая загрузка без мерджинга
  static async loadRawJSON (url, {isBustCache} = {}) {
    return DataUtil._loadJson(url, {isBustCache});
  }

  // Внутренняя загрузка
  static async _loadJson (url, {isDoDataMerge = false, isBustCache = false} = {}) {
    const procUrl = UrlUtil.link(url, {isBustCache});

    let data;
    try {
      data = await DataUtil._pLoad({url: procUrl, id: url, isBustCache});
    } catch (e) {
      setTimeout(() => { throw e; });
    }

    // Fallback к необработанному URL
    if (!data) data = await DataUtil._pLoad({url: url, id: url, isBustCache});

    if (isDoDataMerge) await DataUtil.pDoMetaMerge(url, data);

    return data;
  }

  // Загрузка с GitHub rate limiting fallback
  static async _pLoad_pGetJson ({url, id}) {
    const optionalJsonBase = await this._pLoad_pGetJson_pGetOptionalJson({url});
    if (optionalJsonBase.json) return DataUtil._loaded[id] = optionalJsonBase.json;

    // Fallback на jsDelivr
    if (optionalJsonBase.isJsdelivrRetry()) {
      const urlJsDelivr = optionalJsonBase.getJsDelivrUrl();
      const optionalJsonJsDelivr = await this._pLoad_pGetJson_pGetOptionalJson({url: urlJsDelivr});
      if (optionalJsonJsDelivr.json) return DataUtil._loaded[id] = optionalJsonJsDelivr.json;
    }

    // Fallback на GitHack
    if (optionalJsonBase.isGitHackRetry()) {
      const urlGitHack = optionalJsonBase.getGithackUrl();
      const optionalJsonGitHack = await this._pLoad_pGetJson_pGetOptionalJson({url: urlGitHack});
      if (optionalJsonGitHack.json) return DataUtil._loaded[id] = optionalJsonGitHack.json;
    }

    throw new Error(optionalJsonBase.error);
  }

  // Кэшированная загрузка
  static async _pLoad ({url, id, isBustCache = false}) {
    if (DataUtil._loading[id] && !isBustCache) {
      await DataUtil._loading[id];
      return DataUtil._loaded[id];
    }

    DataUtil._loading[id] = DataUtil._pLoad_pGetJson({url, id});

    await DataUtil._loading[id];
    return DataUtil._loaded[id];
  }

  // Meta-мерджинг (копии, исходники и т.д.)
  static async pDoMetaMerge (ident, data, options) {
    DataUtil._mutAddProps(data);

    const isFresh = !DataUtil._merging[ident];

    DataUtil._merging[ident] ||= DataUtil._pDoMetaMerge(ident, data, options);
    await DataUtil._merging[ident];
    const out = DataUtil._merged[ident];

    if (options?.isSkipMetaMergeCache) {
      delete DataUtil._merging[ident];
      delete DataUtil._merged[ident];
    }

    if (isFresh) DataUtil._verifyMerged(out);

    return out;
  }

  // Добавление __prop к каждой entity
  static _mutAddProps (data) {
    if (!data || typeof data !== "object") return;

    for (const k in data) {
      if (!(data[k] instanceof Array)) continue;

      for (const it of data[k]) {
        if (typeof it !== "object") continue;
        it.__prop = k;
      }
    }
  }

  // Проверка на unresolved _copy
  static _verifyMerged (data) {
    if (!data || typeof data !== "object") return;

    for (const k in data) {
      if (!(data[k] instanceof Array)) continue;

      for (const it of data[k]) {
        if (typeof it !== "object") continue;
        if (it._copy) {
          setTimeout(() => { throw new Error(`Unresolved "_copy" in entity: ${JSON.stringify(it)}`); });
        }
      }
    }
  }
}
```

**Prop-специфичные утилиты:**

```javascript
class _DataUtilPropConfig {
  static async loadRawJSON () {
    return DataUtil.loadRawJSON(this.getDataUrl());
  }

  static async loadUnmergedJSON () {
    return DataUtil.loadRawJSON(this.getDataUrl());
  }

  static async pMergeCopy (lst, ent, options) {
    return DataUtil.generic._pMergeCopy(this, this._PAGE, lst, ent, options);
  }
}
```

## 5. Hist (js/hist.js)

**Управление историей и URL хешами:**

```javascript
class Hist {
  static lastLoadedLink = null;
  static lastLoadedId = null;
  static initialLoad = true;
  static isHistorySuppressed = false;

  static _pHandleUnknownHash = null;
  static _pLoadHash = null;
  static _pLoadSubHash = null;

  static setFnHandleUnknownHash (fn) { this._pHandleUnknownHash = fn; }
  static setFnLoadHash (fn) { this._pLoadHash = fn; }
  static setFnLoadSubhash (fn) { this._pLoadSubHash = fn; }

  static hashChange ({isForceLoad, isBlankFilterLoad = false} = {}) {
    if (this.isHistorySuppressed) return this.setSuppressHistory(false);

    const [link, ...sub] = this.getHashParts();

    if (link !== this.lastLoadedLink || sub.length === 0 || isForceLoad) {
      this.lastLoadedLink = link;
      if (link === HASH_BLANK) {
        isBlankFilterLoad = true;
      } else {
        const listItem = this.getActiveListItem(link);

        if (listItem == null) {
          // Unknown hash - может быть homebrew
          if (typeof this._pHandleUnknownHash === "function" && window.location.hash.length) {
            this._pLoadingUnknownHash = this._pHandleUnknownHash(link, sub);
            return;
          } else {
            this._freshLoad();
            return;
          }
        }

        const toLoad = listItem.ix;
        if (toLoad === undefined) this._freshLoad();
        else {
          this.lastLoadedId = listItem.ix;
          this._pLoadHash(listItem.ix);
          document.title = `${listItem.name} - 5etools`;
        }
      }
    }

    if (typeof this._pLoadSubHash === "function" && (sub.length > 0 || isForceLoad)) {
      this._pLoadSubHash(sub);
    }
    if (isBlankFilterLoad) this._freshLoad();
  }

  static init (initialLoadComplete) {
    window.onhashchange = () => Hist.hashChange({isForceLoad: true});
    if (window.location.hash.length) {
      Hist.hashChange();
    } else {
      Hist._freshLoad();
    }
    if (initialLoadComplete) Hist.initialLoad = false;
  }

  static setListPage (listPage) { this._listPage = listPage; }

  static getHashParts () {
    return Hist.util.getHashParts(window.location.hash);
  }

  static getActiveListItem (link, getIndex) {
    const primaryLists = this._listPage.primaryLists;
    if (primaryLists && primaryLists.length) {
      for (let x = 0; x < primaryLists.length; ++x) {
        const list = primaryLists[x];
        const foundItemIx = list.items.findIndex(it => it.values.hash === link);
        if (~foundItemIx) {
          if (getIndex) return {item: list.items[foundItemIx], x: x, y: foundItemIx, list};
          return list.items[foundItemIx];
        }
      }
    }
  }

  static _freshLoad () {
    // Задержка для фильтрации списка
    (this._pLoadingUnknownHash || Promise.resolve())
      .then(() => {
        setTimeout(() => {
          const goTo = es("#listcontainer").findAll(".list a")[0]?.attr("href");
          if (!goTo) return;

          const parts = location.hash.split(HASH_PART_SEP);
          const fullHash = `${goTo}${parts.length > 1 ? `${HASH_PART_SEP}${parts.slice(1).join(HASH_PART_SEP)}` : ""}`;
          location.replace(fullHash);
        }, 1);
      });
  }
}
```

## 6. UrlUtil (js/utils.js:3421+)

**Работа с URL и хешами:**

```javascript
globalThis.UrlUtil = {
  // Кодирование для хеша
  encodeForHash (toEncode) {
    if (toEncode instanceof Array) return toEncode.map(it => `${it}`.toUrlified()).join(HASH_LIST_SEP);
    else return `${toEncode}`.toUrlified();
  },

  // Авто-кодирование на основе текущей страницы
  autoEncodeHash (obj) {
    const curPage = UrlUtil.getCurrentPage();
    const encoder = UrlUtil.URL_TO_HASH_BUILDER[curPage];
    if (!encoder) throw new Error(`No encoder found for page ${curPage}`);
    return encoder(obj);
  },

  // Декодирование хеша
  decodeHash (hash) {
    return hash.split(HASH_LIST_SEP).map(it => decodeURIComponent(it));
  },

  // Авто-декодирование на основе страницы
  autoDecodeHash (hash, {page = null} = {}) {
    page ||= UrlUtil.getCurrentPage();
    const parts = UrlUtil.decodeHash(hash.toLowerCase().trim());

    // Deities
    if (page === UrlUtil.PG_DEITIES) {
      const [name, pantheon, source] = parts;
      return {name, pantheon, source};
    }

    // Class features
    if (page?.toLowerCase() === "classfeature") {
      const [name, className, classSource, levelRaw, source] = parts;
      return {name, className, classSource, level: Number(levelRaw) || 0, source};
    }

    // Subclass features
    if (page?.toLowerCase() === "subclassfeature") {
      const [name, className, classSource, subclassShortName, subclassSource, levelRaw, source] = parts;
      return {name, className, classSource, subclassShortName, subclassSource, level: Number(levelRaw) || 0, source};
    }

    // Adventures/Books
    if (page === UrlUtil.PG_ADVENTURE || page === UrlUtil.PG_BOOK) {
      const [source] = parts;
      return {source};
    }

    // Default
    const [name, source] = parts;
    return {name, source};
  },

  // Текущая страница
  getCurrentPage () {
    if (typeof window === "undefined") return VeCt.PG_NONE;
    const pSplit = window.location.pathname.split("/");
    let out = pSplit[pSplit.length - 1];
    if (!out.toLowerCase().endsWith(".html")) out += ".html";
    return out;
  },

  // Создание URL с static.5etools.com
  link (href, {isBustCache = false} = {}) {
    if (isBustCache) return UrlUtil._link_getWithParam(href, {param: `t=${Date.now()}`});
    return href;
  },

  // Unpack subhash (key:value~list~sep)
  unpackSubHash (subHash, unencode) {
    if (subHash.includes(HASH_SUB_KV_SEP)) {
      const keyValArr = subHash.split(HASH_SUB_KV_SEP).map(s => s.trim());
      const out = {};
      let k = keyValArr[0].toLowerCase();
      if (unencode) k = decodeURIComponent(k);
      let v = keyValArr[1].toLowerCase();
      if (unencode) v = decodeURIComponent(v);
      out[k] = v.split(HASH_SUB_LIST_SEP).map(s => s.trim());
      if (out[k].length === 1 && out[k] === HASH_SUB_NONE) out[k] = [];
      return out;
    } else {
      throw new Error(`Badly formatted subhash ${subHash}`);
    }
  },

  // Pack subhash
  packSubHash (key, values, opts) {
    opts = opts || {};
    if (opts.isEncodeBoth || opts.isEncodeKey) key = key.toUrlified();
    if (opts.isEncodeBoth || opts.isEncodeValues) values = values.map(it => it.toUrlified());
    return `${key}${HASH_SUB_KV_SEP}${values.join(HASH_SUB_LIST_SEP)}`;
  },

  // Мини-кодирование для subhash
  mini: {
    compress (primitive) {
      const type = typeof primitive;
      if (primitive === undefined) return "u";
      if (primitive === null) return "x";
      switch (type) {
        case "boolean": return `b${Number(primitive)}`;
        case "number": return `n${primitive}`;
        case "string": return `s${primitive.toUrlified()}`;
        default: throw new Error(`Unhandled type "${type}"`);
      }
    },

    decompress (raw) {
      if (!raw) return null;
      const type = raw[0];
      switch (type) {
        case "u": return undefined;
        case "x": return null;
        case "b": return Boolean(Number(raw.slice(1)));
        case "n": return Number(raw.slice(1));
        case "s": return raw.slice(1).fromUrlified();
        default: throw new Error(`Unknown mini-encoded type: "${type}"`);
      }
    }
  }
}
```

## 7. BrewUtil2Base (js/utils-brew/utils-brew-base.js)

**Базовый класс для BrewUtil2 и PrereleaseUtil:**

```javascript
export class BrewUtil2Base {
  _cache_iteration = 0;
  _cache_brewsProc = null;
  _cache_metas = null;
  _cache_sourceStyles = null;
  _cache_brews = null;
  _cache_brewsLocal = null;

  _isDirty = false;
  _brewsTemp = [];
  _addLazy_brewsTemp = [];

  _LOCK = new VeLock({name: this.constructor.name});

  pInit () {
    this._pActiveInit ||= (async () => {
      // Обеспечить кэш local brew
      await this._pGetBrew_pGetLocalBrew();

      this._pInit_doBindDragDrop();
      this._pInit_pDoLoadFonts().then(null);
      await this._pInit_pDoShowReloadMessage();
    })();
    return this._pActiveInit;
  }

  // Drag & drop для JSON файлов
  static _initSharedDragDrop () {
    if (this._IS_INIT_SHARED_DRAG_DROP) return;

    document.body.addEventListener("drop", async evt => {
      if (EventUtil.isInInput(evt)) return;

      evt.stopPropagation();
      evt.preventDefault();

      const files = evt.dataTransfer?.files;
      if (!files?.length) return;

      const pFiles = [...files].map((file, i) => {
        if (!/\.json$/i.test(file.name)) return null;

        return new Promise(resolve => {
          const reader = new FileReader();
          reader.onload = () => {
            let json;
            try {
              json = JSON.parse(reader.result);
            } catch (ignored) {
              return resolve(null);
            }
            resolve({name: file.name, json});
          };
          reader.readAsText(files[i]);
        });
      });

      const fileMetas = (await Promise.allSettled(pFiles))
        .filter(({status}) => status === "fulfilled")
        .map(({value}) => value)
        .filter(Boolean);

      // Разделение на prerelease и brew
      const [prereleaseFileMetas, brewFileMetas] = fileMetas.segregate(fileMeta => this._isPrereleaseDroppedJson(fileMeta.json));

      if (prereleaseFileMetas.length) await PrereleaseUtil.pAddBrewsFromFiles(prereleaseFileMetas);
      if (brewFileMetas.length) await BrewUtil2.pAddBrewsFromFiles(brewFileMetas);

      [PrereleaseUtil, BrewUtil2]
        .find(it => it.isReloadRequired())
        ?.doLocationReload();
    });
  }
}
```

## 8. PrereleaseUtil_ (js/utils-brew/utils-brew-impl-prerelease.js)

**Prerelease контент (Unearthed Arcana):**

```javascript
export class PrereleaseUtil_ extends BrewUtil2Base {
  _STORAGE_KEY = "PRERELEASE_STORAGE";
  _STORAGE_KEY_META = "PRERELEASE_META_STORAGE";
  _STORAGE_KEY_RELOAD_MESSAGE = "PRERELEASE_RELOAD_MESSAGE";
  _STORAGE_KEY_CUSTOM_URL = "PRERELEASE_CUSTOM_REPO_URL";

  _PATH_LOCAL_DIR = "prerelease";
  _PATH_LOCAL_INDEX = VeCt.JSON_PRERELEASE_INDEX;

  _VERSION = 1;

  IS_EDITABLE = false;  // Только чтение
  PAGE_MANAGE = UrlUtil.PG_MANAGE_PRERELEASE;
  URL_REPO_DEFAULT = VeCt.URL_PRERELEASE;
  URL_REPO_ROOT_DEFAULT = VeCt.URL_ROOT_PRERELEASE;
  DISPLAY_NAME = "prerelease content";
  DISPLAY_NAME_PLURAL = "prereleases";
  DEFAULT_AUTHOR = "Wizards of the Coast";

  // DataUtil hooks
  async pGetSourceIndex (urlRoot) { return DataUtil.prerelease.pLoadSourceIndex(urlRoot); }
  getFileUrl (path, urlRoot) { return DataUtil.prerelease.getFileUrl(path, urlRoot); }
  pLoadTimestamps (urlRoot) { return DataUtil.prerelease.pLoadTimestamps(urlRoot); }
  pLoadPropIndex (urlRoot) { return DataUtil.prerelease.pLoadPropIndex(urlRoot); }
  pLoadMetaIndex (urlRoot) { return DataUtil.prerelease.pLoadMetaIndex(urlRoot); }
  pLoadAdventureBookIdsIndex (urlRoot) { return DataUtil.prerelease.pLoadAdventureBookIdsIndex(urlRoot); }
}
```

## Поток выполнения (Execution Flow)

### 1. Инициализация приложения

```
window.onload
  ↓
IndexPage.pOnLoad()
  ↓
PrereleaseUtil.pInit() ─────┐
BrewUtil2.pInit()            ├─→ Promise.all
ExcludeUtil.pInitialise()  ──┘
  ↓
_pOnLoad_initElements()
  ↓
_pOnLoad_pAddHashChangeListener()
  ↓
window.dispatchEvent("toolsLoaded")
```

### 2. Загрузка страницы списка

```
ListPage.pOnLoad()
  ↓
Hist.setListPage(this)
  ↓
_pOnLoad_findPageElements()
  ↓
PrereleaseUtil.pInit() ─────┐
BrewUtil2.pInit()            ├─→ Promise.all
ExcludeUtil.pInitialise()  ──┘
  ↓
_pOnLoad_pInitSettingsManager()
  ↓
_pOnLoad_pGetData()
  ↓
DataUtil.loadJSON(dataSource) ──→ Основной JSON
  ↓
PrereleaseUtil.pGetBrewProcessed() ──→ Prerelease контент
  ↓
BrewUtil2.pGetBrewProcessed() ──→ Homebrew контент
  ↓
BrewUtil2.getMergedData() ──→ Мерджинг всех данных
  ↓
_pOnLoad_pInitPrimaryLists()
  ↓
_addData() ──→ Создание list items
  ↓
Hist.init(true) ──→ Обработка hashchange
  ↓
handleFilterChange()
  ↓
_pOnLoad_pPostLoad()
  ↓
window.dispatchEvent("toolsLoaded")
```

### 3. Навигация по хешу

```
window.onhashchange
  ↓
Hist.hashChange()
  ↓
Hist.getHashParts() ──→ [hash, subhash1, subhash2, ...]
  ↓
Hist.getActiveListItem(hash)
  ↓
_pLoadHash(ix) ──→ Загрузка entity
  ↓
document.title = "${name} - 5etools"
  ↓
_pLoadSubHash(sub) ──→ Subhash (scaled, filter state, etc.)
```

### 4. Unknown hash (homebrew)

```
Hist.hashChange()
  ↓
getActiveListItem() returns null
  ↓
_pHandleUnknownHash(link, sub)
  ↓
// Попытка загрузить из brew/prerelease
BrewUtil2.pGetBrewProcessed() / PrereleaseUtil.pGetBrewProcessed()
  ↓
// Если найдено → перезагрузка страницы
location.reload()
```

## Ключевые файлы

- `index.html` - Главная страница
- `js/index.js` - IndexPage координация
- `js/listpage.js` - ListPage базовый класс
- `js/utils.js:4560+` - DataUtil класс
- `js/utils.js:3421+` - UrlUtil объект
- `js/hist.js` - Hist класс
- `js/utils-brew/utils-brew-base.js` - BrewUtil2Base
- `js/utils-brew/utils-brew-impl-prerelease.js` - PrereleaseUtil
- `js/utils-dataloader.js` - DataLoader
- `js/render.js` - Renderer
- `js/utils.js:8898+` - ExcludeUtil

## Архитектурные паттерны

1. **Dependency Injection** - opts в ListPage конструкторе
2. **Promise.all Parallelization** - Параллельная инициализация
3. **Caching Layers** - _loading, _loaded, _merging, _merged
4. **Event Dispatching** - "toolsLoaded" событие
5. **Hash-based Navigation** - Hist для SPA навигации
6. **Fallback Strategy** - GitHub → jsDelivr → GitHack
7. **Chunked Processing** - MAX_DATA_CHUNK_SIZE для стека
8. **Merge Pipeline** - data → prerelease → homebrew
9. **Shared Drag & Drop** - Общий для brew/prerelease
10. **Lock-based Concurrency** - VeLock для синхронизации

## Статистика

- **~60 страниц** наследуют ListPage
- **3 уровня кэша** в DataUtil
- **2 brew системы** (Prerelease + Homebrew)
- **15 mins** GitHub rate limit timeout
- **4096** MAX_DATA_CHUNK_SIZE
- **4 разделителя хеша**: HASH_PART_SEP, HASH_LIST_SEP, HASH_SUB_LIST_SEP, HASH_SUB_KV_SEP
- **6 fallback URL** (GitHub raw, jsDelivr, GitHack)
- **3 состояния загрузки**: loading, loaded, merged

## Типичные use cases

### 1. Загрузка страницы спеллов

```
SpellsPage.pOnLoad()
  ↓
DataUtil.loadJSON("data/spells.json")
  ↓
PrereleaseUtil.pGetBrewProcessed() ──→ prerelease/spells.json
  ↓
BrewUtil2.pGetBrewProcessed() ──→ homebrew/spells.json
  ↓
BrewUtil2.getMergedData() ──→ {spell: [...merged spells...]}
  ↓
_addData() ──→ _dataList.push(...spells)
  ↓
Hist.init() ──→ Обработка #fireball%PHB
```

### 2. Drag & drop homebrew

```
document.body.ondrop
  ↓
FileReader.readAsText()
  ↓
JSON.parse()
  ↓
_isPrereleaseDroppedJson() ──→ Проверка sources
  ↓
PrereleaseUtil.pAddBrewsFromFiles() / BrewUtil2.pAddBrewsFromFiles()
  ↓
StorageUtil.syncSet() ──→ localStorage
  ↓
doLocationReload() ──→ location.reload()
```

### 3. GitHub rate limit fallback

```
DataUtil._pLoad_pGetJson({url: "https://raw.githubusercontent.com/..."})
  ↓
XMLHttpRequest.status === 429
  ↓
REQUEST_LIMITER_GITHUB_RAW.addFailure()
  ↓
_pLoad_pGetJson({url: "https://cdn.jsdelivr.net/gh/..."})
  ↓
Success → DataUtil._loaded[url] = data
```

### 4. Hash navigation

```
location.hash = "#fireball%PHB,f精确:2~3"
  ↓
Hist.hashChange()
  ↓
Hist.getHashParts() ──→ ["fireball%phb", "f精确:2", "3"]
  ↓
Hist.getActiveListItem("fireball%phb")
  ↓
_pLoadHash(42) ──→ fireball ix=42
  ↓
_pLoadSubHash(["f精确:2", "3"])
  ↓
UrlUtil.unpackSubHash("f精确:2", true) ──→ {精确: ["2"]}
  ↓
FilterBox.fromStoredState({精确: ["2"]})
```

### 5. Meta merge (copy resolution)

```
DataUtil.loadJSON("data/spells.json")
  ↓
DataUtil.pDoMetaMerge()
  ↓
_pDoMetaMerge()
  ↓
_pDoMetaMerge_handleCopyProp("spell", arr, entry)
  ↓
DataUtil.spell.pMergeCopy(arr, entry)
  ↓
_gatherCopyCopies() ──→ Поиск _copy
  ↓
_generic_pMergeCopy_copy() ──→ Глубокий копирования
  ↓
_generic_pMergeCopy_postCopy() ──→ Пост-обработка
  ↓
_verifyMerged() ──→ Проверка на unresolved _copy
```
