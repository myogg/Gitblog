# [Claude Code 團隊展示配置](https://github.com/myogg/Gitblog/issues/184)

tags: Claude Code; X, 

I'm Boris and I created Claude Code. Lots of people have asked how I use Claude Code, so I wanted to show off my setup a bit. My setup might be surprisingly vanilla! Claude Code works great out of the box, so I personally don't customize it much. There is no one correct way to use Claude Code: we intentionally build it in a way that you can use it, customize it, and hack it however you like. Each person on the Claude Code team uses it very differently. So, here goes.

我是Boris，Claude Code是我開發的。很多人問我如何使用Claude Code，所以我想簡單地展示我的配置。

我的配置可能出乎意料地簡單！ Claude Code 開箱即用，效果非常好，所以我個人很少對其進行自訂。使用 Claude Code 沒有唯一正確的方法：我們特意將其設計成可以隨意使用、自訂和修改的。 Claude Code 團隊的每位成員使用它的方式都各不相同。

好了，開始吧。

1/ I run 5 Claudes in parallel in my terminal. I number my tabs 1-5, and use system notifications to know when a Claude needs input 
[](https://code.claude.com/docs/en/terminal-config#iterm-2-system-notifications
)
1/ 我在終端機中並行運行 5 個 Claude 進程。我將標籤頁編號為 1-5，並使用系統通知來了解何時某個 Claude 進程需要輸入

