---
title: 博客已完全开源欢迎修改和添加你的故事！
date: 2022-01-16 14:48:49
tags:
- github
- open source
- tutorial
- hexo
- 教程
---

# Welcome to my blog
Hello, I'm p1slave and this is my personal blog to document my fetish life online and I do not wish to reveal my identity on the internet. I have been using VPN and proxy to hide my traces even with fake names when browsing the websites and pushing my commits here. Please don't try to figure out who I am but you are welcome to share your stories with the rest of the world freely by sending pull requests to this repo [p1slave/blog](https://github.com/p1slave/blog) or even start your own blog. 

Note that your story will be added to my blog immediately once your PR is merged into the master branch if you follow the instruction to make contribution to my repo. If you see typos and errors in the existing posts and blog, feel free to send PR to correct them too. The pen sign on the upper right corner of each blog post is the editing link of that post on Github so you can directly make changes on Github rather than clone the repo locally. 

I hope you can publish your fetish stories here because eventually I will build a fetish forum exclusively for the lovely kinksters I love to hear from and I will automate the migration of your blog posts to the new website so you don't have to copy and paste your stories one by one to a new place. 

## Git config for your alt life
 I want to make my repo public so everyone can fork my repo and add their own stories to my blog. Therefore, I have to be extra cautious about my privacy and I cannot use the same username and email from my normal life because my alt life will shock many people in my real life. The following commands will change your contact info globally if you are working on a complete new laptop or VM for your alt life blog writing.
```
git config --global user.name "p1slave"
git config --global user.email "yourname@yourmail.com"
```

However, I don't want to switch machines and choose to set my alt life username and email specifically only for this repo so I put the git configuration file in `/git-config/config` and I can just replace `/.git/cofig` with this file to avoid the horrible accident when I use my alt life username and push commits to my daily work repo. The other tricky thing is that this blog is hosted under a different GitHub account with different SSH keys but Windows may still use the default `id_rsa` private key and fail to authenticate.

A workaround to solve this issue is to add the following one line `sshCommand = ssh -i ~/.ssh/id_ed25519_xxx` to the git configuration file so now we specify which key we want to use instead of the default key.

The complete git configuration is below:
```
[core]
        repositoryformatversion = 0
        filemode = false
        bare = false
        logallrefupdates = true
        symlinks = false
        ignorecase = true
        sshCommand = ssh -i ~/.ssh/id_ed25519_xxx
[user]
        name = p1slave
        email = xxx@yourmail.com
[remote "origin"]
        url = git@github.com:p1slave/blog.git
        fetch = +refs/heads/*:refs/remotes/origin/*
[branch "master"]
        remote = origin
        merge = refs/heads/master
```

What if we want to clone the repository for the first time? The solution is to add the same `sshCommand` as parameter when cloning the repository. The complete clone command will be:
```
git clone git@github.com:p1slave/blog.git --config core.sshCommand="ssh -i ~/.ssh/id_ed25519_xxx"
```

## Installation and testing
Install all dependencies in `package.json`:
```bash
npm install
```
Install the Hexo command line tools from [https://hexo.io](https://hexo.io)
```bash
npm install hexo-cli -g
```

Run Hexo blog locally with commands:
```bash
# Run in linux or MacOS environment and add `npx` before your commands in Windows
hexo server # or `hexo s`
```

Generate a new post if you have a new story to share. The post title should start with `mentee-contribution-` and please follow the naming convention of my other blog posts for the rest of your post title. The Chinese version of your post title should start with `同好XXX投稿 - 你的文章标题` to be consistent. After the execution of this command, a new Markdown post file will be created in `_posts` folder and inside `_post` folder there is another folder with the exact same name of your post to hold assets. Put your photos and videos in the corresponding folder and they can be accessed directly in your post without specifying the relative path.
```bash
# Here is a good example for naming
hexo new post mentee-contribution-yourname-crushed-under-the-ass-of-some-goddesses 
```

Add the following code block to the end your blog post for showing some multimedia assets. For example, if you have four pictures and choose the third layout to group pictures, you write `{% grouppicture 4-3 %}` followed by `{% asset_img xxx.jpg %}` for each picture you add to the group. No need to specify the path since the photos are put into the asset folder. The complete documentation about how to use tags can be found in [Next theme](https://theme-next.js.org/docs/tag-plugins/group-pictures.html) and the native [Hexo tags](https://hexo.io/docs/tag-plugins). You can easily add and render some Youtube links with `{% youtube xxx_id %}` or even tabs and buttons, etc. There are a lot of good stuff for you to explore if you try to play around with [Hexo plugins](https://hexo.io/plugins/) from the Hexo ecosystem or even you may want to write your plugins at some point.

```bash
{% grouppicture 4-3 %}

{% asset_img 1.jpg %}
{% asset_img 2.jpg %}
{% asset_img 3.jpg %}
{% asset_img 4.jpg %}

{% endgrouppicture %}
```

## Deployment
Currently, I deploy my blog to [Netlify](www.netlify.com) with 100GB for free and actually don't have to do anything for deployment. Every time I push the latest commits to my repo, the webhook will automatically pull the latest commit from master branch to Netlify and build the blog. It's the best solution I found so far and hope I don't have to pay extra money once I have more visitors and traffic over 100GB. 

If your pull request is merged into the master branch but you accidentally commit a photo of you holding your dick and ID card, you are screwed because you cannot reverse the commit without my permission. Send me an Github issue, email or DM immedicately and I will help you to take it down before more people see it. Be careful about the things you want to post online because now anyone can access and analyze the information. Don't tell your friends in your real life about your alt life unless you are ready to take the risk.
