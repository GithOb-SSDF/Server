#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import socket
import struct
import threading
import time
import random
import string
import re

try:
    from colorama import init, Fore, Back, Style
    init(autoreset=True)
except ImportError:
    class Fore:
        RED = '\033[91m'; GREEN = '\033[92m'; YELLOW = '\033[93m'
        BLUE = '\033[94m'; MAGENTA = '\033[95m'; CYAN = '\033[96m'
        WHITE = '\033[97m'; RESET = '\033[0m'
    class Style:
        BRIGHT = '\033[1m'; RESET_ALL = '\033[0m'

os.system('clear' if os.name == 'posix' else 'cls')

BANNER = f"""
{Fore.RED}╔══════════════════════════════════════════════════════════════════════════╗
{Fore.RED}║  {Fore.CYAN}██████╗  ██████╗ ████████╗    ██████╗  ██████╗ ████████╗{Fore.RED}    ║
{Fore.RED}║  {Fore.CYAN}██╔══██╗██╔═══██╗╚══██╔══╝    ██╔══██╗██╔═══██╗╚══██╔══╝{Fore.RED}    ║
{Fore.RED}║  {Fore.CYAN}██████╔╝██║   ██║   ██║       ██████╔╝██║   ██║   ██║   {Fore.RED}    ║
{Fore.RED}║  {Fore.CYAN}██╔══██╗██║   ██║   ██║       ██╔══██╗██║   ██║   ██║   {Fore.RED}    ║
{Fore.RED}║  {Fore.CYAN}██████╔╝╚██████╔╝   ██║       ██████╔╝╚██████╔╝   ██║   {Fore.RED}    ║
{Fore.RED}║  {Fore.CYAN}╚═════╝  ╚═════╝    ╚═╝       ╚═════╝  ╚═════╝    ╚═╝   {Fore.RED}    ║
{Fore.RED}║  {Fore.YELLOW}════════════════════════════════════════════════════════════════════{Fore.RED} ║
{Fore.RED}║  {Fore.GREEN}║  🤖 MCBOT v6.5 - FIX CHAT & API (v0.14.x / v0.15.x)            ║ {Fore.RED}║
{Fore.RED}║  {Fore.GREEN}║  📡 OPTIMIZADO PARA PROTOCOLOS ANTIGUOS PMMP 2.x               ║ {Fore.RED}║
{Fore.RED}║  {Fore.GREEN}║  💬 CHAT EN TIEMPO REAL FIJADO Y PARSEO DE COMANDOS           ║ {Fore.RED}║
{Fore.RED}║  {Fore.GREEN}╚══════════════════════════════════════════════════════════════════╝ {Fore.RED}║
{Fore.RED}╚══════════════════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
"""

print(BANNER)

def generar_nombre():
    nombres = ['Bot', 'Old', 'Retro', 'Pepe', 'Juan', 'Luis', 'Ana', 'Carlos', 'Pedro']
    return random.choice(nombres) + ''.join(random.choices(string.digits, k=3))

