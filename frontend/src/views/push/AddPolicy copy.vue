<template>
  <div class="max-w-6xl mx-auto px-6 py-10">
    <!-- Header -->
    <div class="flex items-center justify-between mb-8">
      <div>
        <h1 class="text-3xl font-bold tracking-tight text-slate-900">新增报警策略</h1>
        <p class="text-slate-500 mt-2">配置告警识别逻辑、区域过滤与多渠道自动化推送规则</p>
      </div>
      <div class="flex items-center gap-3">
        <button class="px-6 py-2.5 text-sm font-semibold text-slate-600 bg-white border border-slate-200 hover:bg-slate-50 transition-colors rounded-lg">取消</button>
        <button class="px-6 py-2.5 text-sm font-semibold text-white bg-primary hover:bg-primary/90 shadow-lg shadow-primary/20 transition-all rounded-lg">保存并启用</button>
      </div>
    </div>

    <div class="space-y-8 pb-10">
      <!-- Section 1: Basic Config -->
      <section class="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <div class="px-6 py-4 border-b border-slate-100 bg-slate-50 flex items-center gap-2 text-primary">
          <span class="material-symbols-outlined text-xl">settings</span>
          <h3 class="font-bold">基础信息</h3>
        </div>
        <div class="p-6">
          <div class="grid grid-cols-12 gap-6">
            <div class="col-span-12 md:col-span-3 space-y-1.5">
              <label class="text-xs font-bold text-slate-500 uppercase tracking-wider">策略 ID</label>
              <input class="w-full bg-slate-100 border-transparent text-slate-500 rounded-lg px-4 py-2.5 cursor-not-allowed outline-none text-sm" readonly type="text" value="STRAT-20231024-001"/>
            </div>
            <div class="col-span-12 md:col-span-5 space-y-1.5">
              <label class="text-xs font-bold text-slate-500 uppercase tracking-wider">策略名称 <span class="text-red-500">*</span></label>
              <input class="w-full bg-white border border-slate-200 rounded-lg px-4 py-2.5 focus:border-primary focus:ring-4 focus:ring-primary/5 transition-all outline-none text-sm" placeholder="例如：涂装车间火灾/烟雾告警策略" type="text"/>
            </div>
            <div class="col-span-6 md:col-span-2 space-y-1.5">
              <label class="text-xs font-bold text-slate-500 uppercase tracking-wider">优先级</label>
              <select class="w-full bg-white border border-slate-200 rounded-lg px-4 py-2.5 focus:border-primary outline-none text-sm appearance-none">
                <option>1 (最高)</option>
                <option>2</option>
                <option>3</option>
                <option>4</option>
                <option>5 (最低)</option>
              </select>
            </div>
            <div class="col-span-6 md:col-span-2 space-y-1.5">
              <label class="text-xs font-bold text-slate-500 uppercase tracking-wider">当前状态</label>
              <div class="flex items-center h-[42px]">
                <label class="relative inline-flex items-center cursor-pointer">
                  <input checked class="sr-only peer" type="checkbox" value=""/>
                  <div class="w-11 h-6 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                  <span class="ms-3 text-sm font-medium text-slate-700">启用</span>
                </label>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Section 2: Trigger Rules -->
      <section class="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <div class="px-6 py-4 border-b border-slate-100 bg-slate-50 flex items-center gap-2 text-primary">
          <span class="material-symbols-outlined text-xl">rule</span>
          <h3 class="font-bold">触发规则</h3>
        </div>
        <div class="p-6 space-y-8">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-8">
            <!-- Left Col -->
            <div class="space-y-6">
              <div class="space-y-2">
                <label class="text-xs font-bold text-slate-500">告警类别</label>
                <div class="flex gap-2">
                  <button class="px-5 py-1.5 rounded-lg border border-primary bg-primary text-white text-sm font-medium">AI告警</button>
                  <button class="px-5 py-1.5 rounded-lg border border-slate-200 bg-white text-slate-600 hover:border-slate-300 text-sm font-medium">系统告警</button>
                </div>
              </div>
              <div class="space-y-2">
                <label class="text-xs font-bold text-slate-500">报警类型 (多选)</label>
                <div class="p-2 border border-slate-200 rounded-lg bg-slate-50/30 flex flex-wrap gap-2 min-h-[46px] items-center">
                  <span class="px-2.5 py-1 bg-white border border-slate-200 rounded-md text-xs flex items-center gap-2">火灾识别 <button class="material-symbols-outlined text-sm hover:text-red-500">close</button></span>
                  <span class="px-2.5 py-1 bg-white border border-slate-200 rounded-md text-xs flex items-center gap-2">烟雾检测 <button class="material-symbols-outlined text-sm hover:text-red-500">close</button></span>
                  <button class="px-2.5 py-1 border border-dashed border-primary text-primary hover:bg-primary/5 rounded-md text-xs flex items-center gap-1">
                    <span class="material-symbols-outlined text-sm">add</span> 添加
                  </button>
                </div>
              </div>
              <div class="space-y-2">
                <label class="text-xs font-bold text-slate-500">区域路径 (支持通配符)</label>
                <div class="p-2 border border-slate-200 rounded-lg bg-slate-50/30 flex flex-wrap gap-2 min-h-[46px] items-center">
                  <span class="px-2.5 py-1 bg-white border border-slate-200 rounded-md text-xs flex items-center gap-2">/一分厂/冲压/A1* <button class="material-symbols-outlined text-sm hover:text-red-500">close</button></span>
                  <button class="px-2.5 py-1 border border-dashed border-primary text-primary hover:bg-primary/5 rounded-md text-xs flex items-center gap-1">
                    <span class="material-symbols-outlined text-sm">add</span> 添加
                  </button>
                </div>
              </div>
              <div class="space-y-2">
                <label class="text-xs font-bold text-slate-500">监控设备 (多选)</label>
                <div class="p-2 border border-slate-200 rounded-lg bg-slate-50/30 flex flex-wrap gap-2 min-h-[46px] items-center">
                  <span class="px-2.5 py-1 bg-white border border-slate-200 rounded-md text-xs flex items-center gap-2">CAM-SOUTH-001 <button class="material-symbols-outlined text-sm hover:text-red-500">close</button></span>
                  <span class="px-2.5 py-1 bg-white border border-slate-200 rounded-md text-xs flex items-center gap-2">CAM-WEST-042 <button class="material-symbols-outlined text-sm hover:text-red-500">close</button></span>
                  <button class="px-2.5 py-1 border border-dashed border-primary text-primary hover:bg-primary/5 rounded-md text-xs flex items-center gap-1">
                    <span class="material-symbols-outlined text-sm">add</span> 添加
                  </button>
                </div>
              </div>
            </div>
            <!-- Right Col -->
            <div class="space-y-6">
              <div class="space-y-2">
                <label class="text-xs font-bold text-slate-500">报警等级过滤</label>
                <div class="flex gap-6 p-1">
                  <label class="flex items-center gap-2 cursor-pointer group">
                    <input checked class="rounded text-red-600 focus:ring-red-500 border-slate-300" type="checkbox"/>
                    <span class="text-sm text-slate-700 group-hover:text-red-600">危险 (Danger)</span>
                  </label>
                  <label class="flex items-center gap-2 cursor-pointer group">
                    <input checked class="rounded text-orange-500 focus:ring-orange-500 border-slate-300" type="checkbox"/>
                    <span class="text-sm text-slate-700 group-hover:text-orange-500">严重 (Critical)</span>
                  </label>
                  <label class="flex items-center gap-2 cursor-pointer group">
                    <input class="rounded text-yellow-500 focus:ring-yellow-500 border-slate-300" type="checkbox"/>
                    <span class="text-sm text-slate-700 group-hover:text-yellow-600">一般 (Warning)</span>
                  </label>
                </div>
              </div>
              <div class="space-y-4">
                <div class="space-y-2">
                  <label class="text-xs font-bold text-slate-500 uppercase tracking-wider">排除区域</label>
                  <div class="p-2 border border-slate-200 rounded-lg bg-slate-50/30 flex flex-wrap gap-2 min-h-[42px] items-center">
                    <span class="px-2 py-0.5 bg-slate-200 text-slate-600 rounded text-[10px] font-bold flex items-center gap-1 uppercase">/DEBUG/* <button class="material-symbols-outlined text-xs hover:text-red-500">close</button></span>
                    <button class="px-2 py-0.5 border border-dashed border-slate-400 text-slate-500 hover:border-primary hover:text-primary rounded text-[10px] font-bold flex items-center gap-1">
                      <span class="material-symbols-outlined text-xs">add</span> 排除路径
                    </button>
                  </div>
                </div>
                <div class="space-y-2">
                  <label class="text-xs font-bold text-slate-500 uppercase tracking-wider">排除设备</label>
                  <div class="p-2 border border-slate-200 rounded-lg bg-slate-50/30 flex flex-wrap gap-2 min-h-[42px] items-center">
                    <span class="px-2 py-0.5 bg-slate-200 text-slate-600 rounded text-[10px] font-bold flex items-center gap-1 uppercase">#CAM-TEST-02 <button class="material-symbols-outlined text-xs hover:text-red-500">close</button></span>
                    <button class="px-2 py-0.5 border border-dashed border-slate-400 text-slate-500 hover:border-primary hover:text-primary rounded text-[10px] font-bold flex items-center gap-1">
                      <span class="material-symbols-outlined text-xs">add</span> 排除 ID
                    </button>
                  </div>
                </div>
              </div>
              <div class="space-y-2">
                <label class="text-xs font-bold text-slate-500">触发时段 (24小时制)</label>
                <div class="flex items-center gap-4 bg-white border border-slate-200 rounded-lg p-2 px-4">
                  <input class="flex-1 text-sm bg-transparent border-none focus:ring-0 p-0" type="time" value="00:00"/>
                  <span class="text-slate-300 font-light">至</span>
                  <input class="flex-1 text-sm bg-transparent border-none focus:ring-0 p-0" type="time" value="23:59"/>
                  <span class="material-symbols-outlined text-slate-400 text-lg">schedule</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Section 3: Push Actions -->
      <section class="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <div class="px-6 py-4 border-b border-slate-100 bg-slate-50 flex items-center justify-between">
          <div class="flex items-center gap-2 text-primary">
            <span class="material-symbols-outlined text-xl">send</span>
            <h3 class="font-bold">推送动作</h3>
          </div>
          <button class="flex items-center gap-1.5 text-xs font-bold text-primary px-3 py-1.5 rounded-lg hover-bg-primary-opacity-5 transition-colors border border-primary-opacity-20 bg-white">
            <span class="material-symbols-outlined text-sm">add</span>
            添加推送配置
          </button>
        </div>
        <div class="p-6 space-y-6">
          <!-- Action Block 1 -->
          <div class="relative p-6 border border-slate-200 bg-slate-50 rounded-xl border-l-4 border-l-primary">
            <button class="absolute top-4 right-4 text-slate-300 hover-text-red-500 transition-colors">
              <span class="material-symbols-outlined">delete</span>
            </button>
            <div class="grid grid-cols-12 gap-8">
              <div class="col-span-12 md:col-span-5 space-y-6">
                <div class="space-y-2">
                  <label class="text-xs font-bold text-slate-500 uppercase tracking-wider">推送渠道 (多选)</label>
                  <div class="p-2 border border-slate-200 rounded-lg bg-white flex flex-wrap gap-2 min-h-[46px] items-center">
                    <span class="px-2.5 py-1 bg-blue-50 text-blue-600 border border-blue-100 rounded-md text-[10px] font-bold flex items-center gap-1"><span class="material-symbols-outlined text-sm">chat</span> 钉钉机器人 <button class="material-symbols-outlined text-xs hover-text-red-500">close</button></span>
                    <span class="px-2.5 py-1 bg-green-50 text-green-600 border border-green-100 rounded-md text-[10px] font-bold flex items-center gap-1"><span class="material-symbols-outlined text-sm">mail</span> 邮件网关 <button class="material-symbols-outlined text-xs hover-text-red-500">close</button></span>
                    <button class="px-2.5 py-1 border border-dashed border-primary text-primary hover-bg-primary-opacity-5 rounded-md text-[10px] font-bold flex items-center gap-1">
                      <span class="material-symbols-outlined text-sm">add</span> 添加渠道
                    </button>
                  </div>
                </div>
                <div class="space-y-2">
                  <label class="text-xs font-bold text-slate-500 uppercase tracking-wider">消息模版</label>
                  <select class="w-full bg-white border border-slate-200 rounded-lg px-4 py-2.5 text-sm focus:border-primary outline-none appearance-none">
                    <option>【紧急】工业园区火灾告警模版 v2</option>
                    <option>【常规】设备运行异常预警</option>
                    <option>自定义模版...</option>
                  </select>
                </div>
              </div>
              <div class="col-span-12 md:col-span-7">
                <div class="grid grid-cols-2 gap-x-6 gap-y-6">
                  <div class="space-y-2">
                    <label class="text-xs font-bold text-slate-500 uppercase tracking-wider">静默时间 (秒)</label>
                    <div class="relative">
                      <input class="w-full bg-white border border-slate-200 rounded-lg px-4 py-2 text-sm focus-border-primary outline-none" type="number" value="300"/>
                      <span class="absolute right-4 top-1-half -translate-y-1-half text-[10px] text-slate-400 font-medium">SECONDS</span>
                    </div>
                    <p class="text-[10px] text-slate-400">相同报警在此时间内不重复发送</p>
                  </div>
                  <div class="space-y-2">
                    <label class="text-xs font-bold text-slate-500 uppercase tracking-wider">去重关键字 (多选下拉)</label>
                    <div class="p-2 border border-slate-200 rounded-lg bg-white flex flex-wrap gap-2 min-h-[40px] items-center">
                      <span class="px-2 py-0.5 bg-slate-100 border border-slate-200 rounded text-[10px] font-mono flex items-center gap-1">camera_id <button class="material-symbols-outlined text-[10px]">close</button></span>
                      <span class="px-2 py-0.5 bg-slate-100 border border-slate-200 rounded text-[10px] font-mono flex items-center gap-1">event_type <button class="material-symbols-outlined text-[10px]">close</button></span>
                      <button class="material-symbols-outlined text-slate-400 ml-auto">expand_more</button>
                    </div>
                    <p class="text-[10px] text-slate-400">用于唯一标识一条报警</p>
                  </div>
                  <div class="space-y-2">
                    <label class="text-xs font-bold text-slate-500 uppercase tracking-wider">发送顺序</label>
                    <input class="w-full bg-white border border-slate-200 rounded-lg px-4 py-2 text-sm focus-border-primary outline-none" type="number" value="1"/>
                    <p class="text-[10px] text-slate-400">数字越小优先级越高</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <!-- Add New Action Trigger -->
          <button class="w-full py-8 border-2 border-dashed border-slate-200 rounded-xl flex flex-col items-center justify-center gap-2 text-slate-400 hover-text-primary hover-border-primary-opacity-50 hover-bg-primary-opacity-5 transition-all group">
            <span class="material-symbols-outlined text-3xl group-hover-scale-110 transition-transform">add_circle</span>
            <span class="text-sm font-semibold">配置备用推送目标</span>
            <span class="text-[10px]">用于配置多级告警链路或备用通知方式</span>
          </button>
        </div>
      </section>
    </div>

    <!-- Actions -->
    <div class="flex items-center justify-end gap-4 mt-8 pb-10">
      <span class="text-xs text-slate-400 italic">所有更改将实时保存为草稿</span>
      <button class="px-8 py-2.5 text-sm font-bold text-white bg-primary rounded-lg shadow-lg shadow-primary-opacity-30 hover-shadow-primary-opacity-40 active-scale-95 transition-all">确认并下发策略</button>
    </div>
  </div>
</template>

<script setup lang="ts">
// 静态页面，无需业务逻辑
</script>

<style scoped>
/* 颜色变量 */
:root {
  --primary: #137fec;
}

