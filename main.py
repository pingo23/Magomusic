import discord
from discord.ext import commands
import yt_dlp
import asyncio
import os

# Configuração do bot
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

# Criar diretório para armazenar músicas
if not os.path.exists("music"):
    os.makedirs("music")

# Fila de músicas
music_queue = []
is_looping = False  # Controle do loop

# Baixar áudio do YouTube
def download_audio(query):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': 'music/%(title)s.%(ext)s',
        'noplaylist': True
    }
    
    search_query = f"ytsearch:{query}"  # Garantir que seja interpretado como busca
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search_query, download=True)['entries'][0]  # Pega o primeiro resultado
            return f"music/{info['title']}.mp3", info['title']
    except Exception as e:
        print(f"Erro ao baixar áudio: {e}")
        return None, None

@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user}')

@bot.command()
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        await channel.connect()
    else:
        await ctx.send("Você precisa estar em um canal de voz!")

@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        # Enviar a mensagem quando o bot se desconectar
        await ctx.send("Feito por 3miojo, obrigado por usar meu bot!")
    else:
        await ctx.send("O bot não está em um canal de voz!")

@bot.command()
async def play(ctx, *, query):
    global is_looping

    if not ctx.voice_client:
        await ctx.invoke(join)
    
    await ctx.send("Buscando a música... 🎵")
    file_path, title = download_audio(query)
    
    if not file_path:
        await ctx.send("Erro ao baixar a música. Tente novamente!")
        return

    music_queue.append(file_path)  # Adicionar à fila de músicas
    if len(music_queue) == 1:  # Se a fila estava vazia, começa a tocar imediatamente
        await play_next(ctx)
    else:
        await ctx.send(f"Adicionado à fila: {title}")

# Função para tocar a próxima música na fila
async def play_next(ctx):
    if len(music_queue) > 0:
        file_path = music_queue[0]  # Pega o arquivo da primeira música na fila
        title = file_path.split("/")[-1].split(".")[0]
        
        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()

        ctx.voice_client.play(discord.FFmpegPCMAudio(file_path), after=lambda e: cleanup_audio(file_path))

        await ctx.send(f'Tocando agora: {title}')
        
        if not is_looping:
            music_queue.pop(0)  # Remove a música tocada da fila

# Remover arquivos de música após a reprodução
def cleanup_audio(file_path):
    try:
        os.remove(file_path)
        print(f"Arquivo removido: {file_path}")
    except Exception as e:
        print(f"Erro ao remover arquivo: {e}")

@bot.command()
async def loop(ctx):
    global is_looping
    is_looping = not is_looping  # Alterna entre loopando ou não
    if is_looping:
        await ctx.send("A música atual está em loop!")
    else:
        await ctx.send("O loop da música foi desativado!")

@bot.command()
async def skip(ctx):
    if ctx.voice_client:
        if len(music_queue) > 1:  # Se houver mais de uma música na fila
            music_queue.pop(0)  # Remove a música atual
            await play_next(ctx)  # Toca a próxima música
            await ctx.send("Música pulada!")
        else:
            await ctx.send("Não há músicas suficientes na fila para pular!")
    else:
        await ctx.send("O bot não está tocando música no momento!")

@bot.command()
async def credits(ctx):
    await ctx.send("Bot desenvolvido por 3miojoAndCrentex157")

bot.run('MTM1MjYwNTkzNTU1MzQ3ODY2Nw.Gxg8Ii._5Z3ttow1Y9YRdyAln5jF5iOr0RQdhaSGjLKKQ')
