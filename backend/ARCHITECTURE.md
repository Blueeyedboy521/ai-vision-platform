# AI 视觉平台 - 后端架构设计

## 一、技术选型

### 1.1 整体技术栈

| 组件 | 技术选型 | 说明 |
|------|----------|------|
| Web 框架 | FastAPI | 异步支持好，自动生成 API 文档 |
| 流媒体服务器 | ZLMediaKit | 国产开源，支持 GB28181，性能优秀 |
| 数据库 | PostgreSQL / SQLite | 业务数据存储 |
| 缓存 | Redis | 会话缓存、消息队列（业务层） |
| AI 推理 | ONNX Runtime / TensorRT | 高性能推理引擎 |
| 视频处理 | OpenCV + FFmpeg | 拉流、解码、编码 |

### 1.2 流媒体服务器选型对比

| 特性 | MediaMTX | ZLMediaKit | SRS |
|------|----------|------------|-----|
| 语言 | Go | C++ | C++ |
| 协议支持 | RTSP/RTMP/HLS/WebRTC | RTSP/RTMP/HLS/WebRTC/GB28181 | RTMP/HLS/WebRTC/SRT |
| 性能 | 中等 | 高 | 高 |
| 权限控制 | Hook 回调 | Hook 回调 + API | Hook 回调 |
| 部署难度 | 最简单（单二进制） | 中等 | 中等 |
| 文档 | 英文，简洁 | 中文，详细 | 中文，完善 |

**推荐 ZLMediaKit**，理由：
- 国产开源，中文文档完善
- 支持 GB28181 国标对接
- 性能优秀，单机可支持数千路
- 权限控制完善，支持多种 Hook 回调

### 1.3 流媒体权限控制

```
┌──────────────────────────────────────────────────────────────┐
│                    权限控制流程                               │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  播放请求 ──► on_play Hook ──► 后端API ──► 返回允许/拒绝      │
│                                                              │
│  推流请求 ──► on_publish Hook ──► 后端API ──► 返回允许/拒绝   │
│                                                              │
│  可验证：token、用户权限、IP白名单、时间限制等                  │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 二、整体架构

### 2.1 系统架构图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              前端 (Vue3)                                     │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                     │
│   │  视频播放器  │    │  告警列表   │    │  系统配置   │                     │
│   │ (flv.js)    │    │ (WebSocket) │    │  (REST)    │                     │
│   └──────┬──────┘    └──────┬──────┘    └──────┬──────┘                     │
└──────────┼──────────────────┼──────────────────┼────────────────────────────┘
           │ HTTP-FLV         │ WS               │ HTTP
           ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ZLMediaKit 流媒体服务器                              │
│                                                                             │
│   输入流 (RTSP)                          输出流 (HTTP-FLV/WebRTC)           │
│   camera_001_raw ──────────────────────► camera_001 (原始流分发)            │
│   camera_002_raw ──────────────────────► camera_002                         │
│                                                                             │
│   Hook回调 ◄────────────────────────────────────────────────────────────►   │
└─────────────────────────────────────────────────────────────────────────────┘
           ▲                                      ▲
           │ RTSP拉流                             │ 权限验证回调
           │                                      │
┌──────────┴──────────────────────────────────────┴────────────────────────────┐
│                          视频处理引擎 (Python)                                │
│                                                                              │
│   ┌────────────────────────────────────────────────────────────────────────┐│
│   │                         主调度器 (Scheduler)                            ││
│   │   • 读取摄像头配置，计算各算法 Worker 数量                                ││
│   │   • 创建内存队列 (multiprocessing.Queue)                                ││
│   │   • 启动 InferenceService 进程                                         ││
│   │   • 启动 Pipeline 进程池                                                ││
│   │   • 健康监控与自动重启                                                   ││
│   └────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                          业务 API 层 (FastAPI)                               │
│   • 用户认证、权限管理                                                        │
│   • 摄像头/点位管理                                                           │
│   • 告警规则配置                                                              │
│   • 告警记录存储查询                                                          │
│   • WebSocket 实时推送                                                        │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 进程结构

```
Main Process (调度器)
├── 读取配置，计算 Worker 数量
├── 创建所有队列 (内存 Queue)
├── 启动 InferenceService 进程
└── 启动 N 个 Pipeline 进程

