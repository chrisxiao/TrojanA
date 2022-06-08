# coding=utf-8
from __future__ import print_function
from __future__ import unicode_literals

import sys

PY3 = True
if sys.version_info.major == 2:
    PY3 = False
    reload(sys)
    sys.setdefaultencoding("utf-8")
    
    from ConfigParser import ConfigParser
    import commands
    from urllib2 import urlopen
else:
    from configparser import ConfigParser
    import subprocess as commands
    from urllib.request import urlopen

import os
import io
import plistlib
import json

import rumps
from genpac import update_gfwlist

CONFIG_TEMPLATE = '''\
[Trojan]
; 一般情况只需填写remote_addr 和 password

; 本地代理地址端口
local_port=1081
; trojan服务器地址(域名)
remote_addr=
; trojan服务器端口
remote_port=443
; trojan服务端配置的密码
password=
; 是否验证ssl证书
ssl.verify=false
ssl.verify_hostname=false
ssl.cert=

[App]
; 本地PAC服务端口
pac_port=1082
'''

APP_MENU = [
    "当前状态:关闭",
    "✅启动",
    None,
    "PAC模式",
    "全局模式",
    None,
    "⚙设置",
    "更新trojan core",
    "从gfwlist更新PAC",
    None,
    "退出",
]

CONFIG_DIR = os.path.join(os.environ.get("HOME", "~"), ".TrojanA")

CONFIG_PATH = os.path.join(CONFIG_DIR, "app.ini")

APP_CONFIG = {}

TROJAN_CONFIG = {}


def plist_write(data, file_name):
    """
    保存plist文件
    """
    if not PY3:
        plistlib.writePlist(data, file_name)
        return
    with open(file_name, "wb") as f:
        plistlib.dump(data, f)


def file_read(file_name):
    """
    读取文件内容
    """
    with io.open(file_name, encoding="utf-8") as f:
        return f.read()


def file_write(data, file_name):
    """
    将数据写入文件
    """
    with io.open(file_name, mode="w", encoding="utf-8") as f:
        f.write(data)


def gen_http_plist():
    """
    生成http服务启动plist配置文件
    """

    home_dir = os.environ.get("HOME", "~")
    http_plist = "com.chrisxiao.trojana.http-server.plist"

    sys_python_cmd = "python3"
    if os.system("type {}".format(sys_python_cmd)) != 0:
        sys_python_cmd = "python"

    data = {
        'RunAtLoad': True,
        'WorkingDirectory': os.path.join(CONFIG_DIR, "pac"),
        'StandardOutPath': os.path.join(home_dir, 'Library/Logs/trojana-http.log'),
        'Label': 'com.chrisxiao.trojana.http-server',
        'ProgramArguments': [sys_python_cmd, os.path.abspath('./httpserver.py'), APP_CONFIG.get("pac_port", "1082")],
        'KeepAlive': True,
        'StandardErrorPath': os.path.join(home_dir, 'Library/Logs/trojana-http.log')
    }

    # print data
    plist_file = os.path.join(home_dir, "Library/LaunchAgents", http_plist)

    # print plist_file
    plist_write(data, plist_file)


def gen_trojan_plist():
    """
    生成trojan启动配置plist文件
    """

    home_dir = os.environ.get("HOME", "~")
    trojan_plist = "com.chrisxiao.trojana.trojan-client.plist"

    data = {
        'RunAtLoad': True,
        'WorkingDirectory': os.path.abspath("./trojan"),
        'StandardOutPath': os.path.join(home_dir, 'Library/Logs/trojana-client.log'),
        'Label': 'com.chrisxiao.trojana.trojan-client',
        'ProgramArguments': ['./trojan', '-c', os.path.join(CONFIG_DIR, 'config.json')],
        'KeepAlive': True,
        'StandardErrorPath': os.path.join(home_dir, 'Library/Logs/trojana-client.log')
    }

    # print data
    plist_file = os.path.join(home_dir, "Library/LaunchAgents", trojan_plist)

    # print plist_file
    plist_write(data, plist_file)


def init_config():
    """
    配置初始化
    """

    conf_dir = os.path.dirname(CONFIG_PATH)
    if not os.path.exists(conf_dir):
        os.mkdir(conf_dir)

    pac_dir = os.path.join(conf_dir, "pac")
    if not os.path.exists(pac_dir):
        os.mkdir(pac_dir)

    if not os.path.exists(CONFIG_PATH): 
        file_write(CONFIG_TEMPLATE, CONFIG_PATH)


