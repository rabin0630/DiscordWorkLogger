import os

from dotenv import load_dotenv
load_dotenv()

# .envにある情報を得る場所

## MYSQL_INFO
MYSQL_INFO = {
    'USER': os.getenv('DB_USER'),
    'PASSWORD': os.getenv('PASSWORD'),
    'HOST': os.getenv('HOST'),
    'DATABASE': os.getenv('DATABASE')
}

## DISCORD_BOT_CONFIG
DISCORD_BOT_CONFIG = {
    'TOKEN': os.getenv('DISCORD_TOKEN'),
    'GUILD_ID': os.getenv('TARGET_GUILD_ID'),
    'CHANNEL_ID': os.getenv('TARGET_CHANNEL_ID')
}