/* 页面特定样式 */
body {
  font-family: 'Inter', 'Noto Sans SC', sans-serif;
  background-color: #f8fafc;
  color: #0f172a;
  min-height: 100vh;
}

/* 自定义样式 */
.no-scrollbar::-webkit-scrollbar {
  display: none;
}

input[type="checkbox"]:checked {
  background-image: url("data:image/svg+xml,%3csvg viewBox='0 0 16 16' fill='white' xmlns='http://www.w3.org/2000/svg'%3e%3cpath d='M12.207 4.793a1 1 0 010 1.414l-5 5a1 1 0 01-1.414 0l-2-2a1 1 0 011.414-1.414L6.5 9.086l4.293-4.293a1 1 0 011.414 0z'/%3e%3c/svg%3e");
}

/* 工具类 */
.flex {
  display: flex;
}

.items-center {
  align-items: center;
}

.justify-between {
  justify-content: space-between;
}

.justify-end {
  justify-content: flex-end;
}

.justify-center {
  justify-content: center;
}

.flex-col {
  flex-direction: column;
}

.flex-wrap {
  flex-wrap: wrap;
}

.gap-2 {
  gap: 0.5rem;
}

.gap-3 {
  gap: 0.75rem;
}

.gap-4 {
  gap: 1rem;
}

