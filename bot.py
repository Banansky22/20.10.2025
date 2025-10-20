import os
import logging
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

print("✅ Бот запускается...")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton("📊 Анализ ликвидности"), KeyboardButton("💎 Анализ рентабельности")],
        [KeyboardButton("🏛️ Финансовая устойчивость"), KeyboardButton("📋 Калькулятор")],
        [KeyboardButton("ℹ️ Помощь")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "🤖 **ФИНАНСОВЫЙ АНАЛИЗАТОР**\n\n"
        "💡 Я помогу проанализировать ваши финансовые показатели!\n\n"
        "Выберите тип анализа:",
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
💡 **ФИНАНСОВЫЙ АНАЛИЗАТОР**

📊 **Доступные функции:**
• 📊 Анализ ликвидности
• 💎 Анализ рентабельности  
• 🏛️ Финансовая устойчивость
• 📋 Калькулятор коэффициентов

📝 **Как использовать:**
Выберите тип анализа и следуйте инструкциям.

🔢 **Примеры ввода:**
• Для ликвидности: 300000 200000
• Для рентабельности: 150000 1000000
• Для устойчивости: 400000 800000
"""
    await update.message.reply_text(help_text)

async def handle_liquidity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Анализ ликвидности"""
    await update.message.reply_text(
        "💧 **АНАЛИЗ ЛИКВИДНОСТИ**\n\n"
        "Введите два числа через пробел:\n"
        "• Оборотные активы\n" 
        "• Краткосрочные обязательства\n\n"
        "Пример: 300000 200000"
    )
    context.user_data['waiting_for'] = 'liquidity'

async def handle_profitability(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Анализ рентабельности"""
    await update.message.reply_text(
        "💎 **АНАЛИЗ РЕНТАБЕЛЬНОСТИ**\n\n"
        "Введите два числа через пробел:\n"
        "• Чистая прибыль\n"
        "• Выручка\n\n"
        "Пример: 150000 1000000"
    )
    context.user_data['waiting_for'] = 'profitability'

async def handle_stability(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Анализ финансовой устойчивости"""
    await update.message.reply_text(
        "🏛️ **ФИНАНСОВАЯ УСТОЙЧИВОСТЬ**\n\n"
        "Введите два числа через пробел:\n"
        "• Собственный капитал\n"
        "• Всего активов\n\n"
        "Пример: 400000 800000"
    )
    context.user_data['waiting_for'] = 'stability'

async def handle_calculator(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Калькулятор коэффициентов"""
    await update.message.reply_text(
        "📋 **КАЛЬКУЛЯТОР КОЭФФИЦИЕНТОВ**\n\n"
        "Введите два числа через пробел для расчета любого коэффициента.\n\n"
        "Пример: 300000 200000"
    )
    context.user_data['waiting_for'] = 'calculator'

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "📊 Анализ ликвидности":
        await handle_liquidity(update, context)
    elif text == "💎 Анализ рентабельности":
        await handle_profitability(update, context)
    elif text == "🏛️ Финансовая устойчивость":
        await handle_stability(update, context)
    elif text == "📋 Калькулятор":
        await handle_calculator(update, context)
    elif text == "ℹ️ Помощь":
        await help_command(update, context)
    else:
        # Обработка числового ввода
        await process_numeric_input(update, context, text)

async def process_numeric_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Обрабатывает числовой ввод"""
    try:
        if ' ' in text:
            numbers = [float(x) for x in text.split()]
            if len(numbers) == 2:
                a, b = numbers
                
                if b == 0:
                    await update.message.reply_text("❌ Ошибка: деление на ноль")
                    return
                
                ratio = a / b
                analysis_type = context.user_data.get('waiting_for', 'calculator')
                
                report = f"📊 **РЕЗУЛЬТАТ АНАЛИЗА**\n\n"
                report += f"• Число A: {a:,.0f} руб.\n"
                report += f"• Число B: {b:,.0f} руб.\n"
                report += f"• Коэффициент: {ratio:.2f}\n\n"
                
                if analysis_type == 'liquidity':
                    report += "💧 **КОЭФФИЦИЕНТ ТЕКУЩЕЙ ЛИКВИДНОСТИ**\n"
                    if ratio >= 2.0:
                        report += "✅ Отличная ликвидность\n"
                        report += "💡 Рекомендация: Поддерживать текущий уровень"
                    elif ratio >= 1.5:
                        report += "⚠️ Нормальная ликвидность\n"
                        report += "💡 Рекомендация: Контролировать динамику"
                    elif ratio >= 1.0:
                        report += "🟡 Пониженная ликвидность\n"
                        report += "💡 Рекомендация: Увеличить оборотные активы"
                    else:
                        report += "❌ Критическая ликвидность\n"
                        report += "💡 Рекомендация: Срочно оптимизировать"
                
                elif analysis_type == 'profitability':
                    percentage = ratio * 100
                    report += f"💎 **РЕНТАБЕЛЬНОСТЬ ПРОДАЖ: {percentage:.1f}%**\n"
                    if percentage >= 15:
                        report += "🚀 Высокая рентабельность\n"
                    elif percentage >= 8:
                        report += "✅ Хорошая рентабельность\n"
                    elif percentage >= 5:
                        report += "⚠️ Средняя рентабельность\n"
                    else:
                        report += "❌ Низкая рентабельность\n"
                
                elif analysis_type == 'stability':
                    report += "🏛️ **КОЭФФИЦИЕНТ АВТОНОМИИ**\n"
                    if ratio >= 0.5:
                        report += "✅ Высокая автономия\n"
                    elif ratio >= 0.3:
                        report += "⚠️ Средняя автономия\n"
                    else:
                        report += "❌ Низкая автономия\n"
                
                else:  # calculator
                    report += "📋 **РАСЧЕТ КОЭФФИЦИЕНТА**\n"
                    if ratio > 1:
                        report += "📈 Значение выше 1.0"
                    elif ratio == 1:
                        report += "➡️ Значение равно 1.0"
                    else:
                        report += "📉 Значение ниже 1.0"
                
                await update.message.reply_text(report)
                return
        
        await update.message.reply_text(
            "❌ Введите два числа через пробел\n\n"
            "Пример: 300000 200000"
        )
        
    except ValueError:
        await update.message.reply_text(
            "❌ Ошибка: введите только числа\n\n"
            "Пример: 300000 200000"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка обработки: {str(e)}")

def main():
    """Основная функция"""
    print("🚀 Запуск финансового анализатора...")
    
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("✅ Бот успешно запущен!")
    print("💡 Готов к работе!")
    
    application.run_polling()

if __name__ == '__main__':
    main()
