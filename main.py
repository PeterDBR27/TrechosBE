import tweepy
import time
import random
import json
import sys
import logging
import datetime
import pytz

from decouple import config

logging.basicConfig(level=logging.INFO)

consumer_key = config('CONSUMER_KEY')
consumer_secret = config('CONSUMER_SECRET')
access_token = config('ACCESS_TOKEN')
access_token_secret = config('ACCESS_TOKEN_SECRET')

client = tweepy.Client(
    consumer_key=consumer_key,
    consumer_secret=consumer_secret,
    access_token=access_token,
    access_token_secret=access_token_secret
)

def obter_verso_aleatorio():
    with open('letras_be.json', 'r', encoding='utf-8') as file: # temos 204 frases (2 por dia então 104 dias)
        dados = json.load(file)

    musica_escolhida = random.choice(list(dados.keys()))
    verso = random.choice(dados[musica_escolhida]).strip()

    return verso, musica_escolhida

def criar_tweet(verso, musica):
    if musica == "lovely":
        cantora = "Billie Eilish (with Khalid)"
    elif musica == "&burn":
        cantora = "Billie Eilish (with Vince Staples)"
    else:
        cantora = "Billie Eilish & FINNEAS"
    assinatura = f"— {musica}, {cantora}"
    tweet = f'"{verso}"\n\n{assinatura}'
    return tweet

def enviar_tweet(tweet):
    try:
        response = client.create_tweet(
            text=tweet,
        )
        tweet_id = response.data['id']
        logging.info(f"Tweet enviado: https://twitter.com/user/status/{tweet_id}")
        return True
    except Exception as e:
        if e.api_codes == 401:
            logging.error("Erro de autenticação: As chaves ou tokens podem estar incorretos.")
        elif e.api_codes == 429:
            logging.warning("Limite de taxa atingido. Aguardando antes de enviar o próximo tweet.")
            time.sleep(60 * 15)
        elif e.api_codes == 403 and "duplicate" in e.message.lower():
            logging.warning("Tweet duplicado. Tentando com outra frase.")
            time.sleep(60 * 15)
        else:
            logging.error(f"Erro ao enviar tweet: {e}")
        return False

def formatar_tempo(minutos):
    horas = int(minutos // 60)
    minutos_restantes = int(minutos % 60)

    if horas > 0 and minutos_restantes > 0:
        return f"{horas} horas e {minutos_restantes} minutos"
    elif horas > 0:
        return f"{horas} horas"
    else:
        return f"{minutos_restantes} minutos"

def agendar_proximo_tweet():
    agora = datetime.datetime.now(pytz.timezone("America/Sao_Paulo"))
    proximo_meio_dia = agora.replace(hour=12, minute=0, second=0, microsecond=0)
    proximo_seis_horas = agora.replace(hour=18, minute=0, second=0, microsecond=0)

    if agora < proximo_meio_dia:
        espera_segundos = (proximo_meio_dia - agora).total_seconds()
    elif agora < proximo_seis_horas:
        espera_segundos = (proximo_seis_horas - agora).total_seconds()
    else:
        amanha_meio_dia = proximo_meio_dia + datetime.timedelta(days=1)
        espera_segundos = (amanha_meio_dia - agora).total_seconds()

    minutos_restantes = espera_segundos // 60
    tempo_formatado = formatar_tempo(minutos_restantes)
    logging.info(f"Próximo tweet em {tempo_formatado}.")
    time.sleep(espera_segundos)

if __name__ == "__main__":
    try:
        while True:
            agendar_proximo_tweet()
            verso_aleatorio, musica_aleatoria = obter_verso_aleatorio()
            while verso_aleatorio:
                tweet = criar_tweet(verso_aleatorio, musica_aleatoria)
                enviado_com_sucesso = enviar_tweet(tweet)

                if enviado_com_sucesso:
                    break

                verso_aleatorio, musica_aleatoria = obter_verso_aleatorio()
    except KeyboardInterrupt:
        logging.info("Trechos Billie Eilish se desconectou!")
        sys.exit(0)