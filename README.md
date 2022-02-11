# 2022-今日校园自动填报脚本

## 预知

* <font color="red">禁止任何人使用此项目提供付费代挂服务</font>
* <font color="red">本项目只用作辅助今日校园签到，拒绝一切隐瞒实情行为</font>

## 引用

* ZimoLoveShuang：https://github.com/ZimoLoveShuang/auto-submit 代码的主要逻辑

* IceTiki：https://github.com/IceTiki/ruoli-sign-optimization 最新版今日校园的加密方式

## 概述

* 项目整合上述两个项目的代码，以及重新抓包分析。针对今日校园版本9.0.18自动填报功能，其他功能及更详细的说明可参考上面两个链接进行实现。在此感谢两位大神。

## 使用说明

1. 将代码下载到本地

   ``` shell
   git clone https://github.com/iccccch/Auto-Submit.git
   ```

2. 打开本地仓库文件夹，配置`config.yml`中对应的学号（username）和密码（password）还有地址（address）等等信息，详情请看`config.yml`中的注释说明，**注意这里的学号和密码都是智慧校园的学号和密码**

3. 本地运行`login.py`，接收手机验证码输入后，将控制台输出的`sessionToken`和`MOD_AUTH_CAS`填入`index.py`中顶部对应的位置

   > 运行`login.py`另外需要`encrypt.py`, `utils.py`, `config.yml`这两个文件

4. 运行`index.py`即可完成今日校园自动填报

5. 部署到服务器可以使用crontab定时签到，或者部署到云函数进行定时签到。详细步骤请查看 [引用](# 引用) 中两位大佬的详细说明。

   > 部署运行`index.py`另外也需要`encrypt.py`, `utils.py`, `config.yml`这两个文件