.gap-6 {
  gap: 1.5rem;
}

.gap-8 {
  gap: 2rem;
}

.gap-12 {
  gap: 3rem;
}

.mb-2 {
  margin-bottom: 0.5rem;
}

.mb-8 {
  margin-bottom: 2rem;
}

.mt-2 {
  margin-top: 0.5rem;
}

.mt-8 {
  margin-top: 2rem;
}

.p-1 {
  padding: 0.25rem;
}

.p-2 {
  padding: 0.5rem;
}

.p-4 {
  padding: 1rem;
}

.p-6 {
  padding: 1.5rem;
}

.p-8 {
  padding: 2rem;
}

.px-3 {
  padding-left: 0.75rem;
  padding-right: 0.75rem;
}

.px-4 {
  padding-left: 1rem;
  padding-right: 1rem;
}

.px-6 {
  padding-left: 1.5rem;
  padding-right: 1.5rem;
}

.py-1 {
  padding-top: 0.25rem;
  padding-bottom: 0.25rem;
}

.py-1.5 {
  padding-top: 0.375rem;
  padding-bottom: 0.375rem;
}

.py-2 {
  padding-top: 0.5rem;
  padding-bottom: 0.5rem;
}

.py-2.5 {
  padding-top: 0.625rem;
  padding-bottom: 0.625rem;
}

