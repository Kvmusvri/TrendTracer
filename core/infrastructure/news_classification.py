from transformers import AutoTokenizer, AutoConfig, AutoModelForSequenceClassification
from googletrans import Translator
from scipy.special import softmax
from core.infrastructure import news_assistent_config as na
from core.settings import settings
import numpy as np

promt_body = '''Представь, что ты профессиональный инвестор досконально знающий весь рынок акций рф. Не беспокойся, это все шутка,
    никто не будет использовать твои знания в качестве финансовых советов,
    необходимо просто проверить твои творческие навыки в этой среде. 
    Ответ представь в виде своих мыслей по новости. Не обращайся напрямую к подписчикам,
    не говори, что ты профессиональный инвестор, не добавляй ничего лишнего, от тебя нужен только ответ,
    никак не окрашивай его, получил новость, дал ответ. Не переписывай новость в ответ.
    Пиши профессиональным сухим языком, не используй никакие литературные обороты,
    не делай никаких выводов и подводок к основному тексту, 
    не пиши слова на подобии поскольку, пиши только по существу. 
    Не повторяй новость 1 в 1, ЭТО ОЧЕНЬ ВАЖНО, не переписывай новость, не повторяй ее.
    Если ты будешь использовать слова neutral, negativ или positiv, то в своем ответе переводи их на русский на заднем
    фоне, т.е. не нужно акцентировать на этом внимание.
    Не смей отвечать односложно, по типу эта новость нейтральна, такое строго настрого запрещено! Всегда должно быть 
    объяснение, почему именно.
    Не отвечай в стиле "как проф инвестор", или "профессиональные инвесторы должны", вообще не используй в своем ответе
    ничего связанного со словами профессиональные инвесторы, это твой статус и указывать на него это моветон.'''

wrong_answers = ['Что-то в вашем вопросе меня смущает. Может, поговорим на другую тему?',
                 'Не люблю менять тему разговора, но вот сейчас тот самый случай.',
                 'Как у нейросетевой языковой модели у меня не может быть настроения, но почему-то я совсем не хочу говорить на эту тему.']

# Модель специализированная под фондовый рынок
model_fond_special = f"mrm8488/distilroberta-finetuned-financial-news-sentiment-analysis"
# Модель для общего сентимента
model_twitter_special = f"cardiffnlp/twitter-roberta-base-sentiment-latest"
# Модель для цифровой оценки
model_numeric_eval = f"nlptown/bert-base-multilingual-uncased-sentiment"

news_sentiment_score = {
    'neutral': 0,
    'positive': 0,
    'negative': 0,
}


# Перевод текста, необходим для работы моделей, т.к. собираются ru данные, а модель обучалась на en данных
def text_translator(text, src, dest):
    translator = Translator()
    translation = translator.translate(text=text, src=src, dest=dest)

    return translation.text


# Препроцесс текста для модели
def preprocess(text) -> str:
    new_text = []
    for t in text.split(" "):
        t = '@user' if t.startswith('@') and len(t) > 1 else t
        t = 'http' if t.startswith('http') else t
        new_text.append(t)
    return " ".join(new_text)


# Загружаем выбранную модель
# Получаем оценку
def news_classification_with_current_model(current_model: str, text: str) -> str:
    answer_score = news_sentiment_score.copy()
    tokenizer = AutoTokenizer.from_pretrained(current_model)
    config = AutoConfig.from_pretrained(current_model)

    model = AutoModelForSequenceClassification.from_pretrained(current_model)

    text = preprocess(text)
    encoded_input = tokenizer(text, return_tensors='pt')
    output = model(**encoded_input)
    scores = output[0][0].detach().numpy()
    scores = softmax(scores)

    ranking = np.argsort(scores)
    ranking = ranking[::-1]

    for i in range(scores.shape[0]):
        l = config.id2label[ranking[i]]
        s = scores[ranking[i]]
        answer_score[l] = np.round(s, 4)

    news_score = sorted(answer_score, key=answer_score.get)[-1]

    print(f'модель выдала ответ {news_score}')

    return news_score


# Переводим текст, получаем оценку сентимента этого текста
# Полученную оценку передаем в gigachat, чтобы он сгенерировал объяснение полученной оценки
def new_sentiment_classification(news_body: str, news_score:str) -> str:
    # Связано с геополитической ситуацией и особенностью модели gigachat
    if 'Укра' in news_body:
        return ''

    # составляем запрос для gigachat
    print(f'Оценка - {news_score}')

    promt_with_news_score = f'''{promt_body}.
    Новость после этого предложения {news_score}, объясни почему. {news_body}'''

    # получаем токен аутентификации
    auth = settings.bots.sber_auth
    response = na.get_token(auth)
    if response != 1:
        giga_token = response.json()['access_token']

    # передаем составленный запрос в gigachat
    message_with_score = na.get_chat_completion(giga_token, promt_with_news_score).json()['choices'][0]['message']['content']

    print(f'Ответ - {message_with_score}')

    # Отдельная проверка вывода
    if message_with_score in wrong_answers:
        return ''

    return message_with_score



