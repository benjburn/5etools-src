# Система проверки целостности данных

## Обзор

5etools использует многоуровневую систему проверки целостности данных, которая гарантирует корректность всех JSON файлов, ссылок, изображений и cross-reference между сущностями.

## Архитектура тестирования

### 1. Тест-оркестратор (test/test-all.js)

**Главный вход для всех тестов:**

```javascript
async function main () {
  // 1. Tag validation (критично)
  if (!(await (await import("./test-tags.js")).default)) handleFail();

  // 2. Image validation (критично)
  if (!(await (await import("./test-images.js")).default)) handleFail();

  // 3. Image path validation (критично)
  if (!(await (await import("./test-image-paths.js")).default)) handleFail();

  // 4. Page numbers (некритично - только логирование)
  await (await import("./test-pagenumbers.js")).default;

  // 5. Image credits (некритично - только логирование)
  await (await import("./test-image-credits.js")).default;

  // 6. JSON schema validation (критично)
  if (!(await (await import("./test-json.js")).default)) handleFail();

  // 7. Misc checks (критично)
  if (!(await (await import("./test-misc.js")).default)) handleFail();

  // 8. Multisource validation (критично)
  if (!(await (await import("./test-multisource.js")).default)) handleFail();

  // 9. Language fonts validation (критично)
  if (!(await (await import("./test-language-fonts.js")).default)) handleFail();

  // 10. Map names validation (критично)
  if (!(await (await import("./test-map-names.js")).default)) handleFail();

  // 11. Adventure/book contents validation (критично)
  if (!(await (await import("./test-adventure-book-contents.js")).default)) handleFail();

  // 12. Map grids/parents (некритично)
  await (await import("./test-map-grids-parents.js")).default;

  // 13. Foundry validation (критично)
  if (!(await (await import("./test-foundry.js")).default)) handleFail();

  process.exit(0);
}
```

**Запуск:**
```bash
npm test              # Все тесты
npm run test:json     # Только JSON schema
npm run test:tags     # Только теги
npm run test:data     # JSON + tags
```

## 2. JSON Schema Validation (test/test-json.js)

**AJV-based schema validation:**

```javascript
import {Um, Uf, JsonTester} from "5etools-utils";

const jsonTester = new JsonTester({
  tagLog: LOG_TAG,
  fnGetSchemaId: (filePath) => {
    const relativeFilePath = filePath.replace("data/", "");

    // Adventure schema
    if (relativeFilePath.startsWith("adventure/")) return "adventure/adventure.json";
    // Book schema
    if (relativeFilePath.startsWith("book/")) return "book/book.json";
    // Bestiary schema
    if (relativeFilePath.startsWith("bestiary/bestiary-")) return "bestiary/bestiary.json";
    if (relativeFilePath.startsWith("bestiary/fluff-bestiary-")) return "bestiary/fluff-bestiary.json";
    // Class schema
    if (relativeFilePath.startsWith("class/class-")) return "class/class.json";
    if (relativeFilePath.startsWith("class/fluff-class-")) return "class/fluff-class.json";
    // Spells schema
    if (relativeFilePath.startsWith("spells/spells-")) return "spells/spells.json";
    if (relativeFilePath.startsWith("spells/fluff-spells-")) return "spells/fluff-spells.json";

    return relativeFilePath;
  },
});
await jsonTester.pInit();

// Сбор всех JSON файлов (кроме generated)
const fileList = Uf.listJsonFiles("data")
  .filter(filePath => {
    if (filePath.includes("data/generated")) return _GENERATED_ALLOWLIST.has(filePath.split("/").at(-1));
    return true;
  });

// Worker-based validation
const results = await jsonTester.pGetErrorsOnDirsWorkers({
  isFailFast: !_IS_FAIL_SLOW,
  fileList,
});

const {errors, errorsFull} = results;

if (errors.length) {
  if (!process.env.CI) fs.writeFileSync(`test/test-json.error.log`, errorsFull.join("\n\n=====\n\n"));
  console.error(`Schema test failed (${errors.length} failure${errors.length === 1 ? "" : "s"}).`);
  return false;
}

console.log(`All schema tests passed.`);
return true;
```

**Особенности:**
- Использует **AJV 8.12.0** для schema validation
- **Worker-based** параллельная обработка
- **Fail-fast** режим (или `FAIL_SLOW=1` для полного отчета)
- **Автоопределение schema** по пути файла
- **Generated allowlist**: только определенные файлы из `data/generated`

