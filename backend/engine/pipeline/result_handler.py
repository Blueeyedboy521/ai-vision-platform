# -*- coding: utf-8 -*-
"""
结果处理线程

处理 AI 推理结果，执行以下操作：
1. 清洗推理结果，推送给 StreamWriter 用于实时绘框（方案A）
2. 触发告警并存储（预留）
3. 推送实时消息（预留）
"""
import threading
import time
from typing import Any, Dict, List, Optional
from queue import Empty

from loguru import logger

from .overlay_state import OverlayState
from engine.utils.region import RegionDetector
import uuid
class ResultHandler:
    """
    结果处理线程
    
    负责:
    - 从结果队列获取推理结果
    - 绘制检测框
    - 生成告警
    - 推送消息
    """
    
    def __init__(
        self,
        camera_id: str,
        camera_name: str,
        result_queue: Any,
        algorithms: List[dict],
        overlay_state: OverlayState,
        alarm_queue: Optional[Any] = None,
    ):
        """
        初始化 ResultHandler
        
        Args:
            camera_id: 摄像头 ID
            result_queue: 推理结果队列
            algorithms: 算法配置列表
            overlay_state: 推送给 StreamWriter 的最新绘框状态（update 内深拷贝）
        """
        self.camera_id = camera_id
        self.camera_name = camera_name
        self.result_queue = result_queue
        self.algorithms = algorithms
        self.overlay_state = overlay_state
        
        self.thread: Optional[threading.Thread] = None
        self.running = False
        
        # 告警去重
        self.recent_alarms: Dict[str, float] = {}  # alarm_key -> timestamp
        self.dedup_window = 10.0  # 去重窗口 (秒)
        # 告警输出队列（交给 Scheduler 统一写入 Redis alarm_queue）
        self.alarm_queue = alarm_queue
        # 上一次用于比对的检测快照（用于 3 秒窗口内的结果对比）
        self._last_snapshot: Optional[Dict[str, Any]] = None
        
        # 统计
        self.processed_results = 0
        self.generated_alarms = 0
        self.pushed_frames = 0
    
    def start(self):
        """启动结果处理"""
        logger.info(f"ResultHandler 启动: {self.camera_id}")
        self.running = True
        
        self.thread = threading.Thread(target=self._process_loop, daemon=True)
        self.thread.start()
    
    def stop(self):
        """停止结果处理"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info(f"ResultHandler 已停止: {self.camera_id}")
    
    def _process_loop(self):
        """处理循环"""
        logger.debug(f"ResultHandler 进入处理循环: {self.camera_id}")
        
        while self.running:
            try:
                # 获取推理结果
                try:
                    result = self.result_queue.get(timeout=0.04)
                except Empty:
                    continue
                
                if result is None:
                    continue
                
                self.processed_results += 1

                frame_id = getattr(result, "frame_id", None)
                detections = result.detections if hasattr(result, "detections") else []

                # 方案A：写入 overlay_state（内部分深拷贝，result 销毁后 Writer 仍可读）
                try:
                    self.overlay_state.update(frame_id=frame_id, detections=detections)
                except Exception:
                    pass
                self.pushed_frames += 1

                # 在不阻塞实时绘框链路的前提下，执行结果清洗与告警判定
                try:
                    cleaned = self._clean_detections(result, detections)
                    if cleaned:
                        self._maybe_raise_alarm(result, cleaned)
                except Exception as e:
                    logger.error(f"ResultHandler 告警清洗异常: {e}")
                
            except Exception as e:
                logger.error(f"ResultHandler 异常: {e}")
    
    def _get_color_by_class(self, class_name: str) -> tuple:
        """根据类别获取颜色"""
        # 告警类别使用红色
        alarm_classes = ["no_helmet", "no_vest", "fire", "smoke", "intrusion"]
        if class_name.lower() in alarm_classes:
            return (0, 0, 255)  # BGR 红色
        
        # 正常类别使用绿色
        return (0, 255, 0)  # BGR 绿色

    # ==== 新增：检测结果清洗与告警判定 ====

    def _clean_detections(self, result: Any, detections: List[dict]) -> List[dict]:
        """
        按摄像头/算法配置对检测结果做一级清洗：
        1. 置信度阈值过滤（按算法维度：每个 detection 尽量使用其对应算法的 confidence）
        2. 区域过滤（若配置了检测区域，仅保留在任一区域内的目标）
        """
        if not detections:
            return []

        # 1. 置信度阈值：从 camera_algorithms 配置中提取（按算法维度）
        #   self.algorithms 结构示例：
        #   {"id": algorithm_id, "model_id": ..., "config": {"confidence": ..., "alert_config": ..., "regions": ...}}
        algo_thresholds: Dict[str, float] = {}
        default_threshold = 0.5
        for algo in self.algorithms or []:
            try:
                algo_id = str((algo or {}).get("id") or "")
                cfg = (algo or {}).get("config") or {}
                conf = cfg.get("confidence")
                if algo_id and isinstance(conf, (int, float)) and conf > 0:
                    algo_thresholds[algo_id] = float(conf)
                    if default_threshold > float(conf):
                        default_threshold = float(conf)
            except Exception:
                continue

        filtered: List[dict] = []
        for d in detections:
            conf = float(d.get("confidence", 0.0))
            algo_id = d.get("algorithm_id")
            # 优先使用 detection 上的 algorithm_id 找到专属阈值；否则退回到默认阈值
            thr = algo_thresholds.get(str(algo_id), default_threshold)
            if conf >= thr:
                filtered.append(d)

        # 2. 区域过滤：若任一算法配置了 regions，则仅保留在这些区域内的目标
        regions = []
        for algo in self.algorithms or []:
            cfg = (algo or {}).get("config") or {}
            for reg in cfg.get("regions") or []:
                # 约定: reg = {"points": [{"x":0.1,"y":0.2}, ...]} 或 [[x,y],...]
                pts = reg.get("points") if isinstance(reg, dict) else reg
                if not pts:
                    continue
                norm_points = []
                for p in pts:
                    if isinstance(p, dict):
                        x, y = p.get("x"), p.get("y")
                    elif isinstance(p, (list, tuple)) and len(p) >= 2:
                        x, y = p[0], p[1]
                    else:
                        continue
                    try:
                        norm_points.append((float(x), float(y)))
                    except Exception:
                        continue
                if len(norm_points) >= 3:
                    regions.append(norm_points)

        if not regions:
            return filtered

        # 假设 bbox 与区域点使用同一坐标系（若为归一化坐标，需在上游统一）
        detectors = [RegionDetector(polygon=pts) for pts in regions]
        result2: List[dict] = []
        for d in filtered:
            bbox = d.get("bbox") or []
            if len(bbox) < 4:
                continue
            x1, y1, x2, y2 = bbox[:4]
            keep = False
            for det in detectors:
                if det.bbox_in_region((x1, y1, x2, y2), mode="center"):
                    keep = True
                    break
            if keep:
                result2.append(d)

        return result2

    def _maybe_raise_alarm(self, result: Any, detections: List[dict]) -> None:
        """
        基于最近一次快照对比判断是否生成有效告警：
        1. 检测数量变化（len 不同）
        2. 检测类别集合变化（class_names 不同）
        3. 在 3 秒窗口内，同名目标的位置偏移较大（IoU 低于阈值）
        """
        if not detections or self.alarm_queue is None:
            return

        now_ts = float(getattr(result, "timestamp", time.time()))
        prev = self._last_snapshot

        # 若无历史快照，直接视为有效告警并更新快照
        if prev is None or now_ts - prev.get("timestamp", 0) >= 3.0:
            is_alarm = False
            prev_dets = (prev or {}).get("detections", [])

            if not prev_dets:
                is_alarm = True
            elif len(detections) != len(prev_dets):
                is_alarm = True
            else:
                names_now = sorted(d.get("class_name", "") for d in detections)
                names_prev = sorted(d.get("class_name", "") for d in prev_dets)
                if names_now != names_prev:
                    is_alarm = True
                else:
                    # 比较同名目标的框偏移：IoU 低说明偏移大
                    iou_threshold = 0.3
                    for cls in set(names_now):
                        now_box = self._first_bbox_by_class(detections, cls)
                        prev_box = self._first_bbox_by_class(prev_dets, cls)
                        if not now_box or not prev_box:
                            continue
                        iou = self._calculate_iou(now_box, prev_box)
                        if iou < iou_threshold:
                            is_alarm = True
                            break

            if is_alarm:
                self._emit_alarm(result, detections, now_ts)
                self._last_snapshot = {"timestamp": now_ts, "detections": list(detections)}

    def _first_bbox_by_class(self, detections: List[dict], class_name: str) -> Optional[tuple]:
        for d in detections:
            if d.get("class_name") != class_name:
                continue
            bbox = d.get("bbox") or []
            if len(bbox) >= 4:
                return tuple(bbox[:4])
        return None

    def _calculate_iou(self, bbox1: tuple, bbox2: tuple) -> float:
        x1 = max(bbox1[0], bbox2[0])
        y1 = max(bbox1[1], bbox2[1])
        x2 = min(bbox1[2], bbox2[2])
        y2 = min(bbox1[3], bbox2[3])
        if x2 <= x1 or y2 <= y1:
            return 0.0
        inter = (x2 - x1) * (y2 - y1)
        area1 = (bbox1[2] - bbox1[0]) * (bbox1[3] - bbox1[1])
        area2 = (bbox2[2] - bbox2[0]) * (bbox2[3] - bbox2[1])
        union = area1 + area2 - inter
        if union <= 0:
            return 0.0
        return inter / union

    def _emit_alarm(self, result: Any, detections: List[dict], ts: float) -> None:
        """
        组装清洗后的告警数据，并写入 Engine 内部告警队列，后续由 Scheduler 写 Redis。
        同时在本地/对象存储中保存截图（使用 StorageInterface.save_image）。
        """
        try:
            frame = getattr(result, "frame", None)
        except Exception:
            frame = None
        # alarm_id = 32位uuid字符串
        alarm_id = uuid.uuid4().hex
        # 1. 先将截图保存到本地临时目录：LOCAL_STORAGE_PATH + '/alarm/camera/{camera_id}.jpg'
        local_snapshot_path = None
        if frame is not None:
            try:
                import os
                import cv2
                from config.settings import settings

                base_dir = getattr(settings, "LOCAL_STORAGE_PATH", ".")
                temp_dir = os.path.join(base_dir, "alarm", "camera")
                os.makedirs(temp_dir, exist_ok=True)
                # 临时文件命名：每路摄像头一个文件，始终覆盖为最新一帧
                filename = f"{alarm_id}.jpg"
                local_snapshot_path = os.path.join(temp_dir, filename)
                cv2.imwrite(local_snapshot_path, frame)
            except Exception as e:
                logger.error(f"保存本地告警截图失败: camera_id={self.camera_id}, err={e}")

        # 取第一个算法作为主算法（后续可扩展为按 detection 关联）
        algo = (self.algorithms or [None])[0] or {}
        algorithm_id = algo.get("id")
        # 从检测结果中尽量获取更友好的算法名称与代码（比如 algo_name / class_name）
        first_det = (detections or [None])[0] or {}
        algorithm_name = first_det.get("algo_name") or ""
        algorithm_code = first_det.get("class_name") or ""
        # 额外输出模型维度与告警配置，便于前端展示与筛选
        model_id = algo.get("model_id")
        cfg = (algo or {}).get("config") or {}
        alert_config = cfg.get("alert_config") or {}
        regions = cfg.get("regions") or []

        from datetime import datetime
        alarm_data = {
            "alarm_id": alarm_id,
            "camera_id": self.camera_id,
            "camera_name": self.camera_name,
            "algorithm_id": algorithm_id,
            "algorithm_name": algorithm_name,
            "algorithm_code": algorithm_code,
            "model_id": model_id,
            "alert_level": "info",
            "description": "",
            "timestamp": datetime.fromtimestamp(ts).isoformat(),
            "detections": detections,
            # 本地临时截图路径，由 Scheduler 的告警转发线程上传到正式存储目录后再写入 snapshot_path
            "local_snapshot_path": local_snapshot_path,
            # 告警配置与区域信息直接透出，前端可用于渲染与过滤
            "alert_config": alert_config,
            "regions": regions,
        }
        logger.info(f"摄像头 {self.camera_id} 生成告警: {alarm_data}")
        try:
            self.alarm_queue.put_nowait(alarm_data)
        except Exception as e:
            logger.error(f"写入 Engine 告警队列失败: {e}")
    
    def _process_alarms(self, detections: list, frame):
        """处理告警"""
        current_time = time.time()
        
        # 清理过期的去重记录
        self._cleanup_dedup_records(current_time)
        
        for det in detections:
            class_name = det.get("class_name", "")
            confidence = det.get("confidence", 0)
            
            # 检查是否触发告警
            if not self._should_trigger_alarm(class_name, confidence):
                continue
            
            # 去重检查
            alarm_key = f"{self.camera_id}_{class_name}"
            if alarm_key in self.recent_alarms:
                continue
            
            # 记录告警
            self.recent_alarms[alarm_key] = current_time
            self.generated_alarms += 1
            
            # 生成告警
            alarm_data = {
                "camera_id": self.camera_id,
                "algorithm_name": class_name,
                "confidence": confidence,
                "bbox": det.get("bbox"),
                "timestamp": current_time
            }
            
            # TODO: 保存告警截图
            # TODO: 存储到数据库
            # TODO: 推送到 Redis
            
            logger.info(f"生成告警: {alarm_data}")
    
    def _should_trigger_alarm(self, class_name: str, confidence: float) -> bool:
        """检查是否应该触发告警"""
        # 告警类别列表
        alarm_classes = ["no_helmet", "no_vest", "fire", "smoke", "intrusion"]
        
        if class_name.lower() not in alarm_classes:
            return False
        
        # 置信度阈值
        if confidence < 0.5:
            return False
        
        return True
    
    def _cleanup_dedup_records(self, current_time: float):
        """清理过期的去重记录"""
        expired_keys = [
            key for key, timestamp in self.recent_alarms.items()
            if current_time - timestamp > self.dedup_window
        ]
        for key in expired_keys:
            del self.recent_alarms[key]
    
    def _push_realtime_message(self, detections: list):
        """推送实时消息"""
        # TODO: 通过 Redis Pub/Sub 推送
        pass
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        return {
            "processed_results": self.processed_results,
            "generated_alarms": self.generated_alarms,
            "pushed_frames": self.pushed_frames
        }
