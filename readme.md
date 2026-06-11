# Yohaku Deploy Action

> **Note:** 本仓库已重命名为 **yohaku-deploy-action**（原名为 `shiroi-deploy-action`）。GitHub 会自动处理旧链接的重定向，原有 fork 和引用不受影响。

这是一个利用 GitHub Action 去构建私有版本站点并部署到远程服务器的工作流。

## Why?

- [Yohaku](https://github.com/Innei/Yohaku) 是当前闭源完整实现。
- Next.js build 需要大量内存，很多服务器并吃不消这样的开销，因此利用 GitHub Action 完成构建后推送到服务器。
- 支持 **Docker** 和 **PM2** 两种部署方式，可根据服务器环境自由选择。

## 部署方式选择

本工作流支持两种部署方式，通过 `DEPLOY_METHOD` 环境变量切换：

| 方式 | 描述 | 适用场景 |
|------|------|----------|
| `docker`（默认） | 构建 Docker 镜像 → SCP 到服务器 → `docker load` + `docker run` | 服务器已安装 Docker，希望容器化运行 |
| `pm2` | 构建 Next.js standalone → SCP zip → `unzip` + `pm2 restart` | 服务器已安装 Node.js/pm2，无需 Docker |

**修改方式：** 在 `.github/workflows/deploy.yml` 的 `env` 段修改 `DEPLOY_METHOD` 值，或在手动运行时通过工作流输入选择。

## 前置准备

### 通用（两种方式都需要）

1. 在你的服务器家目录创建 `yohaku` 目录，新建 `.env` 填写环境变量（参考私有仓库中的 `.env.template`）。
2. Fork 此项目并配置以下 Secrets。

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

设置 pm2 开机自启：
```bash
pm2 startup
pm2 save
```

## 快速开始

1. Fork 此项目。
2. 在仓库 **Settings → Secrets and variables → Actions** 中配置以下 Secrets。
3. 根据需要修改 `.github/workflows/deploy.yml` 中的 `DEPLOY_METHOD`（默认 `docker`）。
4. 推送到 main 分支触发部署。

### 手动触发

工作流支持 `workflow_dispatch` 手动触发，可在运行时选择部署方式：

```bash
# 在 GitHub Actions 页面选择 workflow → Run workflow → 选择 docker 或 pm2
```

## 配置项

工作流支持以下环境变量（在 `.github/workflows/deploy.yml` 的 `env` 段修改，或通过 GitHub Variables 注入）：

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `DEPLOY_METHOD` | `docker` | 部署方式：`docker` 或 `pm2` |
| `SOURCE_REPO` | `innei-dev/Yohaku` | 私有源码仓库（格式：`owner/repo`） |

## Secrets

| Secret | 说明 |
|--------|------|
| `GH_PAT` | 可访问私有源码仓库的 GitHub Token（需 `repo` 权限） |
| `HOST` | 服务器地址 |
| `USER` | 服务器 SSH 用户名 |
| `PASSWORD` | 服务器 SSH 密码（与 KEY 二选一） |
| `KEY` | 服务器 SSH 私钥（与 PASSWORD 二选一） |
| `PORT` | 服务器 SSH 端口 |
| `PUSHPLUS_TOKEN` | （可选）PushPlus 推送通知 Token |

### Docker 方式额外 Secrets

| Secret | 说明 |
|--------|------|
| `BASE_URL` | 站点对外根 URL，例如 `https://example.com` |
| `S3_ACCESS_KEY` | S3 存储密钥 |
| `S3_SECRET_KEY` | S3 存储密钥 |
| `WEBHOOK_SECRET` | Webhook 密钥 |
| `TMDB_API_KEY` | TMDB API 密钥 |
| `GH_TOKEN` | GitHub Token |

### GitHub Token 配置

1. 你的账号可以访问当前私有源码仓库。
2. 进入 [Personal access tokens](https://github.com/settings/tokens) → Tokens (classic) → Generate new token
3. 勾选 `repo` 权限。

## CI 构建与站点 URL

工作流在 GitHub Actions 里执行构建时，会通过 Secrets 注入构建参数。

- **Docker 方式**：通过 `docker/build-push-action` 的 `build-args` 传入，由 Dockerfile 的 `ENV` 指令写入镜像。
- **PM2 方式**：通过 `actions/setup-node` 和构建命令执行 `next build`，构建期使用的环境变量在 `.env` 文件中定义。

建议确保服务器 `~/yohaku/.env` 中的变量与构建参数一致。

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
