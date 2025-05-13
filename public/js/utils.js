async function generateDot(data) {
    try {
        const response = await fetch('/api/lexical/fa/dot', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ data })
        });
        if (!response.ok) {
            throw new Error(response.error);
        }
        const res = await response.json();
        return res.dotSource;
    } catch (error) {
        throw new Error('导出 dot 过程中出错:' + error.message);
    }
}
async function renderDot(dotSource) {
    try {
        const response = await fetch('/api/lexical/fa/render', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ dotSource })
        });

        if (!response.ok) {
            throw new Error(response.error);
        }
        const data = await response.json();
        return data.svg;
    } catch (error) {
        throw new Error('渲染 dot 失败:' + error.message);
    }
}