## 3. Tag Validation (test/test-tags.js)

**Проверка всех `{@tag}` ссылок:**

```javascript
class LinkCheck extends DataTesterBase {
  // Регулярка для поиска тегов
  static _RE = RegExp(
    `{@(${Renderer.tag.TAGS.filter(it => it.defaultSource).map(it => it.tagName).join("|")}) ([^}]*?)}`,
    "g"
  );

  registerParsedPrimitiveHandlers (parsedJsonChecker) {
    parsedJsonChecker.addPrimitiveHandler("string", this._checkString.bind(this));
    parsedJsonChecker.addPrimitiveHandler("object", this._checkObject.bind(this));
  }

  _checkString (str, {filePath}) {
    let match;
    while ((match = this.constructor._RE.exec(str))) {
      const [original, tag, text] = match;
      this._checkTagText({original, tag, text, filePath});
    }
  }

  _checkTagText ({original, tag, text, filePath}) {
    const tagMeta = Renderer.utils.getTagMeta(`@${tag}`, text);

    // Предпочитаем hashHover (указывает на реальную entity)
    const encoded = tagMeta.hashHover || tagMeta.hash;

    const url = `${tagMeta.page || Renderer.tag.getPage(tag)}#${encoded}`.toLowerCase().trim();

    if (!tagTestUrlLookup.hasUrl(url)) {
      this._addMessage(
        `Missing link: ${original} in file ${filePath} (evaluates to "${url}")\n` +
        `${tagTestUrlLookup.getLogPtSimilarUrls({url})}`
      );
    }

    // Специфические проверки для тегов
    switch (tag) {
      case "class":
        this._checkTagText_class({original, tag, text, filePath, tagMeta});
        break;
    }
  }

  _checkTagText_class ({original, tag, text, filePath, tagMeta}) {
    // {@class fighter|phb|and class feature added|Eldritch Knight|phb|2-0}
    if (!tagMeta.others?.length) return;

    let [subclassShortName, subclassSource, featurePart] = tagMeta.others;

    if (!subclassShortName) return;
    subclassSource ||= tagMeta.source;

    const featureIndex = tagTestUrlLookup.getSubclassFeatureIndex(
      tagMeta.name, tagMeta.source,
      subclassShortName, subclassSource
    );

    if (!featureIndex) {
      this._addMessage(
        `Missing subclass link: ${original} in file ${filePath} -- ` +
        `could not find subclass with matching subclassShortName/source\n`
      );
    }

    if (featureIndex && featurePart && !featureIndex.includes(featurePart)) {
      this._addMessage(
        `Malformed subclass link: ${original} in file ${filePath} -- ` +
        `feature index "${featurePart}" was outside expected range\n`
      );
    }
  }

  _checkObject (obj, {filePath}) {
    // Проверка statblock inline entities
    if (obj.type !== "statblock") return obj;

    const prop = obj.prop || Parser.getTagProps(obj.tag)[0];
    const tag = obj.tag || Parser.getPropTag(prop);

    const sourceDefault = Renderer.tag.TAG_LOOKUP[tag].defaultSource;
    const uid = DataUtil.proxy.getUid(prop, {...obj, source: obj.source || sourceDefault});

    this._checkTagText({original: JSON.stringify(obj), tag, text: uid, filePath, isStatblock: true});

    return obj;
  }
}
```

**FilterCheck** - валидация `{@filter}` тегов:

```javascript
class FilterCheck extends DataTesterBase {
  _checkString (str, {filePath}) {
    str.replace(/{@filter ([^}]*)}/g, (m0, m1) => {
      const spl = m1.split("|");
      if (spl.length < 3) {
        this._addMessage(`Invalid filter tag in file ${filePath}: "${str}" was too short!\n`);
        return m0;
      }

      if (!UrlUtil.pageToDisplayPage(`${spl[1]}.html`)) {
        this._addMessage(`Invalid filter tag in file ${filePath}: unknown page in "${str}"\n`);
      }
    });
  }
}
```

## 4. TagTestUrlLookup (test/test-tags/test-tags-entity-registry.js)

**Индекс всех URL для валидации ссылок:**

```javascript
export class TagTestUrlLookup {
  _ALL_URLS_SET = new Set();
  _ALL_URLS_LIST = [];
  _ALL_URLS_SET__VERSIONS = new Set();
  _ALL_URLS_LIST__VERSIONS = [];
  _CLASS_SUBCLASS_LOOKUP = {};

