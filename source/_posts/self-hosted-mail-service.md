---
title: 搭建开源邮箱和邮件订阅服务
date: 2022-04-26 03:19:20
tags:
---

第三方的商业付费服务算是彻底让我的心态崩了，不是想着办法要收你钱就是给你设置一个莫名其妙的限制。本来觉得搭建邮箱服务器很麻烦也没太大必要，就使用了欧洲的一个群发邮件的服务提供商，网址是[zoho.eu](zoho.eu)，开始还觉得挺好用的，因为刚开始我的订阅者也不多才20几个。哪知道今天发送邮件让我彻底崩溃了，我把买过视频的人也手动加进了邮件列表加起来差不多有200人左右，发送了一半的时候提醒我邮箱账号被锁死了，所以有很多订阅者是没法收到邮件的。提示的错误原因是发送频率太高还是发的数量太大，这不至于吧，我才发了200多封邮件。总结一下教训就是别人都是靠不住的，必须靠自己才能拜托依赖丰衣足食，能用开源的项目放在自己服务器上就不要用商业服务。

<!-- more -->

简单做了一下调研，我的选择是搭建邮件服务器用[Mailu](mailu.io)，而邮件订阅列表服务使用[listmonk](listmonk.app)

## 搭建Mailu邮件服务器（已放弃）
自己正经搭建邮箱其实并不是一个好的选择，用的话要做好邮件是不是发不出也收不到的心理准备，~~对我来说问题不大，因为我也不是发重要的邮件，而是发一些广告邮件，只要配置得当并且不滥用发邮件的功能，应该是不会被系统识别为垃圾邮件的。~~ 我收回之前说的话，搭建邮箱服务是让人非常头疼的一项任务，特别是你的服务器上同时还搭载了很多其他服务。很多不信这个邪的最后都会经历从入门到放弃这么一个过程。

就算你按照官方教程[Mailu.io](mailu.io)搭建好了也未必就可以使用，你发的邮件很大概率就是会进了垃圾邮件，邮件系统迟早会被现代社会所淘汰，早期的邮件系统协议并未过多考虑垃圾邮件的处理，初衷是任何人都可以向任何其他人发送信息，显然这个模式是无法适应21世纪的。在我看来并不是只要是个人就有说话和他说的话被他人听到的权利，而是应该取决于他的信用（reputation），有些人可能觉得这么说的话是侵犯了言论自由，然而现实世界就是这样运行的，并不是你自己租一台服务器搭个邮件服务就可以随便开始向外疯狂群发邮件。

许多大公司的邮件收件服务根本就直接忽略来自你私人邮件服务器发出的邮件，具体的过滤机制十分复杂，有的是机器学习来判断你是不是垃圾邮件，更狠一点的直接拒绝任何来源不明的邮件服务器，或者以前没遇到过的地址直接不收，这也就是为什么私人搭邮件服务需要自己上传反向DNS。这就好像大家收到来自noreply@p1slave.com的邮件和看到我的名字p1slave觉得比较放心会点开看，要是看到邮件的来源地址是一串数字比如123.45.6.7这样的ip地址就会直接拖进垃圾邮件分类。

## 申请第三方SMTP服务
大多数主流第三方服务也是一如既往的又贵又垃圾，而且都是只提供包月服务，每个月都是20刀起步，可以发10k或者更多的邮件，发送量稍微大一点估计一个月要50刀了，完全没有任何性价比，除非是面对企业级的用户那每个月交个几百块都不算钱。

