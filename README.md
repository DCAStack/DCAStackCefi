# Welcome to DCA Stack!
## An Automated Dollar Cost Averaging Bot For Your Crypto

**Website: https://www.dcastack.com/**

**Full Docs: https://docs.dcastack.com/**

**Support Us: https://www.dcastack.com/donate/**


This github repo was made in the spirit of **Don't Trust, Verify**. I totally understand the hesitation of using web apps created by strangers on the internet. Especially when it comes to sensitive information like API keys and your crypto. So to help foster trust and gather early user feedback, I'm releasing the source code that directly builds the production environment. 

## Note on Public Alpha

This is a super early preview of DCA Stack. What this means for you, the user, is that there are bugs! What I'm hoping is that with community testing that we can squash these bugs and create a super robust DCA service. Keeping in mind that this is just an alpha release, please only keep funds necessary to faciliate order trading. This will mitigate the risk of using this early release of DCA stack.

If you find any bugs, please feel free to open an issue and include as much detail as possible!

## How can I verify that your website is running the code on the repo and not something malicious?

Excellent question and totally valid concern. We can verify this directly from github!

Simple answer: On the right hand side of the screen (or left), there will be a section called Environments. Click on it. You'll see a button called View Deployment. Click on that and that'll take you to the website that this repo builds. The exact code you see on the repo is what is contained in the deployment since it is an automated process. 

Better answer: The way this repo is configured is that whenever the main branch receives a new commit, it will trigger an automated workflow. This workflow will rebuild the repo and automatically deploy the code to the server. So the code you see in the repo is the exact same code that is being served by the server since it is a complete automated process Github offers it's users (along with heroku). 

You will notice that this takes you to dcastack.herokuapp.com which is the direct connection to the heroku platform on which this entire website is hosted. This is the exact same as the dcastack.com domain. The only difference is the fact that dcastack.com is more convenient for SEO, spreading the word and enhanced with cloudflare.
