# 权限管理系统设计文档

## 1. 系统架构概述

### 1.1 设计目标
- 实现基于角色的访问控制（RBAC）
- 支持细粒度的权限管理（菜单、操作、按钮级）
- 提供资源管理界面，以树形结构维护各类资源
- 实现前后端权限拦截与鉴权
- 支持权限的动态分配与回收

### 1.2 核心模块
- **用户管理**：已存在
- **角色管理**：已存在
- **资源管理**：新增
- **权限分配**：新增
- **权限验证**：新增

## 2. 数据库表设计

### 2.1 资源表（sys_resource）
| 字段名 | 数据类型 | 长度 | 约束 | 描述 |
|-------|---------|------|------|------|
| id | VARCHAR | 36 | PRIMARY KEY | 资源ID（UUID） |
| name | VARCHAR | 100 | NOT NULL | 资源名称 |
| key | VARCHAR | 100 | UNIQUE NOT NULL | 权限Key（如：system:user:list） |
| type | VARCHAR | 20 | NOT NULL | 资源类型（menu/button/api） |
| parent_id | VARCHAR | 36 | NULL | 父资源ID |
| level | INT | 10 | NOT NULL | 资源层级 |
| path | VARCHAR | 500 | NULL | 前端路由路径 |
| component | VARCHAR | 255 | NULL | 前端组件路径 |
| icon | VARCHAR | 50 | NULL | 菜单图标 |
| api_url | VARCHAR | 255 | NULL | 后端API地址 |
| method | VARCHAR | 10 | NULL | API请求方法（GET/POST等） |
| sort | INT | 10 | NOT NULL DEFAULT 0 | 排序字段 |
| status | TINYINT | 1 | NOT NULL DEFAULT 1 | 状态（1-启用，0-禁用） |
| created_by | VARCHAR | 36 | NULL | 创建人ID |
| updated_by | VARCHAR | 36 | NULL | 更新人ID |
| created_at | DATETIME | - | NOT NULL | 创建时间 |
| updated_at | DATETIME | - | NOT NULL | 更新时间 |

### 2.2 角色表（sys_role）
| 字段名 | 数据类型 | 长度 | 约束 | 描述 |
|-------|---------|------|------|------|
| id | VARCHAR | 36 | PRIMARY KEY | 角色ID（UUID） |
| name | VARCHAR | 100 | NOT NULL | 角色名称 |
| code | VARCHAR | 100 | UNIQUE NOT NULL | 角色编码 |
| description | TEXT | - | NULL | 角色描述 |
| status | TINYINT | 1 | NOT NULL DEFAULT 1 | 状态（1-启用，0-禁用） |
| created_by | VARCHAR | 36 | NULL | 创建人ID |
| updated_by | VARCHAR | 36 | NULL | 更新人ID |
| created_at | DATETIME | - | NOT NULL | 创建时间 |
| updated_at | DATETIME | - | NOT NULL | 更新时间 |

### 2.3 用户表（sys_user）
| 字段名 | 数据类型 | 长度 | 约束 | 描述 |
|-------|---------|------|------|------|
| id | VARCHAR | 36 | PRIMARY KEY | 用户ID（UUID） |
| username | VARCHAR | 100 | UNIQUE NOT NULL | 用户名 |
| password | VARCHAR | 255 | NOT NULL | 密码（加密存储） |
| nickname | VARCHAR | 100 | NOT NULL | 昵称 |
| email | VARCHAR | 100 | UNIQUE NULL | 邮箱 |
| phone | VARCHAR | 20 | UNIQUE NULL | 手机号 |
| status | TINYINT | 1 | NOT NULL DEFAULT 1 | 状态（1-启用，0-禁用） |
| created_by | VARCHAR | 36 | NULL | 创建人ID |
| updated_by | VARCHAR | 36 | NULL | 更新人ID |
| created_at | DATETIME | - | NOT NULL | 创建时间 |
| updated_at | DATETIME | - | NOT NULL | 更新时间 |

