// src/utils/websocket.ts
import { message } from "ant-design-vue";

// WebSocket 控制管理器
class WebSocketManager {
    private metricsSocket: WebSocket | null = null;
    private controlSocket: WebSocket | null = null;
    private metricsUrl: string;
    private controlUrl: string;

    // 回调函数
    private onMetricsMessage: ((data: any) => void) | null = null;
    private onControlMessage: ((data: any) => void) | null = null;
    private onConnectionChange: ((connected: boolean) => void) | null = null;

    constructor(
        metricsUrl: string = 'ws://localhost:8000/ws/metrics',
        controlUrl: string = 'ws://localhost:8000/control'
    ) {
        this.metricsUrl = metricsUrl;
        this.controlUrl = controlUrl;
    }

    // 连接所有 WebSocket
    connectAll() {
        this.connectMetrics();
        this.connectControl();
    }

    // 连接监控 WebSocket
    connectMetrics() {
        if (this.metricsSocket && this.metricsSocket.readyState === WebSocket.OPEN) {
            return;
        }

        try {
            this.metricsSocket = new WebSocket(this.metricsUrl);

            this.metricsSocket.onopen = () => {
                console.log('监控 WebSocket 连接已建立');
                this.onConnectionChange?.(true);
            };

            this.metricsSocket.onmessage = (event: MessageEvent) => {
                try {
                    const data = JSON.parse(event.data);
                    this.onMetricsMessage?.(data);
                } catch (err) {
                    console.error("解析监控数据失败:", err);
                }
            };

            this.metricsSocket.onerror = (error) => {
                console.error('监控 WebSocket 错误:', error);
                message.error("监控连接错误");
            };

            this.metricsSocket.onclose = () => {
                console.log('监控 WebSocket 连接已关闭');
                this.onConnectionChange?.(false);
            };
        } catch (error) {
            console.error('创建监控 WebSocket 连接失败:', error);
            message.error("创建监控连接失败");
        }
    }

    // 连接控制 WebSocket
    connectControl() {
        if (this.controlSocket && this.controlSocket.readyState === WebSocket.OPEN) {
            return;
        }

        try {
            this.controlSocket = new WebSocket(this.controlUrl);

            this.controlSocket.onopen = () => {
                console.log('控制 WebSocket 连接已建立');
                message.success("控制连接已建立");
            };

            this.controlSocket.onmessage = (event: MessageEvent) => {
                try {
                    const data = JSON.parse(event.data);
                    this.onControlMessage?.(data);
                } catch (err) {
                    console.error("解析控制响应失败:", err);
                }
            };

            this.controlSocket.onerror = (error) => {
                console.error('控制 WebSocket 错误:', error);
                message.error("控制连接错误");
            };

            this.controlSocket.onclose = () => {
                console.log('控制 WebSocket 连接已关闭');
            };
        } catch (error) {
            console.error('创建控制 WebSocket 连接失败:', error);
            message.error("创建控制连接失败");
        }
    }

    // 发送控制命令
    sendControlCommand(cmd: string, taskId: number, data: any = {}) {
        if (!this.controlSocket || this.controlSocket.readyState !== WebSocket.OPEN) {
            message.error("控制连接未就绪");
            return false;
        }

        const messageObj = {
            cmd: cmd,
            task_id: taskId,
            data: data
        };

        try {
            this.controlSocket.send(JSON.stringify(messageObj));
            console.log(`发送控制命令: ${cmd}`, messageObj);
            return true;
        } catch (error) {
            console.error(`发送控制命令 ${cmd} 失败:`, error);
            message.error("发送命令失败");
            return false;
        }
    }

    // 关闭所有连接
    disconnectAll() {
        if (this.metricsSocket) {
            this.metricsSocket.close();
        }
        if (this.controlSocket) {
            this.controlSocket.close();
        }
    }

    // 设置回调函数
    setOnMetricsMessage(callback: (data: any) => void) {
        this.onMetricsMessage = callback;
    }

    setOnControlMessage(callback: (data: any) => void) {
        this.onControlMessage = callback;
    }

    setOnConnectionChange(callback: (connected: boolean) => void) {
        this.onConnectionChange = callback;
    }

    // 检查连接状态
    isMetricsConnected(): boolean {
        return this.metricsSocket?.readyState === WebSocket.OPEN;
    }

    isControlConnected(): boolean {
        return this.controlSocket?.readyState === WebSocket.OPEN;
    }
}

// 创建单例实例
export const wsManager = new WebSocketManager();