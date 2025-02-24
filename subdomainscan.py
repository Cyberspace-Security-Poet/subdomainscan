#!/usr/bin/env Python
# -*- coding: utf-8 -*-

import sys
import asyncio
from aiohttp_socks import ProxyConnector
import traceback
import aiohttp
from aiohttp import ClientTimeout

def update_account_info(file_path, key, new_value):
    """更新账户配置信息"""
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()

        with open(file_path, 'w') as file:
            for line in lines:
                if line.startswith(f"{key}:"):
                    line = f"{key}:{new_value}\n"
                file.write(line)
    except Exception as e:
        print(f"Error updating {key} in file: {e}")

def modify_account_info(file_path):
    """修改账户信息"""
    update_account_info(file_path, 'username', input("请输入你的快代理账号: "))
    update_account_info(file_path, 'password', input("请输入你的快代理密码: "))
    update_account_info(file_path, 'host', input("请输入你的快代理HOST: "))
    update_account_info(file_path, 'http_port', input("请输入你的HTTP端口: "))
    print("Configuration updated successfully.")

def get_agent(file_path):
    """读取代理配置文件并返回代理信息"""
    config = {}
    try:
        with open(file_path, 'r') as file:
            for line in file:
                line = line.strip()
                if line:
                    key_value = line.split(':', 1)
                    if len(key_value) == 2:
                        config[key_value[0]] = key_value[1]

        # 获取代理选择
        option = input("请输入选项对应的数字:\n不使用代理\t1\n使用HTTP端口获取代理\t2\n")
        if option not in ['1', '2']:
            print("请输入正确的选项!")
            return None

        # 根据选项构建代理
        if option == "1":
            return None  # 不使用代理
        else:
            username = config.get('username')
            password = config.get('password')
            host = config.get('host')
            protocol = "http"
            port = config.get('http_port' if option == "2" else None)
            if not port:
                print(f"未配置 {protocol} 端口")
                return None
            tunnel = f"{host}:{port}"

        proxies = {
            "http": f"{protocol}://{username}:{password}@{tunnel}/",
            "https": f"{protocol}://{username}:{password}@{tunnel}/"
        }
        return proxies
    except Exception as e:
        print(f"Error reading agent file: {e}")
        return None


async def check_subdomain(session, domain_name, sub, proxy_http, proxy_https, counter):
    """检查子域名是否存在"""
    timeout = ClientTimeout(connect=5, total=10)
    url1 = f"http://{sub}.{domain_name}"
    url2 = f"https://{sub}.{domain_name}"

    # 尝试 HTTP 请求
    http_success = False
    try:
        async with session.get(url1, proxy=proxy_http, allow_redirects=False, timeout=timeout) as response:
            counter['checked'] += 1
            if response.status == 200:
                print("[+] Found:" + "http://" + f"{sub}.{domain_name}")
                counter['found'] += 1
                http_success = True
                counter['http_geted so https_passed'] += 1
            else:
                print("[-] " + "http://" + f"{sub}.{domain_name} returned status code: {response.status}")
                counter['notFound'] += 1
    except Exception as e:
        counter['checked'] += 1
        counter['errors'] += 1
        print(f"[!] Error checking {sub}.{domain_name} via HTTP: {e}")
        # traceback.print_exc()

    # 如果 HTTP 检查成功，可以跳过 HTTPS 请求
    if not http_success:
        try:
            async with session.get(url2, proxy=proxy_https, allow_redirects=False, timeout=timeout) as response:
                counter['checked'] += 1
                if response.status == 200:
                    print("[+] Found:" + "https://" + f"{sub}.{domain_name}")
                    counter['found'] += 1
                else:
                    print("[-] " + "https://" + f"{sub}.{domain_name} returned status code: {response.status}")
                    counter['notFound'] += 1
        except Exception as e:
            counter['checked'] += 1
            counter['errors'] += 1
            print(f"[!] Error checking {sub}.{domain_name} via HTTPS: {e}")
            # traceback.print_exc()


async def scan_subdomains(sub_dom, domain_name, proxy_http, proxy_https):
    """扫描所有子域名并计数"""
    counter = {'total': len(sub_dom), 'found': 0, 'checked': 0, 'errors': 0,'notFound': 0,'http_geted so https_passed': 0}
    async with aiohttp.ClientSession() as session:
        tasks = [check_subdomain(session, domain_name, sub, proxy_http, proxy_https, counter) for sub in sub_dom]
        await asyncio.gather(*tasks)

    # 扫描完成后输出结果
    print(f"\nScanning completed\n your dictionary lines: {counter['total']} ")
    print("*****Because both http:// and https:// are used to request subdomains*****,\n",
          "*****6、total checked is twice the number of your dictionary lines.*****")
    print(f"1、{counter['found']} subdomains found.")
    print(f"2、{counter['checked']} subdomains checked")
    print(f"3、{counter['errors']} errors encountered during the scan.such as 'Connection timeout to this subdomain' or 'Host DNS Failed'")
    print(f"4、{counter['notFound']} subdomains notFound.")
    print(f"5、{counter['http_geted so https_passed']} http_geted so https_passed")
    print(f"6、total checked: {int(counter['http_geted so https_passed'])} + {int(counter['checked'])} = {int(counter['http_geted so https_passed']) + int(counter['checked'])}")


def load_subdomains(file_path):
    """加载子域名列表"""
    try:
        with open(file_path) as file:
            sub_name = file.read()
            return sub_name.splitlines()
    except Exception as e:
        print(f"Error loading subdomains from file: {e}")
        return []

if __name__ == '__main__':
    """Windows 平台使用 SelectorEventLoop"""
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    file_path = '快代理账户信息.txt'
    choice = input("Do you need to change your account information? Please enter: y or n\n")

    if choice == "y":
        modify_account_info(file_path)

    subdomains = load_subdomains("dictionary.txt")
    if subdomains:
        domain_name = input("Enter the domain name: ")
        proxies = get_agent(file_path)

        if proxies:
            asyncio.run(scan_subdomains(subdomains, domain_name, proxies.get('http'), proxies.get('https')))
        else:
            print("代理设置无效，退出程序")
    else:
        print("无法加载子域名，退出程序")
