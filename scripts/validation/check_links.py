#!/usr/bin/env python3
"""
Проверка ссылок в JSON данных 5etools.

Этот скрипт выполняет:
- Проверку внутренних ссылок в JSON (теги {@spell}, {@item}, {@creature} и т.д.)
- Проверку cross-source ссылок
- Поиск битых ссылок (которые не разрешаются)
- Генерацию отчёта

Usage:
    python check_links.py [--data-dir PATH] [--output FORMAT]

Examples:
    python check_links.py                    # Проверка с выводом в stdout
    python check_links.py --output json      # Вывод в JSON формате
    python check_links.py --output json --output-file links.json
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple
from collections import defaultdict


class LinkChecker:
    """Проверяет ссылки в JSON данных 5etools."""

    # Entity tag types that can be referenced
    ENTITY_TAGS = {
        "spell", "item", "creature", "feat", "race", "background",
        "deity", "class", "subclass", "condition", "disease", "skill",
        "language", "cult", "boon", "object", "vehicle", "optionalfeature",
        "variantrule", "charoption", "card", "group", "recipe", "reward",
        "sense", "trap", "hazard", "creatureTemplate"
    }

    # Regex pattern to find tags in text
    TAG_PATTERN = re.compile(r'\{@(\w+)\s+([^}]*)\}')

    def __init__(self, data_dir: Path):
        """Инициализация checker'а с путём к директории данных."""
        self.data_dir = Path(data_dir)
        self.entities: Dict[str, Dict[str, List[Dict]]] = defaultdict(lambda: defaultdict(list))
        self.broken_links: List[Dict[str, Any]] = []
        self.cross_source_links: List[Dict[str, Any]] = []
        self.total_links_checked = 0

    def _is_source_based_structure(self) -> bool:
        """Определяет, является ли структура source-based (data_rework) или content-based (data)."""
        # Проверяем наличие source-based индикаторов
        # data_rework/PHB/data/*.json
        has_source_subdirs = False

        for entry in self.data_dir.iterdir():
            if not entry.is_dir():
                continue

            # Пропускаем служебные директории
            if entry.name.startswith('.') or entry.name in ['__pycache__', 'generated']:
                continue

            # Проверяем наличие data/ поддиректории
            data_subdir = entry / "data"
            if data_subdir.exists() and data_subdir.is_dir():
                has_source_subdirs = True
                break

        return has_source_subdirs

    def load_all_data(self) -> None:
        """Загружает все JSON файлы из директории data/ или data_rework/."""
        print("Загрузка JSON данных...", file=sys.stderr)

        # Определяем структуру: source-based (data_rework) или content-based (data)
        is_source_based = self._is_source_based_structure()

        json_files = []

        if is_source_based:
            # Source-based структура: data_rework/PHB/data/*.json
            print("Обнаружена source-based структура (data_rework/)", file=sys.stderr)
            for source_dir in self.data_dir.iterdir():
                if not source_dir.is_dir():
                    continue

                data_subdir = source_dir / "data"
                if not data_subdir.exists():
                    continue

                # Основные JSON файлы
                json_files.extend(data_subdir.glob("*.json"))

                # Поддиректории (bestiary/, class/, adventure/, book/)
                json_files.extend(data_subdir.glob("bestiary/*.json"))
                json_files.extend(data_subdir.glob("class/*.json"))
                json_files.extend(data_subdir.glob("adventure/*.json"))
                json_files.extend(data_subdir.glob("book/*.json"))
        else:
            # Content-based структура: data/*.json, data/*/*.json
            print("Обнаружена content-based структура (data/)", file=sys.stderr)
            json_files = list(self.data_dir.glob("*.json"))
            json_files.extend(self.data_dir.glob("*/*.json"))

            # Исключаем generated директорию
            json_files = [f for f in json_files if "generated" not in str(f)]

        print(f"Найдено {len(json_files)} JSON файлов для обработки", file=sys.stderr)

        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Обрабатываем различные структуры данных
                if isinstance(data, dict):
                    for key, value in data.items():
                        if isinstance(value, list):
                            self._process_entities(value, key, json_file)
                elif isinstance(data, list):
                    self._process_entities(data, json_file.stem, json_file)

            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                print(f"Ошибка чтения {json_file}: {e}", file=sys.stderr)

        # Вывод статистики загрузки
        total_entities = sum(len(sources) for sources in self.entities.values())
        print(f"Загружено {total_entities} entities из {len(self.entities)} категорий", file=sys.stderr)

        # Вывод top категорий
        if total_entities > 0:
            print("Top категорий по количеству entities:", file=sys.stderr)
            for cat, sources in sorted(self.entities.items(), key=lambda x: sum(len(v) for v in x[1].values()), reverse=True)[:10]:
                count = sum(len(entities) for entities in sources.values())
                print(f"  {cat}: {count} entities", file=sys.stderr)

    def _process_entities(self, entities: List[Dict], category: str, source_file: Path) -> None:
        """Обрабатывает список entities и индексирует их."""
        for entity in entities:
            if not isinstance(entity, dict):
                continue

            # Получаем name и source
            name = entity.get("name") or entity.get("id") or entity.get("shortName")
            source = entity.get("source")

            if name and source:
                # Индексируем по категории и source (храним как список для дубликатов)
                self.entities[category][source].append({
                    "name": name,
                    "source": source,
                    "data": entity,
                    "file": str(source_file.relative_to(self.data_dir.parent))
                })

    def check_links(self) -> None:
        """Проверяет все ссылки в данных."""
        print("Проверка ссылок...", file=sys.stderr)

        for category, sources in self.entities.items():
            for source, entities in sources.items():
                for entity in entities:
                    self._check_entity_links(entity["data"], entity, entity["file"])

    def _check_entity_links(self, data: Any, entity_info: Dict, file_path: str) -> None:
        """Рекурсивно проверяет ссылки в entity."""
        if isinstance(data, str):
            self._check_string_links(data, entity_info, file_path)
        elif isinstance(data, dict):
            for value in data.values():
                self._check_entity_links(value, entity_info, file_path)
        elif isinstance(data, list):
            for item in data:
                self._check_entity_links(item, entity_info, file_path)

    def _check_string_links(self, text: str, entity_info: Dict, file_path: str) -> None:
        """Проверяет ссылки в строке."""
        matches = self.TAG_PATTERN.finditer(text)

        for match in matches:
            tag_type = match.group(1)
            tag_content = match.group(2)
            full_tag = match.group(0)

            self.total_links_checked += 1

            # Проверяем только entity теги
            if tag_type not in self.ENTITY_TAGS:
                return

            # Парсим содержимое тега
            parts = tag_content.split("|")
            name = parts[0].strip().lower()
            source = parts[1].strip().lower() if len(parts) > 1 else None
            entity_name = entity_info["name"]
            entity_source = entity_info["source"]

            # Ищем entity
            found = self._find_entity(tag_type, name, source)

            if not found:
                # Битая ссылка
                self.broken_links.append({
                    "tag": full_tag,
                    "tag_type": tag_type,
                    "target_name": name,
                    "target_source": source,
                    "in_entity": f"{entity_name} ({entity_source})",
                    "in_file": file_path,
                    "reason": "Entity not found"
                })
            elif source and found["source"].lower() != source:
                # Cross-source ссылка
                self.cross_source_links.append({
                    "tag": full_tag,
                    "tag_type": tag_type,
                    "target_name": name,
                    "target_requested_source": source,
                    "target_actual_source": found["source"],
                    "in_entity": f"{entity_name} ({entity_source})",
                    "in_file": file_path
                })

    def _find_entity(self, tag_type: str, name: str, source: str = None) -> Dict[str, Any] | None:
        """Ищет entity по типу, имени и source."""
        # Определяем категорию по тегу
        category_map = {
            "spell": "spell",
            "item": "item",
            "creature": "monster",  # creature -> monster
            "feat": "feat",
            "race": "race",
            "background": "background",
            "deity": "deity",
            "class": "class",
            "subclass": "subclass",
            "condition": "condition",
            "disease": "disease",
            "language": "language",
            "card": "card",
        }

        # Получаем категорию
        category = category_map.get(tag_type)

        # Если нет прямого маппинга, пробуем найти
        if not category:
            # Пробуем точное совпадение
            if tag_type in self.entities:
                category = tag_type
            else:
                # Пробуем найти по частичному совпадению
                for cat in self.entities.keys():
                    if tag_type.lower() in cat.lower() or cat.lower() in tag_type.lower():
                        category = cat
                        break

        if not category or category not in self.entities:
            return None

        # Ищем в указанном source или во всех
        if source:
            # Пытаемся найти с точным совпадением source (case-insensitive)
            for src, entities in self.entities[category].items():
                if src.lower() == source:
                    for entity in entities:
                        if entity["name"].lower() == name:
                            return entity
        else:
            # Ищем во всех sources для этой категории
            for source_entities in self.entities[category].values():
                for entity in source_entities:
                    if entity["name"].lower() == name:
                        return entity

        return None

    def generate_report(self) -> Dict[str, Any]:
        """Генерирует отчёт о проверке."""
        # Группируем битые ссылки по типу
        broken_by_type = defaultdict(list)
        for link in self.broken_links:
            broken_by_type[link["tag_type"]].append(link)

        # Группируем cross-source ссылки по типу
        cross_source_by_type = defaultdict(list)
        for link in self.cross_source_links:
            cross_source_by_type[link["tag_type"]].append(link)

        # Считаем уникальные entities с проблемами
        entities_with_broken = set(link["in_entity"] for link in self.broken_links)
        entities_with_cross_source = set(link["in_entity"] for link in self.cross_source_links)

        return {
            "summary": {
                "total_links_checked": self.total_links_checked,
                "broken_links_count": len(self.broken_links),
                "cross_source_links_count": len(self.cross_source_links),
                "entities_with_broken_links": len(entities_with_broken),
                "entities_with_cross_source_links": len(entities_with_cross_source),
            },
            "broken_links_by_type": {
                tag_type: {
                    "count": len(links),
                    "sample": links[:5]  # Первые 5 примеров
                }
                for tag_type, links in broken_by_type.items()
            },
            "cross_source_links_by_type": {
                tag_type: {
                    "count": len(links),
                    "sample": links[:5]  # Первые 5 примеров
                }
                for tag_type, links in cross_source_by_type.items()
            },
            "all_broken_links": self.broken_links[:100],  # Первые 100
            "all_cross_source_links": self.cross_source_links[:100],  # Первые 100
        }