.py-4 {
  padding-top: 1rem;
  padding-bottom: 1rem;
}

.py-8 {
  padding-top: 2rem;
  padding-bottom: 2rem;
}

.pb-10 {
  padding-bottom: 2.5rem;
}

.space-y-1.5 {
  space-y: 0.375rem;
}

.space-y-2 {
  space-y: 0.5rem;
}

.space-y-4 {
  space-y: 1rem;
}

.space-y-6 {
  space-y: 1.5rem;
}

.space-y-8 {
  space-y: 2rem;
}

.text-xs {
  font-size: 0.75rem;
  line-height: 1rem;
}

.text-sm {
  font-size: 0.875rem;
  line-height: 1.25rem;
}

.text-3xl {
  font-size: 1.875rem;
  line-height: 2.25rem;
}

.font-bold {
  font-weight: 700;
}

.font-semibold {
  font-weight: 600;
}

.font-medium {
  font-weight: 500;
}

.font-mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
}

.italic {
  font-style: italic;
}

.uppercase {
  text-transform: uppercase;
}

.tracking-wider {
  letter-spacing: 0.05em;
}

.tracking-tight {
  letter-spacing: -0.025em;
}

.text-slate-400 {
  color: #94a3b8;
}

.text-slate-500 {
  color: #64748b;
}