InferenceService Process (1个)
├── ModelManager: 加载所有模型 (每模型1份)
└── WorkerPool: 弹性数量的推理线程

Pipeline Process (N个，每摄像头1个)
├── Thread 1: 拉流线程
├── Thread 2: 推流线程
└── Thread 3: 结果处理线程
```

---

## 三、核心组件设计

### 3.1 InferenceService (推理服务)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      推理服务进程 (InferenceService)                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │                    模型管理器 (ModelManager)                       │ │
│  │                                                                   │ │
│  │   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │ │
│  │   │ YOLO 模型    │  │ 烟火检测模型  │  │ 安全帽模型   │           │ │
│  │   │ GPU:0        │  │ GPU:0        │  │ GPU:0        │           │ │
│  │   │ 显存: 500MB  │  │ 显存: 300MB  │  │ 显存: 200MB  │           │ │
│  │   └──────────────┘  └──────────────┘  └──────────────┘           │ │
│  │                                                                   │ │
│  │   • 每个模型只加载一次，多 Worker 共享                             │ │
│  │   • 模型加载时预热，避免首次推理延迟                               │ │
│  │                                                                   │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │                    工作线程池 (WorkerPool)                         │ │
│  │                                                                   │ │
│  │   ┌────────────┐  ┌────────────┐  ┌────────────┐                 │ │
│  │   │ YOLO       │  │ YOLO       │  │ Fire       │                 │ │
│  │   │ Worker #1  │  │ Worker #2  │  │ Worker #1  │                 │ │
│  │   └────────────┘  └────────────┘  └────────────┘                 │ │
│  │                                                                   │ │
│  │   每个 Worker:                                                    │ │
│  │   ├── 从对应算法的请求队列获取请求                                 │ │
│  │   ├── 批量凑帧 (batch)                                           │ │
│  │   ├── 调用模型推理                                                │ │
│  │   └── 结果放入请求携带的 result_queue                             │ │
│  │                                                                   │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Worker 数量动态计算

```python
# 输入: 摄像头配置
camera_configs = [
    {"id": "cam_001", "algorithms": ["yolo", "fire"]},
    {"id": "cam_002", "algorithms": ["yolo", "helmet"]},
    {"id": "cam_003", "algorithms": ["yolo"]},
    {"id": "cam_004", "algorithms": ["fire"]},
    {"id": "cam_005", "algorithms": ["yolo", "fire", "helmet"]},
]

# 统计每个算法被多少摄像头使用
algo_usage = {
    "yolo":   4,  # 4 个摄像头使用 → 4×25fps = 100 fps 需求
    "fire":   3,  # 3 个摄像头使用 → 3×25fps = 75 fps 需求
    "helmet": 2,  # 2 个摄像头使用 → 2×25fps = 50 fps 需求
}

