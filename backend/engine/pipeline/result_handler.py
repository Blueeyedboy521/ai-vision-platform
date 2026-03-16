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
from .alert import get_trigger
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
        
        # 告警去重（遗留结构，当前主要依赖各算法 Trigger 内部状态）
        self.recent_alarms: Dict[str, float] = {}  # alarm_key -> timestamp
        self.dedup_window = 10.0  # 去重窗口 (秒)
        # 告警输出队列（交给 Scheduler 统一写入 Redis alarm_queue）
        self.alarm_queue = alarm_queue

        # 告警触发策略（算法级别）：algo_id -> alert_config / trigger
        self._algo_alert_configs: Dict[str, Dict[str, Any]] = {}
        self._algo_triggers: Dict[str, Any] = {}
        for a in algorithms or []:
            algo_id = str((a or {}).get("id") or "")
            if not algo_id:
                continue
            base_cfg = (a.get("config") or {})
            alert_cfg = dict(base_cfg.get("alert_config") or {})
            # 将算法级告警间隔透传给 Trigger，由各自策略内部维护节流状态
            if "alarm_interval_sec" not in alert_cfg:
                alert_cfg["alarm_interval_sec"] = float(
                    base_cfg.get("alarm_interval_sec", 30.0)
                )
            self._algo_alert_configs[algo_id] = alert_cfg
            trigger_type = (alert_cfg.get("trigger_type") or "instant").strip().lower()
            self._algo_triggers[algo_id] = get_trigger(trigger_type, alert_cfg)
        # 默认触发器：当某个算法未配置 alert_config 时使用
        self._default_trigger = get_trigger("instant", {})

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
                    logger.info(f"ResultHandler 清洗后的检测结果: {cleaned}")
                    if cleaned:
                        self._maybe_raise_alarm(result, cleaned)
                        pass
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

    def _filter_by_algorithm_and_confidence(self, detections: List[dict]) -> List[dict]:
        """
        第一步：按摄像头配置的算法列表和置信度阈值做过滤。

        仅保留：
        - algorithm_id 在当前摄像头启用算法列表中的检测结果；
        - 且 detection.confidence ≥ 对应算法配置的 confidence（若未配置则跳过该算法）。
        """
        if not detections:
            return []

        algo_thresholds: Dict[str, float] = {}
        enabled_algo_ids: set[str] = set()
        for algo in self.algorithms or []:
            try:
                algo_id = str((algo or {}).get("id") or "")
                if not algo_id:
                    continue
                enabled_algo_ids.add(algo_id)
                cfg = (algo or {}).get("config") or {}
                conf = cfg.get("confidence")
                if isinstance(conf, (int, float)) and conf > 0:
                    algo_thresholds[algo_id] = float(conf)
            except Exception:
                continue
        # logger.debug( f"[ResultHandler] algo_thresholds={algo_thresholds}, enabled_algo_ids={enabled_algo_ids}, "  f"detections={detections}" )

        filtered: List[dict] = []
        for d in detections:
            conf = float(d.get("confidence", 0.0))
            algo_id_raw = d.get("algorithm_id")
            algo_id = str(algo_id_raw) if algo_id_raw is not None else ""
            # 仅保留在当前摄像头启用算法列表里的检测结果
            if enabled_algo_ids and algo_id and algo_id not in enabled_algo_ids:
                continue
            thr = algo_thresholds.get(algo_id)
            if thr is not None and conf >= thr:
                filtered.append(d)

        # logger.debug(f"[ResultHandler] after threshold filter: {filtered}")
        return filtered

    def _filter_by_regions(self, detections: List[dict]) -> List[dict]:
        """
        第二步：按算法维度进行区域过滤。

        - 每个算法有自己的 regions 列表；
        - detection 按其 algorithm_id 找到对应算法的区域，采用 bbox 与区域「有交叉即可」的模式。
        """
        if not detections:
            return []

        # regions_by_algo: algorithm_id -> list of polygons (每个 polygon 为 (x,y) 元组列表)
        regions_by_algo: Dict[str, List[List[tuple]]] = {}
        for algo in self.algorithms or []:
            algo_id = str((algo or {}).get("id") or "")
            if not algo_id:
                continue
            cfg = (algo or {}).get("config") or {}
            polygons: List[List[tuple]] = []
            for reg in cfg.get("regions") or []:
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
                    polygons.append(norm_points)
            if polygons:
                regions_by_algo[algo_id] = polygons

        if not regions_by_algo:
            return detections

        # logger.debug(f"[ResultHandler] regions_by_algo: {regions_by_algo}")
        # 每个 detection 按其 algorithm_id 取对应算法的区域做过滤
        result2: List[dict] = []
        for d in detections:
            bbox = d.get("bbox") or []
            if len(bbox) < 4:
                continue
            algo_id = str(d.get("algorithm_id") or "")
            regions = regions_by_algo.get(algo_id) if algo_id else None
            if not regions:
                # 该算法未配置区域或 detection 无 algorithm_id，保留
                result2.append(d)
                continue
            x1, y1, x2, y2 = bbox[:4]
            keep = False
            for polygon in regions:
                det = RegionDetector(polygon=polygon)
                # 默认使用 bbox 与区域有交集的模式
                if det.bbox_in_region((x1, y1, x2, y2), mode="intersect"):
                    keep = True
                    break
            if keep:
                result2.append(d)

        return result2

    def _clean_detections(self, result: Any, detections: List[dict]) -> List[dict]:
        """
        按摄像头/算法配置对检测结果做两步清洗：
        1. 置信度 + 算法列表过滤；
        2. 区域过滤（若配置了检测区域，仅保留与区域有交叉的目标）。
        """
        if not detections:
            return []

        step1 = self._filter_by_algorithm_and_confidence(detections)
        if not step1:
            return []

        return self._filter_by_regions(step1)

    def _maybe_raise_alarm(self, result: Any, detections: List[dict]) -> None:
        """
        告警判定：由 alert 包按 trigger_type 策略判断是否应触发；
        告警间隔等状态全部由各算法 Trigger 内部维护，这里仅负责按算法分组与多算法快照复用。
        """
        if not detections or self.alarm_queue is None:
            return

        now_ts = float(getattr(result, "timestamp", time.time()))

        # 按算法级别的告警策略判断是否需要触发：
        # 先按 algorithm_id 分组 detections，再为每个算法调用其 Trigger。
        grouped: Dict[str, List[dict]] = {}
        for d in detections:
            algo_id_raw = d.get("algorithm_id")
            algo_id = str(algo_id_raw) if algo_id_raw is not None else ""
            if not algo_id:
                continue
            grouped.setdefault(algo_id, []).append(d)

        # 逐算法执行触发判断，收集最终需要发出的算法告警列表
        alarms_to_emit: List[Dict[str, Any]] = []
        for algo_id, dets in grouped.items():
            trigger = self._algo_triggers.get(algo_id, self._default_trigger)
            try:
                should_raise = trigger.should_raise(dets, now_ts)
                logger.info(f"算法 {algo_id} 告警触发判断: {should_raise}，now_ts: {now_ts}，detections: {dets}")
                if not should_raise:
                    continue

                alarms_to_emit.append(
                    {
                        "algorithm_id": algo_id,
                        "detections": dets,
                    }
                )
            except Exception as e:
                logger.error(f"算法 {algo_id} 告警触发判断异常: {e}")

        if not alarms_to_emit:
            return

        # 计算同一帧中算法告警数量，用于后续 Snapshot 上传去重
        ref_total = len(alarms_to_emit)

        # 统一抓取一份本地截图，供多算法告警复用
        local_snapshot_path = self._save_local_snapshot(result)

        # 逐算法输出告警
        for item in alarms_to_emit:
            algo_id = item["algorithm_id"]
            dets = item["detections"]
            self._emit_alarm(
                result=result,
                detections=dets,
                ts=now_ts,
                ref_total=ref_total,
                local_snapshot_path=local_snapshot_path,
            )

    def _save_local_snapshot(self, result: Any) -> Optional[str]:
        """
        从当前推理结果中抓取一份截图并保存到本地临时目录。
        返回 local_snapshot_path，失败时返回 None。
        """
        try:
            frame = getattr(result, "frame", None)
        except Exception:
            frame = None
        if frame is None:
            return None

        try:
            import os
            import cv2
            from config.settings import settings
            import uuid as _uuid

            base_dir = getattr(settings, "LOCAL_STORAGE_PATH", ".")
            temp_dir = os.path.join(base_dir, "alarm", "camera")
            os.makedirs(temp_dir, exist_ok=True)
            filename = f"{_uuid.uuid4().hex}.jpg"
            local_path = os.path.join(temp_dir, filename)
            cv2.imwrite(local_path, frame)
            return local_path
        except Exception as e:
            logger.error(f"保存本地告警截图失败: camera_id={self.camera_id}, err={e}")
            return None

    def _emit_alarm(
        self,
        result: Any,
        detections: List[dict],
        ts: float,
        ref_total: int = 1,
        local_snapshot_path: Optional[str] = None,
    ) -> None:
        """
        组装清洗后的告警数据，并写入 Engine 内部告警队列，后续由 Scheduler 写 Redis。
        同时在本地/对象存储中保存截图（使用 StorageInterface.save_image）。
        """
        # alarm_id = 32位uuid字符串
        alarm_id = uuid.uuid4().hex

        # 取当前告警主算法：优先从检测结果的 algorithm_id 找到对应算法配置
        first_det = (detections or [None])[0] or {}
        det_algo_id = first_det.get("algorithm_id")
        algorithm_id: Optional[str] = None
        model_id: Optional[str] = None
        cfg: Dict[str, Any] = {}
        if det_algo_id:
            algo_id_str = str(det_algo_id)
            for a in self.algorithms or []:
                # a:{'id': '9110c2491b6a47969b5a13b642c4226b', 'model_id': 'c130d645e3094936ad852d93449d1c21', 'config': {'confidence': 0.6, 'alert_config': {'trigger_type': 'instant', 'duration_seconds': 0, 'count_threshold': 0, 'cooldown_seconds': 30, 'alert_level': 'critical'}, 'regions': [], 'inference_interval_sec': 5, 'alarm_interval_sec': 30}}
                if str((a or {}).get("id") or "") == algo_id_str:
                    algorithm_id = algo_id_str
                    model_id = (a or {}).get("model_id")
                    cfg = a.get("config") or {}
                    break
        logger.info(f"algorithm_id: {algorithm_id}, cfg: {cfg} ")
        # 从检测结果中尽量获取更友好的算法名称与代码（比如 algo_name / class_name）
        algorithm_name = first_det.get("algo_name") or ""
        algorithm_code = first_det.get("class_name") or ""
        # 额外输出模型维度与告警配置，便于前端展示与筛选
        alert_config = cfg.get("alert_config") or {}
        regions = cfg.get("regions") or []
        alert_level = alert_config.get("alert_level") 
        from datetime import datetime
        alarm_data = {
            "alarm_id": alarm_id,
            "camera_id": self.camera_id,
            "camera_name": self.camera_name,
            "algorithm_id": algorithm_id,
            "algorithm_name": algorithm_name,
            "algorithm_code": algorithm_code,
            "model_id": model_id,
            "alert_level": alert_level,
            "description": "",
            "timestamp": datetime.fromtimestamp(ts).isoformat(),
            "detections": detections,
            # 本地临时截图路径，由 Scheduler 的告警转发线程上传到正式存储目录后再写入 snapshot_path
            "local_snapshot_path": local_snapshot_path,
            # 同一 local_snapshot_path 预计会被引用的次数（多算法时用于上传去重与本地文件回收）
            "local_snapshot_ref_total": max(1, int(ref_total)),
            # 告警配置与区域信息直接透出，前端可用于渲染与过滤
            # "alert_config": alert_config,
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