.text-slate-600 {
  color: #475569;
}

.text-slate-700 {
  color: #334155;
}

.text-slate-900 {
  color: #0f172a;
}

.text-primary {
  color: var(--primary);
}

.text-red-500 {
  color: #ef4444;
}

.text-red-600 {
  color: #dc2626;
}

.text-orange-500 {
  color: #f97316;
}

.text-yellow-500 {
  color: #eab308;
}

.text-yellow-600 {
  color: #ca8a04;
}

.text-blue-600 {
  color: #2563eb;
}

.text-green-600 {
  color: #16a34a;
}

.bg-white {
  background-color: #ffffff;
}

.bg-slate-50 {
  background-color: #f8fafc;
}

.bg-slate-100 {
  background-color: #f1f5f9;
}

.bg-slate-200 {
  background-color: #e2e8f0;
}

.bg-primary {
  background-color: var(--primary);
}

.bg-blue-50 {
  background-color: #eff6ff;
}

.bg-green-50 {
  background-color: #ecfdf5;
}

.border {
  border-width: 1px;
}

.border-2 {
  border-width: 2px;
}

.border-slate-200 {
  border-color: #e2e8f0;
}

.border-slate-300 {
  border-color: #cbd5e1;
}

.border-slate-400 {
  border-color: #94a3b8;
}

