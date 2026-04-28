# Project_ExplorerV1
PROJECT EXPLORER PRO
ENGLISH VERSION
Overview
Project Explorer Pro is a high-performance desktop application designed for advanced directory scanning, file management, and real-time system process monitoring. Built with Python and Tkinter, it delivers a professional, dark-themed interface with robust safety mechanisms to prevent accidental modification or deletion of critical system files.
Features
Multi-threaded recursive directory scanning for optimal performance
Explorer-style interface with detailed file metadata and sorting
Color-coded file type categorization for rapid visual identification
Three-tier safety classification system: SAFE, CRITICAL, and SYSTEM-REMOVABLE
Real-time process monitoring with CPU, memory, and status tracking
Secure file deletion with mandatory safety confirmations
Batch processing, progress tracking, and live statistics
Professional dark theme with consistent UI styling across platforms
System Requirements
Python 3.7 or higher
Supported Operating Systems: Windows, Linux, macOS
Dependencies: tkinter (included in standard Python distribution), psutil
Installation
Download or clone the project directory.
Install required dependencies:
bash
1
Launch the application:
bash
1
Usage
Start the application and acknowledge the safety disclaimer.
Enter a directory path in the input field or use the Browse button to select a folder.
Click Scan to initiate directory traversal. Results populate the main file tree.
Switch to the Task Manager tab to monitor active system processes.
Select files or processes and use the available controls (Delete, End Task). All destructive operations require explicit user confirmation.
Safety & Security Guidelines
Critical system directories and files are automatically identified and locked from deletion.
Files classified as SYSTEM-REMOVABLE are flagged for optional cleanup but require manual approval.
Active process paths are cross-referenced to prevent deletion of files currently in use.
Double-confirmation dialogs are enforced for all file and directory removal operations.
The application performs zero automatic deletions. All modifications are strictly user-initiated.
License
MIT License. Free for personal, educational, and commercial use. Refer to the included LICENSE file for full terms.
РУССКАЯ ВЕРСИЯ
Обзор
Project Explorer Pro — это высокопроизводительное десктопное приложение, предназначенное для расширенного сканирования директорий, управления файлами и мониторинга системных процессов в реальном времени. Разработано на Python с использованием Tkinter. Предоставляет профессиональный интерфейс в тёмной теме и встроенные механизмы безопасности для предотвращения случайного изменения или удаления критически важных системных файлов.
Функциональные возможности
Многопоточное рекурсивное сканирование директорий для максимальной скорости работы
Интерфейс в стиле системного проводника с детальной метаинформацией и сортировкой
Цветовая категоризация типов файлов для быстрой визуальной идентификации
Трёхуровневая система классификации безопасности: БЕЗОПАСНЫЕ, КРИТИЧЕСКИЕ, СИСТЕМНО-УДАЛЯЕМЫЕ
Мониторинг активных процессов с отображением нагрузки на ЦП, объёма памяти и статуса
Безопасное удаление файлов с обязательными диалогами подтверждения
Пакетная обработка, отслеживание прогресса и статистика в реальном времени
Профессиональная тёмная тема с единообразным отображением на всех платформах
Системные требования
Python версии 3.7 или выше
Поддерживаемые ОС: Windows, Linux, macOS
Зависимости: tkinter (входит в стандартную поставку Python), psutil
Установка
Скачайте или клонируйте каталог проекта.
Установите необходимые зависимости:
bash
1
Запустите приложение:
bash
1
Использование
Запустите приложение и ознакомьтесь с предупреждением о безопасности.
Введите путь к директории в поле ввода или используйте кнопку «Обзор» для выбора папки.
Нажмите «Сканировать» для запуска анализа. Результаты отобразятся в основном дереве файлов.
Перейдите на вкладку «Диспетчер задач» для мониторинга активных системных процессов.
Выделите файлы или процессы и используйте доступные элементы управления (Удалить, Завершить задачу). Все операции удаления требуют явного подтверждения пользователя.
Рекомендации по безопасности
Критические системные директории и файлы автоматически определяются и защищены от удаления.
Файлы, классифицированные как СИСТЕМНО-УДАЛЯЕМЫЕ, помечаются для опциональной очистки, но требуют ручного подтверждения.
Пути активных процессов проверяются для предотвращения удаления файлов, используемых в данный момент.
Для всех операций удаления применяются диалоги двойного подтверждения.
Приложение не выполняет автоматическое удаление. Все изменения инициируются исключительно пользователем.
Лицензия
Лицензия MIT. Свободное использование в личных, образовательных и коммерческих целях. Полные условия см. в прилагаемом файле LICENSE.