# 计算 Worker 数量
# 假设: yolo 单 worker (batch=8) 可处理 200 fps
workers = {
    "yolo":   ceil(100 / 200) = 1,
    "fire":   ceil(75 / 150)  = 1,
    "helmet": ceil(50 / 150)  = 1,
}
```

### 3.3 Pipeline (单路流处理管道)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Pipeline 进程 (每摄像头1个)                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  配置: camera_id="cam_001", algorithms=["yolo", "fire"]                 │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │  Thread 1: 拉流线程 (StreamReader)                                 │ │
│  │                                                                   │ │
│  │  职责:                                                            │ │
│  │  ├── 连接 RTSP 流，持续拉取帧                                      │ │
│  │  ├── 帧 → 推流队列 (保证推流帧率不受推理影响)                       │ │
│  │  ├── 帧 → yolo_request_queue (带 result_queue 引用)               │ │
│  │  └── 帧 → fire_request_queue (带 result_queue 引用)               │ │
│  │                                                                   │ │
│  │  跳帧策略: 每 N 帧发送一次推理请求 (可配置)                         │ │
│  │  队列满处理: 丢弃旧帧，保证实时性                                   │ │
│  │                                                                   │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │  Thread 2: 推流线程 (StreamWriter)                                 │ │
│  │                                                                   │ │
│  │  职责:                                                            │ │
│  │  ├── 从推流队列取帧                                                │ │
│  │  ├── FFmpeg 编码                                                  │ │
│  │  └── 推送到流媒体服务器 (RTSP/RTMP)                                │ │
│  │                                                                   │ │
│  │  关键: 独立线程，不等待推理，保证原始帧率 (25fps)                    │ │
│  │                                                                   │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │  Thread 3: 结果处理线程 (ResultHandler)                            │ │
│  │                                                                   │ │
│  │  职责:                                                            │ │
│  │  ├── 从 result_queue 获取推理结果                                  │ │
│  │  ├── 去重过滤 (同目标短时间内不重复告警)                            │ │
│  │  ├── 生成告警记录 (截图、写库)                                     │ │
│  │  ├── WebSocket 推送检测框到前端 (前端叠加显示)                      │ │
│  │  └── 触发消息推送 (邮件、钉钉等)                                   │ │
│  │                                                                   │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  线程总数: 3 个 (拉流 + 推流 + 结果处理)                                │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 四、队列设计

### 4.1 队列结构 (纯内存 Queue)

```
队列类型: multiprocessing.Queue (跨进程共享内存)

推理请求队列 (每算法1个):
├── yolo_request_queue:   Queue(maxsize=100)
├── fire_request_queue:   Queue(maxsize=100)
└── helmet_request_queue: Queue(maxsize=100)

推理结果队列 (每摄像头1个):
├── result_queue_cam_001: Queue(maxsize=50)
├── result_queue_cam_002: Queue(maxsize=50)
└── result_queue_cam_N:   Queue(maxsize=50)
```

### 4.2 数据结构

```python
# 推理请求 (放入算法队列)
InferenceRequest = {
    "request_id": str,          # 唯一请求ID
    "camera_id": str,           # 来源摄像头
    "frame_id": int,            # 帧序号
    "timestamp": float,         # 时间戳
    "image": np.ndarray,        # 直接传 numpy 数组，无需编解码
    "result_queue": Queue,      # 结果返回到哪个队列
}

# 推理结果 (放入摄像头结果队列)
InferenceResult = {
    "request_id": str,
    "camera_id": str,
    "frame_id": int,
    "algorithm": str,
    "detections": List[Detection],
    "inference_time_ms": float,
}

# 检测结果
Detection = {
    "label": str,               # 检测标签 (person, fire, helmet)
    "confidence": float,        # 置信度
    "bbox": [x1, y1, x2, y2],   # 边界框
}
```

### 4.3 数据流

```
1. Pipeline.拉流线程 
   → 帧 → 推流队列 (推流线程消费)
   → 帧 → 算法请求队列 (带 result_queue 引用)

2. InferenceWorker 
   → 从算法队列取帧 
   → 批量推理 
   → 结果放入 result_queue

3. Pipeline.结果处理线程 
   → 从 result_queue 取结果 
   → 去重过滤 
   → WebSocket 推送 + 告警存储
```

---

## 五、批量推理设计

### 5.1 批量策略

```
请求队列              Batch Collector              GPU 推理
    │                      │                          │
┌───▼───┐             ┌────▼────┐               ┌────▼────┐
│ req 1 │────────────►│         │               │         │
│ req 2 │────────────►│ 收集请求 │               │  YOLO   │
│ req 3 │────────────►│         │               │  模型   │
│ req 4 │────────────►│ 触发条件:│───batch=4───►│         │
│ ...   │             │ 1.凑够N帧│               │         │
│       │             │ 2.超时T  │               └────┬────┘
└───────┘             └─────────┘                    │
                                                     │
                      ┌──────────────────────────────┘
                      │
                      ▼
                结果拆分，返回各自 result_queue
```

### 5.2 参数配置

```python
batch_config = {
    "yolo": {
        "max_batch_size": 8,      # 最大批量大小
        "batch_timeout_ms": 50,   # 批量等待超时(ms)
    },
    "fire": {
        "max_batch_size": 4,
        "batch_timeout_ms": 50,
    },
    "helmet": {
        "max_batch_size": 4,
        "batch_timeout_ms": 50,
    },
}