class Bot:
    def __init__(self, ip, puerto, nombre, password):
        self.ip = ip
        self.puerto = puerto
        self.nombre = nombre
        self.password = password
        self.socket = None
        self.conectado = False
        self.running = True
        self.registrado = False
        self.id_cliente = random.randint(0, 2**64-1)
        self.jugadores = []
        self.jugadores_count = "?"
        self.max_jugadores = "?"
        self.server_online = False
        self.motd = "Desconocido"
        self.version = "Desconocida"
        self.api = "PMMP (Antiguo)"
        self.api_detectada = False
        self.play_activo = True  # Activado por defecto para ver alertas
        
        self.MAGIC = b'\x00\xff\xff\x00\xfe\xfe\xfe\xfe\xfd\xfd\xfd\xfd\x12\x34\x56\x78'
        
        # ID de Paquetes válidos para v0.14/v0.15
        self.ID_LOGIN = 0x01
        self.ID_PLAY_STATUS = 0x02
        self.ID_TEXT = 0x09
        self.ID_MOVE_PLAYER = 0x13
        self.ID_DISCONNECT = 0x05
        self.ID_RESOURCE_PACKS_CLIENT_RESPONSE = 0x08
    
    def detectar_api_desde_texto(self, msg):
        msg_lower = msg.lower()
        apis = {
            'pocketmine': 'PocketMine-MP',
            'pmmp': 'PocketMine-MP',
            'genisys': 'Genisys',
            'clear sky': 'ClearSky',
            'nukkit': 'Nukkit'
        }
        
        for key, value in apis.items():
            if key in msg_lower:
                self.api = value
                self.api_detectada = True
                return True
        return False
    
    def obtener_info_ping(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(2)
            
            ping = bytearray()
            ping.extend(b'\x01')
            ping.extend(struct.pack('>Q', int(time.time())))
            ping.extend(self.MAGIC)
            ping.extend(b'\x00' * 8)
            
            sock.sendto(bytes(ping), (self.ip, self.puerto))
            data, addr = sock.recvfrom(2048)
            sock.close()
            
            if len(data) > 0:
                self.server_online = True
                offset = 1 + 8 + 16 # ID + Time + Magic
                info_bytes = data[offset:]
                info_str = info_bytes.decode('utf-8', errors='ignore')
                campos = info_str.split(';')
                
                if len(campos) >= 6:
                    self.motd = campos[1] if len(campos) > 1 else "Desconocido"
                    self.version = campos[3] if len(campos) > 3 else "Desconocida"
                    self.jugadores_count = campos[4] if len(campos) > 4 else "?"
                    self.max_jugadores = campos[5] if len(campos) > 5 else "?"
                    
                    # Forzar detección basada en protocolo heredado
                    if "0.14" in self.version or "0.15" in self.version:
                        self.api = f"PMMP 2.x (PocketMine-MP {self.version})"
                    else:
                        self.api = f"PocketMine-MP {self.version}"
                    self.api_detectada = True
                    return True
            return False
        except:
            self.server_online = False
            return False
    
    def mostrar_info(self):
        estado = f"{Fore.GREEN}ONLINE{Fore.RESET}" if self.server_online else f"{Fore.RED}OFFLINE{Fore.RESET}"
        print(f"\n{Fore.CYAN}╔═══════════════════════════════════════════════════════════════════════╗")
        print(f"{Fore.CYAN}║{Fore.WHITE}                    SERVER INFORMATION                        {Fore.CYAN}║")
        print(f"{Fore.CYAN}╠═══════════════════════════════════════════════════════════════════════╣")
        print(f"{Fore.CYAN}║{Fore.GREEN}  ✅ Estado: {estado:<55}{Fore.CYAN}║")
        print(f"{Fore.CYAN}║{Fore.GREEN}  ✅ IP: {self.ip:<55}{Fore.CYAN}║")
        print(f"{Fore.CYAN}║{Fore.GREEN}  ✅ Puerto: {self.puerto:<51}{Fore.CYAN}║")
        print(f"{Fore.CYAN}║{Fore.GREEN}  ✅ MOTD: {self.motd[:50]:<53}{Fore.CYAN}║")
        print(f"{Fore.CYAN}║{Fore.GREEN}  ✅ Versión: {self.version:<49}{Fore.CYAN}║")
        print(f"{Fore.CYAN}║{Fore.YELLOW}  👥 Jugadores: {self.jugadores_count:<3}/{self.max_jugadores:<3}{' ' * 47}{Fore.CYAN}║")
        print(f"{Fore.CYAN}║{Fore.MAGENTA}  📡 API: {self.api:<54}{Fore.CYAN}║")
        print(f"{Fore.CYAN}╚═══════════════════════════════════════════════════════════════════════╝{Fore.RESET}\n")
    
    def conectar(self):
        try:
            print(f"{Fore.CYAN}[🔍]{Fore.RESET} Obteniendo info del servidor...")
            self.obtener_info_ping()
            self.mostrar_info()
            
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.settimeout(5)
            
            # Enviar paquete de conexión inicial de RakNet
            ping = bytearray()
            ping.extend(b'\x01')
            ping.extend(struct.pack('>Q', int(time.time())))
            ping.extend(self.MAGIC)
            ping.extend(b'\x00' * 8)
            
            self.socket.sendto(bytes(ping), (self.ip, self.puerto))
            
            try:
                data, addr = self.socket.recvfrom(2048)
                if len(data) > 0:
                    print(f"{Fore.GREEN}[✅]{Fore.RESET} ¡El servidor respondió al handshake!")
                    self._enviar_login()
                    return True
            except socket.timeout:
                print(f"{Fore.YELLOW}[⚠️]{Fore.RESET} Timeout en handshake, reintentando de forma directa...")
                self._enviar_login()
                return True
            
            return False
        except Exception as e:
            print(f"{Fore.RED}[❌]{Fore.RESET} Error en conexión: {e}")
            return False
    
    def _enviar_login(self):
        packet = bytearray()
        packet.append(self.ID_LOGIN)
        
        data = bytearray()
        # Protocolo para v0.14.x / v0.15.x (Suele rondar entre el 45 y el 70)
        data.extend(struct.pack('>I', 70)) 
        data.extend(struct.pack('>I', 0))
        
        nombre_bytes = self.nombre.encode('utf-8')
        data.extend(struct.pack('>H', len(nombre_bytes)))
        data.extend(nombre_bytes)
        
        data.extend(b'\x00' * 8)
        data.extend(struct.pack('>Q', self.id_cliente))
        data.extend(b'\x00' * 64)
        data.extend(b'\x00')
        
        packet.extend(struct.pack('>I', len(data)))
        packet.extend(data)
        
        self.socket.sendto(bytes(packet), (self.ip, self.puerto))
        print(f"{Fore.CYAN}[🔑]{Fore.RESET} Autenticando protocolo antiguo como {Fore.GREEN}{self.nombre}{Fore.RESET}")
        
        time.sleep(0.5)
        self._responder_resource_packs()
    
    def _responder_resource_packs(self):
        try:
            packet = bytearray()
            packet.append(self.ID_RESOURCE_PACKS_CLIENT_RESPONSE)
            packet.extend(struct.pack('>B', 3)) # Estado 3 = Ready en versiones retro
            packet.extend(b'\x00' * 4)
            self.socket.sendto(bytes(packet), (self.ip, self.puerto))
        except:
            pass
    
    def enviar_mensaje(self, texto):
        if not self.socket:
            return
        try:
            packet = bytearray()
            packet.append(self.ID_TEXT)
            packet.append(0x01) # Tipo Chat/Texto normal
            
            # En Minecraft antiguo, a veces el emisor va vacío si es mensaje directo
            packet.extend(struct.pack('>H', 0)) 
            
            msg = texto.encode('utf-8')
            packet.extend(struct.pack('>H', len(msg))) # Short en lugar de Int para payloads antiguos
            packet.extend(msg)
            
            self.socket.sendto(bytes(packet), (self.ip, self.puerto))
        except Exception as e:
            pass
    
    def enviar_comando(self, comando):
        self.enviar_mensaje(comando)
    
    def mantener_vivo(self):
        """Manda ticks de movimiento ligeros para que PMMP no asuma AFK/Timeout"""
        if not self.socket:
            return
        try:
            packet = bytearray()
            packet.append(self.ID_MOVE_PLAYER)
            packet.extend(struct.pack('>f', 0.0)) # X
            packet.extend(struct.pack('>f', 64.0)) # Y
            packet.extend(struct.pack('>f', 0.0)) # Z
            packet.extend(struct.pack('>f', 0.0)) # Yaw
            packet.extend(struct.pack('>f', 0.0)) # Pitch
            self.socket.sendto(bytes(packet), (self.ip, self.puerto))
        except:
            pass
    
    def escuchar(self):
        ultimo_tick = time.time()
        while self.running:
            try:
                if self.socket:
                    self.socket.settimeout(0.5)
                    try:
                        data, addr = self.socket.recvfrom(65535)
                        if data:
                            self._procesar_paquete(data)
                    except socket.timeout:
                        pass
                    
                    # Keep-alive cada 2 segundos
                    if time.time() - ultimo_tick > 2:
                        self.mantener_vivo()
                        ultimo_tick = time.time()
                else:
                    time.sleep(0.5)
            except Exception as e:
                continue
    
    def _procesar_paquete(self, data):
        try:
            # Desencapsular cabeceras RakNet si vienen empaquetadas (muy común en PMMP antiguo)
            if data[0] >= 0x80 and data[0] <= 0x8d:
                # Es un paquete de datos RakNet encapsulado, saltamos la cabecera básica (aprox 28 bytes o buscamos ID interno)
                payload = data[28:]
                if len(payload) > 0:
                    packet_id = payload[0]
                    self._analizar_id_interno(packet_id, payload)
            else:
                self._analizar_id_interno(data[0], data)
        except:
            pass

    def _analizar_id_interno(self, packet_id, data):
        if packet_id == self.ID_TEXT:
            self._procesar_texto(data)
        elif packet_id == self.ID_PLAY_STATUS:
            self._procesar_status(data)
        elif packet_id == self.ID_DISCONNECT:
            print(f"{Fore.RED}[❌]{Fore.RESET} Desconectado por el servidor remoto.")
            self.running = False
            
    def _procesar_texto(self, data):
        try:
            # En el protocolo viejo, el offset varía según el tipo de mensaje de texto
            tipo = data[1]
            
            # Limpiar strings binarios usando Regex para extraer texto legible
            strings_legibles = re.findall(r'[\x20-\x7E\xC0-\xFF]{2,}', data.decode('utf-8', errors='ignore'))
            
            if not strings_legibles:
                return

            # Si es tipo 1 (Chat con Nombre) o detectamos un formato "jugador: mensaje"
            if len(strings_legibles) >= 2:
                nombre = strings_legibles[0]
                msg = " ".join(strings_legibles[1:])
                # Ignorar nombres que parezcan comandos o logs internos vacíos
                if nombre.strip() and not nombre.startswith('/') and len(nombre) < 20:
                    print(f"{Fore.YELLOW}[💬]{Fore.RESET} {Fore.CYAN}{nombre}{Fore.RESET}: {msg}")
                    self.detectar_api_desde_texto(msg)
                    return
            
            # Mensajes del sistema o Broadcast (Tipo 0 o Raw)
            full_msg = " ".join(strings_legibles)
            if "joined" in full_msg.lower() or "unió" in full_msg.lower():
                print(f"{Fore.GREEN}[➕]{Fore.RESET} {Fore.WHITE}{full_msg}{Fore.RESET}")
            elif "left" in full_msg.lower() or "salió" in full_msg.lower():
                print(f"{Fore.RED}[➖]{Fore.RESET} {Fore.WHITE}{full_msg}{Fore.RESET}")
            else:
                # Imprimir cualquier otro mensaje del chat general del servidor en tiempo real
                print(f"{Fore.MAGENTA}[📡]{Fore.RESET} {Fore.WHITE}{full_msg}{Fore.RESET}")
                
            self.detectar_api_desde_texto(full_msg)
            if "registered" in full_msg.lower() or "registrado" in full_msg.lower():
                self.registrado = True
        except:
            pass
    
    def _procesar_status(self, data):
        try:
            status = struct.unpack('>I', data[1:5])[0] if len(data) >= 5 else data[1]
            if status == 0:
                print(f"{Fore.GREEN}[✅]{Fore.RESET} ¡Conexión Establecida con éxito!")
                self.conectado = True
                # Lanzar comandos de descubrimiento automatizados
                time.sleep(0.5)
                self.enviar_comando("/ver")
                self.enviar_comando("/about")
        except:
            pass
            
    def cerrar(self):
        self.running = False
        if self.socket:
            self.socket.close()
        print(f"{Fore.YELLOW}[🔌]{Fore.RESET} Desconectado de forma segura.")

def main():
    print(f"\n{Fore.YELLOW}══════════════════════════════════════════════════════════════════════════")
    print(f"{Fore.CYAN}     📡 CONFIGURACIÓN RETRO BEDROCK (0.14.x / 0.15.x)")
    print(f"{Fore.YELLOW}══════════════════════════════════════════════════════════════════════════{Fore.RESET}\n")
    
    ip = input(f"{Fore.GREEN}[?]{Fore.RESET} IP o dominio: ").strip()
    if not ip:
        sys.exit(1)
    
    try:
        puerto = int(input(f"{Fore.GREEN}[?]{Fore.RESET} Puerto (por defecto 19132): ").strip())
    except:
        puerto = 19132
    
    nombre = input(f"{Fore.GREEN}[?]{Fore.RESET} Nombre del Bot (ENTER para aleatorio): ").strip()
    if not nombre:
        nombre = generar_nombre()
    
    password = input(f"{Fore.GREEN}[?]{Fore.RESET} Contraseña para Autenticación: ").strip()
    if not password:
        password = "BotPassword123"
        
    bot = Bot(ip, puerto, nombre, password)
    
    if not bot.conectar():
        print(f"{Fore.RED}[❌]{Fore.RESET} No se pudo inicializar el socket.")
        sys.exit(1)
    
    # Iniciar el hilo de escucha asíncrono en segundo plano para el chat en vivo
    hilo = threading.Thread(target=bot.escuchar, daemon=True)
    hilo.start()
    
    # Intentar Auth por comandos tradicionales de PMMP
    time.sleep(1.5)
    bot.enviar_comando(f"/register {password} {password}")
    bot.enviar_comando(f"/login {password}")
    
    print(f"\n{Fore.GREEN}[✅]{Fore.RESET} Escucha en vivo montada para {Fore.CYAN}{bot.api}{Fore.RESET}")
    print(f"{Fore.YELLOW}💬 Escribe texto normal para hablar en el servidor, o comandos de admin directamente.{Fore.RESET}\n")
    
    try:
        while bot.running:
            texto = input()
            if not texto.strip():
                continue
            if texto.lower() == '/exit':
                bot.cerrar()
                break
            if texto.lower() == '/info':
                bot.mostrar_info()
                continue
            bot.enviar_mensaje(texto)
    except KeyboardInterrupt:
        bot.cerrar()

if __name__ == "__main__":
    main()