[链接](https://code.claude.com/docs/en/terminal-config#iterm-2-system-notifications)

![1000023799.jpg](https://i.829259.xyz/api/cfile/AgACAgUAAx0ER6IxDQACTm5pXlpWTR2fS5__3Kywfvl6M7HBZgACFA1rG0IO8VY55Fimvg6DBAEAAwIAA3gAAzgE)

2/ I also run 5-10 Claudes on http://claude.ai/code, in parallel with my local Claudes. As I code in my terminal, I will often hand off local sessions to web (using &), or manually kick off sessions in Chrome, and sometimes I will --teleport back and forth. I also start a few sessions from my phone (from the Claude iOS app) every morning and throughout the day, and check in on them later.

![1000023799.jpg](https://i.829259.xyz/api/cfile/AgACAgUAAx0ER6IxDQACTm5pXlpWTR2fS5__3Kywfvl6M7HBZgACFA1rG0IO8VY55Fimvg6DBAEAAwIAA3gAAzgE)

3/ I use Opus 4.5 with thinking for everything. It's the best coding model I've ever used, and even though it's bigger & slower than Sonnet, since you have to steer it less and it's better at tool use, it is almost always faster than using a smaller model in the end.

4/ Our team shares a single http://CLAUDE.md for the Claude Code repo. We check it into git, and the whole team contributes multiple times a week. Anytime we see Claude do something incorrectly we add it to the http://CLAUDE.md, so Claude knows not to do it next time.

Other teams maintain their own http://CLAUDE.md's. It is each team's job to keep theirs up to date.

![1000023800.jpg](https://i.829259.xyz/api/cfile/AgACAgUAAx0ER6IxDQACTm9pXlz_qNHTgJgeVeISamYkEAfmaQACFQ1rG0IO8VbH4wXPJwf1hAEAAwIAA3gAAzgE)

5/ During code review, I will often tag @.claude on my coworkers' PRs to add something to the http://CLAUDE.md as part of the PR. We use the Claude Code Github action (/install-github-action) for this. It's our version of 
@danshipper
's Compounding Engineering

![1000023801.jpg](https://i.829259.xyz/api/cfile/AgACAgUAAx0ER6IxDQACTnBpXl0K6FnV1V9-0lcRF2WfqBF8sgACFg1rG0IO8Vbpo9JUC8jt3wEAAwIAA3gAAzgE)

6/ Most sessions start in Plan mode (shift+tab twice). If my goal is to write a Pull Request, I will use Plan mode, and go back and forth with Claude until I like its plan. From there, I switch into auto-accept edits mode and Claude can usually 1-shot it. A good plan is really important!

![1000023802.jpg](https://i.829259.xyz/api/cfile/AgACAgUAAx0ER6IxDQACTnFpXl0Oat-5gRPW9BvlxTm6FhQZKAACFw1rG0IO8VYYZysiMV0ftgEAAwIAA3gAAzgE)

7/ I use slash commands for every "inner loop" workflow that I end up doing many times a day. This saves me from repeated prompting, and makes it so Claude can use these workflows, too. Commands are checked into git and live in .claude/commands/.

![1000023803.png](https://i.829259.xyz/api/cfile/AgACAgUAAx0ER6IxDQACTnJpXl0VG_5xB-qSUCxm9PcaXhLIrwACGA1rG0IO8Vb-FBb90ihaOQEAAwIAA3gAAzgE)

For example, Claude and I use a /commit-push-pr slash command dozens of times every day. The command uses inline bash to pre-compute git status and a few other pieces of info to make the command run quickly and avoid back-and-forth with the model 

8/ I use a few subagents regularly: code-simplifier simplifies the code after Claude is done working, verify-app has detailed instructions for testing Claude Code end to end, and so on. Similar to slash commands, I think of subagents as automating the most common workflows that I do for most PRs.

![1000023804.jpg](https://i.829259.xyz/api/cfile/AgACAgUAAx0ER6IxDQACTnNpXl0YgjAXVHvMSyBKtCNV3-upfAACGQ1rG0IO8VbFFh_ELee2KAEAAwIAA3gAAzgE)

9/ We use a PostToolUse hook to format Claude's code. Claude usually generates well-formatted code out of the box, and the hook handles the last 10% to avoid formatting errors in CI later.

![1000023805.png](https://i.829259.xyz/api/cfile/AgACAgUAAx0ER6IxDQACTnRpXl0aMThKOS7moU6tBx7v4Hi4RAACGg1rG0IO8VbcKAoT1Wzx8AEAAwIAA3gAAzgE)

10/ I don't use --dangerously-skip-permissions. Instead, I use /permissions to pre-allow common bash commands that I know are safe in my environment, to avoid unnecessary permission prompts. Most of these are checked into .claude/settings.json and shared with the team.

![1000023806.jpg](https://i.829259.xyz/api/cfile/AgACAgUAAx0ER6IxDQACTnVpXl0fQ5nC0eHVClaKFYGEBk6ZBQACGw1rG0IO8VY4h5qhFy-YEgEAAwIAA3gAAzgE)

11/ Claude Code uses all my tools for me. It often searches and posts to Slack (via the MCP server), runs BigQuery queries to answer analytics questions (using bq CLI), grabs error logs from Sentry, etc. The Slack MCP configuration is checked into our .mcp.json and shared with the team.


![1000023807.jpg](https://i.829259.xyz/api/cfile/AgACAgUAAx0ER6IxDQACTnZpXl0jgpOqqjsi7leuJqydNh05OgACHA1rG0IO8VZVQ6rXWRbBFQEAAwIAA3gAAzgE)

12/ For very long-running tasks, I will either (a) prompt Claude to verify its work with a background agent when it's done, (b) use an agent Stop hook to do that more deterministically, or (c) use the ralph-wiggum plugin (originally dreamt up by 
@GeoffreyHuntley
). I will also use either --permission-mode=dontAsk or --dangerously-skip-permissions in a sandbox to avoid permission prompts for the session, so Claude can cook without being blocked on me.
[链接](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/ralph-wiggum)

[链接](https://code.claude.com/docs/en/hooks-guide)

![1000023808.jpg](https://i.829259.xyz/api/cfile/AgACAgUAAx0ER6IxDQACTndpXl0mby1AbAkQqdv8JgaBuZ4BewACHQ1rG0IO8VaQPSs0TceROAEAAwIAA3gAAzgE)

13/ A final tip: probably the most important thing to get great results out of Claude Code -- give Claude a way to verify its work. If Claude has that feedback loop, it will 2-3x the quality of the final result.

Claude tests every single change I land to http://claude.ai/code using the Claude Chrome extension. It opens a browser, tests the UI, and iterates until the code works and the UX feels good.

Verification looks different for each domain. It might be as simple as running a bash command, or running a test suite, or testing the app in a browser or phone simulator. Make sure to invest in making this rock-solid.
[链接](https://code.claude.com/docs/en/chrome)

![1000023809.png](https://i.829259.xyz/api/cfile/AgACAgUAAx0ER6IxDQACTnhpXl0tbvsfYoou-z93nc_iHm9VcgACHg1rG0IO8Va-7NFIqj3VtwEAAwIAA3gAAzgE)

