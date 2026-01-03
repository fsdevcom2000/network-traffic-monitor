# Network Traffic Monitor (CLI)

Minimalistic CLI network traffic monitor written in Python.  
Displays incoming/outgoing speeds, total transferred data, supports EMA smoothing, and multiple display modes.

## Features

- Monitor network traffic via `psutil`
- Tracks:
    - Incoming (IN) and outgoing (OUT) speeds
    - Total data transferred (TOTAL)
- **EMA smoothing** (Exponential Moving Average) for trend visualization
- Multiple display modes (`--view`):
    - `raw` — raw instantaneous values
    - `ema` — smoothed values
    - `both` — show raw and EMA together
- Timing controls:
    - `--interval` — polling interval
    - `--once` — run a single measurement and exit
    - `--count N` — run N measurements and exit
-  Select network interface
- ANSI-rendered bars (adaptive scaling)
- Clean architecture:
    - Data collection
    - Aggregation / EMA
    - Rendering

## Usage

### Basic Run

```

./ntm.py

```

Monitors the default interface, 1-second interval, EMA enabled.

---
### Select Interface

```

./ntm.py --iface eth0

```

List available interfaces (planned):

```

./ntm.py --list-ifaces

```

---
### Polling Interval

```

./ntm.py --interval 0.5

```
Minimum interval enforced for stability.

---

### EMA Smoothing

```

./ntm.py --ema-alpha 0.2

```

- `alpha` ∈ (0, 1)
- Lower → stronger smoothing (slower to react)
- Higher → more responsive

Default: `0.3`

---
### Display Mode (`--view`)

```

./ntm.py --view raw 
./ntm.py --view ema 
./ntm.py --view both

```

- `raw` — instantaneous values only
- `ema` — smoothed values only
- `both` — compare raw and EMA side by side
    

Useful for debugging and understanding network behavior.

---

### Single Measurement

```

./ntm.py --once

```

Useful for scripting, cron jobs, or logging.

---

### Limit Number of Measurements

```

./ntm.py --count 10

```
Runs 10 iterations and exits.

---

### Example Output (ANSI)

```

IFACE: eth0   INTERVAL: 1.0s   VIEW: both

IN   RAW:  12.4 MB/s  ████████████ 
IN   EMA:  10.1 MB/s  ██████████  

OUT  RAW:   1.8 MB/s  ██ 
OUT  EMA:   2.1 MB/s  ██ 
 
TOTAL IN:   4.2 GB 
TOTAL OUT:  620 MB

```

## Architecture

```

ntm.py
├── TrafficCollector   # psutil counters
├── TrafficStats       # delta, rate, total
├── EMAFilter          # smoothing
├── Renderer
│   ├── AnsiRenderer
│   ├── PlainRenderer
│   └── JsonRenderer   # future-proofing
└── CLI / argparse

```    

---
## Limitations

- Not designed for high-precision billing
- psutil depends on OS and drivers
- EMA is a trend filter, not true instantaneous measurement

---

# Network Traffic Monitor (CLI)

Минималистичный CLI-монитор сетевого трафика на Python.
Показывает входящую и исходящую скорость, общий объём данных, поддерживает EMA-сглаживание и несколько режимов отображения.

## Возможности

- Мониторинг сетевого трафика через `psutil`
-  Подсчёт:
    - входящей (IN) и исходящей (OUT) скорости
    - общего трафика (TOTAL)
-  **EMA-сглаживание** скорости (экспоненциальное скользящее среднее)
-  Переключение вида:
    - `raw` — сырые значения
    - `ema` — сглаженные значения
    - `both` — одновременно raw и ema
-  Управление временем:
    - `--interval` — интервал опроса
    - `--once` — один замер и выход
    - `--count N` — выполнить N замеров и выйти
        
-  Выбор сетевого интерфейса
-  ANSI-рендер с барами (адаптивный масштаб)
-  Чёткое разделение логики:
    - сбор данных
    - агрегация / EMA
    - рендер

## Использование

### Базовый запуск

```

./ntm.py

```
Мониторинг дефолтного интерфейса, интервал 1 секунда, EMA включена.

### Выбор интерфейса

```

./ntm.py --iface eth0

```

### Посмотреть доступные интерфейсы:

```

./ntm.py --list-ifaces

```

### Интервал опроса

```

./ntm.py --interval 0.5

```

Минимальный интервал ограничен (защита от нулевых и слишком малых значений).

### EMA-сглаживание

```

./ntm.py --ema-alpha 0.2

```

- `alpha` ∈ (0, 1)
    
- меньше → сильнее сглаживание
- больше → быстрее реакция

По умолчанию: `0.3`

### Режим отображения (`--view`)

```

./ntm.py --view raw 
./ntm.py --view ema 
./ntm.py --view both

```

- `raw` — мгновенная скорость
- `ema` — сглаженная скорость
- `both` — сравнение в реальном времени

Полезно для отладки и понимания поведения сети.

### Одноразовый замер

```

./ntm.py --once

```

### Ограничение количества замеров

```

./ntm.py --count 10

```

Скрипт выполнит 10 итераций и завершится.

## Пример вывода (ANSI)

```

IFACE: eth0   INTERVAL: 1.0s   VIEW: both

IN   RAW:  12.4 MB/s  ████████████ 
IN   EMA:  10.1 MB/s  ██████████  

OUT  RAW:   1.8 MB/s  ██ 
OUT  EMA:   2.1 MB/s  ██ 
 
TOTAL IN:   4.2 GB 
TOTAL OUT:  620 MB

```

Бары масштабируются **адаптивно** по максимальной скорости за сессию.

## Архитектура

```

ntm.py
├── TrafficCollector   # чтение счётчиков psutil
├── TrafficStats       # расчёт delta, rate, total
├── EMAFilter          # сглаживание
├── Renderer
│   ├── AnsiRenderer
│   ├── PlainRenderer
│   └── JsonRenderer   # задел под будущее
└── CLI / argparse

```

## Ограничения

- Не предназначен для high-precision биллинга
- psutil зависит от ОС и драйверов
- EMA — фильтр, а не истинная скорость
