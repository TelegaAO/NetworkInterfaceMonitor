# Монитор сетевых интерфейсов

import time
import sys
import os
from datetime import datetime
# Проверяем наличие psutil
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("ВНИМАНИЕ: Библиотека psutil не установлена!")
def format_bytes(b):
    """Форматирование размера в читаемый вид"""
    if b < 1024:
        return f"{b} B"
    elif b < 1024*1024:
        return f"{b/1024:.1f} KB"
    elif b < 1024*1024*1024:
        return f"{b/(1024*1024):.1f} MB"
    else:
        return f"{b/(1024*1024*1024):.1f} GB"
class NetworkMonitor:
    def __init__(self):
        self.prev_stats = {}
        self.update_interval = 15  # Обновление каждые 15 секунд
        self.check_dependencies()
    def check_dependencies(self):
        """Проверить необходимые библиотеки"""
        if not PSUTIL_AVAILABLE:
            print("\n" + "!"*60)
            print("ОШИБКА: Библиотека psutil не установлена!")
            print("Установите её командой:")
            print("pip install psutil")
            print("!"*60)
            input("\nНажмите Enter для выхода...")
            sys.exit(1)
    def get_stats(self):
        """Получить статистику всех сетевых интерфейсов"""
        stats = {}
        try:
            interfaces = psutil.net_io_counters(pernic=True)
            addrs = psutil.net_if_addrs()
            for name, data in interfaces.items():
                is_active = name in addrs and len(addrs[name]) > 0
                stats[name] = {
                    'up': is_active,
                    'sent': data.bytes_sent,
                    'recv': data.bytes_recv,
                    'errin': data.errin,
                    'errout': data.errout,
                    'time': datetime.now()
                }
        except Exception as e:
            print(f"Ошибка получения статистики: {e}")
            return {}
        return stats
    def calculate_speeds(self, current_stats):
        """Рассчитать скорость передачи данных"""
        speeds = {}
        for name, current in current_stats.items():
            if name in self.prev_stats:
                previous = self.prev_stats[name]
                time_diff = (current['time'] - previous['time']).total_seconds()
                if time_diff > 0:
                    speeds[name] = {
                        'sent': (current['sent'] - previous['sent']) / time_diff,
                        'recv': (current['recv'] - previous['recv']) / time_diff,
                        'errin': current['errin'] - previous['errin'],
                        'errout': current['errout'] - previous['errout']
                    }
        return speeds
    def check_problems(self, stats, speeds):
        """Проверить наличие проблем с интерфейсами"""
        problems = []
        for name, data in stats.items():
            if name == 'lo' or name.startswith('Loopback'):
                continue
            if not data['up']:
                problems.append(f"Интерфейс {name} отключен")
            if data['errin'] > 0 or data['errout'] > 0:
                problems.append(f"Ошибки на {name}: вход={data['errin']}, выход={data['errout']}")
            if name in speeds:
                speed_data = speeds[name]
                if speed_data['sent'] > 10*1024*1024:
                    problems.append(f"Высокая исходящая скорость на {name}")
                if speed_data['recv'] > 10*1024*1024:
                    problems.append(f"Высокая входящая скорость на {name}")
        return problems
    def display_info(self, stats, speeds, problems, next_update):
        """Отобразить информацию о сетевых интерфейсах"""
        os.system('cls' if os.name == 'nt' else 'clear')
        print("=" * 60)
        print(f"МОНИТОР СЕТЕВЫХ ИНТЕРФЕЙСОВ - {datetime.now().strftime('%H:%M:%S')}")
        print(f"СТАТУС: АКТИВЕН - обновление через {next_update} сек")
        print("=" * 60)
        # Показываем только не loopback интерфейсы
        for name, data in stats.items():
            if name == 'lo' or name.startswith('Loopback'):
                continue
            status = "ВКЛ" if data['up'] else "ВЫКЛ"
            status_symbol = "[✓]" if data['up'] else "[✗]"
            print(f"\n{status_symbol} {name} ({status})")
            print(f"  Отправлено: {format_bytes(data['sent'])}")
            print(f"  Получено:   {format_bytes(data['recv'])}")
            if name in speeds:
                speed = speeds[name]
                print(f"  Скорость: ↑{format_bytes(speed['sent'])}/s ↓{format_bytes(speed['recv'])}/s")
        # Показываем проблемы если есть
        if problems:
            print(f"\n{'!' * 60}")
            print("ОБНАРУЖЕНЫ ПРОБЛЕМЫ:")
            for problem in problems:
                print(f"  ⚠ {problem}")
            print(f"{'!' * 60}")
        print(f"\nУправление: [Q] Выход  [R] Сбросить  [S] Сохранить")
        print("=" * 60)
    def save_stats(self):
        """Сохранить статистику в файл"""
        try:
            filename = f"network_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"Статистика сетевых интерфейсов - {datetime.now()}\n")
                f.write("=" * 50 + "\n")
            print(f"\n✓ Статистика сохранена в файл: {filename}")
            time.sleep(1)
        except Exception as e:
            print(f"\n✗ Ошибка сохранения: {e}")
            time.sleep(2)
    def wait_input(self, timeout):
        """Ожидать ввода пользователя с таймаутом"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if sys.platform == 'win32':
                try:
                    import msvcrt
                    if msvcrt.kbhit():
                        return msvcrt.getch().decode().lower()
                except:
                    pass
            else:
                try:
                    import select
                    if select.select([sys.stdin], [], [], 0.1)[0]:
                        return sys.stdin.read(1).lower()
                except:
                    pass
            time.sleep(0.1)
        return None
    def run(self):
        """Запуск основного цикла мониторинга"""
        print("Запуск монитора сетевых интерфейсов...")
        print("Сбор данных...")
        time.sleep(1)
        try:
            while True:
                # Получаем данные
                stats = self.get_stats()
                speeds = self.calculate_speeds(stats)
                problems = self.check_problems(stats, speeds)
                # Сохраняем для следующего сравнения
                self.prev_stats = stats
                # Отображаем информацию
                self.display_info(stats, speeds, problems, self.update_interval)
                # Ждем 15 секунд или ввод
                key = self.wait_input(self.update_interval)
                if key == 'q':
                    print("\nВыход из программы...")
                    break
                elif key == 'r':
                    self.prev_stats = {}
                    print("\n✓ Статистика сброшена")
                    time.sleep(1)
                elif key == 's':
                    self.save_stats()
        except KeyboardInterrupt:
            print("\n\nМониторинг остановлен")
        except Exception as e:
            print(f"\nОшибка: {e}")
            input("Нажмите Enter для выхода...")
def main():
    """Главная функция программы"""
    print("=" * 60)
    print("МОНИТОР СЕТЕВЫХ ИНТЕРФЕЙСОВ (обновление: 15 сек)")
    print("=" * 60)
    print("Отслеживание статистики, трафика и обнаружение неисправностей")
    print("\nУправление:")
    print("  Q - Выход из программы")
    print("  R - Сбросить статистику")
    print("  S - Сохранить данные в файл")
    # Проверяем зависимости
    if not PSUTIL_AVAILABLE:
        print("!" * 60)
        print("Библиотека psutil не установлена!")
        print("Установите командой: pip install psutil")
        print("!" * 60)
        return
    # Создаем и запускаем монитор
    monitor = NetworkMonitor()
    monitor.run()
    print("\n" + "=" * 60)
    print("Программа завершена")
    print("=" * 60)
# Запуск программы
if __name__ == "__main__":
    main()