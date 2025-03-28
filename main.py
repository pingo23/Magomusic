import discord
from discord.ext import commands
import yt_dlp
import asyncio
import os
from dotenv import load_dotenv
import wavelink

# Carregar variáveis do .env
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
LAVALINK_HOST = os.getenv("LAVALINK_HOST", "localhost")
LAVALINK_PORT = os.getenv("LAVALINK_PORT", 2333)
LAVALINK_PASSWORD = os.getenv("LAVALINK_PASSWORD", "youshallnotpass")

if not TOKEN:
    raise ValueError("Token do Discord não encontrado! Verifique seu arquivo .env.")

# Configuração do bot
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents, reconnect=True)

# Variáveis globais
music_queue = []
is_playing = False

# Função para conectar ao Lavalink
async def connect_to_lavalink(ctx):
    node = await wavelink.NodePool.create_node(
        bot=bot,
        host=LAVALINK_HOST,
        port=LAVALINK_PORT,
        password=LAVALINK_PASSWORD,
        identifier="default",
        region="us_central"
    )
    await node.connect(ctx.guild.id)

# Função para obter URL do áudio sem download
def get_audio_stream(query):
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'default_search': 'ytsearch',
        'quiet': True,
        'timeout': 20
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=False)
            if 'entries' in info:
                info = info['entries'][0]
            return info['url'], info['title']
    except Exception as e:
        print(f"Erro ao obter áudio: {e}")
        return None, None

# Garante que o bot esteja no canal correto
async def ensure_voice(ctx):
    if not ctx.author.voice:
        await ctx.send("❌ Você precisa estar em um canal de voz para tocar músicas!")
        return

    voice_channel = ctx.author.voice.channel

    if ctx.voice_client:  # Se o bot já está conectado a um canal
        if ctx.voice_client.channel != voice_channel:
            await ctx.voice_client.move_to(voice_channel)
    else:
        try:
            await voice_channel.connect()
        except discord.errors.ClientException as e:
            await ctx.send(f"❌ Erro ao conectar no canal: {e}")

# Função para tocar música com Lavalink
async def play_music(ctx):
    global is_playing

    if not ctx.voice_client:
        await ctx.send("❌ Não estou conectado a um canal de voz!")
        is_playing = False
        return

    if not music_queue:
        is_playing = False
        return

    url, title = music_queue.pop(0)

    try:
        # Usando o Lavalink para tocar a música
        player = ctx.voice_client
        track = await wavelink.YouTubeTrack.search(query=url)
        await player.play(track[0])

        is_playing = True
        await ctx.send(f"🎶 Tocando agora: **{title}**")
    except Exception as e:
        await ctx.send("❌ Erro ao tentar tocar a música.")
        print(f"Erro ao tocar música: {e}")
        is_playing = False

# Função para verificar a fila
async def check_queue(ctx):
    global is_playing
    if music_queue:
        await play_music(ctx)
    else:
        is_playing = False
        await ctx.send("🎵 Fila vazia! Aguardando novas músicas.")

# Comando para tocar música
@bot.command()
async def play(ctx, *, query):
    global is_playing

    if not ctx.author.voice:
        await ctx.send("❌ Você precisa estar em um canal de voz!")
        return

    await ensure_voice(ctx)

    await ctx.send("🔎 Buscando música...")

    url, title = get_audio_stream(query)

    if not url:
        await ctx.send("❌ Erro ao buscar a música! Tente novamente.")
        return

    music_queue.append((url, title))

    if not is_playing:
        await play_music(ctx)
    else:
        await ctx.send(f"📌 **{title}** foi adicionada à fila!")

# Comando para mostrar a fila de músicas
@bot.command()
async def queue(ctx):
    if music_queue:
        queue_list = "\n".join(f"{i+1}. {song[1]}" for i, song in enumerate(music_queue))
        await ctx.send(f"📜 **Fila de músicas:**\n{queue_list}")
    else:
        await ctx.send("📭 A fila está vazia!")

# Comando para pular a música atual
@bot.command()
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏭️ Música pulada!")
        await check_queue(ctx)
    else:
        await ctx.send("❌ Nenhuma música está tocando no momento.")

# Comando para pausar a música
@bot.command()
async def pause(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("⏸️ Música pausada!")
    else:
        await ctx.send("❌ Nenhuma música está tocando para ser pausada.")

# Comando para resumir a música pausada
@bot.command()
async def resume(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("▶️ Música retomada!")
    else:
        await ctx.send("❌ Não há música pausada para retomar.")

# Comando para limpar a fila
@bot.command()
async def clear_queue(ctx):
    global music_queue
    music_queue.clear()
    await ctx.send("🗑️ Fila de músicas limpa!")

# Comando para desconectar do canal de voz
@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Desconectado do canal de voz.")
    else:
        await ctx.send("❌ Não estou em um canal de voz!")

@bot.event
async def on_ready():
    print(f'✅ {bot.user} está online e pronto para tocar música!')

bot.run(TOKEN)
