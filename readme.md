# Yohaku Deploy Action

> **Note:** 本仓库已重命名为 **yohaku-deploy-action**（原名为 `shiroi-deploy-action`）。GitHub 会自动处理旧链接的重定向，原有 fork 和引用不受影响。

这是一个利用 GitHub Action 去构建私有版本站点并部署到远程服务器的工作流。

## Why?

这里的项目关系现在更准确地说是：

- [Yohaku](https://github.com/Innei/Yohaku) 是当前设计语言与视觉体系已经完全重构后的闭源完整实现。
- [Shiro](https://github.com/Innei/Shiro) 是更早期的开源来源项目。
- `Shiroi` 更接近 Yohaku 在大改版之前的历史阶段或兼容称呼；如果你需要旧设计风格，可以切换到 `Shiroi` 对应的历史版本。

开源版本通常提供了预构建的 Docker 镜像或者编译产物可直接使用，但是当前私有完整实现并没有提供。

因为 Next.js build 需要大量内存，很多服务器并吃不消这样的开销。

因此这里提供利用 GitHub Action 去完成构建然后推送到服务器。

你可以使用定时任务去定时更新 Yohaku，或部署旧风格的 Shiroi 历史版本。

支持 **Docker** 和 **PM2** 两种部署方式，可根据服务器环境自由选择。

## 最近变更

- **仓库重命名**：`shiroi-deploy-action` → `yohaku-deploy-action`。
- **PR #17** 将默认源码仓库从 `innei-dev/shiroi` 修改为 `innei-dev/Yohaku`，以匹配当前主力项目。如果你在部署旧版 Shiroi，请将 `SOURCE_REPO` 改回 `innei-dev/shiroi`。
- 工作流已通用化：源码仓库、构建命令、产物路径均可通过环境变量覆盖，详见下节「配置项」。

## How to

开始之前，根据你选择的部署方式准备服务器环境。

### 通用（两种方式都需要）

在你的服务器家目录，新建 `yohaku` 目录，然后新建 `.env` 填写你的变量。

```
# Env from your private Yohaku repo .env.template
BASE_URL=

NEXT_PUBLIC_API_URL=
NEXT_PUBLIC_GATEWAY_URL=

TMDB_API_KEY=
GH_TOKEN=
```

### Docker 方式

服务器需要安装 Docker：
```bash
# 安装 Docker（以 Ubuntu/Debian 为例）
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
```

### PM2 方式

服务器需要安装 Node.js、pnpm、pm2 和 sharp：

```bash
# 安装 Node.js 20
curl -fsSL https://deb.nodesource.com/setup_20.x | bash
apt install -y nodejs

# 安装 pnpm
npm install -g pnpm@latest

# 安装 pm2
npm install -g pm2

# 安装 sharp（可选，但缺少会有报错）
npm install -g sharp
```

PM2 的 ecosystem 配置文件位于本仓库的 `pm2/ecosystem.config.js`，需要在服务器 `~/yohaku/` 目录下放置一份。

为了让 PM2 在服务器重启之后能够还原进程：
```bash
pm2 startup
pm2 save
```

Fork 此项目，然后填写下面的信息。

## 配置项

工作流支持以下环境变量（在 `.github/workflows/deploy.yml` 的 `env` 段修改，或通过 GitHub Variables 注入）：

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `DEPLOY_METHOD` | `docker` | 部署方式：`docker` 或 `pm2` |
| `SOURCE_REPO` | `innei-dev/Yohaku` | 私有源码仓库（格式：`owner/repo`） |
| `BUILD_COMMAND` | `pnpm --filter @yohaku/web build:ci` | 构建命令。workflow 会在构建后自动执行 standalone 打包与 zip；如果你的项目结构不同，可修改此命令 |
| `STANDALONE_SUBPATH` | `standalone/apps/web` | 构建产物中 standalone 包的相对路径。Yohaku 与旧版 Shiroi 若结构不同，请按需调整 |

如果你部署的是旧版 **Shiroi**（monorepo 结构为 `apps/web`），通常保持默认即可；若你的仓库结构不同（例如单仓库直接输出到 `.next/standalone`），请修改 `STANDALONE_SUBPATH`。

## 部署方式选择

通过 `DEPLOY_METHOD` 环境变量切换：

| 方式 | 描述 | 适用场景 |
|------|------|----------|
| `docker`（默认） | 构建 Docker 镜像 → SCP 到服务器 → `docker load` + `docker run` | 服务器已安装 Docker，希望容器化运行 |
| `pm2` | 构建 Next.js standalone → SCP zip → `unzip` + `pm2 restart` | 服务器已安装 Node.js/pm2，无需 Docker |

**修改方式：** 在 `.github/workflows/deploy.yml` 的 `env` 段修改 `DEPLOY_METHOD` 值，或在手动运行时通过工作流输入选择。

## CI 构建与站点 URL 环境变量

工作流在 GitHub Actions 里执行 `next build` 时，会通过仓库 **Secrets** 注入 `BASE_URL`、`NEXT_PUBLIC_API_URL` 与 `NEXT_PUBLIC_GATEWAY_URL`，须与服务器 `~/yohaku/.env`（及私有仓库 `Dockerfile` / 模板）一致。

- **`BASE_URL`**：站点对外根 URL（无尾部斜杠为宜），例如 `https://mx.innei.in`。与私有镜像构建阶段一致：`Dockerfile` 中常用 `ARG BASE_URL`，并令 `NEXT_PUBLIC_GATEWAY_URL=${BASE_URL}`、`NEXT_PUBLIC_API_URL=${BASE_URL}/api/v3`。
- **`NEXT_PUBLIC_*`**：直接参与 `next build` 与客户端 bundle；若启用 **ISR**，构建期/再验证会依赖正确端点，不能只依赖部署机 `.env` 而忽略 Actions。

在仓库 **Settings → Secrets and variables → Actions** 中新增：

- `BASE_URL`
- `NEXT_PUBLIC_API_URL`
- `NEXT_PUBLIC_GATEWAY_URL`

## Secrets

| Secret | 说明 |
| --- | --- |
| `GH_PAT` | 可访问私有源码仓库的 GitHub Token（需 `repo` 权限） |
| `HOST` | 服务器地址 |
| `USER` | 服务器 SSH 用户名 |
| `PASSWORD` | 服务器 SSH 密码（与 KEY 二选一） |
| `KEY` | 服务器 SSH 私钥（与 PASSWORD 二选一） |
| `PORT` | 服务器 SSH 端口 |
| `PUSHPLUS_TOKEN` | （可选）PushPlus 推送通知 Token。未设置时自动跳过推送 |
| `BASE_URL` | 站点对外根 URL |
| `NEXT_PUBLIC_API_URL` | 公开 API URL |
| `NEXT_PUBLIC_GATEWAY_URL` | 公开网关 URL |


### GitHub Token 配置

1. 你的账号可以访问当前私有源码仓库（Yohaku 或你正在使用的对应私有仓库）。
2. 进入 [tokens](https://github.com/settings/tokens) - Personal access tokens - Tokens (classic) - Generate new token - Generate new token (classic)

![](https://github.com/innei-dev/yohaku-deploy-action/assets/41265413/e55d32cb-bd30-46b7-a603-7d00b3f8a413)

### PushPlus 推送通知

设置了 `PUSHPLUS_TOKEN` 后，每次部署完成会通过 PushPlus 推送通知到微信，包含部署状态、版本号、各阶段耗时等。Token 为空时自动跳过，不影响部署流程。

<details>
<summary>推送示例（点击展开）</summary>

```
## Yohaku 部署 ✅ 成功

### 基本信息
| 项目 | 内容 |
|------|------|
| 状态 | ✅ 成功 |
| 版本 | `abc1234` |
| 触发方式 | 代码推送 |
| 运行编号 | #42 |
| 部署方式 | docker |
| 总用时 | 5m 23s |
| 时间 | 2026-06-12 14:30:00 |

### 各阶段结果
| 阶段 | 结果 | 用时 |
|------|------|------|
| Docker 构建 | ✅ success | 3m 15s |
| 镜像打包 | ✅ success（192MB） | 0m 30s |
| 传输到服务器 | ✅ success | 1m 20s |
| 部署启动 | ✅ success | 0m 18s |

### 提交信息
> feat: add new theme support

[查看 GitHub Actions 运行详情](https://github.com/sysfox/yohaku-deploy-action/actions/runs/123456789)
```

</details>

## Docker 部署流程

```
源码 Checkout → Docker Build → Save image(gzip) → SCP到服务器 → docker load → docker run
```

服务器端运行参数：
- 端口映射：`2323:2323`
- 挂载 `~/yohaku/.env` → `/app/.env`
- 容器名：`yohaku`
- 自动重启策略：`--restart always`

镜像保留最后 2 个版本用于回滚，位于 `~/yohaku/images/`。

## PM2 部署流程

```
源码 Checkout → pnpm install → pnpm build:ci → 打包 standalone(zip) → SCP → unzip → pm2 restart
```

服务器端使用 `pm2/ecosystem.config.js` 管理进程。部署目录为 `~/yohaku/standalone/`。

### 历史版本参考

如果你需要**部署旧版 Shiroi**，可直接回退到以下历史 commit：

| Commit | 说明 | 适用场景 |
|--------|------|----------|
| [`bc07cfa`](https://github.com/innei-dev/yohaku-deploy-action/commit/bc07cfa) | **PR #17 之前最后一个 Shiroi 版本**。默认源码仓库为 `innei-dev/shiroi`，部署目录 `~/shiro`，PM2 应用名 `Shiroi`，构建命令为 `sh ./ci-release-build.sh`。 | 推荐：旧版 Shiroi 配置。 |
| [`80466cf`](https://github.com/innei-dev/yohaku-deploy-action/commit/80466cf) | standalone + PM2 部署流程修复版本。引入了 `pm2/ecosystem.config.js` 模板。 | standalone 部署模式。 |
| [`d495fef`](https://github.com/innei-dev/yohaku-deploy-action/commit/d495fef) | 最初加入 `rollback.sh` 的版本。 | 最早部署脚本实现。 |

切换到旧版本：
```bash
git clone https://github.com/innei-dev/yohaku-deploy-action.git
cd yohaku-deploy-action
git checkout bc07cfa
```

## Technical details

参考：[跨仓库全自动构建项目并部署到服务器](./post.md)
