from core.infrastructure import db_config
from core.infrastructure.news_parser import get_first_news
from core.infrastructure.news_classification import text_translator, news_classification_with_current_model
from core.infrastructure.news_classification import model_numeric_eval, model_fond_special, new_sentiment_classification
from core.settings import settings
from core.infrastructure import utils
from aiogram import Bot
from aiogram.types import FSInputFile


async def post_news(num_news: int, bot: Bot) -> None:
    get_first_news(num_news)
    news_post_dict = utils.create_news_sql(num_news)
    # print(news_post_dict)
    dict_keys = list(news_post_dict.keys())[::-1]

    # Заголовки бесполезных повторяющихся новостей. Они всегда будут нейтральными
    useless_news = ['Положительное сальдо операций ЦБ РФ',
                    'Газпром подает газ через Украину на ГИС Суджа',
                    'Депозиты банков в ЦБ составили']
    # собираем пост
    useless = False
    if len(news_post_dict):
        for key in range(len(dict_keys)):
            for useless_tittle in useless_news:
                if useless_tittle in news_post_dict[dict_keys[key]]['news_article_title']:
                    useless = True
            # Если статья не от ПРАЙМ, пропускаем ее
            if "newsml" in news_post_dict[dict_keys[key]]['news_article_url']:
                continue
            # Если статья входит в категорию бесполезных, пропускаем ее
            if useless:
                continue
            # print(news_post_dict[dict_keys[key]]['news_article_ticker'])
            try:
                # print(f"Заголовок - {news_post_dict[dict_keys[key]]['news_article_title']}")

                news_trans_body = (text_translator(news_post_dict[dict_keys[key]]['news_article_title'],
                                                   src='ru',
                                                   dest='en'))

                # получаем оценку новости
                news_score = news_classification_with_current_model(model_fond_special, news_trans_body[0:500])
                score_emodzi = utils.eval_emodzi(news_score)
                # print(f'новость получила {score_emodzi}')

                # Если новость нейтральна, то она никак не влияет на компанию
                # Если компания упоминалась в новости типа Российский рынок акций упал\вырос, то такая новость
                # никак не влияет на компанию
                if not news_score == 'neutral':
                    if 'Российский рынок акций' not in news_post_dict[dict_keys[key]]['news_article_title']:
                        # print('Новость не нейтральна, очки добавились')
                        ticket_score = news_classification_with_current_model(model_numeric_eval, news_post_dict[dict_keys[key]]['news_article_body'][0:500])
                        utils.add_company_score(news_post_dict[dict_keys[key]]['news_article_ticker'], int(ticket_score[0]))

                # получаем объяснение от gigachat
                giga_explain = (
                    new_sentiment_classification(news_post_dict[dict_keys[key]]['news_article_body'][0:500],
                                                 news_score))

                # Выкладываем часть, которую полностью сделала машина
                # Разделение вывода связано с ограничением в 4096 символов в сообщении у телеграмма
                machine_part_news = (
                    f"{score_emodzi}{news_post_dict[dict_keys[key]]['news_article_title']}\n\n"
                    f"_{giga_explain}_\n\n"
                )

                await bot.send_photo(chat_id=settings.bots.channel_id,
                                     photo=FSInputFile(utils.choice_news_pic(news_score)),
                                     caption=machine_part_news,
                                     parse_mode='MARKDOWN')

                # В телеграмме максимум допустимо 4096 символов (с пробелами)
                # если news_article_body больше этого значения, то делим на 2
                if len(news_post_dict[dict_keys[key]]['news_article_body'].lstrip()) >= 4000:
                    paragraphs = news_post_dict[dict_keys[key]]['news_article_body'].lstrip().split('\n\n')

                    first_half = '\n\n'.join(paragraphs[:int(len(paragraphs) / 2)])
                    second_half = '\n\n'.join(paragraphs[int(len(paragraphs) / 2):])

                    parts = [first_half, second_half]
                    for part in parts:
                        part_news = (
                            f"{score_emodzi}{part.lstrip()}\n\n"
                            f"{news_post_dict[dict_keys[key]]['news_date_string']} GMT+3\n"
                            f"{news_post_dict[dict_keys[key]]['news_article_ticker']}\n"
                        )
                        await bot.send_message(chat_id=settings.bots.channel_id,
                                               text=part_news,
                                               parse_mode='Markdown')
                else:
                    # Выкладываем собранную новость
                    news = (
                        f"{score_emodzi}{news_post_dict[dict_keys[key]]['news_article_body'].lstrip()}\n\n"
                        f"{news_post_dict[dict_keys[key]]['news_date_string']} GMT+3\n"
                        f"{news_post_dict[dict_keys[key]]['news_article_ticker']}\n"
                        
                    )

                    await bot.send_message(chat_id=settings.bots.channel_id,
                                           text=news,
                                           parse_mode='Markdown')
            except Exception as e:
                print(e)
                await bot.send_message(chat_id=settings.bots.admin_id,
                                       text=f"ВОЗНИКЛА ОШИБКА С ПОСТОМ\n{news_post_dict[dict_keys[key]]['news_article_title']}\n\n{e.with_traceback()}",
                                       parse_mode='Markdown')
                continue
    else:
        print('Нет новых статей')