# 逻辑: 先到先处理，凑够 batch 或超时就推理
```

---

## 六、去重过滤设计

### 6.1 去重策略

```python
class DedupTracker:
    """基于时间窗口和空间位置的去重"""
    
    def __init__(self, time_window=30, iou_threshold=0.5):
        self.time_window = time_window      # 30秒内同目标不重复报警
        self.iou_threshold = iou_threshold  # IoU > 0.5 视为同一目标
        self.recent_alarms = []             # 最近的告警记录
    
    def filter(self, detections) -> List:
        """过滤掉重复的检测，返回新的告警"""
        now = time.time()
        
        # 清理过期记录
        self.recent_alarms = [
            a for a in self.recent_alarms
            if now - a["time"] < self.time_window
        ]
        
        new_detections = []
        for det in detections:
            if not self._is_duplicate(det):
                new_detections.append(det)
                self.recent_alarms.append({
                    "time": now,
                    "bbox": det["bbox"],
                    "label": det["label"],
                    "algo": det["algorithm"]
                })
        
        return new_detections
    
    def _is_duplicate(self, det) -> bool:
        """检查是否与最近告警重复"""
        for recent in self.recent_alarms:
            if (recent["label"] == det["label"] and
                recent["algo"] == det["algorithm"] and
                self._calc_iou(recent["bbox"], det["bbox"]) > self.iou_threshold):
                return True
        return False
```

### 6.2 去重维度

| 维度 | 说明 |
|------|------|
| 时间窗口 | 同一摄像头同一算法 N 秒内只报一次 |
| 空间位置 | IoU > 阈值的目标视为同一个 |
| 标签类型 | 相同 label 才去重 (person vs car 不去重) |
| 算法来源 | 相同算法才去重 (yolo vs helmet 不去重) |

---

## 七、前端显示方案

### 7.1 推荐: 前端叠加模式

```
后端：
├── 推流线程：直接推原始流，保证帧率
└── 结果处理线程：推理结果 → WebSocket 发送到前端

前端：
├── Video 标签：播放原始流 (flv.js)
├── Canvas 层：根据 WebSocket 收到的检测框，叠加绘制
└── 优点：低延迟、可选择性显示、不增加后端编码负担
```

### 7.2 WebSocket 数据格式

```json
// 检测框推送 (用于前端画框)
{
    "type": "detections",
    "camera_id": "cam_001",
    "frame_id": 12345,
    "timestamp": 1699999999.123,
    "detections": [
        {"algo": "yolo", "label": "person", "bbox": [100,200,150,300], "conf": 0.92},
        {"algo": "fire", "label": "smoke", "bbox": [400,300,200,150], "conf": 0.87}
    ]
}

// 告警推送 (用于告警列表)
{
    "type": "alarm",
    "camera_id": "cam_001",
    "alarm": {
        "id": 123,
        "level": "danger",
        "title": "检测到人员入侵",
        "algorithm": "yolo",
        "image_url": "/alarms/123.jpg",
        "created_at": "2024-01-01T12:00:00"
    }
}
```

---

## 八、性能估算

### 8.1 延迟分析

```
共享推理模式 (内存 Queue):
├── 拉流解码: 10ms
├── 写入队列: <1ms
├── 队列等待: 0~50ms (取决于 batch 策略)
├── 推理: 30ms / batch_size
├── 结果返回: <1ms
└── 总延迟: ~45-90ms (可接受)
```

### 8.2 吞吐量估算

```
场景: 16 路摄像头，每路 25fps，YOLO + Fire 检测

需求:
├── YOLO: 16 × 25 / skip_frames(5) = 80 fps
└── Fire: 16 × 25 / skip_frames(5) = 80 fps

供给 (RTX 3080):
├── YOLO batch=8: ~200 fps → 1 worker 够用
└── Fire batch=4: ~150 fps → 1 worker 够用

