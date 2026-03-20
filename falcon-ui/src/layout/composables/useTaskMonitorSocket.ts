import { onUnmounted, ref, type Ref } from "vue";

import { getToken } from "@/utils/auth";
import { taskRuntimeSocket, type TaskRuntimeSocketMessage } from "@/utils/websocket";

interface MonitorSocketOptions {
  taskId: Ref<number>;
  fetchTaskStatus: () => Promise<void>;
  fetchTaskRuns: () => Promise<void>;
  refreshReportIfNeeded: (force?: boolean) => Promise<void>;
  onResetSelectionToLatest?: () => void;
}

const FALLBACK_ACTIVATION_DELAY_MS = 4000;
const FALLBACK_STATUS_POLL_MS = 5000;
const FALLBACK_DETAILS_POLL_MS = 15000;

export const useTaskMonitorSocket = (options: MonitorSocketOptions) => {
  const wsConnected = ref(false);
  let suppressFallbackOnDisconnect = false;

  let fallbackActivationTimer: ReturnType<typeof setTimeout> | null = null;
  let fallbackStatusPollingTimer: ReturnType<typeof setInterval> | null = null;
  let fallbackDetailsPollingTimer: ReturnType<typeof setInterval> | null = null;

  const stopFallbackPolling = () => {
    if (fallbackActivationTimer) {
      clearTimeout(fallbackActivationTimer);
      fallbackActivationTimer = null;
    }
    if (fallbackStatusPollingTimer) {
      clearInterval(fallbackStatusPollingTimer);
      fallbackStatusPollingTimer = null;
    }
    if (fallbackDetailsPollingTimer) {
      clearInterval(fallbackDetailsPollingTimer);
      fallbackDetailsPollingTimer = null;
    }
  };

  const pollRuntimeSnapshot = async () => {
    if (!options.taskId.value || wsConnected.value) {
      return;
    }

    try {
      await options.fetchTaskStatus();
    } catch (error) {
      console.error("Fallback status polling failed:", error);
    }
  };

  const pollRuntimeDetails = async () => {
    if (!options.taskId.value || wsConnected.value) {
      return;
    }

    try {
      await options.fetchTaskRuns();
      await options.refreshReportIfNeeded(true);
    } catch (error) {
      console.error("Fallback detail polling failed:", error);
    }
  };

  const startFallbackPolling = () => {
    if (fallbackActivationTimer || fallbackStatusPollingTimer || fallbackDetailsPollingTimer) {
      return;
    }

    fallbackActivationTimer = setTimeout(() => {
      fallbackActivationTimer = null;
      if (wsConnected.value || !options.taskId.value) {
        return;
      }

      void pollRuntimeSnapshot();
      void pollRuntimeDetails();

      fallbackStatusPollingTimer = setInterval(() => {
        void pollRuntimeSnapshot();
      }, FALLBACK_STATUS_POLL_MS);

      fallbackDetailsPollingTimer = setInterval(() => {
        void pollRuntimeDetails();
      }, FALLBACK_DETAILS_POLL_MS);
    }, FALLBACK_ACTIVATION_DELAY_MS);
  };

  const connectRuntimeSocket = () => {
    const token = getToken();
    if (!options.taskId.value || !token) {
      return;
    }

    suppressFallbackOnDisconnect = false;
    taskRuntimeSocket.connect(options.taskId.value, token);
  };

  const disconnectRuntimeSocket = () => {
    suppressFallbackOnDisconnect = true;
    stopFallbackPolling();
    taskRuntimeSocket.disconnect();
    wsConnected.value = false;
  };

  const handleRuntimeSocketMessage = async (payload: TaskRuntimeSocketMessage) => {
    if (payload.task_id !== options.taskId.value) {
      return;
    }

    try {
      if (payload.event === "connected") {
        await Promise.all([options.fetchTaskStatus(), options.fetchTaskRuns()]);
        await options.refreshReportIfNeeded(true);
        return;
      }

      await options.fetchTaskStatus();

      if (["started", "finished", "failed", "canceled"].includes(payload.event)) {
        await options.fetchTaskRuns();
        options.onResetSelectionToLatest?.();
        await options.refreshReportIfNeeded(true);
        return;
      }

      if (payload.event === "snapshot") {
        await options.refreshReportIfNeeded(false);
      }
    } catch (error) {
      console.error("Failed to sync runtime data from websocket message:", error);
    }
  };

  taskRuntimeSocket.setOnConnectionChange((connected) => {
    wsConnected.value = connected;
    if (connected) {
      suppressFallbackOnDisconnect = false;
      stopFallbackPolling();
      return;
    }
    if (suppressFallbackOnDisconnect) {
      return;
    }
    startFallbackPolling();
  });

  taskRuntimeSocket.setOnMessage((payload) => {
    void handleRuntimeSocketMessage(payload);
  });

  taskRuntimeSocket.setOnError((event) => {
    console.error("Task runtime websocket failed to connect:", event);
  });

  onUnmounted(() => {
    disconnectRuntimeSocket();
  });

  return {
    wsConnected,
    connectRuntimeSocket,
    disconnectRuntimeSocket,
    stopFallbackPolling,
  };
};