### 2.4 用户-角色关联表（sys_user_role）
| 字段名 | 数据类型 | 长度 | 约束 | 描述 |
|-------|---------|------|------|------|
| id | VARCHAR | 36 | PRIMARY KEY | 关联ID（UUID） |
| user_id | VARCHAR | 36 | NOT NULL | 用户ID |
| role_id | VARCHAR | 36 | NOT NULL | 角色ID |
| created_by | VARCHAR | 36 | NULL | 创建人ID |
| created_at | DATETIME | - | NOT NULL | 创建时间 |

### 2.5 角色-资源关联表（sys_role_resource）
| 字段名 | 数据类型 | 长度 | 约束 | 描述 |
|-------|---------|------|------|------|
| id | VARCHAR | 36 | PRIMARY KEY | 关联ID（UUID） |
| role_id | VARCHAR | 36 | NOT NULL | 角色ID |
| resource_id | VARCHAR | 36 | NOT NULL | 资源ID |
| created_by | VARCHAR | 36 | NULL | 创建人ID |
| created_at | DATETIME | - | NOT NULL | 创建时间 |

## 3. 关联关系

```
┌─────────────┐       ┌────────────────┐       ┌──────────────┐
│   sys_user  │       │ sys_user_role  │       │   sys_role   │
├─────────────┤       ├────────────────┤       ├──────────────┤
│ id          │◄──────┤ user_id        │       │ id           │
│ username    │       │ role_id        │──────►│ name         │
│ password    │       │ created_by     │       │ code         │
│ ...         │       │ created_at     │       │ description  │
└─────────────┘       └────────────────┘       │ ...          │
                                               └──────────────┘
                                                     ▲
                                                     │
┌─────────────────────┐                             │
│ sys_role_resource   │─────────────────────────────┘
├─────────────────────┤
│ id                  │
│ role_id             │
│ resource_id         │
│ created_by          │
│ created_at          │
└─────────────────────┘
                                                     │
┌──────────────┐                                     │
│ sys_resource │◄────────────────────────────────────┘
├──────────────┤
│ id          │
│ name        │
│ key         │
│ type        │
│ parent_id   │
│ ...         │
└──────────────┘
```

## 4. 资源管理设计

### 4.1 资源类型
- **menu**：菜单资源，对应前端路由
- **button**：按钮资源，对应页面操作按钮
- **api**：API资源，对应后端接口

### 4.2 资源树形结构
```
系统管理
├── 用户管理 (menu)
│   ├── 用户列表 (api: GET /api/users)
│   ├── 新增用户 (api: POST /api/users)
│   ├── 编辑用户 (api: PUT /api/users/{id})
│   ├── 删除用户 (api: DELETE /api/users/{id})
│   └── 导出用户 (button)
├── 角色管理 (menu)
│   ├── 角色列表 (api: GET /api/roles)
│   ├── 新增角色 (api: POST /api/roles)
│   └── 编辑角色 (api: PUT /api/roles/{id})
└── 资源管理 (menu)
    ├── 资源列表 (api: GET /api/resources)
    ├── 新增资源 (api: POST /api/resources)
    └── 编辑资源 (api: PUT /api/resources/{id})
```

### 4.3 现有前端资源属性结构