def load_config():
    """
    load config
    """
    config = ConfigParser()
    with io.open(CONFIG_PATH, encoding="utf-8") as f:
        config.readfp(f)

    APP_CONFIG.update(dict(config.items("App")))
    TROJAN_CONFIG.update(dict(config.items("Trojan")))

    pac_file = os.path.join(CONFIG_DIR, "pac", "gfwlist.js")
    if not os.path.exists(pac_file):
        render_pac("./pac/gfwlist.js.tpl", pac_file)

    trojan_conf = os.path.join(os.path.join(CONFIG_DIR, "config.json"))
    if not os.path.exists(trojan_conf):
        render_trojan_conf("./trojan/config.json.tpl", trojan_conf)


def flush_config(config_string):
    """
    flush config
    """

    config = ConfigParser()
    config.readfp(io.StringIO(config_string))
    APP_CONFIG.update(dict(config.items("App")))
    TROJAN_CONFIG.update(dict(config.items("Trojan")))

    file_write(config_string, CONFIG_PATH)
    print("flush config ok")

    render_pac("./pac/gfwlist.js.tpl", os.path.join(CONFIG_DIR, "pac", "gfwlist.js"))
    render_trojan_conf("./trojan/config.json.tpl", os.path.join(CONFIG_DIR, "config.json"))
    print("rewrite config file ok")


def render_pac(tpl_file, dst_file):
    """
    根据配置信息生成pac文件
    """
    tpl = file_read(tpl_file)
    tpl = tpl.replace("__PROXY_PORT__", TROJAN_CONFIG["local_port"])
    # print tpl
    file_write(tpl, dst_file)


def render_trojan_conf(tpl_file, dst_file):
    """
    根据配置信息生成trojan客户端配置文件
    """
    tpl = file_read(tpl_file)

    tpl = tpl.replace("__LOCAL_PORT__", TROJAN_CONFIG["local_port"])
    tpl = tpl.replace("__REMOTE_ADDR__", TROJAN_CONFIG["remote_addr"])
    tpl = tpl.replace("__REMOTE_PORT__", TROJAN_CONFIG["remote_port"])
    tpl = tpl.replace("__PASSWORD__", TROJAN_CONFIG["password"])
    tpl = tpl.replace("__VERIFY__", TROJAN_CONFIG["ssl.verify"])
    tpl = tpl.replace("__VERIFY_HOSTNAME__", TROJAN_CONFIG["ssl.verify_hostname"])
    tpl = tpl.replace("__CERT__", TROJAN_CONFIG["ssl.cert"])
    # print tpl
    file_write(tpl, dst_file)


def pac_mode_on(pac_url):
    """
    打开pac模式
    """
    print("pac on")
    os.system("networksetup -setautoproxyurl 'Wi-Fi' %s" % pac_url)


def pac_mode_off():
    """
    关闭pac模式
    """
    print("pac off")
    os.system("networksetup -setautoproxystate 'Wi-Fi' 'off'")


def global_mode_on(host, port):
    """
    打开全局代理模式
    """
    print("global on")
    os.system("networksetup -setsocksfirewallproxy 'Wi-Fi' %s %s" % (host, port))


def global_mode_off():
    """
    关闭全局代理模式
    """
    print("global off")
    os.system("networksetup -setsocksfirewallproxystate 'Wi-Fi' off")


def start_trojan():
    """
    启动本地trojan服务
    """
    home_dir = os.environ.get("HOME", "~")
    trojan_plist = "com.chrisxiao.trojana.trojan-client.plist"
    plist_file = os.path.join(home_dir, "Library/LaunchAgents", trojan_plist)

    print("trojan started")
    print(os.system("launchctl load " + plist_file))


def stop_trojan():
    """
    关闭本地trojan服务
    """
    home_dir = os.environ.get("HOME", "~")
    trojan_plist = "com.chrisxiao.trojana.trojan-client.plist"
    plist_file = os.path.join(home_dir, "Library/LaunchAgents", trojan_plist)

    print("trojan stop")
    print(os.system("launchctl unload " + plist_file))


def start_pac_server():
    """
    启动本地pac文件http服务
    """
    home_dir = os.environ.get("HOME", "~")
    http_plist = "com.chrisxiao.trojana.http-server.plist"
    plist_file = os.path.join(home_dir, "Library/LaunchAgents", http_plist)

    print("pac server started")
    print(os.system("launchctl load " + plist_file))


def stop_pac_server():
    """
    关闭本地pac文件http服务
    """
    home_dir = os.environ.get("HOME", "~")
    http_plist = "com.chrisxiao.trojana.http-server.plist"
    plist_file = os.path.join(home_dir, "Library/LaunchAgents", http_plist)

    print("pac server stop")
    print(os.system("launchctl unload " + plist_file))


def get_cur_trojan_ver():
    """
    获取当前trojan版本
    """
    ver = commands.getoutput("./trojan/trojan --version").splitlines()[0].split()[-1]
    return ver