  async pInit () {
    await this._pInit_pPopulateUrls();
    await this._pInit_pPopulateUrlsAdditionalFluff();
    await this._pInit_pPopulateClassSubclassIndex();
  }

  async _pInit_pPopulateUrls () {
    // 1. Primary search index
    const primaryIndex = Omnidexer.decompressIndex(
      await utS.UtilSearchIndex.pGetIndex({doLogging: false, noFilter: true})
    );
    primaryIndex.forEach(indexItem => this._addIndexItem(indexItem));

    // 2. Additional item index
    const secondaryIndexItem = Omnidexer.decompressIndex(
      await utS.UtilSearchIndex.pGetIndexAdditionalItem({
        baseIndex: primaryIndex.last().id + 1,
        doLogging: false
      })
    );
    secondaryIndexItem.forEach(indexItem => this._addIndexItem(indexItem));

    // 3. Additional homebrew file (опционально)
    if (this._fileAdditional) {
      const brewIndexItems = Omnidexer.decompressIndex(
        await utS.UtilSearchIndex.pGetIndexLocalHomebrew({
          baseIndex: secondaryIndexItem.last().id + 1,
          filepath: this._fileAdditional
        })
      );
      brewIndexItems.forEach(indexItem => this._addIndexItem(indexItem));
    }

    // 4. Item properties
    (await DataLoader.pCacheAndGetAllSite("itemProperty"))
      .forEach(ent => this._addEntityItem(ent, "itemProperty"));

    // 5. Feat versions
    (await DataLoader.pCacheAndGetAllSite("feat"))
      .filter(ent => ent._versionBase_isVersion)
      .forEach(ent => this._addEntityItem(ent, UrlUtil.PG_FEATS));
  }

  async _pInit_pPopulateUrlsAdditionalFluff () {
    // Monster fluff
    (await DataUtil.monsterFluff.pLoadAll())
      .forEach(ent => this._addEntityItem(ent, "monsterFluff"));

    // Race fluff
    (await DataUtil.raceFluff.loadJSON()).raceFluff
      .forEach(ent => this._addEntityItem(ent, "raceFluff"));
  }

  async _pInit_pPopulateClassSubclassIndex () {
    const classData = await DataUtil.class.loadJSON();

    // Index всех классов
    classData.class.forEach(cls => {
      cls.name = cls.name.toLowerCase();
      cls.source = (cls.source || Parser.SRC_PHB).toLowerCase();

      this._CLASS_SUBCLASS_LOOKUP[cls.source] = this._CLASS_SUBCLASS_LOOKUP[cls.source] || {};
      this._CLASS_SUBCLASS_LOOKUP[cls.source][cls.name] = {};

      // Feature indices ["0-0", "0-1", "1-0", ...]
      const ixFeatures = [];
      cls.classFeatures.forEach((levelFeatures, ixLevel) => {
        levelFeatures.forEach((_, ixFeature) => {
          ixFeatures.push(`${ixLevel}-${ixFeature}`);
        });
      });
      MiscUtil.set(tmpClassIxFeatures, cls.source, cls.name, ixFeatures);
    });

    // Index всех subclass
    classData.subclass.forEach(sc => {
      sc.shortName = (sc.shortName || sc.name).toLowerCase();
      sc.source = (sc.source || sc.classSource).toLowerCase();
      sc.className = sc.className.toLowerCase();
      sc.classSource = sc.classSource.toLowerCase();

      if (sc.className === VeCt.STR_GENERIC.toLowerCase() &&
          sc.classSource === VeCt.STR_GENERIC.toLowerCase()) return;

      this._CLASS_SUBCLASS_LOOKUP[sc.classSource][sc.className][sc.source] =
        this._CLASS_SUBCLASS_LOOKUP[sc.classSource][sc.className][sc.source] || {};
      this._CLASS_SUBCLASS_LOOKUP[sc.classSource][sc.className][sc.source][sc.shortName] =
        MiscUtil.copyFast(MiscUtil.get(tmpClassIxFeatures, sc.classSource, sc.className));
    });
  }

