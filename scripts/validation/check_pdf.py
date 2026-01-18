#!/usr/bin/env python3
"""
Проверка PDF файлов в проекте 5etools.

Проверяет:
- Все PDF файлы в img/pdf/ доступны и читаются
- Ссылки на PDF в JSON данных корректны
- Соответствие между файлами и ссылками

Usage:
    python scripts/validation/check_pdf.py
    cd /path/to/5etools-src && python scripts/validation/check_pdf.py
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple


class PDFValidator:
    """Валидатор PDF файлов и ссылок на них."""

    def __init__(self, project_root: Path):
        """
        Инициализация валидатора.

        Args:
            project_root: Корневая директория проекта
        """
        self.project_root = project_root
        self.pdf_dir = project_root / "img" / "pdf"
        self.data_dir = project_root / "data"

        # Результаты проверки
        self.results = {
            "pdf_files": {
                "total": 0,
                "accessible": 0,
                "inaccessible": [],
                "broken": []
            },
            "json_references": {
                "total": 0,
                "valid": 0,
                "invalid": [],
                "missing_files": []
            },
            "unreferenced_pdfs": [],
            "summary": {
                "errors": 0,
                "warnings": 0
            }
        }

    def find_all_pdfs(self) -> Dict[str, Path]:
        """
        Найти все PDF файлы в img/pdf/.

        Returns:
            Словарь {относительный_путь: абсолютный_путь}
        """
        pdf_files = {}

        if not self.pdf_dir.exists():
            print(f"❌ Директория {self.pdf_dir} не существует", file=sys.stderr)
            return pdf_files

        for pdf_path in self.pdf_dir.rglob("*.pdf"):
            rel_path = pdf_path.relative_to(self.pdf_dir)
            pdf_files[str(rel_path)] = pdf_path

        return pdf_files

    def check_pdf_accessibility(self, pdf_files: Dict[str, Path]) -> None:
        """
        Проверить доступность PDF файлов.

        Args:
            pdf_files: Словарь PDF файлов
        """
        print(f"🔍 Проверка {len(pdf_files)} PDF файлов...")

        for rel_path, abs_path in pdf_files.items():
            self.results["pdf_files"]["total"] += 1

            if not abs_path.exists():
                self.results["pdf_files"]["inaccessible"].append(str(rel_path))
                self.results["summary"]["errors"] += 1
                print(f"  ❌ Файл не существует: {rel_path}")
                continue

            if not abs_path.is_file():
                self.results["pdf_files"]["inaccessible"].append(str(rel_path))
                self.results["summary"]["errors"] += 1
                print(f"  ❌ Не является файлом: {rel_path}")
                continue

            # Проверка чтения файла
            try:
                with open(abs_path, "rb") as f:
                    # Читаем заголовок PDF
                    header = f.read(4)
                    if header != b"%PDF":
                        self.results["pdf_files"]["broken"].append(str(rel_path))
                        self.results["summary"]["errors"] += 1
                        print(f"  ⚠️  Повреждённый PDF: {rel_path}")
                    else:
                        self.results["pdf_files"]["accessible"] += 1
            except Exception as e:
                self.results["pdf_files"]["inaccessible"].append(str(rel_path))
                self.results["summary"]["errors"] += 1
                print(f"  ❌ Ошибка чтения {rel_path}: {e}")

    def find_pdf_references_in_json(self) -> Set[str]:
        """
        Найти все ссылки на PDF в JSON данных.

        Returns:
            Множество относительных путей к PDF файлам
        """
        print("\n🔍 Поиск ссылок на PDF в JSON данных...")

        pdf_pattern = re.compile(r'pdf/([^\s"}]+\.pdf)')
        referenced_pdfs = set()

        # Обходим все JSON файлы в data/
        for json_file in self.data_dir.rglob("*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    content = f.read()

                # Ищем все ссылки на PDF
                matches = pdf_pattern.findall(content)
                for match in matches:
                    # Убираем лишние кавычки и пробелы
                    pdf_path = match.strip('"').strip("'")
                    referenced_pdfs.add(pdf_path)
                    self.results["json_references"]["total"] += 1

            except json.JSONDecodeError:
                # Пропускаем файлы с ошибками JSON
                continue
            except Exception as e:
                print(f"  ⚠️  Ошибка чтения {json_file}: {e}", file=sys.stderr)
                continue

        print(f"  ✓ Найдено {len(referenced_pdfs)} уникальных ссылок")
        return referenced_pdfs

    def validate_pdf_references(
        self,
        pdf_files: Dict[str, Path],
        referenced_pdfs: Set[str]
    ) -> None:
        """
        Проверить корректность ссылок на PDF.

        Args:
            pdf_files: Словарь PDF файлов
            referenced_pdfs: Множество ссылок на PDF
        """
        print("\n🔍 Проверка ссылок на PDF...")

        for pdf_ref in referenced_pdfs:
            # Нормализуем путь
            pdf_ref_normalized = pdf_ref.replace("\\", "/")

            if pdf_ref_normalized in pdf_files:
                self.results["json_references"]["valid"] += 1
            else:
                self.results["json_references"]["invalid"].append(pdf_ref_normalized)
                self.results["json_references"]["missing_files"].append(pdf_ref_normalized)
                self.results["summary"]["errors"] += 1
                print(f"  ❌ Файл не найден: {pdf_ref_normalized}")

        # Проверяем наличие неиспользуемых PDF
        all_pdf_paths = set(pdf_files.keys())
        referenced_paths = {ref.replace("\\", "/") for ref in referenced_pdfs}
        unreferenced = all_pdf_paths - referenced_paths

        if unreferenced:
            self.results["unreferenced_pdfs"] = sorted(list(unreferenced))
            self.results["summary"]["warnings"] += len(unreferenced)
            print(f"\n  ⚠️  Неиспользуемых PDF файлов: {len(unreferenced)}")

    def generate_report(self) -> Dict:
        """
        Сгенерировать отчёт о проверке.

        Returns:
            Словарь с результатами проверки
        """
        # Подсчитываем общее количество уникальных ссылок
        unique_refs = len(set(self.results["json_references"]["missing_files"]))

        report = {
            "status": "success" if self.results["summary"]["errors"] == 0 else "errors",
            "pdf_files": {
                "total": self.results["pdf_files"]["total"],
                "accessible": self.results["pdf_files"]["accessible"],
                "inaccessible": self.results["pdf_files"]["inaccessible"],
                "broken": self.results["pdf_files"]["broken"]
            },
            "json_references": {
                "total_references": self.results["json_references"]["total"],
                "unique_references": self.results["json_references"]["total"] - unique_refs,
                "valid_files": self.results["json_references"]["valid"],
                "missing_files": self.results["json_references"]["missing_files"]
            },
            "unreferenced_pdfs": self.results["unreferenced_pdfs"],
            "summary": {
                "errors": self.results["summary"]["errors"],
                "warnings": self.results["summary"]["warnings"]
            }
        }

        return report

    def print_report(self, report: Dict) -> None:
        """
        Вывести отчёт в stdout.

        Args:
            report: Отчёт о проверке
        """
        print("\n" + "="*60)
        print("📊 ОТЧЁТ О ПРОВЕРКЕ PDF")
        print("="*60)

        # Статус
        status_emoji = "✅" if report["status"] == "success" else "❌"
        print(f"\n{status_emoji} Статус: {report['status'].upper()}")

        # PDF файлы
        print(f"\n📁 PDF файлы:")
        print(f"  Всего: {report['pdf_files']['total']}")
        print(f"  Доступно: {report['pdf_files']['accessible']}")
        print(f"  Недоступно: {len(report['pdf_files']['inaccessible'])}")
        print(f"  Повреждено: {len(report['pdf_files']['broken'])}")

        if report['pdf_files']['inaccessible']:
            print(f"\n  ❌ Недоступные файлы:")
            for f in report['pdf_files']['inaccessible']:
                print(f"    - {f}")

        if report['pdf_files']['broken']:
            print(f"\n  ⚠️  Повреждённые файлы:")
            for f in report['pdf_files']['broken']:
                print(f"    - {f}")

        # Ссылки в JSON
        print(f"\n🔗 Ссылки в JSON данных:")
        print(f"  Всего ссылок: {report['json_references']['total_references']}")
        print(f"  Валидных: {report['json_references']['valid_files']}")
        print(f"  Отсутствует файлов: {len(report['json_references']['missing_files'])}")

        if report['json_references']['missing_files']:
            print(f"\n  ❌ Отсутствующие файлы:")
            for f in report['json_references']['missing_files']:
                print(f"    - {f}")

        # Неиспользуемые PDF
        print(f"\n📋 Неиспользуемые PDF файлы: {len(report['unreferenced_pdfs'])}")
        if report['unreferenced_pdfs']:
            print(f"  ⚠️  Неиспользуемые файлы:")
            for f in report['unreferenced_pdfs'][:10]:  # Показываем первые 10
                print(f"    - {f}")
            if len(report['unreferenced_pdfs']) > 10:
                print(f"    ... и ещё {len(report['unreferenced_pdfs']) - 10}")

        # Итог
        print(f"\n📈 Итог:")
        print(f"  Ошибок: {report['summary']['errors']}")
        print(f"  Предупреждений: {report['summary']['warnings']}")
        print("="*60 + "\n")

    def run(self) -> Dict:
        """
        Запустить проверку.

        Returns:
            Отчёт о проверке
        """
        print("🚀 Начинаю проверку PDF файлов...\n")

        # Находим все PDF файлы
        pdf_files = self.find_all_pdfs()
        print(f"✓ Найдено PDF файлов: {len(pdf_files)}\n")

        # Проверяем доступность
        self.check_pdf_accessibility(pdf_files)

        # Находим ссылки в JSON
        referenced_pdfs = self.find_pdf_references_in_json()

        # Проверяем ссылки
        self.validate_pdf_references(pdf_files, referenced_pdfs)

        # Генерируем отчёт
        report = self.generate_report()

        # Выводим отчёт
        self.print_report(report)

        return report


def main():
    """Главная функция."""
    # Определяем корневую директорию проекта
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent

    # Создаём и запускаем валидатор
    validator = PDFValidator(project_root)
    report = validator.run()

    # Выводим JSON отчёт для машинной обработки
    print(json.dumps(report, indent=2, ensure_ascii=False))

    # Выход с кодом ошибки
    sys.exit(0 if report["status"] == "success" else 1)


if __name__ == "__main__":
    main()