.border-primary {
  border-color: var(--primary);
}

.border-primary-opacity-20 {
  border-color: rgba(19, 127, 236, 0.2);
}

.border-dashed {
  border-style: dashed;
}

.border-l-4 {
  border-left-width: 4px;
}

.border-l-primary {
  border-left-color: var(--primary);
}

.border-b {
  border-bottom-width: 1px;
}

.border-b-slate-100 {
  border-bottom-color: #f1f5f9;
}

.rounded {
  border-radius: 0.25rem;
}

.rounded-md {
  border-radius: 0.375rem;
}

.rounded-lg {
  border-radius: 0.5rem;
}

.rounded-xl {
  border-radius: 0.75rem;
}

.shadow-sm {
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
}

.shadow-lg {
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
}

.shadow-primary-opacity-20 {
  box-shadow: 0 0 0 0.5rem rgba(19, 127, 236, 0.2);
}

.shadow-primary-opacity-30 {
  box-shadow: 0 0 0 0.5rem rgba(19, 127, 236, 0.3);
}

.shadow-primary-opacity-40 {
  box-shadow: 0 0 0 0.5rem rgba(19, 127, 236, 0.4);
}

.transition-colors {
  transition-property: color, background-color, border-color, text-decoration-color, fill, stroke;
  transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
  transition-duration: 150ms;
}

.transition-all {
  transition-property: all;
  transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
  transition-duration: 150ms;
}

.transition-transform {
  transition-property: transform;
  transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
  transition-duration: 150ms;
}

.hover-bg-slate-50:hover {
  background-color: #f8fafc;
}

.hover-bg-primary-opacity-5:hover {
  background-color: rgba(19, 127, 236, 0.05);
}

.hover-bg-primary-opacity-90:hover {
  background-color: rgba(19, 127, 236, 0.9);
}

.hover-border-primary-opacity-50:hover {
  border-color: rgba(19, 127, 236, 0.5);
}

.hover-shadow-primary-opacity-40:hover {
  box-shadow: 0 0 0 0.5rem rgba(19, 127, 236, 0.4);
}

.hover-border-slate-300:hover {
  border-color: #cbd5e1;
}

.hover-border-primary:hover {
  border-color: var(--primary);
}

.hover-text-primary:hover {
  color: var(--primary);
}

.hover-text-red-500:hover {
  color: #ef4444;
}

.active-scale-95:active {
  transform: scale(0.95);
}

.group:hover .group-hover-scale-110 {
  transform: scale(1.1);
}

.group:hover .group-hover-text-primary {
  color: var(--primary);
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border-width: 0;
}

