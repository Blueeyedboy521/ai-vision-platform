# 区域层级路径与通知策略匹配

## 1. 目标

- 策略匹配时按「区域」过滤需要用到**区域层级路径**：ID 层级路径（匹配用）+ 名称层级路径（展示/模板用）。
- 凡带 `camera_id` 的告警（AI 告警、系统告警）都应先根据摄像头查到其所属区域的路径，写入 event，再与策略的 `area_config` 做通配符匹配。
- 区域路径在区域表冗余存储，并在 Redis 按摄像头缓存，减少 dispatch 时查库。

## 2. 统一命名约定（event 与 policy 一致）

| 概念 | 后端/Event/Redis/Policy 存盘（snake_case） | 含义 | 示例 |
|------|------------------------------------------|------|------|
| **ID 层级路径** | `area_id_path` | 用于策略区域匹配、通配符 | `/root_id/1/1.1` |
| **名称层级路径** | `area_name_path` | 用于展示、模板变量 | `根节点/车间/A区域` |

- **Event**：必须包含 `area_id_path`（策略匹配）、`area_name_path`（展示）；为兼容模板变量 `{{area_name}}`，同时设置 `area_name = area_name_path`。
- **Policy 存盘**：与其它 match 字段一致，配置 JSON 使用**下划线**。`area_config` 每项为 `area_id_path`、`area_name_path`（及 `value`、`label`）。
- **区域表 areas**：`id_path` 存 ID 层级路径，`hierarchy_path` 存名称层级路径（已有）。
- **Redis** `camera:area_paths:{camera_id}`：JSON 使用 `area_id_path`、`area_name_path`，与 event 命名一致。

## 3. Redis Key

- **Key**：`camera:area_paths:{camera_id}`
- **Value**：JSON `{"area_id_path": "/...", "area_name_path": "..."}`
- **失效**：
  - 摄像头新增/修改（含 `area_id` 变更）：删除该 `camera_id` 的 key。
  - 区域树变更（某节点 name/parent 变更）：删除「该节点及其所有子孙」对应区域下摄像头的 key。

## 4. 流程简述

1. **dispatch_event** 入口若 `event.get("camera_id")` 存在，先调 `get_camera_area_paths(camera_id)`（先 Redis 后 DB，回写 Redis），将返回的路径写入 `event["area_id_path"]`、`event["area_name_path"]`，并设 `event["area_name"] = event["area_name_path"]`，再执行策略匹配。
2. **get_camera_area_paths**：Redis 未命中则查库（camera → area），写入 Redis 后返回 `{ area_id_path, area_name_path }`。
3. 策略匹配时用 `event["area_id_path"]` 与 `area_config[].areaIdPath`（或 `idPath`）做通配符匹配。
4. 摄像头 API 在创建/更新/删除摄像头后删除该摄像头的 `camera:area_paths:{id}`。
5. 区域 API 在更新区域（触发子树 hierarchy 刷新）后，对该子树下所有摄像头的缓存执行批量删除。