#### 4.3.1 菜单资源
| key | name | type | path | component | icon |
|-----|------|------|------|-----------|------|
| dashboard | 首页概览 | menu | /dashboard | @/views/Dashboard.vue | home |
| messages | 消息中心 | menu | /messages | @/views/Messages.vue | message |
| video_management | 视频管理 | menu | /video | @/views/RouterViewWrapper.vue | video |
| video_cameras | 摄像头管理 | menu | /video/cameras | @/views/CameraManagement.vue | camera |
| video_preview | 视频预览 | menu | /video/preview | @/views/VideoPreview.vue | eye |
| algorithm_management | 算法管理 | menu | /algorithm | @/views/AlgorithmManagement.vue | code |
| push_management | 推送管理 | menu | /push | @/views/RouterViewWrapper.vue | send |
| push_channels | 通道配置 | menu | /push/channels | @/views/push/ChannelManager.vue | settings |
| push_templates | 模板配置 | menu | /push/templates | @/views/push/TemplateManagement.vue | file-text |
| push_policies | 推送策略 | menu | /push/policies | @/views/push/PolicyManagement.vue | list |
| push_add_policy | 新建推送策略 | menu | /push/add-policy | @/views/push/AddPolicy.vue | plus |
| alarm_management | 告警管理 | menu | /alarm | @/views/RouterViewWrapper.vue | alert-circle |
| alarm_list | 告警列表 | menu | /alarm/list | @/views/alarm/AlarmList.vue | list |
| alarm_stats | 告警统计 | menu | /alarm/stats | @/views/alarm/AlarmStats.vue | bar-chart |
| system_config | 系统配置 | menu | /system | @/views/RouterViewWrapper.vue | settings |
| system_overview | 系统概览 | menu | /system/overview | @/views/system/SystemOverview.vue | info |
| system_users | 用户管理 | menu | /system/users | @/views/system/UserManagement.vue | users |
| system_roles | 角色权限 | menu | /system/roles | @/views/system/RoleManagement.vue | shield |
| system_settings | 系统设置 | menu | /system/settings | @/views/system/SystemSettings.vue | cog |
| system_logs | 操作日志 | menu | /system/logs | @/views/system/OperationLogs.vue | log |

#### 4.3.2 API资源
| key | name | type | api_url | method |
|-----|------|------|---------|--------|
| system_health | 系统健康状态 | api | /system/health | GET |
| system_info | 系统信息 | api | /system/info | GET |
| system_dashboard | 系统统计 | api | /system/dashboard | GET |
| system_logs | 系统日志 | api | /system/logs | GET |
| system_cleanup | 清理过期数据 | api | /system/cleanup | POST |
| system_config | 系统配置 | api | /system/config | GET |
| system_config_update | 更新系统配置 | api | /system/config | PUT |
| models_list | 模型列表 | api | /models | GET |
| models_detail | 模型详情 | api | /models/{id} | GET |
| models_create | 创建模型 | api | /models | POST |
| models_update | 更新模型 | api | /models/{id} | PUT |
| models_delete | 删除模型 | api | /models/{id} | DELETE |
| models_load | 加载模型 | api | /models/{id}/load | POST |
| models_unload | 卸载模型 | api | /models/{id}/unload | POST |
| models_classes | 模型类别 | api | /models/{id}/classes | GET |

### 4.4 资源管理功能
- 资源的增删改查
- 资源的树形展示
- 资源的层级管理
- 权限Key的生成与管理
- 前端路由与后端API的关联

## 5. 权限验证逻辑

### 5.1 后端权限验证
1. **接口级验证**：
   - 通过中间件拦截所有API请求
   - 解析请求URL和方法，匹配对应的资源
   - 检查当前用户角色是否拥有该资源的访问权限
   - 无权限则返回403错误

2. **服务层验证**：
   - 在关键业务逻辑中添加权限检查
   - 确保即使绕过API层也能进行权限控制

### 5.2 前端权限验证
1. **路由拦截**：
   - 前端路由守卫检查用户是否有权限访问该路由
   - 无权限则重定向到无权限页面

2. **按钮级控制**：
   - 根据用户权限动态显示/隐藏操作按钮
   - 禁用无权限的操作

3. **菜单过滤**：
   - 根据用户权限动态生成菜单列表
   - 只显示用户有权访问的菜单

## 6. 前后端鉴权方案

### 6.1 后端实现
1. **权限中间件**：
   ```python
   class PermissionMiddleware:
       async def __call__(self, request, call_next):
           # 解析请求路径和方法
           path = request.url.path
           method = request.method
           
           # 获取当前用户
           user = request.state.user
           
           # 检查是否为公开接口
           if self.is_public(path):
               return await call_next(request)
           
           # 检查用户权限
           if not await self.has_permission(user, path, method):
               return JSONResponse({"detail": "权限不足"}, status_code=403)
           
           return await call_next(request)
   ```

2. **权限验证服务**：
   ```python
   class PermissionService:
       async def has_permission(self, user, path, method):
           # 获取用户角色列表
           roles = await self.get_user_roles(user.id)
           
           # 获取资源
           resource = await self.get_resource_by_api(path, method)
           if not resource:
               return False
           
           # 检查是否有角色拥有该资源权限
           for role in roles:
               if await self.check_role_resource(role.id, resource.id):
                   return True
           
           return False
   ```