看到有两个免费plan还不错的，一个是澳大利亚还是新西兰一个小公司叫[SMTP2GO](https://www.smtp2go.com)，能免费一个月发1000封邮件，不过好像每天只能发50还是200，升级一下能去除发送限制，一个月10刀也不是太贵，好处是验证很宽松和界面简单好用，没有其他多余功能。另外一个是[SendPulse](https://sendpulse.com)，每个月免费的邮件更多有15k，但是验证比较复杂需要公司邮箱而不能是个人邮箱才可以注册。我注册以后申请的时候填p1slave的域名，直接被禁了所有SMTP相关服务，可能是审核员打开网站觉得涉黄吧，所以要申请最好临时搭一个看起来像样点的正经网站，要带有邮件订阅表格。只要审核通过就可以再换其他网站域名和不那么正经的网站应用。SendPulse还支持其他短信，聊天机器人，web push等推送服务，最大的好处是可以按照使用量购买，不一定要包月。

最经济实惠的就是[Amazon Simple Email Service (SES)](https://aws.amazon.com/ses/)了，发1000封才一毛钱，如果从亚马逊EC2服务器发就基本免费了，但是要通过审核非常困难，不通过审核只能在沙箱sandbox里使用一个月发200封邮件，很多时候申请production access都是毫无理由的默认直接发拒信，只有你自己去反复申诉，并在你网站完全合规的情况下，把申请书写的情真意切才有可能通过申请，纯看管理员的心情。申请到的话就爽歪歪了，一个月发个几十万封的邮件都没问题，但是要注意bounce rate太高的话会被取消权限。我们不能去滥用给我们的权利，否则亚马逊是可以检测出你在做有损他reputation（声誉）的事情，因为一个ip地址的邮件经常被识别为垃圾邮件，那么从这个ip发推广邮件的其他用户也会受到影响被识别为垃圾邮件发送者。

下面放个写申请书的范例吧，重点描述你发送量多少，如何收集订阅者，还有用什么管理方式来处理退订的人。最好再模拟一个发送邮件的模板截图后加到附件里，让管理员知道你会发什么样的内容，一定要和提交申请时的网站内容保持一致才有可行度，别让人看出你是挂羊头卖狗肉，如果是企业级用户就如实写自己的商业需求，会比个人用户更容易通过，特别是加了企业邮箱以后。
```
1. How often do I send emails?
I have new blog posts about twice a month and sometimes one post every two or three months so I estimate I will send out a couple hundreds of marketing and transactional emails each month.
 
2. How do you maintain your recipient lists?
My mailing list will be maintained by Listmonk and the emails will be only sent to the subscribers with double opt-in confirmation so there will be no bounces unless they deactivate their email addresses.

3. How do you manage bounces, complaints, and unsubscribe requests?
I can always see the bounces from the Listmonk backend and remove them from my list. I believe Listmonk also has the capability to take care of the bounces automatically too. 
If the subscriber decides to opt out, they always have the choice to unsubscribe by clicking the unsubscribe link in the Listmonk template in every email to opt out all future emails. I personally tested out this feature in the testing sandbox environment and it works perfectly well. I always deliver high quality content but no hard feelings if someone decides to unsubscribe from my website.

I've also attached a screenshot of the email example and hope it helps to understand better about how I manage the mailing list and what type of content I want to publish. Let me know if you need more information to approve my request. Thanks!
```

最终我们会创建和拿到一个SMTP服务的用户名和密码，并且因为之前已经和域名绑定了，所以以后发出去的邮件都是跟着自己的域名比如`norepy@p1slave.com`，我们需要把这个用户名和密码保存好，之后要填写到Listmonk里面使用。

## 搭建Listmonk邮件订阅服务
在工作目录下放`docker-compose.yml`文件和另外一个`config.toml`文件，`config.toml`后面会被复制到container里面。运行docker的时候需要在`.env`里面设置四个环境变量用于读取用户名和密码。前两个是app访问数据库需要的用户名密码，而后两个是你自己登入网页后台需要的用户名密码。

```bash
POSTGRES_PASSWORD=xxxxxx
POSTGRES_USER=xxxxxx
LISTMONK_app__admin_username=xxxxxxxxxx
LISTMONK_app__admin_password=xxxxxxxxxx
```

docker-compose文件如下：
```yml
# NOTE: This docker-compose.yml is meant to be just an example guideline
# on how you can achieve the same. It is not intented to run out of the box
# and you must edit the below configurations to suit your needs.
version: "3.7"

services:
  listmonk_db:
    container_name: listmonk_postgre_db
    image: postgres:13
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_DB=listmonk
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U listmonk"]
      interval: 10s
      timeout: 5s
      retries: 6
    volumes:
      - type: volume
        source: listmonk-data
        target: /var/lib/postgresql/data

  listmonk:
    container_name: listmonk_app
    restart: unless-stopped
    image: listmonk/listmonk:v2.1.0
    ports:
      - "9000:9000"
    environment:
      - TZ=Etc/UTC
      - LISTMONK_app__admin_username=${LISTMONK_app__admin_username}
      - LISTMONK_app__admin_password=${LISTMONK_app__admin_password}
    depends_on:
      - listmonk_db
    volumes:
      - $PWD/listmonk/config.toml:/listmonk/config.toml

networks: 
  default: 
    name: external-self-hosted-net 
    external: true 

volumes:
  listmonk-data:
```

Listmonk配置文件如下：
```shell
[app]
# Interface and port where the app will run its webserver. The default value
# of localhost will only listen to connections from the current machine. To
# listen on all interfaces use '0.0.0.0'. To listen on the default web address
# port, use port 80 (this will require running with elevated permissions).
address = "0.0.0.0:9000"

# BasicAuth authentication for the admin dashboard. This will eventually
# be replaced with a better multi-user, role-based authentication system.
# IMPORTANT: Leave both values empty to disable authentication on admin
# only where an external authentication is already setup.
# They will be overwritten by the environmental variables.
admin_username = "listmonk"
admin_password = "listmonk"

[db]
# Use the name of docker container for listmonk database.
host = "listmonk_postgre_db"
port = 5432
user = "listmonk"
password = "listmonk"
database = "listmonk"
ssl_mode = "disable"
max_open = 25
max_idle = 25
max_lifetime = "300s"
```

## Listmonk安装步骤
* Create a `.env` file and copy the variables from vault
```bash
# Add the following two variables only when you also use Caddy reverse proxy. 
CADDY_CLOUDFLARE_ZONE_DNS_API_TOKEN=token
CADDY_LISTMONK_DOMAIN_URL=listmonk.yoursite.com

POSTGRES_PASSWORD=password
POSTGRES_USER=yourname
LISTMONK_app__admin_username=yourname
LISTMONK_app__admin_password=password
```

* Run the Postgres DB for the first time
```bash
docker-compose up postgre
```

* Run the following command for initialization to set up the DB before starting containers or  
```bash
# (or --upgrade to upgrade an existing DB).
docker-compose run --rm listmonk ./listmonk --install 
```

* Run the containers with environmental variables loaded from `.env`
```bash
# Without caddy as reverse proxy: docker-compose up -d app db
docker-compose --env-file .env up
```

## 使用Listmonk群发邮件
TODO: