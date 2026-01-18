#!/usr/bin/env python3
"""
Проверка чистоты источников в data_rework/.

Проверяет, что в каждом каталоге data_rework/{SOURCE}/
находятся только данные с соответствующим source.

Usage:
    python scripts/validation/check_source_purity.py
    python scripts/validation/check_source_purity.py --output json
    python scripts/validation/check_source_purity.py --output-file report.json
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List


def check_entities_recursive(entities: List[Dict], expected_source: str, json_file: Path, path: str = "") -> List[Dict[str, Any]]:
	"""
	Рекурсивно проверить все сущности на правильный source.

	Args:
		entities: Список сущностей
		expected_source: Ожидаемый source
		json_file: Путь к JSON файлу
		path: Текущий путь в JSON структуре

	Returns:
		Список ошибок
	"""
	errors = []

	if not isinstance(entities, list):
		return errors

	for entity in entities:
		if not isinstance(entity, dict):
			continue

		source = entity.get("source")
		name = entity.get("name", "Unknown")

		# Проверить source
		if source is not None and source != expected_source:
			errors.append({
				"file": str(json_file.relative_to(Path.cwd())),
				"path": path,
				"entity_name": name,
				"expected_source": expected_source,
				"actual_source": source
			})

		# Рекурсивно проверить вложенные массивы
		for key, value in entity.items():
			if isinstance(value, list) and key not in ["entries", "additionalEntites", "additionalEntities"]:
				new_path = f"{path}.{key}" if path else key
				errors.extend(check_entities_recursive(value, expected_source, json_file, new_path))

	return errors


def check_file_source_purity(json_file: Path, expected_source: str) -> List[Dict[str, Any]]:
	"""
	Проверить, что все сущности в JSON файле имеют корректный source.

	Args:
		json_file: Путь к JSON файлу
		expected_source: Ожидаемый source (например, "PHB")

	Returns:
		Список ошибок (пустой, если всё ОК)
	"""
	try:
		with open(json_file, 'r', encoding='utf-8') as f:
			data = json.load(f)
	except Exception as e:
		return [{
			"file": str(json_file.relative_to(Path.cwd())),
			"error": f"Failed to load JSON: {e}"
		}]

	errors = []

	# Проверить все массивы верхнего уровня
	for key, value in data.items():
		if key == "_meta":
			continue

		if isinstance(value, list):
			errors.extend(check_entities_recursive(value, expected_source, json_file, key))

	return errors


def check_source_purity(data_rework_dir: Path) -> Dict[str, Any]:
	"""
	Проверить чистоту всех источников в data_rework/.

	Args:
		data_rework_dir: Путь к data_rework/ директории

	Returns:
		Отчёт в формате JSON
	"""
	if not data_rework_dir.exists():
		return {
			"script": "check_source_purity.py",
			"status": "ERROR",
			"message": f"Directory not found: {data_rework_dir}"
		}

	all_errors = []
	checked_files = 0

	# Проверить каждый источник
	for source_dir in sorted(data_rework_dir.iterdir()):
		if not source_dir.is_dir():
			continue

		source_id = source_dir.name
		data_dir = source_dir / "data"

		if not data_dir.exists():
			continue

		# Проверить все JSON файлы
		for json_file in sorted(data_dir.glob("*.json")):
			errors = check_file_source_purity(json_file, source_id)

			if errors:
				all_errors.extend(errors)

			checked_files += 1

	report = {
		"script": "check_source_purity.py",
		"status": "OK" if not all_errors else "ERROR",
		"summary": {
			"checked_files": checked_files,
			"total_errors": len(all_errors)
		},
		"errors": all_errors
	}

	return report


def main():
	parser = argparse.ArgumentParser(
		description="Проверить чистоту источников в data_rework/"
	)
	parser.add_argument(
		"--data-dir",
		type=Path,
		default=Path("data_rework"),
		help="Путь к data_rework/ директории"
	)
	parser.add_argument(
		"--output",
		choices=["text", "json"],
		default="text",
		help="Формат вывода"
	)
	parser.add_argument(
		"--output-file",
		type=Path,
		help="Сохранить отчёт в файл"
	)

	args = parser.parse_args()

	# Запустить проверку
	print(f"Проверка: {args.data_dir}")
	print("=" * 60)

	report = check_source_purity(args.data_dir)

	# Вывод
	if args.output == "json":
		print(json.dumps(report, indent=2, ensure_ascii=False))
	else:
		# Текстовый формат
		if report["status"] == "ERROR":
			if "message" in report:
				print(f"❌ ERROR: {report['message']}")
			else:
				print(f"❌ Найдено {report['summary']['total_errors']} ошибок:")
				print()

				# Группировать ошибки по файлам
				errors_by_file = {}
				for error in report["errors"]:
					file = error["file"]
					if file not in errors_by_file:
						errors_by_file[file] = []
					errors_by_file[file].append(error)

				# Показать первые 10 файлов с ошибками
				for i, (file, errors) in enumerate(list(errors_by_file.items())[:10]):
					print(f"  📄 {file}: {len(errors)} ошибок")
					for error in errors[:3]:  # Показать первые 3 ошибки в файле
						if "error" in error:
							print(f"    ⚠️  {error['error']}")
						else:
							print(f"    ❌ {error['entity_name']}: {error['expected_source']} → {error['actual_source']}")
					if len(errors) > 3:
						print(f"    ... и ещё {len(errors) - 3}")

				total_files = len(errors_by_file)
				if total_files > 10:
					print(f"\n  ... и ещё {total_files - 10} файлов с ошибками")

				print(f"\nПроверено файлов: {report['summary']['checked_files']}")
		else:
			print(f"✅ Проверка прошла успешно!")
			print(f"Проверено файлов: {report['summary']['checked_files']}")

	# Сохранить в файл
	if args.output_file:
		args.output_file.parent.mkdir(parents=True, exist_ok=True)
		with open(args.output_file, 'w', encoding='utf-8') as f:
			json.dump(report, f, indent=2, ensure_ascii=False)
		print(f"\nОтчёт сохранён: {args.output_file}")

	# Exit code
	sys.exit(0 if report["status"] == "OK" else 1)


if __name__ == "__main__":
	main()