def main():
    """Главная функция."""
    parser = argparse.ArgumentParser(
        description="Проверка ссылок в JSON данных 5etools"
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data"),
        help="Путь к директории с данными (default: data/)"
    )
    parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Формат вывода (default: text)"
    )
    parser.add_argument(
        "--output-file",
        type=Path,
        help="Файл для сохранения отчёта (опционально)"
    )

    args = parser.parse_args()

    # Создаём checker
    checker = LinkChecker(args.data_dir)

    # Загружаем данные
    checker.load_all_data()

    # Проверяем ссылки
    checker.check_links()

    # Генерируем отчёт
    report = checker.generate_report()

    # Выводим результаты
    if args.output == "json":
        output = json.dumps(report, indent=2, ensure_ascii=False)
    else:
        output = format_text_report(report)

    if args.output_file:
        args.output_file.write_text(output, encoding="utf-8")
        print(f"\nОтчёт сохранён в: {args.output_file}", file=sys.stderr)
    else:
        print(output)

    # Возвращаем код выхода
    return 1 if report["summary"]["broken_links_count"] > 0 else 0


def format_text_report(report: Dict[str, Any]) -> str:
    """Форматирует отчёт в текстовом виде."""
    lines = []
    lines.append("=" * 80)
    lines.append("ОТЧЁТ О ПРОВЕРКЕ ССЫЛОК")
    lines.append("=" * 80)
    lines.append("")

    # Summary
    summary = report["summary"]
    lines.append("СТАТИСТИКА")
    lines.append("-" * 80)
    lines.append(f"Всего проверено ссылок: {summary['total_links_checked']}")
    lines.append(f"Битых ссылок: {summary['broken_links_count']}")
    lines.append(f"Cross-source ссылок: {summary['cross_source_links_count']}")
    lines.append(f"Entities с битыми ссылками: {summary['entities_with_broken_links']}")
    lines.append(f"Entities с cross-source ссылками: {summary['entities_with_cross_source_links']}")
    lines.append("")

    # Broken links by type
    if report["broken_links_by_type"]:
        lines.append("БИТЫЕ ССЫЛКИ ПО ТИПАМ")
        lines.append("-" * 80)
        for tag_type, info in sorted(
            report["broken_links_by_type"].items(),
            key=lambda x: x[1]["count"],
            reverse=True
        ):
            lines.append(f"\n{tag_type}: {info['count']} ссылок")
            for link in info["sample"]:
                lines.append(f"  - {link['tag']}")
                lines.append(f"    В: {link['in_entity']}")
                lines.append(f"    Файл: {link['in_file']}")
                lines.append(f"    Причина: {link['reason']}")
        lines.append("")

    # Cross-source links by type
    if report["cross_source_links_by_type"]:
        lines.append("CROSS-SOURCE ССЫЛКИ ПО ТИПАМ")
        lines.append("-" * 80)
        for tag_type, info in sorted(
            report["cross_source_links_by_type"].items(),
            key=lambda x: x[1]["count"],
            reverse=True
        ):
            lines.append(f"\n{tag_type}: {info['count']} ссылок")
            for link in info["sample"]:
                lines.append(f"  - {link['tag']}")
                lines.append(f"    В: {link['in_entity']}")
                lines.append(f"    Запрошенный source: {link['target_requested_source']}")
                lines.append(f"    Actual source: {link['target_actual_source']}")
        lines.append("")

    lines.append("=" * 80)
    return "\n".join(lines)


if __name__ == "__main__":
    sys.exit(main())