  hasUrl (url) { return this._ALL_URLS_SET.has(url); }
  hasVersionUrl (url) { return this._ALL_URLS_SET__VERSIONS.has(url); }

  getSubclassFeatureIndex (className, classSource, subclassName, subclassSource) {
    classSource = classSource || Parser.getTagSource("class");
    subclassSource = subclassSource || Parser.SRC_PHB;

    return MiscUtil.get(
      this._CLASS_SUBCLASS_LOOKUP,
      classSource.toLowerCase(),
      className.toLowerCase(),
      subclassSource.toLowerCase(),
      subclassName.toLowerCase()
    );
  }

  getSimilarUrls (url) {
    const mSimilar = /^\w+\.html#\w+/.exec(url);
    if (!mSimilar) return [];

    return this._ALL_URLS_LIST
      .filter(url => url.startsWith(mSimilar[0]))
      .map(url => `\t${url}`)
      .join("\n");
  }
}
```

## 5. Entity File Handlers

**Базовый класс для entity-specific валидации:**

```javascript
export class EntityFileHandlerBase extends DataTesterBase {
  constructor ({tagTestUrlLookup}) {
    super();
    this._tagTestUrlLookup = tagTestUrlLookup;
  }

  registerParsedFileCheckers (parsedJsonChecker) {
    parsedJsonChecker.registerFileHandler(this);
  }

  async pHandleFile (filePath, contents) {
    const fileState = new this.constructor._FileState({filePath, contents});

    await this._pHandleFile_preProcess({filePath, contents, fileState});

    for (const [prop, arr] of Object.entries(contents)) {
      if (!(arr instanceof Array)) continue;

      const filename = filePath.split("/").at(-1);
      const propPrefixed = filename === "foundry.json" || filename.startsWith("foundry-")
        ? `foundry${prop.uppercaseFirst()}`
        : prop;

      if (!this._props.includes(propPrefixed)) continue;

      for (const ent of arr) {
        await this._pDoTestEntity({filePath, fileState, ent, prop, propPrefixed});
      }
    }
  }

  async _pDoTestEntity ({filePath, fileState, ent, prop, propPrefixed}) {
    throw new Error("Unimplemented!");
  }

  // Проверка seeAlso references
  _doCheckSeeAlso ({entity, prop, tag, file}) {
    if (!entity[prop]) return;

    const defaultSource = Parser.getTagSource(tag).toLowerCase();

    // Дедупликация
    const deduped = entity[prop].map(it => {
      it = it.toLowerCase();
      if (!it.includes("|")) it += `|${defaultSource}`;
      return it;
    }).unique();

    if (deduped.length !== entity[prop].length) {
      this._addMessage(`Duplicate "${prop}" in ${file} for ${entity.source}, ${entity.name}\n`);
    }

    entity[prop].forEach(s => {
      const url = this._tagTestUrlLookup.getEncodedProxy(s, tag);
      if (!this._tagTestUrlLookup.hasUrl(url)) {
        this._addMessage(
          `Missing link: ${s} in file ${file} (evaluates to "${url}") in "${prop}"\n` +
          `${this._tagTestUrlLookup.getLogPtSimilarUrls({url})}`
        );
      }
    });
  }

  // Проверка additionalSpells
  _testAdditionalSpells (file, obj) {
    if (!obj.additionalSpells) return;

    obj.additionalSpells.forEach(additionalSpellOption => {
      Object.entries(additionalSpellOption).forEach(([k, levelToSpells]) => {
        if (this.constructor._ADDITIONAL_SPELLS_IGNORED_KEYS.has(k)) return;

        Object.values(levelToSpells).forEach(spellListOrMeta => {
          if (spellListOrMeta instanceof Array) {
            return spellListOrMeta.forEach(sp => this._testAdditionalSpells_testSpellExists(file, sp));
          }

          Object.entries(spellListOrMeta).forEach(([prop, val]) => {
            switch (prop) {
              case "daily":
              case "rest":
              case "resource":
              case "limited":
                Object.values(val).forEach(spellList => spellList.forEach(sp => this._testAdditionalSpells_testSpellExists(file, sp)));
                break;
              case "will":
              case "ritual":
              case "_":
                val.forEach(sp => this._testAdditionalSpells_testSpellExists(file, sp));
                break;
            }
          });
        });
      });
    });
  }
}
```

**Пример: Spell handler:**

```javascript
export class EntityFileHandlerSpell extends EntityFileHandlerBase {
  _props = ["spell"];