.relative {
  position: relative;
}

.absolute {
  position: absolute;
}

.top-4 {
  top: 1rem;
}

.right-4 {
  right: 1rem;
}

.top-1-half {
  top: 50%;
}

.-translate-y-1-half {
  transform: translateY(-50%);
}

.w-full {
  width: 100%;
}

.w-11 {
  width: 2.75rem;
}

.h-5 {
  height: 1.25rem;
}

.h-6 {
  height: 1.5rem;
}

.h-40 {
  height: 10rem;
}

.h-42 {
  height: 10.5rem;
}

.h-46 {
  height: 11.5rem;
}

.min-h-40 {
  min-height: 10rem;
}

.min-h-42 {
  min-height: 10.5rem;
}

.min-h-46 {
  min-height: 11.5rem;
}

.flex-1 {
  flex: 1;
}

.ml-auto {
  margin-left: auto;
}

.ms-3 {
  margin-left: 0.75rem;
}

.appearance-none {
  appearance: none;
}

.outline-none {
  outline: 2px solid transparent;
  outline-offset: 2px;
}

.focus-border-primary:focus {
  border-color: var(--primary);
}

.focus-ring-0:focus {
  box-shadow: 0 0 0 0 rgba(0, 0, 0, 0);
}

.focus-ring-4:focus {
  box-shadow: 0 0 0 4px rgba(0, 0, 0, 0.1);
}

.focus-ring-primary-opacity-5:focus {
  box-shadow: 0 0 0 4px rgba(19, 127, 236, 0.05);
}

.focus-ring-red-500:focus {
  box-shadow: 0 0 0 4px rgba(239, 68, 68, 0.5);
}

.focus-ring-orange-500:focus {
  box-shadow: 0 0 0 4px rgba(249, 115, 22, 0.5);
}

.focus-ring-yellow-500:focus {
  box-shadow: 0 0 0 4px rgba(234, 179, 8, 0.5);
}

.peer:checked ~ .peer-checked-after-translate-x-full {
  transform: translateX(100%);
}

.peer:checked ~ .peer-checked-after-border-white {
  border-color: #ffffff;
}

.peer:checked ~ .peer-checked-bg-primary {
  background-color: var(--primary);
}

.rtl-peer-checked-after-translate-x-full {
  transform: translateX(-100%);
}

.after-content-empty {
  content: '';
}

.after-absolute {
  position: absolute;
}

.after-top-2px {
  top: 2px;
}

.after-start-2px {
  left: 2px;
}

.after-bg-white {
  background-color: #ffffff;
}

.after-border-gray-300 {
  border-color: #d1d5db;
}

.after-border {
  border-width: 1px;
}

.after-rounded-full {
  border-radius: 9999px;
}

.after-h-5 {
  height: 1.25rem;
}

.after-w-5 {
  width: 1.25rem;
}

.after-transition-all {
  transition-property: all;
  transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
  transition-duration: 150ms;
}

/* 网格布局 */
.grid {
  display: grid;
}

.grid-cols-1 {
  grid-template-columns: repeat(1, minmax(0, 1fr));
}

.grid-cols-2 {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.grid-cols-12 {
  grid-template-columns: repeat(12, minmax(0, 1fr));
}

.col-span-12 {
  grid-column: span 12 / span 12;
}

.col-span-6 {
  grid-column: span 6 / span 6;
}

.md\:col-span-2 {
  grid-column: span 2 / span 2;
}

.md\:col-span-3 {
  grid-column: span 3 / span 3;
}

.md\:col-span-5 {
  grid-column: span 5 / span 5;
}

.md\:col-span-7 {
  grid-column: span 7 / span 7;
}

.md\:grid-cols-2 {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

/* 响应式 */
@media (max-width: 768px) {
  .max-w-6xl {
    max-width: 100%;
  }
  
  .px-6 {
    padding-left: 1rem;
    padding-right: 1rem;
  }
  
  .py-10 {
    padding-top: 1.5rem;
    padding-bottom: 1.5rem;
  }
}
</style>