// 格式化函数：保留两位小数
export const formatNumber = (value: number | undefined, fallback: string = '0.00'): string => {
    if (value === undefined || value === null || isNaN(value)) {
        return fallback;
    }
    return value.toFixed(2);
};

// 格式化百分比：保留两位小数
export const formatPercent = (value: number | undefined, fallback: string = '0.00%'): string => {
    if (value === undefined || value === null || isNaN(value)) {
        return fallback;
    }
    return (value * 100).toFixed(2) + '%';
};

// 格式化大数字：添加千位分隔符
export const formatNumberWithCommas = (value: number | undefined, fallback: string = '0'): string => {
    if (value === undefined || value === null || isNaN(value)) {
        return fallback;
    }
    return value.toLocaleString('en-US');
};

