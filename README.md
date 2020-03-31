# TrojanA
a tiny client for trojan on Mac

一个极简版trojan客户端，只可运行在Mac上（macOS 10.14.5版本测试通过，其他版本未测试）。

## 主要特性：

- 完全使用Python编写，使用了[rumps](https://github.com/jaredks/rumps)框架，通过[py2app](https://pypi.org/project/py2app/)构建
- 基于状态栏的App
- 支持PAC及全局代理切换

## 安装：

在这里[下载](https://github.com/chrisxiao/TrojanA/releases)，选择最新版本下载，解压后，移入应用程序目录即可

## 运行：

与普通App一样，运行后状态栏会出现“🐴”图标，说明运行成功。

初次运行后，需要进入“设置”，填写相关服务端配置。确定后，点“开启”即可。

## 内部机制：

- 使用trojan传输数据
- 使用networksetup命令配置系统代理
- 使用Python SimpleHTTPServer模块构建PAC文件HTTP服务
- 使用launchctl管理服务的启动及停止
- 使用rumps框架包装界面

同样的功能也可通过Python+Shell来完成，GUI界面只是为了方便使用。

## 问题反馈：

可以提在Issues中。