  async _pDoTestEntity ({filePath, fileState, ent, prop, propPrefixed}) {
    // Проверка additionalSpells
    this._testAdditionalSpells(filePath, ent);

    // Проверка spell repetitive
    if (ent.spellRepitative) {
      const url = this._tagTestUrlLookup.getEncodedProxy(ent.spellRepitative, "spell");
      if (!this._tagTestUrlLookup.hasUrl(url)) {
        this._addMessage(
          `Missing link: ${ent.spellRepitative} in file ${filePath} (evaluates to "${url}") in "spellRepitative"\n` +
          `${this._tagTestUrlLookup.getLogPtSimilarUrls({url})}`
        );
      }
    }
  }
}
```

## 6. Image Validation (test/test-images.js)

**Проверка токенов и изображений:**

```javascript
class _TestTokenImagesBase {
  _PATH_BASE;      // "img/creature"
  _PROP;           // "monster"
  _NAME;           // "Creatures"
  _EXT = "webp";

  _expected = new Set();
  _existing = new Set();
  _expectedFromHashToken = {};

  _processFileInfos ({fileInfos}) {
    const sourcesImplicit = new Set();

    fileInfos.forEach(json => {
      json[this._PROP].forEach(ent => {
        ent.__prop = this._PROP;

        // Неявный токен (based on name)
        const implicitTokenPath = `${this._PATH_BASE}/${ent.source}/${Parser.nameToTokenName(ent.name)}.${this._EXT}`;

        if (ent.hasToken) this._expectedFromHashToken[implicitTokenPath] = true;

        if (ent.token) {
          // Явный токен
          const explicitTokenUrl = Renderer[this._PROP].getTokenUrl(ent);
          const explicitTokenPath = `${this._PATH_BASE}/${explicitTokenUrl.split("/").slice(3).join("/")}`;
          this._expected.add(explicitTokenPath);
        } else {
          // Неявный токен
          this._expected.add(implicitTokenPath);
          sourcesImplicit.add(ent.source);
        }

        // Токены из variants
        if (ent.variant) {
          ent.variant
            .filter(it => it.token)
            .forEach(entry => this._expected.add(`${this._PATH_BASE}/${entry.token.source}/${Parser.nameToTokenName(entry.token.name)}.${this._EXT}`));
        }

        // Токены из versions
        const versions = DataUtil.proxy.getVersions(ent.__prop, ent, {isExternalApplicationIdentityOnly: true});
        versions.forEach(entVer => {
          if (!Renderer[this._PROP].hasToken(entVer)) return;
          this._expected.add(`${this._PATH_BASE}/${entVer.source}/${Parser.nameToTokenName(entVer.name)}.${this._EXT}`);
        });

        // Alt art
        if (ent.altArt) {
          ent.altArt.forEach(alt => this._expected.add(`${this._PATH_BASE}/${alt.source}/${Parser.nameToTokenName(alt.name)}.${this._EXT}`));
        }
      });
    });
  }

  _readImageDirs () {
    fs.readdirSync(this._PATH_BASE).forEach(dir => {
      fs.readdirSync(`${this._PATH_BASE}/${dir}`).forEach(file => {
        this._existing.add(`${this._PATH_BASE}/${dir}/${file}`);
      });
    });
  }

  _getIsError () {
    let isError = false;
    const results = [];

    // Отсутствующие токены
    this._expected.forEach((img) => {
      if (!this._existing.has(img)) results.push(`[ MISSING] ${img}`);
    });

    // Лишние токены
    this._existing.forEach((img) => {
      delete this._expectedFromHashToken[img];

      if (!this._expected.has(img)) {
        if (this._IS_CLEAN_EXTRAS) {
          fs.unlinkSync(img);
          results.push(`[ !DELETE] ${img}`);
          return;
        }

        results.push(`[   EXTRA] ${img}`);
        isError = true;
      }
    });

    return isError;
  }
}
```

## 7. Misc Validation (test/test-misc.js)

**Проверка category IDs:**

```javascript
function testCatIds () {
  const errors = [];
  Object.keys(Parser.CAT_ID_TO_FULL).forEach(catId => {
    if (Parser.CAT_ID_TO_PROP[catId] === undefined) {
      errors.push(`Missing property for ID: ${catId} (${Parser.CAT_ID_TO_FULL[catId]})`);
    }
    if (UrlUtil.CAT_TO_PAGE[catId] === undefined) {
      errors.push(`Missing page for ID: ${catId} (${Parser.CAT_ID_TO_FULL[catId]})`);
    }
  });
  return errors;
}
```

## 8. Multisource Validation (test/test-multisource.js)

**Проверка multisource файлов:**

```javascript
const _MULTISOURCE_DIRS = [
  "bestiary",
  "spells",
];

