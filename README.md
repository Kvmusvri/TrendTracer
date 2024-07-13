# TrendTracer

Новостной телеграмм бот в сфере финансов. Использует модель машинного обучения для классификации текста. 

Данные собраны с сайта-агрегатора TradingView.

Бот собирает данные, оценивает сентимент и выставляет новости оценку от 1 до 5. Составляет таблицу лидеров на основе полученных оценок. Делает краткую суммаризацию полученной новости.

Таблица лидеров составляется путем вычисления среднего арифметического всех накопленных оценок в базе данных.

СУБД - MySQL.

ЯП - Python 3.11.5.

## Используемые модели:
* Для суммаризации Gigachat.
* Для оценки сентимента DistilRoberta-financial-sentiment (https://huggingface.co/mrm8488/distilroberta-finetuned-financial-news-sentiment-analysis).
* Для составления таблицы лидеров bert-base-multilingual-uncased-sentiment (https://huggingface.co/nlptown/bert-base-multilingual-uncased-sentiment).

Дообучение моделей не производилось.

## Используемые библиотеки
|Lib|Version|
|---|-------|
|APScheduler|3.10.4|
|regex|2023.12.25|
|requests|2.31.0|
|scipy|1.12.0|
|sympy|1.12|
|tensorboard|2.12.3|
|tensorflow-intel|2.12.0|
|tokenizers|0.15.2|
|torch|2.1.0+cpu|
|transformers|4.38.2|

## Для работы требуется
|--------------------|
|Токен Gigachat|
|Токен Telegram|
|Подключение к БД|








