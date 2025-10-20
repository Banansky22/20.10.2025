import os
import logging
import pandas as pd
import io
import numpy as np
from datetime import datetime
import re
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')

if not TELEGRAM_BOT_TOKEN:
    print("❌ ОШИБКА: TELEGRAM_BOT_TOKEN не установлен!")
    exit(1)

print("✅ Бот с полным функционалом запускается...")

# Словарь для соответствия статей баланса
BALANCE_ITEMS = {
    'внеоборотные активы': ['внеоборотные', 'non-current', 'основные средства'],
    'основные средства': ['основные средства', 'fixed assets'],
    'запасы': ['запасы', 'inventories'],
    'дебиторская задолженность': ['дебиторская', 'accounts receivable'],
    'денежные средства': ['денежные средства', 'cash'],
    'оборотные активы': ['оборотные активы', 'current assets'],
    'активы всего': ['активы', 'актив всего', 'total assets'],
    'капитал': ['капитал', 'собственный капитал', 'equity'],
    'уставный капитал': ['уставный капитал', 'authorized capital'],
    'нераспределенная прибыль': ['нераспределенная прибыль', 'retained earnings'],
    'краткосрочные обязательства': ['краткосрочные обязательства', 'short-term liabilities'],
    'кредиторская задолженность': ['кредиторская задолженность', 'accounts payable'],
    'обязательства всего': ['обязательства', 'пассив всего', 'total liabilities'],
    'выручка': ['выручка', 'revenue', 'sales'],
    'чистая прибыль': ['чистая прибыль', 'net profit', 'net income'],
    'валовая прибыль': ['валовая прибыль', 'gross profit']
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton("📊 Полный анализ"), KeyboardButton("🎯 Выборочный анализ")],
        [KeyboardButton("📈 Анализ ликвидности"), KeyboardButton("💎 Анализ рентабельности")],
        [KeyboardButton("🏛️ Финансовая устойчивость"), KeyboardButton("📋 Сравнение с нормативами")],
        [KeyboardButton("🔮 Прогноз тенденций"), KeyboardButton("📄 Экспорт в TXT")],
        [KeyboardButton("📁 Загрузить Excel"), KeyboardButton("ℹ️ Помощь")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "🤖 **ФИНАНСОВЫЙ АНАЛИЗАТОР**\n\n"
        "🚀 Полная версия с анализом Excel файлов!\n\n"
        "📁 Загрузите Excel файл с отчетностью или используйте калькулятор:",
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
🤖 **ФИНАНСОВЫЙ АНАЛИЗАТОР - ПОЛНАЯ ВЕРСИЯ**

📊 **Доступные функции:**
• 📊 Полный анализ - комплексная оценка
• 🎯 Выборочный анализ - нужные показатели  
• 📈 Анализ ликвидности - платежеспособность
• 💎 Анализ рентабельности - эффективность
• 🏛️ Финансовая устойчивость - стабильность
• 📋 Сравнение с нормативами - отраслевые benchmarks
• 🔮 Прогноз тенденций - будущие тренды
• 📄 Экспорт в TXT - текстовый отчет
• 📁 Загрузить Excel - анализ файлов

📝 **Формат Excel файла:**
Столбцы с периодами:
• 31.12.2023, 31.12.2022
• За 2023 год, За 2022 год
• Строки с названиями показателей
"""
    await update.message.reply_text(help_text)

def read_excel_file(file_bytes, file_name):
    """Читает Excel файл"""
    try:
        if file_name.endswith('.xls'):
            return pd.read_excel(io.BytesIO(file_bytes), engine='xlrd')
        else:
            return pd.read_excel(io.BytesIO(file_bytes), engine='openpyxl')
    except Exception as e:
        raise Exception(f"Ошибка чтения файла: {str(e)}")

def detect_periods(df):
    """Определяет периоды в столбцах"""
    periods = []
    
    for col in df.columns:
        col_str = str(col).lower().strip()
        
        # Поиск дат
        date_patterns = [
            r'\d{2}.\d{2}.\d{4}',  # 31.12.2023
            r'\d{4}-\d{2}-\d{2}',   # 2023-12-31
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, col_str)
            if matches:
                try:
                    date_str = matches[0]
                    if '.' in date_str:
                        date_obj = datetime.strptime(date_str, '%d.%m.%Y')
                    else:
                        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                    
                    periods.append({
                        'column': col,
                        'formatted': date_obj.strftime('%d.%m.%Y'),
                        'year': date_obj.year
                    })
                    break
                except:
                    continue
        
        # Поиск текстовых периодов
        if '2024' in col_str:
            periods.append({
                'column': col,
                'formatted': "31.12.2024",
                'year': 2024
            })
        elif '2023' in col_str:
            periods.append({
                'column': col,
                'formatted': "31.12.2023", 
                'year': 2023
            })
        elif '2022' in col_str:
            periods.append({
                'column': col,
                'formatted': "31.12.2022",
                'year': 2022
            })
    
    periods.sort(key=lambda x: x['year'])
    return periods

def find_balance_item(column_name):
    """Находит соответствие статей баланса"""
    column_name = str(column_name).lower().strip()
    
    for item, keywords in BALANCE_ITEMS.items():
        for keyword in keywords:
            if keyword in column_name:
                return item
    return None

def extract_financial_data(df, periods):
    """Извлекает финансовые данные по периодам"""
    financial_data = {}
    
    for period in periods:
        financial_data[period['formatted']] = {}
    
    # Ищем столбец с наименованиями
    indicator_column = None
    for col in df.columns:
        if 'наименование' in str(col).lower() or 'показатель' in str(col).lower():
            indicator_column = col
            break
    
    if not indicator_column:
        return financial_data
    
    # Извлекаем данные
    for row_idx in range(len(df)):
        indicator_name = str(df[indicator_column].iloc[row_idx]).strip()
        
        if not indicator_name or indicator_name in ['Актив', 'Пассив', 'Наименование показателя']:
            continue
        
        item = find_balance_item(indicator_name)
        
        if item:
            for period in periods:
                try:
                    value = pd.to_numeric(df[period['column']].iloc[row_idx], errors='coerce')
                    if not pd.isna(value) and value != 0:
                        financial_data[period['formatted']][item] = value
                except:
                    continue
    
    return financial_data

def calculate_ratios(data):
    """Рассчитывает финансовые коэффициенты"""
    ratios = {}
    
    try:
        assets = data.get('активы всего', 0)
        current_assets = data.get('оборотные активы', 0)
        cash = data.get('денежные средства', 0)
        equity = data.get('капитал', 0)
        current_liabilities = data.get('краткосрочные обязательства', 0)
        revenue = data.get('выручка', 0)
        net_profit = data.get('чистая прибыль', 0)
        
        # Ликвидность
        if current_liabilities > 0:
            ratios['Коэффициент текущей ликвидности'] = current_assets / current_liabilities
            ratios['Коэффициент абсолютной ликвидности'] = cash / current_liabilities
        
        # Рентабельность
        if assets > 0:
            ratios['Рентабельность активов (ROA)'] = (net_profit / assets) * 100
        if equity > 0:
            ratios['Рентабельность капитала (ROE)'] = (net_profit / equity) * 100
        if revenue > 0:
            ratios['Рентабельность продаж (ROS)'] = (net_profit / revenue) * 100
        
        # Устойчивость
        if assets > 0:
            ratios['Коэффициент автономии'] = equity / assets
        
        # Оборачиваемость
        if assets > 0:
            ratios['Оборачиваемость активов'] = revenue / assets
            
    except Exception as e:
        print(f"Ошибка расчета: {e}")
    
    return ratios

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик загрузки Excel файлов"""
    try:
        if not update.message.document:
            await update.message.reply_text("📎 Пожалуйста, пришлите Excel файл")
            return

        file = update.message.document
        file_name = file.file_name.lower()

        if not (file_name.endswith('.xlsx') or file_name.endswith('.xls')):
            await update.message.reply_text("❌ Пожалуйста, пришлите файл в формате Excel (.xlsx или .xls)")
            return

        await update.message.reply_text("⏳ Анализирую структуру файла...")

        # Скачиваем файл
        file_obj = await file.get_file()
        file_bytes = await file_obj.download_as_bytearray()

        # Читаем Excel
        try:
            df = read_excel_file(file_bytes, file_name)
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка чтения файла: {str(e)}")
            return
        
        # Определяем периоды
        periods = detect_periods(df)
        
        if not periods:
            await update.message.reply_text("❌ Не удалось определить периоды в файле")
            return
        
        # Извлекаем данные
        periods_data = extract_financial_data(df, periods)
        
        # Сохраняем в контекст
        context.user_data.update({
            'periods_data': periods_data,
            'file_name': file_name
        })
        
        extracted_count = sum(len(data) for data in periods_data.values())
        await update.message.reply_text(
            f"✅ Файл успешно обработан!\n"
            f"📊 Извлечено показателей: {extracted_count}\n"
            f"📅 Периодов: {len(periods)}\n\n"
            f"🎯 Теперь выберите тип анализа!"
        )

    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка при анализе: {str(e)}")

async def perform_full_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Полный финансовый анализ"""
    if 'periods_data' not in context.user_data:
        await update.message.reply_text("❌ Сначала загрузите файл с данными")
        return
    
    await update.message.reply_text("🔍 Выполняю полный финансовый анализ...")
    
    periods_data = context.user_data['periods_data']
    
    report = "📊 **ПОЛНЫЙ ФИНАНСОВЫЙ АНАЛИЗ**\n\n"
    
    # Основные показатели
    report += "💰 **ДИНАМИКА ПОКАЗАТЕЛЕЙ:**\n\n"
    
    key_indicators = ['выручка', 'чистая прибыль', 'активы всего', 'капитал']
    
    for indicator in key_indicators:
        values = []
        for period, data in periods_data.items():
            if data and indicator in data:
                values.append((period, data[indicator]))
        
        if values:
            report += f"📈 **{indicator.title()}:**\n"
            for period, value in values:
                report += f"• {period}: {value:,.0f} руб.\n"
            
            if len(values) >= 2:
                first_val = values[0][1]
                last_val = values[-1][1]
                change = ((last_val - first_val) / first_val * 100) if first_val != 0 else 0
                trend = "📈" if change > 0 else "📉" if change < 0 else "➡️"
                report += f"  {trend} Изменение: {change:+.1f}%\n"
            
            report += "\n"
    
    # Коэффициенты для последнего периода
    last_period = list(periods_data.keys())[-1]
    last_data = periods_data[last_period]
    ratios = calculate_ratios(last_data)
    
    if ratios:
        report += f"📈 **ФИНАНСОВЫЕ КОЭФФИЦИЕНТЫ ({last_period}):**\n\n"
        for ratio_name, value in ratios.items():
            if 'рентабельность' in ratio_name.lower():
                report += f"• {ratio_name}: {value:.1f}%\n"
            else:
                report += f"• {ratio_name}: {value:.2f}\n"
        
        # Оценка ликвидности
        if 'Коэффициент текущей ликвидности' in ratios:
            cr = ratios['Коэффициент текущей ликвидности']
            report += f"\n💧 **ОЦЕНКА ЛИКВИДНОСТИ:** "
            if cr >= 2.0:
                report += "✅ Отличная\n"
            elif cr >= 1.5:
                report += "⚠️ Нормальная\n"
            elif cr >= 1.0:
                report += "🟡 Пониженная\n"
            else:
                report += "❌ Критическая\n"
    
    await update.message.reply_text(report)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    text = update.message.text
    
    if text == "📊 Полный анализ":
        await perform_full_analysis(update, context)
    elif text == "📈 Анализ ликвидности":
        await update.message.reply_text("💧 Анализирую ликвидность...\n\n🔧 Функция в разработке")
    elif text == "💎 Анализ рентабельности":
        await update.message.reply_text("💎 Анализирую рентабельность...\n\n🔧 Функция в разработке")
    elif text == "🏛️ Финансовая устойчивость":
        await update.message.reply_text("🏛️ Анализирую устойчивость...\n\n🔧 Функция в разработке")
    elif text == "📋 Сравнение с нормативами":
        await update.message.reply_text("🏭 Сравниваю с нормативами...\n\n🔧 Функция в разработке")
    elif text == "🔮 Прогноз тенденций":
        await update.message.reply_text("🔮 Строю прогноз...\n\n🔧 Функция в разработке")
    elif text == "📄 Экспорт в TXT":
        await update.message.reply_text("📄 Создаю отчет...\n\n🔧 Функция в разработке")
    elif text == "🎯 Выборочный анализ":
        await update.message.reply_text("🎯 Выборочный анализ...\n\n🔧 Функция в разработке")
    elif text == "📁 Загрузить Excel":
        await update.message.reply_text("📎 Пожалуйста, загрузите Excel файл с отчетностью")
    elif text == "ℹ️ Помощь":
        await help_command(update, context)

def main():
    """Основная функция"""
    print("🚀 Запуск полной версии бота...")
    
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("✅ Полная версия бота успешно запущена!")
    print("💡 Готов к работе с Excel файлами!")
    
    application.run_polling()

if __name__ == '__main__':
    main()
