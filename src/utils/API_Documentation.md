# TiAlN硬度预测插件 API 文档

## 概述

TiAlN_ML插件是一个基于机器学习模型的TiAlN合金硬度预测工具，通过调用ONNX推理服务来预测TiAlN材料的硬度值。

## 服务信息

- **服务名称**: TiAlN硬度预测服务
- **推理引擎**: ONNX Runtime
- **服务地址**: `http://111.22.21.99:10002`
- **模型UUID**: `70470382-7108-4f92-ad86-69b971f820cb`

## API接口

### 1. 硬度预测接口

**工具名称**: `predict_hardness`

**功能描述**: 基于TiAlN合金的成分和工艺参数预测材料硬度

#### 请求参数

| 参数名 | 类型 | 范围 | 描述 | 必需 |
|--------|------|------|------|------|
| `ti` | number | 0.0 - 1.0 | 钛(Ti)含量 | 是 |
| `al` | number | 0.0 - 1.0 | 铝(Al)含量 | 是 |
| `N` | number | 0.0 - 2.0 | 氮(N)含量 | 是 |
| `time` | number | 0.0 - 500.0 | 处理时间(小时) | 是 |
| `temperature` | number | 0.0 - 1200.0 | 处理温度(摄氏度) | 是 |

#### 参数验证规则

1. **基础验证**:
   - Ti含量: 0.0 ≤ ti ≤ 1.0
   - Al含量: 0.0 ≤ al ≤ 1.0
   - N含量: 0.0 ≤ N ≤ 2.0
   - 处理时间: 0.0 ≤ time ≤ 500.0 小时
   - 处理温度: 0.0 ≤ temperature ≤ 1200.0 °C

2. **成分平衡警告**:
   - 当 Ti + Al 含量之和偏离 1.0 超过 0.2 时会发出警告

#### 请求示例

```json
{
  "method": "tools/call",
  "params": {
    "name": "predict_hardness",
    "arguments": {
      "ti": 0.5,
      "al": 0.5,
      "N": 1.0,
      "time": 100.0,
      "temperature": 800.0
    }
  }
}
```

#### 响应格式

**成功响应**:
```json
{
  "content": [
    {
      "type": "text",
      "text": "2456.7890",
      "mimeType": "text/plain"
    }
  ],
  "isError": false
}
```

**错误响应**:
```json
{
  "content": [
    {
      "type": "text",
      "text": "Missing or invalid 'ti' parameter"
    }
  ],
  "isError": true
}
```

## 底层HTTP API

### ONNX推理接口

**URL**: `POST http://111.22.21.99:10002/models/70470382-7108-4f92-ad86-69b971f820cb/inference`

#### 请求头

```
Content-Type: application/json
Host: 111.22.21.99:10002
```

#### 请求体结构

```json
{
  "inputs": {
    "ti": f64,          // 钛含量
    "al": f64,          // 铝含量
    "N": f64,           // 氮含量
    "time": f64,        // 处理时间(小时)
    "temperature": f64  // 处理温度(摄氏度)
  }
}
```

#### 响应体结构

```json
{
  "outputs": {
    "hardness": {
      "value": f64  // 预测的硬度值
    }
  },
  "inference_time_ms": f64,     // 推理耗时(毫秒)
  "request_id": "string",        // 请求ID
  "model_uuid": "string"         // 模型UUID
}
```

## 错误处理

### 常见错误类型

1. **参数验证错误**:
   - `Missing or invalid 'ti' parameter`
   - `Ti content must be between 0.0 and 1.0`
   - `Al content must be between 0.0 and 1.0`
   - `N content must be between 0.0 and 2.0`
   - `Time must be between 0.0 and 500.0 hours`
   - `Temperature must be between 0.0 and 1200.0°C`

2. **HTTP请求错误**:
   - `ONNX service error: 404 - Not Found`
   - `ONNX service error: 500 - Internal Server Error`

3. **数据处理错误**:
   - `Failed to serialize request`
   - `Failed to parse response`

## 使用示例

### Python示例

```python
import requests
import json

# API端点
url = "http://111.22.21.99:10002/models/70470382-7108-4f92-ad86-69b971f820cb/inference"

# 请求数据
data = {
    "inputs": {
        "ti": 0.3,
        "al": 0.7,
        "N": 1.2,
        "time": 150.0,
        "temperature": 900.0
    }
}

# 发送请求
headers = {
    "Content-Type": "application/json"
}

response = requests.post(url, json=data, headers=headers)
result = response.json()

if response.status_code == 200:
    hardness = result["outputs"]["hardness"]["value"]
    print(f"预测硬度: {hardness:.4f}")
else:
    print(f"错误: {response.status_code}")
```

### JavaScript示例

```javascript
const url = 'http://111.22.21.99:10002/models/70470382-7108-4f92-ad86-69b971f820cb/inference';

const data = {
  inputs: {
    ti: 0.4,
    al: 0.6,
    N: 1.0,
    time: 200.0,
    temperature: 850.0
  }
};

fetch(url, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Host': '111.22.21.99:10002'
  },
  body: JSON.stringify(data)
})
.then(response => response.json())
.then(result => {
  const hardness = result.outputs.hardness.value;
  console.log(`预测硬度: ${hardness.toFixed(4)}`);
})
.catch(error => {
  console.error('错误:', error);
});
```

## 技术规格

- **编程语言**: Rust
- **插件框架**: Extism PDK
- **推理框架**: ONNX Runtime
- **数据格式**: JSON
- **通信协议**: HTTP/HTTPS
- **返回格式**: 纯文本 (硬度值，保留4位小数)

## 性能指标

- **典型推理时间**: < 100ms (根据inference_time_ms字段)
- **输入验证**: 客户端验证 + 服务端验证
- **错误处理**: 完整的错误信息和状态码

## 注意事项

1. 所有输入参数都是必需的，必须在指定的有效范围内
2. Ti + Al含量建议接近1.0以确保成分平衡
3. 服务地址和模型UUID可能需要根据部署环境进行调整
4. 建议在生产环境中添加适当的错误重试机制
5. 服务需要网络连接到 `111.22.21.99:10002`

## 维护信息

- **插件版本**: 0.1.0
- **最后更新**: 2024年
- **兼容性**: TopMat-MCP v1.0+
- **依赖**: extism-pdk, serde, serde_json