function main () {
  const sourceIncorrect = [];

  _MULTISOURCE_DIRS.forEach(dir => {
    const indexPath = `./data/${dir}/index.json`;
    const indexPathFluff = `./data/${dir}/fluff-index.json`;

    const indexes = [
      ut.readJson(indexPath),
      ut.readJson(indexPathFluff),
    ];

    indexes.forEach(index => {
      Object.entries(index).forEach(([source, filename]) => {
        const json = ut.readJson(`./data/${dir}/${filename}`);

        Object.values(json).forEach(arr => {
          if (!arr || !(arr instanceof Array)) return;

          arr.forEach(ent => {
            // Проверка что source сущности совпадает с source в index
            if (!ent.source || source === ent.source) return;
            sourceIncorrect.push(`${filename} :: ${ent.name} :: ${ent.source} -> ${source}`);
          });
        });
      });
    });
  });

  if (!sourceIncorrect.length) {
    console.log(`##### Multisource source test passed! #####`);
    return true;
  }

  console.error(`##### Multisource source test failed! #####\n${sourceIncorrect.join("\n")}`);
}
```

## Поток выполнения

### 1. JSON Schema Validation

```
test-json.js
  ↓
JsonTester.pInit() ──→ Загрузка schemas из 5etools-utils
  ↓
Uf.listJsonFiles("data") ──→ Сбор всех JSON файлов
  ↓
fnGetSchemaId(filePath) ──→ Определение schema по пути
  ↓
pGetErrorsOnDirsWorkers() ──→ Worker-based validation
  ↓
AJV.validate(data, schema) ──→ Schema validation
  ↓
Результат: errors, errorsFull
```

### 2. Tag Validation

```
test-tags.js
  ↓
TagTestUrlLookup.pInit()
  ↓
Omnidexer.pGetIndex() ──→ Primary index
  ↓
Omnidexer.pGetIndexAdditionalItem() ──→ Additional items
  ↓
DataLoader.pCacheAndGetAllSite() ──→ Item properties, feats
  ↓
_build class/subclass index
  ↓
LinkCheck._checkString() ──→ Поиск {@tag}
  ↓
Renderer.utils.getTagMeta() ──→ Парсинг тега
  ↓
TagTestUrlLookup.hasUrl(url) ──→ Проверка URL
  ↓
_getLogPtSimilarUrls() ──→ Similar URLs (опционально)
```

### 3. Image Validation

```
test-images.js
  ↓
_Read JSON files (bestiary.json, etc.)
  ↓
_processFileInfos() ──→ Сбор ожидаемых токенов
  ↓
  - ent.token → explicit token
  - implicit → Parser.nameToTokenName(ent.name)
  - ent.variant → variant tokens
  - ent.version → version tokens
  - ent.altArt → alt art tokens
  ↓
_readImageDirs() ──→ Сбор существующих файлов
  ↓
_compare:
  - _expected vs _existing → MISSING
  - _existing vs _expected → EXTRA