def get_latest_trojan():
    """
    获取最新trojan版本信息
    """

    r = urlopen("https://api.github.com/repos/trojan-gfw/trojan/releases/latest", timeout=10)
    res_json = json.loads(r.read())

    release_ver = res_json["name"].split()[-1]
    download_url = [i["browser_download_url"] for i in res_json["assets"] if i["browser_download_url"].find("macos") > 0]

    return release_ver, download_url


def do_update_trojan():
    """
    检查并更新trojan版本
    """
    now_ver = get_cur_trojan_ver()
    try:
        latest_info = get_latest_trojan()
    except Exception as e:
        print(e)
        return False, "无法获取最新版本信息！"

    if now_ver >= latest_info[0]:
        return False, "已是最新版本，无需更新！"

    print("start downloading new")
    url = latest_info[1][0]
    target = "./download/" + os.path.basename(latest_info[1][0])
    print(target)

    ret = os.system("curl --connect-timeout 10 --max-time 60 -L %s --output %s" % (url, target))
    if ret != 0:
        return False, "无法下载最新版本"
    os.system("unzip -u %s -d ./download/tmp" % target)
    os.system("rm -f ./trojan/trojan")
    os.system("cp ./download/tmp/trojan/trojan ./trojan/trojan")
    os.system("rm -rf ./download/tmp")
    os.system("rm -f %s" % target)

    print("update finished")

    return True, "已是最新版本，无需更新！"




class AwesomeStatusBarApp(rumps.App):

    pac_item = None
    global_item = None
    status_item = None
    config_window = rumps.Window("",
                                 title="基本配置",
                                 default_text=CONFIG_TEMPLATE,
                                 ok="确定",
                                 cancel="取消",
                                 dimensions=(480, 320)
                                )
    pac_url = "http://127.0.0.1:%s/gfwlist.js"

    def initialize(self):
        """
        初始化
        """
        self.pac_item = self.menu["PAC模式"]
        self.pac_item.state = True
        self.global_item = self.menu["全局模式"]
        self.global_item.state = False

        # start_trojan()
        start_pac_server()
        self.pac_url = self.pac_url % APP_CONFIG["pac_port"]
        # pac_mode_on(self.pac_url)


    @rumps.clicked("✅启动")
    def onoff(self, sender):
        if not self.status_item:
            self.status_item = self._menu["当前状态:关闭"]

        self.status_item.title = "当前状态:启动"

        sender.title = "❌关闭" if sender.title == "✅启动" else "✅启动"
        self.status_item.title = "当前状态:关闭" if sender.title == "✅启动" else "当前状态:开启"

        if self.status_item.title == "当前状态:关闭":
            stop_trojan()
            global_mode_off()
            pac_mode_off()
        else:
            start_trojan()
            if self.pac_item.state:
                global_mode_off()
                pac_mode_on(self.pac_url)
            else:
                pac_mode_off()
                global_mode_on("127.0.0.1", TROJAN_CONFIG["local_port"])


        rumps.alert(self.status_item.title)


    @rumps.clicked("⚙设置")
    def settings(self, _):
        self.config_window.default_text = file_read(CONFIG_PATH)
        res = self.config_window.run()
        if res.clicked:
            print(res.clicked)
            # print res.text
            flush_config(res.text)


    @rumps.clicked("PAC模式")
    def pac_mode(self, sender):
        sender.state = True
        self.global_item.state = False
        # 关闭全局代理
        global_mode_off()
        # 打开pac模式
        pac_mode_on(self.pac_url)


    @rumps.clicked("全局模式")
    def global_mode(self, sender):
        sender.state = True
        self.pac_item.state = False
        # 关闭pac模式
        pac_mode_off()
        # 打开全局模式
        global_mode_on("127.0.0.1", TROJAN_CONFIG["local_port"])


    @rumps.clicked("更新trojan core")
    def update_trojan_client(self, sender):
        result, message = do_update_trojan()
        if result:
            if hasattr(self.status_item, "title") and self.status_item.title == "当前状态:开启":
                stop_trojan()
                start_trojan()
        rumps.alert(message)


    @rumps.clicked("从gfwlist更新PAC")
    def update_pac(self, sender):
        if update_gfwlist(os.path.join(CONFIG_DIR, "pac", "gfwlist.js"), TROJAN_CONFIG["local_port"]):
            rumps.alert("更新成功!")
        else:
            rumps.alert("已是最新版本，无需更新！")


    @rumps.clicked("退出")
    def quit(self, _):
        global_mode_off()
        pac_mode_off()
        stop_pac_server()
        stop_trojan()
        rumps.quit_application()


if __name__ == "__main__":

    init_config()
    load_config()
    gen_http_plist()
    gen_trojan_plist()

    app = AwesomeStatusBarApp("🐴", menu=APP_MENU, quit_button=None)
    app.initialize()
    app.run()
