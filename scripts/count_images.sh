#!/bin/bash
# count_images.sh - Сравнение количества картинок в img и data_rework
# Version: 1.0.0
# Date: 2025-01-18

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Путь к проекту (можно переопределить через аргумент)
PROJECT_ROOT="${1:-/home/benjburn/Projects/5etools-src}"

# Проверка существования директорий
if [[ ! -d "$PROJECT_ROOT" ]]; then
    echo -e "${RED}Ошибка:${NC} Директория проекта не найдена: $PROJECT_ROOT"
    exit 1
fi

IMG_DIR="$PROJECT_ROOT/img"
DATA_REWORK_DIR="$PROJECT_ROOT/data_rework"

if [[ ! -d "$IMG_DIR" ]]; then
    echo -e "${RED}Ошибка:${NC} Директория /img не найдена: $IMG_DIR"
    exit 1
fi

if [[ ! -d "$DATA_REWORK_DIR" ]]; then
    echo -e "${RED}Ошибка:${NC} Директория /data_rework не найдена: $DATA_REWORK_DIR"
    exit 1
fi

# Функция подсчёта изображений
count_images() {
    local dir="$1"
    local count

    count=$(find "$dir" -type f \
        \( -name "*.webp" \
        -o -name "*.png" \
        -o -name "*.jpg" \
        -o -name "*.jpeg" \
        -o -name "*.gif" \
        -o -name "*.svg" \
        \) | wc -l)

    echo "$count"
}

# Подсчёт изображений
echo -e "${BLUE}Подсчёт изображений...${NC}"
IMG_COUNT=$(count_images "$IMG_DIR")
DATA_REWORK_COUNT=$(count_images "$DATA_REWORK_DIR")

# Расчёты
DIFF=$((DATA_REWORK_COUNT - IMG_COUNT))

if [[ $IMG_COUNT -gt 0 ]]; then
    PERCENT=$(awk "BEGIN {printf \"%.1f\", ($DATA_REWORK_COUNT / $IMG_COUNT) * 100}")
else
    PERCENT="0.0"
fi

# Определение статуса
# Используем абсолютное значение разницы для вычисления процента
ABS_DIFF=${DIFF#-}  # Удаляем минус если есть
PERCENT_DIFF=$(awk "BEGIN {printf \"%.1f\", ($ABS_DIFF / $IMG_COUNT) * 100}")

if [[ $DIFF -eq 0 ]]; then
    STATUS="${GREEN}✓ Идеально${NC}"
elif [[ $(echo "$PERCENT_DIFF < 5" | awk '{print ($1 < 5)}') -eq 1 ]]; then
    if [[ $DIFF -gt 0 ]]; then
        STATUS="${YELLOW}⚠ Небольшой избыток (+${DIFF})${NC}"
    else
        STATUS="${YELLOW}⚠ Небольшой недостаток (${DIFF})${NC}"
    fi
else
    if [[ $DIFF -gt 0 ]]; then
        STATUS="${RED}✗ Значительный избыток (+${DIFF})${NC}"
    else
        STATUS="${RED}✗ Значительный недостаток (${DIFF})${NC}"
    fi
fi

# Вывод результатов
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Сравнение количества картинок${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${BLUE}/img:${NC}         ${IMG_COUNT}"
echo -e "  ${BLUE}/data_rework:${NC} ${DATA_REWORK_COUNT}"
echo ""
echo -e "  ${BLUE}Разница:${NC}      $ABS_DIFF (${PERCENT_DIFF}%)"
echo -e "  ${BLUE}Покрытие:${NC}     ${PERCENT}%"
echo ""
echo -e "  ${BLUE}Статус:${NC}       $STATUS"
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo ""

# Код выхода: 0 если всё ок, 1 если есть проблемы
if [[ $DIFF -ne 0 ]]; then
    exit 1
fi

exit 0
