# Blog

## Installation
I need to hide my own identity in case someone get a copy of this repository so I cannot use the same username and email for my work. The commands below will change the contact info in my repository and I also copy the git configuration file to `/git-config/config` so I can just copy and replace the file in `/.git`. The other tricky part is that this blog is hosted under a different GitHub account with different SSH keys but Windows may still use the default `id_rsa` private key and fail to authenticate.
```
git config --global user.name "p1slave"
git config --global user.email "mykink01@gmail.com"
```

A workaround is to add the following one line to the git configuration file so now we specify which key we want to use instead of the default key.
```
sshCommand = ssh -i ~/.ssh/id_ed25519_p1s
```
The bad news is what if we want to clone the repository for the first time? The solution is to add the same `sshCommand` as parameter when cloning the repository. The complete clone command will be:
```
git clone git@github.com:p1slave/blog.git --config core.sshCommand="ssh -i ~/.ssh/id_ed25519_xxx"
```

## Testing
Run Hexo blog locally with commands:
```bash
# Run in linux or MacOS environment
hexo server
hexo s
# Run in Windows environment
npx hexo server
```

## Deployment
Currently I deploy it on [Netlify](www.netlify.com) and don't have to do anything for deployment. Every time I push the latest commits to this GitHub repository, the webhook will automatically pull the new commit to Netlify and update the blog. It's the best solution I found so far and hope I don't have to pay more once I have more visitors and traffic.
