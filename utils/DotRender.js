class DotRender {
    constructor() {
        this.cache = new Map();
        this.API_URL = 'https://www.gptkong.com/tools/online_graphviz_render';
    }

    /**
     * 将dot语言转换为SVG
     * @param {string} dotSource - dot语言源代码
     * @returns {Promise<string>} - 返回SVG字符串
     */
    async render(dotSource) {
        // 检查缓存
        if (this.cache.has(dotSource)) {
            return this.cache.get(dotSource);
        }
        try {
            const response = await fetch(this.API_URL, {
                method: 'POST',
                headers: {
                    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                },
                body: `dotSource=${encodeURIComponent(dotSource)}`,
            });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const svgContent = await response.text();
            // 存入缓存
            this.cache.set(dotSource, svgContent);
            return svgContent;
        } catch (error) {
            throw error;
        }
    }

    /**
     * 清除缓存
     */
    clearCache() {
        this.cache.clear();
    }
}

// 导出工具类
export default DotRender;