```

## Ключевые файлы

### Тесты
- `test/test-all.js` - Оркестратор всех тестов
- `test/test-json.js` - JSON schema validation
- `test/test-tags.js` - Tag validation
- `test/test-images.js` - Image validation
- `test/test-image-paths.js` - Image path validation
- `test/test-misc.js` - Misc checks
- `test/test-multisource.js` - Multisource validation
- `test/test-language-fonts.js` - Language fonts
- `test/test-map-names.js` - Map names
- `test/test-adventure-book-contents.js` - Adventure/book contents
- `test/test-foundry.js` - Foundry validation

### Entity handlers
- `test/test-tags/entity-file/test-tags-entity-file-base.js` - Base class
- `test/test-tags/entity-file/test-tags-entity-file-spell.js` - Spells
- `test/test-tags/entity-file/test-tags-entity-file-bestiary.js` - Monsters
- `test/test-tags/entity-file/test-tags-entity-file-class.js` - Classes
- `test/test-tags/entity-file/test-tags-entity-file-items.js` - Items
- И 15+ других handlers

### Infrastructure
- `test/test-tags/test-tags-entity-registry.js` - TagTestUrlLookup
- `package.json` - AJV 8.12.0, ajv-formats 2.1.1
- `5etools-utils` - JsonTester, DataTesterBase (v0.14.33)

## Статистика

- **~2600 строк** тестового кода
- **21 entity handler** для разных типов данных
- **70+ тегов** с defaultSource для валидации
- **3 уровня** проверки: schema, tags, images
- **Worker-based** параллельная обработка
- **AJV 8.12.0** для schema validation
- **Omnidexer** для URL индексации
- **2 URL sets**: regular + versions

## Типичные ошибки

### 1. Missing link

```
{@spell nonexistent|PHB}
  ↓
TagTestUrlLookup.hasUrl("spells.html#nonexistent%phb") → false
  ↓
"Missing link: {@spell nonexistent|PHB} in file data/spells/spells-phb.json"
```

### 2. Schema validation error

```
{
  "name": "Fireball",
  "level": 3,
  "source": "PHB"
  // Missing "entries" property
}
  ↓
AJV.validate(data, spellSchema)
  ↓
"Schema test failed: data/spells/spells-phb.json#/spell/0 must have required property 'entries'"
```

### 3. Missing token

```
{
  "name": "Goblin",
  "source": "MM",
  "hasToken": true
}
  ↓
_expected.add("img/creature/MM/goblin.webp")
_existing.has("img/creature/MM/goblin.webp") → false
  ↓
"[ MISSING] img/creature/MM/goblin.webp"
```

### 4. Multisource mismatch

```
// index.json: {"PHB": "spells-phb.json"}
// spells-phb.json: [
//   {"name": "Fireball", "source": "XPHB", ...}
// ]
  ↓
ent.source ("XPHB") !== source ("PHB")
  ↓
"spells-phb.json :: Fireball :: XPHB -> PHB"
```

### 5. Malformed subclass link

```
{@class Fighter|PHB|Eldritch Knight|PHB|99-0}
  ↓
featureIndex = ["0-0", "1-0", ..., "20-2"]
"99-0" is outside expected range
  ↓
"Malformed subclass link: {@class Fighter|PHB|...} -- feature index '99-0' was outside expected range"
```

## Best Practices

### 1. Добавление новой entity

```javascript
// 1. Добавить handler
export class EntityFileHandlerMyEntity extends EntityFileHandlerBase {
  _props = ["myEntity"];

  async _pDoTestEntity ({filePath, fileState, ent, prop, propPrefixed}) {
    // Проверить специфичные поля
    if (ent.seeAlso) {
      this._doCheckSeeAlso({entity: ent, prop: "seeAlso", tag: "myEntity", file: filePath});
    }

    if (ent.additionalSpells) {
      this._testAdditionalSpells(filePath, ent);
    }
  }
}

// 2. Зарегистрировать в test-tags.js
import {EntityFileHandlerMyEntity} from "./test-tags/entity-file/test-tags-entity-file-myentity.js";

const entityFileHandlers = [
  // ...
  new EntityFileHandlerMyEntity({tagTestUrlLookup}),
];
```

### 2. Добавление нового тега

```javascript
// 1. Добавить в Renderer.tag (render.js)
static TagMyEntity = class extends this._TagBaseAt {
  tagName = "myentity";
  defaultSource = Parser.SRC_PHB;
  page = UrlUtil.PG_MYENTITY;
};

// 2. Добавить в UrlUtil.URL_TO_HASH_BUILDER
"myentity": (ent) => {
  return UrlUtil.encodeForHash(ent.name) + HASH_LIST_SEP + UrlUtil.encodeForHash(ent.source);
};

// 3. Добавить в LinkCheck._RE_TAG_BLOCKLIST (если нужно)
```

### 3. Schema изменения

```javascript
// Schema должны быть в 5etools-utils
// Изменения требуют публикации новой версии 5etools-utils
```

## CI/CD Integration

```yaml
# .github/workflows/test.yml
- name: Run tests
  run: npm test

# FAIL_SLOW=1 для полного отчета
- name: Run tests (detailed)
  run: FAIL_SLOW=1 npm test
```
