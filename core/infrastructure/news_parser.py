from core.infrastructure import db_config
import requests
import re


def collect_data(article_cards: list, num_news: int) -> dict:
    """
    Парсинг статей с сайта tradingview
    :param article_cards: список ссылок на статьи
    :param num_news: кол-во статей которое нужно взять из списка ссылок
    :return news_dict: словарь собранных статей
    """

    news_dict = {}
    for article in range(num_news):
        article_url = f'https://ru.tradingview.com/news/{article_cards[article]}/'
        request_link = f"https://news-headlines.tradingview.com/v2/story?id={article_cards[article]}&lang=ru"
        article_r = requests.get(url=request_link).json()

        main_string = ''
        article_body = article_r['astDescription']['children']
        # флаг таблицы
        is_table = False
        for i in article_body:
            if i['type'] == 'table':
                is_table = True
                break

        # Если статья - таблица, пропускаем
        # Статья является таблицей, если флаг таблицы true

        if not is_table:
            # Собираем тело статьи
            for i in range(len(article_body)):
                # print(article_body[i]['children'])
                for j in range(len(article_body[i]['children'])):
                    if isinstance(article_body[i]['children'][j], str):
                        main_string += article_body[i]['children'][j]
                if i != len(article_body) - 1:
                    main_string += '\n\n'

            main_string = re.sub('  ', ' ', main_string)
            main_string = main_string.replace('>', '').replace('<', '')
            # id статьи - последние цифры в ссылке
            # из заголовка убираем лишние кавычки
            article_id = article_r['id'].split(':')[-2]
            article_title = article_r['title'].strip().replace('"', '')

            # собираем тикер компании из статьи, тикеров может быть несколько или не быть вообще
            article_ticker_list = []
            try:
                for i in range(len(article_r['relatedSymbols'])):
                    if article_r['relatedSymbols'][i]['symbol'].split(':')[0] == 'MOEX':
                        article_ticker_list.append(article_r['relatedSymbols'][i]['symbol'].split(':')[1])

                article_ticker = ', '.join(article_ticker_list)
            except Exception:
                article_ticker = ''

            # собираем дату статьи в формате timestamp
            article_date_timestamp = article_r['published']

            # записываем все полученные данные в словарь и возвращаем его
            news_dict[article_id] = {
                "article_url": article_url,
                "article_date_timestamp": article_date_timestamp,
                "article_ticker": article_ticker,
                "article_title": article_title,
                "article_text": main_string,
            }

            # print(news_dict)

    return news_dict


def write_data_sql(news_dict: dict):
    """
        Запись собранных данных в mysql базу данных
        :param news_dict: словарь статей, которые необходимо внести в базу данных
        :return:
    """
    # получаем в виде списка заголовки и айдишники статей
    labels = list(news_dict[list(news_dict.keys())[0]].keys())
    dict_keys = list(news_dict.keys())[::-1]
    cursor = db_config.connection.cursor()
    for key in range(len(dict_keys)):
        cursor.execute(db_config.query[0], dict_keys[key])
        exist_row = cursor.fetchall()
        if exist_row:
            # print("Старая статья")
            continue
        else:
            # print("Новая статья")
            row_values = [dict_keys[key]]
            for label in range(len(labels)):
                row_values.append(news_dict[dict_keys[key]][labels[label]])
            cursor.execute(db_config.query[1], row_values)
            db_config.connection.commit()
    cursor.close()


def get_first_news(nums_news: int):
    """
    Получает элементы статьи из собранного словаря и производит запись в MySQL базу данных
    :return:
    """

    url = "https://news-headlines.tradingview.com/v2/headlines?category=stock&client=web&lang=ru&market_country=RU&streaming=true"
    response = requests.get(url=url).json()

    article_cards = []
    for i in range(len(response['items'])):
        link = response['items'][i]['id']
        article_cards.append(link)

    # получаем словарь статей с указанной размерностью
    # если словаря не существует, значит на сайте случился сбой
    news_dict = collect_data(article_cards, nums_news)
    if news_dict:
        write_data_sql(news_dict)
    else:
        print('В данный момент невозможно cобрать данные')


def main():
    get_first_news(10)


if __name__ == '__main__':
    main()
