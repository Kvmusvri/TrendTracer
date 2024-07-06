from core.infrastructure import db_config
from core.settings import settings
from datetime import datetime
import re


def fill_leader_news_post(leader_dict: dict, leader_sorted_ticket:dict) -> list:
    news_str_arr = []
    limit_ten_ticket = 0
    for ticket in leader_sorted_ticket:
        if limit_ten_ticket == 10:
            return news_str_arr
        news_str_arr.append(f"{limit_ten_ticket+1}. #{ticket} - {leader_dict[ticket]}")
        limit_ten_ticket += 1

    return news_str_arr


def eval_emodzi(news_score: str) -> str:
    score_emodzi = ''
    if news_score == 'positive':
        score_emodzi = '🟢'
    if news_score == 'negative':
        score_emodzi = '🔴'
    if news_score == 'neutral':
        score_emodzi = '⚪'
    return score_emodzi


def create_news_sql(num_rows: int) -> dict:
    cursor = db_config.connection.cursor()

    cursor.execute(db_config.query[2], num_rows)
    rows_list = cursor.fetchall()

    news_post_dict = {}
    for i in range(len(rows_list)):
        cursor.execute(db_config.query[3], rows_list[i]['article_id'])
        exist_row = cursor.fetchall()
        if exist_row[0]['article_use']:
            pass
            # print('Старая статья')
        else:
            # print('Новая статья')
            cursor.execute(db_config.query[4], rows_list[i]['article_id'])
            db_config.connection.commit()

            if rows_list[i]['article_ticker']:
                s = re.split(', ', str(rows_list[i]['article_ticker']))
                news_article_ticker = ''
                for string in s:
                    news_article_ticker += "#" + string + ' '
                news_article_ticker = news_article_ticker[:-1]
            else:
                news_article_ticker = '#Общее'

            news_date_string = re.split(' ', str(datetime.fromtimestamp(float(rows_list[i]['article_date_timestamp']))))
            news_date_string[0] = "-".join(re.split('-', news_date_string[0])[::-1])
            news_date_string = ' '.join(news_date_string)

            news_article_url = rows_list[i]['article_url']
            news_article_body = rows_list[i]['article_text']
            news_article_title = rows_list[i]['article_title']

            news_post_dict[rows_list[i]['article_id']] = {
                'news_article_url': news_article_url,
                'news_date_string': news_date_string,
                'news_article_body': news_article_body,
                'news_article_ticker': news_article_ticker,
                'news_article_title': news_article_title
            }

    cursor.close()
    return news_post_dict


def add_company_score(tickets_string: str, news_score: int) -> None:
    if "#Общее" in tickets_string:
        return

    cursor = db_config.connection.cursor()
    cursor.execute(db_config.query[7])
    all_tickets = cursor.fetchall()
    exist_tickets = []
    for ticket in all_tickets:
        exist_tickets.append(ticket['company_ticket'])

    company_tickets = tickets_string.replace(' ', '').split('#')
    if company_tickets[0] == '':
        company_tickets.pop(0)

    # print(company_tickets)

    for company_ticket in company_tickets:
        if company_ticket in exist_tickets:
            # прибавляем к существующему число
            cursor.execute(db_config.query[6], [news_score, company_ticket])
            # print('Нашлось прибавилось')

        # добавляем новую строку с news_score
        else:
            cursor.execute(db_config.query[5], [company_ticket, news_score])
            # print('не нашлось создалось')

    db_config.connection.commit()

    cursor.close()


def choice_news_pic(news_score: str) -> str:
    use_news_pic = ''
    if news_score == 'positive':
        use_news_pic = settings.bots.news_good_pic_path
    if news_score == 'negative':
        use_news_pic = settings.bots.news_bad_pic_path
    if news_score == 'neutral':
        use_news_pic = settings.bots.news_pic_path
    return use_news_pic