async def leader_board(bot: Bot) -> None:
    cursor = db_config.connection.cursor()
    cursor.execute('SELECT * FROM company_scores WHERE company_ticket <> "IMOEX" AND company_ticket <> "RTSI" ;')
    all_companies = cursor.fetchall()

    cursor.execute('SELECT SUM(company_news_score) FROM company_scores WHERE company_ticket <> "IMOEX" AND company_ticket <> "RTSI";')
    sum_score = list(cursor.fetchall()[0].values())[0]

    mean = round(sum_score/len(all_companies))

    # # если больше среднего, считаем компанию хорошей
    good_companies = {}
    bad_companies = {}


    for i in range(len(all_companies)):
        if all_companies[i]['company_news_score'] > mean:
            good_companies[all_companies[i]['company_ticket']] = all_companies[i]['company_news_score']
        if all_companies[i]['company_news_score'] < mean:
            bad_companies[all_companies[i]['company_ticket']] = all_companies[i]['company_news_score']

    if len(good_companies) > len(bad_companies):
        # добавляем все компании рейтинг которых равен среднему в хорошие
        for i in range(len(all_companies)):
            if all_companies[i]['company_news_score'] == mean:
                good_companies[all_companies[i]['company_ticket']] = all_companies[i]['company_news_score']

    elif len(good_companies) < len(bad_companies):
        # добавляем все компании рейтинг которых равен среднему в плохие
        for i in range(len(all_companies)):
            if all_companies[i]['company_news_score'] == mean:
                bad_companies[all_companies[i]['company_ticket']] = all_companies[i]['company_news_score']

    good_companies_sorted_ticket = sorted(good_companies, key=good_companies.get)[::-1]
    bad_companies_sorted_ticket = sorted(bad_companies, key=bad_companies.get)[::-1]

    good_news = utils.fill_leader_news_post(good_companies, good_companies_sorted_ticket)
    bad_news = utils.fill_leader_news_post(bad_companies, bad_companies_sorted_ticket)

    good_string = '\n'.join(good_news)
    bad_string = '\n'.join(bad_news)

    if good_string:
        await bot.send_photo(chat_id=settings.bots.channel_id,
                             photo=FSInputFile(str(settings.bots.leader_good_pic)),
                             caption="Московская биржа\n\n__Тикеры с новостным рейтингом выше среднего__\n\n" +
                                     f"{good_string}\n\n#leaderboard",
                             parse_mode='Markdown'
                             )

    if bad_string:
        await bot.send_photo(chat_id=settings.bots.channel_id,
                             photo=FSInputFile(settings.bots.leader_bad_pic),
                             caption="Московская биржа\n\n__Тикеры с новостным рейтингом ниже среднего__\n\n" +
                                     f"{bad_string}\n\n#leaderboard",
                             parse_mode='Markdown'
                             )