### 6.2 前端实现
1. **权限存储**：
   - 登录后从后端获取用户权限列表
   - 存储在全局状态管理中（如Vuex/Pinia）

2. **路由守卫**：
   ```javascript
   router.beforeEach((to, from, next) => {
     const permissions = store.state.permissions
     const requiresAuth = to.meta.requiresAuth
     
     if (requiresAuth && !hasPermission(permissions, to.path)) {
       next('/403')
     } else {
       next()
     }
   })
   ```

3. **权限指令**：
   ```javascript
   Vue.directive('permission', {
     inserted(el, binding) {
       const permission = binding.value
       const permissions = store.state.permissions
       
       if (!hasPermission(permissions, permission)) {
         el.style.display = 'none'
       }
     }
   })
   ```

4. **菜单生成**：
   ```javascript
   computed: {
     menuList() {
       return this.filterMenu(this.allMenus, this.permissions)
     }
   },
   
   methods: {
     filterMenu(menus, permissions) {
       return menus.filter(menu => {
         if (menu.children) {
           menu.children = this.filterMenu(menu.children, permissions)
           return menu.children.length > 0
         }
         return hasPermission(permissions, menu.key)
       })
     }
   }
   ```

## 7. 权限分配流程

### 7.1 角色授权
1. 进入角色管理页面
2. 选择目标角色
3. 打开权限分配对话框
4. 在树形结构中选择需要分配的资源
5. 保存权限分配

### 7.2 用户角色分配
1. 进入用户管理页面
2. 选择目标用户
3. 打开角色分配对话框
4. 选择需要分配的角色
5. 保存角色分配

### 7.3 权限继承
- 菜单权限会自动继承给子菜单
- 父资源权限会自动包含子资源权限

## 8. 性能优化

### 8.1 缓存策略
- 缓存用户权限列表，减少数据库查询
- 缓存资源树形结构，提高前端渲染速度

### 8.2 权限验证优化
- 使用Redis存储权限信息，提高验证速度
- 实现权限验证的本地缓存，减少重复验证

## 9. 安全考虑

### 9.1 权限控制
- 防止越权访问
- 防止权限提升
- 定期权限审计

### 9.2 数据安全
- 密码加密存储
- API请求验证
- 防止SQL注入

## 10. 开发计划

### 10.1 阶段一：数据库设计与迁移（1周）
- 设计数据库表结构
- 创建迁移脚本
- 执行数据库迁移
- 初始化基础数据

### 10.2 阶段二：后端实现（2周）
- 创建资源管理API
- 实现权限验证中间件
- 完善角色-资源关联功能
- 实现用户-角色多对多关联
- 开发权限验证服务

### 10.3 阶段三：前端实现（2周）
- 开发资源管理界面
- 实现权限控制组件
- 完善路由守卫和权限指令
- 开发角色授权界面
- 开发用户角色分配界面

### 10.4 阶段四：测试与优化（1周）
- 功能测试：验证权限分配和验证功能
- 安全测试：验证权限控制的安全性
- 性能测试：验证权限验证的性能
- 优化代码和性能

### 10.5 阶段五：部署与文档（1周）
- 部署到测试环境
- 编写用户文档
- 编写开发文档
- 培训相关人员

## 11. 扩展性考虑

### 11.1 未来功能
- 支持权限模板（预设的权限组合）
- 支持临时权限（如临时授权某个用户访问特定资源）
- 支持权限审计和日志记录
- 支持数据权限控制（后续规划）

### 11.2 技术扩展
- 支持多种认证方式（如OAuth2、LDAP）
- 支持细粒度的数据权限控制
- 支持权限分析和优化建议

## 12. 总结

本设计方案实现了一个完整的权限管理系统，包括：
- 资源的树形管理（使用UUID）
- 基于角色的权限分配（支持多角色）
- 前后端的权限验证
- 细粒度的权限控制

该方案具有良好的扩展性和可维护性，能够满足系统的权限管理需求，为后续的功能扩展提供了基础。