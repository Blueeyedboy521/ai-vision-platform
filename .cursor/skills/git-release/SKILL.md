---
name: git-release
description: Manage version tags and releases for code deployment. Use when the user wants to create a new version tag, push tags to remote, release a new version, or manage semantic versioning (semver).
---

# Git Release - 版本发布技能

## 功能概述

帮助创建版本 Tag、推送到远程仓库，支持语义化版本管理。

## 使用流程

### 1. 查看当前版本

首先检查现有的 tags：

```bash
# 查看所有 tags
git tag -l

# 查看最新的 tag
git describe --tags --abbrev=0

# 查看 tag 详情
git tag -l -n
```

### 2. 创建新版本 Tag

#### 语义化版本规范 (SemVer)

版本号格式: `v主版本.次版本.修订版本` (例如: v1.2.3)

| 版本类型 | 何时递增 | 示例 |
|---------|---------|------|
| 主版本 (Major) | 不兼容的 API 变更 | v1.0.0 → v2.0.0 |
| 次版本 (Minor) | 新增向后兼容的功能 | v1.0.0 → v1.1.0 |
| 修订版本 (Patch) | 向后兼容的问题修复 | v1.0.0 → v1.0.1 |

#### 创建 Tag 命令

```bash
# 创建轻量级 tag
git tag v1.0.0

# 创建附注 tag（推荐）
git tag -a v1.0.0 -m "Release v1.0.0: 初始版本发布"

# 为特定 commit 创建 tag
git tag -a v1.0.0 -m "Release v1.0.0" <commit-hash>
```

### 3. 推送 Tag 到远程

```bash
# 推送单个 tag
git push origin v1.0.0

# 推送所有本地 tags
git push origin --tags

# 推送附注 tags（不推送轻量级 tags）
git push origin --follow-tags
```

### 4. 删除 Tag（如需要）

```bash
# 删除本地 tag
git tag -d v1.0.0

# 删除远程 tag
git push origin --delete v1.0.0
```

## 版本发布检查清单

创建新版本前，请确认：

- [ ] 所有代码已提交并推送
- [ ] 当前分支是 main/master
- [ ] 测试通过
- [ ] 更新了 CHANGELOG（如有）
- [ ] 版本号符合语义化规范

## 快速发布工作流

当用户请求发布新版本时，执行以下步骤：

1. **确认当前状态**
   ```bash
   git status
   git log --oneline -5
   git tag -l --sort=-v:refname | head -5
   ```

2. **确定版本号**
   - 查看上一个版本
   - 根据变更类型确定新版本号

3. **创建并推送 Tag**
   ```bash
   git tag -a vX.Y.Z -m "Release vX.Y.Z: 版本描述"
   git push origin vX.Y.Z
   ```

4. **验证发布**
   ```bash
   git tag -l -n | head -5
   git ls-remote --tags origin | tail -5
   ```

## Tag 命名建议

```
v1.0.0          # 正式版本
v1.0.0-alpha.1  # Alpha 测试版
v1.0.0-beta.1   # Beta 测试版
v1.0.0-rc.1     # 候选发布版
```

## 示例

**用户**: "发布 v1.2.0 版本"

**操作**:
```bash
# 1. 检查状态
git status
git describe --tags --abbrev=0

# 2. 创建 tag
git tag -a v1.2.0 -m "Release v1.2.0: 新增视频预览功能"

# 3. 推送到远程
git push origin v1.2.0

# 4. 验证
git tag -l -n | grep v1.2.0
```
