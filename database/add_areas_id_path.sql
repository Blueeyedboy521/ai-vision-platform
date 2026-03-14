-- 区域表增加 id_path（ID 层级路径），用于策略区域匹配
-- 执行后需运行应用启动期 fix_area_hierarchy 回填 id_path，或由区域增改时 compute_hierarchy 自动维护

ALTER TABLE areas
ADD COLUMN id_path VARCHAR(1000) DEFAULT NULL COMMENT 'ID层级路径，如 /root_id/1/1.1' AFTER hierarchy_path;

CREATE INDEX idx_id_path ON areas (id_path(255));
