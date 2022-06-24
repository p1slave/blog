---
title: Discuz论坛运维学习笔记
tags:
---

## 搭建论坛上线
过程其实非常简单，随便买一台服务器，安装[宝塔面板](https://bt.cn)，然后把Discuz论坛的代码上传到根目录就可以了，甚至都不需要上传直接在“一键部署”里面找到Discuz点一下就生成一个网站

## 管理员运维
这个任务真的非常艰巨，后台有成千上万个选项加上多如牛毛的插件让人眼花缭乱


30上限可在用户组编辑-论坛相关-帖子相关-主题(附件)最高售价

## 搭建Discuz的PHP开发环境

打开`/opt/lampp/etc/httpd.conf`修改文件，取消其中一行注释
```dotnetcli
Include etc/extra/httpd-vhosts.conf
```
然后加上我们自己的子域名和指向的文件夹，在本地要开放PHP对文件夹的所有权限，因此需要修改一个文件在```/opt/lampp/etc/extra/httpd-vhosts.conf```
第一个配置保留默认的localhost根域名，第二个就绑定Discuz的源代码文件夹了，注意文件权限要给Discuz源代码文件夹的上一级，因为后面安装Discuz的时候会在上一级文件夹里写入点东西，否则会报写入错误。
```dotnetcli
<VirtualHost *:80>
	DocumentRoot "/opt/lampp/htdocs/"
	ServerName localhost
</VirtualHost>

<VirtualHost *:80>
	DocumentRoot "/path/to/DiscuzX/upload"
	ServerName discuz.localhost
	<Directory "/path/to/DiscuzX/">
		Allow from all
		AllowOverride All
		Require all granted
		Options Indexes
	</Directory>
</VirtualHost>
```

给Discuz根目录下所有文件夹写权限```sudo chmod 777 /path/DiscuzX/upload -R```，本地开发加上就一个文件夹，不至于会有什么安全问题，除非你想不开又去开了本地的80端口。

重启一下所有服务```sudo /opt/lampp/lampp restart```

我草注意写localhost而不是127.0.0.1否则安装时显示connection refused