显存: ~1GB (vs 独立模式 8GB+)
```

### 8.3 资源估算参考

| 摄像头数量 | CPU 核心 | 内存 | GPU |
|-----------|---------|------|-----|
| 1-4 路 | 4 核 | 8GB | 可选 |
| 5-16 路 | 8 核 | 16GB | 1x RTX 3060+ |
| 17-32 路 | 16 核 | 32GB | 1x RTX 3080+ |
| 32+ 路 | 多机部署 | - | 多 GPU |

---

## 九、架构优势总结

| 优势 | 说明 |
|------|------|
| 零序列化开销 | numpy 数组通过 Queue 共享内存传递 |
| 弹性扩展 | Worker 数量根据实际配置动态计算 |
| 职责清晰 | 推理、推流、告警处理完全解耦 |
| 资源高效 | 模型只加载一次，显存利用率高 |
| 推流不阻塞 | 推流线程独立，不受推理速度影响 |
| 前端灵活 | 检测框前端叠加，可选择性显示 |

---

## 十、模型与检测能力分层设计

### 10.1 设计背景

一个模型可能训练了多个检测类别，例如一个 YOLO 模型同时能检测：
- 人 (person)
- 安全帽 (helmet) / 未戴安全帽 (no_helmet)
- 反光衣 (vest) / 未穿反光衣 (no_vest)

需要设计合理的数据模型，既能复用模型节省资源，又能灵活配置各检测能力。

### 10.2 分层架构

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        模型与检测能力分层设计                                     │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  模型层 (Model)：物理模型文件，只加载一次                                         │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │  模型ID: yolo_safety_v1                                                 │   │
│  │  模型名称: 安全生产检测模型                                               │   │
│  │  模型文件: yolov8-safety.pt                                             │   │
│  │  支持的类别: [person, helmet, no_helmet, vest, no_vest]                 │   │
│  │  显存占用: 500MB                                                        │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
│  检测能力层 (Algorithm)：业务定义的检测场景                                       │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │  能力: 人员入侵检测                                                      │   │
│  │  所属模型: yolo_safety_v1                                               │   │
│  │  使用类别: [person]                                                     │   │
│  │  置信度: 0.5 | 告警条件: 立即告警                                        │   │
│  ├─────────────────────────────────────────────────────────────────────────┤   │
│  │  能力: 安全帽检测                                                        │   │
│  │  所属模型: yolo_safety_v1                                               │   │
│  │  使用类别: [no_helmet]                                                  │   │
│  │  置信度: 0.6 | 告警条件: 持续3秒后告警                                    │   │
│  ├─────────────────────────────────────────────────────────────────────────┤   │
│  │  能力: 反光衣检测                                                        │   │
│  │  所属模型: yolo_safety_v1                                               │   │
│  │  使用类别: [no_vest]                                                    │   │
│  │  置信度: 0.6 | 告警条件: 立即告警                                        │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
│  摄像头配置层：选择启用哪些检测能力，可覆盖默认参数                                │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │  摄像头: 车间入口-01                                                     │   │
│  │  ├── 人员入侵检测 (置信度: 0.5, 区域: 已配置)                            │   │
│  │  └── 安全帽检测 (置信度: 0.7, 区域: 全画面)  ← 覆盖了默认置信度            │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 10.3 数据库模型

```sql
-- 模型表 (物理模型文件)
CREATE TABLE models (
    id              SERIAL PRIMARY KEY,
    code            VARCHAR(50) UNIQUE NOT NULL,    -- 唯一标识
    name            VARCHAR(100) NOT NULL,          -- 显示名称
    model_type      VARCHAR(20) NOT NULL,           -- YOLO / ResNet / Custom
    model_path      VARCHAR(500) NOT NULL,          -- 模型文件路径
    classes         JSONB NOT NULL,                 -- 支持的类别 ["person", "helmet", ...]
    gpu_memory_mb   INT,                            -- 预估显存占用
    inference_ms    INT,                            -- 预估推理时间
    is_enabled      BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- 检测能力表 (业务检测场景)
CREATE TABLE algorithms (
    id                  SERIAL PRIMARY KEY,
    code                VARCHAR(50) UNIQUE NOT NULL,    -- 唯一标识
    name                VARCHAR(100) NOT NULL,          -- 显示名称
    model_id            INT REFERENCES models(id),      -- 关联模型
    target_classes      JSONB NOT NULL,                 -- 使用哪些类别 ["person"]
    default_confidence  FLOAT DEFAULT 0.5,              -- 默认置信度阈值
    alert_config        JSONB,                          -- 告警配置
    is_enabled          BOOLEAN DEFAULT TRUE,
    created_at          TIMESTAMP DEFAULT NOW()
);

-- 摄像头-算法配置表
CREATE TABLE camera_algorithms (
    id              SERIAL PRIMARY KEY,
    camera_id       INT REFERENCES cameras(id),
    algorithm_id    INT REFERENCES algorithms(id),
    confidence      FLOAT,                          -- 覆盖默认置信度 (可选)
    alert_config    JSONB,                          -- 覆盖默认告警配置 (可选)
    regions         JSONB,                          -- 检测区域 (多边形坐标)
    is_enabled      BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT NOW(),
    UNIQUE(camera_id, algorithm_id)
);
```

### 10.4 告警配置结构

```json
{
    "trigger_type": "instant",     // instant(立即) / duration(持续) / count(计数)
    "duration_seconds": 0,         // 持续 N 秒才告警
    "count_threshold": 0,          // 检测到 N 个才告警
    "cooldown_seconds": 30,        // 告警冷却时间
    "alert_level": "warning"       // info / warning / danger
}
```

**示例配置：**

| 检测能力 | 告警配置 | 说明 |
|----------|----------|------|
| 人员入侵 | instant, cooldown=30s | 检测到立即告警 |
| 安全帽检测 | duration=3s, cooldown=60s | 持续3秒未戴帽才告警，避免误报 |
| 人员聚集 | count>=5, duration=10s | 5人以上聚集超过10秒才告警 |

### 10.5 推理服务处理逻辑

```python
def process_inference(frame, camera_config):
    """
    1. 根据摄像头配置的算法，确定需要哪些模型
    2. 每个模型只推理一次，得到所有类别的检测结果
    3. 按算法配置过滤和分发结果
    """
    
    # 示例: 摄像头配置了 人员入侵 + 安全帽检测
    # 两个算法都用 yolo_safety_v1 模型
    
    # 步骤1: 模型只推理一次
    all_detections = yolo_model.detect(frame)
    # 返回: [
    #   {label: "person", conf: 0.9, bbox: [...]},
    #   {label: "no_helmet", conf: 0.7, bbox: [...]},
    #   {label: "helmet", conf: 0.8, bbox: [...]},
    # ]
    
    # 步骤2: 按算法配置分发结果
    results = {}
    
    for algo_config in camera_config.algorithms:
        algo_detections = []
        for det in all_detections:
            # 检查类别是否匹配
            if det["label"] in algo_config.target_classes:
                # 检查置信度是否达标
                if det["conf"] >= algo_config.confidence:
                    # 检查是否在检测区域内 (如果配置了区域)
                    if is_in_region(det["bbox"], algo_config.regions):
                        algo_detections.append(det)
        
        results[algo_config.code] = algo_detections
    
    return results
```

### 10.6 设计优势

| 优势 | 说明 |
|------|------|
| 模型复用 | 同一模型文件只加载一次，多个检测能力共享 |
| 配置灵活 | 每个检测能力独立配置置信度、告警条件 |
| 易于扩展 | 新增检测能力只需配置，无需改代码 |
| 更新简单 | 模型更新只改一处，所有关联能力自动生效 |
| 摄像头级覆盖 | 可针对特定摄像头调整参数 |

---

## 十一、待确认事项

1. **跳帧策略**: 每几帧推理一次？不同算法是否不同？
2. **告警去重时间窗口**: 30秒是否合适？
3. **是否需要告警截图/录像**: 告警时保存图片或视频片段？
4. **消息推送渠道**: 邮件、钉钉、微信、短信？
5. **多机部署**: 是否需要考虑？如需要，推理服务可改用 Redis 队列
