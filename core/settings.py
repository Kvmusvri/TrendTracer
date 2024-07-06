from environs import Env
from dataclasses import dataclass


@dataclass
class Bots:
    bot_token: str
    admin_id: int
    channel_id: int
    news_pic_path: str
    news_good_pic_path: str
    news_bad_pic_path: str
    leader_good_pic: str
    leader_bad_pic: str
    sber_auth: str
    sber_id: str
    sber_secret: str
    host: str
    user: str
    password: str
    db_name: str


@dataclass
class Settings:
    bots: Bots


def get_settings(path: str):
    env = Env()
    env.read_env(path)

    return Settings(
        bots=Bots(
            bot_token=env.str("TOKEN_API"),
            admin_id=env.int("USER_ID"),
            channel_id=env.int("CHANNEL_ID"),
            news_pic_path=env.str("NEWS_PIC_PATH"),
            news_good_pic_path=env.str("NEWS_GOOD_PIC"),
            news_bad_pic_path=env.str("NEWS_BAD_PIC"),
            leader_good_pic=env.str("LEADER_GOOD_PIC"),
            leader_bad_pic=env.str("LEADER_BAD_PIC"),
            sber_auth=env.str("SBER_AUTH"),
            sber_id=env.str("SBER_ID"),
            sber_secret=env.str("SBER_SECRET"),
            host=env.str("HOST"),
            user=env.str("USER"),
            password=env.str("PASSWORD"),
            db_name=env.str("DB_NAME")

        )
    )


settings = get_settings(r'input')
# print(settings)